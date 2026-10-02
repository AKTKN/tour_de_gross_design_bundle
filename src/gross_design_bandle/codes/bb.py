"""BB matrices and canonical CSS logical quotients, constructed over GF(2)."""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from numbers import Integral
import re

import numpy as np

from gross_design_bandle.algebra import gf2
from gross_design_bandle.algebra.pauli import Pauli

CONVENTION = "tdg_v1_xy_LR_plus_X_minus_Z"
FIXTURE_CONVENTION = "X check at (i,j) has L support (i,j)+A and R support (i,j)+B; Z check has L support (i,j)-B and R support (i,j)-A. Coordinates reduced modulo ell,m."


def stable_id(data):
    return sha256(json.dumps(data, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def integer(value):
    if not isinstance(value, Integral) or isinstance(value, bool):
        raise ValueError("expected integer coordinate")
    return int(value)


def name_id(value):
    if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9_.-]+", value):
        raise ValueError("invalid name or block ID")
    return value


def terms(value):
    out = []
    for pair in value:
        if len(pair) != 2:
            raise ValueError("coordinate must have two components")
        out.append(tuple(integer(v) for v in pair))
    return tuple(out)


@dataclass(frozen=True)
class BBCodeSpec:
    name: str
    ell: int
    m: int
    A: tuple[tuple[int, int], ...]
    B: tuple[tuple[int, int], ...]
    source: str
    convention: str = CONVENTION

    def __post_init__(self):
        name_id(self.name)
        if integer(self.ell) < 1 or integer(self.m) < 1:
            raise ValueError("torus orders must be positive")
        if self.convention != CONVENTION:
            raise ValueError("unknown BB convention")
        if not isinstance(self.source, str) or not self.source:
            raise ValueError("missing source provenance")
        object.__setattr__(self, "ell", int(self.ell))
        object.__setattr__(self, "m", int(self.m))
        object.__setattr__(self, "A", terms(self.A))
        object.__setattr__(self, "B", terms(self.B))
        for polynomial in (self.A, self.B):
            reduced = [(i % self.ell, j % self.m) for i, j in polynomial]
            if not polynomial or len(set(reduced)) != len(reduced):
                raise ValueError("empty or duplicate polynomial terms on torus")

    @property
    def cells(self):
        return self.ell * self.m

    @property
    def n(self):
        return 2 * self.cells

    @property
    def id(self):
        return stable_id(self.to_dict())

    def qubit_index(self, side, i, j):
        if side not in ("L", "R"):
            raise ValueError("unknown qubit side")
        return (side == "R") * self.cells + (integer(i) % self.ell) * self.m + integer(j) % self.m

    def register(self, block_id):
        name_id(block_id)
        return tuple(f"{block_id}:{s}:{i}:{j}" for s in ("L", "R") for i in range(self.ell) for j in range(self.m))

    def check_ids(self, block_id, sector):
        name_id(block_id)
        if sector not in ("X", "Z"):
            raise ValueError("unknown check sector")
        return tuple(f"{block_id}:{sector}:{i}:{j}" for i in range(self.ell) for j in range(self.m))

    def to_dict(self):
        return {"schema_version": 1, "name": self.name, "ell": self.ell, "m": self.m,
                "A": [list(t) for t in self.A], "B": [list(t) for t in self.B],
                "source": self.source, "convention": self.convention}

    @classmethod
    def from_dict(cls, data):
        if set(data) != {"schema_version", "name", "ell", "m", "A", "B", "source", "convention"} or data["schema_version"] != 1:
            raise ValueError("invalid BBCodeSpec schema")
        return cls(**{key: val for key, val in data.items() if key != "schema_version"})

    def to_json(self):
        return json.dumps(self.to_dict(), sort_keys=True)

    @classmethod
    def from_json(cls, text):
        return cls.from_dict(json.loads(text))


def check_matrices(spec):
    # Row t is check (i,j). Columns are side-major, then i*m+j.
    a, b = (np.zeros((spec.cells, spec.cells), dtype=np.uint8) for _ in range(2))
    for matrix, polynomial in ((a, spec.A), (b, spec.B)):
        for i in range(spec.ell):
            for j in range(spec.m):
                for dx, dy in polynomial:
                    matrix[i * spec.m + j, ((i + dx) % spec.ell) * spec.m + (j + dy) % spec.m] ^= 1
    return np.hstack((a, b)), np.hstack((b.T, a.T))


def derive_css_logicals(hx, hz):
    lx = gf2.quotient_basis(gf2.kernel(hz), hx)
    lz = gf2.quotient_basis(gf2.kernel(hx), hz)
    # Canonicalize Z representatives so Lx Lz^T=I without changing X labels.
    lz = gf2.matmul(gf2.inverse(gf2.matmul(lx, lz.T)).T, lz)
    return lx, lz


@dataclass(frozen=True, eq=False)
class CodeData:
    spec: BBCodeSpec
    block_id: str
    hx: np.ndarray
    hz: np.ndarray
    logical_x: tuple[Pauli, ...]
    logical_z: tuple[Pauli, ...]
    logical_labels: tuple[str, ...]
    basis_source: str

    def __post_init__(self):
        name_id(self.block_id)
        object.__setattr__(self, "hx", gf2.readonly(self.hx))
        object.__setattr__(self, "hz", gf2.readonly(self.hz))
        for field in ("logical_x", "logical_z", "logical_labels"):
            object.__setattr__(self, field, tuple(getattr(self, field)))
        if not isinstance(self.basis_source, str) or not self.basis_source:
            raise ValueError("missing logical-basis provenance")
        expected = check_matrices(self.spec)
        if any(not np.array_equal(a, b) for a, b in zip((self.hx, self.hz), expected)):
            raise ValueError("checks mismatch declared BB convention")
        if gf2.matmul(self.hx, self.hz.T).any():
            raise ValueError("noncommuting CSS checks")
        k = self.spec.n - gf2.rank(self.hx) - gf2.rank(self.hz)
        if len(self.logical_x) != k or len(self.logical_z) != k or len(self.logical_labels) != k:
            raise ValueError("logical basis size differs from code dimension")
        if len(set(self.logical_labels)) != k or any(not isinstance(label, str) or not label for label in self.logical_labels):
            raise ValueError("logical labels must be unique and nonempty")
        for sector, logicals in (("X", self.logical_x), ("Z", self.logical_z)):
            for p in logicals:
                p.require_hermitian()
                if p.qubit_ids != self.qubit_ids or any(p.z if sector == "X" else p.x):
                    raise ValueError("logical register or CSS sector mismatch")
        if gf2.matmul(self.hz, self.lx.T).any() or gf2.matmul(self.hx, self.lz.T).any():
            raise ValueError("logical outside centralizer")
        if not np.array_equal(gf2.matmul(self.lx, self.lz.T), np.eye(k, dtype=np.uint8)):
            raise ValueError("logical basis is not canonical")

    @property
    def qubit_ids(self):
        return self.spec.register(self.block_id)

    @property
    def lx(self):
        return gf2.readonly(np.asarray([p.x for p in self.logical_x], dtype=np.uint8).reshape(-1, self.spec.n))

    @property
    def lz(self):
        return gf2.readonly(np.asarray([p.z for p in self.logical_z], dtype=np.uint8).reshape(-1, self.spec.n))

    @property
    def k(self):
        return len(self.logical_labels)

    @property
    def id(self):
        return stable_id(self.to_dict())

    @property
    def checks(self):
        zero = (0,) * self.spec.n
        return tuple(Pauli(0, tuple(row), zero, self.qubit_ids) for row in self.hx) + tuple(
            Pauli(0, zero, tuple(row), self.qubit_ids) for row in self.hz)

    @property
    def check_ids(self):
        return self.spec.check_ids(self.block_id, "X") + self.spec.check_ids(self.block_id, "Z")

    def logical(self, sector, label):
        if label not in self.logical_labels or sector not in ("X", "Y", "Z"):
            raise ValueError("unknown logical label or sector")
        i = self.logical_labels.index(label)
        if sector == "Y":
            return (self.logical_x[i] * self.logical_z[i]).with_phase(1).require_hermitian()
        return (self.logical_x if sector == "X" else self.logical_z)[i]

    def to_dict(self):
        return {"schema_version": 1, "spec": self.spec.to_dict(), "block_id": self.block_id,
                "hx": self.hx.tolist(), "hz": self.hz.tolist(),
                "logical_x": [p.to_dict() for p in self.logical_x],
                "logical_z": [p.to_dict() for p in self.logical_z],
                "logical_labels": list(self.logical_labels), "basis_source": self.basis_source}

    @classmethod
    def from_dict(cls, data):
        if set(data) != {"schema_version", "spec", "block_id", "hx", "hz", "logical_x", "logical_z", "logical_labels", "basis_source"} or data["schema_version"] != 1:
            raise ValueError("invalid CodeData schema")
        return cls(BBCodeSpec.from_dict(data["spec"]), data["block_id"], data["hx"], data["hz"],
                   tuple(Pauli.from_dict(p) for p in data["logical_x"]),
                   tuple(Pauli.from_dict(p) for p in data["logical_z"]),
                   tuple(data["logical_labels"]), data["basis_source"])

    def to_json(self):
        return json.dumps(self.to_dict(), sort_keys=True)

    @classmethod
    def from_json(cls, text):
        return cls.from_dict(json.loads(text))


def build_bb_code(spec, block_id, logical_rows=None, logical_labels=None, basis_source=None):
    hx, hz = check_matrices(spec)
    lx, lz = derive_css_logicals(hx, hz) if logical_rows is None else map(lambda a: gf2.binary(a, 2), logical_rows)
    labels = tuple(str(i + 1) for i in range(len(lx))) if logical_labels is None else tuple(logical_labels)
    ids = spec.register(block_id)
    zero = (0,) * spec.n
    return CodeData(spec, block_id, hx, hz,
                    tuple(Pauli(0, tuple(row), zero, ids) for row in lx),
                    tuple(Pauli(0, zero, tuple(row), ids) for row in lz), labels,
                    basis_source or "deterministic GF(2) centralizer quotient; no distance claim")
