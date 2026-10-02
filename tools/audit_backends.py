"""Collect import signatures and the resolved phase-00 environment, without sampling."""
import argparse
import hashlib
import importlib.metadata as metadata
import importlib.util
import inspect
import json
import platform
from pathlib import Path
import sys
from audit_sources import ROOT, EXTERNAL_ROOT


def load_memory_builder():
    path = EXTERNAL_ROOT / "SlidingWindowDecoder/src/build_circuit.py"
    spec = importlib.util.spec_from_file_location("tdg_donor_memory_audit", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.build_circuit


def probe():
    import qldpc.experimental.surgery as surgery
    import relay_bp
    import stim
    functions = {f"qldpc.experimental.surgery.{name}": getattr(surgery, name) for name in (
        "build_gadget", "build_bridge", "build_single_ppm_circuit", "build_joint_ppm_circuit", "keep_only_observable", "logical_state_init")}
    functions.update({"SlidingWindowDecoder.src.build_circuit.build_circuit": load_memory_builder(),
        "relay_bp.RelayDecoderF32": relay_bp.RelayDecoderF32,
        "relay_bp.RelayDecoderF32.decode": relay_bp.RelayDecoderF32.decode,
        "relay_bp.RelayDecoderF32.decode_detailed": relay_bp.RelayDecoderF32.decode_detailed,
        "relay_bp.RelayDecoderF32.decode_batch": relay_bp.RelayDecoderF32.decode_batch,
        "relay_bp.ObservableDecoderRunner": relay_bp.ObservableDecoderRunner})
    return {"python": platform.python_version(), "platform": platform.platform(), "versions": {name: metadata.version(name) for name in ("numpy", "scipy", "stim", "sinter", "qldpc", "relay-bp")}, "signatures": {name: str(inspect.signature(value)) for name, value in functions.items()}, "unavailable_readme_apis": ["relay_bp.RelayDecoderF32.par_decode_batch"], "stim_import_path": stim.__file__, "scope": "imports/signatures only; tiny deterministic interface tests are separate; no sampling"}


def environment_lock():
    packages = {}
    for dist in metadata.distributions():
        name = dist.metadata["Name"].lower().replace("_", "-")
        packages[name] = dist.version
    files = {}
    for name in ("qldpc", "relay-bp", "stim"):
        dist = metadata.distribution(name)
        files[name] = {str(p): hashlib.sha256(dist.locate_file(p).read_bytes()).hexdigest() for p in dist.files if str(p).endswith((".py", ".so")) and dist.locate_file(p).is_file()}
    return {"schema_version": 1, "environment": "tour_de_gross", "python": platform.python_version(), "platform": platform.platform(), "packages": dict(sorted(packages.items())), "installed_backend_files_sha256": files, "scope": "observed import environment; not a validated physical circuit/Relay reproduction lock"}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--environment-output", type=Path)
    args = parser.parse_args()
    args.output.write_text(json.dumps(probe(), indent=2) + "\n")
    if args.environment_output:
        args.environment_output.write_text(json.dumps(environment_lock(), indent=2) + "\n")
