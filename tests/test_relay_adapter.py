"""E03--E05: joint current-Relay semantics, never historical equivalence."""
from dataclasses import replace
from types import SimpleNamespace
import hashlib
import json
from pathlib import Path

import numpy as np
import pytest
from scipy import sparse
import stim

from gross_design_bandle.bench.relay import JointRelayAdapter, RelayConfig, summarize, verify_backend
from gross_design_bandle.validation.relay import trace_current_relay
from gross_design_bandle.noise import Location, NoiseProfile, build_fault_model

ROOT = Path(__file__).resolve().parents[1]


def tiny_config(n, **kwargs):
    return RelayConfig(pre_iter=4, num_sets=2, set_max_iter=5,
                       explicit_gammas=np.array([np.linspace(.1,.2,n),
                           np.linspace(-.3,.4,n),np.linspace(.45,-.2,n)]), **kwargs)


def synthetic(config=None):
    H = sparse.csc_matrix([[1,1,0,0,0],[0,1,1,0,0],[0,0,1,1,0]],dtype=np.uint8)
    L = sparse.csc_matrix([[1,0,1,0,1],[0,1,1,0,0]],dtype=np.uint8)
    return JointRelayAdapter(H, [.01,.02,.04,.01,.01], L,
        logical_names=('X-action','Z-action'), config=config or tiny_config(5))


@pytest.fixture(scope='module')
def small_fault_model():
    # Encoded Bell reference: X, Z and Y on data0 act jointly on both-sector
    # readouts; data2 faults are logical-only. No random/noisy sampling.
    c = stim.Circuit('R 0 1 2\nH 0\nCX 0 1\nI 0 2\nCX 0 1\nH 0\nM 0 1 2\nDETECTOR rec[-3]\nDETECTOR rec[-2]\nOBSERVABLE_INCLUDE(0) rec[-3]\nOBSERVABLE_INCLUDE(1) rec[-2]\nOBSERVABLE_INCLUDE(2) rec[-1]')
    locations = tuple(Location(f'data{q}',3,'idle',(q,),'I','small_Bell',3,0,'data',()) for q in (0,2))
    return build_fault_model(c,locations,NoiseProfile('a7_uniform_expanded',.03),
                             admission_policy='include_all', grouping_policy='preserve_copies')


def test_E03_joint_syndrome_and_small_circuit_scoring(small_fault_model):
    decoder = synthetic()
    errors = np.zeros((4,5),dtype=np.uint8)
    errors[1,1] = 1; errors[2,2] = 1; errors[3,4] = 1
    syndromes = np.asarray(decoder.H @ errors.T).T % 2
    truth = np.asarray(decoder.Lambda @ errors.T).T % 2
    outcomes = decoder.decode_batch(syndromes)
    assert all(r.success and np.array_equal(decoder.H @ r.correction % 2,s) for r,s in zip(outcomes,syndromes))
    assert not outcomes[0].logical_prediction.any()
    assert np.array_equal(outcomes[2].logical_prediction,[1,1])  # joint X/Z
    counts = summarize(outcomes,truth)
    assert counts == dict(shots=4, failures=1, invalid_returns=0, nonconvergence=0,
                          residual_syndrome_failures=0, observable_failures=1)
    # Logical-only fault is invisible to H and must remain a scored failure.
    assert np.array_equal(syndromes[0],syndromes[3]) and truth[3].any()
    m = small_fault_model
    d = JointRelayAdapter.from_fault_model(m,np.full(m.N,.003),
        logical_names=('X-action','Z-action','logical-only'),config=tiny_config(m.N))
    e = np.zeros((5,m.N),dtype=np.uint8)
    # I, X, Y, Z on data0 and X on data2; Y has both detector bits.
    e[1,0] = 1; e[2,5] = 1; e[3,10] = 1; e[4,15] = 1
    s = np.asarray(m.H @ e.T).T % 2; actions = np.asarray(m.Lambda @ e.T).T % 2
    assert np.array_equal(s[2],[1,1]) and not s[4].any() and actions[4,2]
    r = d.decode_batch(s)
    report = summarize(r,actions)
    assert report['shots'] == 5 and report['failures'] >= 1
    for result,sigma in zip(r,s):
        if result.success:
            assert np.array_equal(m.H @ result.correction % 2,sigma)
        else:
            assert result.invalid_return or not result.backend_success


