"""Independent binary Pauli propagation oracle for fixed fault signatures.

No primitive catalogue or admission policy is defined here. X/Z components of
one injected Pauli are propagated jointly, including measurement feedforward.
"""
import numpy as np


def fault_signature(circuit, after_instruction, x, z):
    flat = list(circuit.flattened())
    if after_instruction not in range(-1, len(flat)) or min(x, z) < 0 or (x | z) >> circuit.num_qubits:
        raise ValueError('invalid fault location/register')
    # The fault is absent before the specified boundary.
    ex = ez = 0
    records, detectors = [], []
    obs = np.zeros(circuit.num_observables, dtype=np.uint8)
    for i, op in enumerate(flat):
        if i == after_instruction+1:
            ex, ez = x, z
        ts = op.targets_copy(); name = op.name
        def parity(targets):
            return sum(records[len(records)+t.value] for t in targets) % 2
        if name in ('DETECTOR', 'OBSERVABLE_INCLUDE'):
            bit = parity(ts)
            if name == 'DETECTOR':
                detectors.append(bit)
            else:
                obs[int(op.gate_args_copy()[0])] ^= bit
        elif name == 'MPAD':
            records.extend(0 for t in ts)
        elif name in ('R', 'RX', 'RY'):
            for t in ts:
                ex &= ~(1 << t.value); ez &= ~(1 << t.value)
        elif name in ('M', 'MX', 'MY'):
            for t in ts:
                bit = 1 << t.value
                records.append((bool(ex & bit) if name == 'M' else bool(ez & bit) if name == 'MX'
                                else bool(ex & bit) ^ bool(ez & bit)))
        elif name == 'MPP':
            cursor = 0
            while cursor < len(ts):
                flip = 0
                while True:
                    t = ts[cursor]; bit = 1 << t.value
                    flip ^= (bool(ex & bit) if t.is_z_target else bool(ez & bit) if t.is_x_target
                             else bool(ex & bit) ^ bool(ez & bit))
                    cursor += 1
                    if cursor == len(ts) or not ts[cursor].is_combiner:
                        break
                    cursor += 1
                records.append(flip)
        elif name in ('H', 'S', 'S_DAG'):
            for t in ts:
                bit = 1 << t.value
                if name == 'H':
                    if bool(ex & bit) != bool(ez & bit):
                        ex ^= bit; ez ^= bit
                elif ex & bit:
                    ez ^= bit
        elif name in ('CX', 'CY', 'CZ', 'SWAP'):
            for a, b in zip(ts[::2], ts[1::2]):
                bb = 1 << b.value
                if a.is_measurement_record_target:
                    if parity([a]):
                        if name in ('CX', 'CY'):
                            ex ^= bb
                        if name in ('CZ', 'CY'):
                            ez ^= bb
                    continue
                aa = 1 << a.value
                xa, za, xb, zb = bool(ex & aa), bool(ez & aa), bool(ex & bb), bool(ez & bb)
                if name == 'SWAP':
                    if xa != xb:
                        ex ^= aa | bb
                    if za != zb:
                        ez ^= aa | bb
                elif name == 'CX':
                    if xa:
                        ex ^= bb
                    if zb:
                        ez ^= aa
                elif name == 'CZ':
                    if xa:
                        ez ^= bb
                    if xb:
                        ez ^= aa
                else:
                    if xa:
                        ex ^= bb; ez ^= bb
                    if xb != zb:
                        ez ^= aa
        elif name not in ('I', 'X', 'Y', 'Z', 'TICK', 'QUBIT_COORDS', 'SHIFT_COORDS'):
            raise ValueError(f'unsupported fault oracle gate {name}')
    return np.array(detectors, dtype=np.uint8), obs


def inject_fixed_fault(circuit, after_instruction, x, z):
    """One probability-one joint Pauli, for deterministic oracle checks only."""
    import stim
    if after_instruction not in range(-1, len(list(circuit.flattened()))):
        raise ValueError('invalid fixed-fault location')
    out = stim.Circuit()
    def append_fault():
        targets = []
        for q in range(circuit.num_qubits):
            a, b = x >> q & 1, z >> q & 1
            if a or b:
                targets.append((stim.target_y if a and b else stim.target_x if a else stim.target_z)(q))
        if targets:
            out.append('CORRELATED_ERROR', targets, 1)
    if after_instruction == -1:
        append_fault()
    for i, instruction in enumerate(circuit.flattened()):
        out.append(instruction)
        if i == after_instruction:
            append_fault()
    return out
