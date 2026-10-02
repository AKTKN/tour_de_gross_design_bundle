#!/usr/bin/env python3
"""Export gross C10 noise populations and fixed-fault evidence, without rates."""
import argparse
import csv
import gzip
import hashlib
import json
import os
from pathlib import Path
from collections import Counter
import stim
from scipy import sparse
from gross_design_bandle.codes.reference_profiles import load_reference_code
from gross_design_bandle.lpu.reference import build_reference_lpu
from gross_design_bandle.surgery.deformation import compile_deformation
from gross_design_bandle.flows.harness import build_benchmark
from gross_design_bandle.noise import NoiseProfile, build_fault_model, emit_noise
from gross_design_bandle.noise.locations import benchmark_locations
from gross_design_bandle.validation.faults import validate_faults
from gross_design_bandle.bench.artifacts import export_fault_model, file_hash


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir',required=True,type=Path)
    parser.add_argument('--cache-dir', type=Path, default=Path(os.environ.get('GROSS_DESIGN_CACHE_DIR', 'cache/faults')))
    parser.add_argument('--legacy-json', action='store_true', help='Also export the large legacy JSON/NPZ catalogue')
    args = parser.parse_args(); args.output_dir.mkdir(parents=True,exist_ok=True)
    root = Path(__file__).resolve().parents[1]
    sources = sorted((root/'src/gross_design_bandle').rglob('*.py'))+[
        Path(__file__).resolve(),root/'tests/test_noise_and_fault_model.py',root/'docs/NOISE_AND_FAULT_MODEL.md',root/'locks/noise-and-fault-sources.json']
    def hashes():
        return {str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}
    before = hashes()
    published = {r['series']:int(r['N_expanded']) for r in csv.DictReader((root/'reference/table6.csv').open())}
    code = load_reference_code('gross','block_0'); df = compile_deformation(build_reference_lpu(code,'X'))
    index = {'schema_version':1,'scope':'C10 independent gross memory/X1 noise audit; no logical-error-rate sampling or distance claim',
        'stim_version':stim.__version__,'p_for_emission':.001,'rounds':10,
        'admission_policy':'include_all','grouping_policy':'joint_signature_xor',
        'strict_paper_equivalence':False,'open_items':['O1','O2','O3','O4','O5'],'benchmarks':{},'files':{}}
    for operation in ('memory','X1'):
        name = f'gross_{operation}_C10'
        h = build_benchmark(code,operation=operation,rounds=10,deformation=df if operation=='X1' else None)
        h.validate()
        ls,policy = benchmark_locations(code,h,operation=operation,rounds=10,deformation=df)
        (args.output_dir/f'{name}_ideal.stim').write_text(str(h.circuit)+'\n')
        (args.output_dir/f'{name}_locations.json').write_text(json.dumps({'policy':policy,
            'locations':[l.to_dict() for l in ls], 'logical_generators':h.logical_generators},indent=2)+'\n')
        entry = {'policy':policy,'physical_locations':len(ls),'locations_by_kind':dict(Counter(l.kind for l in ls)), 'profiles':{}}
        fixed = None
        for profile_name in ('a7_uniform_expanded','paper_linearized_unequal','standard_categorical_depolarizing'):
            profile = NoiseProfile(profile_name,.001)
            noisy = emit_noise(h.circuit,ls,profile)
            dem = noisy.detector_error_model(allow_gauge_detectors=False,approximate_disjoint_errors=False)
            stem = f'{name}_{profile_name}'
            (args.output_dir/f'{stem}.stim').write_text(str(noisy)+'\n')
            info = {'strict_DEM_detectors':dem.num_detectors,'strict_DEM_observables':dem.num_observables,
                'compact_DEM_errors':dem.num_errors,'independent':profile.independent}
            if profile.independent:
                m = build_fault_model(h.circuit,ls,profile,admission_policy='include_all',grouping_policy='joint_signature_xor',cache_dir=args.cache_dir)
                artifact = export_fault_model(args.output_dir, stem, m)
                info['numeric_artifact'] = str(artifact.relative_to(args.output_dir))
                if args.legacy_json:
                    with gzip.open(args.output_dir/f'{stem}_catalogue.json.gz','wt',encoding='utf-8') as f:
                        json.dump(m.to_dict(),f,separators=(',',':')); f.write('\n')
                    sparse.save_npz(args.output_dir/f'{stem}_H.npz',m.H)
                    sparse.save_npz(args.output_dir/f'{stem}_Lambda.npz',m.Lambda)
                info.update({'N_raw':len(m.raw),'N_copies':len(m.copy_to_raw),'N_admitted':m.N,
                    'N_decoder_groups':len(m.group_signatures),'H_shape':list(m.H.shape),'Lambda_shape':list(m.Lambda.shape)})
                if fixed is None:
                    fixed = validate_faults(m,exhaustive=False,counterexample_path=args.output_dir/f'{name}_counterexample.json')
                    (args.output_dir/f'{name}_fixed_faults.json').write_text(json.dumps(fixed,indent=2)+'\n')
                if profile_name=='a7_uniform_expanded':
                    report = m.discrepancy(published['gross_idle' if operation=='memory' else 'gross_X'],policy)
                    info['Table6_N_discrepancy'] = report
                    (args.output_dir/f'{name}_N_discrepancy.json').write_text(json.dumps(report,indent=2)+'\n')
                info['fixed_raw_signatures_checked'] = fixed['checked_raw_primitives']
            else:
                info['Bernoulli_H_Lambda_model'] = 'not applicable: categorical alternatives are mutually exclusive per location'
            entry['profiles'][profile_name] = info
            print(stem,info,flush=True)
        entry['fault_validation_scope'] = {k:v for k,v in fixed.items() if k!='trials'}
        index['benchmarks'][name] = entry
    if hashes()!=before:
        raise ValueError('sources changed during audit export')
    index['source_sha256'] = before
    for p in sorted(args.output_dir.rglob('*')):
        if p.is_file() and p.name!='index.json':
            index['files'][str(p.relative_to(args.output_dir))] = {'bytes':p.stat().st_size,'sha256':file_hash(p)}
    (args.output_dir/'index.json').write_text(json.dumps(index,indent=2)+'\n')


if __name__=='__main__':
    main()
