"""Explicit target-to-source data/check maps, verified against literal matrices.

qLDPC BBCode canonical coordinates are documented in src/qldpc/codes/quantum.py
at locked commit 60fc2cf465e880d6e64afacc933d33455d787bf4 (Apache-2.0).
This local adapter copies no donor implementation. It imports no donor backend.
"""
from __future__ import annotations

from dataclasses import dataclass
import json

import numpy as np

from gross_design_bandle.algebra import gf2
from .bb import CONVENTION, BBCodeSpec, check_matrices, integer, stable_id

SOURCE_CONVENTIONS = ("qldpc_xy", "qldpc_yx", "explicit_permuted_tdg")


def permutation(values, size):
    out = tuple(integer(v) for v in values)
    if sorted(out) != list(range(size)):
        raise ValueError("invalid permutation")
    return out


@dataclass(frozen=True)
class ConventionAdapter:
    spec: BBCodeSpec
    source_convention: str
    qubits: tuple[int, ...]
    x_checks: tuple[int, ...]
    z_checks: tuple[int, ...]
    target_convention: str = CONVENTION

    def __post_init__(self):
        if self.source_convention not in SOURCE_CONVENTIONS or self.target_convention != CONVENTION:
            raise ValueError("unknown source or target convention")
        for key, size in (("qubits", self.spec.n), ("x_checks", self.spec.cells), ("z_checks", self.spec.cells)):
            object.__setattr__(self, key, permutation(getattr(self, key), size))

    @property
    def id(self):
        return stable_id(self.to_dict())

    def adapt_checks(self, source_hx, source_hz):
        outputs = []
        for matrix, rows in ((source_hx, self.x_checks), (source_hz, self.z_checks)):
            matrix = gf2.binary(matrix, 2)
            if matrix.shape != (self.spec.cells, self.spec.n):
                raise ValueError("donor matrix shape mismatch")
            outputs.append(matrix[np.ix_(rows, self.qubits)])
        if any(not np.array_equal(out, expected) for out, expected in zip(outputs, check_matrices(self.spec))):
            raise ValueError("check/qubit map does not match declared BB convention")
        return tuple(gf2.readonly(out) for out in outputs)

    def adapt_pauli(self, pauli, source_ids, block_id):
        if pauli.qubit_ids != tuple(source_ids) or len(source_ids) != self.spec.n:
            raise ValueError("source register mismatch")
        return pauli.permuted(self.qubits, self.spec.register(block_id))

    def to_dict(self):
        return {"schema_version": 1, "spec": self.spec.to_dict(), "source_convention": self.source_convention,
                "target_convention": self.target_convention, "qubits": list(self.qubits),
                "x_checks": list(self.x_checks), "z_checks": list(self.z_checks)}

    @classmethod
    def from_dict(cls, data):
        if set(data) != {"schema_version", "spec", "source_convention", "target_convention", "qubits", "x_checks", "z_checks"} or data["schema_version"] != 1:
            raise ValueError("invalid ConventionAdapter schema")
        return cls(BBCodeSpec.from_dict(data["spec"]), **{key: val for key, val in data.items() if key not in ("schema_version", "spec")})

    def to_json(self):
        return json.dumps(self.to_dict(), sort_keys=True)

    @classmethod
    def from_json(cls, text):
        return cls.from_dict(json.loads(text))


def qldpc_adapter(spec, symbol_order=("x", "y")):
    """Specify the *actual* donor orders dict insertion order, then verify matrices."""
    symbol_order = tuple(symbol_order)
    if symbol_order not in (("x", "y"), ("y", "x")):
        raise ValueError("unknown qLDPC symbol order")
    cells = tuple(i * spec.m + j if symbol_order == ("x", "y") else j * spec.ell + i
                  for i in range(spec.ell) for j in range(spec.m))
    qubits = cells + tuple(spec.cells + i for i in cells)
    return ConventionAdapter(spec, "qldpc_" + "".join(symbol_order), qubits, cells, cells)
