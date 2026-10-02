#!/usr/bin/env python3
"""Export bounded ideal-only symbolic protocols and direct branch residuals."""
import argparse
import hashlib
from itertools import product
import json
from pathlib import Path

import numpy as np

from gross_design_bandle.algebra.pauli import Pauli
from gross_design_bandle.codes import load_reference_code
from gross_design_bandle.lpu.reference import build_reference_lpu
from gross_design_bandle.surgery.deformation import compile_deformation
from gross_design_bandle.surgery.graph import AuxiliaryGraph, Edge
from gross_design_bandle.surgery.ports import PortMap
from gross_design_bandle.surgery.protocol import build_ideal_protocol
from gross_design_bandle.validation.instrument import dense_branch, pauli_matrix


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    data = ("toy:q0", "toy:q1")
    graph = AuxiliaryGraph(("v0", "v1"), (Edge("a", ("v0", "v1"), "local tiny oracle"),), (), "tiny")
    ports = PortMap(graph.vertices, (Pauli.from_word("YI", data), Pauli.from_word("IZ", data)),
                    ("toy",), Pauli.from_word("YZ", data))
    toy = build_ideal_protocol(graph, ports, rounds=2, protocol_id="two_vertex_YZ")
    code = load_reference_code("gross", "block_a")
    df = compile_deformation(build_reference_lpu(code, "X"))
    gross = build_ideal_protocol(df.graph, df.lpu.ports, rounds=3, deformation=df, protocol_id="gross_X1")
    index = {}
    for name, protocol in (("two_vertex_YZ", toy), ("gross_X1", gross)):
        symbolic = args.output_dir / f"{name}.json"
        symbolic.write_text(json.dumps(protocol.to_dict(), indent=2) + "\n")
        stim_path = args.output_dir / f"{name}.stim"
        stim_path.write_text("# IDEAL ONLY: oracle MPP; no noisy gadget or detector claim\n" + str(protocol.to_stim()))
        for path in (symbolic, stim_path):
            index[path.name] = {"sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "bytes": path.stat().st_size}
    residuals = []
    completeness = np.zeros((4, 4), dtype=complex)
    for s in product((0, 1), repeat=2):
        for z in product((0, 1), repeat=1):
            raw = dense_branch(toy, s, z, rounds=2)
            t, q = toy.frame.evaluate(dict(zip(toy.frame.edge_outcome_ids, z)))
            corrected = pauli_matrix(q) @ raw
            m = sum(s) % 2
            expected = .5*(-1)**sum(a*b for a, b in zip(s, t))*(np.eye(4)+(-1)**m*pauli_matrix(ports.target))/2
            residual = float(np.max(np.abs(corrected-expected)))
            if residual > 1e-12:
                raise AssertionError(f"branch {s,z} residual {residual}")
            completeness += corrected.conj().T @ corrected
            residuals.append({"vertex_bits": list(s), "edge_bits": list(z), "t": list(t),
                              "outcome": m, "max_abs_residual": residual})
    complete_residual = float(np.max(np.abs(completeness-np.eye(4))))
    if complete_residual > 1e-12:
        raise AssertionError("instrument is not trace preserving when outcomes are summed")
    report = {"schema_version": 1, "ideal_only": True, "branches": residuals,
              "completeness_max_abs_residual": complete_residual,
              "artifacts": index, "gross_scope": "Symbolic oracle export; tests/test_ideal_protocol.py validates encoded states",
              "open_items": ["O1", "O2", "O3", "O4", "O5"]}
    (args.output_dir / "index.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"branches_checked": len(residuals), "max_abs_residual": max(r["max_abs_residual"] for r in residuals),
                      "completeness_max_abs_residual": complete_residual, "files": list(index)}))


if __name__ == "__main__":
    main()
