"""Integer-time physical IR, bipartite coloring and Eq. (65)--(67) checks."""
from collections import Counter, defaultdict
from dataclasses import dataclass, asdict
import json
from hashlib import sha256
from .checks import support

POLICY = {'name': 'native_controlled_pauli_v1', 'RX_MX_R_M_ticks': 1,
          'CX_CY_CZ_ticks': 1, 'basis_conversion': 'native; no free inserted Clifford gates',
          'idle_policy': 'every unoccupied live data or prepared ancilla tick',
          'noise': 'location candidates only; no stochastic channel emitted in phase04'}


@dataclass(frozen=True)
class Op:
    time: int
    gate: str
    qubits: tuple[str, ...]
    check_id: str | None = None
    data_id: str | None = None
    outcome_id: str | None = None
    invert: bool = False
    phase: str = 'body'
    round: int = 0

    def __post_init__(self):
        if isinstance(self.time, bool) or not isinstance(self.time, int) or self.time < 0:
            raise ValueError('time must be a nonnegative integer')
        arity = {'RX':1,'R':1,'MX':1,'M':1,'CX':2,'CZ':2,'CY':2}.get(self.gate)
        if arity is None or len(self.qubits) != arity or len(set(self.qubits)) != arity:
            raise ValueError('invalid physical operation')
        if (self.gate in ('MX','M')) != (self.outcome_id is not None):
            raise ValueError('readout must have an absolute outcome ID')

    def to_dict(self):
        return asdict(self)


@dataclass(frozen=True)
class Schedule:
    data: tuple[str, ...]
    checks: tuple
    ops: tuple[Op, ...]
    duration: int
    profile: str
    policy: dict | None = None

    def __post_init__(self):
        if self.policy is None:
            object.__setattr__(self, 'policy', dict(POLICY))
        if not isinstance(self.duration,int) or self.duration < 1 or any(o.time >= self.duration for o in self.ops):
            raise ValueError('operations outside duration')
        if len(set(self.register)) != len(self.register) or len({c.id for c in self.checks}) != len(self.checks):
            raise ValueError('duplicate physical or algebraic identities')
        if any(set(c.pauli.qubit_ids) != set(self.data) for c in self.checks):
            raise ValueError('check and schedule data registers differ')

    @property
    def register(self):
        return self.data + tuple(a for c in self.checks for a in c.ancillas)

    def ordered_ops(self):
        return tuple(sorted(self.ops, key=lambda o:(o.time, o.check_id or '', o.qubits)))

    def to_dict(self):
        return {'schema_version':1,'profile':self.profile,'duration':self.duration,
                'data':list(self.data),'register':list(self.register),'policy':self.policy,
                'checks':[c.to_dict() for c in self.checks], 'ops':[o.to_dict() for o in self.ordered_ops()],
                'ledger':self.ledger()}

    @property
    def hash(self):
        return sha256(json.dumps(self.to_dict(),sort_keys=True,separators=(',',':')).encode()).hexdigest()

    def to_stim(self):
        import stim
        validate(self)
        if self.policy != POLICY:
            raise ValueError('unsupported physical basis/noise policy; new lowering and fingerprint required')
        circuit = stim.Circuit()
        index = {q:i for i,q in enumerate(self.register)}
        by_time = defaultdict(list)
        for op in self.ordered_ops():
            by_time[op.time].append(op)
        for time in range(self.duration):
            for op in by_time[time]:
                targets = [index[q] for q in op.qubits]
                if op.invert:
                    targets[0] = stim.target_inv(targets[0])
                circuit.append(op.gate, targets)
            circuit.append('TICK')
        return circuit

    @property
    def outcomes(self):
        return tuple(o.outcome_id for o in self.ordered_ops() if o.outcome_id)

    def readouts(self):
        # Sort once, rather than once per check and round on a large LPU.
        rounds, outcomes = defaultdict(set), defaultdict(list)
        for o in self.ordered_ops():
            rounds[o.check_id].add(o.round)
            if o.outcome_id:
                outcomes[o.check_id, o.round].append(o.outcome_id)
        return {f'{c.id}/{r}': tuple(outcomes[c.id, r])
                for c in self.checks for r in sorted(rounds[c.id])}

    def ledger(self):
        """Candidate locations, not O4 primitive multiplicities or Table-6 N."""
        busy = {(o.time,q) for o in self.ops for q in o.qubits}
        intervals = {q:[0,self.duration] for q in self.data}
        anc_intervals = []
        for q in self.register[len(self.data):]:
            starts = sorted(o.time for o in self.ops if q in o.qubits and o.gate in ('R','RX'))
            ends = sorted(o.time+1 for o in self.ops if q in o.qubits and o.gate in ('M','MX'))
            if len(starts) != len(ends):
                raise ValueError('unmatched ancilla live intervals')
            anc_intervals += [(q,s,e) for s,e in zip(starts,ends)]
        idles = [(q,t) for q,(s,e) in intervals.items() for t in range(s,e) if (t,q) not in busy]
        idles += [(q,t) for q,s,e in anc_intervals for t in range(s,e) if (t,q) not in busy]
        counts = Counter(o.gate for o in self.ops)
        counts['IDLE'] = len(idles)
        bell = {(c.ancillas[0],c.ancillas[1]) for c in self.checks if c.kind == 'bell'}
        return {'installed_qubits':len(self.register), 'active_qubits':len({q for o in self.ops for q in o.qubits}),
                'live_data_intervals':intervals,'live_ancilla_intervals':anc_intervals,
                'idle_locations':idles,'locations_by_kind':dict(sorted(counts.items())),
                'bell_couplers':sorted(bell),'bell_preparations':sum(o.gate=='CX' and o.data_id is None for o in self.ops),
                'fault_catalogue_complete':False}


