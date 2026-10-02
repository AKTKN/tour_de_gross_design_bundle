"""Noiseless physical in-module bodies; encoding is a separate ideal harness."""
from dataclasses import dataclass, replace
from collections import Counter, defaultdict
from gross_design_bandle.surgery.frame import Parity, build_split_frame
from .schedule import Op, Schedule
from .surgery import staged_schedule
from .memory import memory_schedule


@dataclass(frozen=True)
class PhysicalProtocol:
    deformation: object
    cycle: Schedule
    rounds: int
    split: tuple[Op,...]
    terminal: Schedule
    schedule_metadata: dict

    @property
    def register(self):
        # Original memory ancillas reuse the same physical BB check identities.
        return self.cycle.register

    @property
    def frame(self):
        return build_split_frame(self.deformation.graph,self.deformation.lpu.ports,
                                 tuple(o.outcome_id for o in self.split))

    @property
    def logical_outcome(self):
        ids = self.cycle.readouts()
        return Parity(tuple(outcome for v in self.deformation.graph.vertices
                            for outcome in ids[f'vertex:{v}/0']))

    @property
    def timing(self):
        return {'edge_initialization':1,'deformed_cycle':self.cycle.duration,
                'deformed_rounds':self.rounds,'deformed_body':self.rounds*self.cycle.duration,
                'edge_split':1,'original_check_verification':self.terminal.duration,
                'input_terminal_harness':0,
                'total':2+self.rounds*self.cycle.duration+self.terminal.duration}

    def outcomes(self):
        return tuple(i.replace('deformed/0/','deformed/'+str(r)+'/')
                     for r in range(self.rounds) for i in self.cycle.outcomes)+tuple(o.outcome_id for o in self.split)+self.terminal.outcomes

    def to_stim(self):
        import stim
        result = stim.Circuit()
        index = {q:i for i,q in enumerate(self.register)}
        edges = self.cycle.data[len(self.deformation.lpu.ports.target.qubit_ids):]
        result.append('R',[index[q] for q in edges]); result.append('TICK')
        result += self.rounds*self.cycle.to_stim()
        for op in self.split:
            result.append('M',[index[op.qubits[0]]])
        result.append('TICK')
        # Remap the independent original-memory fragment onto reused BB sites.
        for instruction in self.terminal.to_stim():
            targets = [stim.target_inv(index[self.terminal.register[t.value]]) if t.is_inverted_result_target
                       else index[self.terminal.register[t.value]] for t in instruction.targets_copy()]
            result.append(instruction.name,targets,instruction.gate_args_copy())
        return result

    def complete_ops(self):
        offset = 1
        ops = [Op(0,'R',(q,),phase='edge_initialize')
               for q in self.cycle.data[len(self.deformation.lpu.ports.target.qubit_ids):]]
        for r in range(self.rounds):
            ops += [replace(o,time=o.time+offset,round=r,
                    outcome_id=o.outcome_id.replace('deformed/0/',f'deformed/{r}/') if o.outcome_id else None)
                    for o in self.cycle.ordered_ops()]
            offset += self.cycle.duration
        ops += [replace(o,time=offset) for o in self.split]
        offset += 1
        ops += [replace(o,time=o.time+offset,phase='original_check_verification') for o in self.terminal.ordered_ops()]
        return tuple(ops)

    def ledger(self):
        ops = self.complete_ops()
        busy = {(o.time,q) for o in ops for q in o.qubits}
        if len(busy) != sum(len(o.qubits) for o in ops):
            raise ValueError('protocol boundary qubit collision')
        total = self.timing['total']
        data = self.deformation.lpu.ports.target.qubit_ids
        edges = self.cycle.data[len(data):]
        split_end = 2+self.rounds*self.cycle.duration
        intervals = {q:[0,total if q in data else split_end] for q in self.cycle.data}
        anc_intervals = []
        for q in self.register[len(self.cycle.data):]:
            starts = sorted(o.time for o in ops if o.qubits==(q,) and o.gate in ('R','RX'))
            ends = sorted(o.time+1 for o in ops if o.qubits==(q,) and o.outcome_id)
            if len(starts)!=len(ends) or any(s>=e for s,e in zip(starts,ends)):
                raise ValueError('incomplete protocol ancilla lifetime')
            anc_intervals += [(q,s,e) for s,e in zip(starts,ends)]
        idles = [(q,t) for q,(s,e) in intervals.items() for t in range(s,e) if (t,q) not in busy]
        idles += [(q,t) for q,s,e in anc_intervals for t in range(s,e) if (t,q) not in busy]
        # Label every tick, including inactive data idles at phase boundaries.
        phases = {0:'edge_initialize',split_end-1:'split'}
        phases.update({t:'deformed' for t in range(1,split_end-1)})
        phases.update({t:'original_check_verification' for t in range(split_end,total)})
        counts = Counter(o.gate for o in ops); counts['IDLE']=len(idles)
        by_phase = defaultdict(Counter)
        for o in ops:
            by_phase[phases[o.time]][o.gate]+=1
        for q,t in idles:
            by_phase[phases[t]]['IDLE']+=1
        return {'installed_qubits':len(self.register),'active_qubits':len({q for o in ops for q in o.qubits}),
                'live_data_intervals':intervals,'live_ancilla_intervals':anc_intervals,
                'idle_locations':idles,'locations_by_kind':dict(counts),
                'locations_by_phase':{p:dict(c) for p,c in by_phase.items()},
                'bell_couplers':self.cycle.ledger()['bell_couplers'],
                'policy':self.cycle.policy,'fault_catalogue_complete':False,
                'edge_data_inactive_after_split':list(edges)}

    def to_dict(self):
        return {'schema_version':1,'scope':'physical noiseless in-module instrument; no detectors or benchmark scoring',
                'operation':self.deformation.lpu.operation,
                'register':list(self.register),'timing':self.timing,'cycle_hash':self.cycle.hash,
                'cycle':self.cycle.to_dict(),'schedule_metadata':self.schedule_metadata,
                'terminal_memory':self.terminal.to_dict(), 'complete_operations':[o.to_dict() for o in self.complete_ops()],
                'complete_location_ledger':self.ledger(),
                'physical_outcomes':list(self.outcomes()),'algebraic_readouts':self.cycle.readouts(),
                'logical_outcome':self.logical_outcome.to_dict(),'split_frame':self.frame.to_dict(),
                'input_contract':'encoded data supplied externally; auxiliary edge qubits reset here',
                'noise_emitted':False,'decoder_invoked':False}


def build_physical_x1(deformation,rounds=1):
    if deformation.lpu.operation!='X' or len(deformation.lpu.codes)!=1:
        raise ValueError('phase04 complete physical instrument is X1 only')
    return build_physical_inmodule(deformation,rounds)


def build_physical_inmodule(deformation,rounds=10):
    """Direct signed X1, X1*X7 or Y1 measurement on one fixed LPU.

    C=10 is the gross reference choice. Other positive counts are explicit
    construction/debug profiles, not the published gross configuration.
    """
    if deformation.lpu.operation not in ('X','XX','Y') or len(deformation.lpu.codes)!=1:
        raise ValueError('physical in-module instrument requires one X/XX/Y block')
    if not isinstance(rounds,int) or isinstance(rounds,bool) or rounds<1:
        raise ValueError('round count must be positive integer')
    cycle,metadata = staged_schedule(deformation)
    split = tuple(Op(0,'M',(q,),outcome_id=f'split/{e}',phase='split')
                  for e,q in zip(deformation.graph.edge_ids,cycle.data[len(deformation.lpu.ports.target.qubit_ids):]))
    return PhysicalProtocol(deformation,cycle,rounds,split,memory_schedule(deformation.lpu.codes[0]),metadata)
