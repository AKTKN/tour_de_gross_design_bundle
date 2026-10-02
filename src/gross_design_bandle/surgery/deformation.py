"""Compile and certify algebraic deformations, not measurement instruments."""
from dataclasses import dataclass
import json
from pathlib import Path

import numpy as np

from gross_design_bandle.algebra import gf2
from gross_design_bandle.algebra.certificates import SignedGroup
from gross_design_bandle.algebra.pauli import Pauli
from .cycles import omitted_cycle_complement
from .dressing import dress_boundaries
from .ports import embed


def fixed_input_subspace(group, codes, data_register):
    """Image of (G_deformed intersect data Paulis) in the INPUT logical quotient.

    This is a stabilizer constraint calculation. It is not proof of a physical
    instrument's coherence or outcome statistics (phase 03).
    """
    n, d = len(group.register), len(data_register)
    if group.register[:d] != data_register:
        raise ValueError("input data must precede edge register")
    rows = group.rows
    edge_rows = np.hstack((rows[:, d:n], rows[:, n+d:]))
    coefficients = gf2.kernel(edge_rows.T)
    intersection = gf2.matmul(coefficients, rows)
    data_rows = np.hstack((intersection[:, :d], intersection[:, n:n+d]))
    old = tuple(embed(p, data_register) for c in codes for p in c.checks)
    old_rows = np.array([p.x + p.z for p in old], dtype=np.uint8)
    if (gf2.matmul(data_rows[:, :d], old_rows[:, d:].T) ^ gf2.matmul(data_rows[:, d:], old_rows[:, :d].T)).any():
        raise ValueError("fixed data subgroup outside input centralizer")
    lx = tuple(embed(p, data_register) for c in codes for p in c.logical_x)
    lz = tuple(embed(p, data_register) for c in codes for p in c.logical_z)
    basis = lx + lz
    x = np.array([p.x for p in lz + lx], dtype=np.uint8)
    z = np.array([p.z for p in lz + lx], dtype=np.uint8)
    coords = gf2.matmul(data_rows[:, :d], z.T) ^ gf2.matmul(data_rows[:, d:], x.T)
    # Preserve actual generator coefficients and signed products for every
    # independent fixed logical direction, rather than exporting just a rank.
    selected, span = [], np.zeros((0, len(basis)), dtype=np.uint8)
    for i, row in enumerate(coords):
        if gf2.rank(np.vstack((span, row))) > len(span):
            selected.append(i)
            span = gf2.row_basis(np.vstack((span, row)))
    names = [f"{c.block_id}:X{label}" for c in codes for label in c.logical_labels]
    names += [f"{c.block_id}:Z{label}" for c in codes for label in c.logical_labels]
    return {"logical_basis": names, "rank": len(selected), "row_basis": span.tolist(),
            "edge_free_intersection_coefficients": coefficients.tolist(),
            "edge_free_intersection_logical_coordinates": coords.tolist(),
            "independent_witnesses": [{"logical_coordinates": coords[i].tolist(),
                "coefficients": coefficients[i].tolist(), "product": group.product(coefficients[i]).to_dict()}
                for i in selected]}


def require_requested_constraint(fixed, expected_coordinates):
    expected = gf2.binary(expected_coordinates, 1)
    actual = np.array(fixed["row_basis"], dtype=np.uint8).reshape(-1, len(expected))
    if not expected.any() or gf2.rank(actual) != 1 or not np.array_equal(actual[0], expected):
        raise ValueError("fixed input subspace differs from exactly one requested logical constraint")


