#!/usr/bin/env python3
"""Export all fixed phase10 profiles and bounded A.8 inputs. No solver/sampler."""
import argparse
import csv
import gc
import hashlib
import json
import os
from pathlib import Path
from time import perf_counter
import numpy as np
import stim
from gross_design_bandle.bench.two_gross import PROFILES, build_two_gross
from gross_design_bandle.bench.artifacts import export_fault_model, file_hash
from gross_design_bandle.noise import NoiseProfile, build_fault_model, emit_noise
from gross_design_bandle.noise.cache import key_for
from gross_design_bandle.validation.phenomenological import prepare_phenomenological_jobs
from gross_design_bandle.surgery.ports import embed


def structural_digest(model):
    """Checksum every structural value without retaining a second catalogue."""
    digest = hashlib.sha256()
    def array(name, value):
        digest.update((name+':'+str(value.shape)+':'+value.dtype.str+';').encode())
        digest.update(memoryview(np.ascontiguousarray(value)).cast('B'))
    for name in ('H','Lambda'):
        matrix = getattr(model,name)
        digest.update((name+':'+str(matrix.shape)+';').encode())
        for field in ('data','indices','indptr'): array(name+'/'+field,getattr(matrix,field))
    for field in ('copy_to_raw','copy_ordinal','admission_mask','admitted_to_copy','admitted_to_group'):
        array(field,getattr(model,field))
    width = (model.H.shape[0]+model.Lambda.shape[0]+7)//8
    for field in ('raw_signatures','group_signatures'):
        values = getattr(model,field); digest.update((field+':'+str(len(values))+';').encode())
        for value in values: digest.update(int(value).to_bytes(width,'little'))
    return digest.hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path, required=True)
    parser.add_argument('--cache-dir', type=Path, default=Path(os.environ.get('GROSS_DESIGN_CACHE_DIR','cache/faults')))
    args = parser.parse_args(); out = args.output_dir; out.mkdir(parents=True,exist_ok=True)
    root = Path(__file__).resolve().parents[1]
    sources = sorted((root/'src/gross_design_bandle').rglob('*.py'))+[
        Path(__file__).resolve(),root/'tests/test_two_gross_extension.py',root/'docs/TWO_GROSS_EXTENSION.md',
        root/'locks/two-gross-extension-sources.json']
    def hashes(): return {str(p.relative_to(root)):file_hash(p) for p in sources}
    before = hashes()
    def save(path,value): path.write_text(json.dumps(value,indent=2)+'\n')
    table = {r['series']:int(r['N_expanded']) for r in csv.DictReader((root/'reference/table6.csv').open())}
    summary = []; jobs_saved = set()
    for profile in PROFILES:
        path = out/profile.name; path.mkdir(exist_ok=True); times = {}; t = perf_counter()
        construction = build_two_gross(profile.name); h = construction.harness
        validations = h.validate(); locations, policy = construction.locations()
        times['construction_locations_validation_seconds'] = perf_counter()-t
        save(path/'harness.json', h.to_dict())
        (path/'ideal.stim').write_text(str(h.circuit)+'\n')
        (path/'physical.stim').write_text(str(h.physical_body)+'\n')
        save(path/'locations.json', {'policy':policy,'locations':[l.to_dict() for l in locations]})
        physical = construction.physical
        if construction.deformation is not None:
            df = construction.deformation
            save(path/'deformation.json', df.to_certificate())
            save(path/'physical.json', physical.to_dict())
            # C17/C18 share intrinsic phenomenological inputs; no duplicate job.
            if df.lpu.operation not in jobs_saved:
                jobs = prepare_phenomenological_jobs(df); jobpath = out/('A8_'+df.lpu.operation)
                jobpath.mkdir(exist_ok=True); metadata = jobs.manifest()
                metadata['origin_profile'] = profile.to_dict()
                for kind in ('spatial_M','spatial_q','temporal_M','temporal_q'):
                    np.save(jobpath/(kind+'.npy'),getattr(jobs,kind),allow_pickle=False)
                metadata['files'] = {p.name:{'bytes':p.stat().st_size,'sha256':file_hash(p)}
                                     for p in sorted(jobpath.glob('*.npy'))}
                candidate = embed(construction.codes[0].logical_z[0], jobs.register)
                n = len(jobs.register); q = jobs.spatial_q[0]
                partner = next(p for p in jobs.spatial_q if (int(p[:n]@q[n:])+int(p[n:]@q[:n]))%2)
                save(jobpath/'candidate_witnesses.json', {
                    'scope':'feasible candidates only; no optimization or lower bound',
                    'temporal':{'q_index':0,'bits':list(candidate.x+candidate.z),
                                'check':jobs.check_witness('temporal',0,candidate.x+candidate.z)},
                    'spatial':{'q_index':0,'bits':partner.tolist(),
                               'check':jobs.check_witness('spatial',0,partner)}})
                save(jobpath/'manifest.json',metadata); jobs_saved.add(df.lpu.operation)
        elif profile.operation=='shift':
            save(path/'routing_roles.json', {'plan':physical.plan.to_dict(),'ledger':physical.ledger(),
                'roles_by_tick':{str(t):{q:physical.role_at(q,t) for q in physical.register} for t in range(physical.duration)}})
        else:
            save(path/'physical.json',physical.to_dict())
        noise = NoiseProfile('a7_uniform_expanded',.001)
        key = key_for(h.circuit,locations,artifact='fault_model',profile=noise.name,
                      admission='include_all',grouping='joint_signature_xor')
        checked = json.loads((root/'evidence/phase10/fault_checks'/(profile.name+'.json')).read_text())
        if checked['model_key'] != key or checked['profile'] != profile.to_dict():
            raise ValueError('independent numerical fault evidence does not match this physical profile')
        for name, expected in checked['source_sha256'].items():
            if file_hash(root/'src/gross_design_bandle'/name) != expected:
                raise ValueError('independent fault oracle source changed; rerun checks')
        # These are actual forward/Stim/reverse signatures, not a cached test
        # pass. Tests execute them again; export only packages their evidence.
        save(path/'fixed_faults.json',checked)
        initial_hit = (args.cache_dir/'models'/key).is_dir()
        t = perf_counter()
        model = build_fault_model(h.circuit,locations,noise,admission_policy='include_all',
                                   grouping_policy='joint_signature_xor',cache_dir=args.cache_dir)
        times['initial_model_seconds'] = perf_counter()-t
        counts = {'N_raw':len(model.raw),'N_copies':model.N,'N_decoder_groups':len(model.group_signatures),
                  'H_shape':list(model.H.shape),'Lambda_shape':list(model.Lambda.shape)}
        discrepancy = model.discrepancy(table[profile.name],policy) if profile.published_series else None
        t = perf_counter(); artifact = export_fault_model(path,profile.name,model)
        times['export_seconds'] = perf_counter()-t
        structural_sha256 = structural_digest(model)
        # Two simultaneous C18/K47 Python catalogues can exceed local memory.
        # Keep the complete content checksum and release each model in turn.
        del model; gc.collect()
        for label,p in (('warm',.001),('changed_p',.002)):
            t = perf_counter()
            reused = build_fault_model(h.circuit,locations,NoiseProfile(noise.name,p),
                admission_policy='include_all',grouping_policy='joint_signature_xor',cache_dir=args.cache_dir)
            times[label+'_seconds'] = perf_counter()-t
            assert structural_digest(reused)==structural_sha256
            np.testing.assert_allclose(reused.probabilities,p/15,rtol=0,atol=0)
            del reused; gc.collect()
        save(path/'population.json', discrepancy if discrepancy else {
            'N_raw':counts['N_raw'],'N_include_all':counts['N_copies'],'Table6_comparison':None,
            'reason':'two-gross surgery is an extension; no Table6 series'})
        t = perf_counter(); noisy = emit_noise(h.circuit,locations,noise)
        dem = noisy.detector_error_model(allow_gauge_detectors=False,approximate_disjoint_errors=False)
        (path/'a7_uniform_expanded.stim').write_text(str(noisy)+'\n')
        times['noisy_emission_DEM_seconds'] = perf_counter()-t
        record = {'profile':profile.to_dict(),'validations':validations,
                  **counts,
                  'independent_raw_faults_checked':checked['audit']['checked_raw_primitives'],
                  'Table6_N_discrepancy':discrepancy,'noise_policy':policy,
                  'strict_noisy_DEM':{'detectors':dem.num_detectors,'observables':dem.num_observables,
                                       'compact_errors':dem.num_errors},
                  'numeric_artifact':str(artifact.relative_to(out)),
                  'cache':{'initial_hit':initial_hit,'key':key,'warm_changed_p_structure_equal':True,
                           'structural_sha256':structural_sha256,'timings':times}}
        save(path/'summary.json',record); summary.append(record)
        print(json.dumps({'profile':profile.name,'N':counts['N_copies'],'timings':times}),flush=True)
        del construction, h, locations, physical, noisy, dem
        gc.collect()
    if hashes()!=before: raise ValueError('source changed during export')
    save(out/'index.json',{'schema_version':1,'phase':'10','branch':'feature/10_two_gross_extension',
        'worktree':str(root),'profiles':summary,'solver_jobs':'prepared_not_launched',
        'solver_backend_tested':False,'sampled_rates':False,'paper_exact':False,
        'open_items':['O1','O2','O3','O4','O5'],'stim_version':stim.__version__,
        'source_sha256':before,'files':{str(p.relative_to(out)):{'bytes':p.stat().st_size,'sha256':file_hash(p)}
            for p in sorted(out.rglob('*')) if p.is_file() and p.name!='index.json'}})


if __name__=='__main__': main()
