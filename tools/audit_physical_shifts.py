#!/usr/bin/env python3
"""Export the independent gross C10 shift channel; no rates or decoding."""
import argparse
import csv
import json
import os
from pathlib import Path
from time import perf_counter
import numpy as np
import stim
from gross_design_bandle.codes import load_reference_code
from gross_design_bandle.circuits.shift import shift_sequence
from gross_design_bandle.flows.shift import build_shift_benchmark
from gross_design_bandle.noise.shift import shift_locations
from gross_design_bandle.noise import NoiseProfile, build_fault_model, emit_noise
from gross_design_bandle.noise.cache import key_for
from gross_design_bandle.bench.artifacts import export_fault_model, file_hash
from gross_design_bandle.validation.faults import validate_faults
from gross_design_bandle.algebra.logical_basis import derive_shift_action


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir',type=Path,required=True)
    parser.add_argument('--cache-dir',type=Path,default=Path(os.environ.get('GROSS_DESIGN_CACHE_DIR','cache/faults')))
    args=parser.parse_args(); out=args.output_dir; out.mkdir(parents=True,exist_ok=True)
    root=Path(__file__).resolve().parents[1]
    sources=sorted((root/'src/gross_design_bandle').rglob('*.py'))+[
        Path(__file__).resolve(),root/'tests/test_physical_shifts.py',root/'docs/PHYSICAL_SHIFTS.md',root/'locks/shift-sources.json']
    def hashes(): return {str(p.relative_to(root)):file_hash(p) for p in sources}
    before=hashes()
    def save(name,value): (out/name).write_text(json.dumps(value,indent=2)+'\n')
    times={}; started=perf_counter(); code=load_reference_code('gross','block_0')
    seq=shift_sequence(code,10); h=build_shift_benchmark(code,10)
    save('gross_shift_C10_harness.json',h.to_dict())
    save('gross_shift_C10_roles_timing.json',{'routing':seq.plan.to_dict(),'ledger':seq.ledger(),
        'roles_by_tick':{str(t):{q:seq.role_at(q,t) for q in seq.register} for t in range(seq.duration)}})
    (out/'gross_shift_C10_ideal.stim').write_text(str(h.circuit)+'\n')
    (out/'gross_shift_C10_physical.stim').write_text(str(h.physical_body)+'\n')
    validations=h.validate()
    locations,policy=shift_locations(code,h,10)
    save('gross_shift_C10_locations.json',{'policy':policy,'locations':[l.to_dict() for l in locations]})
    save('gross_shift_x_action.json',derive_shift_action(code,*seq.plan.delta).to_dict())
    times['harness_locations_validation_seconds']=perf_counter()-started
    profile=NoiseProfile('a7_uniform_expanded',.001)
    key=key_for(h.circuit,locations,artifact='fault_model',profile=profile.name,
                admission='include_all',grouping='joint_signature_xor')
    hit=(args.cache_dir/'models'/key).is_dir()
    def build(p):
        return build_fault_model(h.circuit,locations,NoiseProfile(profile.name,p),
            admission_policy='include_all',grouping_policy='joint_signature_xor',cache_dir=args.cache_dir)
    started=perf_counter(); m=build(.001); times['initial_model_seconds']=perf_counter()-started
    for label,p in (('warm',.001),('changed_p',.002)):
        started=perf_counter(); reused=build(p); times[label+'_seconds']=perf_counter()-started
        assert reused.raw_signatures==m.raw_signatures and reused.group_signatures==m.group_signatures
        assert (reused.H!=m.H).nnz==(reused.Lambda!=m.Lambda).nnz==0
        for field in ('copy_to_raw','copy_ordinal','admission_mask','admitted_to_copy','admitted_to_group'):
            np.testing.assert_array_equal(getattr(m,field),getattr(reused,field))
        np.testing.assert_allclose(reused.probabilities,p/15,rtol=0,atol=0)
    started=perf_counter(); artifact=export_fault_model(out,'gross_shift_C10',m)
    times['export_seconds']=perf_counter()-started
    started=perf_counter()
    fixed=validate_faults(m,exhaustive=False,counterexample_path=out/'counterexample.json')
    times['independent_fault_strata_seconds']=perf_counter()-started
    save('gross_shift_C10_fixed_faults.json',fixed)
    published=next(int(r['N_expanded']) for r in csv.DictReader((root/'reference/table6.csv').open()) if r['series']=='gross_shift')
    discrepancy=m.discrepancy(published,policy); save('gross_shift_C10_N_discrepancy.json',discrepancy)
    profiles={}
    for name in ('a7_uniform_expanded','paper_linearized_unequal','standard_categorical_depolarizing'):
        noisy=emit_noise(h.circuit,locations,NoiseProfile(name,.001))
        dem=noisy.detector_error_model(allow_gauge_detectors=False,approximate_disjoint_errors=False)
        (out/('gross_shift_C10_'+name+'.stim')).write_text(str(noisy)+'\n')
        profiles[name]={'strict_DEM_detectors':dem.num_detectors,'strict_DEM_observables':dem.num_observables,
                        'compact_DEM_errors':dem.num_errors}
    if hashes()!=before: raise ValueError('source changed during audit')
    index={'schema_version':1,'phase':'09','branch':'feature/09_shift_automorphism','worktree':str(root),
        'instructions':10,'normalization':'P_circuit/10','paper_exact':False,'sampled_rates':False,'stim_version':stim.__version__,
        'open_items':['O1','O2','O3','O4','O5'],'timing':seq.validate(),'validations':validations,
        'profiles':profiles,'policy':policy,'N_raw':len(m.raw),'N_copies':m.N,
        'N_decoder_groups':len(m.group_signatures),'H_shape':list(m.H.shape),'Lambda_shape':list(m.Lambda.shape),
        'fixed_raw_primitives_checked':fixed['checked_raw_primitives'],'Table6_N_discrepancy':discrepancy,
        'numeric_artifact':str(artifact.relative_to(out)),
        'cache':{'initial_model_hit':hit,'model_key':key,'warm_changed_p_structure_equal':True,'timings':times},
        'source_sha256':before,
        'files':{str(p.relative_to(out)):{'bytes':p.stat().st_size,'sha256':file_hash(p)} for p in sorted(out.rglob('*')) if p.is_file() and p.name!='index.json'}}
    save('index.json',index)
    print(json.dumps({k:index[k] for k in ('N_raw','N_copies','N_decoder_groups','H_shape','Lambda_shape','fixed_raw_primitives_checked','cache')},indent=2),flush=True)


if __name__=='__main__': main()
