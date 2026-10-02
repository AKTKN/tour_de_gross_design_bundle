#!/usr/bin/env python3
"""Export independent gross XX/Y C10 circuits, joint faults and Table-6 deltas.

No decoder, distance search, rate sampling or published fit evaluation.
"""
import argparse
import csv
import gzip
import hashlib
import json
import os
from pathlib import Path
from time import perf_counter
import numpy as np
import stim
from scipy import sparse
from gross_design_bandle.bench.artifacts import export_fault_model, file_hash
from gross_design_bandle.codes.reference_profiles import load_reference_code
from gross_design_bandle.lpu.reference import build_reference_lpu
from gross_design_bandle.surgery.deformation import compile_deformation
from gross_design_bandle.circuits.protocol import build_physical_inmodule
from gross_design_bandle.flows.harness import build_benchmark
from gross_design_bandle.validation.connectivity import installed_connectivity
from gross_design_bandle.validation.faults import validate_faults
from gross_design_bandle.noise import NoiseProfile, build_fault_model, emit_noise
from gross_design_bandle.noise.locations import benchmark_locations
from gross_design_bandle.noise.cache import key_for


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir',type=Path,required=True)
    parser.add_argument('--cache-dir',type=Path,default=Path(os.environ.get('GROSS_DESIGN_CACHE_DIR','cache/faults')))
    parser.add_argument('--legacy-json',action='store_true')
    args=parser.parse_args(); args.output_dir.mkdir(parents=True,exist_ok=True)
    root=Path(__file__).resolve().parents[1]
    sources=sorted((root/'src/gross_design_bandle').rglob('*.py'))+[
        Path(__file__).resolve(),root/'tests/test_inmodule_xx_y.py',root/'docs/INMODULE_XX_Y.md',root/'locks/inmodule-xx-y-sources.json']
    def hashes(): return {str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}
    before=hashes()
    def save(name,value):
        (args.output_dir/name).write_text(json.dumps(value,indent=2)+'\n')
    published={r['series']:int(r['N_expanded']) for r in csv.DictReader((root/'reference/table6.csv').open())}
    code=load_reference_code('gross','block_0')
    index={'schema_version':1,'rounds':10,'stim_version':stim.__version__,
        'scope':'independent physical gross XX/Y audit; no rate or distance claim',
        'paper_exact':False,'open_items':['O1','O2','O3','O4','O5'],'benchmarks':{}}
    save('installed_connectivity.json',installed_connectivity(code))
    for op,target in (('XX','X1*X7'),('Y','Y1')):
        started=perf_counter()
        times={}
        name=f'gross_{op}_C10'; df=compile_deformation(build_reference_lpu(code,op)); physical=build_physical_inmodule(df)
        save(name+'_deformation.json',df.to_certificate()); save(name+'_physical.json',physical.to_dict())
        (args.output_dir/(name+'_instrument.stim')).write_text(str(physical.to_stim())+'\n')
        hs={mode:build_benchmark(code,operation=target,rounds=10,deformation=df,split_mode=mode) for mode in ('frame','active')}
        validations={}
        for mode,h in hs.items():
            validations[mode]=h.validate(flow_oracle="stim_reference")
            save(name+'_'+mode+'_harness.json',h.to_dict())
            (args.output_dir/(name+'_'+mode+'_ideal.stim')).write_text(str(h.circuit)+'\n')
        h=hs['frame']; locations,policy=benchmark_locations(code,h,operation=target,rounds=10,deformation=df)
        save(name+'_locations.json',{'policy':policy,'locations':[l.to_dict() for l in locations]})
        times['harness_locations_and_ledgers_seconds']=perf_counter()-started
        cache_key=key_for(h.circuit,locations,artifact='fault_model',profile='a7_uniform_expanded',
                          admission='include_all',grouping='joint_signature_xor')
        initial_hit=(args.cache_dir/'models'/cache_key).is_dir()
        started=perf_counter()
        m=build_fault_model(h.circuit,locations,NoiseProfile('a7_uniform_expanded',.001),
                           admission_policy='include_all',grouping_policy='joint_signature_xor',cache_dir=args.cache_dir)
        times['initial_model_seconds']=perf_counter()-started
        for label,p in (('warm',.001),('changed_p',.002)):
            started=perf_counter()
            reused=build_fault_model(h.circuit,locations,NoiseProfile('a7_uniform_expanded',p),
                          admission_policy='include_all',grouping_policy='joint_signature_xor',cache_dir=args.cache_dir)
            times[label+'_seconds']=perf_counter()-started
            assert reused.raw_signatures==m.raw_signatures and reused.group_signatures==m.group_signatures
            assert (reused.H!=m.H).nnz==(reused.Lambda!=m.Lambda).nnz==0
            for field in ('copy_to_raw','copy_ordinal','admission_mask','admitted_to_copy','admitted_to_group'):
                np.testing.assert_array_equal(getattr(reused,field),getattr(m,field))
            np.testing.assert_allclose(reused.probabilities,p/15,rtol=0,atol=0)
        started=perf_counter()
        artifact = export_fault_model(args.output_dir,name,m)
        times['first_export_seconds']=perf_counter()-started
        started=perf_counter()
        assert export_fault_model(args.output_dir,name,m)==artifact
        times['reused_export_seconds']=perf_counter()-started
        if args.legacy_json:
            with gzip.open(args.output_dir/(name+'_catalogue.json.gz'),'wt',encoding='utf-8') as f:
                json.dump(m.to_dict(),f,separators=(',',':')); f.write('\n')
            sparse.save_npz(args.output_dir/(name+'_H.npz'),m.H); sparse.save_npz(args.output_dir/(name+'_Lambda.npz'),m.Lambda)
        fixed=validate_faults(m,exhaustive=False,counterexample_path=args.output_dir/(name+'_counterexample.json'))
        save(name+'_fixed_faults.json',fixed)
        report=m.discrepancy(published['gross_'+op],policy); save(name+'_N_discrepancy.json',report)
        profiles={}
        for profile_name in ('a7_uniform_expanded','paper_linearized_unequal','standard_categorical_depolarizing'):
            noisy=emit_noise(h.circuit,locations,NoiseProfile(profile_name,.001))
            dem=noisy.detector_error_model(allow_gauge_detectors=False,approximate_disjoint_errors=False)
            (args.output_dir/(name+'_'+profile_name+'.stim')).write_text(str(noisy)+'\n')
            profiles[profile_name]={'strict_DEM_detectors':dem.num_detectors,'strict_DEM_observables':dem.num_observables,
                                     'compact_DEM_errors':dem.num_errors}
        entry={'physical_timing':physical.timing,'validations':validations,'noise_policy':policy,
            'cache':{'initial_model_hit':initial_hit,'model_key':cache_key,
                     'warm_and_changed_p_structure_equal':True,'timings':times},
            'N_raw':len(m.raw),'N_copies':m.N,'N_decoder_groups':len(m.group_signatures),
            'numeric_artifact':str(artifact.relative_to(args.output_dir)),
            'H_shape':list(m.H.shape),'Lambda_shape':list(m.Lambda.shape),
            'fixed_raw_primitives_checked':fixed['checked_raw_primitives'],
            'Table6_N_discrepancy':report,'profiles':profiles}
        index['benchmarks'][name]=entry
        print(name,json.dumps({k:entry[k] for k in ('N_raw','N_copies','N_decoder_groups','fixed_raw_primitives_checked','H_shape','Lambda_shape')}),flush=True)
    if hashes()!=before: raise ValueError('source changed during export')
    index['source_sha256']=before
    index['files']={str(p.relative_to(args.output_dir)):{'bytes':p.stat().st_size,'sha256':file_hash(p)}
                    for p in sorted(args.output_dir.rglob('*')) if p.is_file() and p.name!='index.json'}
    save('index.json',index)


if __name__=='__main__': main()