@dataclass(frozen=True, eq=False)
class DeformedCode:
    lpu: object
    graph: object
    dressing_profile: str
    dressing: np.ndarray
    boundaries: np.ndarray
    group: SignedGroup
    omitted_cycles: np.ndarray
    omitted_witnesses: np.ndarray
    fixed_input: dict
    target_witness: np.ndarray

    def __post_init__(self):
        for field in ("dressing", "boundaries", "omitted_cycles", "omitted_witnesses", "target_witness"):
            object.__setattr__(self, field, gf2.readonly(getattr(self, field)))

    @property
    def merged_k(self):
        return len(self.group.register) - gf2.rank(self.group.rows)

    def to_certificate(self):
        n_old = sum(len(c.checks) for c in self.lpu.codes)
        old = tuple(embed(p, self.lpu.ports.target.qubit_ids) for c in self.lpu.codes for p in c.checks)
        return {"schema_version": 1,
            "scope": "Signed algebraic deformation only; no instrument, circuit, distance or sampling claim",
            "source": "arXiv:2506.03094v1 PDF A.1/A.3/A.4; immutable reference JSON",
            "code_ids": [c.id for c in self.lpu.codes], "operation": self.lpu.operation,
            "geometry": self.lpu.geometry, "graph": self.graph.to_dict(),
            "ladders": [list(path) for path in self.lpu.ladders],
            "installed_full_census": self.lpu.installed_full_census if self.graph.id == self.lpu.graph.id else None,
            "incidence": self.graph.incidence.tolist(), "selected_cycle_matrix": self.graph.cycle_matrix.tolist(),
            "ports": [{"vertex_id": v, "pauli": p.to_dict()} for v, p in zip(self.graph.vertices, self.lpu.ports.ports)],
            "target": self.lpu.ports.target.to_dict(), "dressing_profile": self.dressing_profile,
            "old_check_dressing": [{"check_id": self.group.ids[i], "old": p.to_dict(),
                "boundary": self.boundaries[i].tolist(), "edge_mask": self.dressing[i].tolist(),
                "dressed": self.group.generators[i].to_dict()} for i, p in enumerate(old)],
            "generator_order": list(self.group.ids),
            "generators": [p.to_dict() for p in self.group.generators],
            "omitted_cycle_certificates": [{"edge_mask": cycle.tolist(), "coefficients": witness.tolist(),
                "product_phase_mod4": self.group.product(witness).phase,
                "product": self.group.product(witness).to_dict()}
                for cycle, witness in zip(self.omitted_cycles, self.omitted_witnesses)],
            "identity_relations": [{"coefficients": relation.tolist(), "product_phase_mod4": self.group.product(relation).phase}
                for relation in self.group.relations],
            "target_product": {"coefficients": self.target_witness[0].tolist(),
                "product": self.group.product(self.target_witness[0]).to_dict()},
            "fixed_input_subspace": self.fixed_input,
            "ranks": {"input_k": sum(c.k for c in self.lpu.codes), "merged_k": self.merged_k,
                "deformed_stabilizer": gf2.rank(self.group.rows), "selected_cycles": gf2.rank(self.graph.cycle_matrix),
                "full_cycles": len(self.graph.edges) - len(self.graph.vertices) + 1,
                "omitted_cycle_complement": len(self.omitted_cycles)},
            "checks": {"BT_transpose_equals_boundary": True, "BC_transpose_zero": True,
                "commuting": True, "no_minus_I": True, "signed_vertex_product_equals_target": True,
                "all_omitted_cycles_in_combined_signed_span": True,
                "fixed_input_exactly_requested": True},
            "phase_convention": "i**phase X**x Z**z; +1 generator sector; actual outcomes/instrument are phase 03",
            "old_generator_count": n_old}

    def save_certificate(self, path):
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.to_certificate(), indent=2) + "\n")


def compile_deformation(lpu, *, graph=None, dressing_profile="paper_local", extra_checks=()):
    graph = lpu.graph if graph is None else graph
    if graph.vertices != lpu.ports.vertices:
        raise ValueError("graph and port vertex ordering differ")
    data = lpu.ports.target.qubit_ids
    edge_register = tuple(f"edge:{e}" for e in graph.edge_ids)
    register = data + edge_register
    if len(set(register)) != len(register):
        raise ValueError("data and edge registers overlap")
    d, e = len(data), len(edge_register)
    old = tuple(embed(p, data) for c in lpu.codes for p in c.checks)
    a = np.array([[p.symplectic(port) for port in lpu.ports.ports] for p in old], dtype=np.uint8)
    t = dress_boundaries(graph, a, dressing_profile)
    if not np.array_equal(gf2.matmul(graph.incidence, t.T), a.T):
        raise ValueError("invalid dressing boundary certificate")
    dressed = tuple(Pauli(p.phase, p.x + (0,)*e, p.z + tuple(row), register) for p, row in zip(old, t))
    vertices = tuple(Pauli(p.phase, p.x + tuple(b), p.z + (0,)*e, register)
                     for p, b in zip(lpu.ports.ports, graph.incidence))
    cycles = tuple(Pauli(0, (0,)*(d+e), (0,)*d + tuple(row), register) for row in graph.cycle_matrix)
    extra_checks = tuple(extra_checks)
    group = SignedGroup(tuple(i for c in lpu.codes for i in c.check_ids) +
                        tuple(f"vertex:{v}" for v in graph.vertices) + tuple(f"cycle:{c.id}" for c in graph.cycles) +
                        tuple(f"extra:{i}" for i in range(len(extra_checks))), dressed + vertices + cycles + extra_checks)
    target = embed(lpu.ports.target, register)
    target_witness = np.zeros((1, len(group.generators)), dtype=np.uint8)
    target_witness[0, len(old):len(old)+len(vertices)] = 1
    if group.product(target_witness[0]) != target:
        raise ValueError("signed vertex product differs from requested target")
    missing = omitted_cycle_complement(graph)
    missing_targets = tuple(Pauli(0, (0,)*(d+e), (0,)*d + tuple(row), register) for row in missing)
    try:
        witnesses = group.witnesses(missing_targets)
    except ValueError as exc:
        raise ValueError("unjustified cycle omission in combined signed group") from exc
    fixed = fixed_input_subspace(group, lpu.codes, data)
    basis = tuple(embed(p, data) for c in lpu.codes for p in c.logical_z) + tuple(embed(p, data) for c in lpu.codes for p in c.logical_x)
    expected = np.array([lpu.ports.target.symplectic(p) for p in basis], dtype=np.uint8)
    require_requested_constraint(fixed, expected)
    if len(register) - gf2.rank(group.rows) != sum(c.k for c in lpu.codes) - 1:
        raise ValueError("merged code dimension differs from one logical loss")
    return DeformedCode(lpu, graph, dressing_profile, t, a, group, missing, witnesses, fixed, target_witness)
