"""A03--A05: frozen paths and unchanged delivered audit are independent oracles.

Signed products are independently multiplied through Pauli.__mul__, rather than
through SignedGroup's coefficient implementation. No circuits or distance tests.
"""
from dataclasses import replace
import json
from pathlib import Path
import sys

import numpy as np
import pytest

from gross_design_bandle.algebra import gf2
from gross_design_bandle.algebra.certificates import SignedGroup
from gross_design_bandle.algebra.pauli import Pauli
from gross_design_bandle.codes.reference_profiles import load_reference_code, reference_fixture
from gross_design_bandle.lpu.reference import build_reference_lpu, build_half_graph, label_index, validate_port_geometry
from gross_design_bandle.surgery.cycles import full_cycle_basis, with_full_cycle_basis
from gross_design_bandle.surgery.deformation import compile_deformation, fixed_input_subspace, require_requested_constraint
from gross_design_bandle.surgery.dressing import dress_boundaries
from gross_design_bandle.surgery.graph import AuxiliaryGraph, Cycle, Edge
from gross_design_bandle.surgery.ports import PortMap, embed, product

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import audit_reference as independent

PROFILES = ("gross", "two_gross")
OPERATIONS = ("X", "XX", "Y", "inter_XX")
CASES = tuple((p, op) for p in PROFILES for op in OPERATIONS)


@pytest.fixture(scope="module")
def constructions():
    result = {}
    for profile in PROFILES:
        a, b = (load_reference_code(profile, block) for block in ("block_a", "block_b"))
        for operation in OPERATIONS:
            lpu = build_reference_lpu(a, operation, b if operation == "inter_XX" else None)
            result[profile, operation] = compile_deformation(lpu)
    return result


@pytest.mark.parametrize("profile", PROFILES)
def test_A03_geometry_and_exact_reference_paths(profile, constructions):
    code = constructions[profile, "X"].lpu.codes[0]
    fixture = reference_fixture(profile)
    checks = validate_port_geometry(code)
    assert checks["weight"] == (12 if profile == "gross" else 20)
    assert all(checks[k] for k in checks if k != "weight")
    # Independently check all four A.1 conditions on literal physical supports.
    base = (code.logical("X", "1"), code.logical("X", "7"), code.logical("Z", "1"), code.logical("Z", "7"))
    support = [np.array(p.x) | np.array(p.z) for p in base]
    for i in range(4):
        for j in range(i):
            overlap = int(np.dot(support[i], support[j]))
            assert overlap == int({i, j} in ({0, 2}, {1, 3})) == base[i].symplectic(base[j])
    for checks_matrix, first, second in ((code.hz, support[0], support[1]), (code.hx, support[2], support[3])):
        assert not np.any((checks_matrix @ first > 0) & (checks_matrix @ second > 0))
    assert independent.rank(np.vstack((code.hx, code.lx))) == independent.rank(code.hx) + 12
    assert independent.rank(np.vstack((code.hz, code.lz))) == independent.rank(code.hz) + 12
    for half, label in (("l", "1"), ("r", "7")):
        graph = build_half_graph(code, half)
        assert (len(graph.vertices), len(graph.edges)) == ((12, 18) if profile == "gross" else (20, 32))
        assert len(graph.cycles) == len(fixture[f"cycles_{half}"])
        for cycle, path in zip(graph.cycles, fixture[f"cycles_{half}"]):
            expected_pairs = [{f"{code.block_id}:{half}:{code.qubit_ids[label_index(s, code.spec)]}" for s in pair}
                              for pair in zip(path, path[1:])]
            actual_pairs = [set(next(e for e in graph.edges if e.id == id).endpoints) for id in cycle.edge_ids]
            assert actual_pairs == expected_pairs
        # Adjacent-check edges have exactly their named pair, with no path dressing.
        named = {id: row for id, row in zip(code.spec.check_ids(code.block_id, "Z"), code.hz)}
        for e in graph.edges:
            if ":adj:" in e.id:
                row = named[e.id.split(":adj:")[1]]
                pair = np.flatnonzero(row & code.logical("X", label).x)
                assert set(e.endpoints) == {f"{code.block_id}:{half}:{code.qubit_ids[q]}" for q in pair}
    full = constructions[profile, "XX"].lpu
    expected = fixture["expected_full_graph"]
    assert (len(full.graph.vertices), len(full.graph.edges), len(full.graph.cycles)) == (expected["vertices"], expected["edges"], expected["selected_cycle_checks"])
    assert full.installed_full_census["total"] == expected["physical_lpu_qubits"]
    assert full.installed_full_census["shared_bell_measurement_qubits"] == 2
    assert full.installed_full_census["vertex_measurement_qubits"] == len(full.graph.vertices) + 1
    assert full.graph.shared_vertex in full.graph.vertices
    assert all(full.graph.shared_vertex not in path for path in full.ladders)
    assert len(full.ladders[0]) == (11 if profile == "gross" else 17)


