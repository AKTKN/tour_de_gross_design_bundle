"""A.7-style deterministic gross memory/X1 harness around physical bodies.

Ideal encoding, final MPP closure and reference qubits are explicit boundaries.
The physical body retains the phase04 native schedule. A raw instrument API is
separate and may have random outcomes; it cannot be a decoding experiment.
"""
from dataclasses import dataclass
from functools import reduce
import stim
import numpy as np
from gross_design_bandle.algebra import gf2
from gross_design_bandle.surgery.frame import Parity
from gross_design_bandle.circuits.memory import memory_schedule
from gross_design_bandle.circuits.protocol import build_physical_x1
from .records import RecordProgram
from .observables import LogicalBasisAdapter, correlation
from .boundaries import input_boundary, mpp
from .stabilizer_flows import verify_deterministic


def xor(parities):
    return reduce(lambda a, b:a ^ b, parities, Parity())


def frame_parity(frame, pauli):
    return xor(term for term, port in zip(frame.terms, frame.ports.ports) if port.symplectic(pauli))


def remap(circuit, source, destination):
    out = stim.Circuit()
    index = {q:i for i,q in enumerate(destination)}
    for op in circuit.flattened():
        targets = []
        for t in op.targets_copy():
            if t.is_measurement_record_target or t.is_combiner:
                targets.append(t)
            elif t.is_x_target or t.is_y_target or t.is_z_target:
                targets.append((stim.target_x if t.is_x_target else stim.target_y if t.is_y_target else stim.target_z)
                               (index[source[t.value]], invert=t.is_inverted_result_target))
            else:
                q = index[source[t.value]]
                targets.append(stim.target_inv(q) if t.is_inverted_result_target else q)
        out.append(op.name, targets, op.gate_args_copy())
    return out


@dataclass(frozen=True)
class BenchmarkHarness:
    circuit: stim.Circuit
    register: tuple
    outcome_ids: tuple
    annotations: tuple
    logical_generators: dict
    boundary_policy: dict
    physical_body: stim.Circuit
    split_mode: str

    def validate(self, *, flow_oracle='stim_reference'):
        if flow_oracle not in ('stim_reference', 'signed_affine'):
            raise ValueError('unknown flow oracle')
        cert = self.logical_generators
        expected = set(range(cert['rank']))
        emitted = {int(i.gate_args_copy()[0]) for i in self.circuit.flattened() if i.name == 'OBSERVABLE_INCLUDE'}
        if emitted != expected or len(set(cert['names'])) != cert['rank']:
            raise ValueError('named observable coverage mismatch')
        if gf2.rank(np.array(cert['logical_coordinates'], dtype=np.uint8)) != cert['rank']:
            raise ValueError('named logical generator rank mismatch')
        saved = cert['physical_parities']
        if [p['index'] for p in saved] != list(range(cert['rank'])) or [p['name'] for p in saved] != cert['names']:
            raise ValueError('named physical parity coverage mismatch')
        if len(self.outcome_ids) != self.circuit.num_measurements or len(set(self.outcome_ids)) != len(self.outcome_ids):
            raise ValueError('symbolic measurement ledger mismatch')
        dem = self.circuit.detector_error_model(allow_gauge_detectors=False)
        if flow_oracle == 'stim_reference':
            from .stabilizer_flows import _verify_reference_signs
            flows = _verify_reference_signs(self.circuit)
        else:
            flows = verify_deterministic(self.circuit)
        if dem.num_observables != self.logical_generators['rank']:
            raise ValueError('strict DEM observable rank/count mismatch')
        return {'exact_flows': flows, 'strict_dem_detectors': dem.num_detectors,
                'strict_dem_observables': dem.num_observables, 'gauge_workaround': False}

    def to_dict(self):
        return {'schema_version': 1, 'scope': 'noiseless single-block A.7-style gross memory/X1 benchmark',
            'register': list(self.register), 'symbolic_outcomes': list(self.outcome_ids),
            'annotations': list(self.annotations), 'logical_generators': self.logical_generators,
            'boundaries': self.boundary_policy, 'split_mode': self.split_mode,
            'noise_emitted': False, 'paper_exact': False, 'decoder_invoked': False}


