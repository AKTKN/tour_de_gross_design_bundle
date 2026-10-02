"""Signed commuting data ports, with explicit block identity."""
from dataclasses import dataclass

from gross_design_bandle.algebra.pauli import Pauli


def product(paulis, register):
    result = Pauli.identity(register)
    for p in paulis:
        result = result * p
    return result


def embed(pauli, register):
    """Embed into a larger named register without changing the XZ phase."""
    if not set(pauli.qubit_ids) <= set(register):
        raise ValueError("embedding register does not contain source")
    indices = {q: i for i, q in enumerate(pauli.qubit_ids)}
    return Pauli(pauli.phase, tuple(pauli.x[indices[q]] if q in indices else 0 for q in register),
                 tuple(pauli.z[indices[q]] if q in indices else 0 for q in register), tuple(register))


@dataclass(frozen=True)
class PortMap:
    vertices: tuple[str, ...]
    ports: tuple[Pauli, ...]
    block_ids: tuple[str, ...]
    target: Pauli

    def __post_init__(self):
        for field in ("vertices", "ports", "block_ids"):
            object.__setattr__(self, field, tuple(getattr(self, field)))
        if len(set(self.vertices)) != len(self.vertices) or len(self.vertices) != len(self.ports):
            raise ValueError("port vertex correspondence differs")
        if not self.block_ids or len(set(self.block_ids)) != len(self.block_ids):
            raise ValueError("blocks must have distinct explicit IDs")
        if any(q.split(":", 1)[0] not in self.block_ids for q in self.target.qubit_ids):
            raise ValueError("data register has unknown block ID")
        self.target.require_hermitian()
        for i, p in enumerate(self.ports):
            p.require_hermitian()
            if p.qubit_ids != self.target.qubit_ids or any(not p.commutes(q) for q in self.ports[:i]):
                raise ValueError("noncommuting or mismatched ports")
        if product(self.ports, self.target.qubit_ids) != self.target:
            raise ValueError("signed port product differs from target")
