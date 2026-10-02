"""Phase08 physical Fig. 13(b), encoded projectors and full named K47 flows."""
from dataclasses import replace
import numpy as np
import pytest
import stim
from gross_design_bandle.algebra import gf2
from gross_design_bandle.algebra.pauli import Pauli
from gross_design_bandle.codes.blocks import CodeBlocks
from gross_design_bandle.codes.reference_profiles import load_reference_code
from gross_design_bandle.lpu.reference import build_reference_lpu
from gross_design_bandle.lpu.code_code_adapter import adapter_connectivity
from gross_design_bandle.surgery.deformation import compile_deformation
from gross_design_bandle.surgery.protocol import to_stim_pauli
from gross_design_bandle.circuits.protocol import build_physical_inter
from gross_design_bandle.circuits.schedule import validate
from gross_design_bandle.validation.physical import check_tableau
from gross_design_bandle.flows.observables import LogicalBasisAdapter, correlation
from gross_design_bandle.flows.boundaries import mpp
from gross_design_bandle.flows.harness import build_benchmark
from gross_design_bandle.flows.signatures import fault_signature, inject_fixed_fault
from gross_design_bandle.flows.stabilizer_flows import verify_deterministic_stim
from gross_design_bandle.noise import NoiseProfile, build_fault_model, emit_noise
from gross_design_bandle.noise.locations import benchmark_locations
from gross_design_bandle.validation.faults import validate_faults


@pytest.fixture(scope='module')
def adapter():
    codes = tuple(load_reference_code('gross',id) for id in ('module_a','module_b'))
    blocks = CodeBlocks(codes)
    df = compile_deformation(build_reference_lpu(codes[0],'inter_XX',codes[1]))
    return blocks,df,build_physical_inter(df),LogicalBasisAdapter.two_blocks(blocks)


@pytest.fixture(scope='module')
def harnesses(adapter):
    blocks,df,_,_ = adapter
    return {mode:build_benchmark(blocks.codes,operation='inter_XX',rounds=10,deformation=df,split_mode=mode)
            for mode in ('frame','active')}


def input_state(blocks, basis, protocol, mode):
    refs = tuple(f'choi:{i}' for i in range(blocks.k))
    register = protocol.register+refs
    stabs = [to_stim_pauli(p,register) for p in blocks.checks]
    witnesses = list(stabs)
    # Independent encoded Choi inputs on the two modules, followed by a
    # genuinely joint random measurement. Known-sign cases use the logical
    # CX basis and are entangled across modules inside the measured sector.
    xs,zs = (blocks.logical_x,blocks.logical_z) if mode == 'independent_choi' else (basis.x,basis.z)
    pairs = []
    for i,(x,z) in enumerate(zip(xs,zs)):
        if i == 0 and mode != 'independent_choi':
            pair = (x.with_phase(2*int(mode=='minus')),Pauli.from_word('X',(refs[0],)))
        else:
            pair = tuple(correlation(p,a,refs[i],register) for p,a in ((x,'X'),(z,'Z')))
        pairs.append(pair)
        stabs.extend(to_stim_pauli(p,register) for p in pair)
        if mode != 'independent_choi':
            witnesses.extend(to_stim_pauli(p,register) for p in pair)
        else:
            witnesses.append(to_stim_pauli(pair[0],register))
            if i not in (0,blocks.codes[0].k):
                witnesses.append(to_stim_pauli(pair[1],register))
    if mode == 'independent_choi':
        witnesses.append(to_stim_pauli(pairs[0][1]*pairs[blocks.codes[0].k][1],register))
    sim = stim.TableauSimulator(seed=0)
    sim.do(stim.Tableau.from_stabilizers(stabs,allow_redundant=True,allow_underconstrained=True).to_circuit())
    return sim,register,refs,witnesses


def test_negative_blocks_profiles_and_rounds_fail_closed(adapter):
    blocks,df,_,_=adapter
    with pytest.raises(ValueError,match='scope'):
        build_benchmark(blocks.codes[0],operation='inter_XX',deformation=df)
    with pytest.raises(ValueError,match='distinct'):
        build_reference_lpu(blocks.codes[0],'inter_XX',load_reference_code('gross','module_a'))
    with pytest.raises(ValueError,match='distinct'):
        CodeBlocks((blocks.codes[0],blocks.codes[0]))
    for rounds in (0,-1,True,1.5):
        with pytest.raises(ValueError,match='positive'): build_physical_inter(df,rounds)
    with pytest.raises(ValueError,match='O1'):
        build_benchmark(blocks.codes,operation='inter_XX',deformation=df,observable_profile='published_inter_K23')
    with pytest.raises(ValueError,match='exact signed target'):
        build_benchmark(tuple(reversed(blocks.codes)),operation='inter_XX',deformation=df)


