"""Phase07 full physical instruments; exact signed and independent fault oracles.

Encoded Choi witnesses cover the complete DATA+reference stabilizer group.
C10 is used throughout the gross physical profile; no noisy rate sampling.
"""
from dataclasses import replace
import json
import numpy as np
import pytest
import stim
from gross_design_bandle.algebra import gf2
from gross_design_bandle.algebra.pauli import Pauli
from gross_design_bandle.codes.reference_profiles import load_reference_code
from gross_design_bandle.lpu.reference import build_reference_lpu
from gross_design_bandle.surgery.deformation import compile_deformation
from gross_design_bandle.surgery.ports import product
from gross_design_bandle.surgery.frame import Parity
from gross_design_bandle.surgery.protocol import to_stim_pauli
from gross_design_bandle.circuits.protocol import build_physical_inmodule
from gross_design_bandle.circuits.checks import support
from gross_design_bandle.circuits.schedule import validate
from gross_design_bandle.validation.physical import check_tableau
from gross_design_bandle.validation.connectivity import installed_connectivity
from gross_design_bandle.flows.harness import build_benchmark, TruthTableInstrument, frame_parity
from gross_design_bandle.flows.observables import LogicalBasisAdapter, correlation
from gross_design_bandle.flows.boundaries import input_boundary, mpp
from gross_design_bandle.flows.records import RecordProgram, Chunk, Repeat, Annotation
from gross_design_bandle.flows.stabilizer_flows import verify_deterministic
from gross_design_bandle.flows.signatures import fault_signature, inject_fixed_fault
from gross_design_bandle.noise import NoiseProfile, build_fault_model, emit_noise
from gross_design_bandle.noise.locations import benchmark_locations
from gross_design_bandle.validation.faults import validate_faults

TARGETS = ('X1*X7', 'Y1')


@pytest.fixture(scope='module')
def operations():
    code = load_reference_code('gross', 'phase07')
    return code, {target:compile_deformation(build_reference_lpu(code, op))
                  for target,op in zip(TARGETS,('XX','Y'))}


@pytest.fixture(scope='module')
def harnesses(operations):
    c, dfs = operations
    return {t:{mode:build_benchmark(c, operation=t, rounds=2, deformation=df, split_mode=mode)
               for mode in ('frame','active')} for t,df in dfs.items()}


@pytest.fixture(scope='module')
def c10_harnesses(operations):
    c,dfs=operations
    return {t:{mode:build_benchmark(c,operation=t,rounds=10,deformation=df,split_mode=mode)
               for mode in ('frame','active')} for t,df in dfs.items()}


@pytest.fixture(scope='module')
def models(operations, c10_harnesses):
    c, dfs = operations
    result = {}
    for t,df in dfs.items():
        h = c10_harnesses[t]['frame']
        ls,policy = benchmark_locations(c,h,operation=t,rounds=10,deformation=df)
        result[t] = build_fault_model(h.circuit,ls,NoiseProfile('a7_uniform_expanded',.001),
                     admission_policy='include_all',grouping_policy='joint_signature_xor'),policy
    return result


def encoded_input(c, basis, physical, mode, seed):
    refs = tuple(f'choi_ref:{i}' for i in range(c.k))
    register = physical.register+refs
    stabs = [to_stim_pauli(p,register) for p in c.checks]
    witnesses = list(stabs)
    for i,(x,z) in enumerate(zip(basis.x,basis.z)):
        if i == 0 and mode != 'choi':
            pair = (x.with_phase(2*int(mode=='minus')),Pauli.from_word('X',(refs[0],)))
        else:
            pair = tuple(correlation(p,a,refs[i],register) for p,a in ((x,'X'),(z,'Z')))
        stabs += [to_stim_pauli(p,register) for p in pair]
        if i or mode != 'choi':
            witnesses += [to_stim_pauli(p,register) for p in pair]
    initial = stim.TableauSimulator(seed=seed)
    initial.do(stim.Tableau.from_stabilizers(stabs,allow_redundant=True,allow_underconstrained=True).to_circuit())
    return initial, register, refs, witnesses


