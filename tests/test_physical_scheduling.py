"""Phase04 oracles: literal signed Paulis, dense Choi branches and PDF layers."""
from dataclasses import replace
from itertools import product
from pathlib import Path
import hashlib
import numpy as np
import pytest
import stim
from gross_design_bandle.algebra.pauli import Pauli
from gross_design_bandle.codes.reference_profiles import load_reference_code
from gross_design_bandle.lpu.reference import build_reference_lpu
from gross_design_bandle.surgery.deformation import compile_deformation
from gross_design_bandle.surgery.protocol import to_stim_pauli,build_ideal_protocol
from gross_design_bandle.circuits.checks import Check,support
from gross_design_bandle.circuits.primitive import primitive_schedule
from gross_design_bandle.circuits.schedule import Schedule,Op,validate,collision_check,bipartite_layers
from gross_design_bandle.circuits.memory import memory_schedule
from gross_design_bandle.circuits.surgery import staged_schedule
from gross_design_bandle.circuits.protocol import build_physical_x1
from gross_design_bandle.integrations.sliding_window import extract_layers,adapted_edges,DONOR_SHA256
from gross_design_bandle.validation.physical import check_tableau
from gross_design_bandle.validation.connectivity import installed_connectivity


@pytest.fixture(scope='module')
def gross():
    code=load_reference_code('gross','physical')
    df=compile_deformation(build_reference_lpu(code,'X'))
    cycle,metadata=staged_schedule(df)
    return code,df,cycle,metadata


def test_C01_signed_single_and_bell_tableau_oracles():
    for word in map(''.join,product('IXYZ',repeat=2)):
        for sign in (-1,1):
            p=Pauli.from_word(word,('d0','d1'),sign)
            for c in (Check.single('s',p),Check.bell('b',p,('d0',) if word[0]!='I' else ())):
                s=primitive_schedule(c)
                validate(s)
                assert check_tableau(s,c)['signed_readout_matches']
                # Literal independent Pauli conversion includes negative Y.
                assert to_stim_pauli(p)==stim.PauliString(('+' if sign==1 else '-')+word)
    for word in ('II','ZI','IZ','ZZ'):
        p=Pauli.from_word(word,('d0','d1'),-1)
        c=Check.single('z',p,basis='Z')
        assert check_tableau(primitive_schedule(c),c)['nondemolition']


def reduced_density(sim,keep):
    n=sim.num_qubits
    # Stim little endian -> numpy tensor axes q0,q1,... after reshape+reverse.
    psi=sim.state_vector(endian='little').reshape((2,)*n).transpose(tuple(reversed(range(n))))
    rest=tuple(i for i in range(n) if i not in keep)
    matrix=psi.transpose(tuple(keep)+rest).reshape(2**len(keep),-1)
    return matrix@matrix.conj().T


def test_bell_all_branches_dense_choi_projector():
    # Every branch on an input maximally entangled with TWO reference qubits.
    # A wrong Bell parity or independently measured halves destroys coherence.
    matrices={'I':np.eye(2),'X':np.array([[0,1],[1,0]]),
              'Y':np.array([[0,-1j],[1j,0]]),'Z':np.diag([1,-1])}
    for word,sign in (('YZ',-1),('XX',1),('ZY',1)):
        c=Check.bell('bell',Pauli.from_word(word,('d0','d1'),sign),('d0',))
        s=primitive_schedule(c)
        p=sign*np.kron(matrices[word[0]],matrices[word[1]])
        choi=np.eye(4).reshape(-1)/2
        accum=[np.zeros((16,16),complex),np.zeros((16,16),complex)]
        for bits in product((0,1),repeat=2):
            sim=stim.TableauSimulator()
            sim.set_num_qubits(6)
            sim.h(0);sim.cx(0,4);sim.h(1);sim.cx(1,5)
            probability=1.
            cursor=0
            for op in s.ordered_ops():
                qs=[s.register.index(q) for q in op.qubits]
                if op.gate=='MX':
                    raw=bits[cursor]^int(op.invert)
                    expect=sim.peek_x(qs[0])
                    if expect==0:
                        probability*=.5
                    elif expect!=(-1)**raw:
                        probability=0.;break
                    sim.postselect_x(qs[0],desired_value=bool(raw));cursor+=1
                else:
                    circuit=stim.Circuit();circuit.append(op.gate,qs);sim.do(circuit)
            assert probability==.25
            rho=reduced_density(sim,(0,1,4,5))
            projected=np.kron((np.eye(4)+(-1)**sum(bits)*p)/2,np.eye(4))@choi
            expected=np.outer(projected,projected.conj())
            np.testing.assert_allclose(probability*rho,expected/2,atol=1e-7)
            accum[sum(bits)%2]+=probability*rho
        for m in (0,1):
            projected=np.kron((np.eye(4)+(-1)**m*p)/2,np.eye(4))@choi
            np.testing.assert_allclose(accum[m],np.outer(projected,projected.conj()),atol=1e-7)
        assert len(s.readouts()['bell/0'])==2


