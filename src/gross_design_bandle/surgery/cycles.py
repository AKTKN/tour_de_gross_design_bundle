"""Generic full-cycle oracle; it does not select the paper's measured checks."""
from gross_design_bandle.algebra import gf2
from .graph import AuxiliaryGraph, Cycle


def full_cycle_basis(graph):
    return gf2.readonly(gf2.kernel(graph.incidence))


def omitted_cycle_complement(graph):
    """Independent missing directions, modulo the selected cycles alone."""
    return gf2.readonly(gf2.quotient_basis(full_cycle_basis(graph), graph.cycle_matrix))


def with_full_cycle_basis(graph):
    """Explicit generic profile, never substituted into a reference LPU."""
    cycles = tuple(Cycle(f"oracle:cycle:{i}", tuple(e for e, bit in zip(graph.edge_ids, row) if bit),
                         "generic GF(2) incidence-kernel oracle")
                   for i, row in enumerate(full_cycle_basis(graph)))
    return AuxiliaryGraph(graph.vertices, graph.edges, cycles, "generic_full_cycle_basis", graph.shared_vertex)
