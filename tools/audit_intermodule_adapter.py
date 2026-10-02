#!/usr/bin/env python3
"""Export the independent Fig. 13(b) gross C10/K47 audit. No rate sampling."""
import argparse
import json
import os
from pathlib import Path
from time import perf_counter
import numpy as np
import stim
from gross_design_bandle.bench.artifacts import export_fault_model, file_hash
from gross_design_bandle.codes.reference_profiles import load_reference_code
from gross_design_bandle.lpu.reference import build_reference_lpu
from gross_design_bandle.lpu.code_code_adapter import adapter_connectivity
from gross_design_bandle.surgery.deformation import compile_deformation
from gross_design_bandle.circuits.protocol import build_physical_inter
from gross_design_bandle.flows.harness import build_benchmark
from gross_design_bandle.noise import NoiseProfile, build_fault_model, emit_noise
from gross_design_bandle.noise.locations import benchmark_locations
from gross_design_bandle.noise.cache import key_for
from gross_design_bandle.validation.faults import validate_faults


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir',type=Path,required=True)
    parser.add_argument('--cache-dir',type=Path,default=Path(os.environ.get('GROSS_DESIGN_CACHE_DIR','cache/faults')))
    args=parser.parse_args(); args.output_dir.mkdir(parents=True,exist_ok=True)
    root=Path(__file__).resolve().parents[1]
    sources=sorted((root/'src/gross_design_bandle').rglob('*.py'))+[
        Path(__file__).resolve(),root/'tests/test_intermodule_adapter.py',root/'docs/INTERMODULE_ADAPTER.md',
        root/'locks/intermodule-adapter-sources.json']
    def hashes(): return {str(p.relative_to(root)):file_hash(p) for p in sources}
    before=hashes()
    def save(name,value): (args.output_dir/name).write_text(json.dumps(value,indent=2)+'\n')
    codes=tuple(load_reference_code('gross',id) for id in ('module_a','module_b'))
    started=perf_counter(); times={}
    df=compile_deformation(build_reference_lpu(codes[0],'inter_XX',codes[1]))
    physical=build_physical_inter(df)
    save('deformation.json',df.to_certificate()); save('physical.json',physical.to_dict())
    resources=adapter_connectivity(physical); save('resources.json',resources)
    (args.output_dir/'instrument.stim').write_text(str(physical.to_stim())+'\n')
    validations={}; harnesses={}
    for mode in ('frame','active'):
        h=build_benchmark(codes,operation='inter_XX',rounds=10,deformation=df,split_mode=mode)
        validations[mode]=h.validate(); harnesses[mode]=h
        save(mode+'_harness.json',h.to_dict())
        (args.output_dir/(mode+'_ideal.stim')).write_text(str(h.circuit)+'\n')
    h=harnesses['frame']
    locations,policy=benchmark_locations(codes,h,operation='inter_XX',rounds=10,deformation=df)
    save('locations.json',{'policy':policy,'locations':[l.to_dict() for l in locations]})
    times['construction_harness_and_ledgers_seconds']=perf_counter()-started
    key=key_for(h.circuit,locations,artifact='fault_model',profile='a7_uniform_expanded',admission='include_all',grouping='joint_signature_xor')
    initial_hit=(args.cache_dir/'models'/key).is_dir()
    started=perf_counter()
    model=build_fault_model(h.circuit,locations,NoiseProfile('a7_uniform_expanded',.001),
        admission_policy='include_all',grouping_policy='joint_signature_xor',cache_dir=args.cache_dir)
    times['initial_model_seconds']=perf_counter()-started
    for label,p in (('warm',.001),('changed_p',.002)):
        started=perf_counter()
        reused=build_fault_model(h.circuit,locations,NoiseProfile('a7_uniform_expanded',p),
            admission_policy='include_all',grouping_policy='joint_signature_xor',cache_dir=args.cache_dir)
        times[label+'_seconds']=perf_counter()-started
        assert (reused.H!=model.H).nnz==(reused.Lambda!=model.Lambda).nnz==0
        assert reused.raw_signatures==model.raw_signatures and reused.group_signatures==model.group_signatures
        for field in ('copy_to_raw','copy_ordinal','admission_mask','admitted_to_copy','admitted_to_group'):
            np.testing.assert_array_equal(getattr(reused,field),getattr(model,field))
        np.testing.assert_allclose(reused.probabilities,p/15,rtol=0,atol=0)
    started=perf_counter(); artifact=export_fault_model(args.output_dir,'gross_inter_XX_C10_K47',model)
    times['first_export_seconds']=perf_counter()-started
    started=perf_counter(); assert export_fault_model(args.output_dir,'gross_inter_XX_C10_K47',model)==artifact
    times['reused_export_seconds']=perf_counter()-started
    started=perf_counter()
    fixed=validate_faults(model,exhaustive=False,counterexample_path=args.output_dir/'counterexample.json')
    times['stratified_fault_validation_seconds']=perf_counter()-started
    save('fixed_faults.json',fixed)
    discrepancy=model.discrepancy(743456,policy); save('N_discrepancy.json',discrepancy)
    started=perf_counter()
    noisy=emit_noise(h.circuit,locations,model.profile)
    dem=noisy.detector_error_model(allow_gauge_detectors=False)
    (args.output_dir/'a7_uniform_expanded.stim').write_text(str(noisy)+'\n')
    times['noisy_emission_strict_DEM_seconds']=perf_counter()-started
    if hashes()!=before: raise ValueError('source changed during export')
    index={'schema_version':1,'scope':'independent gross Fig13b C10/K47; no rates, decoder or distance claims',
        'paper_exact':False,'open_items':['O1','O2','O3','O4','O5'],'rounds':10,'stim_version':stim.__version__,
        'merged_k':df.merged_k,'observable_profile':h.logical_generators['profile'],
        'published_K23':'unimplemented; actual row definitions unresolved O1',
        'active_qubits':resources['active_qubits'],'installed_qubits':resources['installed_qubits'],
        'physical_timing':physical.timing,'validations':validations,
        'H_shape':list(model.H.shape),'Lambda_shape':list(model.Lambda.shape),
        'N_raw':len(model.raw),'N_copies':model.N,'N_decoder_groups':len(model.group_signatures),
        'fixed_raw_primitives_checked':fixed['checked_raw_primitives'],'Table6_N_discrepancy':discrepancy,
        'noisy_strict_DEM':{'detectors':dem.num_detectors,'observables':dem.num_observables,'compact_errors':dem.num_errors},
        'numeric_artifact':str(artifact.relative_to(args.output_dir)),
        'cache':{'initial_model_hit':initial_hit,'model_key':key,'warm_and_changed_p_structure_equal':True,'timings':times},
        'source_sha256':before,
        'files':{str(p.relative_to(args.output_dir)):{'bytes':p.stat().st_size,'sha256':file_hash(p)}
                 for p in sorted(args.output_dir.rglob('*')) if p.is_file() and p.name!='index.json'}}
    save('index.json',index)
    print(json.dumps({k:index[k] for k in ('merged_k','active_qubits','installed_qubits','N_raw','N_copies','N_decoder_groups','H_shape','Lambda_shape','cache')}),flush=True)


if __name__=='__main__': main()
