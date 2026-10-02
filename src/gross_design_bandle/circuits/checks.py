"""Physical signed check identities, independent of their schedules.

Native RX/MX, CZ and CY each occupy one tick. This is an explicitly named
construction policy, not a certification of the paper's noisy gate catalogue.
"""
from dataclasses import dataclass
from gross_design_bandle.algebra.pauli import Pauli


def support(pauli):
    pauli.require_hermitian()
    return {q: 'Y' if x and z else 'X' if x else 'Z'
            for q, x, z in zip(pauli.qubit_ids, pauli.x, pauli.z) if x or z}


@dataclass(frozen=True)
class Check:
    id: str
    pauli: Pauli
    ancillas: tuple[str, ...]
    parts: tuple[tuple[str, ...], ...]
    kind: str = 'single'
    basis: str = 'X'

    def __post_init__(self):
        self.pauli.require_hermitian()
        if self.kind not in ('single', 'bell') or self.basis not in ('X', 'Z'):
            raise ValueError('unknown physical check policy')
        size = 2 if self.kind == 'bell' else 1
        if len(self.ancillas) != size or len(self.parts) != size or len(set(self.ancillas)) != size:
            raise ValueError('wrong physical ancilla count')
        if not self.id or any(not a or a in self.pauli.qubit_ids for a in self.ancillas):
            raise ValueError('ancillas must be distinct from data')
        flattened = tuple(q for part in self.parts for q in part)
        if len(set(flattened)) != len(flattened) or set(flattened) != set(support(self.pauli)):
            raise ValueError('Bell halves overlap or do not partition check support')
        if self.basis == 'Z' and (self.kind == 'bell' or set(support(self.pauli).values()) - {'Z'}):
            raise ValueError('Z readout policy is only for pure Z single checks')

    @classmethod
    def single(cls, id, pauli, *, basis='X', ancilla=None):
        return cls(id, pauli, (ancilla or f'anc:{id}',), (tuple(support(pauli)),), basis=basis)

    @classmethod
    def bell(cls, id, pauli, left, *, ancillas=None):
        left = tuple(left)
        return cls(id, pauli, ancillas or (f'anc:{id}:l', f'anc:{id}:r'),
                   (left, tuple(q for q in support(pauli) if q not in left)), 'bell')

    @property
    def negative(self):
        return (self.pauli.phase - sum(x*z for x,z in zip(self.pauli.x,self.pauli.z))) % 4 == 2

    def interaction(self, q):
        a = next(a for a, part in zip(self.ancillas, self.parts) if q in part)
        axis = support(self.pauli)[q]
        if self.basis == 'Z':
            return 'CX', (q, a)
        return {'X': 'CX', 'Y': 'CY', 'Z': 'CZ'}[axis], (a, q)

    def to_dict(self):
        return {'id': self.id, 'pauli': self.pauli.to_dict(), 'ancillas': list(self.ancillas),
                'parts': [list(p) for p in self.parts], 'kind': self.kind, 'basis': self.basis}
