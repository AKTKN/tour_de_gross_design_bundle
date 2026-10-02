"""Phase10: shared generators on frozen two-gross, no rates/distance claims.

Unchanged tiny gate/Bell exhaustive oracles remain in earlier test modules.
Large C17/C18 flows use strict Stim plus raw signs; faults use bounded strata.
"""
from dataclasses import replace
from time import perf_counter
import csv
import json
from pathlib import Path
import numpy as np
import pytest
import stim
from gross_design_bandle.algebra import gf2
from gross_design_bandle.algebra.pauli import Pauli
from gross_design_bandle.bench.two_gross import PROFILES, profile_named, build_two_gross
from gross_design_bandle.codes.blocks import CodeBlocks
from gross_design_bandle.codes.reference_profiles import load_reference_code
from gross_design_bandle.circuits.shift import transfer_plan, two_cnot_ops, PROFILE, TWO_GROSS_PROFILE
from gross_design_bandle.circuits.schedule import validate
from gross_design_bandle.flows.boundaries import mpp
from gross_design_bandle.flows.harness import build_benchmark
from gross_design_bandle.flows.observables import LogicalBasisAdapter, correlation
from gross_design_bandle.flows.signatures import fault_signature, inject_fixed_fault
from gross_design_bandle.flows.stabilizer_flows import verify_deterministic_stim
from gross_design_bandle.lpu.reference import build_half_graph
from gross_design_bandle.surgery.deformation import compile_deformation
from gross_design_bandle.surgery.ports import embed, product
from gross_design_bandle.surgery.protocol import to_stim_pauli
from gross_design_bandle.validation.physical import check_schedule_tableaus
from gross_design_bandle.validation.connectivity import installed_connectivity
from gross_design_bandle.lpu.code_code_adapter import adapter_connectivity
from gross_design_bandle.validation.phenomenological import prepare_phenomenological_jobs
from gross_design_bandle.noise import NoiseProfile, build_fault_model, emit_noise
from gross_design_bandle.noise.locations import Location
from gross_design_bandle.validation.faults import validate_faults
from gross_design_bandle.noise.cache import key_for
from gross_design_bandle.bench.artifacts import file_hash

NAMES = tuple(p.name for p in PROFILES)
SURGERIES = NAMES[2:]


def test_fault_audit_revalidation_contract_and_corrupt_raw_oracle(tmp_path):
    circuit = stim.Circuit('R 0\nI 0\nM 0\nDETECTOR rec[-1]')
    locations = (Location('idle',1,'idle',(0,),'I','toy',1,0,'BB_data'),)
    model = build_fault_model(circuit,locations,NoiseProfile('a7_uniform_expanded',.001),
        admission_policy='include_all',grouping_policy='joint_signature_xor',cache_dir=False)
    result = validate_faults(model,exhaustive=True,counterexample_path=tmp_path/'counterexample.json',
                             validate_model=False)
    assert result['all_agree'] and result['checked_raw_primitives']==3
    assert result['full_model_revalidated'] is False
    for flag in (1,None):
        with pytest.raises(ValueError,match='boolean'):
            validate_faults(model,exhaustive=True,counterexample_path=tmp_path/'counterexample.json',validate_model=flag)
    corrupt = list(model.raw_signatures); corrupt[0] ^= 1
    with pytest.raises(ValueError,match='counterexample'):
        validate_faults(replace(model,raw_signatures=tuple(corrupt)),exhaustive=True,
                        counterexample_path=tmp_path/'counterexample.json',validate_model=False)
    assert (tmp_path/'counterexample.json').stat().st_size>0


@pytest.fixture(scope='module')
def constructions():
    # Lazily share changed geometry/harnesses; no test-pass caching.
    items = {}
    def get(name):
        if name not in items:
            items[name] = build_two_gross(name)
        return items[name]
    return get


@pytest.fixture(scope='module')
def models(constructions):
    items = {}
    def get(name):
        if name not in items:
            # Native numerical cache retains work across tests/processes;
            # release large Python catalogues when advancing to a new profile.
            items.clear()
            c = constructions(name); t = perf_counter()
            locations, policy = c.locations()
            construction_seconds = perf_counter()-t; t = perf_counter()
            model = build_fault_model(c.harness.circuit, locations, NoiseProfile('a7_uniform_expanded', .001),
                admission_policy='include_all', grouping_policy='joint_signature_xor')
            items[name] = model, policy, {'locations_seconds': construction_seconds,
                                       'model_seconds': perf_counter()-t}
        return items[name]
    return get


