"""D01--D05: exact signed flows, strict DEM and independent fault propagation."""
from dataclasses import replace
from itertools import product
import json
import numpy as np
import pytest
import stim
from gross_design_bandle.algebra import gf2
from gross_design_bandle.algebra.pauli import Pauli
from gross_design_bandle.codes.reference_profiles import load_reference_code
from gross_design_bandle.lpu.reference import build_reference_lpu
from gross_design_bandle.surgery.deformation import compile_deformation
from gross_design_bandle.surgery.frame import Parity
from gross_design_bandle.surgery.protocol import to_stim_pauli
from gross_design_bandle.circuits.checks import Check
from gross_design_bandle.circuits.primitive import primitive_schedule
from gross_design_bandle.flows.records import RecordProgram, Chunk, Annotation, Repeat
from gross_design_bandle.flows.stabilizer_flows import SignedTracker, Row, pauli_row, verify_deterministic
from gross_design_bandle.flows.observables import LogicalBasisAdapter
from gross_design_bandle.flows.boundaries import mpp
from gross_design_bandle.flows.harness import build_benchmark, TruthTableInstrument
from gross_design_bandle.flows.signatures import fault_signature, inject_fixed_fault


@pytest.fixture(scope='module')
def harnesses():
    code = load_reference_code('gross', 'flow_test')
    df = compile_deformation(build_reference_lpu(code, 'X'))
    return code, df, {
        'memory':build_benchmark(code, rounds=3),
        'frame':build_benchmark(code, operation='X1', rounds=3, deformation=df),
        'active':build_benchmark(code, operation='X1', rounds=3, deformation=df, split_mode='active')}


def test_D01_nested_repeat_symbolic_records_and_signed_constants():
    inner = (Chunk(stim.Circuit('RX 0\nZ 0\nMX 0'), ('negative_x',)),
             Annotation('known_minus', 'detector', Parity(('negative_x',),1), 'reset', '-X after RX then Z'))
    outer = (Chunk(stim.Circuit('R 1\nM 1'), ('zero',)), Repeat('inner',3,inner),
             Annotation('outer', 'detector', Parity(('zero',)), 'repeat', 'reset Z'))
    program = RecordProgram((Repeat('outer',2,outer),))
    compact = program.lower(); unrolled = program.lower(compact=False)
    assert compact.circuit.flattened() == unrolled.circuit.flattened()
    assert compact.outcome_ids == unrolled.outcome_ids
    assert len(compact.outcome_ids) == len(set(compact.outcome_ids)) == 14
    assert compact.annotations == unrolled.annotations
    assert 'REPEAT 2' in str(compact.circuit) and 'REPEAT 3' in str(compact.circuit)
    assert compact.outcome_ids[1] == 'outer/0/inner/0/negative_x'
    assert verify_deterministic(compact.circuit)['all_zero']
    assert compact.circuit.detector_error_model(allow_gauge_detectors=False).num_detectors == 8


def test_D01_nested_repeat_carries_random_stabilizer_sign_across_iterations():
    # A genuinely random initial Z outcome, then repeated nondemolition Z.
    # Both nested repeat levels carry an absolute previous outcome identity.
    inner = (Chunk(stim.Circuit('M 0'), ('m',)),
             Annotation('repeat_Z','detector',Parity(('m','prev')), 'repeat', 'stable signed Z'))
    outer = (Repeat('inner',3,inner,(('prev','outer_prev','m'),)),
             Annotation('cross_inner','detector',Parity(('inner/0/m','inner/2/m')),
                        'repeat','same signed Z at both inner endpoints'))
    p = RecordProgram((Chunk(stim.Circuit('RX 0\nM 0'),('seed',)),
                       Repeat('outer',2,outer,(('outer_prev','seed','inner/2/m'),))))
    compact = p.lower(); unrolled = p.lower(compact=False)
    assert compact.circuit.flattened() == unrolled.circuit.flattened()
    assert compact.annotations == unrolled.annotations
    assert 'REPEAT 2' in str(compact.circuit) and 'REPEAT 3' in str(compact.circuit)
    assert compact.annotations[4]['parity']['ids'] == ['outer/1/inner/0/m','outer/0/inner/2/m']
    assert verify_deterministic(compact.circuit)['all_zero']
    assert compact.circuit.detector_error_model(allow_gauge_detectors=False).num_detectors == 8


