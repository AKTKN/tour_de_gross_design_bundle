"""Phase09: transfer channel/frame, real routing, C10 noise and timing."""
from dataclasses import replace
from time import perf_counter
import pytest
import stim
from gross_design_bandle.algebra.pauli import Pauli
from gross_design_bandle.codes import load_reference_code
from gross_design_bandle.circuits.shift import transfer_plan, shift_sequence, two_cnot_ops, PROFILE
from gross_design_bandle.flows.shift import build_shift_benchmark
from gross_design_bandle.flows.stabilizer_flows import verify_deterministic
from gross_design_bandle.noise import NoiseProfile, build_fault_model, emit_noise
from gross_design_bandle.noise.shift import shift_locations
from gross_design_bandle.validation.faults import validate_faults
from gross_design_bandle.bench.rates import shift_rate


def toy_transfer(*, fault=False, correction=True, negative=False):
    # Full two-data Choi state, including Y and a negative generator. Check
    # destination c0 starts in |1>: destination state must be tracked too.
    c = stim.Circuit('R 0 1 2 3 4 5\nH 0 1\nCX 0 4 1 5\nS 1\nX 2')
    if negative: c.append('Z',[0])
    c += stim.Circuit('CX 0 2 1 3\nCX 2 0 3 1')
    if fault: c.append('X',[0])  # changes reused |m>, hence an output X frame
    c += stim.Circuit('M 0 1\nCX 2 1 3 0\nCX 1 2 0 3\nM 2 3')
    if correction:
        c.append('X',[1])  # initial c0 frame
        c.append('CX',[stim.target_rec(-3),1,stim.target_rec(-4),0])
    return c


def test_B06_two_transfer_Choi_signed_Paulis_and_recorded_frame():
    # Exact signed propagation: source X transfers exactly; source Z/Y carry
    # the vacated-source Z stabilizer. Its known sign is the destination X
    # frame. This certifies the channel for arbitrary inputs.
    ids=('s','d')
    for word,expected in [('XI','IX'),('ZI','ZZ'),('YI','ZY'),('IZ','ZI')]:
        actual=Pauli.from_word(word,ids).conjugated('CNOT','s','d').conjugated('CNOT','d','s')
        assert actual==Pauli.from_word(expected,ids)
    for negative in (False,True):
        for fault in (False,True):
            sim=stim.TableauSimulator(); sim.do_circuit(toy_transfer(fault=fault,negative=negative))
            # Ideal swap oracle acts on the complete entangled state. Four
            # independent correlations certify every data logical degree.
            for word,sign in [('IXIIXI',-1 if negative else 1),('IZIIZI',1),('YIIIIX',1),('ZIIIIZ',1)]:
                assert sim.peek_observable_expectation(stim.PauliString(word))==sign
            records=sim.current_measurement_record()
            assert records[-2:]==list(reversed(records[-4:-2]))
    # Both material failures break the intended corrected channel.
    sim=stim.TableauSimulator(); sim.do_circuit(toy_transfer(fault=True,correction=False))
    assert sim.peek_observable_expectation(stim.PauliString('IZIIZI'))==-1
    bad=stim.Circuit('R 0 1 2\nH 0\nCX 0 2\nCX 0 1\nM 0')
    sim=stim.TableauSimulator(); sim.do_circuit(bad)  # omitted reverse CX measures data
    assert sim.peek_observable_expectation(stim.PauliString('IX X'.replace(' ','')))==0
    # Actual gross routing on a full physical Choi input (not restricted to
    # the BB codespace): all 144 data degrees and both Pauli sectors. Local
    # Cliffords supply Y and negative correlations. Nonzero destination
    # states plus a changed vacated-site bit exercise the carried frame.
    code=load_reference_code('gross','arbitrary'); plan=transfer_plan(code)
    n=code.spec.n; ref0=len(plan.register)
    initial=stim.Circuit(); initial.append('R',range(ref0+n))
    initial.append('H',range(n))
    initial.append('CX',[q for i in range(n) for q in (i,ref0+i)])
    initial.append('S',range(0,n,3)); initial.append('H',range(0,n,5)); initial.append('Z',range(0,n,7))
    b={a:int(i%3==0) for i,a in enumerate(plan.register[n:])}
    initial.append('X',[plan.register.index(a) for a,bit in b.items() if bit])
    sim=stim.TableauSimulator(); sim.do_circuit(initial)
    tableau=sim.current_inverse_tableau().inverse()
    input_generators=[tableau.z_output(q) for q in list(range(n))+list(range(ref0,ref0+n))]
    for stage,pairs in enumerate((plan.first,plan.second)):
        for op in two_cnot_ops(pairs,0,phase='test'):
            sim.do_circuit(stim.Circuit('CX '+' '.join(str(plan.register.index(q)) for q in op.qubits)))
        if stage==0: sim.x(0)
        for source,dest in pairs: sim.measure(plan.register.index(source))
    records=sim.current_measurement_record()
    for (source,check),(_,dest) in zip(plan.first,plan.second):
        q=plan.data.index(dest)
        if b[check]^records[q]: sim.x(q)
    full_permutation=plan.target_to_source+tuple(range(n,ref0+n))
    for p in input_generators:
        expected=stim.PauliString([p[q] for q in full_permutation]); expected.sign=p.sign
        assert sim.peek_observable_expectation(expected)==1


