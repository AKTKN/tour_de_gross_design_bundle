"""Export eight bounded phase-02 signed certificates; no backend or solver jobs."""
import argparse
from hashlib import sha256
import json
from pathlib import Path

from gross_design_bandle.codes.reference_profiles import load_reference_code
from gross_design_bandle.lpu.reference import build_reference_lpu
from gross_design_bandle.surgery.deformation import compile_deformation


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    summaries = []
    for profile in ("gross", "two_gross"):
        a, b = (load_reference_code(profile, block) for block in ("block_a", "block_b"))
        for operation in ("X", "XX", "Y", "inter_XX"):
            lpu = build_reference_lpu(a, operation, b if operation == "inter_XX" else None)
            deformation = compile_deformation(lpu)
            path = args.output_dir / f"{profile}-{operation}.json"
            deformation.save_certificate(path)
            raw = path.read_bytes()
            summary = {"code": profile, "operation": operation, "certificate": path.name,
                       "bytes": len(raw), "sha256": sha256(raw).hexdigest(),
                       "vertices": len(lpu.graph.vertices), "edges": len(lpu.graph.edges),
                       "selected_cycles": len(lpu.graph.cycles),
                       "omitted_cycle_complement": len(deformation.omitted_cycles),
                       "merged_k": deformation.merged_k, "fixed_input_logical_rank": deformation.fixed_input["rank"],
                       "installed_full_census": lpu.installed_full_census}
            summaries.append(summary)
            print(json.dumps(summary), flush=True)
    report = {"scope": "Signed algebra only; no physical circuits, instrument verification, distance, decoding or sampling",
              "O1_O5": "Remain unresolved; not assumed by phase-02 algebra", "results": summaries}
    (args.output_dir / "index.json").write_text(json.dumps(report, indent=2) + "\n")


if __name__ == "__main__":
    main()