@pytest.mark.parametrize("profile,operation", CASES)
def test_A04_signed_products_dressing_and_cycle_certificates(profile, operation, constructions, tmp_path):
    df = constructions[profile, operation]
    lpu, graph = df.lpu, df.graph
    fixture = reference_fixture(profile)
    oracle = independent.surgery_graph(fixture, operation)
    b, c = independent.matrices(oracle)
    assert np.array_equal(graph.incidence, b)
    assert np.array_equal(graph.cycle_matrix, c)
    assert np.array_equal(np.array([p.x for p in lpu.ports.ports]), oracle.port_x)
    assert np.array_equal(np.array([p.z for p in lpu.ports.ports]), oracle.port_z)
    assert independent.rank(b) == len(graph.vertices) - 1
    assert not (b @ c.T % 2).any()
    assert np.array_equal(b @ df.dressing.T % 2, df.boundaries.T)
    assert set(df.dressing.sum(axis=1)) <= {0, 1}
    assert product(lpu.ports.ports, lpu.ports.target.qubit_ids) == lpu.ports.target
    d, n = len(lpu.ports.target.x), len(df.group.register)
    generators = df.group.generators
    rows = np.array([p.x + p.z for p in generators], dtype=np.uint8)
    assert not ((rows[:, :n] @ rows[:, n:].T + rows[:, n:] @ rows[:, :n].T) % 2).any()
    assert product((p for p, bit in zip(generators, df.target_witness[0]) if bit), df.group.register) == embed(lpu.ports.target, df.group.register)
    if operation == "Y":
        shared = lpu.ports.ports[graph.vertices.index(graph.shared_vertex)]
        assert shared.phase == 1 and sum(x*z for x, z in zip(shared.x, shared.z)) == 1
        assert lpu.ports.target == lpu.codes[0].logical("Y", "1")
    # Omitted directions are not implied by selected cycles alone; they are
    # implied by the combined SIGNED group, not merely a binary rank test.
    assert len(df.omitted_cycles) > 0
    assert independent.rank(np.vstack((c, df.omitted_cycles))) == len(full_cycle_basis(graph))
    assert independent.rank(c) < len(full_cycle_basis(graph))
    for cycle, witness in zip(df.omitted_cycles, df.omitted_witnesses):
        expected = Pauli(0, (0,)*n, (0,)*d + tuple(cycle), df.group.register)
        assert product((p for p, bit in zip(generators, witness) if bit), df.group.register) == expected
    for relation in independent.kernel_basis(rows.T):
        assert product((p for p, bit in zip(generators, relation) if bit), df.group.register) == Pauli.identity(df.group.register)
    path = tmp_path / f"{profile}-{operation}.json"
    df.save_certificate(path)
    exported = json.loads(path.read_text())
    restored = tuple(Pauli.from_dict(p) for p in exported["generators"])
    assert restored == generators
    for record in exported["omitted_cycle_certificates"]:
        actual = product((p for p, bit in zip(restored, record["coefficients"]) if bit), df.group.register)
        assert actual == Pauli.from_dict(record["product"])
        assert actual.phase == record["product_phase_mod4"] == 0
    for record in exported["old_check_dressing"]:
        old = embed(Pauli.from_dict(record["old"]), df.group.register)
        edge_z = Pauli(0, (0,)*n, (0,)*d + tuple(record["edge_mask"]), df.group.register)
        assert old * edge_z == Pauli.from_dict(record["dressed"])
    assert exported["ranks"]["merged_k"] == (23 if operation == "inter_XX" else 11)