@pytest.mark.parametrize('target', TARGETS)
def test_B04_complete_C10_signed_instrument_and_encoded_coherence(operations, target):
    c,dfs = operations; df = dfs[target]
    p = build_physical_inmodule(df)  # gross default C=10
    basis = LogicalBasisAdapter.single_block(c,target)
    assert p.rounds == 10 and p.cycle.data[len(c.qubit_ids):] == tuple('edge:'+e for e in df.graph.edge_ids)
    instrument = TruthTableInstrument(p)
    circuit = instrument.circuit
    readouts = p.cycle.readouts()
    assert not {'MPP','DETECTOR','OBSERVABLE_INCLUDE'} & {op.name for op in circuit.flattened()}
    assert circuit.num_measurements == len(p.outcomes()) == 10*187+47+144
    for mode in ('plus','minus','choi'):
        initial,register,refs,witnesses = encoded_input(c,basis,p,mode,0)
        actual = initial.copy(); actual.do(circuit)
        outcomes = dict(zip(p.outcomes(),map(int,actual.current_measurement_record())))
        m = instrument.logical_outcome.evaluate(outcomes)
        assert m == int(mode=='minus') if mode != 'choi' else m in (0,1)
        _,frame = p.frame.evaluate(outcomes)
        actual.do_pauli_string(to_stim_pauli(frame,register))
        assert initial.peek_observable_expectation(to_stim_pauli(basis.x[0],register)) == (0 if mode=='choi' else (-1)**m)
        expected = initial.copy()
        expected.postselect_observable(to_stim_pauli(basis.x[0],register),desired_value=bool(m))
        expected_group = witnesses+[to_stim_pauli(basis.x[0].with_phase(2*m),register)]
        if mode == 'choi':
            expected_group += [to_stim_pauli(Pauli.from_word('X',(refs[0],),(-1)**m),register)]
        # Complete rank-n basis on data + all twelve references. Matching
        # every +1 generator certifies the reduced pure state, including
        # coherence within the measured eigenspace (not just output bits).
        assert gf2.rank(np.array([[int(a in (1,2)) for a in ps]+[int(a in (2,3)) for a in ps]
                                 for ps in expected_group],dtype=np.uint8)) == c.spec.n+c.k
        for ps in expected_group:
            assert expected.peek_observable_expectation(ps) == actual.peek_observable_expectation(ps) == 1
        for check in p.cycle.checks:
            values = [sum(outcomes[i.replace('deformed/0/',f'deformed/{r}/')]
                          for i in readouts[f'{check.id}/0'])%2 for r in range(10)]
            assert len(set(values)) == 1
            if not check.id.startswith('vertex:'):
                assert values == [0]*10
        for id,old in zip(c.check_ids,c.checks):
            assert outcomes[f'memory/0/{id}/0'] == frame.symplectic(old)
        if target == 'X1*X7':
            # Measuring the product must leave each separate factor random.
            assert actual.peek_observable_expectation(to_stim_pauli(c.logical_x[0],register)) == 0
            assert actual.peek_observable_expectation(to_stim_pauli(c.logical_x[6],register)) == 0


def test_B04_negative_separate_factors_destroy_retained_coherence(operations):
    c,dfs = operations
    for target,factors,witness in (
        ('X1*X7',(c.logical_x[0],c.logical_x[6]),6),
        ('Y1',(c.logical_x[0],c.logical_z[0]),0)):
        p=build_physical_inmodule(dfs[target]); basis=LogicalBasisAdapter.single_block(c,target)
        initial,register,refs,_=encoded_input(c,basis,p,'plus',7)
        bad=initial.copy()
        for factor in factors: bad.do(mpp(factor,register))
        preserved = correlation(basis.z[witness],'Z',refs[witness],register) if witness else basis.x[0]
        assert initial.peek_observable_expectation(to_stim_pauli(preserved,register)) == 1
        assert bad.peek_observable_expectation(to_stim_pauli(preserved,register)) == 0


