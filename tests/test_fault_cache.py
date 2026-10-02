"""Reuse must preserve columns and fail closed on stale or incomplete artifacts."""
from dataclasses import replace
import numpy as np
import pytest
import stim

from gross_design_bandle.noise import NoiseProfile, Location, build_fault_model
from gross_design_bandle.noise import catalogue, cache
from gross_design_bandle.bench.artifacts import save_fault_model, load_fault_model, write_bundle
from gross_design_bandle.flows.stabilizer_flows import verify_deterministic, verify_deterministic_stim


@pytest.fixture
def fixture(monkeypatch):
    monkeypatch.delenv('GROSS_DESIGN_CACHE_DIR', raising=False)
    c = stim.Circuit('R 0\nI 0\nM 0\nDETECTOR rec[-1]\nOBSERVABLE_INCLUDE(0) rec[-1]')
    ls = (Location('idle', 1, 'idle', (0,), 'I', 'test', 0, 0, 'data'),)
    return c, ls


def build(fixture, root=False, **changes):
    c, ls = fixture
    return build_fault_model(c, ls, NoiseProfile(changes.pop('profile', 'a7_uniform_expanded'), changes.pop('p', .03)),
        admission_policy=changes.pop('admission', 'include_all'),
        grouping_policy=changes.pop('grouping', 'joint_signature_xor'), cache_dir=root, **changes)


def assert_same(a, b):
    assert a.raw == b.raw and a.raw_signatures == b.raw_signatures
    assert a.group_signatures == b.group_signatures and a.N == b.N
    for name in ('copy_to_raw', 'copy_ordinal', 'admission_mask', 'admitted_to_copy',
                 'admitted_to_group', 'probabilities', 'decoder_probabilities'):
        np.testing.assert_array_equal(getattr(a, name), getattr(b, name))
    assert (a.H != b.H).nnz == (a.Lambda != b.Lambda).nnz == 0


def test_cold_warm_and_probability_reuse(fixture, tmp_path, monkeypatch):
    expected = build(fixture)
    expected_changed = build(fixture, p=.06)
    cold = build(fixture, tmp_path)
    assert_same(expected, cold)
    # Warm reads must avoid both propagation and rebuilding the sparse matrices.
    def unexpected(*args, **kwargs):
        pytest.fail('warm cache recomputed numerical work')
    monkeypatch.setattr(catalogue, 'joint_signatures', unexpected)
    from gross_design_bandle.bench import columns
    monkeypatch.setattr(columns, 'matrix_from_signatures', unexpected)
    warm = build(fixture, tmp_path)
    assert_same(expected, warm)
    changed = build(fixture, tmp_path, p=.06)
    assert_same(expected_changed, changed)
    np.testing.assert_array_equal(changed.probabilities, 2 * expected.probabilities)
    assert changed.raw_signatures == expected.raw_signatures
    assert (changed.H != expected.H).nnz == 0
    assert not np.array_equal(changed.decoder_probabilities, expected.decoder_probabilities)


def test_signature_reuse_across_population_policies(fixture, tmp_path, monkeypatch):
    build(fixture, tmp_path)
    def unexpected(*args):
        pytest.fail('same physical circuit propagated again')
    monkeypatch.setattr(catalogue, 'joint_signatures', unexpected)
    unequal = build(fixture, tmp_path, profile='paper_linearized_unequal')
    excluded = build(fixture, tmp_path, admission='exclude_joint_zero')
    copies = build(fixture, tmp_path, grouping='preserve_copies')
    assert unequal.N == 3 and excluded.N == 10 and copies.N == 15
    for m in (unequal, excluded, copies):
        m.validate()


def test_physical_and_implementation_changes_invalidate(fixture, tmp_path, monkeypatch):
    c, ls = fixture
    original = catalogue.joint_signatures
    calls = []
    def counted(*args):
        calls.append(1)
        return original(*args)
    monkeypatch.setattr(catalogue, 'joint_signatures', counted)
    build(fixture, tmp_path)
    changed = stim.Circuit(str(c).replace('I 0', 'Z 0'))
    build((changed, ls), tmp_path)
    build((c, (replace(ls[0], role='edge'),)), tmp_path)
    identity = cache.implementation_identity()
    monkeypatch.setattr(cache, 'implementation_identity', lambda: {**identity, 'format': 999})
    build(fixture, tmp_path)
    assert len(calls) == 4