def test_negative_profiles_blocks_and_paper_claims():
    for name in ('two_gross_inter_XX', 'paper_exact', 'two_gross_Y_C17_extension'):
        with pytest.raises(ValueError, match='unknown'): profile_named(name)
    for ids in (('same', 'same'), ('only_one',)):
        with pytest.raises(ValueError, match='distinct'):
            build_two_gross(SURGERIES[-1], block_ids=ids)
    with pytest.raises(ValueError, match='inter only'):
        build_two_gross('two_gross_shift', observable_profile='published_inter_K23')
    with pytest.raises(ValueError, match='split mode'):
        build_two_gross('two_gross_idle', split_mode='active')
    code = load_reference_code('two_gross', 'negative')
    with pytest.raises(ValueError, match='same reference'):
        CodeBlocks((code, load_reference_code('gross', 'other')))
    with pytest.raises(ValueError, match='O3'): transfer_plan(code, profile=PROFILE)
    with pytest.raises(ValueError, match='O3'): transfer_plan(code, profile='paper_exact')
    for value in (True, float('nan'), -1, 1.1):
        with pytest.raises(ValueError): PROFILES[0].report_rate(value)


def test_extension_labels_and_normalization(constructions):
    for p in PROFILES:
        metadata = p.to_dict()
        assert metadata['circuit_distance'] is None and metadata['open_items'] == ['O1','O2','O3','O4','O5']
        if p.operation in ('memory', 'shift'):
            assert p.rounds == 18 and p.divisor == 18
            assert metadata['Figure15_series'] == p.name
            assert p.report_rate(.036) == pytest.approx(.002)
        else:
            assert metadata['classification'] == 'extension' and metadata['Figure15_series'] is None
            assert p.divisor == 1 and p.report_rate(.036) == .036
    assert [p.rounds for p in PROFILES if p.blocks == 2] == [17, 18]
    assert all(p.rounds == 18 for p in PROFILES if p.blocks == 1)
    c = constructions(SURGERIES[-1])
    with pytest.raises(ValueError, match='O1'):
        build_benchmark(c.codes, operation='inter_XX', deformation=c.deformation,
                        observable_profile='published_inter_K23')


def test_two_gross_signed_algebra_and_reduced_reference_cycles(constructions):
    code = constructions(SURGERIES[0]).codes[0]
    assert gf2.rank(code.hx) == gf2.rank(code.hz) == 138
    assert not gf2.matmul(code.hx, code.hz.T).any()
    np.testing.assert_array_equal(gf2.matmul(code.lx, code.lz.T), np.eye(12, dtype=np.uint8))
    for p in (code.logical_x[0], code.logical_x[6], code.logical_z[0], code.logical_z[6]):
        assert sum(x|z for x,z in zip(p.x,p.z)) == 20
    for half in ('l', 'r'):
        graph = build_half_graph(code, half)
        assert (len(graph.vertices), len(graph.edges)) == (20, 32)
        assert sum(':expansion:' in e.id for e in graph.edges) == 2
    for name in SURGERIES:
        df = constructions(name).deformation
        assert df.fixed_input['rank'] == 1 and df.merged_k == (23 if len(df.lpu.codes)==2 else 11)
        assert product(df.lpu.ports.ports, df.lpu.ports.target.qubit_ids) == df.lpu.ports.target
        for cycle, witness in zip(df.omitted_cycles, df.omitted_witnesses):
            expected = Pauli(0, (0,)*len(df.group.register),
                (0,)*len(df.lpu.ports.target.qubit_ids)+tuple(cycle), df.group.register)
            assert product((p for p,b in zip(df.group.generators,witness) if b), df.group.register) == expected
        if df.lpu.operation in ('XX', 'Y'):
            assert (len(df.graph.vertices),len(df.graph.edges),len(df.graph.cycles)) == (39,81,37)
            assert sum(':bridge:' in e.id for e in df.graph.edges) == 17
            assert df.lpu.installed_full_census['total'] == 158
        if df.lpu.operation == 'inter_XX':
            assert (len(df.graph.vertices),len(df.graph.edges),len(df.graph.cycles)) == (57,98,38)
            assert not any('triangle' in id for id in df.group.ids)
    df = constructions('two_gross_Y_C18_extension').deformation
    assert df.lpu.ports.target == (code.logical_x[0]*code.logical_z[0]).with_phase(1)
    damaged = replace(df.graph, cycles=tuple(c for c in df.graph.cycles if ':bridge:' not in c.id))
    with pytest.raises(ValueError, match='unjustified cycle omission'): compile_deformation(df.lpu, graph=damaged)
    shared = df.graph.vertices.index(df.graph.shared_vertex); ports = list(df.lpu.ports.ports)
    ports[shared] = ports[shared].with_phase(3)
    with pytest.raises(ValueError, match='imaginary-phase'): replace(df.lpu.ports, ports=tuple(ports))