def collision_check(schedule):
    occupied = set()
    register = set(schedule.register)
    for op in schedule.ops:
        if any(q not in register for q in op.qubits):
            raise ValueError('unknown physical qubit')
        for q in op.qubits:
            if (op.time,q) in occupied:
                raise ValueError(f'qubit collision at {op.time}: {q}')
            occupied.add((op.time,q))


def overlap_pairs(checks):
    supports = tuple(support(c.pauli) for c in checks)
    for i,a in enumerate(checks):
        sa = supports[i]
        for j,b in enumerate(checks[:i]):
            sb = supports[j]
            overlap = tuple(q for q in sa.keys() & sb.keys() if sa[q] != sb[q])
            if len(overlap) % 2:
                raise ValueError(f'noncommuting algebraic checks: {a.id}, {b.id}')
            if overlap:
                yield a,b,overlap


def validate(schedule):
    collision_check(schedule)
    ids = [o.outcome_id for o in schedule.ops if o.outcome_id]
    if len(ids) != len(set(ids)):
        raise ValueError('duplicate physical outcome IDs')
    rounds = sorted({o.round for o in schedule.ops})
    times = {}
    by_id = {c.id:c for c in schedule.checks}
    supports = {c.id:support(c.pauli) for c in schedule.checks}
    for op in schedule.ops:
        if op.check_id not in by_id:
            raise ValueError('unowned physical operation')
        owner = by_id[op.check_id]
        if op.data_id is None:
            if len(op.qubits)==2:
                if owner.kind!='bell' or op.gate!='CX' or op.qubits!=owner.ancillas:
                    raise ValueError('unowned Bell or check interaction')
            elif op.qubits[0] not in owner.ancillas:
                raise ValueError('preparation/readout targets wrong physical ancilla')
        if op.data_id is not None:
            if op.check_id not in by_id or op.data_id not in supports[op.check_id]:
                raise ValueError('unknown check interaction')
            check = by_id[op.check_id]
            if (op.gate,op.qubits) != check.interaction(op.data_id):
                raise ValueError('wrong controlled Pauli or physical ancilla')
            key = (op.round,op.check_id,op.data_id)
            if key in times:
                raise ValueError('duplicate check interaction')
            times[key] = op.time
    overlaps = 0
    for r in rounds:
        for c in schedule.checks:
            ops = [o for o in schedule.ops if o.round == r and o.check_id == c.id]
            if not ops:
                raise ValueError('missing check round')
            for q in supports[c.id]:
                if (r,c.id,q) not in times:
                    raise ValueError('missing check support interaction')
            preparations = [o for o in ops if o.data_id is None and o.gate == 'CX']
            if c.kind == 'bell':
                if len(preparations)!=1 or preparations[0].qubits != c.ancillas:
                    raise ValueError('missing Bell preparation')
                if any(preparations[0].time >= times[r,c.id,q] for q in support(c.pauli)):
                    raise ValueError('Bell preparation must precede both halves')
            elif preparations:
                raise ValueError('unexpected Bell preparation')
            for i,a in enumerate(c.ancillas):
                resets = [o for o in ops if o.gate in ('R','RX') and o.qubits == (a,)]
                reads = [o for o in ops if o.gate in ('M','MX') and o.qubits == (a,)]
                expected_reset = 'R' if c.basis == 'Z' or c.kind == 'bell' and i==1 else 'RX'
                expected_read = 'M' if c.basis == 'Z' else 'MX'
                if len(resets)!=1 or len(reads)!=1 or resets[0].gate!=expected_reset or reads[0].gate!=expected_read or reads[0].invert != (c.negative and i==0):
                    raise ValueError('invalid check preparation/readout/sign')
                gates = [o.time for o in ops if len(o.qubits)==2 and a in o.qubits]
                if gates and not (resets[0].time < min(gates) <= max(gates) < reads[0].time):
                    raise ValueError('invalid ancilla lifecycle')
                if not gates and resets[0].time >= reads[0].time:
                    raise ValueError('invalid identity-check lifecycle')
        for a,b,overlap in overlap_pairs(schedule.checks):
            product = 1
            for q in overlap:
                product *= times[r,a.id,q]-times[r,b.id,q]
            if product <= 0:
                raise ValueError(f'Eq. (67) anticommuting overlap ordering: {a.id}, {b.id}, {overlap}')
            overlaps += 1
    return {'collision_free':True,'physical_checks_complete':True,'bell_precedes_interactions':True,
            'eq67_overlap_pairs':overlaps}