def test_C01_gross_all_physical_checks_and_collision_free(gross):
    _,df,s,_=gross
    assert validate(s)['collision_free']
    assert len(s.checks)==len(df.group.generators)==161
    for check in s.checks:
        assert check_tableau(s,check)['signed_readout_matches']
        assert check_tableau(s,check,composite=True)['signed_readout_matches']
    assert 'MPP' not in str(s.to_stim())
    assert s.to_stim().num_measurements==161
    assert {c.id for c in s.checks}==set(df.group.ids)


def test_C02_every_overlap_and_full_surgery_constraints(gross):
    code,_,s,_=gross
    assert validate(s)['eq67_overlap_pairs']>0
    # Both physical Bell halves and mixed Y ports are checked in the full LPU.
    for operation in ('XX','Y'):
        df=compile_deformation(build_reference_lpu(code,operation))
        schedule,_=staged_schedule(df)
        assert validate(schedule)['eq67_overlap_pairs']>0
        bell=next(c for c in schedule.checks if c.kind=='bell')
        assert len(bell.ancillas)==2 and len(schedule.readouts()[f'{bell.id}/0'])==2
        assert check_tableau(schedule,bell)['signed_readout_matches']
        for c in schedule.checks:
            assert check_tableau(schedule,c)['nondemolition']


def reversed_overlap():
    ids=('d0','d1')
    x=Check.single('x',Pauli.from_word('XX',ids))
    z=Check.single('z',Pauli.from_word('ZZ',ids))
    # x: d0 before z, but d1 after z. Both t1 and t2 remain conflict-free.
    gates=(Op(1,*x.interaction('d0'),'x','d0'),Op(2,*x.interaction('d1'),'x','d1'),
           Op(2,*z.interaction('d0'),'z','d0'),Op(1,*z.interaction('d1'),'z','d1'))
    from gross_design_bandle.circuits.schedule import finish_checks
    return Schedule(ids,(x,z),finish_checks((x,z),gates),4,'invalid_overlap')


def test_negative_collision_free_reversed_anticommuting_overlap():
    s=reversed_overlap()
    collision_check(s)
    with pytest.raises(ValueError,match=r'Eq. \(67\)'):
        validate(s)
    # Exact inverse-tableau propagation finds an unwanted ancilla input
    # factor. This checks the actual simultaneous circuit, not just metadata.
    with pytest.raises(ValueError,match='ancilla input factor'):
        check_tableau(s,s.checks[0],composite=True)


# Independently transcribed from Figure 4b AFTER mapping Figure 3 colors/roles.
PAPER_LAYERS=((1,'Z','R','A1_T'),(2,'X','L','A2'),(2,'Z','R','A3_T'),
              (3,'X','R','B2'),(3,'Z','L','B1_T'),(4,'X','R','B1'),(4,'Z','L','B2_T'),
              (5,'X','R','B3'),(5,'Z','L','B3_T'),(6,'X','L','A1'),(6,'Z','R','A2_T'),(7,'X','L','A3'))


