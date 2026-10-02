"""Real Tanner-edge transfers; named reconstruction, never paper-exact O3.

Two CXs send (|psi>, |b>) to (|b>, X**b |psi>). A Z readout
of the vacated source records its state for reuse, rather than resetting it.
The end-of-cycle X readout followed by Z preparation is a declared one-tick
cross-basis measure/prepare bundle. Its two noise locations remain separate.
"""
from dataclasses import dataclass
from collections import defaultdict
from .memory import memory_schedule
from .schedule import Op
from gross_design_bandle.codes.reference_profiles import physical_shift_permutation

PROFILE = 'gross_B1_B0_x_plus_measure_prepare_v1'
TWO_GROSS_PROFILE = 'two_gross_B1_B0_x_plus_measure_prepare_v1'
TIMING_POLICY = {
    'name': PROFILE,
    'CX_ticks': 1, 'M_ticks': 1, 'RX_ticks': 1,
    'X_check_MX_then_R_ticks': 1,
    'X_check_MX_then_R': 'ordered cross-basis measure/prepare bundle; separate readout and preparation faults',
    'Z_check_initialization': 'reuse stage-2 Z projection with recorded X frame; no hidden reset',
    'initial_check_R_ticks': 1,
    'paper_exact': False,
}


def reconstruction_profile(code, profile=None):
    expected = {'gross': PROFILE, 'two_gross': TWO_GROSS_PROFILE}.get(code.spec.name)
    if expected is None or profile not in (None, expected):
        raise ValueError('unknown reconstruction profile; paper-exact shift unresolved O3')
    return expected


def timing_policy(profile):
    return {**TIMING_POLICY, 'name': profile}


@dataclass(frozen=True)
class TransferPlan:
    register: tuple
    data: tuple
    first: tuple  # (original data site, check site)
    second: tuple  # (check site, output data site), aligned with first
    target_to_source: tuple
    delta: tuple
    profile: str

    def validate(self, code):
        if self.register != memory_schedule(code).register or self.data != code.qubit_ids:
            raise ValueError('shift register mismatch')
        n = len(self.data)
        if len(self.first) != n or len(self.second) != n:
            raise ValueError('missing transfer pair')
        anc = set(self.register[n:])
        if (tuple(a for a,b in self.first) != self.data or
            set(b for a,b in self.first) != anc or
            len(set(b for a,b in self.first)) != n or
            tuple(a for a,b in self.second) != tuple(b for a,b in self.first) or
            set(b for a,b in self.second) != set(self.data)):
            raise ValueError('transfer stages are not bijective data/check role changes')
        owner = {f'anc:{id}':p for id,p in zip(code.check_ids,code.checks)}
        for source,check in self.first:
            p = owner[check]; q = self.data.index(source)
            if not (p.x[q] or p.z[q]):
                raise ValueError('first transfer is not a Tanner edge')
        for check,destination in self.second:
            p = owner[check]; q = self.data.index(destination)
            if not (p.x[q] or p.z[q]):
                raise ValueError('second transfer is not a Tanner edge')
        actual = [None]*n
        for (source,_),(_,dest) in zip(self.first,self.second):
            actual[self.data.index(dest)] = self.data.index(source)
        if tuple(actual) != self.target_to_source or self.target_to_source != physical_shift_permutation(code.spec,*self.delta):
            raise ValueError('transfer permutation disagrees with oracle')
        return {'Tanner_edges':2*n, 'bijective_roles':True, 'physical_permutation_verified':True}

    def to_dict(self):
        return {'profile':self.profile, 'delta':self.delta, 'target_to_source':self.target_to_source,
                'first':self.first, 'second':self.second, 'register':self.register,
                'scope':'physical routing reconstruction; O3 open'}


def transfer_plan(code, *, profile=None):
    profile = reconstruction_profile(code, profile)
    s = code.spec; bi,bj = s.B[1],s.B[0]
    delta = (bi[0]-bj[0],bi[1]-bj[1])
    first,second = [],[]
    for side in ('L','R'):
        for i in range(s.ell):
            for j in range(s.m):
                source = code.qubit_ids[s.qubit_index(side,i,j)]
                # L uses Z (minus B); R uses X (plus B).
                cx,cy = (i+bi[0],j+bi[1]) if side=='L' else (i-bj[0],j-bj[1])
                sector = 'Z' if side=='L' else 'X'
                check = f'anc:{code.block_id}:{sector}:{cx%s.ell}:{cy%s.m}'
                dest = code.qubit_ids[s.qubit_index(side,i+delta[0],j+delta[1])]
                first.append((source,check)); second.append((check,dest))
    out = TransferPlan(memory_schedule(code).register,code.qubit_ids,tuple(first),tuple(second),
                       physical_shift_permutation(s,*delta),delta,profile)
    out.validate(code)
    return out


