"""TdG v1 A.1/A.3 geometry and Fig. 13(b) algebraic adapter.

Independent implementation from frozen JSON and BB matrices, without importing
the delivered audit. No graph-expansion or distance claim is made here.
"""
from dataclasses import dataclass
import re

import numpy as np

from gross_design_bandle.algebra import gf2
from gross_design_bandle.algebra.pauli import Pauli
from gross_design_bandle.codes.reference_profiles import reference_fixture, reconstruct_reference_basis, FROZEN_SHA256
from gross_design_bandle.surgery.graph import AuxiliaryGraph, Edge
from gross_design_bandle.surgery.ports import PortMap, embed


def label_index(label, spec):
    match = re.fullmatch(r"(1|(?:x\d*)?(?:y\d*)?)([LR])", label)
    if not match or not match[1]:
        raise ValueError("invalid paper qubit label")
    coords = re.fullmatch(r"(?:x(\d*))?(?:y(\d*))?", match[1])
    if match[1] == "1":
        i = j = 0
    else:
        i = (int(coords[1]) if coords[1] else 1) if match[1].startswith("x") else 0
        j = (int(coords[2]) if coords[2] else 1) if "y" in match[1] else 0
    return spec.qubit_index(match[2], i, j)


def dual_index(q, spec, offset):
    side, cell = divmod(q, spec.cells)
    i, j = divmod(cell, spec.m)
    return spec.qubit_index("R" if side == 0 else "L", offset[0] - i, offset[1] - j)


def require_reference_code(code, fixture):
    if (code.spec.ell, code.spec.m, code.spec.A, code.spec.B) != (
        fixture["ell"], fixture["m"], tuple(map(tuple, fixture["A"])), tuple(map(tuple, fixture["B"]))):
        raise ValueError("code specification differs from reference LPU")
    lx, lz = reconstruct_reference_basis(fixture, code.spec)
    if (code.logical_labels != tuple(map(str, range(1, 13))) or
        not np.array_equal(code.lx, lx) or not np.array_equal(code.lz, lz) or
        any(p.phase != 0 for p in code.logical_x + code.logical_z)):
        raise ValueError("signed logical basis differs from literal reference shifts")


def validate_port_geometry(code):
    """The four numbered A.1 requirements plus pairwise adjacent intersections."""
    fixture = reference_fixture(code.spec.name)
    require_reference_code(code, fixture)
    base = (code.logical("X", "1"), code.logical("X", "7"),
            code.logical("Z", "1"), code.logical("Z", "7"))
    supports = [np.array(p.x, dtype=np.uint8) | np.array(p.z, dtype=np.uint8) for p in base]
    weight = 12 if code.spec.name == "gross" else 20
    if any(int(s.sum()) != weight for s in supports):
        raise ValueError("reference port weight differs")
    for i in range(4):
        for j in range(i):
            expected = int({i, j} in ({0, 2}, {1, 3}))
            if base[i].symplectic(base[j]) != expected or int((supports[i] & supports[j]).sum()) != expected:
                raise ValueError("A.1 pairing/disjoint support condition fails")
    # The literal shifted representatives must span both full logical quotients.
    if gf2.rank(np.vstack((code.hx, code.lx))) != gf2.rank(code.hx) + 12 or gf2.rank(np.vstack((code.hz, code.lz))) != gf2.rank(code.hz) + 12:
        raise ValueError("A.1 shifts do not generate twelve logical pairs")
    zx = [np.flatnonzero((code.hz @ s) > 0) for s in supports[:2]]
    xz = [np.flatnonzero((code.hx @ s) > 0) for s in supports[2:]]
    if set(zx[0]) & set(zx[1]) or set(xz[0]) & set(xz[1]):
        raise ValueError("A.1 adjacent-check sets overlap")
    # Check the claimed ZX-dual graph isomorphism on actual check supports.
    for x, z in ((supports[0], supports[3]), (supports[1], supports[2])):
        mapped_pairs = []
        for row in code.hz:
            hits = np.flatnonzero(row & x)
            if len(hits) not in (0, 2):
                raise ValueError("adjacent Z check does not meet port in a pair")
            if len(hits):
                mapped_pairs.append(tuple(sorted(dual_index(int(q), code.spec, fixture["dual_shift"]) for q in hits)))
        z_pairs = []
        for row in code.hx:
            hits = np.flatnonzero(row & z)
            if len(hits) not in (0, 2):
                raise ValueError("adjacent X check does not meet port in a pair")
            if len(hits):
                z_pairs.append(tuple(map(int, hits)))
        if sorted(mapped_pairs) != sorted(z_pairs):
            raise ValueError("ZX-dual adjacent-check graph differs")
    return {"weight": weight, "A1_pairing": True, "A1_shift_generation": True,
            "A1_support_intersections": True, "A1_disjoint_adjacent_checks": True,
            "ZX_dual_adjacent_graphs_isomorphic": True}


