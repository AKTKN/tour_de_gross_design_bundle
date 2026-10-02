# Phase 02 graph and deformation semantics

This layer constructs algebraic measurements of X1, X1 X7 and Y1 for both
frozen BB profiles, and an algebraic two-block X1 tensor X1 adapter. It does
not construct physical circuits or establish measurement-instrument coherence,
distance, noise fingerprints or Figure-15 equivalence.

`lpu.reference.build_reference_lpu(code, operation, second_code=None)` loads
the unchanged reference JSON. `operation` is `X`, `XX`, `Y` or `inter_XX`.
Inter measurements require two distinct explicit block IDs and matching code
specifications. Each adjacent-check edge has a stable ID containing its block,
half and old check ID; each expansion/bridge edge has a separate source-based
ID. Cycles contain edge IDs, so parallel edges are not conflated. Conversion
from a vertex path rejects ambiguous parallel edges. The full graph identifies
the two reference vertices once and retains every specified ladder and cycle.

A.1's four numbered requirements are checked on the actual physical supports:
canonical pairing, generation of the twelve logical pairs by the literal shifts,
disjoint commuting supports with single-qubit anticommuting overlaps, and
disjoint adjacent-check sets. The adjacent X/Z graph isomorphism under the
paper's shifted ZX duality is checked separately. The two-gross representatives
retain weight 20 and both expansion edges per half.

`surgery.deformation.compile_deformation(lpu)` preserves local dressing:
each nonzero old-check boundary must match exactly one incidence column. It
never replaces a missing local edge with a longer path. The explicitly named
`generic_gf2` dressing and `cycles.with_full_cycle_basis(graph)` oracle are
separate choices. The reference measured cycles remain 19 or 37, rather than
the 25 or 43 directions in the full graph cycle space.

The shared Y port is +Y = i X Z. All signed Paulis use `i**phase X**x Z**z`;
the phase is not the sign of a tensor product of Hermitian Pauli letters. The
product of all vertex checks is exactly the requested signed target on the
data, with identity on the edge register. No sequential X/Z measurement is
used. Signed group validation checks Hermiticity, every symplectic commutator
and a basis of all binary identity relations. A commuting Hermitian identity
relation must have phase zero, so no -I is generated.

`DeformedCode.save_certificate(path)` exports the ordered signed generators,
incidence and selected-cycle matrices, old checks and their explicit dressing
edge masks, boundary equations, a complement of the selected cycles in the
full graph cycle space, signed combined-group span coefficients for that
complement, identity relations, and the vertex-product target witness. Together
the selected cycles and complement span every graph cycle; their signed
products are all +Z cycles in the combined deformed group.

The fixed input subspace is computed, not inferred from merged dimension. Take
the kernel of the generators' edge X/Z columns to find every data-only group
element, check it lies in the input-code centralizer, then map that intersection
to the input logical quotient by symplectic pairing. Its image must be exactly
the one-dimensional span of the requested Pauli label. Certificates record the
full edge-free intersection, all its input logical coordinates and independent
signed witnesses. Merged dimensions are 11 in-module and 23 inter-module.
Measuring X1 and X7 separately has two independent fixed input labels and is
rejected for the XX specification even though XX is their parity.

Certificate signs refer to a consistent +1 generator sector. They do not model
individual measurement outcomes or prove the physical measurement instrument;
that is phase 03. The installed full-LPU census counts the shared vertex as
two Bell measurement qubits and reproduces 90/158. Inter adapter counts
35/58/20 and 57/98/38 are derived active algebraic graph counts, not that
installed census. Identity-port subdivision vertices have degree two; each
bridge cycle is one six-edge joint cycle. No in-module triangular bridge cycle
is active in the inter profile. Bell partitioning and scheduling are later work.

Provenance: `locks/deformation-sources.json`; independent implementation with
no copied donor code. Unchanged `tools/audit_reference.py` is a binary oracle;
signed witness tests separately multiply through `Pauli.__mul__`. O1--O5 remain
open. In particular, merged dimension 23 does not define the published inter
K23 action-observable profile; full-two-block K47 remains a separate profile.

Reproduce in `tour_de_gross`:

```bash
python -m pytest -q tests/test_deformation.py
python tools/audit_deformation.py --output-dir evidence/phase02/certificates
python tools/audit_reference.py --output evidence/phase02/independent-audit.json
```