def test_E03_negative_returns_and_nonconvergence():
    d = synthetic(); sigma = np.array([1,1,0],dtype=np.uint8)
    good = d.decode(sigma)
    base = dict(decoding=good.correction, decoded_detectors=sigma, success=True,
                posterior_ratios=good.posterior_ratios, iterations=good.iterations,
                max_iter=good.backend_max_iter)
    mutations = [dict(decoding=np.zeros(4,dtype=np.uint8)),
                 dict(decoding=np.zeros(5,dtype=float)),
                 dict(decoding=np.full(5,2,dtype=np.uint8)),
                 dict(decoded_detectors=np.zeros(3,dtype=float)),
                 dict(posterior_ratios=np.full(5,np.nan)),dict(success=1),
                 dict(iterations=d.config.iteration_cap+1),
                 dict(decoding=np.zeros(5,dtype=np.uint8))]
    results = [d.validate_result(SimpleNamespace(**(base|change)),sigma) for change in mutations]
    assert all(r.invalid_return and not r.success for r in results)
    counts = summarize(results,np.zeros((len(results),2),dtype=np.uint8))
    assert counts['failures'] == counts['invalid_returns'] == len(results)
    assert counts['residual_syndrome_failures'] == 1
    # Two identical check equations with incompatible observed parities.
    bad = JointRelayAdapter(sparse.csc_matrix([[1,1],[1,1]],dtype=np.uint8),
        [.003,.003],sparse.csc_matrix([[1,1]],dtype=np.uint8),
        logical_names=('joint',),config=tiny_config(2))
    r = bad.decode(np.array([1,0],dtype=np.uint8))
    assert not r.success and not r.backend_success and r.residual_syndrome.any()
    assert r.iterations == bad.config.iteration_cap
    assert summarize([r],np.zeros((1,1),dtype=np.uint8)) == dict(shots=1,failures=1,
        invalid_returns=0,nonconvergence=1,residual_syndrome_failures=1,observable_failures=0)
    # A backend nonconvergence claim is a failure even if its vector is valid.
    r = d.validate_result(SimpleNamespace(**(base|{'success':False})),sigma)
    assert not r.success and not r.residual_syndrome.any()


