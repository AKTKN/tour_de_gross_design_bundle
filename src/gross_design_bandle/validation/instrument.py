"""Tiny branchwise matrix contraction, independent of the cut-frame formula.

Matrices are numerical complex amplitudes of exact Pauli/projector maps (no
sampling); tests use explicit tolerances. GF(2) and Pauli signs remain exact.
"""
from dataclasses import dataclass

import numpy as np

from gross_design_bandle.algebra import gf2
from gross_design_bandle.algebra.pauli import Pauli
from gross_design_bandle.surgery.frame import Parity


def pauli_matrix(pauli):
    if len(pauli.x) > 10:
        raise ValueError("dense ideal oracle limited to ten qubits")
    x = np.array([[0, 1], [1, 0]], dtype=complex)
    z = np.diag([1, -1]).astype(complex)
    result = np.array([[1]], dtype=complex)
    for a, b in zip(pauli.x, pauli.z):
        result = np.kron(result, np.linalg.matrix_power(x, a) @ np.linalg.matrix_power(z, b))
    return (1j**pauli.phase) * result


def dense_branch(protocol, vertex_bits, edge_bits, *, rounds=1):
    """<z| product of measured vertex/cycle projectors |0>_E.

    Generic graph oracle only: original-code/dressed checks require an encoded
    input and are exercised separately by stabilizer tests. Repeated vertices
    here have the same outcome, as required for noiseless branches.
    """
    if protocol.deformation is not None:
        raise ValueError("dense graph oracle does not omit encoded checks silently")
    s, z = gf2.binary(vertex_bits, 1), gf2.binary(edge_bits, 1)
    d, e = len(protocol.ports.target.x), len(protocol.graph.edges)
    if len(s) != len(protocol.graph.vertices) or len(z) != e:
        raise ValueError("branch dimensions differ")
    if d+e > 8:
        raise ValueError("tiny branch oracle limited to eight total qubits")
    if not isinstance(rounds, int) or isinstance(rounds, bool) or rounds < 1:
        raise ValueError("invalid round count")
    state = np.zeros((2**(d+e), 2**d), dtype=complex)
    state[np.arange(2**d) * 2**e, np.arange(2**d)] = 1
    for _ in range(rounds):
        for p, bit in zip(protocol.vertices, s):
            state = (state + (-1)**int(bit) * pauli_matrix(p) @ state)/2
        for p in protocol.cycles:
            state = (state + pauli_matrix(p) @ state)/2
    edge_index = sum(int(bit) << (e-1-i) for i, bit in enumerate(z))
    return state.reshape(2**d, 2**e, 2**d)[:, edge_index, :]


def bell_readout_branch(left, right, bits):
    """Actual ideal Bell control/readout contraction for disjoint data halves.

    Prepare (|00>+|11>)/sqrt(2), independently control the two data Paulis,
    and read both ancillas in X. Each branch equals Pi_(b0 XOR b1)/sqrt(2).
    This is a check-template oracle, not a scheduled/noisy Bell implementation.
    """
    left.require_hermitian()
    right.require_hermitian()
    left._compatible(right)
    if any((a or b) and (c or d) for a, b, c, d in zip(left.x, left.z, right.x, right.z)):
        raise ValueError("Bell halves overlap data")
    b = gf2.binary(bits, 1)
    if len(b) != 2:
        raise ValueError("Bell readout requires two bits")
    n = len(left.x)
    if n > 6:
        raise ValueError("tiny Bell oracle limited to six data qubits")
    identity = np.eye(2**n, dtype=complex)
    # Matrix-valued ancilla wavefunction: control-a0 left, control-a1 right.
    wave = np.zeros((2, 2, 2**n, 2**n), dtype=complex)
    wave[0, 0] = identity / np.sqrt(2)
    wave[1, 1] = identity / np.sqrt(2)
    for a0 in range(2):
        for a1 in range(2):
            if a0:
                wave[a0, a1] = pauli_matrix(left) @ wave[a0, a1]
            if a1:
                wave[a0, a1] = pauli_matrix(right) @ wave[a0, a1]
    x0 = np.array([1, (-1)**int(b[0])]) / np.sqrt(2)
    x1 = np.array([1, (-1)**int(b[1])]) / np.sqrt(2)
    return np.einsum("a,b,abij->ij", x0, x1, wave)


@dataclass(frozen=True)
class IdealBellCheck:
    """Named two-readout check oracle; no physical schedule or noise policy."""
    left: Pauli
    right: Pauli
    outcome_ids: tuple[str, str]
    ideal_only = True

    def __post_init__(self):
        object.__setattr__(self, "outcome_ids", tuple(self.outcome_ids))
        if len(self.outcome_ids) != 2:
            raise ValueError("Bell check requires two outcome IDs")
        Parity(self.outcome_ids)
        self.left.require_hermitian()
        self.right.require_hermitian()
        self.left._compatible(self.right)
        if any((a or b) and (c or d) for a, b, c, d in zip(self.left.x, self.left.z, self.right.x, self.right.z)):
            raise ValueError("Bell halves overlap data")

    @property
    def readout(self):
        return Parity(self.outcome_ids)

    def branch(self, outcomes):
        return bell_readout_branch(self.left, self.right, [Parity((i,)).evaluate(outcomes) for i in self.outcome_ids])

    def to_dict(self):
        return {"ideal_only": True, "left": self.left.to_dict(), "right": self.right.to_dict(),
                "physical_outcome_ids": list(self.outcome_ids), "algebraic_readout": self.readout.to_dict()}
