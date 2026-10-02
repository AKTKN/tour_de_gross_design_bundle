"""Ideal split frame with absolute edge-outcome IDs; no noisy decoding policy."""
from dataclasses import dataclass

import numpy as np

from gross_design_bandle.algebra import gf2
from .ports import product


@dataclass(frozen=True)
class Parity:
    ids: tuple[str, ...] = ()
    constant: int = 0

    def __post_init__(self):
        object.__setattr__(self, "ids", tuple(self.ids))
        if len(set(self.ids)) != len(self.ids) or any(not isinstance(i, str) or not i for i in self.ids):
            raise ValueError("parity IDs must be distinct nonempty strings")
        gf2.binary([self.constant], 1)

    def __xor__(self, other):
        return Parity(tuple(sorted(set(self.ids) ^ set(other.ids))), self.constant ^ other.constant)

    def evaluate(self, outcomes):
        if not self.ids:
            return self.constant
        try:
            bits = gf2.binary([outcomes[i] for i in self.ids], 1)
        except KeyError as exc:
            raise ValueError(f"missing symbolic outcome {exc.args[0]}") from exc
        return (int(bits.sum()) + self.constant) % 2

    def to_dict(self):
        return {"ids": list(self.ids), "constant": self.constant}


@dataclass(frozen=True)
class SplitFrame:
    graph: object
    ports: object
    root: str
    edge_outcome_ids: tuple[str, ...]
    terms: tuple[Parity, ...]
    tree_edge_ids: tuple[str, ...]

    def evaluate(self, outcomes):
        t = np.array([term.evaluate(outcomes) for term in self.terms], dtype=np.uint8)
        z = np.array([Parity((i,)).evaluate(outcomes) for i in self.edge_outcome_ids], dtype=np.uint8)
        if not np.array_equal(gf2.matmul(self.graph.incidence.T, t[:, None])[:, 0], z):
            raise ValueError("edge readout is not a cut: unresolved cycle parity; ideal frame only")
        q = product((p for p, bit in zip(self.ports.ports, t) if bit), self.ports.target.qubit_ids)
        return tuple(map(int, t)), q

    def to_dict(self):
        return {"root": self.root, "tree_edge_ids": list(self.tree_edge_ids),
                "edge_outcome_ids": list(self.edge_outcome_ids),
                "terms": [{"vertex_id": v, "parity": term.to_dict(), "pauli": p.to_dict()}
                          for v, term, p in zip(self.graph.vertices, self.terms, self.ports.ports)]}


def build_split_frame(graph, ports, edge_outcome_ids, root=None, tree_edge_ids=None):
    """Solve B^T t=z symbolically along an explicit rooted spanning tree.

    Evaluation checks *all* edges, including chords. Raw noisy readouts cannot
    be passed off as corrected cut data. The root component is fixed to zero.
    """
    if graph.vertices != ports.vertices:
        raise ValueError("graph/port vertex ordering differs")
    ids = tuple(edge_outcome_ids)
    if len(ids) != len(graph.edges) or len(set(ids)) != len(ids) or any(not i for i in ids):
        raise ValueError("edge outcome IDs differ")
    root = graph.vertices[0] if root is None else root
    if root not in graph.vertices:
        raise ValueError("unknown frame root")
    if tree_edge_ids is None:
        seen, chosen = {root}, []
        while len(seen) < len(graph.vertices):
            edge = next(e for e in graph.edges if (e.endpoints[0] in seen) != (e.endpoints[1] in seen))
            chosen.append(edge.id)
            seen.update(edge.endpoints)
        tree_edge_ids = tuple(chosen)
    tree = tuple(tree_edge_ids)
    if len(tree) != len(graph.vertices)-1 or len(set(tree)) != len(tree) or not set(tree) <= set(graph.edge_ids):
        raise ValueError("invalid spanning tree edge IDs")
    terms = {root: Parity()}
    pending = [e for e in graph.edges if e.id in tree]
    edge_ids = dict(zip(graph.edge_ids, ids))
    while pending:
        candidates = [e for e in pending if (e.endpoints[0] in terms) != (e.endpoints[1] in terms)]
        if not candidates:
            raise ValueError("spanning tree is disconnected or cyclic")
        edge = candidates[0]
        u, v = edge.endpoints
        if v in terms:
            u, v = v, u
        terms[v] = terms[u] ^ Parity((edge_ids[edge.id],))
        pending.remove(edge)
    return SplitFrame(graph, ports, root, ids, tuple(terms[v] for v in graph.vertices), tree)
