"""B01--B04_X1: branch matrices and encoded Choi/stabilizer oracles.

No noise, distance, Monte Carlo benchmark, detector or Relay claims. The dense
oracle contracts projectors directly; expected channels use only the requested
data Pauli. Encoded Choi tests retain a reference for every logical qubit.
"""
from dataclasses import replace
from itertools import product as bits
from types import SimpleNamespace

import numpy as np
import pytest
import stim

from gross_design_bandle.algebra import gf2
from gross_design_bandle.algebra.pauli import Pauli
from gross_design_bandle.codes import load_reference_code, small_debug_code
from gross_design_bandle.lpu.reference import build_reference_lpu
from gross_design_bandle.surgery.cycles import with_full_cycle_basis
from gross_design_bandle.surgery.deformation import compile_deformation
from gross_design_bandle.surgery.frame import Parity, build_split_frame
from gross_design_bandle.surgery.graph import AuxiliaryGraph, Cycle, Edge
from gross_design_bandle.surgery.ports import PortMap, embed, product
from gross_design_bandle.surgery.protocol import IdealProtocol, build_ideal_protocol, to_stim_pauli
from gross_design_bandle.validation.instrument import IdealBellCheck, bell_readout_branch, dense_branch, pauli_matrix


def toy(kind="two", word="XX", sign=1):
    n = len(word)
    ids = tuple(f"data:q{i}" for i in range(n))
    if kind == "two":
        vertices, pairs = ("v0", "v1"), ((0, 1),)
    elif kind == "triangle":
        vertices, pairs = ("v0", "v1", "v2"), ((0, 1), (1, 2), (2, 0))
    else:
        vertices, pairs = ("v0", "dummy", "v1"), ((0, 1), (1, 2))
    edges = tuple(Edge(f"e{i}", (vertices[u], vertices[v]), "local tiny oracle") for i, (u, v) in enumerate(pairs))
    cycles = (Cycle("triangle", tuple(e.id for e in edges), "local tiny oracle"),) if kind == "triangle" else ()
    graph = AuxiliaryGraph(vertices, edges, cycles, f"tiny_{kind}")
    ports = []
    for i, v in enumerate(vertices):
        w = ["I"]*n
        if v != "dummy":
            q = int(v[1:])
            w[q] = word[q]
        ports.append(Pauli.from_word("".join(w), ids, sign=sign if i == 0 else 1))
    return graph, PortMap(vertices, tuple(ports), ("data",), Pauli.from_word(word, ids, sign))


def check_dense_channel(protocol, *, rounds=1):
    d, v, e = len(protocol.ports.target.x), len(protocol.graph.vertices), len(protocol.graph.edges)
    target = pauli_matrix(protocol.ports.target)
    projectors = [(np.eye(2**d) + (-1)**m * target)/2 for m in (0, 1)]
    # A fixed arbitrary complex state and a maximally reference-entangled state.
    rng = np.random.default_rng(1303)
    arbitrary = rng.normal(size=2**d) + 1j*rng.normal(size=2**d)
    arbitrary /= np.linalg.norm(arbitrary)
    choi = np.eye(2**d).reshape(-1)/np.sqrt(2**d)
    states = (arbitrary, choi)
    accum = [[np.zeros((len(psi), len(psi)), dtype=complex) for _ in (0, 1)] for psi in states]
    complete = np.zeros((2**d, 2**d), dtype=complex)
    valid, forbidden = 0, 0
    for s in bits((0, 1), repeat=v):
        m = sum(s) % 2
        for z in bits((0, 1), repeat=e):
            raw = dense_branch(protocol, s, z, rounds=rounds)
            outcome = dict(zip(protocol.frame.edge_outcome_ids, z))
            try:
                t, q = protocol.frame.evaluate(outcome)
            except ValueError:
                np.testing.assert_allclose(raw, 0, atol=1e-12)
                forbidden += 1
                continue
            corrected = pauli_matrix(q) @ raw
            scalar = 2**(1-v) * (-1)**sum(a*b for a, b in zip(s, t))
            np.testing.assert_allclose(corrected, scalar*projectors[m], atol=1e-12)
            complete += corrected.conj().T @ corrected
            for i, psi in enumerate(states):
                operator = corrected if i == 0 else np.kron(corrected, np.eye(2**d))
                out = operator @ psi
                accum[i][m] += np.outer(out, out.conj())
            valid += 1
    np.testing.assert_allclose(complete, np.eye(2**d), atol=1e-12)
    for i, psi in enumerate(states):
        for m in (0, 1):
            projected = (projectors[m] if i == 0 else np.kron(projectors[m], np.eye(2**d))) @ psi
            np.testing.assert_allclose(accum[i][m], np.outer(projected, projected.conj()), atol=1e-12)
    return valid, forbidden, accum


