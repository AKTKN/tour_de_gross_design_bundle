"""Strict GF(2) linear algebra. Inputs must already contain binary integers."""
from __future__ import annotations

import numpy as np


def binary(value, ndim=None):
    a = np.asarray(value)
    if a.dtype.kind not in "biu" or np.any((a != 0) & (a != 1)):
        raise ValueError("expected binary integers")
    if ndim is not None and a.ndim != ndim:
        raise ValueError(f"expected {ndim} dimensions")
    return a.astype(np.uint8, copy=True)


def readonly(value):
    a = binary(value, 2)
    # Immutable backing storage, even if a caller tries setflags(write=True).
    return np.frombuffer(a.tobytes(), dtype=np.uint8).reshape(a.shape)


def matmul(a, b):
    a, b = binary(a, 2), binary(b, 2)
    if a.shape[1] != b.shape[0]:
        raise ValueError("matrix dimensions differ")
    # uint8 overflow is harmless modulo two, including for wide matrices.
    return (a @ b) & 1


def rref(a):
    a = binary(a, 2)
    pivots = []
    for col in range(a.shape[1]):
        row = len(pivots)
        hits = np.flatnonzero(a[row:, col])
        if not len(hits):
            continue
        hit = row + int(hits[0])
        a[[row, hit]] = a[[hit, row]]
        others = np.flatnonzero(a[:, col])
        others = others[others != row]
        a[others] ^= a[row]
        pivots.append(col)
    return a, tuple(pivots)


def rank(a):
    return len(rref(a)[1])


def row_basis(a):
    reduced, pivots = rref(a)
    return reduced[:len(pivots)]


def kernel(a):
    reduced, pivots = rref(a)
    free = [i for i in range(reduced.shape[1]) if i not in pivots]
    out = np.zeros((len(free), reduced.shape[1]), dtype=np.uint8)
    for row, col in enumerate(free):
        out[row, col] = 1
        out[row, list(pivots)] = reduced[:len(pivots), col]
    return out


def solve(a, b):
    """One solution of A X=B with free variables zero; reject inconsistency."""
    a, b = binary(a, 2), binary(b, 2)
    if a.shape[0] != b.shape[0]:
        raise ValueError("matrix dimensions differ")
    reduced, pivots = rref(np.hstack((a, b)))
    if any(col >= a.shape[1] for col in pivots):
        raise ValueError("inconsistent GF(2) system")
    out = np.zeros((a.shape[1], b.shape[1]), dtype=np.uint8)
    out[list(pivots)] = reduced[:len(pivots), a.shape[1]:]
    return out


def inverse(a):
    a = binary(a, 2)
    if a.shape[0] != a.shape[1] or rank(a) != a.shape[0]:
        raise ValueError("matrix is not invertible")
    return solve(a, np.eye(a.shape[0], dtype=np.uint8))


def span_coefficients(rows, targets):
    """C with C @ rows=targets, or ValueError when outside the row span."""
    return solve(binary(rows, 2).T, binary(targets, 2).T).T


def quotient_basis(kernel_rows, stabilizer_rows):
    """Deterministic representatives of ker / span(stabilizers)."""
    kernel_rows, stabilizer_rows = binary(kernel_rows, 2), binary(stabilizer_rows, 2)
    if kernel_rows.shape[1] != stabilizer_rows.shape[1]:
        raise ValueError("quotient widths differ")
    span_coefficients(kernel_rows, stabilizer_rows)
    span = row_basis(stabilizer_rows)
    selected = []
    for row in kernel_rows:
        candidate = np.vstack((span, row))
        if rank(candidate) > len(span):
            selected.append(row)
            span = row_basis(candidate)
    return np.asarray(selected, dtype=np.uint8).reshape(-1, kernel_rows.shape[1])
