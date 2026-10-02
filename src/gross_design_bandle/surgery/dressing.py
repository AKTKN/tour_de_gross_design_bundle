"""Separate prescribed local dressing from the generic GF(2) solve."""
import numpy as np

from gross_design_bandle.algebra import gf2


def dress_boundaries(graph, boundaries, profile):
    boundaries = gf2.binary(boundaries, 2)
    b = graph.incidence
    if boundaries.shape[1] != b.shape[0]:
        raise ValueError("boundary vertex dimensions differ")
    if profile == "generic_gf2":
        return gf2.readonly(gf2.solve(b, boundaries.T).T)
    if profile != "paper_local":
        raise ValueError("unknown dressing profile")
    t = np.zeros((len(boundaries), len(graph.edges)), dtype=np.uint8)
    for i, boundary in enumerate(boundaries):
        if not boundary.any():
            continue
        matches = np.flatnonzero(np.all(b == boundary[:, None], axis=0))
        if int(boundary.sum()) != 2 or len(matches) != 1:
            raise ValueError("paper dressing requires one unambiguous adjacent edge; no path fallback")
        t[i, matches[0]] = 1
    return gf2.readonly(t)