def test_same_installed_geometry_mixed_ports_Bell_partition_and_schedule(operations):
    c,dfs=operations; xx,y=(dfs[t] for t in TARGETS)
    assert xx.graph == y.graph and xx.lpu.installed_full_census == y.lpu.installed_full_census
    installed = installed_connectivity(c)
    edges = {frozenset(e) for e in installed['edges']}
    cycles=[]; active=[]
    for df in (xx,y):
        p=build_physical_inmodule(df); s=p.cycle; cycles.append(s)
        assert validate(s)['collision_free'] and validate(s)['eq67_overlap_pairs']>0
        for check in s.checks:
            assert check_tableau(s,check,composite=True)['signed_readout_matches']
        couplers={frozenset(o.qubits) for o in s.ops if o.gate in ('CX','CY','CZ')}
        assert couplers <= edges; active.append(couplers)
        ledger=p.ledger()
        assert ledger['installed_qubits']==ledger['active_qubits']==378
        assert len(ledger['bell_couplers'])==1
        assert len(df.graph.cycles)==19 and df.merged_k==11
        bell=next(check for check in s.checks if check.kind=='bell')
        assert len(bell.parts)==2 and not set(bell.parts[0]) & set(bell.parts[1])
        assert set(bell.parts[0]) | set(bell.parts[1]) == set(support(bell.pauli))
        assert len(s.readouts()[f'{bell.id}/0'])==2
        assert product(df.lpu.ports.ports,c.qubit_ids)==df.lpu.ports.target
    assert cycles[0].register==cycles[1].register and active[0] != active[1]
    assert xx.lpu.ports.ports != y.lpu.ports.ports and not np.array_equal(xx.dressing,y.dressing)
    shared=y.lpu.ports.ports[y.graph.vertices.index(y.graph.shared_vertex)]
    assert list(support(shared).values()).count('Y')==1
    assert y.lpu.ports.target==(c.logical_x[0]*c.logical_z[0]).with_phase(1)
    assert any(o.gate=='CY' for o in cycles[1].ops)


@pytest.mark.parametrize('target', TARGETS)
def test_D01_nested_full_Bell_rounds_preserve_parities(operations, target):
    c,dfs=operations; p=build_physical_inmodule(dfs[target]); s=p.cycle
    initial,register,_=input_boundary(c,LogicalBasisAdapter.single_block(c,target),s.register)
    prep=stim.Circuit(); prep.append('R',[register.index(q) for q in s.data[len(c.qubit_ids):]])
    ids=tuple(f'm{i}' for i in range(len(s.outcomes)))
    by_id=dict(zip(s.outcomes,ids)); body=[Chunk(s.to_stim(),ids)]
    readouts=s.readouts()
    for check in s.checks:
        current=tuple(by_id[i] for i in readouts[f'{check.id}/0'])
        body.append(Annotation(check.id,'detector',Parity(current+tuple('prev_'+i for i in current)),
                               'repeat','stable signed joint readout, including both Bell halves'))
    inner=Repeat('inner',2,tuple(body),tuple(('prev_'+i,'outer_'+i,i) for i in ids))
    outer=Repeat('outer',2,(inner,),tuple(('outer_'+i,'seed_'+i,'inner/1/'+i) for i in ids))
    program=RecordProgram((Chunk(initial),Chunk(prep),Chunk(s.to_stim(),tuple('seed_'+i for i in ids)),outer))
    compact,unrolled=program.lower(),program.lower(compact=False)
    assert compact.circuit.flattened()==unrolled.circuit.flattened()
    assert compact.annotations==unrolled.annotations and compact.outcome_ids==unrolled.outcome_ids
    from gross_design_bandle.flows.stabilizer_flows import verify_deterministic_stim
    assert verify_deterministic_stim(compact.circuit)['all_zero']
    assert compact.circuit.detector_error_model(allow_gauge_detectors=False).num_detectors==4*186


