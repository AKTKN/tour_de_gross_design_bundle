"""An explicit tensor product view; never a new BB code specification."""
from dataclasses import dataclass
from gross_design_bandle.surgery.ports import embed


@dataclass(frozen=True)
class CodeBlocks:
    codes: tuple

    def __post_init__(self):
        if not isinstance(self.codes, (tuple, list)):
            raise ValueError('inter scope requires a sequence of two explicit blocks')
        object.__setattr__(self, 'codes', tuple(self.codes))
        if len(self.codes) != 2 or len({c.block_id for c in self.codes}) != 2:
            raise ValueError('two distinct explicit block IDs required')
        if any(c.spec.name not in ('gross', 'two_gross') for c in self.codes) or self.codes[0].spec != self.codes[1].spec:
            raise ValueError('inter physical profile requires two blocks of the same reference code')

    @property
    def block_id(self):
        return '+'.join(c.block_id for c in self.codes)

    @property
    def qubit_ids(self):
        return tuple(q for c in self.codes for q in c.qubit_ids)

    @property
    def k(self):
        return sum(c.k for c in self.codes)

    @property
    def check_ids(self):
        return tuple(id for c in self.codes for id in c.check_ids)

    def _paulis(self, field):
        return tuple(embed(p, self.qubit_ids) for c in self.codes for p in getattr(c, field))

    @property
    def checks(self):
        return self._paulis('checks')

    @property
    def logical_x(self):
        return self._paulis('logical_x')

    @property
    def logical_z(self):
        return self._paulis('logical_z')
