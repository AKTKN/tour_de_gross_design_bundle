"""Load frozen TdG transcriptions; never write or regenerate reference fixtures."""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path

import numpy as np

from .bb import BBCodeSpec, FIXTURE_CONVENTION, build_bb_code, terms

# Delivered scientific fixture byte hashes (SHA256SUMS.delivery.txt).
FROZEN_SHA256 = {
    "gross": "937872cf0cb56785484d0622836c1711e4ece1a1c1b8bafb64a7852535341080",
    "two_gross": "9aaf8a1515a3021c217d6735932c07f3e5293b9af94818aa83f13e46c6faddd1",
}


def reference_fixture(profile, reference_dir=None):
    if profile not in FROZEN_SHA256:
        raise ValueError("unknown frozen reference profile")
    directory = Path(reference_dir) if reference_dir is not None else Path(__file__).resolve().parents[3] / "reference"
    raw = (directory / f"{profile}.json").read_bytes()
    if sha256(raw).hexdigest() != FROZEN_SHA256[profile]:
        raise ValueError("reference fixture differs from frozen source")
    data = json.loads(raw)
    if data["convention"] != FIXTURE_CONVENTION or data["name"] != profile:
        raise ValueError("mismatched reference convention/profile")
    return data


def physical_shift_permutation(spec, dx, dy):
    """target_to_source: translated support at (i,j) comes from (i-dx,j-dy)."""
    from .bb import integer
    dx, dy = integer(dx), integer(dy)
    return tuple(spec.qubit_index(s, i - dx, j - dy) for s in ("L", "R") for i in range(spec.ell) for j in range(spec.m))


def shift_rows(rows, spec, dx, dy):
    return np.asarray(rows)[:, physical_shift_permutation(spec, dx, dy)]


def reconstruct_reference_basis(fixture, spec):
    def support(left, right):
        row = np.zeros(spec.n, dtype=np.uint8)
        for side, key in (("L", left), ("R", right)):
            for i, j in terms(fixture[key]):
                row[spec.qubit_index(side, i, j)] ^= 1
        return row

    def dual(row):
        result = np.zeros(spec.n, dtype=np.uint8)
        ox, oy = terms([fixture["dual_shift"]])[0]
        for q in np.flatnonzero(row):
            side, cell = divmod(int(q), spec.cells)
            i, j = divmod(cell, spec.m)
            result[spec.qubit_index("R" if side == 0 else "L", ox - i, oy - j)] ^= 1
        return result

    x1, x7 = support("p", "q"), support("r", "s")
    z1, z7 = dual(x7), dual(x1)
    translate = lambda row, i, j: shift_rows(row[None, :], spec, i, j)[0]
    alpha, beta = terms(fixture["alpha"]), terms(fixture["beta"])
    lx = np.array([translate(x1, i, j) for i, j in alpha] + [translate(x7, -i, -j) for i, j in beta])
    lz = np.array([translate(z1, i, j) for i, j in beta] + [translate(z7, -i, -j) for i, j in alpha])
    return lx, lz


def load_reference_code(profile, block_id, reference_dir=None):
    fixture = reference_fixture(profile, reference_dir)
    spec = BBCodeSpec(profile, fixture["ell"], fixture["m"], fixture["A"], fixture["B"], fixture["source"])
    return build_bb_code(spec, block_id, reconstruct_reference_basis(fixture, spec),
                         tuple(str(i) for i in range(1, 13)),
                         f"arXiv:2506.03094v1 PDF Eqs. (31)--(36); fixture SHA256 {FROZEN_SHA256[profile]}")


def small_debug_code(block_id="debug"):
    """Own 18-qubit BB fixture; logical labels are derived, no X7 assumption.

    This is an algebra debugging fixture, not a scaled TdG LPU or distance claim.
    """
    spec = BBCodeSpec("debug18", 3, 3, ((0, 0), (1, 0), (0, 1)),
                      ((0, 0), (2, 0), (0, 2)), "local phase-01 debug construction; 3x3 torus")
    return build_bb_code(spec, block_id)
