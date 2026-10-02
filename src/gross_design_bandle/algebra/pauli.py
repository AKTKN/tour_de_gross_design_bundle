"""P = i**phase X**x Z**z, in the declared ordered physical register.

The stored phase is relative to XZ, not to a tensor of I/X/Y/Z.
Thus XZ=-iY and Y=iXZ. Every operation preserves the full phase.
"""
from __future__ import annotations

from dataclasses import dataclass
import json
from numbers import Integral

from .gf2 import binary


@dataclass(frozen=True)
class Pauli:
    phase: int
    x: tuple[int, ...]
    z: tuple[int, ...]
    qubit_ids: tuple[str, ...]

    def __post_init__(self):
        if not isinstance(self.phase, Integral) or isinstance(self.phase, bool):
            raise ValueError("phase must be an integer modulo four")
        object.__setattr__(self, "phase", int(self.phase) % 4)
        object.__setattr__(self, "x", tuple(map(int, binary(self.x, 1))))
        object.__setattr__(self, "z", tuple(map(int, binary(self.z, 1))))
        object.__setattr__(self, "qubit_ids", tuple(self.qubit_ids))
        if len(self.x) != len(self.z) or len(self.x) != len(self.qubit_ids):
            raise ValueError("register dimensions differ")
        if len(set(self.qubit_ids)) != len(self.qubit_ids) or any(
            not isinstance(q, str) or not q for q in self.qubit_ids
        ):
            raise ValueError("qubit IDs must be unique nonempty strings")

    @classmethod
    def from_word(cls, word, qubit_ids=None, sign=1):
        if sign not in (-1, 1) or any(p not in "IXYZ" for p in word):
            raise ValueError("invalid Hermitian Pauli word/sign")
        ids = tuple(qubit_ids) if qubit_ids is not None else tuple(f"q{i}" for i in range(len(word)))
        return cls(word.count("Y") + (2 if sign == -1 else 0),
                   tuple(int(p in "XY") for p in word),
                   tuple(int(p in "ZY") for p in word), ids)

    @classmethod
    def identity(cls, qubit_ids):
        return cls.from_word("I" * len(qubit_ids), qubit_ids)

    def _compatible(self, other):
        if self.qubit_ids != other.qubit_ids:
            raise ValueError("ordered physical registers differ")

    def __mul__(self, other):
        self._compatible(other)
        return Pauli(self.phase + other.phase + 2 * sum(a*b for a, b in zip(self.z, other.x)),
                     tuple(a ^ b for a, b in zip(self.x, other.x)),
                     tuple(a ^ b for a, b in zip(self.z, other.z)), self.qubit_ids)

    def with_phase(self, delta):
        return Pauli(self.phase + delta, self.x, self.z, self.qubit_ids)

    def symplectic(self, other):
        self._compatible(other)
        return sum(a*d + b*c for a, b, c, d in zip(self.x, self.z, other.x, other.z)) % 2

    def commutes(self, other):
        return self.symplectic(other) == 0

    @property
    def hermitian(self):
        return (self.phase - sum(a*b for a, b in zip(self.x, self.z))) % 2 == 0

    def require_hermitian(self):
        if not self.hermitian:
            raise ValueError("imaginary-phase Pauli cannot be a measured check")
        return self

    def dagger(self):
        return Pauli(-self.phase + 2 * sum(a*b for a, b in zip(self.x, self.z)),
                     self.x, self.z, self.qubit_ids)

    def conjugated(self, gate, *qubits):
        """U P U† for H, S, S_DAG, X, Y, Z, CNOT, CZ, SWAP."""
        arity = 2 if gate in ("CNOT", "CZ", "SWAP") else 1
        if gate not in ("H", "S", "S_DAG", "X", "Y", "Z", "CNOT", "CZ", "SWAP"):
            raise ValueError("unknown Clifford gate")
        if len(qubits) != arity or len(set(qubits)) != arity or any(q not in self.qubit_ids for q in qubits):
            raise ValueError("invalid gate operands")
        indices = tuple(self.qubit_ids.index(q) for q in qubits)

        def generator(kind, index):
            word = ["I"] * len(self.x)
            word[index] = kind
            return Pauli.from_word("".join(word), self.qubit_ids)

        def image(kind, index):
            if index not in indices:
                return generator(kind, index)
            q = indices[0]
            if gate == "H":
                return generator("Z" if kind == "X" else "X", q)
            if gate in ("S", "S_DAG"):
                if kind == "Z":
                    return generator("Z", q)
                return generator("Y", q).with_phase(2 if gate == "S_DAG" else 0)
            if gate in ("X", "Y", "Z"):
                return generator(kind, q).with_phase(2 if kind != gate else 0)
            control, target = indices
            if gate == "SWAP":
                return generator(kind, target if index == control else control)
            if gate == "CZ":
                return generator(kind, index) if kind == "Z" else generator("X", index) * generator("Z", target if index == control else control)
            if kind == "X" and index == control:
                return generator("X", control) * generator("X", target)
            if kind == "Z" and index == target:
                return generator("Z", control) * generator("Z", target)
            return generator(kind, index)

        out = Pauli.identity(self.qubit_ids).with_phase(self.phase)
        for kind, bits in (("X", self.x), ("Z", self.z)):
            for index, bit in enumerate(bits):
                if bit:
                    out = out * image(kind, index)
        return out

    def permuted(self, target_to_source, target_ids=None):
        p = tuple(target_to_source)
        if any(not isinstance(i, Integral) or isinstance(i, bool) for i in p) or sorted(p) != list(range(len(self.x))):
            raise ValueError("not a qubit permutation")
        ids = tuple(target_ids) if target_ids is not None else self.qubit_ids
        return Pauli(self.phase, tuple(self.x[i] for i in p), tuple(self.z[i] for i in p), ids)

    def to_dict(self):
        return {"schema_version": 1, "phase": self.phase, "x": list(self.x), "z": list(self.z), "qubit_ids": list(self.qubit_ids)}

    @classmethod
    def from_dict(cls, data):
        if set(data) != {"schema_version", "phase", "x", "z", "qubit_ids"} or data["schema_version"] != 1:
            raise ValueError("invalid Pauli schema")
        return cls(data["phase"], data["x"], data["z"], data["qubit_ids"])

    def to_json(self):
        return json.dumps(self.to_dict(), sort_keys=True)

    @classmethod
    def from_json(cls, text):
        return cls.from_dict(json.loads(text))