@pytest.mark.parametrize('name', SURGERIES)
def test_two_gross_complete_signed_instrument(constructions, name):
    c = constructions(name); p = c.physical
    code = CodeBlocks(c.codes) if len(c.codes)==2 else c.codes[0]
    basis = LogicalBasisAdapter.two_blocks(code) if len(c.codes)==2 else LogicalBasisAdapter.single_block(code,c.profile.operation)
    refs = tuple(f'choi:{i}' for i in range(code.k)); register = p.register+refs
    assert p.rounds == c.profile.rounds
    circuit = p.to_stim()
    assert not {'MPP','DETECTOR','OBSERVABLE_INCLUDE'} & {op.name for op in circuit.flattened()}
    for mode in ('plus','minus','choi'):
        checks = [to_stim_pauli(s,register) for s in code.checks]; witnesses = list(checks)
        for i,(x,z) in enumerate(zip(basis.x,basis.z)):
            pair = ((x.with_phase(2*int(mode=='minus')), Pauli.from_word('X',(refs[i],)))
                    if i==0 and mode!='choi' else
                    tuple(correlation(q,a,refs[i],register) for q,a in ((x,'X'),(z,'Z'))))
            checks.extend(to_stim_pauli(q,register) for q in pair)
            if i or mode!='choi': witnesses.extend(to_stim_pauli(q,register) for q in pair)
        initial = stim.TableauSimulator(seed=0)
        initial.do(stim.Tableau.from_stabilizers(checks,allow_redundant=True,allow_underconstrained=True).to_circuit())
        actual = initial.copy(); actual.do(circuit)
        outcomes = dict(zip(p.outcomes(),map(int,actual.current_measurement_record())))
        bit = p.logical_outcome.evaluate(outcomes)
        if mode!='choi': assert bit == int(mode=='minus')
        else: assert initial.peek_observable_expectation(to_stim_pauli(basis.x[0],register)) == 0
        _,frame = p.frame.evaluate(outcomes); actual.do_pauli_string(to_stim_pauli(frame,register))
        expected = initial.copy(); expected.postselect_observable(to_stim_pauli(basis.x[0],register),desired_value=bool(bit))
        group = witnesses+[to_stim_pauli(basis.x[0].with_phase(2*bit),register)]
        if mode=='choi': group.append(to_stim_pauli(Pauli.from_word('X',(refs[0],),(-1)**bit),register))
        assert gf2.rank(np.array([[int(a in (1,2)) for a in q]+[int(a in (2,3)) for a in q] for q in group],dtype=np.uint8)) == len(code.qubit_ids)+code.k
        for q in group: assert expected.peek_observable_expectation(q) == actual.peek_observable_expectation(q) == 1
        for id,s in zip(code.check_ids,code.checks):
            assert outcomes[f'memory/0/{id}/0'] == frame.symplectic(s)
        if mode=='plus' and c.profile.operation in ('X1*X7','inter_XX','Y1'):
            # Material negative: measuring separate factors destroys coherence.
            factors = (code.logical_x[0],code.logical_x[6]) if c.profile.operation=='X1*X7' else (
                (code.logical_x[0],code.logical_x[12]) if c.profile.operation=='inter_XX' else
                (code.logical_x[0],code.logical_z[0]))
            bad = initial.copy()
            for factor in factors: bad.do(mpp(factor,register))
            retained = 6 if c.profile.operation=='X1*X7' else 12 if c.profile.operation=='inter_XX' else 0
            witness = (correlation(basis.z[retained],'Z',refs[retained],register) if retained else basis.x[0])
            assert initial.peek_observable_expectation(to_stim_pauli(witness,register)) == 1
            assert bad.peek_observable_expectation(to_stim_pauli(witness,register)) == 0