@pytest.mark.parametrize('target', TARGETS)
def test_D02_C10_strict_harness_every_boundary_and_raw_API(operations,harnesses,c10_harnesses,target):
    # Strict DEM/raw signs on both C10 split modes, independently checked by
    # signed affine propagation on the short changed boundaries.
    variants = list(harnesses[target].items())+[
        ('C10_'+mode,h) for mode,h in c10_harnesses[target].items()]
    for mode,h in variants:
        cert=h.validate(flow_oracle="stim_reference" if mode.startswith("C10_") else "signed_affine")
        assert cert['exact_flows']['all_zero'] and cert['strict_dem_observables']==23
        assert not cert['gauge_workaround'] and not h.to_dict()['paper_exact']
        d,l=h.circuit.compile_detector_sampler(seed=47).sample(4,separate_observables=True)
        assert not d.any() and not l.any()
        assert 'MPP' not in {i.name for i in h.physical_body.flattened()}
        assert {'merge','repeat','split','final_closure','logical_action'} <= {a['flow_class'] for a in h.annotations}
        assert all(a['justification'] for a in h.annotations)
        assert all(a['parity']['ids'] for a in h.annotations if a['kind'] in ('detector','observable'))
        # Empty rooted-path correction terms are explicit classical no-ops.
        assert all(a['kind'] in ('CX','CY','CZ') for a in h.annotations if not a['parity']['ids'])
        assert len([a for a in h.annotations if a['name'].startswith('split/old:')])==144
        assert len(set(h.outcome_ids))==h.circuit.num_measurements
        c,dfs=operations; df=dfs[target]
        assert h.boundary_policy['measured_slot']==df.lpu.ports.target.to_dict()
        assert len(h.boundary_policy['edge_reset_Z_qubits'])==47
        frame=build_physical_inmodule(df).frame
        for j,(id,old) in enumerate(zip(c.check_ids,c.checks)):
            a=next(a for a in h.annotations if a['name']==f'split/old:{id}')
            expected=Parity(tuple(f'split/{edge}' for edge,bit in zip(df.graph.edge_ids,df.dressing[j]) if bit))
            if h.split_mode=='active': expected ^= frame_parity(frame,old)
            assert {i for i in a['parity']['ids'] if i.startswith('split/')}==set(expected.ids)


@pytest.mark.parametrize('target', TARGETS)
def test_D03_C10_joint_fault_strata_and_Table6_population(models,target,tmp_path):
    m,policy=models[target]
    result=validate_faults(m,exhaustive=False,counterexample_path=tmp_path/f'{target}-counterexample.json')
    assert result['all_agree']
    anchors = {0,5,9}
    expected = {(l.phase,l.gate,l.role,l.round) for l in m.locations if l.round in anchors}
    actual = {(t['location']['phase'],t['location']['gate'],t['location']['role'],t['location']['round'])
              for t in result['trials']}
    assert actual == expected
    trials=result['trials']
    assert {t['location']['phase'] for t in trials}=={'edge_initialize','deformed','split'}
    assert {t['location']['round'] for t in trials}>={0,5,9}
    assert any(t['location']['role']=='Bell_preparation' for t in trials)
    for half in (0,1):
        assert any(t['location']['role']==f'Bell_half_{half}_interaction' for t in trials)
        assert any(t['location']['role']==f'Bell_half_{half}_reset_or_readout' for t in trials)
    if target=='Y1': assert any(t['location']['gate']=='CY' for t in trials)
    published=398717 if target=='X1*X7' else 400117
    report=m.discrepancy(published,policy)
    assert report['include_all_N']==m.N and report['delta_admitted_minus_published']==m.N-published
    assert m.H.shape[1]==m.Lambda.shape[1]==m.N and m.Lambda.shape[0]==23
    assert report['delta_admitted_minus_published'] != 0  # documented independent policy, no padding
    noisy=emit_noise(m.circuit,m.locations,m.profile)
    dem=noisy.detector_error_model(allow_gauge_detectors=False,approximate_disjoint_errors=False)
    assert dem.num_observables==23 and dem.num_detectors==m.H.shape[0]


