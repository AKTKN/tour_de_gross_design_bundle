"""Export one bounded tiny-circuit smoke pilot; never paper performance evidence."""
import argparse
import json
from pathlib import Path
import time

import numpy as np
import stim

from gross_design_bandle.bench.artifacts import export_fault_model, file_hash
from gross_design_bandle.bench.relay import JointRelayAdapter, RelayConfig
from gross_design_bandle.bench.results import append_chunk, read_chunks
from gross_design_bandle.bench.sampling import PilotBudget, run_chunk, run_manifest
from gross_design_bandle.noise import Location, NoiseProfile, build_fault_model


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path, required=True)
    parser.add_argument('--cache-dir', type=Path, required=True)
    args = parser.parse_args()
    start = time.monotonic()
    out = args.output_dir
    out.mkdir(parents=True, exist_ok=True)
    circuit = stim.Circuit('R 0 1 2\nH 0\nCX 0 1\nI 0 2\nCX 0 1\nH 0\nM 0 1 2\nDETECTOR rec[-3]\nDETECTOR rec[-2]\nOBSERVABLE_INCLUDE(0) rec[-3]\nOBSERVABLE_INCLUDE(1) rec[-2]\nOBSERVABLE_INCLUDE(2) rec[-1]')
    locations = tuple(Location(f'data{q}',3,'idle',(q,),'I','small_Bell',3,0,'data',()) for q in (0,2))
    t0 = time.monotonic()
    model = build_fault_model(circuit, locations, NoiseProfile('a7_uniform_expanded', .03),
        admission_policy='include_all', grouping_policy='preserve_copies', cache_dir=args.cache_dir)
    first_seconds = time.monotonic()-t0
    t0 = time.monotonic()
    warm = build_fault_model(circuit, locations, NoiseProfile('a7_uniform_expanded', .03),
        admission_policy='include_all', grouping_policy='preserve_copies', cache_dir=args.cache_dir)
    warm_seconds = time.monotonic()-t0
    assert (warm.H != model.H).nnz == 0 and (warm.Lambda != model.Lambda).nnz == 0
    decoder = JointRelayAdapter.from_fault_model(model, np.full(model.N,.003),
        logical_names=('X-action','Z-action','logical-only'),
        config=RelayConfig(pre_iter=4,num_sets=2,set_max_iter=5,
                           explicit_gammas=np.array([np.full(model.N,.1),np.full(model.N,.2)])))
    manifest = run_manifest(model, decoder, series='small_Bell_smoke', profile_label='independent_tiny_pilot')
    manifest_path = out/'run-manifest.json'
    if manifest_path.exists():
        if json.loads(manifest_path.read_text()) != manifest:
            raise ValueError('run manifest differs on resume')
    else:
        manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True)+'\n')
    chunks = out/'chunks.jsonl'
    budget = PilotBudget(256, 3, 120)
    # One fresh bounded pilot: 3 accessible points, 32 shots each.
    points = [('fixed_weight',1), ('fixed_weight',2), ('bernoulli',.03)]
    existing = read_chunks(chunks)
    for i, (mode, value) in enumerate(points):
        key = (manifest['run_hash'], 'small_Bell_smoke', mode, i, 0)
        if key in existing:
            stored = existing[key]
            if stored['point_value'] != value or stored['counts']['shots'] != 32:
                raise ValueError('stored point differs on resume')
            budget.check(('small_Bell_smoke',mode,i), 32)
            continue
        row = run_chunk(model, decoder, run_hash=manifest['run_hash'], series='small_Bell_smoke',
            mode=mode, point_index=i, point_value=value, chunk_index=0,
            shots=32, budget=budget)
        append_chunk(chunks, row)
    artifact = export_fault_model(out, 'small_Bell', model)
    report = {'pilot_only': True, 'performance_evidence': False,
              'points': len(points), 'shots_per_point': 32,
              'total_shots': 96, 'wall_seconds': time.monotonic()-start,
              'first_model_seconds': first_seconds, 'warm_model_seconds': warm_seconds,
              'fault_model_export': str(artifact.relative_to(out)),
              'run_hash': manifest['run_hash'],
              'open_items': ['O1','O2','O3','O4','O5'],
              'files': {p.name: file_hash(p) for p in (manifest_path,chunks)}}
    if report['wall_seconds'] > 120:
        raise TimeoutError('pilot exceeded total wall-time budget')
    (out/'pilot-report.json').write_text(json.dumps(report, indent=2, sort_keys=True)+'\n')
    print(json.dumps(report, sort_keys=True))


if __name__ == '__main__':
    main()