@pytest.mark.parametrize("word,sign", [("XX", 1), ("YZ", 1), ("XX", -1)])
def test_B01_all_branches_arbitrary_and_reference_entangled(word, sign):
    graph, ports = toy(word=word, sign=sign)
    protocol = build_ideal_protocol(graph, ports)
    valid, forbidden, _ = check_dense_channel(protocol)
    assert valid == 8 and forbidden == 0
    assert protocol.ideal_only and protocol.to_dict()["ideal_only"]
    assert protocol.to_stim().num_measurements == len(protocol.outcomes)


@pytest.mark.parametrize("kind,word", [("triangle", "XYZ"), ("dummy", "XY")])
def test_B02_root_path_and_repeat_channels(kind, word):
    graph, ports = toy(kind, word)
    channels = []
    trees = (("e0", "e1"), ("e1", "e2"), ("e0", "e2")) if kind == "triangle" else (("e0", "e1"),)
    for root in graph.vertices:
        for tree in trees:
            protocol = build_ideal_protocol(graph, ports, rounds=2, root=root, tree_edge_ids=tree)
            valid, forbidden, channel = check_dense_channel(protocol, rounds=2)
            assert valid == 32 and forbidden == (32 if kind == "triangle" else 0)
            channels.append(channel)
    for channel in channels[1:]:
        for actual, expected in zip(channel, channels[0]):
            for a, b in zip(actual, expected):
                np.testing.assert_allclose(a, b, atol=1e-12)


def test_B02_bell_split_readout_xor_preserves_coherence():
    ids = ("data:q0", "data:q1")
    left = Pauli.from_word("YI", ids)
    right = Pauli.from_word("IZ", ids, -1)
    target = pauli_matrix(left*right)
    bell = IdealBellCheck(left, right, ("bell/readout/left", "bell/readout/right"))
    choi = np.eye(4).reshape(-1)/2
    channel = [np.zeros((16, 16), dtype=complex) for _ in (0, 1)]
    for a, b in bits((0, 1), repeat=2):
        branch = bell.branch(dict(zip(bell.outcome_ids, (a, b))))
        projector = (np.eye(4) + (-1)**(a ^ b)*target)/2
        np.testing.assert_allclose(branch, projector/np.sqrt(2), atol=1e-12)
        out = np.kron(branch, np.eye(4)) @ choi
        channel[a ^ b] += np.outer(out, out.conj())
    for m in (0, 1):
        out = np.kron((np.eye(4)+(-1)**m*target)/2, np.eye(4)) @ choi
        np.testing.assert_allclose(channel[m], np.outer(out, out.conj()), atol=1e-12)
    # Both physical readouts have stable IDs and the algebraic result is XOR.
    parity = bell.readout
    assert [parity.evaluate(dict(zip(parity.ids, b))) for b in bits((0, 1), repeat=2)] == [0, 1, 1, 0]
    assert bell.to_dict()["ideal_only"]
    assert bell.to_dict()["physical_outcome_ids"] == list(bell.outcome_ids)


def debug_deformation():
    code = small_debug_code("debug")
    target = code.logical("X", "1")
    assert gf2.rank(np.vstack((code.hx, target.x))) == gf2.rank(code.hx)+1
    support = [i for i, b in enumerate(target.x) if b]
    vertices = tuple(f"port:{i}" for i in support)
    edges = tuple(Edge(f"path:{i}", (vertices[i], vertices[i+1]), "local debugging fixture") for i in range(len(vertices)-1))
    edges += (Edge("chord", (vertices[-1], vertices[0]), "local debugging fixture"),)
    graph = with_full_cycle_basis(AuxiliaryGraph(vertices, edges, (), "generic_debug18"))
    ports = []
    for i in support:
        word = ["I"]*code.spec.n
        word[i] = "X"
        ports.append(Pauli.from_word("".join(word), code.qubit_ids))
    portmap = PortMap(vertices, tuple(ports), (code.block_id,), target)
    lpu = SimpleNamespace(codes=(code,), graph=graph, ports=portmap)
    return code, compile_deformation(lpu, dressing_profile="generic_gf2")