@pytest.fixture(scope='module')
def gross_shift():
    code=load_reference_code('gross','block_0'); times={}
    t=perf_counter(); h=build_shift_benchmark(code,10)
    locations,policy=shift_locations(code,h,10); times['harness_locations_seconds']=perf_counter()-t
    t=perf_counter()
    model=build_fault_model(h.circuit,locations,NoiseProfile('a7_uniform_expanded',.001),
        admission_policy='include_all',grouping_policy='joint_signature_xor')
    times['model_seconds']=perf_counter()-t
    return code,h,locations,policy,model,times


def test_shift_timing_C10_real_permutation_roles_K24_and_rate(gross_shift):
    code,h,ls,policy,m,times=gross_shift
    sequence=shift_sequence(code,10); plan=sequence.plan
    assert plan.delta==(1,0) and plan.validate(code)['Tanner_edges']==288
    assert sequence.duration==141 and h.physical_body.num_ticks==141
    assert h.boundary_policy['divisor']==10 and shift_rate(.037,10)==pytest.approx(.0037)
    assert h.validate()['strict_dem_observables']==24
    # Per instruction: four actual CX transfer layers and two vacated-source
    # readouts, then every ordinary Fig4b syndrome interaction. No SWAP/MPP
    # appears inside the body.
    assert all(op.name not in ('SWAP','MPP') for op in h.physical_body.flattened())
    for r in range(10):
        ops=[o for o in sequence.ops if o.round==r and o.phase.startswith('transfer_')]
        assert len([o for o in ops if o.gate=='CX'])==4*code.spec.n
        assert len([o for o in ops if o.gate=='M'])==2*code.spec.n
        base=1+14*r
        assert {o.time-base for o in ops}==set(range(6))
    source,anc=plan.first[0]
    assert [sequence.role_at(source,t) for t in (1,3,4,6,7)]==[
        'transfer_1_source','vacated_data_readout','transfer_2_destination','BB_data','BB_data']
    assert sequence.role_at(anc,3)=='code_data_on_check' and sequence.role_at(anc,6)=='vacated_check_readout'
    history=h.boundary_policy['role_and_frame_history']
    assert len(history)==10 and len(history[-1]['data_X_frame'])==144
    assert any(f['ids'] for f in history[-1]['data_X_frame'])
    assert sum(a['flow_class']=='transfer_readout' for a in h.annotations)==2880
    assert policy['noisy_ticks']==141 and policy['paper_exact'] is False


