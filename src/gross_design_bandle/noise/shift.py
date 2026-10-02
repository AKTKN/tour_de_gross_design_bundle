"""Noise provenance for every transfer, reuse, bundle and syndrome boundary."""
from collections import defaultdict
from gross_design_bandle.circuits.shift import shift_sequence, timing_policy
from gross_design_bandle.flows.boundaries import input_boundary
from gross_design_bandle.flows.observables import LogicalBasisAdapter
from .locations import Location, validate_locations


def shift_locations(code, harness, instructions=10, *, profile=None):
    sequence = shift_sequence(code,instructions,profile=profile)
    profile = sequence.plan.profile
    if (harness.split_mode!='frame' or harness.boundary_policy.get('profile')!=profile or
        harness.boundary_policy.get('instructions')!=instructions):
        raise ValueError('shift harness/profile/instruction mismatch')
    initial,register,_ = input_boundary(code,LogicalBasisAdapter.single_block(code),sequence.register)
    flat = list(harness.circuit.flattened()); prefix = list(initial.flattened())
    if register!=harness.register or flat[:len(prefix)]!=prefix:
        raise ValueError('shift ideal boundary/register mismatch')
    by = defaultdict(list); ticks = {}; t=0
    for i in range(len(prefix),len(flat)):
        op = flat[i]
        if t>=sequence.duration: break
        if op.name=='TICK': ticks[t]=i-1; t+=1; continue
        if op.name not in ('R','RX','M','MX','CX'):
            raise ValueError('unexpected instruction inside physical shift')
        ts = op.targets_copy(); width = 2 if op.name=='CX' else 1
        if any(q.is_measurement_record_target for q in ts):
            raise ValueError('unmodelled feedback inside shift')
        for j in range(0,len(ts),width):
            by[t].append((op.name,tuple(register[q.value] for q in ts[j:j+width]),i))
    expected = defaultdict(list)
    for o in sequence.ordered_ops(): expected[o.time].append((o.gate,o.qubits))
    if t!=sequence.duration or {t:[(g,qs) for g,qs,i in es] for t,es in by.items()}!=dict(expected):
        raise ValueError('physical shift instruction coverage mismatch')
    index = {q:i for i,q in enumerate(register)}; result=[]
    for time,ops in expected.items():
        owners = [o for o in sequence.ordered_ops() if o.time==time]
        for o,(_,_,i) in zip(owners,by[time]):
            kind = 'preparation' if o.gate in ('R','RX') else 'readout' if o.outcome_id else 'two_qubit'
            role = 'to_check_transfer' if o.phase=='transfer_1' and kind=='two_qubit' else \
                   'to_data_transfer' if o.phase=='transfer_2' and kind=='two_qubit' else \
                   sequence.role_at(o.qubits[0],time)
            result.append(Location(f'{time}/{o.gate}/'+','.join(o.qubits),i-1 if kind=='readout' else i,
                kind,tuple(index[q] for q in o.qubits),o.gate,o.phase,time,o.round,role))
    for q,time in sequence.ledger()['idle_locations']:
        local = (time-1)%14 if time else -1
        phase = 'shift_initialize' if time==0 else 'transfer_1' if local<3 else 'transfer_2' if local<6 else 'following_syndrome'
        result.append(Location(f'{time}/IDLE/{q}',ticks[time],'idle',(index[q],),'I',phase,time,
                               max(0,(time-1)//14),sequence.role_at(q,time)))
    result.sort(key=lambda l:(l.after_instruction,l.id)); validate_locations(harness.circuit,result)
    return tuple(result), {'profile':profile,'paper_exact':False,'noisy_ticks':sequence.duration,
        'boundaries':'initial check R noisy; encoded data/references and terminal MPP ideal',
        'timing_policy':timing_policy(profile),'idle_policy':'every unoccupied live physical site each tick',
        'frames':'classical XOR; no noise channel or metadata replacement for transfers',
        'O4':'all primitive copies retained; joint-zero admission explicitly selectable'}
