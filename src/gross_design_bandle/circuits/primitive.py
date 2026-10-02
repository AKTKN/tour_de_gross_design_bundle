"""One physical check with its absolute physical readouts and XOR."""
from .checks import support
from .schedule import Op, Schedule, finish_checks, validate


def primitive_schedule(check):
    gates = []
    cursor = 1
    if check.kind=='bell':
        gates.append(Op(cursor,'CX',check.ancillas,check.id,phase='primitive'))
        cursor += 1
    # Disjoint halves run concurrently. This is a construction primitive;
    # system-level interleaving is validated by the schedule layer.
    for part in check.parts:
        for i,q in enumerate(part):
            gates.append(Op(cursor+i,*check.interaction(q),check.id,q,phase='primitive'))
    ops = finish_checks((check,),gates,phase='primitive')
    out = Schedule(check.pauli.qubit_ids,(check,),ops,max(o.time for o in ops)+1,'physical_check_v1')
    validate(out)
    return out