def encoded_input(code, protocol, mode, seed=0):
    """Prepare a full encoded Choi state, or X1 eigenstate plus preserved Choi.

    Expected stabilizers are input code generators and named logical/reference
    pairs, independent of deformation/paths/frames/vertex checks.
    """
    refs = tuple(f"reference:{i}" for i in range(code.k))
    register = protocol.register + refs
    stabilizers = [to_stim_pauli(p, register) for p in code.checks]
    for edge in protocol.register[len(code.qubit_ids):]:
        stabilizers.append(to_stim_pauli(Pauli.from_word("Z", (edge,)), register))
    for i, (lx, lz) in enumerate(zip(code.logical_x, code.logical_z)):
        rx = embed(Pauli.from_word("X", (refs[i],)), register)
        rz = embed(Pauli.from_word("Z", (refs[i],)), register)
        if i == 0 and mode in ("plus", "minus"):
            stabilizers.extend((to_stim_pauli(lx.with_phase(2 if mode == "minus" else 0), register), to_stim_pauli(rx)))
        else:
            stabilizers.extend((to_stim_pauli(embed(lx, register)*rx), to_stim_pauli(embed(lz, register)*rz)))
    tableau = stim.Tableau.from_stabilizers(stabilizers, allow_redundant=True)
    simulator = stim.TableauSimulator(seed=seed)
    simulator.do(tableau.to_circuit())
    return simulator, register, refs


def postselect_records(simulator, records, values, paulis):
    probability = 1.0
    for record, observable in zip(records, paulis):
        bit = values[record.id]
        expectation = simulator.peek_observable_expectation(observable)
        if expectation == 0:
            probability *= .5
        elif expectation != (-1)**bit:
            return 0.0
        simulator.postselect_observable(observable, desired_value=bool(bit))
    return probability


def assert_corrected_state(initial, actual, register, protocol, outcomes):
    m = protocol.logical_outcome.evaluate(outcomes)
    _, q = protocol.frame.evaluate(outcomes)
    actual.do_pauli_string(to_stim_pauli(q, register))
    expected = initial.copy()
    observable = to_stim_pauli(protocol.ports.target, register)
    born = (1+(-1)**m*initial.peek_observable_expectation(observable))/2
    expected.postselect_observable(observable, desired_value=bool(m))
    for edge, id in zip(protocol.register[len(protocol.ports.target.x):], protocol.frame.edge_outcome_ids):
        if outcomes[id]:
            expected.x(register.index(edge))
    assert actual.canonical_stabilizers() == expected.canonical_stabilizers()
    return born, m


@pytest.fixture(scope="module")
def debug():
    return debug_deformation()


def test_B03_debug18_all_branches_encoded_choi(debug):
    code, df = debug
    protocol = build_ideal_protocol(df.graph, df.lpu.ports, rounds=2, deformation=df, protocol_id="debug18")
    initial, register, refs = encoded_input(code, protocol, "choi")
    assert len(refs) == code.k == 4
    assert len(df.graph.cycles) == len(df.graph.edges)-len(df.graph.vertices)+1
    paulis = [to_stim_pauli(r.pauli, register) for r in protocol.outcomes]
    sums = [0., 0.]
    branches = 0
    v = len(df.graph.vertices)
    # Exhaust every allowed (vertex, cut) branch: 2048 for six ports.
    for s in bits((0, 1), repeat=v):
        for tail in bits((0, 1), repeat=v-1):
            t = np.array((0,)+tail, dtype=np.uint8)
            z = gf2.matmul(df.graph.incidence.T, t[:, None])[:, 0]
            values = dict(zip(protocol.frame.edge_outcome_ids, map(int, z)))
            _, q = protocol.frame.evaluate(values)
            for r in protocol.outcomes:
                if r.kind == "vertex":
                    values[r.id] = s[df.graph.vertices.index(r.check_id)]
                elif r.kind in ("cycle", "dressed"):
                    values[r.id] = 0
                elif r.kind == "original":
                    values[r.id] = embed(q, protocol.register).symplectic(r.pauli)
            actual = initial.copy()
            probability = postselect_records(actual, protocol.outcomes, values, paulis)
            born, m = assert_corrected_state(initial, actual, register, protocol, values)
            assert probability == 2**(2-2*v)*born
            sums[m] += probability
            branches += 1
    assert branches == 2048
    assert sums == [.5, .5]


@pytest.fixture(scope="module")
def gross_x():
    code = load_reference_code("gross", "block_a")
    return code, compile_deformation(build_reference_lpu(code, "X"))


