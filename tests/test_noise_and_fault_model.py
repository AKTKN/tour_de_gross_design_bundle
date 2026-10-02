"""D03/E01/E02: independent signatures, exact cancellation and population maps."""
from dataclasses import replace
from itertools import product
import numpy as np
import pytest
import stim
from gross_design_bandle.noise import NoiseProfile, Location, build_fault_model, emit_noise, parity_probability
from gross_design_bandle.noise.signatures import joint_signatures
from gross_design_bandle.noise.locations import benchmark_locations
from gross_design_bandle.validation.faults import validate_faults
from gross_design_bandle.codes.reference_profiles import load_reference_code
from gross_design_bandle.flows.harness import build_benchmark
from gross_design_bandle.lpu.reference import build_reference_lpu
from gross_design_bandle.surgery.deformation import compile_deformation


def loc(i,kind,qs,gate,identity=None,path=()):
    return Location(identity or f'{i}/{kind}/{qs}',i,kind,qs,gate,'test',max(i,0),0,'fixture',path)


def model(c,ls, *, name='a7_uniform_expanded', admission='include_all', grouping='preserve_copies',p=.03):
    return build_fault_model(c,ls,NoiseProfile(name,p),admission_policy=admission,grouping_policy=grouping)


def scan(c):
    result = []
    for i,op in enumerate(c.flattened()):
        if op.name in ('R','RX','RY','M','MX','MY','CX','CY','CZ','SWAP'):
            kind = 'preparation' if op.name.startswith('R') else 'readout' if op.name.startswith('M') else 'two_qubit'
            width = 2 if kind=='two_qubit' else 1
            ts = op.targets_copy()
            if any(t.is_measurement_record_target for t in ts):
                continue
            for j in range(0,len(ts),width):
                result.append(loc(i-1 if kind=='readout' else i,kind,tuple(t.value for t in ts[j:j+width]),op.name))
        # Idle injection fixtures also test every local Pauli after each gate.
        if op.name in ('H','S','S_DAG','CX','CY','CZ','SWAP','MPP'):
            for q in range(c.num_qubits):
                result.append(loc(i,'idle',(q,),'I'))
    return tuple(result)


def test_D03_exhaustive_gate_templates_and_joint_Bell_faults(tmp_path):
    for gate in ('CX','CY','CZ','SWAP'):
        # Bell-encoded inputs with both-sector terminal Bell correlations.
        c = stim.Circuit('R 0 1 2 3\nH 0 1\nCX 0 2 1 3\nS 0\nS_DAG 1\nH 0')
        c.append(gate,[0,1]); c.append('TICK'); c.append(gate,[0,1])
        c += stim.Circuit('H 0\nS 1\nS_DAG 0\nCX 0 2 1 3\nH 0 1\nM 0 1 2 3')
        for j in range(4):
            c.append('OBSERVABLE_INCLUDE',[stim.target_rec(-4+j)],j)
        m = model(c,scan(c))
        result = validate_faults(m,exhaustive=True,counterexample_path=tmp_path/'template-counterexample.json')
        assert result['checked_raw_primitives'] == len(m.raw) and result['all_agree']
    # Negative YY, physical Bell reset/CNOT/CY/readout and both-half XOR.
    from gross_design_bandle.algebra.pauli import Pauli
    from gross_design_bandle.circuits.checks import Check
    from gross_design_bandle.circuits.primitive import primitive_schedule
    from gross_design_bandle.flows.boundaries import mpp
    p = Pauli.from_word('YY',('d0','d1'),-1)
    s = primitive_schedule(Check.bell('bell',p,('d0',)))
    c = stim.Circuit('R 0 1 2 3\nH 0\nCX 0 1')+s.to_stim()
    c.append('DETECTOR',[stim.target_rec(-1),stim.target_rec(-2)])
    c += mpp(p,s.register); c.append('OBSERVABLE_INCLUDE',[stim.target_rec(-1)],0)
    result = validate_faults(model(c,scan(c)),exhaustive=True,counterexample_path=tmp_path/'Bell-counterexample.json')
    assert result['all_agree']
    for c in (stim.Circuit('RY 0\nMY 0\nDETECTOR rec[-1]\nOBSERVABLE_INCLUDE(0) rec[-1]'),
              stim.Circuit('RX 0\nMX 0\nDETECTOR rec[-1]'),
              stim.Circuit('RX 0\nZ 0\nRX 1\nCY 1 0\nM 1\nCY rec[-1] 0\nMX 0\nMPAD 1\nDETECTOR rec[-1] rec[-2]\nOBSERVABLE_INCLUDE(0) rec[-1] rec[-2]')):
        assert validate_faults(model(c,scan(c)),exhaustive=True,counterexample_path=tmp_path/'Y-feedback-counterexample.json')['all_agree']


