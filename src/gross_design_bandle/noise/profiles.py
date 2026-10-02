"""A.7 equal-q, unequal independent and categorical comparison channels."""
from dataclasses import dataclass
import math

PROFILES = ('a7_uniform_expanded', 'paper_linearized_unequal',
            'standard_categorical_depolarizing')
MULTIPLICITIES = {'preparation':15, 'readout':15, 'idle':5, 'two_qubit':1}


@dataclass(frozen=True)
class NoiseProfile:
    name: str
    p: float

    def __post_init__(self):
        if self.name not in PROFILES:
            raise ValueError('unknown noise profile')
        if isinstance(self.p, bool) or not isinstance(self.p, (int, float)) or not math.isfinite(self.p) or not 0 <= self.p <= 1:
            raise ValueError('p must be finite in [0,1]')

    @property
    def independent(self):
        return self.name != 'standard_categorical_depolarizing'

    def probability(self, kind):
        m = MULTIPLICITIES[kind]
        return self.p/15 if self.name == 'a7_uniform_expanded' else m*self.p/15

    def copies(self, kind):
        return MULTIPLICITIES[kind] if self.name == 'a7_uniform_expanded' else 1


def parity_probability(probabilities):
    """Exact probability that independent equivalent Pauli copies have odd parity."""
    values = tuple(probabilities)
    if any(not math.isfinite(p) or not 0 <= p <= 1 for p in values):
        raise ValueError('invalid Bernoulli probability')
    return (1-math.prod(1-2*p for p in values))/2
