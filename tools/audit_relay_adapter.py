#!/usr/bin/env python3
"""Bounded phase-11 source, fixed-vector and compact artifact audit; no sampling."""
import argparse
from dataclasses import replace
import json
from pathlib import Path
from time import perf_counter

import numpy as np
from scipy import sparse
import stim

from audit_sources import EXTERNAL_ROOT, git, verify_blob, verify_source_lock
from gross_design_bandle.bench.artifacts import export_fault_model, file_hash, read_bundle, write_bundle
from gross_design_bandle.bench.relay import JointRelayAdapter, RelayConfig, matrix_identity, summarize
from gross_design_bandle.noise import Location, NoiseProfile, build_fault_model
from gross_design_bandle.noise.cache import implementation_identity, key_for
from gross_design_bandle.validation.relay import trace_current_relay


def jsonable(value):
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, dict):
        return {k:jsonable(v) for k,v in value.items()}
    if isinstance(value, (list,tuple)):
        return [jsonable(v) for v in value]
    return value


def outcome(value):
    return jsonable(vars(value))


def save_numeric(path, metadata, arrays):
    """Reuse a checksummed identical bundle; never replace conflicting inputs."""
    if path.exists():
        old_metadata, old_arrays = read_bundle(path)
        if old_metadata != jsonable(metadata) or set(old_arrays) != set(arrays):
            raise ValueError('existing decoder artifact has different metadata or arrays')
        if any(not np.array_equal(old_arrays[k],v) for k,v in arrays.items()):
            raise ValueError('existing decoder artifact has different numerical inputs')
    else:
        write_bundle(path,metadata,arrays)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path, required=True)
    parser.add_argument('--cache-dir', type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    out = args.output_dir
    out.mkdir(parents=True,exist_ok=True)
    sources = ['src/gross_design_bandle/bench/relay.py',
        'src/gross_design_bandle/validation/relay.py', 'tools/audit_relay_adapter.py',
        'locks/relay-adapter-sources.json','docs/RELAY_ADAPTER.md','tests/test_relay_adapter.py']
    before = {name:file_hash(root/name) for name in sources}
    def save(name,data):
        (out/name).write_text(json.dumps(jsonable(data),indent=2)+'\n')
    locked = json.loads((root/'locks/source-lock.json').read_text())
    verification = verify_source_lock(locked)
    supplemental = json.loads((root/'locks/relay-adapter-sources.json').read_text())
    checkout = EXTERNAL_ROOT/'relay'
    for path,record in supplemental['backend']['inspected_files'].items():
        committed = git(checkout,'show',f"{supplemental['backend']['commit']}:{path}")
        verify_blob(committed,record['git_blob'],record['sha256'])
        verify_blob((checkout/path).read_bytes(),record['git_blob'],record['sha256'])
    if file_hash(root/'reference/relay_table7.json') != supplemental['reference_relay_table7_sha256']:
        raise ValueError('Table-7 fixture hash changed')
    verification['phase11_inspected_files'] = supplemental['backend']['inspected_files']
    verification['first_public_release'] = git(checkout,'show','-s','--format=%H %cI',
        '1290a2cae83a5f8a16dca09456681159288b8dd6').decode().strip()
    verification['O2'] = 'unresolved; inspected source does not establish historical keys, priors or column policy'
    save('source-verification.json',verification)

    c = stim.Circuit('R 0 1 2\nH 0\nCX 0 1\nI 0 2\nCX 0 1\nH 0\nM 0 1 2\nDETECTOR rec[-3]\nDETECTOR rec[-2]\nOBSERVABLE_INCLUDE(0) rec[-3]\nOBSERVABLE_INCLUDE(1) rec[-2]\nOBSERVABLE_INCLUDE(2) rec[-1]')
    locations = tuple(Location(f'data{q}',3,'idle',(q,),'I','small_Bell',3,0,'data',()) for q in (0,2))
    policy = dict(admission_policy='include_all',grouping_policy='preserve_copies')
    noise = NoiseProfile('a7_uniform_expanded',.03)
    timings = {}
    def build(name,profile,cache):
        t = perf_counter()
        model = build_fault_model(c,locations,profile,cache_dir=cache,**policy)
        timings[name] = perf_counter()-t
        return model
    cold = build('uncached_seconds',noise,False)
    key = key_for(c,locations,artifact='fault_model',profile=noise.name,
                  admission='include_all',grouping='preserve_copies')
    existed = (args.cache_dir/'models'/key).exists()
    cached = build('initial_cache_seconds',noise,args.cache_dir)
    warm = build('warm_seconds',noise,args.cache_dir)
    changed = build('changed_p_seconds',replace(noise,p=.04),args.cache_dir)
    for other in (cached,warm,changed):
        assert matrix_identity(cold.H)==matrix_identity(other.H)
        assert matrix_identity(cold.Lambda)==matrix_identity(other.Lambda)
        assert cold.raw_signatures==other.raw_signatures
        for name in ('copy_to_raw','copy_ordinal','admission_mask','admitted_to_copy','admitted_to_group'):
            assert np.array_equal(getattr(cold,name),getattr(other,name))
    assert not np.array_equal(warm.probabilities,changed.probabilities)
    export_started = perf_counter()
    model_path = export_fault_model(out,'small_Bell',warm)
    timings['native_export_seconds'] = perf_counter()-export_started
    fixed_priors = np.full(warm.N,.003)
    config = RelayConfig(pre_iter=4,num_sets=2,set_max_iter=5,
        explicit_gammas=np.array([np.linspace(.1,.2,warm.N),np.linspace(-.3,.4,warm.N),np.linspace(.45,-.2,warm.N)]))
    decoder = JointRelayAdapter.from_fault_model(warm,fixed_priors,
        logical_names=('X-action','Z-action','logical-only'),config=config)
    second = JointRelayAdapter.from_fault_model(changed,fixed_priors,
        logical_names=decoder.logical_names,config=config)
    assert decoder.manifest()['prior_policy']==second.manifest()['prior_policy']
    raw_table7 = json.loads((root/'reference/relay_table7.json').read_text())
    arrays = {'priors':decoder.priors,'explicit_gammas':config.explicit_gammas,
              'input_to_decoder':decoder.input_to_decoder}
    save_numeric(out/'decoder_inputs',decoder.manifest(historical_raw_parameters=raw_table7),arrays)
    metadata,loaded = read_bundle(out/'decoder_inputs')
    for name,value in arrays.items():
        assert np.array_equal(loaded[name],value)
    grouped = JointRelayAdapter.from_fault_model(warm,fixed_priors,
        logical_names=decoder.logical_names,
        config=RelayConfig(pre_iter=4,num_sets=0,set_max_iter=1),graph_profile='joint_signature_xor')
    grouped_arrays = {'priors':grouped.priors,'input_to_decoder':grouped.input_to_decoder}
    for name in ('H','Lambda'):
        for field in ('data','indices','indptr'):
            grouped_arrays[name+'_'+field] = getattr(getattr(grouped,name),field)
    save_numeric(out/'grouped_decoder_inputs',grouped.manifest(historical_raw_parameters=raw_table7),grouped_arrays)
    read_bundle(out/'grouped_decoder_inputs')
    errors = np.zeros((5,warm.N),dtype=np.uint8)
    for row,column in enumerate((0,5,10,15),start=1):
        errors[row,column] = 1
    syndromes = np.asarray(warm.H @ errors.T).T % 2
    actions = np.asarray(warm.Lambda @ errors.T).T % 2
    results = decoder.decode_batch(syndromes)
    save('small-circuit-scoring.json',{'scope':'five fixed injected vectors, not Monte Carlo or rate observations',
        'errors':errors,'syndromes':syndromes,'logical_truth':actions,
        'results':[outcome(r) for r in results], 'counts':summarize(results,actions)})

    H = sparse.csc_matrix([[1,1,0,0],[0,1,1,0],[0,0,1,1],[1,0,0,1]],dtype=np.uint8)
    L = sparse.csc_matrix([[1,0,1,0],[0,1,0,1]],dtype=np.uint8)
    sigma = np.ones(4,dtype=np.uint8)
    for precision in ('float32','float64'):
        cfg = RelayConfig(precision=precision,pre_iter=4,num_sets=2,set_max_iter=10,
            explicit_gammas=np.array([[.1]*4,[-.3,-.067,.167,.4],[.4,-.3,.4,-.3]]),stopping_criterion='all')
        d = JointRelayAdapter(H,[.004,.003,.006,.005],L,logical_names=('X','Z'),config=cfg)
        result = d.decode(sigma)
        oracle = trace_current_relay(H.toarray(),d.priors,sigma,cfg)
        assert result.success==oracle['success'] and np.array_equal(result.correction,oracle['correction'])
        assert result.iterations==oracle['iterations']
        save(precision+'-recurrence.json',{'manifest':d.manifest(historical_raw_parameters=raw_table7),
            'H':H.toarray(),'Lambda':L.toarray(),'priors':d.priors,
            'explicit_gammas':cfg.explicit_gammas,'syndrome':sigma,'backend_result':outcome(result),
            'oracle':oracle,'trajectory_scope':'oracle-only intermediate states; selected backend result independently compared; pytest also verifies accessible first-leg prefixes'})
    save('cache-and-timing.json',{'model_key':key,'initial_key_present':existed,'timings':timings,
        'numerical_identity':implementation_identity(), 'warm_reuse':'H/Lambda, raw signatures and copy/admission/group maps identical; changed p reweights probabilities only',
        'invalidation':'phase11 changes only decoder/oracle/test/docs; fault numerical implementation keys unchanged',
        'fixed_weight_priors':'same immutable .003 vector at sampling p=.03 and .04; no true-weight conditioning',
        'fault_model':str(model_path.relative_to(out))})
    after = {name:file_hash(root/name) for name in sources}
    if before != after:
        raise ValueError('source changed during export')
    files = {str(p.relative_to(out)):{'bytes':p.stat().st_size,'sha256':file_hash(p)}
             for p in sorted(out.rglob('*')) if p.is_file() and p.name!='index.json'}
    if not files or any(not record['bytes'] for record in files.values()):
        raise ValueError('empty evidence')
    save('index.json',{'phase':'11','source_sha256':before,'files':files,'paper_exact':False,
        'scope':'current-Relay integration on fixed small vectors only; no sampling, solver or historical-backend execution'})
    print(json.dumps({'status':'verified','evidence_files':len(files),'timings':timings}))


if __name__ == '__main__':
    main()
