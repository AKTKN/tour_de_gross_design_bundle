"""A06: physical support translations, independent audit and exact quotient witnesses."""
from dataclasses import replace
from functools import reduce
import numpy as np
import pytest

from gross_design_bandle.algebra import gf2
from gross_design_bandle.algebra.logical_basis import ShiftAction, derive_shift_action, logical_coordinates
from gross_design_bandle.algebra.pauli import Pauli
from gross_design_bandle.codes import load_reference_code, small_debug_code
from gross_design_bandle.codes.reference_profiles import physical_shift_permutation, reference_fixture
from test_codes import independent


def power(matrix, exponent):
    out = np.eye(len(matrix), dtype=np.uint8)
    for _ in range(exponent):
        out = gf2.matmul(out, matrix)
    return out


def product_paulis(paulis, bits, ids):
    return reduce(lambda out, item: out*item[1] if item[0] else out,
                  zip(bits, paulis), Pauli.identity(ids))


def verify_signed_witnesses(code, action, dx, dy):
    basis = code.logical_x + code.logical_z
    assert action.code_id == code.id
    for logical, row, checks, phase in zip(basis, action.matrix, action.stabilizer_coefficients, action.phase_offsets):
        actual = logical.permuted(physical_shift_permutation(code.spec, dx, dy))
        reconstructed = product_paulis(code.checks, checks, code.qubit_ids) * product_paulis(basis, row, code.qubit_ids)
        assert actual == reconstructed.with_phase(phase)
        # Independent audit rank checks every binary residual is in the check span.
        residual = actual * product_paulis(basis, row, code.qubit_ids).dagger()
        rows = np.array([p.x + p.z for p in code.checks], dtype=np.uint8)
        assert independent.rank(np.vstack((rows, residual.x + residual.z))) == independent.rank(rows)


@pytest.mark.parametrize('profile', ['gross', 'two_gross'])
def test_physical_shift_full_logical_actions_and_quotient_witnesses(profile):
    code = load_reference_code(profile, 'a')
    fixture = reference_fixture(profile)
    k = code.k
    zero = np.zeros((k, k), dtype=np.uint8)
    symplectic_form = np.block([[zero, np.eye(k, dtype=np.uint8)], [np.eye(k, dtype=np.uint8), zero]])
    for axis, delta in (('x', (1, 0)), ('y', (0, 1))):
        action = derive_shift_action(code, *delta)
        # Derive from literal support permutation, then compare the printed 6x6 blocks.
        audit_x = np.array([independent.shift(row, *delta, fixture) @ code.lz.T % 2 for row in code.lx])
        audit_z = np.array([independent.shift(row, *delta, fixture) @ code.lx.T % 2 for row in code.lz])
        assert np.array_equal(action.matrix, np.block([[audit_x, zero], [zero, audit_z]]))
        printed = np.array(fixture['logical_M' + axis], dtype=np.uint8)
        printed_x = np.block([[printed.T, np.zeros_like(printed)], [np.zeros_like(printed), printed]])
        assert np.array_equal(action.matrix[:k, :k], printed_x)
        assert np.array_equal(action.matrix[k:, k:], gf2.inverse(printed_x).T)
        assert np.array_equal(gf2.matmul(gf2.matmul(action.matrix, symplectic_form), action.matrix.T), symplectic_form)
        assert set(action.phase_offsets) == {0}
        verify_signed_witnesses(code, action, *delta)


@pytest.mark.parametrize('profile', ['gross', 'two_gross'])
def test_shift_inverses_commuting_actions_and_logical_sixth_powers(profile):
    code = load_reference_code(profile, 'a')
    actions = [derive_shift_action(code, *delta) for delta in ((1, 0), (0, 1), (-1, 0), (0, -1))]
    x, y, xi, yi = [a.matrix for a in actions]
    identity = np.eye(2*code.k, dtype=np.uint8)
    assert np.array_equal(gf2.matmul(x, xi), identity)
    assert np.array_equal(gf2.matmul(xi, x), identity)
    assert np.array_equal(gf2.matmul(y, yi), identity)
    assert np.array_equal(gf2.matmul(yi, y), identity)
    assert np.array_equal(gf2.matmul(x, y), gf2.matmul(y, x))
    assert np.array_equal(derive_shift_action(code, 1, 1).matrix, gf2.matmul(x, y))
    for matrix in (x, y):
        assert np.array_equal(power(matrix, 6), identity)
    for delta in ((6, 0), (0, 6)):
        action = derive_shift_action(code, *delta)
        assert np.array_equal(action.matrix, identity)
        assert set(action.phase_offsets) == {0}
        verify_signed_witnesses(code, action, *delta)
    # ell=12: physical x^6 is visibly nonidentity although quotient action is I.
    assert physical_shift_permutation(code.spec, 6, 0) != tuple(range(code.spec.n))
    assert actions[0].stabilizer_coefficients.any()


@pytest.mark.parametrize('profile', ['gross', 'two_gross'])
def test_row_column_convention_on_mixed_logical_paulis(profile):
    code = load_reference_code(profile, 'a')
    action = derive_shift_action(code, 1, 0)
    assert np.array_equal(action.column_matrix, action.matrix.T)
    assert not np.array_equal(action.matrix, action.column_matrix)
    rng = np.random.default_rng(10)
    basis = code.logical_x + code.logical_z
    for _ in range(20):
        coefficients = rng.integers(0, 2, 2*code.k, dtype=np.uint8)
        # i^(number of overlapping logical X/Z factors) makes this Hermitian.
        p = product_paulis(basis, coefficients, code.qubit_ids).with_phase(int(coefficients[:code.k] @ coefficients[code.k:]) % 4)
        assert p.hermitian
        physical = p.permuted(physical_shift_permutation(code.spec, 1, 0))
        actual = logical_coordinates(code, physical)
        row_action = gf2.matmul(coefficients[None, :], action.matrix)[0]
        column_action = gf2.matmul(action.column_matrix, coefficients[:, None])[:, 0]
        assert np.array_equal(actual, row_action) and np.array_equal(actual, column_action)


def test_signed_basis_changes_preserve_phase_in_shift_witnesses():
    code = load_reference_code('gross', 'signed')
    code = replace(code, logical_x=(code.logical_x[0].with_phase(2),)+code.logical_x[1:])
    action = derive_shift_action(code, 1, 0)
    assert 2 in action.phase_offsets
    verify_signed_witnesses(code, action, 1, 0)


def test_shift_action_serialization_and_malformed_certificate_rejection():
    code = small_debug_code()
    action = derive_shift_action(code, 1, 0)
    assert ShiftAction.from_json(action.to_json()).to_dict() == action.to_dict()
    for changes in ({'code_id': 'bad'}, {'matrix': np.zeros((8, 7), dtype=np.uint8)},
                    {'phase_offsets': (1.5,)*8}, {'phase_offsets': (4,)*8},
                    {'stabilizer_coefficients': np.zeros((7, 18), dtype=np.uint8)}):
        with pytest.raises(ValueError):
            replace(action, **changes)


def test_rejects_noncentralizer_wrong_block_and_invalid_shifts():
    code = small_debug_code('a')
    nonlogical = Pauli.from_word('X'+'I'*17, code.qubit_ids)
    with pytest.raises(ValueError, match='centralizer'):
        logical_coordinates(code, nonlogical)
    with pytest.raises(ValueError, match='register'):
        logical_coordinates(code, small_debug_code('b').logical('Y', '1'))
    for delta in ((0.5, 1), (True, 0), ('x', 0)):
        with pytest.raises(ValueError, match='integer'):
            derive_shift_action(code, *delta)
