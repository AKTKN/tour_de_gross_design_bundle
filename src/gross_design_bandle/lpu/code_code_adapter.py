"""Module ownership and installed/active Fig. 13(b) connectivity ledgers."""
from collections import Counter, defaultdict
from gross_design_bandle.codes.blocks import CodeBlocks
from gross_design_bandle.circuits.checks import support
from gross_design_bandle.validation.connectivity import installed_connectivity


def adapter_connectivity(protocol):
    df = protocol.deformation
    blocks = CodeBlocks(df.lpu.codes)
    if df.lpu.operation != 'inter_XX':
        raise ValueError('one-to-one inter adapter required')
    owner = {q:c.block_id for c in blocks.codes for q in c.qubit_ids}
    for e in df.graph.edge_ids:
        owners = [c.block_id for c in blocks.codes if e.startswith(c.block_id+':')]
        if len(owners) != 1:
            raise ValueError('auxiliary data lacks unique physical module')
        owner['edge:'+e] = owners[0]
    active_edges, active_nodes, cross = set(), set(protocol.register), []
    for check in protocol.cycle.checks:
        modules = tuple({owner[q] for q in part} for part in check.parts)
        if check.kind == 'bell':
            if modules != tuple({c.block_id} for c in blocks.codes):
                raise ValueError('Bell halves must partition the two physical modules')
            size = 1 if check.id.startswith('vertex:adapter:') else 3
            if any(len(part) != size for part in check.parts):
                raise ValueError('one-to-one identifying / six-edge joint cycle support required')
            cross.append({'id':check.id, 'parts':[list(p) for p in check.parts],
                          'ancillas':list(check.ancillas),
                          'physical_readout_XOR':list(protocol.cycle.readouts()[check.id+'/0'])})
            active_edges.add(tuple(sorted(check.ancillas)))
        elif len(modules[0]) != 1:
            raise ValueError('single check crosses modules without Bell mediation')
        for ancilla,part in zip(check.ancillas,check.parts):
            owner[ancilla] = next(iter({owner[q] for q in part}))
            active_edges.update(tuple(sorted((ancilla,q))) for q in part)
    if any('bridge:triangle' in c.id for c in protocol.cycle.checks):
        raise ValueError('in-module triangular bridge checks must be inactive')
    # Installed full LPUs retain unused half/triangle capability. Joint cycle
    # halves reuse each module's installed bridge-square measurement site.
    installed_edges, installed_nodes = set(), set()
    modules = []
    for c in blocks.codes:
        ledger = installed_connectivity(c); modules.append(ledger)
        installed_nodes.update(ledger['degrees'])
        for q in ledger['degrees']:
            owner[q] = c.block_id
        installed_edges.update(tuple(sorted(e)) for e in ledger['edges'])
    for check in protocol.cycle.checks:
        if check.id.startswith('vertex:adapter:'):
            installed_nodes.update(check.ancillas)
    installed_edges.update(active_edges)
    if not active_nodes <= installed_nodes:
        raise ValueError('active adapter sites are absent from installed layout')
    adjacency = defaultdict(set)
    for a,b in installed_edges:
        adjacency[a].add(b); adjacency[b].add(a)
    degree = {q:len(adjacency[q]) for q in sorted(installed_nodes)}
    if max(degree.values()) > 7:
        raise ValueError('installed inter connectivity exceeds degree seven')
    return {'profile':'fig13b_one_to_one_full_LPU_capability_v1',
            'block_ids':[c.block_id for c in blocks.codes],
            'active_qubits':len(active_nodes), 'installed_qubits':len(installed_nodes),
            'inactive_installed_qubits':sorted(installed_nodes-active_nodes),
            'module_full_LPU_census':[{'total':m['installed_total'],'LPU':m['installed_lpu']} for m in modules],
            'new_identifying_measurement_sites':sum(len(c.ancillas) for c in protocol.cycle.checks if c.id.startswith('vertex:adapter:')),
            'joint_cycle_sites':'reuse installed module bridge-square checks',
            'bridge_data_by_module':{c.block_id:[q for q in owner if q.startswith(f'edge:{c.block_id}:bridge:')] for c in blocks.codes},
            'cross_module_checks':cross, 'owners':owner,
            'active_edges':[list(e) for e in sorted(active_edges)],
            'installed_edges':[list(e) for e in sorted(installed_edges)],
            'installed_degrees':degree,'maximum_installed_degree':max(degree.values()),
            'installed_degree_histogram':dict(sorted(Counter(degree.values()).items())),
            'active_triangular_bridge_checks':0,
            'scope':'two complete installed LPUs plus one-to-one adapter; active graph is smaller; no O3 equivalence claim'}
