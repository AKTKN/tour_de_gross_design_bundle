"""A.5 staged coloring with legal ASAP compaction; fixed BB gate offsets."""
from collections import defaultdict
from functools import lru_cache
from dataclasses import replace
from gross_design_bandle.integrations.sliding_window import adapted_edges
from .checks import Check, support
from .schedule import Op, Schedule, finish_checks, bipartite_layers, overlap_pairs, validate


def physical_checks(deformation):
    df = deformation
    code = df.lpu.codes[0]
    if len(df.lpu.codes)!=1 or df.lpu.operation=='inter_XX':
        raise ValueError('phase04 physical scheduler supports in-module checks only')
    nold = len(code.checks)
    checks = []
    for i,(id,p) in enumerate(zip(df.group.ids,df.group.generators)):
        if i<nold:
            # A dressed X check has Z on auxiliary edges and therefore must use
            # the generic X-ancilla controlled-Pauli primitive.
            checks.append(Check.single(id,p,basis='Z' if i>=code.spec.cells else 'X'))
        elif id == f'vertex:{df.graph.shared_vertex}':
            # The shared algebraic vertex is two physical check qubits. Split
            # its LPU support by the original half, and assign BB port support
            # to the corresponding half. A shared Y lives on the left half.
            left = [q for q in support(p) if q.startswith('edge:') and ':l:' in q]
            from gross_design_bandle.codes.reference_profiles import reference_fixture
            from gross_design_bandle.lpu.reference import label_index
            fixture = reference_fixture(code.spec.name)
            shared_q = code.qubit_ids[label_index(fixture['identified_vertices'][0],code.spec)]
            # The same installed Bell half keeps its fixed BB coupler even
            # when ZX-duality swaps which half's logical port supplies it.
            if shared_q in support(p):
                left.append(shared_q)
            checks.append(Check.bell(id,p,left))
        else:
            checks.append(Check.single(id,p))
    return tuple(checks)


def staged_schedule(deformation):
    df = deformation
    checks = physical_checks(df)
    by_id = {c.id:c for c in checks}
    code = df.lpu.codes[0]
    old_ids = set(code.check_ids)
    bb_data = set(code.qubit_ids)
    raw = []
    phase_log = []
    cursor = 1
    # The first Bell CNOT is at t=1, so its RX/R occupy t=0.
    bell = [Op(cursor,'CX',c.ancillas,c.id,phase='bell_prepare') for c in checks if c.kind=='bell']
    raw += bell
    if bell:
        cursor += 1
    def color_phase(name, candidates):
        nonlocal cursor
        layers = bipartite_layers([(next(a for a in c.ancillas if a in c.interaction(q)[1]),q,(c,q)) for c,q in candidates])
        for layer in layers:
            raw.extend(Op(cursor,*c.interaction(q),c.id,q,phase=name) for c,q in layer)
            cursor += 1
        phase_log.append({'phase':name,'color_layers':len(layers)})
    color_phase('lpu_to_bb',[(c,q) for c in checks if c.id not in old_ids for q in support(c.pauli) if q in bb_data])
    bb_edges,adapter = adapted_edges(code)
    bb_start = cursor-1
    raw.extend(Op(bb_start+t,*by_id[id].interaction(q),id,q,phase='frozen_bb') for t,id,q in bb_edges)
    cursor = bb_start+8
    for axis in ('X','Z'):
        color_phase(f'lpu_internal_{axis}',[(c,q) for c in checks if c.id not in old_ids
                        for q,p in support(c.pauli).items() if q not in bb_data and p==axis])
    color_phase('bb_to_lpu',[(c,q) for c in checks if c.id in old_ids for q in support(c.pauli) if q not in bb_data])
    initial_times = {(o.check_id,o.data_id):o.time for o in raw if o.data_id}
    # Preserve all initial qubit orderings and all Eq. (67) orientations. Group
    # BB gates into seven anchor nodes; chain anchors with unit weight to keep
    # every translated BB edge at the same original offset + Delta_BB.
    groups, op_nodes = {}, {}
    for i,o in enumerate(raw):
        key = ('BB',o.time-bb_start) if o.phase=='frozen_bb' else ('gate',i)
        groups.setdefault(key,[]).append(o)
        op_nodes[o.check_id,o.data_id] = key
    # Empty BB anchor layers still have a clock meaning.
    for t in range(1,8):
        groups.setdefault(('BB',t),[])
    predecessors = {k:{} for k in groups}
    def before(a,b,weight=1):
        if a==b:
            raise ValueError('incompatible same-layer dependency')
        predecessors[b][a] = max(weight,predecessors[b].get(a,0))
    for t in range(1,7):
        before(('BB',t),('BB',t+1))
    by_qubit = defaultdict(list)
    for key,ops in groups.items():
        for o in ops:
            for q in o.qubits:
                by_qubit[q].append((o.time,key))
    for sequence in by_qubit.values():
        sequence.sort()
        for (_,a),(_,b) in zip(sequence,sequence[1:]):
            before(a,b)
    for a,b,overlap in overlap_pairs(checks):
        for q in overlap:
            ak,bk = op_nodes[a.id,q],op_nodes[b.id,q]
            if initial_times[a.id,q]<initial_times[b.id,q]:
                before(ak,bk)
            else:
                before(bk,ak)
    # ASAP respects preparation/readout ticks as well: consecutive interactions
    # of different checks on the SAME physical ancilla cannot happen, since
    # identities are unique. Bell reset->CNOT->interactions is in the same DAG.
    times = {}
    def earliest(k,visiting):
        if k in times:
            return times[k]
        if k in visiting:
            raise ValueError('cyclic schedule constraints')
        times[k] = max([1]+[earliest(p,visiting|{k})+w for p,w in predecessors[k].items()])
        return times[k]
    for k in groups:
        earliest(k,set())
    # A single anchor constant is enforced: predecessors into a later anchor
    # can delay the entire frozen BB block, never just that anchor.
    delta = max(times['BB',t]-t for t in range(1,8))
    for t in range(1,8):
        times['BB',t] = delta+t
    # Recompute non-BB successors after fixing anchors; the staged graph has no
    # later-LPU -> BB dependency beyond phase2, so this cannot move anchors.
    @lru_cache(None)
    def anchored(k):
        if k[0]=='BB':
            return times[k]
        value = max([1]+[anchored(p)+w for p,w in predecessors[k].items()])
        times[k] = value
        return value
    for k in groups:
        anchored(k)
    if any(times[k]<times[p]+w for k,preds in predecessors.items() for p,w in preds.items()):
        raise ValueError('frozen BB timing violates compacted dependency')
    gates = tuple(replace(o,time=times[k]) for k,ops in groups.items() for o in ops)
    ops = finish_checks(checks,gates,phase='deformed')
    schedule = Schedule(df.group.register,checks,ops,max(o.time for o in ops)+1,
                        'tdg_a5_staged_coloring_asap_v1')
    validate(schedule)
    return schedule, {'stages':phase_log,'Delta_BB':delta,'adapter':adapter.to_dict(),
                      'precompaction_gate_depth':max(o.time for o in raw),
                      'deformed_cycle_ticks':schedule.duration,'paper_reported_cycle_ticks':12,
                      'exact_coloring_choice_equivalence':False}
