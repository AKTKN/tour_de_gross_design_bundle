"""Immutable edge-ID graphs. Parallel edges are legal and never conflated."""
from dataclasses import dataclass

import numpy as np

from gross_design_bandle.algebra import gf2
from gross_design_bandle.codes.bb import stable_id


@dataclass(frozen=True)
class Edge:
    id: str
    endpoints: tuple[str, str]
    source: str

    def __post_init__(self):
        object.__setattr__(self, "endpoints", tuple(self.endpoints))
        if not self.id or not self.source or len(self.endpoints) != 2 or self.endpoints[0] == self.endpoints[1]:
            raise ValueError("invalid edge ID/source/endpoints")


@dataclass(frozen=True)
class Cycle:
    id: str
    edge_ids: tuple[str, ...]
    source: str

    def __post_init__(self):
        object.__setattr__(self, "edge_ids", tuple(self.edge_ids))
        if not self.id or not self.source or not self.edge_ids or len(set(self.edge_ids)) != len(self.edge_ids):
            raise ValueError("invalid cycle ID/source/edge set")


@dataclass(frozen=True)
class AuxiliaryGraph:
    vertices: tuple[str, ...]
    edges: tuple[Edge, ...]
    cycles: tuple[Cycle, ...]
    profile: str
    shared_vertex: str | None = None

    def __post_init__(self):
        for field in ("vertices", "edges", "cycles"):
            object.__setattr__(self, field, tuple(getattr(self, field)))
        for ids in (self.vertices, self.edge_ids, tuple(c.id for c in self.cycles)):
            if len(ids) != len(set(ids)) or any(not isinstance(i, str) or not i for i in ids):
                raise ValueError("duplicate or empty graph IDs")
        if not self.vertices or not self.profile or (self.shared_vertex is not None and self.shared_vertex not in self.vertices):
            raise ValueError("invalid graph profile/shared vertex")
        if any(v not in self.vertices for e in self.edges for v in e.endpoints):
            raise ValueError("unknown edge endpoint")
        if any(e not in self.edge_ids for c in self.cycles for e in c.edge_ids):
            raise ValueError("unknown cycle edge ID")
        if gf2.rank(self.incidence) != len(self.vertices) - 1:
            raise ValueError("disconnected graph")
        if gf2.matmul(self.incidence, self.cycle_matrix.T).any():
            raise ValueError("cycle has nonzero boundary")

    @property
    def edge_ids(self):
        return tuple(e.id for e in self.edges)

    @property
    def incidence(self):
        b = np.zeros((len(self.vertices), len(self.edges)), dtype=np.uint8)
        index = {v: i for i, v in enumerate(self.vertices)}
        for j, edge in enumerate(self.edges):
            for v in edge.endpoints:
                b[index[v], j] = 1
        return gf2.readonly(b)

    @property
    def cycle_matrix(self):
        c = np.zeros((len(self.cycles), len(self.edges)), dtype=np.uint8)
        index = {e: i for i, e in enumerate(self.edge_ids)}
        for i, cycle in enumerate(self.cycles):
            c[i, [index[e] for e in cycle.edge_ids]] = 1
        return gf2.readonly(c)

    @property
    def id(self):
        return stable_id(self.to_dict())

    def cycle_from_path(self, id, path, source):
        """Reference path helper: fail closed when endpoints are ambiguous."""
        if len(path) < 3 or path[0] != path[-1]:
            raise ValueError("cycle path is not closed")
        ids = []
        for u, v in zip(path, path[1:]):
            matches = [e.id for e in self.edges if set(e.endpoints) == {u, v}]
            if len(matches) != 1:
                raise ValueError("missing or ambiguous path edge; use explicit edge IDs")
            ids.append(matches[0])
        return Cycle(id, tuple(ids), source)

    def to_dict(self):
        return {"profile": self.profile, "shared_vertex": self.shared_vertex,
                "vertices": list(self.vertices),
                "edges": [{"id": e.id, "endpoints": list(e.endpoints), "source": e.source} for e in self.edges],
                "cycles": [{"id": c.id, "edge_ids": list(c.edge_ids), "source": c.source} for c in self.cycles]}