def test_E04_fixed_gamma_recurrence_candidates_and_prior_policy():
    import relay_bp
    provenance = json.loads((ROOT/'locks/relay-adapter-sources.json').read_text())
    external = Path('/home/quantum_teresheys/workspace/tour_de_gross_design_bundle/external_libs/relay')
    for path,record in provenance['backend']['inspected_files'].items():
        assert hashlib.sha256((external/path).read_bytes()).hexdigest()==record['sha256']
    assert provenance['reference_relay_table7_sha256']==hashlib.sha256((ROOT/'reference/relay_table7.json').read_bytes()).hexdigest()
    H = np.array([[1,1,0,0],[0,1,1,0],[0,0,1,1],[1,0,0,1]],dtype=np.uint8)
    L = sparse.csc_matrix([[1,0,1,0],[0,1,0,1]],dtype=np.uint8)
    sigma = np.ones(4,dtype=np.uint8)
    raw = json.loads((ROOT/'reference/relay_table7.json').read_text())
    for precision in ('float32','float64'):
        config = RelayConfig(precision=precision,pre_iter=4,num_sets=2,set_max_iter=10,
            explicit_gammas=np.array([[.1]*4,[-.3,-.067,.167,.4],[.4,-.3,.4,-.3]]),
            stopping_criterion='all')
        d = JointRelayAdapter(sparse.csc_matrix(H),[.004,.003,.006,.005],L,
            logical_names=('X','Z'),config=config)
        oracle = trace_current_relay(H,d.priors,sigma,config)
        actual = d.decode(sigma)
        assert actual.backend_success == oracle['success']
        assert np.array_equal(actual.correction,oracle['correction'])
        assert actual.iterations == oracle['iterations']
        assert actual.candidate_cost == pytest.approx(oracle['cost'])
        np.testing.assert_allclose(actual.posterior_ratios,oracle['posterior'],rtol=2e-6,atol=2e-6)
        assert any(t['leg']>0 for t in oracle['trace']) and oracle['candidates']
        assert len(oracle['candidates'])==2
        assert oracle['candidates'][1]['cost'] < oracle['candidates'][0]['cost']
        # The selected vector changes when we stop at the first convergence.
        first = JointRelayAdapter(sparse.csc_matrix(H),d.priors,L,logical_names=('X','Z'),
            config=replace(config,stopping_criterion='nconv',stop_nconv=1)).decode(sigma)
        assert first.iterations < actual.iterations and not np.array_equal(first.correction,actual.correction)
        # API doesn't expose an internal Relay trajectory. First-leg prefixes
        # expose each reachable decision and posterior up to convergence.
        first_leg = [t for t in oracle['trace'] if t['leg']==0]
        for step in first_leg:
            backend = getattr(relay_bp,'RelayDecoderF32' if precision=='float32' else 'RelayDecoderF64')(
                sparse.csc_matrix(H),d.priors,alpha=1.,gamma0=config.gamma0,
                pre_iter=step['iteration'],num_sets=0,set_max_iter=1,
                explicit_gammas=config.explicit_gammas)
            result = backend.decode_detailed(sigma)
            assert np.array_equal(result.decoding,step['correction'])
            np.testing.assert_allclose(result.posterior_ratios,step['posterior'],rtol=2e-6,atol=2e-6)
        # In real arithmetic the unclipped min-sum recurrence is homogeneous
        # for uniform positive LLRs. Verify only these finite-precision vectors.
        uniform = JointRelayAdapter(sparse.csc_matrix(H),np.full(4,.003),L,
                                   logical_names=('X','Z'),config=config)
        d2 = JointRelayAdapter(sparse.csc_matrix(H),np.full(4,.03),L,
                              logical_names=('X','Z'),config=config)
        r1 = uniform.decode(sigma); r2 = d2.decode(sigma)
        assert np.array_equal(r1.correction,r2.correction) and r1.iterations==r2.iterations
        uniform_oracle = trace_current_relay(H,uniform.priors,sigma,config)
        assert np.array_equal(r1.correction,uniform_oracle['candidates'][0]['correction'])
        # Audit the iteration ramp too: alpha=0 requests the ramp; None in
        # upstream is alpha=1, contrary to the phase-00 prose description.
        ramp_config = replace(config,alpha=0.,alpha_iteration_scaling_factor=2.)
        ramp = JointRelayAdapter(sparse.csc_matrix(H),d.priors,L,logical_names=('X','Z'),config=ramp_config).decode(sigma)
        ramp_oracle = trace_current_relay(H,d.priors,sigma,ramp_config)
        assert np.array_equal(ramp.correction,ramp_oracle['correction'])
        assert ramp.iterations==ramp_oracle['iterations']
        manifest = d.manifest(historical_raw_parameters=raw)
        assert manifest['historical_raw_parameters']==raw and not manifest['paper_exact']
        assert manifest['resolved_backend_parameters']['gamma0']==.1
        assert manifest['prior_policy']['sampling_p_dependent'] is False
        assert manifest['prior_policy']['true_weight_conditioned'] is False
        # No conditioned weight or p argument exists; priors are owned/frozen.
        assert not d.priors.flags.writeable
        with pytest.raises(TypeError): d.decode(sigma,weight=2)
        with pytest.raises(TypeError): d.decode(sigma,p=.2)
    # Nonuniform priors change which member of the same coset is preferred.
    pair = sparse.csc_matrix([[1,1]],dtype=np.uint8)
    for p,expected in [([.01,.1],[0,1]),([.1,.01],[1,0])]:
        d = JointRelayAdapter(pair,p,pair,logical_names=('joint',),config=tiny_config(2))
        assert np.array_equal(d.decode(np.array([1],dtype=np.uint8)).correction,expected)