def test_E01_duplicate_cancellation_exact_subsets_and_bounded_Stim_sampling():
    c = stim.Circuit('R 0\nI 0\nM 0\nDETECTOR rec[-1]\nOBSERVABLE_INCLUDE(0) rec[-1]')
    ls = (loc(1,'idle',(0,),'I','copy_a'),loc(1,'idle',(0,),'I','copy_b'))
    m = model(c,ls,name='paper_linearized_unequal',p=.3)
    # X and Y flip the Z readout; Z has zero joint signature. Four independent
    # effective bits, rather than one categorical outcome at each idle.
    exact = 0.; q = .1
    for bits in product((0,1),repeat=m.N):
        weight = sum(bits); probability = q**weight*(1-q)**(m.N-weight)
        syndrome = np.asarray(m.H@np.array(bits,dtype=np.uint8)).ravel()%2
        exact += probability*int(syndrome[0])
    expected = parity_probability([q]*4)
    assert exact == pytest.approx(expected,abs=1e-14)
    # Explicit two-copy cancellation, in both H and Lambda.
    error = np.zeros(m.N,dtype=np.uint8); error[[0,3]] = 1
    assert not (m.H@error%2).any() and not (m.Lambda@error%2).any()
    noisy = emit_noise(c,ls,m.profile)
    ds,obs = noisy.compile_detector_sampler(seed=611).sample(32768,separate_observables=True)
    rng = np.random.default_rng(612)
    errors = (rng.random((32768,m.N))<m.probabilities).astype(np.uint8)
    signatures = np.asarray(m.H@errors.T).T%2
    tolerance = 6*np.sqrt(expected*(1-expected)/32768)
    assert abs(ds.mean()-expected)<tolerance and abs(signatures.mean()-expected)<tolerance
    assert np.array_equal(ds,obs)


def test_E01_equal_q_first_order_and_categorical_profile_separation():
    for multiplicity in (5,15):
        # Exact binomial polynomial: linear term m*q and quadratic term
        # -m*(m-1)*q^2; the finite-p channel must not be called identical.
        p = 1e-3; q = p/15
        difference = multiplicity*q-parity_probability([q]*multiplicity)
        assert difference > 0
        assert difference/q**2 == pytest.approx(multiplicity*(multiplicity-1),rel=.002)
        half = multiplicity*q/2-parity_probability([q/2]*multiplicity)
        assert difference/half == pytest.approx(4,rel=.002)
    c = stim.Circuit('R 0 1\nCX 0 1\nM 0 1\nDETECTOR rec[-1]\nDETECTOR rec[-2]')
    ls = (loc(1,'two_qubit',(0,1),'CX'),)
    independent = emit_noise(c,ls,NoiseProfile('paper_linearized_unequal',.2))
    categorical = emit_noise(c,ls,NoiseProfile('standard_categorical_depolarizing',.2))
    assert sum(op.name=='E' for op in independent.flattened()) == 15
    assert sum(op.name=='DEPOLARIZE2' for op in categorical.flattened()) == 1
    # P(X flip on first) has 8 independent terms vs categorical probability 8p/15.
    assert parity_probability([.2/15]*8) != pytest.approx(8*.2/15)
    assert 'ELSE_CORRELATED_ERROR' not in str(independent)
    for name,copies in [('a7_uniform_expanded',15),('paper_linearized_unequal',1),('standard_categorical_depolarizing',1)]:
        profile = NoiseProfile(name,.03)
        assert profile.copies('preparation')==copies
        single = emit_noise(stim.Circuit('R 0\nM 0'),(loc(0,'preparation',(0,),'R'),),profile)
        assert single.num_measurements==1


