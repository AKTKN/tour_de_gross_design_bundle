"""One reverse binary sensitivity sweep for joint detector/logical signatures.

Independent from flows.signatures' forward Pauli injection oracle and from
Stim's DEM. Each output bit occupies one bit of an arbitrary-precision integer.
No graphlike decomposition, gauge flags or DEM compaction is used.
"""


def joint_signatures(circuit, faults):
    flat = list(circuit.flattened())
    counts = []; m = d = 0
    for op in flat:
        counts.append((m,d))
        if op.name in ('M','MX','MY','MPAD'):
            m += len(op.targets_copy())
        elif op.name == 'MPP':
            ts = op.targets_copy()
            m += sum(j==0 or not ts[j-1].is_combiner for j,t in enumerate(ts) if not t.is_combiner)
        elif op.name == 'DETECTOR':
            d += 1
    sx = [0]*circuit.num_qubits; sz = sx.copy(); records = [0]*m
    requested = {}
    for j,(boundary,x,z) in enumerate(faults):
        if boundary not in range(-1,len(flat)) or min(x,z)<0 or (x|z)>>circuit.num_qubits:
            raise ValueError('invalid fault boundary/register')
        requested.setdefault(boundary,[]).append((j,x,z))
    signatures = [0]*len(faults)

    def save(boundary):
        for j,x,z in requested.get(boundary,()):
            value = 0
            while x:
                bit = x & -x; value ^= sx[bit.bit_length()-1]; x ^= bit
            while z:
                bit = z & -z; value ^= sz[bit.bit_length()-1]; z ^= bit
            signatures[j] = value

    for i in range(len(flat)-1,-1,-1):
        save(i)
        op = flat[i]; name = op.name; ts = op.targets_copy(); m,d = counts[i]
        if name in ('DETECTOR','OBSERVABLE_INCLUDE'):
            value = 1 << (d if name=='DETECTOR' else circuit.num_detectors+int(op.gate_args_copy()[0]))
            for t in ts:
                if not t.is_measurement_record_target or not 0 <= m+t.value < m:
                    raise ValueError('annotation record outside history')
                records[m+t.value] ^= value
        elif name in ('M','MX','MY'):
            for j,t in enumerate(ts):
                if name in ('M','MY'):
                    sx[t.value] ^= records[m+j]
                if name in ('MX','MY'):
                    sz[t.value] ^= records[m+j]
        elif name == 'MPP':
            cursor = j = 0
            while cursor < len(ts):
                while True:
                    t = ts[cursor]
                    if t.is_z_target or t.is_y_target:
                        sx[t.value] ^= records[m+j]
                    if t.is_x_target or t.is_y_target:
                        sz[t.value] ^= records[m+j]
                    cursor += 1
                    if cursor == len(ts) or not ts[cursor].is_combiner:
                        break
                    cursor += 1
                j += 1
        elif name in ('R','RX','RY'):
            for t in ts:
                sx[t.value] = sz[t.value] = 0
        elif name in ('H','S','S_DAG'):
            for t in reversed(ts):
                q = t.value
                if name == 'H':
                    sx[q],sz[q] = sz[q],sx[q]
                else:
                    sx[q] ^= sz[q]
        elif name in ('CX','CY','CZ','SWAP'):
            for a,b in reversed(list(zip(ts[::2],ts[1::2]))):
                q = b.value
                if a.is_measurement_record_target:
                    if not 0 <= m+a.value < m:
                        raise ValueError('feedback record outside history')
                    records[m+a.value] ^= ((sx[q] if name in ('CX','CY') else 0) ^ (sz[q] if name in ('CZ','CY') else 0))
                    continue
                p = a.value
                if name == 'CX':
                    sx[p] ^= sx[q]; sz[q] ^= sz[p]
                elif name == 'CZ':
                    sx[p] ^= sz[q]; sx[q] ^= sz[p]
                elif name == 'CY':
                    sx[p] ^= sx[q]^sz[q]; sx[q] ^= sz[p]; sz[q] ^= sz[p]
                else:
                    sx[p],sx[q] = sx[q],sx[p]; sz[p],sz[q] = sz[q],sz[p]
        elif name not in ('I','X','Y','Z','MPAD','TICK','QUBIT_COORDS','SHIFT_COORDS'):
            raise ValueError(f'unsupported sensitivity gate {name}')
        if op.gate_args_copy() and name in ('M','MX','MY','MPP'):
            raise ValueError('base circuit must be noiseless')
    save(-1)
    return tuple(signatures)