def test_shift_faults_both_transfers_syndrome_reuse_and_boundaries(gross_shift,tmp_path):
    code,h,ls,policy,m,times=gross_shift
    m.validate()
    assert len(m.raw)==len(m.raw_signatures) and m.H.shape[1]==m.Lambda.shape[1]==m.N
    assert all(r['copies'] in (1,5,15) for r in m.raw)
    assert {l.phase for l in ls}=={'shift_initialize','transfer_1','transfer_2','following_syndrome'}
    assert max(l.time for l in ls)==140 and all(l.qubits[0]<288 for l in ls)
    audit=validate_faults(m,exhaustive=False,counterexample_path=tmp_path/'shift-counterexample.json')
    assert audit['all_agree']
    strata={(t['location']['phase'],t['location']['round']) for t in audit['trials']}
    for r in (0,5,9):
        for phase in ('transfer_1','transfer_2','following_syndrome'): assert (phase,r) in strata
    for phase in ('transfer_1','transfer_2'):
        words={t['pauli_word'] for t in audit['trials'] if t['location']['phase']==phase}
        assert {'IX','ZI','XX','YZ'}<=words
    # Every primitive at both transfers has a computed joint signature;
    # independent large checks use the documented bounded strata.
    for phase in ('transfer_1','transfer_2'):
        assert sum(m.locations[r['location_index']].phase==phase for r in m.raw)>8000
    # A vacated-source readout flip changes the known reused destination,
    # but the recorded correction preserves every logical Bell correlation.
    # Using the INPUT source's bit instead of the OUTPUT site's bit would
    # corrupt these logical signatures even while the ideal DEM still passes.
    reused=[s for r,s in zip(m.raw,m.raw_signatures)
            if (l:=m.locations[r['location_index']]).phase=='transfer_1' and l.kind=='readout']
    assert len(reused)==1440 and all(s and not (s>>h.circuit.num_detectors) for s in reused)
    for name in ('a7_uniform_expanded','paper_linearized_unequal','standard_categorical_depolarizing'):
        noisy=emit_noise(h.circuit,ls,NoiseProfile(name,.001))
        dem=noisy.detector_error_model(allow_gauge_detectors=False,approximate_disjoint_errors=False)
        assert dem.num_observables==24 and dem.num_detectors==h.circuit.num_detectors
    # Readout/reset in the X-check bundle are distinct physical fault sites.
    bundles={(l.time,l.qubits) for l in ls if l.gate=='MX'}
    assert bundles=={(l.time,l.qubits) for l in ls if l.gate=='R' and l.phase=='following_syndrome'}
    assert any(l.role=='code_data_on_check' and l.kind=='idle' for l in ls)


def test_negative_shift_profiles_routing_frame_and_noise_boundaries():
    c=load_reference_code('gross','negative'); plan=transfer_plan(c)
    for count in (0,True,1.5):
        with pytest.raises(ValueError,match='positive integer'): shift_sequence(c,count)
    with pytest.raises(ValueError,match='O3'): transfer_plan(c,profile='paper_exact')
    with pytest.raises(ValueError,match='collide'): two_cnot_ops((('a','b'),('a','c')),0,phase='transfer_1')
    with pytest.raises(ValueError,match='permutation'):
        replace(plan,target_to_source=tuple(range(144))).validate(c)
    bad=list(plan.second); bad[0],bad[1]=(bad[0][0],bad[1][1]),(bad[1][0],bad[0][1])
    with pytest.raises(ValueError,match='Tanner|permutation'): replace(plan,second=tuple(bad)).validate(c)
    h=build_shift_benchmark(c,1)
    with pytest.raises(ValueError,match='mismatch'): shift_locations(c,h,2)
    # Signed affine oracle on a short changed boundary: record-offset mistake
    # and omitted reused-destination frame both create a wrong detector.
    verify_deterministic(stim.Circuit('R 0 1\nX 1\nCX 0 1\nCX 1 0\nM 0\nMPAD 1\nDETECTOR rec[-1] rec[-2]'))
    for text in ('R 0 1\nX 1\nCX 0 1\nCX 1 0\nM 0\nDETECTOR rec[-1]',
                 'R 0\nM 0\nMPAD 1\nDETECTOR rec[-1]'):
        with pytest.raises(ValueError,match='nonzero signed flow'): verify_deterministic(stim.Circuit(text))
    changed=h.circuit.copy()
    # A removed real transfer gate cannot be concealed by the same ledger.
    i=next(i for i,op in enumerate(changed) if op.name=='TICK')+1
    changed.pop(i)
    with pytest.raises(ValueError,match='coverage|unexpected'):
        shift_locations(c,replace(h,circuit=changed),1)
    for p,count in ((float('nan'),10),(.1,True),(1.1,10)):
        with pytest.raises(ValueError): shift_rate(p,count)