def test_E02_admission_logical_only_zero_columns_hyperedges_and_joint_grouping():
    # X flips three detectors (hyperedge) AND a logical row. A separate X on
    # qubit1 is logical-only. Z terms are genuinely zero/zero.
    c = stim.Circuit('R 0 1\nI 0 1\nM 0 1\nDETECTOR rec[-2]\nDETECTOR rec[-2]\nDETECTOR rec[-2]\nOBSERVABLE_INCLUDE(0) rec[-1]\nOBSERVABLE_INCLUDE(1) rec[-2]')
    ls = (loc(1,'idle',(0,),'I'),loc(1,'idle',(1,),'I'))
    all_m = model(c,ls,grouping='joint_signature_xor')
    admitted = model(c,ls,admission='exclude_joint_zero',grouping='joint_signature_xor')
    assert len(all_m.copy_to_raw)==30 and admitted.N==20 and all_m.N==30
    assert all_m.H.shape[1] == all_m.Lambda.shape[1] == all_m.N
    assert (all_m.H[:,0].toarray().ravel()==1).all() and all_m.Lambda[1,0]==1
    logical_only = all_m.H[:,15].toarray().ravel()
    assert not logical_only.any() and all_m.Lambda[0,15]==1
    # Equal detector signatures but different logical signatures must NOT merge.
    assert all_m.admitted_to_group[10] != all_m.admitted_to_group[15]
    assert all_m.admitted_to_group[0] == all_m.admitted_to_group[5]
    assert all_m.decoder_probabilities[all_m.admitted_to_group[0]] == pytest.approx(parity_probability([.002]*10))
    # The exact unconditional joint distribution survives explicit XOR grouping.
    small = model(c,ls,name='paper_linearized_unequal',grouping='joint_signature_xor',p=.3)
    raw_dist = {}; grouped_dist = {}
    for bits in product((0,1),repeat=small.N):
        p = np.prod([q if b else 1-q for b,q in zip(bits,small.probabilities)])
        value = 0
        for j,b in enumerate(bits):
            if b: value ^= small.group_signatures[small.admitted_to_group[j]]
        raw_dist[value] = raw_dist.get(value,0)+p
    for bits in product((0,1),repeat=len(small.group_signatures)):
        p = np.prod([q if b else 1-q for b,q in zip(bits,small.decoder_probabilities)])
        value = 0
        for s,b in zip(small.group_signatures,bits):
            if b: value ^= s
        grouped_dist[value] = grouped_dist.get(value,0)+p
    assert raw_dist == pytest.approx(grouped_dist,abs=1e-14)
    report = admitted.discrepancy(123,{'profile':'test'})
    assert report['exclude_joint_zero_N']==20 and report['include_all_N']==30
    assert report['zero_H_nonzero_Lambda_retained']==10 and report['delta_admitted_minus_published']==-103
    maps = all_m.to_dict()
    assert maps['copy_ordinal'][:5]==list(range(5)) and len(maps['admission_mask'])==30