@pytest.mark.parametrize('target', TARGETS)
def test_D04_active_frame_joint_fault_signatures_and_closure(models,c10_harnesses,target,tmp_path):
    m,_=models[target]; active=c10_harnesses[target]['active']
    # All primitive tensor words across each noisy phase/gate/role and the
    # first/middle/last rounds. Copies preserve the same joint signature.
    from gross_design_bandle.noise.signatures import joint_signatures
    # Compare EVERY raw column with active feedforward using the reverse sweep.
    # Separate forward/Stim checks then span all boundaries/gates/physical roles.
    faults=[(m.locations[r['location_index']].after_instruction,r['x'],r['z']) for r in m.raw]
    assert joint_signatures(active.circuit,faults)==m.raw_signatures
    chosen={}
    for j,raw in enumerate(m.raw):
        loc=m.locations[raw['location_index']]
        if loc.round in (0,5,9):
            chosen.setdefault((loc.phase,loc.gate,loc.role,loc.round),j)
    for j in chosen.values():
        raw=m.raw[j]; loc=m.locations[raw['location_index']]
        expected=fault_signature(m.circuit,loc.after_instruction,raw['x'],raw['z'])
        actual=fault_signature(active.circuit,loc.after_instruction,raw['x'],raw['z'])
        if any(not np.array_equal(a,b) for a,b in zip(expected,actual)):
            (tmp_path/'active-frame-counterexample.json').write_text(json.dumps({'raw':raw,'location':loc.to_dict()}))
            pytest.fail('active/frame counterexample')
        # Independent probability-one oracle also exercises active feedforward.
        ds,ls=inject_fixed_fault(active.circuit,loc.after_instruction,raw['x'],raw['z']).compile_detector_sampler(seed=12).sample(1,separate_observables=True)
        np.testing.assert_array_equal(ds[0],actual[0]); np.testing.assert_array_equal(ls[0],actual[1])
    assert set(chosen)=={(l.phase,l.gate,l.role,l.round) for l in m.locations if l.round in (0,5,9)}
    # Diagnostic faults at the NOISELESS original verification and ideal
    # terminal boundaries are outside the primitive population, but their
    # signatures must still agree between active and recorded correction.
    def physical_boundaries(h):
        n=0; found={}
        for i,op in enumerate(h.circuit.flattened()):
            if op.name in ('M','MX','MPP'):
                found[n,str(op)]=i
            n+=stim.Circuit(str(op)).num_measurements
        return found
    frame_boundaries=physical_boundaries(c10_harnesses[target]['frame'])
    active_boundaries=physical_boundaries(active)
    for boundary_prefix in ('memory/0/','closure/','logical_terminal/'):
        key=next(k for k in frame_boundaries if m.circuit.num_measurements>k[0]
                 and c10_harnesses[target]['frame'].outcome_ids[k[0]].startswith(boundary_prefix))
        fi,ai=frame_boundaries[key],active_boundaries[key]
        op=list(m.circuit.flattened())[fi]
        q=next(t.value for t in op.targets_copy() if not t.is_combiner)
        expected=fault_signature(m.circuit,fi-1,1<<q,1<<q)
        observed=fault_signature(active.circuit,ai-1,1<<q,1<<q)
        assert all(np.array_equal(a,b) for a,b in zip(expected,observed))
        ds,ls=inject_fixed_fault(active.circuit,ai-1,1<<q,1<<q).compile_detector_sampler(seed=92).sample(1,separate_observables=True)
        np.testing.assert_array_equal(ds[0],observed[0]); np.testing.assert_array_equal(ls[0],observed[1])
    assert any(i.name=='CY' and any(t.is_measurement_record_target for t in i.targets_copy())
               for i in active.physical_body.flattened()) if target=='Y1' else True


