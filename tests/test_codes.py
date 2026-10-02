"""A02: unchanged delivered audit, literal fixtures and donor matrices as oracles."""
from dataclasses import FrozenInstanceError, replace
from itertools import product
import json
from pathlib import Path
import sys

import numpy as np
import pytest

from gross_design_bandle.algebra import gf2
from gross_design_bandle.algebra.pauli import Pauli
from gross_design_bandle.codes import BBCodeSpec, CodeData, load_reference_code, small_debug_code
from gross_design_bandle.codes.bb import CONVENTION
from gross_design_bandle.codes.conventions import ConventionAdapter, qldpc_adapter
from gross_design_bandle.codes.reference_profiles import reference_fixture

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import audit_reference as independent


@pytest.mark.parametrize('profile,expected_rank', [('gross', 66), ('two_gross', 138)])
def test_reference_ranks_and_complete_canonical_basis(profile, expected_rank):
    fixture = json.loads((ROOT / 'reference' / f'{profile}.json').read_text())
    code = load_reference_code(profile, 'block_a')
    original = independent.code_data(fixture)
    for actual, expected in zip((code.hx, code.hz, code.lx, code.lz), original):
        assert np.array_equal(actual, expected)
    delivered = next(row for row in json.loads((ROOT / 'evidence/algebra_audit.json').read_text())['results'] if row['code'] == profile)
    assert gf2.rank(code.hx) == gf2.rank(code.hz) == expected_rank == delivered['rank_Hx'] == delivered['rank_Hz']
    assert not gf2.matmul(code.hx, code.hz.T).any()
    assert not gf2.matmul(code.hx, code.lz.T).any()
    assert not gf2.matmul(code.hz, code.lx.T).any()
    assert np.array_equal(gf2.matmul(code.lx, code.lz.T), np.eye(12, dtype=np.uint8))
    assert gf2.rank(np.vstack((code.hx, code.lx))) == expected_rank + 12
    assert gf2.rank(np.vstack((code.hz, code.lz))) == expected_rank + 12
    assert code.logical_labels == tuple(map(str, range(1, 13)))
    for i in ('1', '7'):
        for sector in ('X', 'Z'):
            p = code.logical(sector, i)
            assert sum(p.x) + sum(p.z) == delivered['chosen_port_weight']
            assert p.hermitian
        assert code.logical('Y', i) == (code.logical('X', i)*code.logical('Z', i)).with_phase(1)
        assert code.logical('Y', i)*code.logical('Y', i) == Pauli.identity(code.qubit_ids)
    assert len(set(code.qubit_ids)) == code.spec.n
    assert len(set(code.check_ids)) == 2*code.spec.cells


def test_immutable_ids_blocks_and_serialization():
    code = load_reference_code('gross', 'block_a')
    restored = CodeData.from_json(code.to_json())
    assert restored.to_dict() == code.to_dict() and restored.id == code.id
    assert BBCodeSpec.from_json(code.spec.to_json()) == code.spec
    assert code.id == load_reference_code('gross', 'block_a').id
    other = load_reference_code('gross', 'block_b')
    assert other.id != code.id and other.spec.id == code.spec.id
    assert not set(code.qubit_ids) & set(other.qubit_ids)
    assert not set(code.check_ids) & set(other.check_ids)
    with pytest.raises(ValueError):
        code.logical('X', '1') * other.logical('X', '1')
    with pytest.raises(FrozenInstanceError):
        code.block_id = 'other'
    with pytest.raises(FrozenInstanceError):
        code.spec.name = 'other'
    for array in (code.hx, code.hz, code.lx, code.lz):
        with pytest.raises(ValueError):
            array.flat[0] = 1
        with pytest.raises(ValueError):
            array.setflags(write=True)


def test_small_debug_fixture_derives_own_labels():
    code = small_debug_code('small_a')
    # Enumerate 2^9 maps of each half to get an independent image-size rank.
    for checks in (code.hx, code.hz):
        for half in (checks[:, :9], checks[:, 9:]):
            images = {tuple((half @ np.array(v, dtype=np.uint8)) % 2) for v in product((0, 1), repeat=9)}
            assert len(images) == 128
    assert code.spec.n == 18 and code.k == 4
    assert gf2.rank(code.hx) == gf2.rank(code.hz) == 7
    assert independent.rank(code.hx) == independent.rank(code.hz) == 7
    assert code.logical_labels == ('1', '2', '3', '4')
    assert not gf2.matmul(code.hx, code.hz.T).any()
    assert np.array_equal(gf2.matmul(code.lx, code.lz.T), np.eye(4, dtype=np.uint8))
    for checks, logicals in ((code.hx, code.lx), (code.hz, code.lz)):
        assert gf2.rank(np.vstack((checks, logicals))) == 11
    with pytest.raises(ValueError, match='unknown logical'):
        code.logical('X', '7')


def test_donor_convention_provenance_matches_installed_source():
    import hashlib
    import qldpc
    provenance = json.loads((ROOT / 'locks/algebra-sources.json').read_text())
    pinned = json.loads((ROOT / 'locks/source-lock.json').read_text())
    donor = next(row for row in pinned['repositories'] if row['directory'] == 'qLDPC')
    assert provenance['donor']['commit'] == donor['commit']
    record = provenance['donor']['files']['src/qldpc/codes/quantum.py']
    installed = Path(qldpc.__file__).parent / 'codes/quantum.py'
    assert hashlib.sha256(installed.read_bytes()).hexdigest() == record['sha256']
    for path, digest in provenance['independent_oracles'].items():
        assert hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == digest