@pytest.mark.parametrize("mode", ["plus", "minus", "choi"])
def test_B04_X1_gross_encoded_reference_and_both_signs(gross_x, mode):
    code, df = gross_x
    outcomes_seen = set()
    # Bounded exact stabilizer trajectories, not a noisy performance pilot.
    for seed in range(12):
        root = df.graph.vertices[seed % len(df.graph.vertices)]
        protocol = build_ideal_protocol(df.graph, df.lpu.ports, rounds=3, deformation=df,
                                        root=root, protocol_id=f"gross_X1_{seed}")
        initial, register, refs = encoded_input(code, protocol, mode, seed)
        actual = initial.copy()
        circuit = protocol.to_stim()
        assert circuit.num_measurements == len(protocol.outcomes)
        actual.do(circuit)
        values = dict(zip((r.id for r in protocol.outcomes), map(int, actual.current_measurement_record())))
        born, m = assert_corrected_state(initial, actual, register, protocol, values)
        assert born == (.5 if mode == "choi" else 1)
        assert m == (mode == "minus") if mode != "choi" else m in (0, 1)
        outcomes_seen.add(m)
        # Explicit full preserved logical coherence and reference correlations.
        for i in range(1, code.k):
            for logical, axis in ((code.logical_x[i], "X"), (code.logical_z[i], "Z")):
                joint = embed(logical, register)*embed(Pauli.from_word(axis, (refs[i],)), register)
                assert actual.peek_observable_expectation(to_stim_pauli(joint)) == 1
        for check in code.checks:
            assert actual.peek_observable_expectation(to_stim_pauli(check, register)) == 1
        for r in protocol.outcomes:
            if r.kind in ("cycle", "dressed"):
                assert values[r.id] == 0
            if r.kind == "vertex":
                first = next(x for x in protocol.outcomes if x.kind == "vertex" and x.check_id == r.check_id)
                assert values[r.id] == values[first.id]
        # Re-evaluate exactly the same branch with every possible root.
        _, base = protocol.frame.evaluate(values)
        for alternative_root in df.graph.vertices:
            alternative = build_split_frame(df.graph, df.lpu.ports, protocol.frame.edge_outcome_ids, alternative_root)
            _, other = alternative.evaluate(values)
            assert base*other in (Pauli.identity(code.qubit_ids), df.lpu.ports.target)
    assert outcomes_seen == ({0, 1} if mode == "choi" else {int(mode == "minus")})


def test_symbolic_state_machine_and_record_ids():
    graph, ports = toy()
    protocol = IdealProtocol(graph, ports, protocol_id="state_test")
    for action in (protocol.merge, protocol.repeat, protocol.split, protocol.finish, protocol.to_stim, protocol.to_dict):
        with pytest.raises(ValueError):
            action()
    protocol.prepare()
    with pytest.raises(ValueError):
        protocol.prepare()
    protocol.merge().repeat().split().finish()
    for action in (protocol.prepare, protocol.merge, protocol.repeat, protocol.split, protocol.finish):
        with pytest.raises(ValueError):
            action()
    ids = [r.id for r in protocol.outcomes]
    assert len(ids) == len(set(ids)) == protocol.to_stim().num_measurements
    assert set(protocol.logical_outcome.ids) <= set(ids)
    for term in protocol.frame.terms:
        assert set(term.ids) <= set(ids)
    saved = protocol.to_dict()
    assert all(r["id"] for r in saved["outcomes"])
    assert [t["vertex_id"] for t in saved["split_frame"]["terms"]] == list(graph.vertices)
    for rounds in (0, -1, True, 1.5):
        with pytest.raises(ValueError):
            build_ideal_protocol(graph, ports, rounds=rounds)
    # A failed root/path validation preserves the valid merged prefix.
    pending = IdealProtocol(graph, ports).prepare().merge()
    count = len(pending.outcomes)
    with pytest.raises(ValueError, match="root"):
        pending.split(root="absent")
    assert pending.state == "merged" and len(pending.outcomes) == count
    pending.split().finish()