def test_B05_C10_joint_projector_and_complete_retained_state(adapter):
    blocks,df,p,basis=adapter
    circuit=p.to_stim()
    assert df.merged_k == 23 and df.fixed_input['rank'] == 1
    assert (len(df.graph.vertices),len(df.graph.edges),len(df.graph.cycles)) == (35,58,20)
    assert p.rounds == 10 and not any('bridge:triangle' in id for id in df.group.ids)
    assert not {'MPP','DETECTOR','OBSERVABLE_INCLUDE'} & {i.name for i in circuit.flattened()}
    assert circuit.num_measurements == len(p.outcomes())
    for mode in ('plus','minus','independent_choi'):
        initial,register,refs,witnesses=input_state(blocks,basis,p,mode)
        actual=initial.copy(); actual.do(circuit)
        outcomes=dict(zip(p.outcomes(),map(int,actual.current_measurement_record())))
        bit=p.logical_outcome.evaluate(outcomes)
        if mode != 'independent_choi': assert bit == int(mode=='minus')
        assert initial.peek_observable_expectation(to_stim_pauli(basis.x[0],register)) == (0 if mode=='independent_choi' else (-1)**bit)
        _,frame=p.frame.evaluate(outcomes)
        actual.do_pauli_string(to_stim_pauli(frame,register))
        expected=initial.copy(); expected.postselect_observable(to_stim_pauli(basis.x[0],register),desired_value=bool(bit))
        group=witnesses+[to_stim_pauli(basis.x[0].with_phase(2*bit),register)]
        rows=np.array([[int(a in (1,2)) for a in ps]+[int(a in (2,3)) for a in ps] for ps in group],dtype=np.uint8)
        assert gf2.rank(rows) == len(blocks.qubit_ids)+blocks.k
        for ps in group:
            assert expected.peek_observable_expectation(ps) == actual.peek_observable_expectation(ps) == 1
        for c in blocks.codes:
            assert actual.peek_observable_expectation(to_stim_pauli(c.logical_x[0],register)) == 0
        for id,old in zip(blocks.check_ids,blocks.checks):
            assert outcomes[f'memory/0/{id}/0'] == frame.symplectic(old)


def test_B05_negative_separate_logicals_destroy_joint_coherence(adapter):
    blocks,_,p,basis=adapter
    initial,register,refs,_=input_state(blocks,basis,p,'plus')
    bad=initial.copy()
    for c in blocks.codes: bad.do(mpp(c.logical_x[0],register))
    preserved=to_stim_pauli(correlation(basis.z[12],'Z',refs[12],register),register)
    assert initial.peek_observable_expectation(preserved) == 1
    assert bad.peek_observable_expectation(preserved) == 0


def test_C_Bell_partition_XOR_schedule_and_resource_census(adapter):
    blocks,_,p,_=adapter
    ledger=adapter_connectivity(p)
    assert ledger['active_qubits'] == p.ledger()['active_qubits'] == 710
    assert ledger['installed_qubits'] == 778 and len(ledger['inactive_installed_qubits']) == 68
    assert p.ledger()['installed_qubits'] == 778 and p.ledger()['allocated_fragment_qubits'] == 710
    assert all(len(qs)==11 for qs in ledger['bridge_data_by_module'].values())
    assert ledger['maximum_installed_degree'] <= 7
    assert len(ledger['owners']) == 778
    assert len(ledger['cross_module_checks']) == 21
    assert sum(c.id.startswith('vertex:adapter:') for c in p.cycle.checks) == 11
    assert sum(c.id.startswith('cycle:adapter:') for c in p.cycle.checks) == 10
    assert validate(p.cycle)['eq67_overlap_pairs'] > 0
    for c in p.cycle.checks:
        assert check_tableau(p.cycle,c,composite=True)['signed_readout_matches']
    assert all(len(c['physical_readout_XOR'])==2 for c in ledger['cross_module_checks'])


def test_C_Bell_negative_wrong_module_and_missing_preparation(adapter):
    _,_,p,_=adapter
    check=next(c for c in p.cycle.checks if c.id.startswith('cycle:adapter:'))
    left,right=check.parts
    wrong=replace(check,parts=((left[0],)+right[1:],(right[0],)+left[1:]))
    bad=replace(p,cycle=replace(p.cycle,checks=tuple(wrong if c.id==check.id else c for c in p.cycle.checks)))
    with pytest.raises(ValueError,match='physical modules'): adapter_connectivity(bad)
    missing=replace(p.cycle,ops=tuple(o for o in p.cycle.ops if o.check_id != check.id or o.phase!='bell_prepare'))
    with pytest.raises(ValueError,match='Bell preparation'): validate(missing)


