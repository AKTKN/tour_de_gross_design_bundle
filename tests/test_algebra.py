"""A01: dense complex matrices and exhaustive finite sets are independent oracles."""
from itertools import product
import json

import numpy as np
import pytest

from gross_design_bandle.algebra import gf2
from gross_design_bandle.algebra.pauli import Pauli

I = np.eye(2, dtype=complex)
X = np.array([[0, 1], [1, 0]], dtype=complex)
Y = np.array([[0, -1j], [1j, 0]], dtype=complex)
Z = np.diag([1, -1]).astype(complex)


def dense(p):
    out = np.ones((1, 1), dtype=complex)
    for x, z in zip(p.x, p.z):
        out = np.kron(out, (X if x else I) @ (Z if z else I))
    return (1j ** p.phase) * out


def all_paulis(n):
    ids = tuple(f"q{i}" for i in range(n))
    return [Pauli(phase, bits[:n], bits[n:], ids)
            for phase in range(4) for bits in product((0, 1), repeat=2*n)]


def test_signed_pauli_exhaustive_multiplication_and_commutation():
    # All phases, all one-/two-qubit supports: 256 + 4096 ordered products.
    for n in (1, 2):
        paulis = all_paulis(n)
        matrices = [dense(p) for p in paulis]
        for p, a in zip(paulis, matrices):
            assert np.array_equal(dense(p.dagger()), a.conj().T)
            for q, b in zip(paulis, matrices):
                assert np.array_equal(dense(p*q), a @ b)
                assert p.commutes(q) == np.array_equal(a @ b, b @ a)
                assert np.array_equal(a @ b, (-1)**p.symplectic(q) * (b @ a))
    x, y, z = (Pauli.from_word(w) for w in "XYZ")
    assert x*z == y.with_phase(-1)
    assert (x*z).with_phase(1) == y


def test_signed_pauli_exhaustive_clifford_conjugation():
    h = np.array([[1, 1], [1, -1]], dtype=complex) / np.sqrt(2)
    s = np.diag([1, 1j])
    local = {"H": h, "S": s, "S_DAG": s.conj().T, "X": X, "Y": Y, "Z": Z}
    for n in (1, 2):
        for p in all_paulis(n):
            a = dense(p)
            for gate, u in local.items():
                for slot in range(n):
                    unitary = u if n == 1 else np.kron(u, I) if slot == 0 else np.kron(I, u)
                    assert np.allclose(dense(p.conjugated(gate, f"q{slot}")), unitary @ a @ unitary.conj().T, atol=1e-14)
            if n == 2:
                swap = np.eye(4)[[0, 2, 1, 3]]
                cnot = np.eye(4)[[0, 1, 3, 2]]
                for gate, u in (("CNOT", cnot), ("CZ", np.diag([1, 1, 1, -1])), ("SWAP", swap)):
                    for args, unitary in ((('q0', 'q1'), u), (('q1', 'q0'), swap @ u @ swap)):
                        assert np.allclose(dense(p.conjugated(gate, *args)), unitary @ a @ unitary.conj().T, atol=1e-14)


def test_hermitian_checks_and_json():
    for n in (1, 2):
        for p in all_paulis(n):
            assert Pauli.from_json(p.to_json()) == p
            assert p.hermitian == np.array_equal(dense(p), dense(p).conj().T)
            if p.hermitian:
                assert p.require_hermitian() * p == Pauli.identity(p.qubit_ids)
            else:
                with pytest.raises(ValueError, match="imaginary-phase"):
                    p.require_hermitian()
    assert Pauli.from_word("YY", sign=-1).hermitian


def test_pauli_rejects_invalid_checks_registers_and_gates():
    with pytest.raises(ValueError):
        Pauli(0, (2,), (0,), ('q',))
    with pytest.raises(ValueError):
        Pauli(0.5, (0,), (0,), ('q',))
    with pytest.raises(ValueError):
        Pauli(0, (0, 1), (0,), ('q',))
    with pytest.raises(ValueError):
        Pauli(0, (0, 1), (0, 0), ('q', 'q'))
    with pytest.raises(ValueError):
        Pauli.from_word("M")
    p = Pauli.from_word("YZ", ('a:0', 'a:1'))
    q = Pauli.from_word("YZ", ('b:0', 'b:1'))
    for operation in (lambda: p*q, lambda: p.commutes(q), lambda: p.conjugated("T", 'a:0'),
                      lambda: p.conjugated("CNOT", 'a:0', 'a:0'), lambda: p.conjugated("H", 'missing'),
                      lambda: p.permuted((0, 0)), lambda: p.permuted((0.0, 1.0))):
        with pytest.raises(ValueError):
            operation()
    bad = json.loads(p.to_json())
    bad['schema_version'] = 2
    with pytest.raises(ValueError):
        Pauli.from_dict(bad)


def test_gf2_exhaustive_small_systems():
    # Independently enumerate every 2x3 binary map and all RHS vectors.
    vectors = np.array(list(product((0, 1), repeat=3)), dtype=np.uint8)
    for entries in product((0, 1), repeat=6):
        a = np.array(entries, dtype=np.uint8).reshape(2, 3)
        images = (a @ vectors.T).T % 2
        assert 2 ** gf2.rank(a) == len(set(map(tuple, images)))
        ker = gf2.kernel(a)
        assert not gf2.matmul(a, ker.T).any()
        assert gf2.rank(ker) == 3 - gf2.rank(a)
        assert len(vectors[np.all(images == 0, axis=1)]) == 2 ** len(ker)
        for rhs in product((0, 1), repeat=2):
            b = np.array(rhs, dtype=np.uint8).reshape(2, 1)
            exists = np.any(np.all(images == b.T, axis=1))
            if exists:
                solution = gf2.solve(a, b)
                assert np.array_equal(gf2.matmul(a, solution), b)
            else:
                with pytest.raises(ValueError, match="inconsistent"):
                    gf2.solve(a, b)
    for entries in product((0, 1), repeat=4):
        a = np.array(entries, dtype=np.uint8).reshape(2, 2)
        if gf2.rank(a) == 2:
            assert np.array_equal(gf2.matmul(a, gf2.inverse(a)), np.eye(2, dtype=np.uint8))
        else:
            with pytest.raises(ValueError):
                gf2.inverse(a)
    assert gf2.kernel(np.zeros((0, 3), dtype=np.uint8)).shape == (3, 3)
    assert gf2.rank(np.zeros((3, 0), dtype=np.uint8)) == 0


def test_gf2_rejects_malformed_and_inconsistent_inputs():
    for value in ([[0, 2]], [[-1, 0]], [[0.0, 1.0]], [[0.5]], [["0"]]):
        with pytest.raises(ValueError, match="binary integers"):
            gf2.rank(value)
    with pytest.raises(ValueError):
        gf2.rank([0, 1])
    with pytest.raises(ValueError):
        gf2.solve([[1, 0]], [[0], [1]])
    with pytest.raises(ValueError):
        gf2.span_coefficients([[1, 0]], [[0, 1]])
    with pytest.raises(ValueError):
        gf2.quotient_basis([[1, 0]], [[0, 1]])