@pytest.mark.parametrize('target', TARGETS)
def test_D05_named_K23_physical_logical_action_complete_rank(operations,c10_harnesses,target):
    c,dfs=operations; h=c10_harnesses[target]['frame']; basis=LogicalBasisAdapter.single_block(c,target)
    cert=h.logical_generators
    assert cert['rank']==gf2.rank(np.array(cert['logical_coordinates'],dtype=np.uint8))==23
    assert len(set(cert['names']))==23 and all(p.commutes(basis.x[0]) for p in basis.generators)
    initial,_,_=input_boundary(c,basis,build_physical_inmodule(dfs[target]).register)
    boundary=len(list(initial.flattened()))-1; actions=[]
    for p in c.logical_x+c.logical_z:
        x=sum(b<<q for q,b in enumerate(p.x)); z=sum(b<<q for q,b in enumerate(p.z))
        d,l=fault_signature(h.circuit,boundary,x,z)
        expected=np.array([p.symplectic(g) for g in basis.generators],dtype=np.uint8)
        assert not d.any(); np.testing.assert_array_equal(l,expected)
        ds,ls=inject_fixed_fault(h.circuit,boundary,x,z).compile_detector_sampler(seed=83).sample(1,separate_observables=True)
        np.testing.assert_array_equal(ds[0],d); np.testing.assert_array_equal(ls[0],l); actions.append(l)
    assert gf2.rank(np.array(actions,dtype=np.uint8))==23


@pytest.mark.parametrize('target', TARGETS)
def test_negative_Bell_offset_frame_and_target_corruption(operations,harnesses,target):
    c,dfs=operations; h=harnesses[target]['frame']; df=dfs[target]
    # Wrong offset and missing Bell half on the actual repeated shared check.
    names=[a['name'] for a in h.annotations if a['kind']=='detector']
    shared=f'deformed/1/vertex:{df.graph.shared_vertex}'
    for mutation in ('offset','half'):
        bad=stim.Circuit(); k=0; changed=False
        for op in h.circuit.flattened():
            if op.name=='DETECTOR':
                name=names[k]; k+=1
                if name==shared:
                    ts=op.targets_copy()
                    assert len(ts)==4
                    if mutation=='offset': ts[-1]=stim.target_rec(ts[-1].value-1)
                    else: ts=ts[:-1]
                    bad.append('DETECTOR',ts); changed=True; continue
            bad.append(op)
        assert changed
        with pytest.raises(ValueError,match='nonzero signed flow'): verify_deterministic(bad)
        with pytest.raises(ValueError,match='non-deterministic detectors'): bad.detector_error_model(allow_gauge_detectors=False)
    a=next(a for a in h.annotations if a['kind']=='observable' and a['observable_index']>=12
           and any(i.startswith('split/') for i in a['parity']['ids']))
    bad=stim.Circuit()
    for op in h.circuit.flattened():
        if op.name=='OBSERVABLE_INCLUDE' and int(op.gate_args_copy()[0])==a['observable_index']:
            ts=[t for t in op.targets_copy() if h.outcome_ids[h.circuit.num_measurements+t.value].startswith('logical_terminal/')]
            bad.append(op.name,ts,op.gate_args_copy())
        else: bad.append(op)
    with pytest.raises(ValueError,match='nonzero signed flow'): verify_deterministic(bad)
    with pytest.raises(ValueError,match='non-deterministic observables'): bad.detector_error_model(allow_gauge_detectors=False)
    # A self-consistent but sign-inverted target cannot enter the named harness.
    ports=replace(df.lpu.ports,target=df.lpu.ports.target.with_phase(2),
                  ports=(df.lpu.ports.ports[0].with_phase(2),)+df.lpu.ports.ports[1:])
    wrong=compile_deformation(replace(df.lpu,ports=ports))
    with pytest.raises(ValueError,match='exact signed target'): build_benchmark(c,operation=target,deformation=wrong)
    with pytest.raises(ValueError,match='imaginary-phase'):
        replace(df.lpu.ports,target=df.lpu.ports.target.with_phase(1))
    if target=='Y1':
        p=build_physical_inmodule(df); bell=next(c for c in p.cycle.checks if c.kind=='bell')
        bad=replace(p.cycle,ops=tuple(replace(o,gate='CX') if o.gate=='CY' else o for o in p.cycle.ops))
        with pytest.raises(ValueError,match='wrong signed Pauli'): check_tableau(bad,bell)
        with pytest.raises(ValueError,match='wrong controlled Pauli'): validate(bad)