def test_two_gross_shift_arbitrary_physical_Choi(constructions):
    c = constructions('two_gross_shift'); code = c.codes[0]; plan = c.physical.plan
    assert plan.profile == TWO_GROSS_PROFILE and plan.validate(code)['Tanner_edges']==2*code.spec.n
    n = code.spec.n; ref0 = len(plan.register)
    initial = stim.Circuit(); initial.append('R',range(ref0+n)); initial.append('H',range(n))
    initial.append('CX',[q for i in range(n) for q in (i,ref0+i)])
    initial.append('S',range(0,n,3)); initial.append('Z',range(0,n,7))
    destination = {a:int(i%3==0) for i,a in enumerate(plan.register[n:])}
    initial.append('X',[plan.register.index(a) for a,b in destination.items() if b])
    sim = stim.TableauSimulator(); sim.do(initial)
    tableau = sim.current_inverse_tableau().inverse()
    generators = [tableau.z_output(q) for q in list(range(n))+list(range(ref0,ref0+n))]
    for stage,pairs in enumerate((plan.first,plan.second)):
        for op in two_cnot_ops(pairs,0,phase='oracle'):
            sim.do(stim.Circuit('CX '+' '.join(str(plan.register.index(q)) for q in op.qubits)))
        if stage==0: sim.x(0)
        for source,dest in pairs: sim.measure(plan.register.index(source))
    records = sim.current_measurement_record()
    for (source,check),(_,dest) in zip(plan.first,plan.second):
        q = plan.data.index(dest)
        if destination[check]^records[q]: sim.x(q)
    permutation = plan.target_to_source+tuple(range(n,ref0+n))
    for p in generators:
        expected = stim.PauliString([p[q] for q in permutation]); expected.sign = p.sign
        assert sim.peek_observable_expectation(expected)==1
    with pytest.raises(ValueError,match='permutation'):
        replace(plan,target_to_source=tuple(range(n))).validate(code)


@pytest.mark.parametrize('name', NAMES)
def test_two_gross_schedule_and_physical_readout(constructions, name):
    c = constructions(name); p = c.physical
    if c.profile.operation == 'shift':
        assert p.validate()['instruction_ticks']==14 and p.duration==253
        assert c.harness.physical_body.num_ticks==253
        for r in range(18):
            ops = [o for o in p.ops if o.round==r and o.phase.startswith('transfer_')]
            assert sum(o.gate=='CX' for o in ops)==4*c.codes[0].spec.n
            assert sum(o.gate=='M' for o in ops)==2*c.codes[0].spec.n
    else:
        s = p if c.profile.operation=='memory' else p.cycle
        assert validate(s)['collision_free'] and validate(s)['eq67_overlap_pairs']>0
        # Each changed physical signed check, composite schedule oracle.
        one = replace(s, ops=tuple(o for o in s.ops if o.round==0))
        readouts = check_schedule_tableaus(one)
        assert {r['check_id'] for r in readouts} == {check.id for check in one.checks}
        assert all(r['signed_readout_matches'] and r['nondemolition'] for r in readouts)
        if c.profile.operation=='memory': assert s.duration==145
        else:
            bells = [check for check in s.checks if check.kind=='bell']
            for check in bells:
                assert len(s.readouts()[f'{check.id}/0'])==2
            if len(c.codes)==2:
                census = adapter_connectivity(p)
                assert all(len(qs)==17 for qs in census['bridge_data_by_module'].values())
                assert len(census['cross_module_checks'])==33
                assert census['maximum_installed_degree']<=7
                assert census['installed_qubits']==2*(288+288+158)+34
            elif c.profile.operation in ('X1*X7','Y1'):
                assert len(p.register)==288+288+158
                assert installed_connectivity(c.codes[0])['maximum_degree']<=7
            # Negative: Bell readout cannot survive lost preparation.
            if bells:
                check = bells[0]
                missing = replace(s,ops=tuple(o for o in s.ops if not(o.check_id==check.id and o.phase=='bell_prepare')))
                with pytest.raises(ValueError,match='Bell preparation'): validate(missing)