def test_exact_signed_tracker_clifford_measurement_and_reset_oracle():
    # Exhaustive signed two-qubit conjugations against an exact independent
    # Stim Clifford tableau, including Y, both signs, CY and CZ phases.
    for gate, targets in [('H',[0]),('S',[1]),('S_DAG',[0]),('CX',[0,1]),
                           ('CY',[0,1]),('CZ',[0,1]),('SWAP',[0,1])]:
        circuit = stim.Circuit(); circuit.append(gate,targets); circuit.append('I',[1])
        tableau = stim.Tableau.from_circuit(circuit)
        for word in map(''.join,product('IXYZ',repeat=2)):
            for sign in ('+','-'):
                p = stim.PauliString(sign+word)
                tracker = SignedTracker(2); tracker.rows = [pauli_row(p)]
                tracker.gate(gate,targets)
                assert tracker.rows[0] == pauli_row(tableau(p))
    # Reset one half of entangled input: remaining half becomes mixed, rather
    # than acquiring a fictitious known sign from an unrecorded measurement.
    tracker = SignedTracker(2).run(stim.Circuit('H 0\nCX 0 1\nR 0\nM 1\nM 1\nDETECTOR rec[-1] rec[-2]'))
    assert tracker.measurements[0] != 0 and tracker.constraints == [0]
    with pytest.raises(ValueError,match='unsupported'):
        verify_deterministic(stim.Circuit('X_ERROR(0.1) 0'))


def test_D02_gross_memory_and_X1_strict_deterministic_harness(harnesses):
    _,_,hs = harnesses
    for key,h in hs.items():
        result = h.validate()
        assert result['strict_dem_observables'] == (24 if key == 'memory' else 23)
        assert result['exact_flows']['all_zero'] and not result['gauge_workaround']
        # Bounded noiseless oracle trajectories, not a noisy rate pilot.
        ds, os = h.circuit.compile_detector_sampler(seed=117).sample(4,separate_observables=True)
        assert not ds.any() and not os.any()
        assert 'MPP' not in {i.name for i in h.physical_body.flattened()}
        assert h.boundary_policy['profile'] == 'a7_single_block_independent_boundaries_v1'
        assert not h.to_dict()['paper_exact']


def test_D02_every_boundary_parity_has_saved_signed_justification(harnesses):
    code,df,hs = harnesses
    h = hs['frame']
    classes = {a['flow_class'] for a in h.annotations}
    assert {'merge','repeat','split','final_closure','logical_action'} <= classes
    assert all(a['justification'] and a['parity']['ids'] for a in h.annotations)
    assert len([a for a in h.annotations if a['name'].startswith('split/old:')]) == len(code.checks)
    for j,id in enumerate(code.check_ids):
        a = next(a for a in h.annotations if a['name'] == f'split/old:{id}')
        # Port-frame terms cancel between prediction and corrected raw readout;
        # the retained dependency still contains the measured Z dressing.
        for e,b in zip(df.graph.edge_ids,df.dressing[j]):
            assert (f'split/{e}' in a['parity']['ids']) == bool(b)
        assert any(i.startswith('deformed/2/') for i in a['parity']['ids'])
    assert hs['memory'].circuit.num_detectors == 4*len(code.checks)
    assert len(h.outcome_ids) == len(set(h.outcome_ids)) == h.circuit.num_measurements


def test_D02_truth_table_instrument_remains_separate_and_random(harnesses):
    from gross_design_bandle.circuits.protocol import build_physical_x1
    from gross_design_bandle.flows.observables import correlation
    from gross_design_bandle.surgery.ports import embed
    c,df,_ = harnesses
    protocol = build_physical_x1(df)
    instrument = TruthTableInstrument(protocol)
    refs = tuple(f'raw_ref:{i}' for i in range(c.k)); register = protocol.register+refs
    stabs = [to_stim_pauli(p,register) for p in c.checks]
    for i,(x,z) in enumerate(zip(c.logical_x,c.logical_z)):
        stabs += [to_stim_pauli(correlation(p,a,refs[i],register)) for p,a in ((x,'X'),(z,'Z'))]
    initial = stim.Tableau.from_stabilizers(stabs,allow_redundant=True,allow_underconstrained=True).to_circuit()
    tracker = SignedTracker(len(register)).run(initial + instrument.circuit)
    assert tracker.known(pauli_row(to_stim_pauli(c.logical_x[0],register))) != 0
    parity = 0
    for id in instrument.logical_outcome.ids:
        parity ^= tracker.measurements[protocol.outcomes().index(id)]
    assert parity != 0  # exact nonconstant affine outcome, without random sampling
    assert instrument.circuit.num_detectors == instrument.circuit.num_observables == 0