def test_negative_scope_and_noise_policy_fail_closed(operations,harnesses):
    c,dfs=operations
    for rounds in (0,-1,True,1.5):
        with pytest.raises(ValueError,match='positive'): build_physical_inmodule(dfs['Y1'],rounds)
    with pytest.raises(ValueError,match='exact signed target'):
        build_benchmark(c,operation='Y1',deformation=dfs['X1*X7'])
    with pytest.raises(ValueError,match='software split frame'):
        benchmark_locations(c,harnesses['Y1']['active'],operation='Y1',rounds=2,deformation=dfs['Y1'])
    with pytest.raises(ValueError,match='O1'): LogicalBasisAdapter.single_block(c,'published_inter_K23')
    with pytest.raises(ValueError,match='in-module'):
        build_physical_inmodule(compile_deformation(build_reference_lpu(c,'inter_XX',load_reference_code('gross','other'))))


def test_negative_signed_flow_cache_tracks_phase_value_and_state_changes():
    from gross_design_bandle.flows.stabilizer_flows import SignedTracker, Row
    tracker=SignedTracker(1); z=Row(0,1)
    assert tracker.known(z)==0
    cache=tracker._known_basis
    tracker.measure(z)
    assert tracker.known(z)==0 and tracker._known_basis is cache
    # The binary span is unchanged but the sign/affine value changes. A
    # phase-blind cache would incorrectly accept the final known-minus flow.
    tracker.rows[0]=Row(0,1,2)
    assert tracker.known(z)==1 and tracker._known_basis is not cache
    tracker.rows[0]=Row(0,1,2,8)
    assert tracker.known(z)==9
    tracker.reset(0,'X')
    assert tracker.known(z) is None
    tracker.gate('H',[0])
    assert tracker.known(z)==0
    tracker.gate('X',[0])
    assert tracker.known(z)==1
    tracker.reset(0,'X'); tracker.measure(z)
    assert tracker.known(z)==tracker.measurements[-1] != 0
    with pytest.raises(ValueError,match='nonzero signed flow'):
        verify_deterministic(stim.Circuit('RX 0\nMX 0\nZ 0\nMX 0\nDETECTOR rec[-1]'))


def test_negative_joint_Bell_preparation_subspace_required(operations):
    c,dfs=operations; p=build_physical_inmodule(dfs['X1*X7'])
    triangle=next(check for check in p.cycle.checks if check.id.endswith('bridge:triangle'))
    assert check_tableau(p.cycle,triangle,composite=True)['nondemolition']
    bad=replace(p.cycle,ops=tuple(o for o in p.cycle.ops if o.phase!='bell_prepare'))
    with pytest.raises(ValueError,match='ancilla|preserve'):
        check_tableau(bad,triangle,composite=True)


def test_D02_exact_reference_signs_agree_with_independent_affine_oracle():
    from gross_design_bandle.flows.stabilizer_flows import verify_deterministic_stim
    for text in ('RX 0\nMX 0\nDETECTOR rec[-1]\nOBSERVABLE_INCLUDE(0) rec[-1]',
                 'RY 0\nMY 0\nDETECTOR rec[-1]',
                 'RX 0\nZ 0\nMX 0\nMPAD 1\nDETECTOR rec[-1] rec[-2]'):
        c=stim.Circuit(text)
        assert verify_deterministic_stim(c)['all_zero'] and verify_deterministic(c)['all_zero']
    for text in ('RX 0\nZ 0\nMX 0\nDETECTOR rec[-1]',
                 'RX 0\nZ 0\nMX 0\nOBSERVABLE_INCLUDE(0) rec[-1]'):
        c=stim.Circuit(text)
        # Strict determinacy alone permits a constant - sign, which the
        # reference-record sign check must reject (sampler flips hide it).
        c.detector_error_model(allow_gauge_detectors=False)
        for oracle in (verify_deterministic,verify_deterministic_stim):
            with pytest.raises(ValueError,match='nonzero signed flow'): oracle(c)
    with pytest.raises(ValueError,match='non-deterministic'):
        verify_deterministic_stim(stim.Circuit('RX 0\nM 0\nDETECTOR rec[-1]'))
    with pytest.raises(ValueError,match='unsupported'):
        verify_deterministic_stim(stim.Circuit('R 0\nX_ERROR(.1) 0'))
