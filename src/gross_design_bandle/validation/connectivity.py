"""Installed full-LPU connectivity: both X and ZX-dual port/dressing options."""
from collections import Counter,defaultdict
from dataclasses import replace
from gross_design_bandle.algebra.pauli import Pauli
from gross_design_bandle.codes.reference_profiles import reference_fixture
from gross_design_bandle.lpu.reference import build_reference_lpu,dual_index
from gross_design_bandle.surgery.ports import PortMap,product
from gross_design_bandle.surgery.deformation import compile_deformation
from gross_design_bandle.circuits.surgery import physical_checks
from gross_design_bandle.circuits.checks import support


def installed_connectivity(code):
    lpu = build_reference_lpu(code,'XX')
    fixture = reference_fixture(code.spec.name)
    ports = []
    for p in lpu.ports.ports:
        word = ['I']*code.spec.n
        for i,bit in enumerate(p.x):
            if bit:
                word[dual_index(i,code.spec,fixture['dual_shift'])]='Z'
        ports.append(Pauli.from_word(''.join(word),code.qubit_ids))
    dual = replace(lpu,ports=PortMap(lpu.graph.vertices,tuple(ports),(code.block_id,),product(ports,code.qubit_ids)))
    implementations = [physical_checks(compile_deformation(profile)) for profile in (lpu,dual)]
    adjacency = defaultdict(set)
    nodes = set(code.qubit_ids)
    for checks in implementations:
        for c in checks:
            nodes.update(c.ancillas)
            nodes.update(c.pauli.qubit_ids)
            for q in support(c.pauli):
                a = next(a for a,part in zip(c.ancillas,c.parts) if q in part)
                adjacency[a].add(q); adjacency[q].add(a)
            if c.kind=='bell':
                a,b=c.ancillas
                adjacency[a].add(b); adjacency[b].add(a)
    degree = {q:len(adjacency[q]) for q in sorted(nodes)}
    lpu_nodes = nodes-set(code.qubit_ids)-{f'anc:{id}' for id in code.check_ids}
    expected = fixture['expected_full_graph']['physical_lpu_qubits']
    if len(lpu_nodes)!=expected or max(degree.values())>7:
        raise ValueError('installed full-LPU connectivity census violates Fig. 5')
    shared = next(c for c in implementations[0] if c.kind=='bell')
    if any(degree[a]!=5 for a in shared.ancillas):
        raise ValueError('installed shared Bell sides must each have degree five')
    return {'installed_total':len(nodes),'installed_lpu':len(lpu_nodes),'maximum_degree':max(degree.values()),
            'bell_couplers':[list(shared.ancillas)],'bell_half_degrees':[degree[a] for a in shared.ancillas],
            'degree_histogram':dict(sorted(Counter(degree.values()).items())),
            'lpu_degree_histogram':dict(sorted(Counter(degree[q] for q in lpu_nodes).items())),
            'degrees':degree,'edges':[list((q,r)) for q in sorted(nodes) for r in sorted(adjacency[q]) if q<r],
            'scope':'installed connectivity union of X ports and ZX-dual Z ports; includes inactive couplers'}