def test_D05_named_K24_K23_ranks_and_future_basis_adapters(harnesses):
    c,_,hs = harnesses
    for target in ('memory','X1','X1*X7','Y1'):
        basis = LogicalBasisAdapter.single_block(c,target)
        cert = basis.certificate(c)
        assert cert['rank'] == gf2.rank(np.array(cert['logical_coordinates'],dtype=np.uint8)) == (24 if target == 'memory' else 23)
        assert len(set(cert['names'])) == cert['rank']
        assert all(p.hermitian for p in basis.generators)
        if target == 'X1*X7':
            assert basis.x[0] == c.logical_x[0]*c.logical_x[6]
            assert basis.z[6] == c.logical_z[0]*c.logical_z[6]
        elif target == 'Y1':
            assert basis.x[0] == (c.logical_x[0]*c.logical_z[0]).with_phase(1)
    for key,h in hs.items():
        cert = h.logical_generators
        assert len(cert['physical_parities']) == cert['rank']
        assert [p['name'] for p in cert['physical_parities']] == cert['names']
    assert hs['frame'].logical_generators['physical_parities'][0]['parity']['ids'] == list(
        next(a['parity']['ids'] for a in hs['frame'].annotations if a['kind']=='observable' and a['observable_index']==0))


def assert_signature(circuit, location, x, z, path):
    expected = fault_signature(circuit,location,x,z)
    faulty = inject_fixed_fault(circuit,location,x,z)
    actual = tuple(a[0].astype(np.uint8) for a in faulty.compile_detector_sampler(seed=913).sample(1,separate_observables=True))
    if not all(np.array_equal(a,b) for a,b in zip(expected,actual)):
        path.write_text(json.dumps({'location':location,'x':x,'z':z,
            'expected':[a.tolist() for a in expected], 'actual':[a.tolist() for a in actual]}))
        pytest.fail(f'fault signature counterexample: {path}')
    return expected


def test_D03_small_Bell_negative_Y_exhaustive_joint_faults(tmp_path):
    p = Pauli.from_word('YY',('d0','d1'),-1)
    check = Check.bell('bell',p,('d0',))
    schedule = primitive_schedule(check)
    # Bell data has XX=ZZ=+1, hence -YY=+1. The physical negative YY
    # check includes both Bell readout halves and a real CY on each data half.
    c = stim.Circuit('R 0 1 2 3\nH 0\nCX 0 1')+schedule.to_stim()
    ids = schedule.outcomes; c.append('DETECTOR',[stim.target_rec(-1),stim.target_rec(-2)])
    c += mpp(p,schedule.register)
    c.append('OBSERVABLE_INCLUDE',[stim.target_rec(-1)],0)
    assert verify_deterministic(c)['all_zero']
    for location,op in enumerate(c.flattened()):
        if op.name not in ('CX','CY','CZ','R','RX','M','MX'):
            continue
        qubits = [t.value for t in op.targets_copy()]
        # Every nonidentity tensor Pauli on this gate's operands, including
        # jointly correlated two-qubit X/Z faults, after the physical operation.
        for word in product('IXYZ',repeat=len(qubits)):
            if set(word) == {'I'}:
                continue
            x = sum(1<<q for q,a in zip(qubits,word) if a in 'XY')
            z = sum(1<<q for q,a in zip(qubits,word) if a in 'ZY')
            assert_signature(c,location,x,z,tmp_path/'small_counterexample.json')


def physical_locations(h):
    count = 0; locations = []
    for i,op in enumerate(h.circuit.flattened()):
        ts = op.targets_copy()
        if op.name in ('R','RX','CX','CY','CZ','M','MX','MPP') and not any(t.is_measurement_record_target for t in ts):
            locations.append((i,count,op))
        count += stim.Circuit(str(op)).num_measurements
    return locations


