"""Transfer readout flows, carried X frames and full K24 shift channel harness."""
from gross_design_bandle.circuits.shift import shift_sequence, PROFILE, TIMING_POLICY
from gross_design_bandle.codes.reference_profiles import physical_shift_permutation
from gross_design_bandle.surgery.frame import Parity
from .harness import BenchmarkHarness, remap, xor
from .boundaries import input_boundary, mpp
from .observables import LogicalBasisAdapter, correlation
from .records import RecordProgram


def x_frame_parity(frame, pauli):
    if len(frame) != len(pauli.z):
        raise ValueError('shift frame register mismatch')
    return xor(f for f,z in zip(frame,pauli.z) if z)


def build_shift_benchmark(code, instructions=10, *, profile=PROFILE):
    sequence = shift_sequence(code,instructions,profile=profile)
    plan = sequence.plan; basis = LogicalBasisAdapter.single_block(code,'memory')
    initial,register,refs = input_boundary(code,basis,sequence.register)
    program = RecordProgram(); program.chunk(initial)
    body = remap(sequence.to_stim(),sequence.register,register)
    program.chunk(body,sequence.outcomes)
    data_index = {q:i for i,q in enumerate(plan.data)}
    frame = tuple(Parity() for q in plan.data)
    anc = {q:Parity() for q in plan.register[len(plan.data):]}
    previous = None; history = []
    checks = code.checks
    key = lambda p:(p.phase,p.x,p.z)
    shifted_old = {key(p.permuted(plan.target_to_source)):id for id,p in zip(code.check_ids,checks)}
    def det(name,parity,kind,why): program.mark(name,'detector',parity,kind,why)
    for r in range(instructions):
        first = {q:Parity((f'shift/{r}/transfer_1/{q}',)) for q in plan.data}
        second = {q:Parity((f'shift/{r}/transfer_2/{q}',)) for q in anc}
        carried = [None]*len(frame)
        intermediate = {}
        for (source,check),(_,dest) in zip(plan.first,plan.second):
            det(f'shift/{r}/vacated_data/{source}',first[source]^anc[check],'transfer_readout',
                'two-CNOT vacated source equals recorded destination Z state')
            det(f'shift/{r}/vacated_check/{check}',second[check]^first[dest],'transfer_readout',
                'second vacated source equals first measured destination Z state')
            intermediate[check] = frame[data_index[source]]^anc[check]
            carried[data_index[dest]] = intermediate[check]^first[dest]
        frame = tuple(carried)
        current = {}
        for id,p in zip(code.check_ids,checks):
            q = f'anc:{id}'; raw = Parity((f'shift/{r}/syndrome/{id}',))
            prepared = second[q] if ':Z:' in id else Parity()
            current[id] = raw^prepared^x_frame_parity(frame,p)
            prediction = previous[shifted_old[key(p)]] if previous else Parity()
            det(f'shift/{r}/syndrome/{id}',current[id]^prediction,'following_syndrome',
                'signed check with reused Z-ancilla and data frames; previous check transported by physical shift')
            anc[q] = raw if ':Z:' in id else Parity()
        history.append({'instruction':r, 'data_X_frame':[p.to_dict() for p in frame],
                        'data_Z_frame':[Parity().to_dict() for q in plan.data],
                        'intermediate_check_site_X_frame':{q:p.to_dict() for q,p in intermediate.items()},
                        'check_site_Z_state_frame':{q:p.to_dict() for q,p in anc.items()},
                        'physical_to_input_logical_site':physical_shift_permutation(code.spec,
                            (r+1)*plan.delta[0],(r+1)*plan.delta[1])})
        previous = current
    for id,p in zip(code.check_ids,checks):
        outcome = f'closure/{id}'
        program.chunk(mpp(p,register),(outcome,))
        det(outcome,Parity((outcome,))^x_frame_parity(frame,p)^previous[id],
            'final_closure','ideal old check equals last corrected physical syndrome')
    terminal = []
    permutation = physical_shift_permutation(code.spec,instructions*plan.delta[0],instructions*plan.delta[1])
    for k,(name,p) in enumerate(zip(basis.names,basis.generators)):
        p = p.permuted(permutation)
        ref = refs[k if k<code.k else k-code.k]
        joint = correlation(p,'X' if k<code.k else 'Z',ref,register)
        outcome = f'logical_terminal/{name}'; program.chunk(mpp(joint,register),(outcome,))
        program.mark(name,'observable',Parity((outcome,))^x_frame_parity(frame,p),
                     'logical_action','transported encoded Bell correlation corrected by transfer frame',k)
        terminal.append(joint.to_dict())
    lowered = program.lower(); cert = basis.certificate(code)
    cert['target'] = 'shift'; cert['terminal_readout_paulis'] = terminal
    cert['physical_parities'] = [{'index':a['observable_index'],'name':a['name'],'parity':a['parity']}
                               for a in lowered.annotations if a['kind']=='observable']
    return BenchmarkHarness(lowered.circuit,register,lowered.outcome_ids,lowered.annotations,cert,
        {'profile':PROFILE,'paper_exact':False,'open_items':['O1','O2','O3','O4','O5'],
         'timing':sequence.validate(),'timing_policy':TIMING_POLICY,'instructions':instructions,
         'reporting':'P_circuit/C; no sampled rate in this construction',
         'divisor':instructions,'transfer_plan':plan.to_dict(),'role_and_frame_history':history,
         'boundaries':'ideal encoded input/references and terminal MPP; noisy initial check preparation',
         'ideal_reference_qubits':list(refs.values())},body,'frame')
