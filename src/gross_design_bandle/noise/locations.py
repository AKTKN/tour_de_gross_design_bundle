"""Physical location ledger; all boundaries and idle lifetimes are explicit.

An insertion boundary is after a flattened Stim instruction (-1 means before
the first). Readout flips are Paulis BEFORE readout; preparations are AFTER reset.
No faults are added to the ideal encoding, references or terminal verification.
"""
from dataclasses import dataclass, asdict
from collections import defaultdict
from gross_design_bandle.circuits.memory import memory_schedule
from gross_design_bandle.circuits.protocol import build_physical_x1
from gross_design_bandle.flows.boundaries import input_boundary
from gross_design_bandle.flows.observables import LogicalBasisAdapter


@dataclass(frozen=True)
class Location:
    id: str
    after_instruction: int
    kind: str
    qubits: tuple[int, ...]
    gate: str
    phase: str
    time: int
    round: int
    role: str
    repeat_path: tuple = ()

    def to_dict(self):
        return asdict(self)


def validate_locations(circuit, locations):
    flat = list(circuit.flattened())
    seen = set()
    arities = {'preparation':1, 'readout':1, 'idle':1, 'two_qubit':2}
    gates = {'preparation':('R','RX','RY'), 'readout':('M','MX','MY'),
             'idle':('I',), 'two_qubit':('CX','CY','CZ','SWAP')}
    for loc in locations:
        if not loc.id or loc.id in seen:
            raise ValueError('empty or duplicate location identity')
        seen.add(loc.id)
        if loc.kind not in arities or loc.gate not in gates[loc.kind] or len(loc.qubits) != arities[loc.kind]:
            raise ValueError('location kind/gate/arity mismatch')
        if len(set(loc.qubits)) != len(loc.qubits) or any(type(q) is not int or q not in range(circuit.num_qubits) for q in loc.qubits):
            raise ValueError('invalid physical location qubits')
        if type(loc.after_instruction) is not int or loc.after_instruction not in range(-1,len(flat)):
            raise ValueError('invalid physical insertion boundary')
        if loc.kind != 'idle':
            i = loc.after_instruction+(loc.kind=='readout')
            if i not in range(len(flat)) or flat[i].name != loc.gate:
                raise ValueError('location gate does not match physical boundary')
            ts = flat[i].targets_copy()
            if any(t.is_measurement_record_target for t in ts):
                raise ValueError('classical feedback is not a physical two-qubit location')
            qs = tuple(t.value for t in ts)
            width = arities[loc.kind]
            if loc.qubits not in tuple(qs[j:j+width] for j in range(0,len(qs),width)) or len(set(qs)) != len(qs):
                raise ValueError('location operands mismatch or non-disjoint batched gates')
        if not loc.phase or not loc.role or type(loc.time) is not int or loc.time < 0 or type(loc.round) is not int or loc.round < 0:
            raise ValueError('missing physical location provenance')


def benchmark_locations(code, harness, *, operation, rounds, deformation=None):
    """Named independent v1 policy derived from the phase04 schedule ledger.

    Native CX/CY/CZ (including Bell preparation) each get 15 joint primitives.
    Every live idle gets X/Y/Z. Active gates do not also get an idle. Software
    frame processing is classical. The last original round remains noise-free.
    """
    if harness.split_mode != 'frame':
        raise ValueError('noise policy currently requires software split frame')
    if operation == 'memory':
        s = memory_schedule(code, rounds)
        ops, ledger, register, duration = s.ordered_ops(), s.ledger(), s.register, s.duration
        phases = {t:'memory' for t in range(duration)}
        round_at = {t:min(t//8,rounds-1) for t in range(duration)}
    elif operation == 'X1':
        p = build_physical_x1(deformation,rounds)
        duration = 2+rounds*p.cycle.duration
        ops = tuple(o for o in p.complete_ops() if o.time < duration)
        ledger, register = p.ledger(), p.register
        phases = {t:('edge_initialize' if t == 0 else 'split' if t == duration-1 else 'deformed') for t in range(duration)}
        round_at = {t:max(0,min((t-1)//p.cycle.duration,rounds-1)) for t in range(duration)}
    else:
        raise ValueError('noise benchmark scope is gross memory/X1')
    initial, expected_register, _ = input_boundary(code, LogicalBasisAdapter.single_block(code,operation),register)
    if expected_register != harness.register:
        raise ValueError('noise register/harness mismatch')
    flat = list(harness.circuit.flattened()); prefix = list(initial.flattened())
    if flat[:len(prefix)] != prefix:
        raise ValueError('ideal boundary not separable; new noise policy required')
    tick = 0; physical = defaultdict(list); tick_boundary = {}
    for i in range(len(prefix),len(flat)):
        op = flat[i]
        if tick >= duration:
            break
        if op.name == 'TICK':
            tick_boundary[tick] = i-1; tick += 1
        elif op.name in ('R','RX','M','MX','CX','CY','CZ'):
            ts = op.targets_copy()
            width = 2 if op.name in ('CX','CY','CZ') else 1
            if any(t.is_measurement_record_target for t in ts):
                raise ValueError('unmodelled classical feedback inside noisy region')
            for j in range(0,len(ts),width):
                physical[tick].append((op.name,tuple(harness.register[t.value] for t in ts[j:j+width]),i))
    if tick != duration:
        raise ValueError('incomplete physical time ledger')
    lookup = {(t,g,qs):i for t,entries in physical.items() for g,qs,i in entries}
    expected = {(o.time,o.gate,o.qubits) for o in ops}
    if set(lookup) != expected or len(lookup) != len(ops):
        raise ValueError('schedule/noise instruction coverage mismatch')
    index = {q:i for i,q in enumerate(harness.register)}
    result = []
    for o in ops:
        i = lookup[o.time,o.gate,o.qubits]
        kind = 'preparation' if o.gate in ('R','RX') else 'readout' if o.outcome_id else 'two_qubit'
        result.append(Location(f'{o.time}/{o.gate}/'+','.join(o.qubits), i-1 if kind=='readout' else i,
            kind,tuple(index[q] for q in o.qubits),o.gate,phases[o.time],o.time,o.round,
            'Bell_preparation' if len(o.qubits)==2 and o.data_id is None else 'check_interaction' if o.data_id else 'reset_or_readout'))
    data = set(code.qubit_ids)
    for q,t in ledger['idle_locations']:
        if t < duration:
            result.append(Location(f'{t}/IDLE/{q}',tick_boundary[t],'idle',(index[q],),'I',
                phases[t],t,round_at[t], 'BB_data' if q in data else 'edge_data' if q.startswith('edge:') else 'prepared_ancilla'))
    result.sort(key=lambda l:(l.after_instruction,l.id))
    validate_locations(harness.circuit,result)
    return tuple(result), {'profile':'native_schedule_independent_noise_v1',
        'gate_policy':'native controlled Paulis; one joint two-qubit channel per CX/CY/CZ including Bell preparation',
        'idle_policy':'X,Y,Z on every unoccupied live data/prepared ancilla tick; no active-gate idle',
        'boundaries':'ideal encoding/references and last original verification/terminal MPP have no noise',
        'schedule_data':ledger['live_data_intervals'], 'schedule_ancillas':ledger['live_ancilla_intervals'],
        'noisy_ticks':duration, 'paper_exact':False, 'O4':'both admission counts reported; Table-6 population unresolved'}