@pytest.mark.parametrize('corruption', ['partial', 'matrix', 'signatures', 'metadata'])
def test_invalid_cache_rebuilt_without_stale_success(fixture, tmp_path, corruption):
    expected = build(fixture, tmp_path)
    entry = next((tmp_path / 'models').glob('*/manifest.json')).parent
    if corruption == 'partial':
        (entry / 'manifest.json').unlink()
    elif corruption == 'matrix':
        (entry / 'H_data.npy').write_bytes(b'partial')
    elif corruption == 'metadata':
        import json
        record = json.loads((entry / 'manifest.json').read_text())
        record['metadata']['p'] = .06
        (entry / 'manifest.json').write_text(json.dumps(record))
    else:
        sig = next((tmp_path / 'signatures').glob('*/manifest.json')).parent
        (sig / 'indices.npy').write_bytes(b'partial')
        (entry / 'manifest.json').unlink()
    rebuilt = build(fixture, tmp_path)
    assert_same(expected, rebuilt)
    assert list((tmp_path / 'models').glob('*.invalid-*'))


def test_interrupted_compute_is_not_a_cache_entry(fixture, tmp_path, monkeypatch):
    def interrupted(*args):
        raise KeyboardInterrupt
    with monkeypatch.context() as patch:
        patch.setattr(catalogue, 'joint_signatures', interrupted)
        with pytest.raises(KeyboardInterrupt):
            build(fixture, tmp_path)
    assert not list(tmp_path.rglob('manifest.json'))
    assert build(fixture, tmp_path).N == 15
    with pytest.raises(ValueError, match='object arrays'):
        write_bundle(tmp_path / 'partial', {}, {'a': np.array([object()])})
    assert not (tmp_path / 'partial').exists()


def test_compact_artifact_roundtrip_mmap_and_zero_columns(fixture, tmp_path):
    m = build(fixture)
    path = tmp_path / 'model'
    save_fault_model(path, m)
    loaded = load_fault_model(path)
    assert_same(m, loaded)
    assert isinstance(loaded.copy_to_raw, np.memmap)
    assert not loaded.H.data.flags.writeable
    assert len(loaded.raw) == 3 and loaded.N == 15  # zero/zero columns retained
    with pytest.raises(OSError):
        save_fault_model(path, m)
    (path / 'Lambda_indices.npy').write_bytes(b'broken')
    with pytest.raises(ValueError, match='checksum'):
        load_fault_model(path)


def test_logical_only_columns_survive_storage(tmp_path):
    c = stim.Circuit('R 0\nI 0\nM 0\nOBSERVABLE_INCLUDE(0) rec[-1]')
    ls = (Location('idle', 1, 'idle', (0,), 'I', 'test', 0, 0, 'data'),)
    m = build((c, ls), False, admission='exclude_joint_zero')
    save_fault_model(tmp_path / 'model', m)
    loaded = load_fault_model(tmp_path / 'model')
    assert loaded.H.shape == (0, 10) and loaded.Lambda.nnz == 10


@pytest.mark.parametrize('text', [
    'R 0\nM 0\nDETECTOR rec[-1]',
    'R 0\nREPEAT 3 {\nM 0\nDETECTOR rec[-1]\n}\nOBSERVABLE_INCLUDE(0) rec[-1]',
    'RY 0\nMY 0\nDETECTOR rec[-1]\nOBSERVABLE_INCLUDE(0) rec[-1]',
])
def test_stim_and_independent_small_signed_checks_agree(text):
    c = stim.Circuit(text)
    assert verify_deterministic(c)['all_zero'] == verify_deterministic_stim(c)['all_zero']


@pytest.mark.parametrize('text', [
    'RX 0\nM 0\nDETECTOR rec[-1]',  # random
    'R 0\nX 0\nM 0\nDETECTOR rec[-1]',  # constant wrong sign
    'R 0\nX 0\nM 0\nOBSERVABLE_INCLUDE(0) rec[-1]',
    'R 0\nM !0\nDETECTOR rec[-1]',
    'R 0\nM 0\nDETECTOR rec[-2]',
])
def test_stim_check_rejects_random_sign_and_offset_corruption(text):
    with pytest.raises(ValueError):
        verify_deterministic_stim(stim.Circuit(text))