def two_cnot_ops(pairs, start, *, phase, round=0):
    pairs = tuple(pairs)
    if len(set(q for pair in pairs for q in pair)) != 2*len(pairs):
        raise ValueError('transfer pairs collide')
    return tuple(Op(start+k,'CX',(a,b) if k==0 else (b,a),phase=phase,round=round)
                 for k in range(2) for a,b in pairs)


@dataclass(frozen=True)
class ShiftSequence:
    plan: TransferPlan
    instructions: int
    ops: tuple
    duration: int

    @property
    def register(self):
        return self.plan.register

    def ordered_ops(self):
        # Tuple order is meaningful for the declared MX/R bundle.
        return tuple(sorted(self.ops,key=lambda o:o.time))

    @property
    def outcomes(self):
        return tuple(o.outcome_id for o in self.ordered_ops() if o.outcome_id)

    def validate(self):
        busy = defaultdict(list)
        ids = []
        for o in self.ordered_ops():
            if o.time >= self.duration or any(q not in self.register for q in o.qubits):
                raise ValueError('shift operation outside physical ledger')
            for q in o.qubits:
                busy[o.time,q].append(o.gate)
            if o.outcome_id:
                ids.append(o.outcome_id)
        for (t,q),gates in busy.items():
            if len(gates)>1 and not (gates==['MX','R'] and t%14==0 and t>0 and ':X:' in q):
                raise ValueError('shift qubit collision outside declared measure/prepare bundle')
        if len(set(ids)) != len(ids):
            raise ValueError('duplicate shift outcome')
        return {'collision_free_except_declared_bundle':True, 'duration_ticks':self.duration,
                'instruction_ticks':14, 'initialization_ticks':1}

    def to_stim(self):
        import stim
        self.validate()
        c = stim.Circuit(); index = {q:i for i,q in enumerate(self.register)}
        by = defaultdict(list)
        for o in self.ordered_ops(): by[o.time].append(o)
        for t in range(self.duration):
            for o in by[t]: c.append(o.gate,[index[q] for q in o.qubits])
            c.append('TICK')
        return c

    def role_at(self, q, t):
        if q not in self.register or type(t) is not int or t not in range(self.duration):
            raise ValueError('invalid instantaneous role query')
        if t==0: return 'BB_data' if q in self.plan.data else 'check_zero_preparation'
        local = (t-1)%14
        data = q in self.plan.data
        if local<2: return 'transfer_1_source' if data else 'transfer_1_destination'
        if local==2: return 'vacated_data_readout' if data else 'code_data_on_check'
        if local<5: return 'transfer_2_destination' if data else 'transfer_2_source'
        if local==5: return 'BB_data' if data else 'vacated_check_readout'
        return 'BB_data' if data else 'syndrome_ancilla'

    def ledger(self):
        # Every site is live: vacated sites are reused with recorded X frames.
        busy = {(o.time,q) for o in self.ops for q in o.qubits}
        return {'idle_locations':[(q,t) for t in range(self.duration) for q in self.register if (t,q) not in busy],
                'installed_qubits':len(self.register), 'live_sites':[0,self.duration],
                'timing':self.validate(), 'policy':timing_policy(self.plan.profile)}


def shift_sequence(code, instructions=10, *, profile=None):
    if type(instructions) is not int or instructions<1:
        raise ValueError('instructions must be a positive integer')
    plan = transfer_plan(code,profile=profile); memory = memory_schedule(code)
    ops = [Op(0,'R',(a,),phase='shift_initialize') for a in plan.register[len(plan.data):]]
    for r in range(instructions):
        base = 1+14*r
        for stage,pairs in enumerate((plan.first,plan.second),1):
            phase = f'transfer_{stage}'; start = base+3*(stage-1)
            ops.extend(two_cnot_ops(pairs,start,phase=phase,round=r))
            ops.extend(Op(start+2,'M',(a,),outcome_id=f'shift/{r}/{phase}/{a}',phase=phase,round=r) for a,b in pairs)
        # Stage-2 Z measurement at base+5 prepares Z check ancillas up to X
        # frame. Inherit every ordinary Fig4b CNOT at time+base+5.
        for o in memory.ordered_ops():
            if o.gate=='R': continue
            time = base+5+o.time
            outcome = f'shift/{r}/syndrome/{o.check_id}' if o.outcome_id else None
            ops.append(Op(time,o.gate,o.qubits,o.check_id,o.data_id,outcome,
                          phase='following_syndrome',round=r))
            if o.gate=='MX':
                ops.append(Op(time,'R',o.qubits,o.check_id,phase='following_syndrome',round=r))
    out = ShiftSequence(plan,instructions,tuple(ops),1+14*instructions)
    out.validate()
    return out
