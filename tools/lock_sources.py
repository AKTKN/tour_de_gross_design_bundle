"""Freeze inspected source bytes from reference commits; no downloads or edits."""
import hashlib
import json
from audit_sources import ROOT, EXTERNAL_ROOT, git, verify_source_lock

FILES = {
    "qLDPC": ["README.md", "LICENSE", "COPYRIGHT", "pyproject.toml", "src/qldpc/experimental/surgery/__init__.py", "src/qldpc/experimental/surgery/circuit.py", "src/qldpc/experimental/surgery/gadget.py", "src/qldpc/experimental/surgery/bridge.py", "experiments/lattice_surgery/README.md"],
    "SlidingWindowDecoder": ["README.md", "src/build_circuit.py", "src/utils.py", "src/include/README.md", "src/include/COPYRIGHT"],
    "relay": ["README.md", "LICENSE.txt", "pyproject.toml", "Cargo.toml", "Cargo.lock", "src/relay_bp/__init__.py", "src/relay_bp/bp/__init__.py", "src/relay_bp/decoder.py", "src/relay_bp/observable_decoder.py", "crates/relay_bp/src/bp/relay.rs", "crates/relay_bp/src/bp/min_sum.rs", "crates/relay_bp_py/src/bp/relay.rs", "crates/relay_bp_py/src/decoder.rs", "crates/relay_bp_py/src/observable_decoder.rs", "tests/testdata/circuits.py"],
    "bicycle-architecture-compiler": ["README.md", "LICENSE", "Cargo.toml"],
}
HISTORY = [
    "1290a2cae83a5f8a16dca09456681159288b8dd6:crates/relay_bp/src/bp/min_sum.rs",
    "1290a2cae83a5f8a16dca09456681159288b8dd6:crates/relay_bp/src/bp/relay.rs",
    "1b41b689ad27128274fc7d0bb93c6ed50135c507:crates/relay_bp/src/bp/min_sum.rs",
    "3f9a80109343f07155598596973f5e98a34dbd5a:crates/relay_bp/src/bp/min_sum.rs",
]


def record(checkout, object_path):
    data = git(checkout, "show", object_path)
    return {"git_blob": git(checkout, "rev-parse", object_path).decode().strip(), "sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)}


if __name__ == "__main__":
    reference = json.loads((ROOT / "reference/sources.json").read_text())
    lock = {"schema_version": 1, "audit_date": "2026-10-02", "scope": "source and import capability audit only; no paper-equivalence certification", "reference_sources_sha256": hashlib.sha256((ROOT / "reference/sources.json").read_bytes()).hexdigest(), "repositories": [], "open_items": {f"O{i}": "unresolved" for i in range(1, 6)}}
    for pin in reference["repositories"]:
        name = pin["repo"].split("/")[-1]
        checkout = EXTERNAL_ROOT / name
        paths = FILES[name]
        entry = {"repo": pin["repo"], "url": f'https://github.com/{pin["repo"]}', "directory": name, "commit": pin["observed_commit"], "tree": git(checkout, "rev-parse", f'{pin["observed_commit"]}^{{tree}}').decode().strip(), "license": "build_circuit.py: no license notice or repository-level license; utils.py: Apache-2.0; src/include: Radford Neal permissive notice (README calls it MIT), with GNU routines caveat" if name == "SlidingWindowDecoder" else "Apache-2.0", "license_paths": [p for p in paths if p in ("LICENSE", "LICENSE.txt", "COPYRIGHT", "src/include/COPYRIGHT", "src/utils.py")], "source_modified": False, "files": {p: record(checkout, f'{pin["observed_commit"]}:{p}') for p in paths}}
        if name == "relay":
            entry["history_files"] = {p: record(checkout, p) for p in HISTORY}
        lock["repositories"].append(entry)
    verify_source_lock(lock)
    (ROOT / "locks/source-lock.json").write_text(json.dumps(lock, indent=2) + "\n")
