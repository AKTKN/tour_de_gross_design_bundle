"""Exact signed mixed-state stabilizer propagation with affine outcome bits.

Independent of Stim's randomized signed has_flow API. Rows store i^p X^x Z^z
and their eigenvalue as an integer bitset (bit zero is the affine constant).
Unrecorded resets trace out their qubit before adding its + axis stabilizer.
Only noiseless Clifford instructions are admitted; noise is never ignored.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class Row:
    x: int
    z: int
    phase: int = 0
    value: int = 0

    def mul(self, other):
        return Row(self.x ^ other.x, self.z ^ other.z,
                   (self.phase+other.phase+2*(self.z & other.x).bit_count()) % 4,
                   self.value ^ other.value)

    def anti(self, other):
        return ((self.x & other.z).bit_count() + (self.z & other.x).bit_count()) % 2


def pauli_row(pauli):
    x = z = phase = 0
    for q, p in enumerate(pauli):
        if p in (1, 2):
            x |= 1 << q
        if p in (2, 3):
            z |= 1 << q
        phase += p == 2
    if pauli.sign not in (1, -1):
        raise ValueError('imaginary measured Pauli')
    return Row(x, z, (phase+2*(pauli.sign == -1)) % 4)


class SignedTracker:
    def __init__(self, n):
        self.n = n
        self.rows = [Row(0, 1 << q) for q in range(n)]
        self.measurements = []
        self.constraints = []
        self.observables = {}

    def known(self, p):
        basis = {}
        for row in self.rows:
            mask = row.x | (row.z << self.n)
            while mask:
                pivot = mask.bit_length()-1
                if pivot not in basis:
                    basis[pivot] = row
                    break
                row = row.mul(basis[pivot]); mask = row.x | (row.z << self.n)
        residual = p
        mask = residual.x | (residual.z << self.n)
        while mask:
            pivot = mask.bit_length()-1
            if pivot not in basis:
                return None
            residual = residual.mul(basis[pivot]); mask = residual.x | (residual.z << self.n)
        if residual.phase % 2:
            raise ValueError('non-Hermitian signed flow')
        return residual.value ^ (residual.phase // 2)

    def measure(self, p):
        anti = [i for i, r in enumerate(self.rows) if r.anti(p)]
        if anti:
            value = 1 << (len(self.measurements)+1)
            pivot = self.rows[anti[0]]
            for i in anti[1:]:
                self.rows[i] = self.rows[i].mul(pivot)
            self.rows[anti[0]] = Row(p.x, p.z, p.phase, value)
        else:
            value = self.known(p)
            if value is None:
                value = 1 << (len(self.measurements)+1)
                self.rows.append(Row(p.x, p.z, p.phase, value))
        self.measurements.append(value)

    def reset(self, q, axis):
        # Row elimination on both local columns computes the partial trace.
        for column in ('x', 'z'):
            hits = [i for i, row in enumerate(self.rows) if getattr(row, column) >> q & 1]
            if hits:
                pivot = self.rows[hits[0]]
                for i in hits[1:]:
                    self.rows[i] = self.rows[i].mul(pivot)
                self.rows.pop(hits[0])
        bit = 1 << q
        self.rows.append(Row(bit if axis in ('X', 'Y') else 0,
                             bit if axis in ('Z', 'Y') else 0, int(axis == 'Y')))

    def gate(self, gate, qs):
        if gate == 'CY':
            self.gate('S_DAG', [qs[1]]); self.gate('CX', qs); self.gate('S', [qs[1]])
            return
        result = []
        for row in self.rows:
            x, z, p = row.x, row.z, row.phase
            a = 1 << qs[0]; xa, za = int(bool(x & a)), int(bool(z & a))
            if gate == 'H':
                p += 2*xa*za
                if xa != za:
                    x ^= a; z ^= a
            elif gate in ('S', 'S_DAG'):
                p += xa*(1 if gate == 'S' else -1)
                if xa:
                    z ^= a
            elif gate in ('X', 'Y', 'Z'):
                p += 2*((za if gate == 'X' else xa if gate == 'Z' else xa+za) % 2)
            elif gate in ('CX', 'CZ', 'SWAP'):
                b = 1 << qs[1]; xb, zb = int(bool(x & b)), int(bool(z & b))
                if gate == 'CX':
                    if xa:
                        x ^= b
                    if zb:
                        z ^= a
                elif gate == 'CZ':
                    p += 2*xa*xb
                    if xa:
                        z ^= b
                    if xb:
                        z ^= a
                else:
                    if xa != xb:
                        x ^= a | b
                    if za != zb:
                        z ^= a | b
            elif gate not in ('I',):
                raise ValueError(f'unsupported exact flow gate {gate}')
            result.append(Row(x, z, p % 4, row.value))
        self.rows = result

    def parity(self, targets):
        value = 0
        for target in targets:
            if not target.is_measurement_record_target or target.value >= 0:
                raise ValueError('flow annotation needs past record targets')
            if len(self.measurements)+target.value < 0:
                raise ValueError("record offset outside measurement history")
            try:
                value ^= self.measurements[len(self.measurements)+target.value]
            except IndexError as exc:
                raise ValueError('record offset outside measurement history') from exc
        return value

    def run(self, circuit):
        for instruction in circuit.flattened():
            name, ts = instruction.name, instruction.targets_copy()
            if name in ('TICK', 'QUBIT_COORDS', 'SHIFT_COORDS'):
                continue
            if name in ('DETECTOR', 'OBSERVABLE_INCLUDE'):
                value = self.parity(ts)
                if name == 'DETECTOR':
                    self.constraints.append(value)
                else:
                    k = int(instruction.gate_args_copy()[0])
                    self.observables[k] = self.observables.get(k, 0) ^ value
            elif name == 'MPAD':
                self.measurements.extend(t.value for t in ts)
            elif name in ('R', 'RX', 'RY'):
                for t in ts:
                    self.reset(t.value, {'R':'Z', 'RX':'X', 'RY':'Y'}[name])
            elif name in ('M', 'MX', 'MY'):
                for t in ts:
                    bit = 1 << t.value
                    self.measure(Row(bit if name != 'M' else 0, bit if name != 'MX' else 0,
                        int(name == 'MY') + 2*int(t.is_inverted_result_target)))
            elif name == 'MPP':
                cursor = 0
                while cursor < len(ts):
                    p = Row(0, 0)
                    while True:
                        t = ts[cursor]; bit = 1 << t.value
                        p = p.mul(Row(bit if t.is_x_target or t.is_y_target else 0,
                            bit if t.is_z_target or t.is_y_target else 0,
                            int(t.is_y_target) + 2*int(t.is_inverted_result_target)))
                        cursor += 1
                        if cursor == len(ts) or not ts[cursor].is_combiner:
                            break
                        cursor += 1
                    self.measure(p)
            elif name in ('CX', 'CY', 'CZ', 'SWAP'):
                for a, b in zip(ts[::2], ts[1::2]):
                    if a.is_measurement_record_target:
                        if name == 'SWAP' or not b.is_qubit_target:
                            raise ValueError('unsupported feedforward')
                        value = self.parity([a]); bit = 1 << b.value
                        axis = Row(bit if name != 'CZ' else 0, bit if name != 'CX' else 0)
                        self.rows = [Row(r.x, r.z, r.phase, r.value ^ (value if r.anti(axis) else 0))
                                     for r in self.rows]
                    else:
                        self.gate(name, [a.value, b.value])
            else:
                for t in ts:
                    self.gate(name, [t.value])
        return self


def verify_deterministic(circuit):
    tracker = SignedTracker(circuit.num_qubits).run(circuit)
    bad_d = [i for i, p in enumerate(tracker.constraints) if p]
    bad_o = [i for i, p in tracker.observables.items() if p]
    if bad_d or bad_o:
        raise ValueError(f'nonzero signed flow: detectors={bad_d}, observables={bad_o}')
    return {'oracle': 'exact signed affine stabilizer propagation; no randomized flow tests',
            'detectors': len(tracker.constraints), 'observables': len(tracker.observables),
            'all_zero': True}


def verify_deterministic_stim(circuit):
    """Strict determinacy plus raw reference signs, without Python state propagation.

    The DEM proves each declared parity is constant; a noiseless reference record
    fixes that constant. Detector samples alone subtract the reference baseline
    and would miss a deterministic wrong sign.
    """
    circuit.detector_error_model(allow_gauge_detectors=False)
    return _verify_reference_signs(circuit)


def _verify_reference_signs(circuit):
    """Internal sign check; caller must first extract this circuit's strict DEM."""
    import stim
    allowed = {'R','RX','RY','M','MX','MY','MPP','MPAD','H','S','S_DAG','X','Y','Z',
               'CX','CY','CZ','SWAP','I','TICK','QUBIT_COORDS','SHIFT_COORDS',
               'DETECTOR','OBSERVABLE_INCLUDE'}
    flat = list(circuit.flattened())
    if any(op.name not in allowed for op in flat):
        raise ValueError('unsupported exact noiseless reference flow gate')
    reference = circuit.reference_sample()
    cursor = 0; detectors = []; observables = {}
    for op in flat:
        if op.name in ('DETECTOR', 'OBSERVABLE_INCLUDE'):
            value = 0
            for t in op.targets_copy():
                if not t.is_measurement_record_target or not 0 <= cursor + t.value < cursor:
                    raise ValueError('record offset outside measurement history')
                value ^= int(reference[cursor + t.value])
            if op.name == 'DETECTOR':
                detectors.append(value)
            else:
                k = int(op.gate_args_copy()[0])
                observables[k] = observables.get(k, 0) ^ value
        else:
            cursor += stim.Circuit(str(op)).num_measurements
    if any(detectors) or any(observables.values()):
        raise ValueError('nonzero signed flow: strict deterministic reference parity')
    return {'oracle': 'strict Stim determinacy and exact reference-record signs',
            'detectors': len(detectors), 'observables': len(observables), 'all_zero': True}