@dataclass(frozen=True)
class TruthTableInstrument:
    """No detector/observable claims; encoded input is supplied by the caller."""
    protocol: object

    @property
    def circuit(self):
        return self.protocol.to_stim()

    @property
    def logical_outcome(self):
        return self.protocol.logical_outcome


def build_benchmark(code, *, operation='memory', rounds=1, deformation=None, split_mode='frame'):
    if code.spec.name != 'gross' or operation not in ('memory', 'X1'):
        raise ValueError('validated physical harness scope is gross memory/X1')
    if not isinstance(rounds, int) or isinstance(rounds, bool) or rounds < 1:
        raise ValueError('rounds must be a positive integer')
    if split_mode not in ('frame', 'active'):
        raise ValueError('split_mode must be frame or active')
    if operation == 'memory' and deformation is not None:
        raise ValueError('memory does not take a deformation')
    basis = LogicalBasisAdapter.single_block(code, operation)
    if operation == 'X1':
        if deformation is None or deformation.lpu.codes != (code,) or deformation.lpu.ports.target != basis.x[0]:
            raise ValueError('X1 harness requires the same block and exact signed X1 deformation')
        physical = build_physical_x1(deformation, rounds)
        pregister = physical.register
    else:
        schedule = memory_schedule(code, rounds)
        pregister = schedule.register
    initial, register, refs = input_boundary(code, basis, pregister)
    program = RecordProgram(); program.chunk(initial)
    body = stim.Circuit()
    scored = []
    terminal_paulis = []
    frame = None
    phases = ['ideal_input', 'physical_memory', 'ideal_terminal']

    def detector(name, parity, flow_class, why):
        program.mark(name, 'detector', parity, flow_class, why)

    if operation == 'memory':
        c = remap(schedule.to_stim(), schedule.register, register)
        body += c; program.chunk(c, schedule.outcomes)
        readouts = schedule.readouts()
        for r in range(rounds):
            for id in code.check_ids:
                p = Parity(readouts[f'{id}/{r}'])
                if r:
                    p ^= Parity(readouts[f'{id}/{r-1}'])
                detector(f'memory/{r}/{id}', p, 'first_round' if r == 0 else 'repeat',
                         '+1 encoded stabilizer input' if r == 0 else 'same signed nondemolition stabilizer')
        last_old = {id:Parity(readouts[f'{id}/{rounds-1}']) for id in code.check_ids}
    else:
        phases = ['ideal_input', 'edge_reset', 'merge', 'deformed_repeat', 'split',
                  'split_correction_'+split_mode, 'noiseless_physical_original_round', 'ideal_terminal']
        df = deformation
        frame = physical.frame
        edges = physical.cycle.data[len(code.qubit_ids):]
        c = stim.Circuit(); c.append('R', [register.index(q) for q in edges]); c.append('TICK')
        program.chunk(c); body += c
        last = {}
        for r in range(rounds):
            ids = tuple(i.replace('deformed/0/', f'deformed/{r}/') for i in physical.cycle.outcomes)
            c = remap(physical.cycle.to_stim(), physical.cycle.register, register)
            program.chunk(c, ids); body += c
            current = {check.id:Parity(tuple(i.replace('deformed/0/', f'deformed/{r}/')
                       for i in physical.cycle.readouts()[f'{check.id}/0'])) for check in physical.cycle.checks}
            for check in physical.cycle.checks:
                if r or not check.id.startswith('vertex:'):
                    detector(f'deformed/{r}/{check.id}', current[check.id] ^ (last[check.id] if r else Parity()),
                        'repeat' if r else 'merge',
                        'stable signed check readout XOR (including Bell halves)' if r else
                        'dressed old check = old check times reset edge Z; selected cycle is reset edge Z product')
            last = current
        measured_target = xor(last[f'vertex:{v}'] for v in df.graph.vertices)
        scored.append((0, basis.x_names[0], measured_target))
        c = stim.Circuit(); c.append('M', [register.index(q) for q in edges]); c.append('TICK')
        program.chunk(c, tuple(o.outcome_id for o in physical.split)); body += c
        split_ids = tuple(o.outcome_id for o in physical.split)
        for cycle, mask in zip(df.graph.cycles, df.graph.cycle_matrix):
            detector(f'split/cycle:{cycle.id}', Parity(tuple(i for i,b in zip(split_ids,mask) if b)) ^ last[f'cycle:{cycle.id}'],
                     'split', 'Z-edge product equals last selected signed cycle readout')
        if split_mode == 'active':
            for vertex, port, term in zip(df.graph.vertices, df.lpu.ports.ports, frame.terms):
                for q, x, z in zip(port.qubit_ids, port.x, port.z):
                    if x or z:
                        gate = 'CY' if x and z else 'CX' if x else 'CZ'
                        program.mark(f'frame/{vertex}/{q}', gate, term, 'split_correction',
                                     'rooted path Pauli port correction; global port phase is unobservable', register.index(q))
        c = remap(physical.terminal.to_stim(), physical.terminal.register, register)
        program.chunk(c, physical.terminal.outcomes); body += c
        last_old = {}
        for j,(id, p) in enumerate(zip(code.check_ids, code.checks)):
            corrected = Parity(physical.terminal.readouts()[f'{id}/0'])
            if split_mode == 'frame':
                corrected ^= frame_parity(frame, p)
            last_old[id] = corrected
            prediction = last[id] ^ Parity(tuple(i for i,b in zip(split_ids,df.dressing[j]) if b)) ^ frame_parity(frame, p)
            detector(f'split/old:{id}', corrected ^ prediction, 'split',
                     'retained old = last dressed old times split Z dressing; corrected by port anticommutation')

    body = RecordProgram(program.nodes[1:]).lower().circuit
    # A separately labelled final noiseless closure, including all old checks.
    for id, p in zip(code.check_ids, code.checks):
        outcome = f'closure/{id}'; program.chunk(mpp(p, register), (outcome,))
        corrected = Parity((outcome,))
        if frame is not None and split_mode == 'frame':
            corrected ^= frame_parity(frame, p)
        detector(outcome, corrected ^ last_old[id], 'final_closure', 'noiseless old check equals preceding physical original check')
    # All terminal correlations commute, even though their data Paulis do not.
    for k,(name, p) in enumerate(zip(basis.names, basis.generators)):
        if operation == 'X1' and k == 0:
            joint = p
        else:
            i = k if k < code.k else k-code.k+(operation == 'X1')
            joint = correlation(p, 'X' if k < code.k else 'Z', refs[i], register)
        terminal_paulis.append(joint.to_dict())
        outcome = f'logical_terminal/{name}'
        program.chunk(mpp(joint, register), (outcome,))
        parity = Parity((outcome,))
        if frame is not None and split_mode == 'frame':
            parity ^= frame_parity(frame, p)
        if operation == 'X1' and k == 0:
            detector('target_terminal_consistency', parity ^ measured_target, 'final_closure',
                     'signed vertex product is measured X1; split ports commute with target')
        else:
            scored.append((k, name, parity))
    for k, name, parity in sorted(scored):
        program.mark(name, 'observable', parity, 'logical_action',
                     'known + target measurement' if operation == 'X1' and k == 0 else
                     'encoded Bell correlation with ideal reference, corrected by tracked split frame', k)
    lowered = program.lower()
    certificate = basis.certificate(code)
    certificate['terminal_readout_paulis'] = terminal_paulis
    certificate['physical_parities'] = [{'index':a['observable_index'], 'name':a['name'], 'parity':a['parity']}
                                       for a in lowered.annotations if a['kind'] == 'observable']
    return BenchmarkHarness(lowered.circuit, register, lowered.outcome_ids, lowered.annotations, certificate,
        {'profile':'a7_single_block_independent_boundaries_v1', 'phases':phases,
         'input':'ideal encoded Bell pairs; measured slot in + target eigenstate',
         'physical_last_original_round':'noise-free in this harness',
         'terminal':'ideal commuting original checks and logical/reference Bell correlations',
         'ideal_reference_qubits':list(refs.values()), 'strict_paper_equivalence':False,
         'reset_output_flows': [{'name':id, 'output_pauli':p.to_dict(), 'value':Parity().to_dict()}
                                for id,p in zip(code.check_ids,code.checks)],
         'measured_slot': basis.x[0].to_dict() if operation == 'X1' else None,
         'edge_reset_Z_qubits': list(edges) if operation == 'X1' else [],
         'initial_logical_correlations': [correlation(p,axis,refs[i],register).to_dict()
              for i in refs for p,axis in ((basis.x[i],'X'),(basis.z[i],'Z'))]}, body, split_mode)
