"""Executed backend API checks, bounded to tiny deterministic inputs."""
import hashlib
import importlib.metadata as metadata
import inspect
import json
from pathlib import Path
import sys
import numpy as np
import pytest
from scipy.sparse import csr_matrix

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from audit_backends import load_memory_builder, probe


def test_locked_dependencies_import_and_match_installed_bytes():
    env = json.loads((ROOT / "locks/environment-lock.json").read_text())
    result = probe()
    assert result["python"] == env["python"]
    for name, version in env["packages"].items():
        assert metadata.version(name) == version
    for name, files in env["installed_backend_files_sha256"].items():
        dist = metadata.distribution(name)
        for path, sha in files.items():
            assert hashlib.sha256(dist.locate_file(path).read_bytes()).hexdigest() == sha


def test_reviewed_upstream_api_signatures():
    import qldpc.experimental.surgery as surgery
    import relay_bp
    assert list(inspect.signature(surgery.build_gadget).parameters) == ["code", "x", "basis"]
    assert list(inspect.signature(surgery.build_single_ppm_circuit).parameters) == ["gadget", "rounds", "noise_model", "data_init"]
    assert list(inspect.signature(surgery.build_joint_ppm_circuit).parameters) == ["g_l", "g_r", "bridge", "rounds", "noise_model", "data_init"]
    assert list(inspect.signature(load_memory_builder()).parameters) == ["code", "A_list", "B_list", "p", "num_repeat", "z_basis", "use_both", "HZH"]
    params = inspect.signature(relay_bp.RelayDecoderF32).parameters
    assert {"gamma0", "set_max_iter", "explicit_gammas", "seed", "alpha"} <= set(params)
    assert not {"gamma", "rng_width", "ewainit_discount_factor", "set_num_iters", "max_iter", "ms_scaling_factor"} & set(params)
    assert not hasattr(relay_bp.RelayDecoderF32, "par_decode_batch")


def test_installed_qldpc_matches_pinned_source():
    import qldpc
    locked = json.loads((ROOT / "locks/source-lock.json").read_text())
    entry = next(x for x in locked["repositories"] if x["directory"] == "qLDPC")
    package_root = Path(qldpc.__file__).parent
    for path, record in entry["files"].items():
        if path.startswith("src/qldpc/"):
            installed = package_root / path.removeprefix("src/qldpc/")
            assert hashlib.sha256(installed.read_bytes()).hexdigest() == record["sha256"]


def test_qldpc_rejects_Y_basis():
    from qldpc.codes import CSSCode
    from qldpc.experimental.surgery import build_gadget
    code = CSSCode([[1, 1, 0]], [[1, 1, 0]])
    with pytest.raises(ValueError):
        build_gadget(code, np.array([0, 0, 1], dtype=np.uint8), basis="Y")


def test_relay_tiny_explicit_gamma_syndrome_interface():
    import relay_bp
    matrix = csr_matrix([[1, 1, 0], [0, 1, 1]], dtype=np.uint8)
    decoder = relay_bp.RelayDecoderF32(matrix, np.full(3, 0.003), alpha=1.0,
        gamma0=0.1, pre_iter=4, num_sets=2, set_max_iter=4,
        explicit_gammas=np.array([[0.1, 0.2, 0.3], [0.3, 0.2, 0.1]]), seed=7)
    syndrome = np.array([1, 1], dtype=np.uint8)
    result = decoder.decode_detailed(syndrome)
    assert result.success
    assert np.array_equal(np.asarray(matrix @ result.decoding) % 2, syndrome)
    assert np.array_equal(result.decoding, [0, 1, 0])
    assert result.iterations <= 12
    # Reusing the instance must reinitialize trial-local state.
    assert np.array_equal(decoder.decode(syndrome), result.decoding)


def test_relay_rejects_historical_keyword():
    import relay_bp
    with pytest.raises(TypeError):
        relay_bp.RelayDecoderF32(csr_matrix([[1, 1]], dtype=np.uint8), np.array([0.01, 0.01]), ewainit_discount_factor=0.875)


def test_stim_strict_detector_failure_is_not_hidden():
    import stim
    deterministic = stim.Circuit("R 0\nM 0\nDETECTOR rec[-1]")
    assert deterministic.detector_error_model(allow_gauge_detectors=False).num_detectors == 1
    random_detector = stim.Circuit("R 0\nH 0\nM 0\nDETECTOR rec[-1]")
    with pytest.raises(ValueError, match="non-deterministic detectors"):
        random_detector.detector_error_model(allow_gauge_detectors=False)
