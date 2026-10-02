"""Exact signed Abelian-group witnesses, including all identity relations."""
from dataclasses import dataclass

import numpy as np

from . import gf2
from .pauli import Pauli


@dataclass(frozen=True, eq=False)
class SignedGroup:
    ids: tuple[str, ...]
    generators: tuple[Pauli, ...]

    def __post_init__(self):
        object.__setattr__(self, "ids", tuple(self.ids))
        object.__setattr__(self, "generators", tuple(self.generators))
        if not self.generators or len(self.ids) != len(self.generators) or len(set(self.ids)) != len(self.ids) or any(not i for i in self.ids):
            raise ValueError("invalid signed generator IDs")
        register = self.generators[0].qubit_ids
        for p in self.generators:
            p.require_hermitian()
            if p.qubit_ids != register:
                raise ValueError("signed generator registers differ")
        rows = self.rows
        n = len(register)
        if (gf2.matmul(rows[:, :n], rows[:, n:].T) ^ gf2.matmul(rows[:, n:], rows[:, :n].T)).any():
            raise ValueError("noncommuting signed generators")
        # A basis of the relation kernel is sufficient: commuting Hermitian
        # identity products have real signs, and relation signs form a character.
        for relation in self.relations:
            if self.product(relation).phase != 0:
                raise ValueError("signed stabilizer group generates -I")

    @property
    def register(self):
        return self.generators[0].qubit_ids

    @property
    def rows(self):
        return gf2.readonly(np.array([p.x + p.z for p in self.generators], dtype=np.uint8))

    @property
    def relations(self):
        return gf2.readonly(gf2.kernel(self.rows.T))

    def product(self, coefficients):
        coefficients = gf2.binary(coefficients, 1)
        if len(coefficients) != len(self.generators):
            raise ValueError("signed witness length differs")
        n = len(self.register)
        x, z = np.zeros(n, dtype=np.uint8), np.zeros(n, dtype=np.uint8)
        phase = 0
        for i in np.flatnonzero(coefficients):
            p = self.generators[int(i)]
            px, pz = np.array(p.x, dtype=np.uint8), np.array(p.z, dtype=np.uint8)
            phase = (phase + p.phase + 2 * int(z @ px)) % 4
            x ^= px
            z ^= pz
        return Pauli(phase, tuple(x), tuple(z), self.register)

    def witnesses(self, targets):
        targets = tuple(targets)
        if any(p.qubit_ids != self.register for p in targets):
            raise ValueError("span target register differs")
        rows = np.array([p.x + p.z for p in targets], dtype=np.uint8).reshape(-1, 2 * len(self.register))
        coefficients = gf2.span_coefficients(self.rows, rows)
        for target, witness in zip(targets, coefficients):
            if self.product(witness) != target:
                raise ValueError("span witness has wrong signed phase")
        return gf2.readonly(coefficients)