@pytest.mark.parametrize('name', NAMES)
def test_two_gross_C18_C17_strict_flows_and_named_rows(constructions, name):
    c = constructions(name); h = c.harness
    K = 47 if len(c.codes)==2 else 24 if c.deformation is None else 23
    cert = h.validate(flow_oracle='stim_reference')
    assert cert['exact_flows']['all_zero'] and cert['strict_dem_observables']==K
    assert h.logical_generators['rank']==K and len(set(h.logical_generators['names']))==K
    assert h.boundary_policy['benchmark_profile']==c.profile.to_dict()
    assert 'MPP' not in {op.name for op in h.physical_body.flattened()}
    if c.deformation is not None:
        active = build_benchmark(c.codes if len(c.codes)==2 else c.codes[0], operation=c.profile.operation,
            rounds=c.profile.rounds, deformation=c.deformation, split_mode='active')
        assert active.validate()['exact_flows']['all_zero']
    # Rebind one known-zero boundary record to a known-one raw record. The
    # independent raw-sign oracle must reject even when a DEM has no gauge.
    bad = stim.Circuit(); changed = False
    for op in h.circuit.flattened():
        if op.name=='DETECTOR' and not changed:
            bad.append('MPAD', [1])
            ts = [stim.target_rec(-1)]+[stim.target_rec(t.value-1) for t in op.targets_copy()[1:]]
            bad.append('DETECTOR',ts); changed = True
        else: bad.append(op)
    assert changed
    with pytest.raises(ValueError): verify_deterministic_stim(bad)