@pytest.mark.parametrize("profile,operation", CASES)
def test_A05_exactly_requested_input_logical_subspace(profile, operation, constructions):
    df = constructions[profile, operation]
    k = sum(c.k for c in df.lpu.codes)
    n, d = len(df.group.register), len(df.lpu.ports.target.qubit_ids)
    rows = np.array([p.x + p.z for p in df.group.generators], dtype=np.uint8)
    relations = independent.kernel_basis(np.hstack((rows[:, d:n], rows[:, n+d:])).T)
    edge_free = relations @ rows % 2
    basis = tuple(embed(p, df.lpu.ports.target.qubit_ids) for c in df.lpu.codes for p in c.logical_z)
    basis += tuple(embed(p, df.lpu.ports.target.qubit_ids) for c in df.lpu.codes for p in c.logical_x)
    bx, bz = np.array([p.x for p in basis]), np.array([p.z for p in basis])
    coords = (edge_free[:, :d] @ bz.T + edge_free[:, n:n+d] @ bx.T) % 2
    expected = np.zeros(2*k, dtype=np.uint8)
    expected[0] = 1
    if operation == "XX":
        expected[6] = 1
    elif operation == "Y":
        expected[k] = 1
    elif operation == "inter_XX":
        expected[12] = 1
    assert independent.rank(coords) == 1
    assert independent.rank(np.vstack((coords, expected))) == 1
    assert df.fixed_input["rank"] == 1 and df.fixed_input["row_basis"] == [expected.tolist()]
    assert df.merged_k == k - 1 == (23 if operation == "inter_XX" else 11)
    for record in df.fixed_input["independent_witnesses"]:
        actual = product((p for p, bit in zip(df.group.generators, record["coefficients"]) if bit), df.group.register)
        assert actual == Pauli.from_dict(record["product"])
        assert not any(actual.x[d:]) and not any(actual.z[d:])


@pytest.mark.parametrize("profile", PROFILES)
def test_inter_adapter_block_ids_zero_ports_and_no_triangles(profile, constructions):
    df = constructions[profile, "inter_XX"]
    graph, ports = df.graph, df.lpu.ports
    assert ports.block_ids == ("block_a", "block_b")
    assert graph.shared_vertex is None and df.lpu.installed_full_census is None
    assert (len(graph.vertices), len(graph.edges), len(graph.cycles)) == ((35, 58, 20) if profile == "gross" else (57, 98, 38))
    adapters = [i for i, v in enumerate(graph.vertices) if v.startswith("adapter:")]
    assert len(adapters) == len(df.lpu.ladders[0])
    for i in adapters:
        assert ports.ports[i] == Pauli.identity(ports.target.qubit_ids)
        assert graph.incidence[i].sum() == 2
    bridge_cycles = [c for c in graph.cycles if c.id.startswith("adapter:")]
    assert len(bridge_cycles) == len(adapters) - 1
    assert all(len(c.edge_ids) == 6 for c in bridge_cycles)
    assert not any("triangle" in c.id for c in graph.cycles)
    a, b = df.lpu.codes
    with pytest.raises(ValueError, match="distinct IDs"):
        build_reference_lpu(a, "inter_XX", a)
    with pytest.raises(ValueError, match="exactly two"):
        build_reference_lpu(a, "inter_XX")
    with pytest.raises(ValueError, match="exactly two"):
        build_reference_lpu(a, "XX", b)