def test_K47_named_centralizer_distinct_from_K23_dimension(adapter,harnesses):
    blocks,df,_,basis=adapter
    cert=basis.certificate(blocks)
    assert cert['rank'] == 47 and df.merged_k == 23
    assert cert['profile']=='full_two_block_centralizer_K47' and not cert['paper_exact']
    assert len(cert['names'])==len(set(cert['names']))==47
    assert set(cert['names']) == {basis.x_names[0]} | {f'{c.block_id}:X{i}' for c in blocks.codes for i in c.logical_labels if not (c==blocks.codes[0] and i=='1')} | {f'{c.block_id}:Z{i}' for c in blocks.codes for i in c.logical_labels if i!='1'} | {basis.z_names[12]}
    assert all(p.commutes(df.lpu.ports.target) for p in basis.generators)
    assert all(h.logical_generators['rank']==47 for h in harnesses.values())


def test_D_inter_C10_strict_boundaries_and_Bell_XOR_negative(adapter,harnesses):
    blocks,df,p,_=adapter
    for h in harnesses.values():
        result=h.validate()
        assert result['exact_flows']['all_zero'] and result['strict_dem_observables']==47
        assert len(h.boundary_policy['ideal_reference_qubits'])==23
        assert len([a for a in h.annotations if a['name'].startswith('split/old:')])==288
        assert {'merge','repeat','split','final_closure','logical_action'} <= {a['flow_class'] for a in h.annotations}
        assert 'MPP' not in {i.name for i in h.physical_body.flattened()}
    # A single half is random. Lose one half from a first joint-cycle detector
    # while preserving the physical Bell circuit: strict DEM must reject it.
    h=harnesses['frame']; bad=stim.Circuit(); changed=False
    annotation=next(a for a in h.annotations if a['name'].startswith('deformed/0/cycle:adapter:'))
    ids=annotation['parity']['ids']; indexes={id:i for i,id in enumerate(h.outcome_ids)}
    seen=0
    for op in h.circuit.flattened():
        if op.name=='DETECTOR' and set(seen+t.value for t in op.targets_copy())=={indexes[id] for id in ids} and not changed:
            bad.append('DETECTOR',op.targets_copy()[:1]); changed=True
        else: bad.append(op)
        seen += op.num_measurements
    assert changed
    with pytest.raises(ValueError,match='non-deterministic'): verify_deterministic_stim(bad)


@pytest.fixture(scope='module')
def fault_model(adapter,harnesses):
    blocks,df,_,_=adapter; h=harnesses['frame']
    locations,policy=benchmark_locations(blocks.codes,h,operation='inter_XX',rounds=10,deformation=df)
    return build_fault_model(h.circuit,locations,NoiseProfile('a7_uniform_expanded',.001),
                            admission_policy='include_all',grouping_policy='joint_signature_xor'),policy


def test_D_inter_joint_faults_and_active_frame_equivalence(adapter,harnesses,fault_model,tmp_path):
    model,policy=fault_model
    result=validate_faults(model,exhaustive=False,counterexample_path=tmp_path/'counterexample.json')
    assert result['all_agree'] and model.Lambda.shape[0]==47
    roles={t['location']['role'] for t in result['trials']}
    for kind in ('identifying','joint_cycle'):
        assert kind+'_Bell_preparation' in roles
        for half in (0,1): assert f'{kind}_Bell_half_{half}_interaction' in roles
    assert model.N==len(model.copy_to_raw) and model.H.shape[1]==model.Lambda.shape[1]
    report=model.discrepancy(743456,policy)
    assert report['delta_admitted_minus_published']==model.N-743456
    # Identical physical faults with both correction conventions, including
    # both halves and joint X/Z, on changed bridge gates and split readouts.
    active=harnesses['active'].circuit
    for role in ('identifying_Bell_half_0_interaction','joint_cycle_Bell_half_1_interaction','reset_or_readout'):
        loc=next(l for l in model.locations if l.role==role and (role!='reset_or_readout' or l.phase=='split'))
        x=sum(1<<q for q in loc.qubits); z=1<<loc.qubits[-1]
        expected=fault_signature(model.circuit,loc.after_instruction,x,z)
        other=fault_signature(active,loc.after_instruction,x,z)
        assert all(np.array_equal(a,b) for a,b in zip(expected,other))
        actual=inject_fixed_fault(active,loc.after_instruction,x,z).compile_detector_sampler(seed=0).sample(1,separate_observables=True)
        assert all(np.array_equal(a,b[0]) for a,b in zip(expected,actual))
    noisy=emit_noise(model.circuit,model.locations,model.profile)
    assert noisy.detector_error_model(allow_gauge_detectors=False).num_observables==47