def build_half_graph(code, half):
    if half not in ("l", "r"):
        raise ValueError("unknown half LPU")
    fixture = reference_fixture(code.spec.name)
    require_reference_code(code, fixture)
    support = code.logical("X", "1" if half == "l" else "7").x
    vertex = lambda q: f"{code.block_id}:{half}:{code.qubit_ids[q]}"
    vertices = tuple(vertex(q) for q, bit in enumerate(support) if bit)
    edges = []
    for check_id, row in zip(code.spec.check_ids(code.block_id, "Z"), code.hz):
        hits = np.flatnonzero(row & support)
        if len(hits) == 2:
            edges.append(Edge(f"{code.block_id}:{half}:adj:{check_id}", tuple(vertex(int(q)) for q in hits),
                              f"arXiv:2506.03094v1 A.3 adjacent check {check_id}"))
        elif len(hits):
            raise ValueError("reference adjacent check intersection is not zero/two")
    for i, pair in enumerate(fixture[f"extra_edges_{half}"]):
        edges.append(Edge(f"{code.block_id}:{half}:expansion:{i}", tuple(vertex(label_index(s, code.spec)) for s in pair),
                          f"arXiv:2506.03094v1 Eq. {'41' if half == 'l' else '53'}"))
    graph = AuxiliaryGraph(vertices, tuple(edges), (), f"tdg_v1_{code.spec.name}_half_{half}")
    cycles = tuple(graph.cycle_from_path(f"{code.block_id}:{half}:cycle:{i}",
                                         [vertex(label_index(s, code.spec)) for s in path],
                                         f"reference/{code.spec.name}.json cycles_{half}[{i}]")
                   for i, path in enumerate(fixture[f"cycles_{half}"]))
    return AuxiliaryGraph(vertices, tuple(edges), cycles, graph.profile)


@dataclass(frozen=True)
class ReferenceLPU:
    codes: tuple
    operation: str
    graph: AuxiliaryGraph
    ports: PortMap
    ladders: tuple[tuple[str, ...], ...]
    geometry: dict

    @property
    def installed_full_census(self):
        if self.operation not in ("XX", "Y"):
            return None  # Active half/inter counts are not installed full-LPU counts.
        return {"edge_data_qubits": len(self.graph.edges),
                "vertex_measurement_qubits": len(self.graph.vertices) + 1,
                "cycle_measurement_qubits": len(self.graph.cycles),
                "shared_bell_measurement_qubits": 2,
                "total": len(self.graph.edges) + len(self.graph.vertices) + 1 + len(self.graph.cycles)}