@pytest.mark.parametrize("profile", PROFILES)
def test_required_cycle_deletion_is_rejected(profile, constructions):
    lpu = constructions[profile, "XX"].lpu
    # Removing every bridge cycle is an unjustified deletion; both missing span
    # and extra encoded edge degrees are visible in the independent binary oracle.
    damaged = replace(lpu.graph, cycles=tuple(c for c in lpu.graph.cycles if ":bridge:" not in c.id))
    with pytest.raises(ValueError, match="unjustified cycle omission"):
        compile_deformation(lpu, graph=damaged)
    # At least one individually deleted published cycle is actually necessary.
    rejected = []
    for cycle in lpu.graph.cycles:
        candidate = replace(lpu.graph, cycles=tuple(c for c in lpu.graph.cycles if c.id != cycle.id))
        try:
            compile_deformation(lpu, graph=candidate)
        except ValueError as exc:
            assert "unjustified cycle omission" in str(exc)
            rejected.append(cycle.id)
    assert rejected


@pytest.mark.parametrize("profile", PROFILES)
def test_separate_X1_X7_measurements_rejected_for_XX(profile, constructions):
    df = constructions[profile, "XX"]
    code = df.lpu.codes[0]
    extra = tuple(embed(code.logical("X", label), df.group.register) for label in ("1", "7"))
    # Their parity is XX, but the actual input constraints have rank two.
    group = SignedGroup(df.group.ids + ("separate:X1", "separate:X7"), df.group.generators + extra)
    fixed = fixed_input_subspace(group, df.lpu.codes, df.lpu.ports.target.qubit_ids)
    assert fixed["rank"] == 2 and len(group.register) - independent.rank(group.rows) == 10
    expected = np.zeros(24, dtype=np.uint8)
    expected[[0, 6]] = 1
    with pytest.raises(ValueError, match="exactly one requested"):
        require_requested_constraint(fixed, expected)
    with pytest.raises(ValueError, match="exactly one requested"):
        compile_deformation(df.lpu, extra_checks=extra)


def test_signed_group_rejects_minus_identity_and_phase_only_span():
    z = Pauli.from_word("Z", ("block:q",))
    with pytest.raises(ValueError, match="-I"):
        SignedGroup(("z", "minus_z"), (z, z.with_phase(2)))
    with pytest.raises(ValueError, match="imaginary-phase"):
        SignedGroup(("imaginary_z",), (z.with_phase(1),))
    group = SignedGroup(("z",), (z,))
    with pytest.raises(ValueError, match="wrong signed phase"):
        group.witnesses((z.with_phase(2),))
    with pytest.raises(ValueError, match="noncommuting"):
        SignedGroup(("x", "z"), (Pauli.from_word("X", z.qubit_ids), z))
    with pytest.raises(ValueError, match="signed port product"):
        PortMap(("v",), (z.with_phase(2),), ("block",), z)
    with pytest.raises(ValueError, match="imaginary-phase"):
        PortMap(("v",), (z.with_phase(1),), ("block",), z)