def test_E05_scalar_native_batch_and_independent_streams():
    H = sparse.csc_matrix([[1,1,0,0],[0,1,1,0],[0,0,1,1],[1,0,0,1]],dtype=np.uint8)
    L = sparse.csc_matrix([[1,0,1,0],[0,1,0,1]],dtype=np.uint8)
    sigma = np.array([[1,1,1,1],[1,0,1,0],[1,1,1,1],[0,0,0,0]],dtype=np.uint8)
    def decoder(config):
        return JointRelayAdapter(H,np.full(4,.003),L,logical_names=('X','Z'),config=config)
    fixed = decoder(tiny_config(4,stopping_criterion='all'))
    scalar = [fixed.decode(s) for s in sigma]; batch = fixed.decode_batch(sigma)
    for a,b in zip(scalar,batch):
        assert np.array_equal(a.correction,b.correction) and a.iterations==b.iterations
        assert a.success==b.success and a.candidate_cost==b.candidate_cost
        assert np.array_equal(a.posterior_ratios,b.posterior_ratios)
    config = replace(fixed.config,explicit_gammas=None,set_max_iter=10,num_sets=4,seed=91)
    d = decoder(config); ids = [41,93,27,8]
    scalar = [d.decode(s,stream_id=i) for s,i in zip(sigma,ids)]
    batch = d.decode_batch(sigma,stream_ids=ids)
    permutation = [2,0,3,1]
    other_worker = decoder(config)
    shuffled = other_worker.decode_batch(sigma[permutation],stream_ids=[ids[i] for i in permutation])
    for j,i in enumerate(permutation):
        for b in (batch[i],shuffled[j]):
            assert np.array_equal(scalar[i].correction,b.correction)
            assert np.array_equal(scalar[i].posterior_ratios,b.posterior_ratios)
            assert scalar[i].iterations==b.iterations and scalar[i].stream_seed==b.stream_seed
    assert len({r.stream_seed for r in scalar})==len(ids)
    assert not np.array_equal(scalar[0].posterior_ratios,scalar[2].posterior_ratios)
    assert fixed.decode_batch(np.empty((0,4),dtype=np.uint8)) == ()