def test_C03_donor_source_convention_and_paper_layers(gross,tmp_path):
    code,_,_,_=gross
    assert extract_layers()==PAPER_LAYERS
    edges,adapter=adapted_edges(code)
    assert adapter.qubits==tuple(range(code.spec.n))
    assert len(edges)==6*len(code.check_ids)
    # Literal coordinate oracle, independent of matrix/transposition adapter.
    for t,id,q in edges:
        sector='X' if id in code.check_ids[:code.spec.cells] else 'Z'
        check_index=code.check_ids.index(id)%code.spec.cells
        i,j=divmod(check_index,code.spec.m)
        layer=next(l for l in PAPER_LAYERS if l[0]==t and l[1]==sector)
        _,_,side,term=layer
        delta=(code.spec.A if term[0]=='A' else code.spec.B)[(2,0,1)[int(term[1])-1]]
        direction=-1 if term.endswith('_T') else 1
        assert q==code.qubit_ids[code.spec.qubit_index(side,i+direction*delta[0],j+direction*delta[1])]
    bad=tmp_path/'donor.py';bad.write_text('not pinned')
    with pytest.raises(ValueError,match='source hash'):
        extract_layers(bad)


def test_C03_staggered_8C_plus_1_offsets_and_repeat():
    for name in ('gross','two_gross'):
        c=load_reference_code(name,'memory')
        for rounds in (1,3):
            s=memory_schedule(c,rounds)
            assert s.duration==8*rounds+1
            assert sum(i.name=='TICK' for i in s.to_stim())==s.duration
            assert validate(s)['eq67_overlap_pairs']>0
            for r in range(rounds):
                for i,check in enumerate(s.checks):
                    reset=next(o for o in s.ops if o.round==r and o.check_id==check.id and o.gate in ('R','RX'))
                    read=next(o for o in s.ops if o.round==r and o.check_id==check.id and o.outcome_id)
                    assert (reset.time,read.time)==((8*r+1,8*r+8) if i<c.spec.cells else (8*r,8*r+7))
            for ccheck in s.checks:
                one=replace(s,ops=tuple(o for o in s.ops if o.round==0))
                assert check_tableau(one,ccheck)['signed_readout_matches']


def test_C04_ledger_counts_intervals_idle_and_policy_hash(gross):
    _,_,s,_=gross
    ledger=s.ledger()
    assert ledger['installed_qubits']==ledger['active_qubits']==323
    assert ledger['bell_couplers']==[] and ledger['bell_preparations']==0
    assert ledger['locations_by_kind']=={'CX':930,'CZ':23,'IDLE':1004,'M':72,'MX':89,'R':72,'RX':89}
    busy={(o.time,q) for o in s.ops for q in o.qubits}
    idles={tuple(x) for x in ledger['idle_locations']}
    assert len(idles)==1004
    for q,(begin,end) in ledger['live_data_intervals'].items():
        assert (begin,end)==(0,12)
        assert all(((t,q) in busy)^((q,t) in idles) for t in range(begin,end))
    for q,begin,end in ledger['live_ancilla_intervals']:
        assert all(((t,q) in busy)^((q,t) in idles) for t in range(begin,end))
    assert not ledger['fault_catalogue_complete']
    for key,value in (('basis_conversion','explicit local Cliffords'),('idle_policy','data-only')):
        changed=replace(s,policy={**s.policy,key:value})
        assert changed.hash!=s.hash
        with pytest.raises(ValueError,match='unsupported physical basis/noise policy'):
            changed.to_stim()
    shifted=replace(s,ops=tuple(replace(o,time=o.time+1) for o in s.ops),duration=s.duration+1)
    assert shifted.hash!=s.hash


def test_C04_bell_couplers_and_physical_census_are_separate(gross):
    c,_,_,_=gross
    df=compile_deformation(build_reference_lpu(c,'XX'))
    s,_=staged_schedule(df)
    ledger=s.ledger()
    assert ledger['installed_qubits']==378  # 288 BB + 90 LPU
    assert len(s.checks)==186 and len(s.outcomes)==187
    assert len(ledger['bell_couplers'])==ledger['bell_preparations']==1
    assert len(df.graph.vertices)==23
    assert len({a for check in s.checks[144:] for a in check.ancillas})==43