def test_negative_missing_split_frame_changes_instrument():
    graph, ports = toy(word="XX")
    protocol = build_ideal_protocol(graph, ports)
    s, z = (0, 0), (1,)
    raw = dense_branch(protocol, s, z)
    projector = (np.eye(4)+pauli_matrix(ports.target))/2
    # Choi witnesses detect a unitary inside the retained eigenspace.
    choi = np.eye(4).reshape(-1)/2
    missing = np.kron(raw, np.eye(4)) @ choi
    desired = np.kron(projector/2, np.eye(4)) @ choi
    with pytest.raises(AssertionError):
        np.testing.assert_allclose(np.outer(missing, missing.conj()), np.outer(desired, desired.conj()), atol=1e-12)
    _, q = protocol.frame.evaluate(dict(zip(protocol.frame.edge_outcome_ids, z)))
    corrected = np.kron(pauli_matrix(q), np.eye(4)) @ missing
    np.testing.assert_allclose(np.outer(corrected, corrected.conj()), np.outer(desired, desired.conj()), atol=1e-12)


def test_negative_Y_phase_and_inverted_target_sign():
    graph, ports = toy(word="YZ")
    imaginary = ports.ports[0].with_phase(-1)  # XZ instead of iXZ.
    with pytest.raises(ValueError, match="imaginary-phase"):
        replace(ports, ports=(imaginary, ports.ports[1]))
    with pytest.raises(ValueError, match="signed port product"):
        replace(ports, ports=(ports.ports[0].with_phase(2), ports.ports[1]))
    # A self-consistent but wrong -Y target still fails the independent +Y oracle.
    wrong_ports = replace(ports, target=ports.target.with_phase(2),
                          ports=(ports.ports[0].with_phase(2), ports.ports[1]))
    wrong = build_ideal_protocol(graph, wrong_ports)
    branch = dense_branch(wrong, (0, 0), (0,))
    desired = (np.eye(4)+pauli_matrix(ports.target))/4
    with pytest.raises(AssertionError):
        np.testing.assert_allclose(branch, desired, atol=1e-12)
    with pytest.raises(ValueError, match="imaginary-phase"):
        to_stim_pauli(imaginary)


def test_negative_noncut_and_invalid_paths_or_symbols():
    graph, ports = toy("triangle", "XYZ")
    frame = build_split_frame(graph, ports, ("z0", "z1", "z2"))
    with pytest.raises(ValueError, match="not a cut"):
        frame.evaluate({"z0": 1, "z1": 0, "z2": 0})
    with pytest.raises(ValueError, match="missing symbolic"):
        frame.evaluate({"z0": 0})
    with pytest.raises(ValueError, match="binary"):
        frame.evaluate({"z0": .5, "z1": 0, "z2": 0})
    for tree in (("e0",), ("e0", "e0"), ("e0", "absent")):
        with pytest.raises(ValueError, match="spanning tree"):
            build_split_frame(graph, ports, ("z0", "z1", "z2"), tree_edge_ids=tree)
    with pytest.raises(ValueError, match="root"):
        build_split_frame(graph, ports, ("z0", "z1", "z2"), root="absent")
    with pytest.raises(ValueError, match="outcome IDs"):
        build_split_frame(graph, ports, ("same",)*3)
    with pytest.raises(ValueError):
        Parity(("same", "same"))
    with pytest.raises(ValueError, match="overlap"):
        bell_readout_branch(ports.ports[0], ports.ports[0], (0, 0))
    with pytest.raises(ValueError, match="overlap"):
        IdealBellCheck(ports.ports[0], ports.ports[0], ("a", "b"))
    with pytest.raises(ValueError):
        IdealBellCheck(ports.ports[0], ports.ports[1], ("same", "same"))


def test_signed_mpp_lowering_matches_pauli_oracle():
    # Cover signs and all one/two-qubit Pauli words, including identity MPAD.
    for word in ("".join(w) for w in bits("IXYZ", repeat=2)):
        for sign in (-1, 1):
            graph = AuxiliaryGraph(("only",), (), (), "one_vertex_oracle")
            p = Pauli.from_word(word, ("data:q0", "data:q1"), sign)
            ports = PortMap(graph.vertices, (p,), ("data",), p)
            protocol = build_ideal_protocol(graph, ports)
            sim = stim.TableauSimulator(seed=9)
            sim.h(0)
            sim.cx(0, 1)
            before = sim.copy()
            sim.do(protocol.to_stim())
            record = int(sim.current_measurement_record()[0])
            # Literal Stim word/sign is independent of the conversion helper.
            literal = stim.PauliString(("+" if sign == 1 else "-")+word)
            assert to_stim_pauli(p) == literal
            before.postselect_observable(literal, desired_value=bool(record))
            assert sim.canonical_stabilizers() == before.canonical_stabilizers()