def test_graph_negative_inputs_parallel_ids_and_generic_oracle():
    e0, e1 = Edge("e0", ("a", "b"), "toy"), Edge("e1", ("a", "b"), "toy")
    graph = AuxiliaryGraph(("a", "b"), (e0, e1), (Cycle("parallel", ("e0", "e1"), "toy"),), "toy")
    assert np.array_equal(graph.cycle_matrix, [[1, 1]])
    assert np.array_equal(full_cycle_basis(graph), [[1, 1]])
    reordered = replace(graph, edges=(e1, e0))
    assert set(reordered.edge_ids) == set(graph.edge_ids)
    assert reordered.cycles == graph.cycles
    with pytest.raises(ValueError, match="ambiguous"):
        graph.cycle_from_path("bad", ("a", "b", "a"), "toy")
    with pytest.raises(ValueError, match="duplicate"):
        replace(graph, edges=(e0, e0))
    with pytest.raises(ValueError, match="disconnected"):
        replace(graph, vertices=("a", "b", "isolated"))
    with pytest.raises(ValueError, match="nonzero boundary"):
        replace(graph, cycles=(Cycle("bad", ("e0",), "toy"),))
    with pytest.raises(ValueError, match="unknown cycle edge"):
        replace(graph, cycles=(Cycle("bad", ("missing",), "toy"),))
    with pytest.raises(ValueError, match="invalid edge"):
        Edge("loop", ("a", "a"), "toy")
    with pytest.raises(ValueError, match="unambiguous"):
        dress_boundaries(graph, np.array([[1, 1]], dtype=np.uint8), "paper_local")
    chain = AuxiliaryGraph(("a", "b", "c"), (e0, Edge("e2", ("b", "c"), "toy")), (), "toy")
    boundary = np.array([[1, 0, 1]], dtype=np.uint8)
    with pytest.raises(ValueError, match="no path fallback"):
        dress_boundaries(chain, boundary, "paper_local")
    generic = dress_boundaries(chain, boundary, "generic_gf2")
    assert generic.tolist() == [[1, 1]]
    with pytest.raises(ValueError, match="inconsistent"):
        dress_boundaries(chain, np.array([[1, 0, 0]], dtype=np.uint8), "generic_gf2")


@pytest.mark.parametrize("profile", PROFILES)
def test_generic_full_basis_is_separate_from_paper(profile, constructions):
    lpu = constructions[profile, "Y"].lpu
    generic = with_full_cycle_basis(lpu.graph)
    assert generic.profile == "generic_full_cycle_basis"
    assert len(generic.cycles) > len(lpu.graph.cycles)
    df = compile_deformation(lpu, graph=generic, dressing_profile="generic_gf2")
    assert df.merged_k == 11 and len(df.omitted_cycles) == 0
    assert df.fixed_input["row_basis"] == constructions[profile, "Y"].fixed_input["row_basis"]
    assert lpu.graph.profile.startswith("tdg_v1_") and len(lpu.graph.cycles) == (19 if profile == "gross" else 37)


def test_Y_port_sign_and_wrong_target_are_rejected(constructions):
    lpu = constructions["gross", "Y"].lpu
    ports = list(lpu.ports.ports)
    shared = lpu.graph.vertices.index(lpu.graph.shared_vertex)
    # Omitting i in Y=iXZ makes a non-Hermitian check; flipping its sign
    # gives -Y rather than the requested +Y even though binary support matches.
    for delta, message in ((3, "imaginary-phase"), (2, "signed port product")):
        corrupted = list(ports)
        corrupted[shared] = corrupted[shared].with_phase(delta)
        with pytest.raises(ValueError, match=message):
            replace(lpu.ports, ports=tuple(corrupted))
    code = lpu.codes[0]
    with pytest.raises(ValueError, match="signed port product"):
        replace(lpu.ports, target=code.logical("X", "1"))


def test_nonreference_logical_basis_is_rejected(constructions):
    code = constructions["gross", "X"].lpu.codes[0]
    lx, lz = list(code.logical_x), list(code.logical_z)
    # This remains a canonical CodeData basis with the same four base ports,
    # but its other labels no longer mean the literal published shifts.
    lx[1], lx[2] = lx[2], lx[1]
    lz[1], lz[2] = lz[2], lz[1]
    relabeled = replace(code, logical_x=tuple(lx), logical_z=tuple(lz))
    with pytest.raises(ValueError, match="literal reference shifts"):
        build_reference_lpu(relabeled, "X")
    negative = list(code.logical_x)
    negative[1] = negative[1].with_phase(2)
    with pytest.raises(ValueError, match="literal reference shifts"):
        build_half_graph(replace(code, logical_x=tuple(negative)), "l")