def test_C05_installed_full_connectivity_matches_published_census():
    # Histograms independently summed from Fig. 5(b,c), including BOTH Bell sides.
    expected={'gross':(90,{3:2,4:27,5:16,6:43,7:2}),
              'two_gross':(158,{3:12,4:38,5:32,6:54,7:22})}
    for name,(total,histogram) in expected.items():
        c=load_reference_code(name,'installed')
        result=installed_connectivity(c)
        assert result['installed_lpu']==total
        assert result['installed_total']==2*c.spec.n+total
        assert result['maximum_degree']==7
        assert result['lpu_degree_histogram']==histogram
        assert result['bell_half_degrees']==[5,5]
        assert len(result['bell_couplers'])==1
        # Original BB data and original BB check sites have gained <=1 coupler.
        for q in c.qubit_ids+tuple(f'anc:{id}' for id in c.check_ids):
            assert result['degrees'][q] in (6,7)


def test_coloring_is_optimal_delta_and_conflict_free():
    edges=(('a','x',0),('a','y',1),('a','z',2),('b','x',3),('b','y',4),('c','z',5))
    layers=bipartite_layers(edges)
    assert len(layers)==3
    assert sorted(p for layer in layers for p in layer)==list(range(6))
    for layer in layers:
        assert len({edges[p][0] for p in layer})==len(layer)
        assert len({edges[p][1] for p in layer})==len(layer)


def test_gross_X1_physical_instrument_matches_ideal_projection(gross):
    c,df,s,metadata=gross
    physical=build_physical_x1(df,rounds=2)
    assert physical.timing=={'edge_initialization':1,'deformed_cycle':12,'deformed_rounds':2,
        'deformed_body':24,'edge_split':1,'original_check_verification':9,'input_terminal_harness':0,'total':35}
    circuit=physical.to_stim()
    assert not {'MPP','DETECTOR','OBSERVABLE_INCLUDE'} & {i.name for i in circuit.flattened()}
    assert circuit.num_measurements==2*161+18+144==len(physical.outcomes())
    ledger=physical.ledger()
    assert ledger['installed_qubits']==ledger['active_qubits']==323
    assert ledger['locations_by_phase']['edge_initialize']=={'R':18,'IDLE':144}
    assert ledger['locations_by_phase']['split']=={'M':18,'IDLE':144}
    assert all(ledger['live_data_intervals'][q]==[0,26] for q in ledger['edge_data_inactive_after_split'])
    assert all(ledger['live_data_intervals'][q]==[0,35] for q in c.qubit_ids)
    assert sum(ledger['locations_by_kind'].values())==sum(sum(x.values()) for x in ledger['locations_by_phase'].values())
    serialized=physical.to_dict()
    assert len(serialized['complete_operations'])==len(physical.complete_ops())
    assert len(set(serialized['physical_outcomes']))==len(physical.outcomes())
    assert sum(i.name=='TICK' for i in circuit.flattened())==35
    refs=tuple(f'ref:{i}' for i in range(c.k))
    register=physical.register+refs
    for mode in ('plus','minus','choi'):
        for seed in range(4):
            stabs=[to_stim_pauli(p,register) for p in c.checks]
            from gross_design_bandle.surgery.ports import embed
            for i,(lx,lz) in enumerate(zip(c.logical_x,c.logical_z)):
                rx=embed(Pauli.from_word('X',(refs[i],)),register)
                rz=embed(Pauli.from_word('Z',(refs[i],)),register)
                if i==0 and mode!='choi':
                    stabs.extend((to_stim_pauli(lx.with_phase(2 if mode=='minus' else 0),register),to_stim_pauli(rx)))
                else:
                    stabs.extend((to_stim_pauli(embed(lx,register)*rx),to_stim_pauli(embed(lz,register)*rz)))
            initial=stim.TableauSimulator(seed=seed)
            initial.do(stim.Tableau.from_stabilizers(stabs,allow_redundant=True,allow_underconstrained=True).to_circuit())
            actual=initial.copy();actual.do(circuit)
            values=dict(zip(physical.outcomes(),map(int,actual.current_measurement_record())))
            outcome=physical.logical_outcome.evaluate(values)
            assert outcome==int(mode=='minus') if mode!='choi' else outcome in (0,1)
            _,frame=physical.frame.evaluate(values)
            actual.do_pauli_string(to_stim_pauli(frame,register))
            expected=initial.copy()
            expected.postselect_observable(to_stim_pauli(c.logical('X','1'),register),desired_value=bool(outcome))
            # Check a complete basis of DATA+REFERENCE stabilizers (not just
            # syndrome determinism). This establishes preserved Choi coherence.
            expected_generators=[to_stim_pauli(p,register) for p in c.checks]
            expected_generators.append(to_stim_pauli(c.logical('X','1').with_phase(2*outcome),register))
            for i in range(1,c.k):
                for logical,axis in ((c.logical_x[i],'X'),(c.logical_z[i],'Z')):
                    expected_generators.append(to_stim_pauli(embed(logical,register)*embed(Pauli.from_word(axis,(refs[i],)),register)))
            # The measured reference X is fixed by the target outcome for Choi.
            expected_generators.append(to_stim_pauli(Pauli.from_word('X',(refs[0],),(-1)**outcome if mode=='choi' else 1),register))
            for p in expected_generators:
                assert expected.peek_observable_expectation(p)==actual.peek_observable_expectation(p)==1
            for check in s.checks:
                if check.id.startswith('vertex:'):
                    assert values[f'deformed/0/{check.id}/0']==values[f'deformed/1/{check.id}/0']
                else:
                    assert values[f'deformed/0/{check.id}/0']==0
            # Original BB checks before frame are the predicted frame syndrome.
            for id,p in zip(c.check_ids,c.checks):
                assert values[f'memory/0/{id}/0']==frame.symplectic(p)


