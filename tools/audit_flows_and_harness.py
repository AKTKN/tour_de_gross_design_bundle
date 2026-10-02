#!/usr/bin/env python3
"""Export phase05 C10 ideal harnesses and fixed-fault integrity evidence.

No stochastic pilot, Relay call, primitive catalogue or distance job is run.
"""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
import stim
from gross_design_bandle.codes.reference_profiles import load_reference_code
from gross_design_bandle.lpu.reference import build_reference_lpu
from gross_design_bandle.surgery.deformation import compile_deformation
from gross_design_bandle.flows.harness import build_benchmark
from gross_design_bandle.flows.signatures import fault_signature, inject_fixed_fault


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args(); args.output_dir.mkdir(parents=True,exist_ok=True)
    root = Path(__file__).resolve().parents[1]
    source_paths = list((root/'src/gross_design_bandle/flows').glob('*.py')) + [Path(__file__).resolve(),root/'tests/test_flows_and_harness.py',root/'docs/FLOWS_AND_HARNESS.md',root/'locks/flows-and-harness-sources.json']
    source_hashes = {str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in source_paths}
    code = load_reference_code('gross','block_0')
    df = compile_deformation(build_reference_lpu(code,'X'))
    index = {'scope':'noiseless construction and fixed-fault oracle evidence only',
             'stim_version':stim.__version__, 'source':'locks/flows-and-harness-sources.json',
             'rounds':10, 'files':{}, 'validations':{}}
    for operation,mode in [('memory','frame'),('X1','frame'),('X1','active')]:
        name = f'gross_{operation}_C10_{mode}'
        h = build_benchmark(code,operation=operation,rounds=10,
                            deformation=df if operation=='X1' else None,split_mode=mode)
        validation = h.validate()
        ds,os = h.circuit.compile_detector_sampler(seed=535).sample(4,separate_observables=True)
        if ds.any() or os.any():
            raise ValueError('nonzero noiseless benchmark result')
        validation['bounded_noiseless_oracle_trajectories'] = 4
        index['validations'][name] = validation
        (args.output_dir/f'{name}.stim').write_text(str(h.circuit)+'\n')
        (args.output_dir/f'{name}.json').write_text(json.dumps(h.to_dict(),indent=2)+'\n')
        print(name,validation,flush=True)
        # One fixed Y fault per physical gate kind/measurement-phase bucket.
        # These signatures validate joint effects; their count is not Table-6 N.
        seen = set(); trials = []; measurements = 0
        boundaries = [0,1,161,9*161,10*161,10*161+18,10*161+18+144,10*161+18+288]
        for i,op in enumerate(h.circuit.flattened()):
            ts = op.targets_copy()
            phase = sum(measurements>=b for b in boundaries)
            key = (phase,op.name)
            if key not in seen and op.name in ('R','RX','CX','CY','CZ','M','MX','MPP') and not any(t.is_measurement_record_target for t in ts):
                seen.add(key)
                q = next(t.value for t in ts if not t.is_combiner)
                x = z = 1<<q
                expected = fault_signature(h.circuit,i,x,z)
                actual = tuple(a[0].astype(np.uint8) for a in inject_fixed_fault(h.circuit,i,x,z).compile_detector_sampler(seed=54).sample(1,separate_observables=True))
                trial = {'after_instruction':i,'gate':op.name,'measurement_count':measurements,
                         'phase_bucket':phase,'joint_fault':{'x':x,'z':z},
                         'expected':[a.tolist() for a in expected],'actual':[a.tolist() for a in actual]}
                trials.append(trial)
                if not all(np.array_equal(a,b) for a,b in zip(expected,actual)):
                    (args.output_dir/f'{name}_counterexample.json').write_text(json.dumps(trial,indent=2)+'\n')
                    raise ValueError('fixed-fault counterexample exported')
            measurements += stim.Circuit(str(op)).num_measurements
        (args.output_dir/f'{name}_fixed_faults.json').write_text(json.dumps({'scope':'fixed oracle injections; no Monte Carlo data','trials':trials},indent=2)+'\n')
    for path in sorted(args.output_dir.iterdir()):
        if path.is_file() and path.name!='index.json':
            index['files'][path.name] = {'bytes':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
    current_hashes = {str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in source_paths}
    if current_hashes != source_hashes:
        raise ValueError('implementation changed during evidence export')
    index['implementation_sha256'] = source_hashes
    (args.output_dir/'index.json').write_text(json.dumps(index,indent=2)+'\n')


if __name__=='__main__':
    main()