@pytest.mark.parametrize('profile', ['gross', 'two_gross'])
def test_actual_qldpc_check_and_qubit_permutations(profile):
    # Real pinned backend executed only for matrix construction, no distance search.
    from qldpc.codes import BBCode
    from sympy import symbols
    code = load_reference_code(profile, 'a')
    x, y = symbols('x y')
    a = sum(x**i * y**j for i, j in code.spec.A)
    b = sum(x**i * y**j for i, j in code.spec.B)
    for order, orders in ((('x', 'y'), {x: code.spec.ell, y: code.spec.m}),
                          (('y', 'x'), {y: code.spec.m, x: code.spec.ell})):
        donor = BBCode(orders, a, b)
        adapter = qldpc_adapter(code.spec, order)
        # Exact complete permutations, independently described by array coordinates.
        cells = tuple(i*code.spec.m+j if order == ('x', 'y') else j*code.spec.ell+i
                      for i in range(code.spec.ell) for j in range(code.spec.m))
        assert adapter.x_checks == adapter.z_checks == cells
        assert adapter.qubits == cells + tuple(code.spec.cells+i for i in cells)
        if order == ('y', 'x'):
            assert adapter.qubits != tuple(range(code.spec.n))
        hx, hz = adapter.adapt_checks(donor.matrix_x.view(np.ndarray), donor.matrix_z.view(np.ndarray))
        assert np.array_equal(hx, code.hx) and np.array_equal(hz, code.hz)
        assert ConventionAdapter.from_json(adapter.to_json()).id == adapter.id


def test_separate_check_maps_and_signed_pauli_conversion():
    code = small_debug_code()
    rng = np.random.default_rng(101)
    qubits = rng.permutation(code.spec.n)
    xrows = rng.permutation(code.spec.cells)
    zrows = rng.permutation(code.spec.cells)
    adapter = ConventionAdapter(code.spec, 'explicit_permuted_tdg', qubits, xrows, zrows)
    source_x = code.hx[np.ix_(np.argsort(xrows), np.argsort(qubits))]
    source_z = code.hz[np.ix_(np.argsort(zrows), np.argsort(qubits))]
    hx, hz = adapter.adapt_checks(source_x, source_z)
    assert np.array_equal(hx, code.hx) and np.array_equal(hz, code.hz)
    source_ids = tuple(f'donor:{i}' for i in range(code.spec.n))
    expected = code.logical('Y', '1').with_phase(2)
    donor_pauli = expected.permuted(np.argsort(qubits), source_ids)
    assert adapter.adapt_pauli(donor_pauli, source_ids, code.block_id) == expected
    assert ConventionAdapter.from_json(adapter.to_json()) == adapter


def test_rejects_malformed_specs_and_mismatched_conventions():
    code = small_debug_code()
    for changes in ({'ell': 0}, {'m': 1.5}, {'A': ((0, 0), (3, 0))}, {'B': ()},
                    {'A': ((0.5, 0),)}, {'convention': 'unknown'}, {'source': ''}):
        with pytest.raises(ValueError):
            replace(code.spec, **changes)
    with pytest.raises(ValueError):
        replace(code, block_id='a:b')
    with pytest.raises(ValueError):
        replace(code, logical_labels=('1',)*4)
    with pytest.raises(ValueError):
        replace(code, logical_x=code.logical_x[:-1])
    with pytest.raises(ValueError, match='imaginary-phase'):
        replace(code, logical_x=(code.logical_x[0].with_phase(1),)+code.logical_x[1:])
    with pytest.raises(ValueError):
        replace(code, logical_z=code.logical_z[::-1])
    bad = code.to_dict()
    bad['hx'][0][0] ^= 1
    with pytest.raises(ValueError, match='convention'):
        CodeData.from_dict(bad)
    bad = code.to_dict()
    bad['logical_x'][0]['qubit_ids'][0] = 'different_block:0'
    with pytest.raises(ValueError, match='register'):
        CodeData.from_dict(bad)
    bad = code.spec.to_dict()
    bad['extra'] = 0
    with pytest.raises(ValueError, match='schema'):
        BBCodeSpec.from_dict(bad)
    with pytest.raises(ValueError):
        reference_fixture('unknown')


def test_rejects_wrong_donor_permutations_and_matrix_bits():
    code = small_debug_code()
    adapter = qldpc_adapter(code.spec)
    for changes in ({'qubits': (0,)*code.spec.n}, {'x_checks': tuple(range(8))},
                    {'z_checks': tuple([0.0]*9)}, {'source_convention': 'unknown'}, {'target_convention': 'unknown'}):
        with pytest.raises(ValueError):
            replace(adapter, **changes)
    for changes in ({'qubits': tuple(reversed(adapter.qubits))}, {'x_checks': tuple(reversed(adapter.x_checks))},
                    {'z_checks': tuple(reversed(adapter.z_checks))}):
        with pytest.raises(ValueError, match='does not match'):
            replace(adapter, **changes).adapt_checks(code.hx, code.hz)
    for hx, hz in ((code.hx[:, :-1], code.hz), (code.hx.astype(float), code.hz)):
        with pytest.raises(ValueError):
            adapter.adapt_checks(hx, hz)
    with pytest.raises(ValueError):
        qldpc_adapter(code.spec, ('x', 'z'))


def test_corrupted_fixture_rejected_without_rewriting_reference(tmp_path):
    raw = (ROOT / 'reference/gross.json').read_bytes()
    (tmp_path / 'gross.json').write_bytes(raw)
    assert load_reference_code('gross', 'a', tmp_path).k == 12
    corrupted = json.loads(raw)
    corrupted['convention'] = 'different'
    (tmp_path / 'gross.json').write_text(json.dumps(corrupted))
    with pytest.raises(ValueError, match='frozen source'):
        load_reference_code('gross', 'a', tmp_path)
    assert (ROOT / 'reference/gross.json').read_bytes() == raw