def bipartite_layers(edges):
    """Optimal Delta coloring via regular multigraph completion/perfect matchings.

    Edges are (physical ancilla, data, payload). Dummy edges are discarded. No
    ILP, external coloring library or mutation of the scientific cycle basis.
    """
    edges = tuple(edges)
    if not edges:
        return ()
    left = list(dict.fromkeys(e[0] for e in edges))
    right = list(dict.fromkeys(e[1] for e in edges))
    size = max(len(left),len(right))
    li,ri = {q:i for i,q in enumerate(left)}, {q:i for i,q in enumerate(right)}
    remaining = [(li[a],ri[b],payload) for a,b,payload in edges]
    lc,rc = Counter(a for a,b,p in remaining), Counter(b for a,b,p in remaining)
    degree = max(max(lc.values()),max(rc.values()))
    ld = [degree-lc[i] for i in range(size)]
    rd = [degree-rc[i] for i in range(size)]
    j = 0
    for i in range(size):
        while ld[i]:
            while not rd[j]:
                j += 1
            remaining.append((i,j,None)); ld[i]-=1; rd[j]-=1
    layers = []
    for _ in range(degree):
        adjacency = defaultdict(list)
        for index,(a,b,p) in enumerate(remaining):
            adjacency[a].append((b,index))
        matching = {}
        def augment(a,seen):
            for b,index in adjacency[a]:
                if b in seen:
                    continue
                seen.add(b)
                if b not in matching or augment(remaining[matching[b]][0],seen):
                    matching[b] = index
                    return True
            return False
        for a in range(size):
            if not augment(a,set()):
                raise ValueError('regular bipartite graph lacks perfect matching')
        chosen = set(matching.values())
        layers.append(tuple(remaining[i][2] for i in sorted(chosen) if remaining[i][2] is not None))
        remaining = [e for i,e in enumerate(remaining) if i not in chosen]
    assert not remaining
    return tuple(layers)


def finish_checks(checks, gates, *, round=0, phase='body'):
    """Ancilla reset as late as possible; readout as early as possible."""
    ops = list(gates)
    for c in checks:
        for i,a in enumerate(c.ancillas):
            times = [o.time for o in gates if o.check_id==c.id and a in o.qubits]
            start,end = (min(times)-1,max(times)+1) if times else (0,1)
            reset = 'R' if c.basis=='Z' or c.kind=='bell' and i==1 else 'RX'
            read = 'M' if c.basis=='Z' else 'MX'
            ops += [Op(start,reset,(a,),c.id,phase=phase,round=round),
                    Op(end,read,(a,),c.id,outcome_id=f'{phase}/{round}/{c.id}/{i}',
                       invert=c.negative and i==0,phase=phase,round=round)]
    return tuple(ops)
