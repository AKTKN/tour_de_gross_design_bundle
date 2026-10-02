"""Read-only offline verification of inspected Git blobs and worktree bytes."""
from pathlib import Path
import argparse
import hashlib
import json
import os
import subprocess

ROOT = Path(__file__).resolve().parents[1]
EXTERNAL_ROOT = Path(os.environ.get(
    "TOUR_DE_GROSS_EXTERNAL_LIBS",
    "/home/quantum_teresheys/workspace/tour_de_gross_design_bundle/external_libs",
))


def git(path: Path, *args: str) -> bytes:
    # Disallow partial-clone lazy downloads during verification/tests.
    env = dict(os.environ, GIT_NO_LAZY_FETCH="1")
    return subprocess.check_output(["git", "-c", "protocol.allow=never", "-C", str(path), *args], env=env)


def verify_blob(data: bytes, expected_blob: str, expected_sha256: str) -> None:
    blob = hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()
    if blob != expected_blob or hashlib.sha256(data).hexdigest() != expected_sha256:
        raise ValueError("source blob/hash mismatch")


def verify_source_lock(lock: dict, external_root: Path = EXTERNAL_ROOT) -> dict:
    if lock["reference_sources_sha256"] != hashlib.sha256((ROOT / "reference/sources.json").read_bytes()).hexdigest():
        raise ValueError("reference sources fixture hash differs from lock")
    reference = json.loads((ROOT / "reference/sources.json").read_text())
    pins = {entry["repo"]: entry for entry in reference["repositories"]}
    if {entry["repo"] for entry in lock["repositories"]} != set(pins):
        raise ValueError("source lock repository coverage differs from reference")
    verified = []
    for entry in lock["repositories"]:
        pin = pins[entry["repo"]]
        if entry["commit"] != pin["observed_commit"]:
            raise ValueError("commit differs from reference pin")
        checkout = external_root / entry["directory"]
        if git(checkout, "rev-parse", "HEAD").decode().strip() != entry["commit"]:
            raise ValueError("checkout HEAD differs from locked commit")
        if git(checkout, "rev-parse", "HEAD^{tree}").decode().strip() != entry["tree"]:
            raise ValueError("source tree differs from lock")
        if not set(pin.get("files", {})) <= set(entry["files"]):
            raise ValueError("missing reference-pinned source file")
        for path, record in entry["files"].items():
            if path in pin.get("files", {}) and record["git_blob"] != pin["files"][path]:
                raise ValueError("blob differs from reference pin")
            actual_blob = git(checkout, "rev-parse", f"HEAD:{path}").decode().strip()
            if actual_blob != record["git_blob"]:
                raise ValueError("committed blob differs from lock")
            verify_blob(git(checkout, "show", f"HEAD:{path}"), record["git_blob"], record["sha256"])
            verify_blob((checkout / path).read_bytes(), record["git_blob"], record["sha256"])
        for path, record in entry.get("history_files", {}).items():
            verify_blob(git(checkout, "show", path), record["git_blob"], record["sha256"])
        verified.append({"repo": entry["repo"], "commit": entry["commit"], "files": len(entry["files"]), "license": entry["license"]})
    return {"status": "verified", "repositories": verified, "network": "disabled during verification"}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lock", type=Path, default=ROOT / "locks/source-lock.json")
    parser.add_argument("--external-root", type=Path, default=EXTERNAL_ROOT)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = verify_source_lock(json.loads(args.lock.read_text()), args.external_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