@pytest.mark.parametrize('name', NAMES)
def test_two_gross_joint_fault_strata_and_catalogue(constructions, models, name, tmp_path):
    c = constructions(name); m,policy,timing = models(name)
    audit = validate_faults(m, exhaustive=False, counterexample_path=tmp_path/'counterexample.json',
                            validate_model=False)
    # Save numerical oracle observations, never a pytest result or a reason to
    # skip checks on a later run. The final exporter verifies their provenance.
    root = Path(__file__).resolve().parents[1]
    audit_dir = root/'evidence/phase10/fault_checks'; audit_dir.mkdir(parents=True,exist_ok=True)
    sources = ('validation/faults.py','flows/signatures.py','noise/signatures.py','noise/locations.py')
    (audit_dir/(name+'.json')).write_text(json.dumps({
        'profile':c.profile.to_dict(),
        'model_key':key_for(m.circuit,m.locations,artifact='fault_model',profile=m.profile.name,
                            admission=m.admission_policy,grouping=m.grouping_policy),
        'source_sha256':{p:file_hash(root/'src/gross_design_bandle'/p) for p in sources},
        'audit':audit},indent=2)+'\n')
    assert audit['all_agree'] and audit['word_policy']=='representative'
    anchors = {0,c.profile.rounds//2,c.profile.rounds-1}
    expected = {(l.phase,l.gate,l.role,l.round) for l in m.locations if l.round in anchors}
    assert {(t['location']['phase'],t['location']['gate'],t['location']['role'],t['location']['round']) for t in audit['trials']} == expected
    assert {'IX','ZI','XX','YZ'} <= {t['pauli_word'] for t in audit['trials']}
    assert m.H.shape[1]==m.Lambda.shape[1]==m.N==len(m.admitted_to_copy)
    assert m.admission_mask.all() and set(r['copies'] for r in m.raw)=={1,5,15}
    assert m.Lambda.shape[0]==c.harness.logical_generators['rank']
    if c.profile.operation=='shift':
        readout = [s for r,s in zip(m.raw,m.raw_signatures) if
            (l:=m.locations[r['location_index']]).phase=='transfer_1' and l.kind=='readout']
        assert len(readout)==18*288 and all(s and not(s>>m.H.shape[0]) for s in readout)
        assert {'transfer_1','transfer_2','following_syndrome'} <= {l.phase for l in m.locations}
    noisy = emit_noise(m.circuit,m.locations,m.profile)
    dem = noisy.detector_error_model(allow_gauge_detectors=False, approximate_disjoint_errors=False)
    assert dem.num_observables==m.Lambda.shape[0] and dem.num_detectors==m.H.shape[0]
    if c.profile.published_series:
        table = Path(__file__).resolve().parents[1]/'reference/table6.csv'
        row = next(r for r in csv.DictReader(table.open()) if r['series']==name)
        report = m.discrepancy(int(row['N_expanded']),policy)
        assert report['delta_admitted_minus_published']==m.N-int(row['N_expanded'])
    else:
        # Representative changed Bell/Y/split signatures in both conventions.
        active = build_benchmark(c.codes if len(c.codes)==2 else c.codes[0],operation=c.profile.operation,
            rounds=c.profile.rounds,deformation=c.deformation,split_mode='active')
        chosen = {}
        for trial in audit['trials']:
            l = m.locations[m.raw[trial['raw_index']]['location_index']]
            if l.gate=='CY' or 'Bell' in l.role or l.phase=='split':
                chosen.setdefault((l.phase,l.gate,l.role),trial['raw_index'])
        assert chosen
        for j in chosen.values():
            raw = m.raw[j]; l = m.locations[raw['location_index']]
            expected = fault_signature(m.circuit,l.after_instruction,raw['x'],raw['z'])
            actual = fault_signature(active.circuit,l.after_instruction,raw['x'],raw['z'])
            assert all(np.array_equal(a,b) for a,b in zip(expected,actual))
            ds,ls = inject_fixed_fault(active.circuit,l.after_instruction,raw['x'],raw['z']).compile_detector_sampler(seed=0).sample(1,separate_observables=True)
            np.testing.assert_array_equal(ds[0],actual[0]); np.testing.assert_array_equal(ls[0],actual[1])


def test_bounded_A8_jobs_and_independent_witness_checks(constructions):
    for name in (SURGERIES[0],SURGERIES[1],SURGERIES[2],SURGERIES[3]):
        c = constructions(name); df = c.deformation; jobs = prepare_phenomenological_jobs(df)
        metadata = jobs.manifest()
        assert len(jobs.spatial_q)==2*df.merged_k and len(jobs.temporal_q)==1
        assert metadata['budget']['aggregate_wall_seconds']==120 and metadata['status']=='prepared_not_launched'
        assert not any(id.startswith('vertex:') for id in jobs.temporal_ids)
        assert len(jobs.temporal_ids)==len(df.group.ids)-len(df.graph.vertices)
        # Temporal anticommuting input Z1 commutes with every nonvertex check.
        candidate = embed(c.codes[0].logical_z[0],df.group.register)
        temporal = jobs.check_witness('temporal',0,candidate.x+candidate.z)
        assert temporal['verified'] and temporal['weight']==20
        # The complete quotient has a partner anticommuting with q_0.
        n = len(jobs.register); q = jobs.spatial_q[0]
        partner = next(p for p in jobs.spatial_q if (int(p[:n]@q[n:])+int(p[n:]@q[:n]))%2)
        assert jobs.check_witness('spatial',0,partner)['verified']
        with pytest.raises(ValueError,match='anticommutation'):
            jobs.check_witness('temporal',0,[0]*(2*n))
        with pytest.raises(ValueError,match='binary'):
            jobs.check_witness('spatial',0,[2]*(2*n))
        with pytest.raises(ValueError,match='register'):
            jobs.check_witness('temporal',0,[0])
        unit = np.zeros(2*n,dtype=np.uint8)
        column = next(i for i in range(2*n) if jobs.temporal_M[:,(i+n)%(2*n)].any())
        unit[column] = 1
        with pytest.raises(ValueError,match='commutation'):
            jobs.check_witness('temporal',0,unit)
        assert metadata['lower_bound'] is None and metadata['circuit_distance_search'] is False
    # OR weight: a Y contributes one site, independently of solver inputs.
    toy = replace(jobs, register=('q',), spatial_M=np.zeros((0,2),dtype=np.uint8),
                  spatial_q=np.array([[1,0]],dtype=np.uint8))
    assert toy.check_witness('spatial',0,[1,1])['weight']==1