def stratified_locations(h):
    locations = physical_locations(h)
    # All construction phases: ideal input, edge reset, merge and repeat gates,
    # split, noise-free original verification, old and logical ideal closure.
    ranges = [(0,0),(0,1),(1,161),(161,322),(322,483),(483,501),(501,645),(645,789),(789,812)]
    chosen = []
    for lo,hi in ranges:
        candidates = [item for item in locations if (item[1]==0 if lo==hi else lo <= item[1] < hi)]
        for gate in ('R','RX','CX','CZ','MX','M','MPP'):
            hits = [item for item in candidates if item[2].name==gate]
            if hits:
                chosen.append(hits[len(hits)//2])
    return list({i:(i,n,o) for i,n,o in chosen}.values())


def test_D04_active_split_and_tracked_frame_identical_fault_signatures(harnesses,tmp_path):
    _,_,hs = harnesses
    frame,active = hs['frame'], hs['active']
    active_locations = physical_locations(active)
    seen_phases = set()
    for i,n,op in stratified_locations(frame):
        # Match actual physical gate/record position, despite inserted active
        # feedforward and different annotation offsets. Both use the same body.
        matches = [j for j,k,o in active_locations if k==n and o==op]
        assert matches
        j = matches[0]
        t = next(t for t in op.targets_copy() if not t.is_combiner)
        q = t.value
        # Joint Y contains both X and Z. For a two-qubit gate add X on its
        # second operand to exercise correlated signatures as well.
        x = z = 1<<q
        if op.name in ('CX','CZ'):
            x ^= 1<<op.targets_copy()[1].value
        ef = assert_signature(frame.circuit,i,x,z,tmp_path/'frame_counterexample.json')
        ea = assert_signature(active.circuit,j,x,z,tmp_path/'active_counterexample.json')
        assert all(np.array_equal(a,b) for a,b in zip(ef,ea))
        seen_phases.add(n//161)
    assert {0,1,2,3,4} <= seen_phases
    assert any(i.name == 'CX' and any(t.is_measurement_record_target for t in i.targets_copy()) for i in active.physical_body.flattened())


def test_D04_Y_frame_and_Bell_XOR_signed_flows():
    # Random split-like bit controls Y, which anticommutes with X. Software
    # frame normalization is compared with physical CY feedforward.
    frame = stim.Circuit('RX 0\nZ 0\nRX 1\nCY 1 0\nM 1\nMX 0\nMPAD 1\nDETECTOR rec[-1] rec[-2] rec[-3]')
    active = stim.Circuit('RX 0\nZ 0\nRX 1\nCY 1 0\nM 1\nCY rec[-1] 0\nMX 0\nMPAD 1\nDETECTOR rec[-1] rec[-2]')
    assert verify_deterministic(frame)['all_zero'] and verify_deterministic(active)['all_zero']
    for gate in ('X','Y','Z'):
        x,z = int(gate in 'XY')<<1,int(gate in 'ZY')<<1
        a = fault_signature(frame,2,x,z); b = fault_signature(active,2,x,z)
        assert all(np.array_equal(c,d) for c,d in zip(a,b))
    c = Check.bell('negative_Y',Pauli.from_word('YZ',('d0','d1'),-1),('d0',))
    s = primitive_schedule(c)
    program = RecordProgram(); program.chunk(mpp(c.pauli,s.register),('initial',)); program.chunk(s.to_stim(),s.outcomes)
    program.mark('Bell_XOR','detector',Parity(('initial',)+s.outcomes),'repeat','signed joint Bell parity equals initial signed YZ')
    lowered = program.lower()
    assert verify_deterministic(lowered.circuit)['all_zero']
    assert lowered.circuit.detector_error_model(allow_gauge_detectors=False).num_detectors == 1


def test_negative_record_offset_corruption_fails_exact_flow_and_strict_DEM(harnesses):
    _,_,hs = harnesses
    h = hs['frame']; circuit = stim.Circuit(); detector_index = 0; changed = False
    det_names = [a['name'] for a in h.annotations if a['kind']=='detector']
    for op in h.circuit.flattened():
        if op.name == 'DETECTOR':
            name = det_names[detector_index]; detector_index += 1
            if not changed and name.startswith('deformed/1/vertex:'):
                ts = op.targets_copy(); ts[-1] = stim.target_rec(ts[-1].value-1)
                circuit.append('DETECTOR',ts); changed = True; continue
        circuit.append(op)
    assert changed
    with pytest.raises(ValueError,match='nonzero signed flow'):
        verify_deterministic(circuit)
    with pytest.raises(ValueError,match='non-deterministic detectors'):
        circuit.detector_error_model(allow_gauge_detectors=False)


def test_negative_missing_unknown_duplicate_records_and_unresolved_profiles(harnesses):
    c,df,_ = harnesses
    with pytest.raises(ValueError,match='count'):
        Chunk(stim.Circuit('M 0'),())
    p = RecordProgram(); p.mark('bad','detector',Parity(('future',)),'merge','bad future boundary')
    with pytest.raises(ValueError,match='future'):
        p.lower()
    p = RecordProgram(); p.chunk(stim.Circuit('M 0 1'),('duplicate','duplicate'))
    with pytest.raises(ValueError,match='duplicate'):
        p.lower()
    with pytest.raises(ValueError,match='positive'):
        Repeat('bad',0,())
    with pytest.raises(ValueError,match='history'):
        verify_deterministic(stim.Circuit('M 0\nDETECTOR rec[-2]'))
    with pytest.raises(ValueError,match='O1'):
        LogicalBasisAdapter.single_block(c,'published_inter_K23')
    for operation in ('Y1','X1*X7','inter_XX'):
        with pytest.raises(ValueError,match='scope'):
            build_benchmark(c,operation=operation,deformation=df)
    with pytest.raises(ValueError,match='positive'):
        build_benchmark(c,rounds=True)
    with pytest.raises(ValueError,match='same block'):
        build_benchmark(c,operation='X1')
    with pytest.raises(ValueError,match='nonzero signed flow'):
        verify_deterministic(stim.Circuit('RX 0\nZ 0\nMX 0\nDETECTOR rec[-1]'))


def test_negative_omitted_frame_Bell_half_and_terminal_sign(harnesses):
    _,_,hs = harnesses
    h = hs['frame']
    # Remove all software-frame contributions from one final Z generator.
    a = next(a for a in h.annotations if a['kind']=='observable' and a['observable_index']>=12
             and any(i.startswith('split/') for i in a['parity']['ids']))
    bad = stim.Circuit()
    for op in h.circuit.flattened():
        if op.name=='OBSERVABLE_INCLUDE' and int(op.gate_args_copy()[0])==a['observable_index']:
            final = [t for t in op.targets_copy() if h.outcome_ids[len(h.outcome_ids)+t.value].startswith('logical_terminal/')]
            bad.append(op.name,final,op.gate_args_copy())
        else:
            bad.append(op)
    with pytest.raises(ValueError,match='nonzero signed flow'):
        verify_deterministic(bad)
    with pytest.raises(ValueError,match='non-deterministic observables'):
        bad.detector_error_model(allow_gauge_detectors=False)
    check = Check.bell('negative_Y',Pauli.from_word('YZ',('d0','d1'),-1),('d0',))
    s = primitive_schedule(check)
    program = RecordProgram(); program.chunk(mpp(check.pauli,s.register),('initial',)); program.chunk(s.to_stim(),s.outcomes)
    program.mark('missing_half','detector',Parity(('initial',s.outcomes[0])),'repeat','deliberately wrong Bell parity')
    with pytest.raises(ValueError,match='nonzero signed flow'):
        verify_deterministic(program.lower().circuit)
    with pytest.raises(ValueError,match='nonzero signed flow'):
        verify_deterministic(stim.Circuit('RX 0\nMX !0\nDETECTOR rec[-1]'))
    missing = stim.Circuit()
    for op in h.circuit.flattened():
        if op.name != 'OBSERVABLE_INCLUDE' or int(op.gate_args_copy()[0]) != 5:
            missing.append(op)
    with pytest.raises(ValueError,match='named observable coverage'):
        replace(h,circuit=missing).validate()


def test_D05_physical_parities_realize_complete_named_logical_action(harnesses,tmp_path):
    from gross_design_bandle.flows.boundaries import input_boundary
    c,_,hs = harnesses
    for name in ('memory','frame'):
        h = hs[name]
        basis = LogicalBasisAdapter.single_block(c,'memory' if name=='memory' else 'X1')
        physical_register = h.register[:-len(h.boundary_policy['ideal_reference_qubits'])]
        initial,_,_ = input_boundary(c,basis,physical_register)
        boundary = len(list(initial.flattened()))-1
        actions = []
        for p in c.logical_x+c.logical_z:
            x = sum(b<<q for q,b in enumerate(p.x)); z = sum(b<<q for q,b in enumerate(p.z))
            d,l = assert_signature(h.circuit,boundary,x,z,tmp_path/'logical_action_counterexample.json')
            expected = np.array([p.symplectic(g) for g in basis.generators],dtype=np.uint8)
            assert not d.any()  # encoded input logical Pauli has no syndrome
            np.testing.assert_array_equal(l,expected)
            actions.append(l)
        assert gf2.rank(np.array(actions,dtype=np.uint8)) == h.logical_generators['rank']
