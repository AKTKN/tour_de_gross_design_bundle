"""Named single-block Clifford basis and centralizer action generators."""
from dataclasses import dataclass
import numpy as np
from gross_design_bandle.algebra import gf2
from gross_design_bandle.algebra.pauli import Pauli
from gross_design_bandle.surgery.ports import embed


@dataclass(frozen=True)
class LogicalBasisAdapter:
    target: str
    x: tuple[Pauli, ...]
    z: tuple[Pauli, ...]
    x_names: tuple[str, ...]
    z_names: tuple[str, ...]
    abstract_cliffords: tuple

    @classmethod
    def two_blocks(cls, blocks, profile='full_two_block_centralizer_K47'):
        if profile == 'published_inter_K23':
            raise ValueError('published inter K23 rows unresolved O1; no subset is inferred')
        if profile != 'full_two_block_centralizer_K47':
            raise ValueError('unknown inter observable profile')
        a, b = blocks.codes
        x, z = list(blocks.logical_x), list(blocks.logical_z)
        xn = [f'{c.block_id}:X{i}' for c in blocks.codes for i in c.logical_labels]
        zn = [f'{c.block_id}:Z{i}' for c in blocks.codes for i in c.logical_labels]
        # Logical CX(a:1,b:1): designated X becomes the product, and the
        # retained b:Z1 becomes Z1 tensor Z1. No individual X1 readout.
        j = a.k
        x[0] = x[0]*x[j]; z[j] = z[0]*z[j]
        xn[0] = f'{a.block_id}:X1*{b.block_id}:X1'
        zn[j] = f'{a.block_id}:Z1*{b.block_id}:Z1'
        for i in range(blocks.k):
            for k in range(blocks.k):
                if x[i].symplectic(z[k]) != int(i == k) or x[i].symplectic(x[k]) or z[i].symplectic(z[k]):
                    raise ValueError('inter adapter is not canonical')
        return cls('inter_XX', tuple(x), tuple(z), tuple(xn), tuple(zn),
                   (('CX', f'{a.block_id}:1', f'{b.block_id}:1'),))

    @classmethod
    def single_block(cls, code, target='memory'):
        if target not in ('memory', 'X1', 'X1*X7', 'Y1'):
            raise ValueError('unknown single-block logical target; inter K23 is unresolved O1')
        if target == 'X1*X7' and '7' not in code.logical_labels:
            raise ValueError('logical X7 unavailable')
        x, z = list(code.logical_x), list(code.logical_z)
        xn = [f'{code.block_id}:X{i}' for i in code.logical_labels]
        zn = [f'{code.block_id}:Z{i}' for i in code.logical_labels]
        cliffords = ()
        if target == 'X1*X7':
            a, b = code.logical_labels.index('1'), code.logical_labels.index('7')
            x[a] = x[a]*x[b]; z[b] = z[a]*z[b]
            xn[a] = f'{code.block_id}:X1*X7'; zn[b] = f'{code.block_id}:Z1*Z7'
            cliffords = (('CX', '1', '7'),)
        elif target == 'Y1':
            a = code.logical_labels.index('1')
            x[a] = (x[a]*z[a]).with_phase(1).require_hermitian()
            xn[a] = f'{code.block_id}:Y1'
            cliffords = (('S', '1'),)
        # Exact symplectic validation, including physical Hermitian Y signs.
        for i in range(code.k):
            for j in range(code.k):
                if x[i].symplectic(z[j]) != int(i == j) or x[i].symplectic(x[j]) or z[i].symplectic(z[j]):
                    raise ValueError('adapter is not a canonical logical Clifford basis')
        return cls(target, tuple(x), tuple(z), tuple(xn), tuple(zn), cliffords)

    @property
    def generators(self):
        return self.x + (self.z if self.target == 'memory' else self.z[1:])

    @property
    def names(self):
        return self.x_names + (self.z_names if self.target == 'memory' else self.z_names[1:])

    def certificate(self, code):
        logical = code.logical_z + code.logical_x
        coords = np.array([[p.symplectic(q) for q in logical] for p in self.generators], dtype=np.uint8)
        expected = 2*code.k-int(self.target != 'memory')
        if gf2.rank(coords) != expected:
            raise ValueError('logical action rank mismatch')
        if self.target != 'memory' and any(not p.commutes(self.x[0]) for p in self.generators):
            raise ValueError('generator outside measured centralizer')
        return {'profile': 'full_two_block_centralizer_K47' if self.target == 'inter_XX' else 'single_block_a7_ideal_v1', 'target': self.target,
                'abstract_cliffords': list(self.abstract_cliffords), 'rank': expected,
                'logical_coordinates': coords.tolist(), 'names': list(self.names),
                'physical_generators': [p.to_dict() for p in self.generators],
                'scope': 'named full input centralizer; physical validation is separate',
                'paper_exact': False, 'O1': 'published inter K23 rows unresolved' if self.target == 'inter_XX' else None}


def correlation(pauli, axis, ref, register):
    return embed(pauli, register)*embed(Pauli.from_word(axis, (ref,)), register)