def build_reference_lpu(code, operation, second_code=None):
    if operation not in ("X", "XX", "Y", "inter_XX"):
        raise ValueError("unknown reference measurement")
    if (operation == "inter_XX") != (second_code is not None):
        raise ValueError("inter measurement requires exactly two explicit blocks")
    if second_code is not None and (second_code.block_id == code.block_id or second_code.spec != code.spec):
        raise ValueError("inter blocks must have distinct IDs and the same code specification")
    fixture = reference_fixture(code.spec.name)
    geometry = validate_port_geometry(code)
    codes = (code,) if second_code is None else (code, second_code)
    register = tuple(q for c in codes for q in c.qubit_ids)
    left = build_half_graph(code, "l")
    vertex_for = lambda c, h, s: f"{c.block_id}:{h}:{c.qubit_ids[label_index(s, c.spec)]}"
    lp = tuple(vertex_for(code, "l", s) for s in fixture["bridge_l"])
    assignments = {}

    def add(v, c, q, axis):
        assignments.setdefault(v, []).append((c.qubit_ids[q], axis))

    def add_half(graph, c, half, axis, alias=lambda v: v):
        indices = {f"{c.block_id}:{half}:{q}": i for i, q in enumerate(c.qubit_ids)}
        for v in graph.vertices:
            q = indices[v]
            if axis == "Z":
                q = dual_index(q, c.spec, fixture["dual_shift"])
            add(alias(v), c, q, axis)

    if operation == "X":
        graph, ladders = left, (lp,)
        add_half(left, code, "l", "X")
        target = code.logical("X", "1")
    elif operation == "inter_XX":
        right = build_half_graph(second_code, "l")
        rp = tuple(vertex_for(second_code, "l", s) for s in fixture["bridge_l"])
        adapters = tuple(f"adapter:{code.block_id}:{second_code.block_id}:{i}" for i in range(len(lp)))
        edges = left.edges + right.edges + tuple(
            Edge(f"{c.block_id}:bridge:{i}", (v, a), "arXiv:2506.03094v1 Fig. 13(b); subdivided algebraic bridge")
            for i, a in enumerate(adapters) for c, v in ((code, lp[i]), (second_code, rp[i])))
        graph = AuxiliaryGraph(left.vertices + right.vertices + adapters, edges, left.cycles + right.cycles,
                               f"tdg_v1_{code.spec.name}_inter_XX_algebraic")
        new = tuple(graph.cycle_from_path(f"adapter:square:{i}",
                    (lp[i], lp[i+1], adapters[i+1], rp[i+1], rp[i], adapters[i], lp[i]),
                    "Fig. 13(b) derived six-edge joint cycle; no triangular bridge check") for i in range(len(lp)-1))
        graph = AuxiliaryGraph(graph.vertices, graph.edges, graph.cycles + new, graph.profile)
        ladders = (lp, rp)
        add_half(left, code, "l", "X")
        add_half(right, second_code, "l", "X")
        target = embed(code.logical("X", "1"), register) * embed(second_code.logical("X", "1"), register)
    else:
        right = build_half_graph(code, "r")
        shared_pair = (vertex_for(code, "l", fixture["identified_vertices"][0]),
                       vertex_for(code, "r", fixture["identified_vertices"][1]))
        shared = f"{code.block_id}:shared"
        alias = lambda v: shared if v in shared_pair else v
        vertices = tuple(dict.fromkeys(alias(v) for v in left.vertices + right.vertices))
        edges = tuple(Edge(e.id, tuple(alias(v) for v in e.endpoints), e.source) for e in left.edges + right.edges)
        lp = tuple(alias(v) for v in lp)
        rp = tuple(alias(vertex_for(code, "r", s)) for s in fixture["bridge_r"])
        edges += tuple(Edge(f"{code.block_id}:bridge:{i}", (u, v),
                            f"arXiv:2506.03094v1 Eq. {'39' if code.spec.name == 'gross' else '63'}")
                       for i, (u, v) in enumerate(zip(lp, rp)))
        graph = AuxiliaryGraph(vertices, edges, left.cycles + right.cycles,
                               f"tdg_v1_{code.spec.name}_full", shared)
        new = tuple(graph.cycle_from_path(f"{code.block_id}:bridge:square:{i}",
                    (lp[i], lp[i+1], rp[i+1], rp[i], lp[i]), "A.3 reference bridge square") for i in range(len(lp)-1))
        triangle = graph.cycle_from_path(f"{code.block_id}:bridge:triangle", (shared, lp[0], rp[0], shared),
                                        f"arXiv:2506.03094v1 Eq. {'40' if code.spec.name == 'gross' else '64'}")
        graph = AuxiliaryGraph(vertices, edges, graph.cycles + new + (triangle,), graph.profile, shared)
        ladders = (lp, rp)
        add_half(left, code, "l", "X", alias)
        add_half(right, code, "r", "X" if operation == "XX" else "Z", alias)
        target = code.logical("X", "1") * code.logical("X", "7") if operation == "XX" else code.logical("Y", "1")

    ports = []
    for v in graph.vertices:
        word = ["I"] * len(register)
        for q, axis in assignments.get(v, []):
            i = register.index(q)
            if word[i] == "I":
                word[i] = axis
            elif word[i] == "X" and axis == "Z":
                word[i] = "Y"  # The unique shared overlap is i X Z, not X Z.
            else:
                raise ValueError("unexpected overlapping reference ports")
        ports.append(Pauli.from_word("".join(word), register))
    geometry["fixture_sha256"] = FROZEN_SHA256[code.spec.name]
    return ReferenceLPU(codes, operation, graph, PortMap(graph.vertices, tuple(ports),
                        tuple(c.block_id for c in codes), target), ladders, geometry)
