"""Physical translation action on the full logical quotient, with span witnesses.

Row convention: transformed generator i has coefficients in row i.
For a row vector c, c' = c M; column coefficients use M.T.
No noisy shift or physical transfer circuit is implemented here.
"""
from __future__ import annotations

from dataclasses import dataclass
import json
from numbers import Integral
import re
import numpy as np

from . import gf2
from .pauli import Pauli
from gross_design_bandle.codes.reference_profiles import physical_shift_permutation


def logical_coordinates(code, pauli):
    if pauli.qubit_ids != code.qubit_ids:
        raise ValueError("logical register mismatch")
    if any(not pauli.commutes(check) for check in code.checks):
        raise ValueError("Pauli outside stabilizer centralizer")
    return np.array([pauli.symplectic(p) for p in code.logical_z + code.logical_x], dtype=np.uint8)


@dataclass(frozen=True, eq=False)
class ShiftAction:
    code_id: str
    matrix: np.ndarray
    phase_offsets: tuple[int, ...]
    stabilizer_coefficients: np.ndarray

    def __post_init__(self):
        object.__setattr__(self, "matrix", gf2.readonly(self.matrix))
        object.__setattr__(self, "stabilizer_coefficients", gf2.readonly(self.stabilizer_coefficients))
        object.__setattr__(self, "phase_offsets", tuple(self.phase_offsets))
        if not isinstance(self.code_id, str) or not re.fullmatch(r"[0-9a-f]{64}", self.code_id):
            raise ValueError("invalid code ID")
        size = self.matrix.shape[0]
        if self.matrix.shape[1] != size or size % 2 or self.stabilizer_coefficients.shape[0] != size:
            raise ValueError("invalid shift action dimensions")
        if len(self.phase_offsets) != size or any(not isinstance(p, Integral) or isinstance(p, bool) or p not in range(4) for p in self.phase_offsets):
            raise ValueError("invalid shift phase offsets")
        object.__setattr__(self, "phase_offsets", tuple(int(p) for p in self.phase_offsets))

    @property
    def column_matrix(self):
        return self.matrix.T

    def to_dict(self):
        return {"schema_version": 1, "code_id": self.code_id, "row_matrix": self.matrix.tolist(),
                "phase_offsets": list(self.phase_offsets),
                "stabilizer_coefficients": self.stabilizer_coefficients.tolist()}

    def to_json(self):
        return json.dumps(self.to_dict(), sort_keys=True)

    @classmethod
    def from_json(cls, text):
        data = json.loads(text)
        if set(data) != {"schema_version", "code_id", "row_matrix", "phase_offsets", "stabilizer_coefficients"} or data["schema_version"] != 1:
            raise ValueError("invalid ShiftAction schema")
        return cls(data["code_id"], data["row_matrix"], data["phase_offsets"], data["stabilizer_coefficients"])


def derive_shift_action(code, dx, dy):
    permutation = physical_shift_permutation(code.spec, dx, dy)
    basis = code.logical_x + code.logical_z
    checks = code.checks
    symplectic_checks = np.array([p.x + p.z for p in checks], dtype=np.uint8)
    coefficients, residuals = [], []
    shifted = [p.permuted(permutation) for p in basis]
    for p in shifted:
        coords = logical_coordinates(code, p)
        representative = Pauli.identity(code.qubit_ids)
        for bit, logical in zip(coords, basis):
            if bit:
                representative = representative * logical
        residual = p * representative.dagger()
        coefficients.append(coords)
        residuals.append(residual.x + residual.z)
    witnesses = gf2.span_coefficients(symplectic_checks, np.array(residuals, dtype=np.uint8))
    offsets = []
    for p, coords, witness in zip(shifted, coefficients, witnesses):
        reconstructed = Pauli.identity(code.qubit_ids)
        for bit, check in zip(witness, checks):
            if bit:
                reconstructed = reconstructed * check
        for bit, logical in zip(coords, basis):
            if bit:
                reconstructed = reconstructed * logical
        if reconstructed.x != p.x or reconstructed.z != p.z:
            raise ValueError("invalid shift quotient witness")
        offsets.append((p.phase - reconstructed.phase) % 4)
    return ShiftAction(code.id, np.array(coefficients, dtype=np.uint8), tuple(offsets), witnesses)
