"""Offline source provenance checks against independent reference pins."""
import copy
import hashlib
import json
from pathlib import Path
import sys
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from audit_sources import verify_blob, verify_source_lock


def lock():
    return json.loads((ROOT / "locks/source-lock.json").read_text())


def test_locked_commits_blobs_and_worktree_bytes():
    data = lock()
    assert data["reference_sources_sha256"] == hashlib.sha256((ROOT / "reference/sources.json").read_bytes()).hexdigest()
    result = verify_source_lock(data)
    assert result["status"] == "verified"
    assert len(result["repositories"]) == 4
    for entry in data["repositories"]:
        assert entry["files"]
        if entry["directory"] != "SlidingWindowDecoder":
            assert entry["license_paths"]
            assert set(entry["license_paths"]) <= set(entry["files"])


def test_changed_blob_bytes_are_rejected():
    data = b"independent source oracle\n"
    git_hash = hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()
    sha = hashlib.sha256(data).hexdigest()
    verify_blob(data, git_hash, sha)
    with pytest.raises(ValueError, match="blob/hash mismatch"):
        verify_blob(data + b"changed", git_hash, sha)


def test_reference_commit_cannot_be_replaced():
    data = copy.deepcopy(lock())
    data["repositories"][0]["commit"] = "0" * 40
    with pytest.raises(ValueError, match="reference pin"):
        verify_source_lock(data)


def test_missing_pinned_blob_is_rejected():
    data = copy.deepcopy(lock())
    qldpc = next(x for x in data["repositories"] if x["directory"] == "qLDPC")
    del qldpc["files"]["src/qldpc/experimental/surgery/circuit.py"]
    with pytest.raises(ValueError, match="missing reference-pinned"):
        verify_source_lock(data)
