"""Prepare bounded A.8 Eq. (84) inputs; this module never invokes a solver.

Spatial jobs use a complete quotient basis of the deformed stabilizer code.
Temporal constraints omit vertex checks and do not add the measured target.
"""
from dataclasses import dataclass
import numpy as np
from gross_design_bandle.algebra import gf2
from gross_design_bandle.algebra.pauli import Pauli
from gross_design_bandle.codes.blocks import CodeBlocks
from gross_design_bandle.flows.observables import LogicalBasisAdapter
from gross_design_bandle.surgery.ports import embed


def symplectic_rows(rows):
    n = rows.shape[1] // 2
    return np.hstack((rows[:, n:], rows[:, :n]))


@dataclass(frozen=True)
class PhenomenologicalJobs:
    register: tuple
    spatial_M: np.ndarray
    spatial_q: np.ndarray
    temporal_M: np.ndarray
    temporal_q: np.ndarray
    generator_ids: tuple
    temporal_ids: tuple

    def check_witness(self, kind, q_index, bits):
        if kind not in ('spatial', 'temporal'):
            raise ValueError('unknown phenomenological job kind')
        M, qs = (self.spatial_M, self.spatial_q) if kind == 'spatial' else (self.temporal_M, self.temporal_q)
        if type(q_index) is not int or q_index not in range(len(qs)):
            raise ValueError('invalid job index')
        bits = gf2.binary(bits, 1)
        n = len(self.register)
        if len(bits) != 2*n:
            raise ValueError('witness register mismatch')
        if gf2.matmul(symplectic_rows(M), bits[:, None]).any():
            raise ValueError('witness violates commutation constraint')
        if not gf2.matmul(symplectic_rows(qs[q_index:q_index+1]), bits[:, None])[0, 0]:
            raise ValueError('witness fails target anticommutation')
        return {'verified': True, 'weight': int((bits[:n] | bits[n:]).sum()),
                'bound_type': 'upper bound only; no solver lower bound'}

    def manifest(self):
        return {'schema_version': 1, 'source': 'arXiv:2506.03094v1 PDF A.8 Eq. (84)',
                'register': list(self.register), 'spatial_generator_ids': list(self.generator_ids),
                'temporal_generator_ids': list(self.temporal_ids),
                'spatial_jobs': len(self.spatial_q), 'temporal_jobs': 1,
                'constraints': 'M J p^T = 0; q J p^T = 1 over GF(2)',
                'objective': 'sum_i (x_i OR z_i); Y counts once',
                'MILP': {'variables': 'binary x_i,z_i,w_i; integer parity slack t_j',
                         'weight_constraints': ['w_i >= x_i', 'w_i >= z_i', 'w_i <= x_i+z_i'],
                         'slack_bounds': '0 <= t_r <= floor(row_weight/2); target uses floor((row_weight-1)/2)',
                         'parity_constraints': 'sum_j (M J)[r,j] p_j - 2t_r = 0; sum_j (q J)[j] p_j - 2t_q = 1'},
                'budget': {'aggregate_wall_seconds': 120, 'per_job_wall_seconds': 5,
                           'per_job_node_limit': 1000, 'aggregate_node_limit': 10000,
                           'workers': 1, 'automatic_retries': 0},
                'result_required': ['optimum_or_incumbent', 'solver_lower_bound', 'gap',
                                    'termination_reason', 'witness_bits', 'independent_witness_check'],
                'status': 'prepared_not_launched', 'solver_backend': None,
                'lower_bound': None, 'distance_claim': None,
                'circuit_distance_search': False}


def prepare_phenomenological_jobs(deformation):
    df = deformation; codes = df.lpu.codes
    code = CodeBlocks(codes) if len(codes) == 2 else codes[0]
    target = {'X': 'X1', 'XX': 'X1*X7', 'Y': 'Y1', 'inter_XX': 'inter_XX'}[df.lpu.operation]
    basis = LogicalBasisAdapter.two_blocks(code) if len(codes) == 2 else LogicalBasisAdapter.single_block(code, target)
    n = len(df.group.register); d = len(df.lpu.ports.target.qubit_ids)
    qs = []
    # Every retained input centralizer generator can be dressed by edge Z
    # to commute with vertices. The omitted target is already a stabilizer.
    for p in basis.generators[1:]:
        boundary = np.array([p.symplectic(port) for port in df.lpu.ports.ports], dtype=np.uint8)
        dressing = gf2.solve(df.graph.incidence, boundary[:, None])[:, 0]
        q = Pauli(p.phase, p.x + (0,)*(n-d), p.z + tuple(dressing), df.group.register)
        if any(not q.commutes(g) for g in df.group.generators):
            raise ValueError('spatial quotient dressing failed')
        qs.append(q.x + q.z)
    spatial = gf2.binary(qs, 2)
    rows = df.group.rows
    if len(qs) != 2*df.merged_k or gf2.rank(np.vstack((rows, spatial))) != gf2.rank(rows) + len(qs):
        raise ValueError('spatial quotient is incomplete')
    selected = [i for i, id in enumerate(df.group.ids) if not id.startswith('vertex:')]
    target = embed(df.lpu.ports.target, df.group.register)
    temporal_q = np.array([target.x + target.z], dtype=np.uint8)
    # Detect accidental inclusion of the target in the commuting span.
    gf2.solve(np.vstack((symplectic_rows(rows[selected]), symplectic_rows(temporal_q))),
              np.array([[0]]*len(selected)+[[1]], dtype=np.uint8))
    return PhenomenologicalJobs(df.group.register, gf2.readonly(rows), gf2.readonly(spatial),
                               gf2.readonly(rows[selected]), gf2.readonly(temporal_q),
                               df.group.ids, tuple(df.group.ids[i] for i in selected))