def test_negative_bad_sign_gate_bell_preparation_and_collision():
    c=Check.bell('b',Pauli.from_word('YZ',('d0','d1'),-1),('d0',))
    s=primitive_schedule(c)
    badsign=replace(s,ops=tuple(replace(o,invert=False) if o.outcome_id else o for o in s.ops))
    with pytest.raises(ValueError,match='wrong signed Pauli'):
        check_tableau(badsign,c)
    badgate=replace(s,ops=tuple(replace(o,gate='CX') if o.gate=='CY' else o for o in s.ops))
    with pytest.raises(ValueError,match='wrong signed Pauli'):
        check_tableau(badgate,c)
    with pytest.raises(ValueError,match='wrong controlled Pauli'):
        validate(badgate)
    late=replace(s,ops=tuple(replace(o,time=s.duration) if o.gate=='CX' and o.data_id is None else o for o in s.ops),duration=s.duration+1)
    with pytest.raises(ValueError,match='Bell preparation must precede'):
        validate(late)
    duplicated=replace(s,ops=s.ops+(s.ops[0],))
    with pytest.raises(ValueError,match='collision'):
        validate(duplicated)
    with pytest.raises(ValueError,match='overlap'):
        Check.bell('bad',c.pauli,('d0','d0'))
    with pytest.raises(ValueError,match='imaginary-phase'):
        Check.single('bad',c.pauli.with_phase(1))


def test_negative_missing_interaction_and_bad_round_request(gross):
    _,df,s,_=gross
    o=next(o for o in s.ops if o.data_id)
    incomplete=replace(s,ops=tuple(x for x in s.ops if x is not o))
    with pytest.raises(ValueError,match='missing check support'):
        validate(incomplete)
    # Extra unowned gates and data resets must not escape per-check validation.
    idle=next((t,q) for q,t in s.ledger()['idle_locations'] if q in s.data)
    t,q=idle
    orphan=replace(s,ops=s.ops+(Op(t,'R',(q,),phase='unexpected'),))
    with pytest.raises(ValueError,match='unowned physical operation'):
        validate(orphan)
    wrongsite=replace(s,ops=s.ops+(Op(t,'R',(q,),s.checks[0].id),))
    with pytest.raises(ValueError,match='wrong physical ancilla'):
        validate(wrongsite)
    for rounds in (0,-1,True,1.5):
        with pytest.raises(ValueError,match='positive'):
            build_physical_x1(df,rounds)
    c=load_reference_code('gross','bad')
    with pytest.raises(ValueError,match='X1 only'):
        build_physical_x1(compile_deformation(build_reference_lpu(c,'Y')))