def test_E02_nested_repeats_and_observable_only_terms(tmp_path):
    c = stim.Circuit('''R 0
REPEAT 2 {
    REPEAT 3 {
        I 0
        M 0
        DETECTOR rec[-1]
        R 0
    }
}
M 0
OBSERVABLE_INCLUDE(0) rec[-1]
''')
    ls = []; iteration = 0
    for i,op in enumerate(c.flattened()):
        if op.name=='I':
            ls.append(loc(i,'idle',(0,),'I',f'outer/{iteration//3}/inner/{iteration%3}',(iteration//3,iteration%3)))
            iteration += 1
    ls.append(loc(len(list(c.flattened()))-3,'idle',(0,),'I','terminal_logical_only'))
    m = model(c,ls)
    assert len({l.repeat_path for l in m.locations[:-1]})==6
    assert len(set(m.copy_to_raw))==21
    assert validate_faults(m,exhaustive=True,counterexample_path=tmp_path/'repeat-counterexample.json')['all_agree']
    flat = model(c.flattened(),ls)
    assert (m.H!=flat.H).nnz==0 and (m.Lambda!=flat.Lambda).nnz==0
    assert not m.H[:,-15].toarray().any() and m.Lambda[0,-15]==1


@pytest.fixture(scope='module')
def gross_models():
    code = load_reference_code('gross','noise_test')
    df = compile_deformation(build_reference_lpu(code,'X'))
    result = {}
    for operation in ('memory','X1'):
        h = build_benchmark(code,operation=operation,rounds=2,deformation=df if operation=='X1' else None)
        ls,policy = benchmark_locations(code,h,operation=operation,rounds=2,deformation=df)
        result[operation] = model(h.circuit,ls,admission='exclude_joint_zero',grouping='joint_signature_xor'),policy
    return result


def test_D03_gross_memory_X1_deterministic_strata(gross_models,tmp_path):
    for operation,(m,policy) in gross_models.items():
        evidence = validate_faults(m,exhaustive=False,counterexample_path=tmp_path/f'{operation}-counterexample.json')
        assert evidence['all_agree'] and evidence['checked_raw_primitives']>30
        phases = {t['location']['phase'] for t in evidence['trials']}
        assert phases == ({'memory'} if operation=='memory' else {'edge_initialize','deformed','split'})
        assert policy['paper_exact'] is False
        if operation=='X1':
            # X1 uses the half-LPU and has no shared Bell check; the Bell
            # primitive is exhaustively checked in the separate YY fixture.
            assert any(t['location']['role']=='edge_data' for t in evidence['trials'])


def test_E02_gross_population_location_coverage_and_noise_fingerprints(gross_models):
    for operation,(m,policy) in gross_models.items():
        m.validate()
        assert m.N>1000 and policy['noisy_ticks']>10
        assert all(l.phase!='original_check_verification' for l in m.locations)
        assert all(l.time<policy['noisy_ticks'] for l in m.locations)
        assert all(r['copies'] in (1,5,15) for r in m.raw)
        assert m.H.nnz and m.Lambda.nnz
        noisy = emit_noise(m.circuit,m.locations,m.profile)
        dem = noisy.detector_error_model(allow_gauge_detectors=False,approximate_disjoint_errors=False)
        assert dem.num_detectors==m.H.shape[0] and dem.num_observables==m.Lambda.shape[0]
        # DEM compaction is explicitly separate from the admitted population.
        assert dem.num_errors != m.N


def test_negative_profiles_admission_maps_and_corrupt_signatures(tmp_path):
    c = stim.Circuit('R 0\nI 0\nM 0\nDETECTOR rec[-1]')
    ls = (loc(1,'idle',(0,),'I'),)
    for name,p in [('unknown',.1),('a7_uniform_expanded',float('nan')),('a7_uniform_expanded',True),('paper_linearized_unequal',1.1)]:
        with pytest.raises(ValueError): NoiseProfile(name,p)
    with pytest.raises(TypeError): build_fault_model(c,ls,NoiseProfile('a7_uniform_expanded',.1))
    with pytest.raises(ValueError,match='categorical'): model(c,ls,name='standard_categorical_depolarizing')
    with pytest.raises(ValueError,match='policy'): model(c,ls,admission='silently_drop_zero_H')
    with pytest.raises(ValueError,match='identity'): model(c,ls+ls)
    with pytest.raises(ValueError,match='qubits'): model(c,(replace(ls[0],qubits=(2,)),))
    with pytest.raises(ValueError,match='boundary'): model(c,(replace(ls[0],after_instruction=999),))
    with pytest.raises(ValueError,match='gate'): model(c,(loc(1,'preparation',(0,),'R'),))
    with pytest.raises(ValueError,match='non-disjoint'):
        model(stim.Circuit('R 0 1\nCX 0 1 0 1'),(loc(1,'two_qubit',(0,1),'CX'),))
    with pytest.raises(ValueError,match='unsupported'): joint_signatures(stim.Circuit('X_ERROR(.1) 0'),())
    with pytest.raises(ValueError,match='non-deterministic'): model(stim.Circuit('RX 0\nM 0\nDETECTOR rec[-1]'),())
    m = model(c,ls,grouping='joint_signature_xor')
    with pytest.raises(ValueError,match='admission'): replace(m,admission_mask=~m.admission_mask).validate()
    with pytest.raises(ValueError,match='multiplicity'): replace(m,copy_ordinal=m.copy_ordinal[::-1]).validate()
    with pytest.raises(ValueError,match='alignment'): replace(m,Lambda=m.Lambda[:,:-1]).validate()
    bad = m.H.copy(); bad[0,0] = 0
    with pytest.raises(ValueError,match='signatures'): replace(m,H=bad).validate()
    with pytest.raises(ValueError,match='probability'): replace(m,probabilities=m.probabilities*2).validate()
    groups = m.admitted_to_group.copy(); groups[0] = groups[-1]
    with pytest.raises(ValueError,match='joint signature'): replace(m,admitted_to_group=groups).validate()
    # A corrupted physical raw signature is found by the separate oracles,
    # even if all corresponding exported H columns are self-consistent.
    m = model(c,ls,name='paper_linearized_unequal')
    from gross_design_bandle.bench.columns import matrix_from_signatures
    bad_s = list(m.raw_signatures); bad_s[0] ^= 1
    corrupt = replace(m,raw_signatures=tuple(bad_s),group_signatures=tuple(bad_s),H=matrix_from_signatures(bad_s,1))
    with pytest.raises(ValueError,match='counterexample'):
        validate_faults(corrupt,exhaustive=True,counterexample_path=tmp_path/'counterexample.json')
    assert (tmp_path/'counterexample.json').stat().st_size>0