def test_negative_parameters_profiles_and_graphs(small_fault_model,monkeypatch,tmp_path):
    for kwargs in ({'precision':'int32'},{'pre_iter':0},{'num_sets':-1},{'seed':True},
        {'gamma_dist_interval':(.3,.3)},{'gamma0':np.nan},{'alpha':-1},
        {'candidate_selection':'last_candidate'},{'stopping_criterion':'typo'},
        {'explicit_gammas':np.empty((0,5))}):
        with pytest.raises(ValueError): RelayConfig(**kwargs)
    d = synthetic()
    for kwargs,match in [({'profile':'historical_table7'},'O2'),
        ({'config':{'ewainit_discount_factor':.875}},'config'),
        ({'config':tiny_config(4)},'gamma column'),
        ({'logical_names':('X',)},'logical names'),
        ({'graph_profile':'separate_X_Z'},'graph'),
        ({'input_to_decoder':[0,1,1,3,4]},'identity')]:
        options = dict(logical_names=d.logical_names,config=d.config)|kwargs
        with pytest.raises(ValueError,match=match): JointRelayAdapter(d.H,d.priors,d.Lambda,**options)
    with pytest.raises(ValueError,match='alignment'):
        JointRelayAdapter(d.H,d.priors,d.Lambda[:,:-1],logical_names=d.logical_names)
    for p in ([0,.1,.1,.1,.1],[.5]*5,[np.nan]*5,[.01]*4):
        with pytest.raises(ValueError,match='priors'): JointRelayAdapter(d.H,p,d.Lambda,logical_names=d.logical_names)
    with pytest.raises(ValueError,match='nonbinary'):
        JointRelayAdapter(d.H.astype(float),d.priors,d.Lambda,logical_names=d.logical_names)
    # Sparse-coordinate duplicates cancel over GF(2); equal fault columns
    # are distinct variables and are never canceled/merged in this profile.
    coo = sparse.coo_matrix((np.ones(4,dtype=np.uint8),([0,0,0,0],[0,0,1,2])),shape=(1,3))
    canonical = JointRelayAdapter(coo,[.003]*3,sparse.csc_matrix((1,3),dtype=np.uint8),
        logical_names=('row',),config=tiny_config(3))
    assert np.array_equal(canonical.H.toarray(),[[0,1,1]])
    with pytest.raises(ValueError,match='syndrome'): d.decode(np.zeros(3,dtype=float))
    with pytest.raises(ValueError,match='truth'): summarize([d.decode(np.zeros(3,dtype=np.uint8))],np.zeros((1,1),dtype=np.uint8))
    seeded = synthetic(replace(d.config,explicit_gammas=None))
    with pytest.raises(ValueError,match='stream_id'): seeded.decode(np.zeros(3,dtype=np.uint8))
    with pytest.raises(ValueError,match='duplicate'): seeded.decode_batch(np.zeros((2,3),dtype=np.uint8),stream_ids=[1,1])
    with pytest.raises(ValueError,match='stream_ids'): seeded.decode_batch(np.zeros((2,3),dtype=np.uint8))
    m = small_fault_model; priors = np.full(m.N,.003)
    preserve = JointRelayAdapter.from_fault_model(m,priors,logical_names=('X','Z','only'),config=tiny_config(m.N))
    grouped = JointRelayAdapter.from_fault_model(m,priors,logical_names=('X','Z','only'),
        config=RelayConfig(pre_iter=4,num_sets=0,set_max_iter=1),graph_profile='joint_signature_xor')
    assert preserve.H.shape[1]==m.N and grouped.H.shape[1]<m.N
    # Equal H=0 logical-only and ineffective variables stay distinct.
    assert grouped.input_to_decoder[10] != grouped.input_to_decoder[15]
    assert preserve.manifest()['decoder_graph']['profile']=='preserve_columns'
    assert grouped.manifest()['decoder_graph']['profile']=='joint_signature_xor'
    priors[0] = .2
    assert preserve.priors[0]==.003  # caller cannot retune the fixed decoder
    for e in (np.zeros(m.N,dtype=np.uint8),np.eye(1,m.N,5,dtype=np.uint8)[0]):
        g = np.zeros(grouped.H.shape[1],dtype=np.uint8)
        np.bitwise_xor.at(g,grouped.input_to_decoder,e)
        assert np.array_equal(m.H @ e % 2,grouped.H @ g % 2)
        assert np.array_equal(m.Lambda @ e % 2,grouped.Lambda @ g % 2)
    # A version label alone does not admit another compiled backend.
    wrong_binary = tmp_path/'other-build.so'; wrong_binary.write_bytes(b'unaudited build')
    with monkeypatch.context() as patch:
        patch.setattr('gross_design_bandle.bench.relay.importlib.metadata.distribution',
                      lambda name: SimpleNamespace(version='0.2.2',locate_file=lambda p:wrong_binary))
        verify_backend.cache_clear()
        try:
            with pytest.raises(ValueError,match='audited source build'): synthetic()
        finally:
            verify_backend.cache_clear()
