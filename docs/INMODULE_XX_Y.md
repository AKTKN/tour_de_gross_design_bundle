# Physical in-module XX and Y

Phase 07 extends the local physical generator and deterministic single-block
harness to gross `X1*X7` and `Y1`. This is an independent construction of the
frozen v1 LPU, not an exact Figure-15 reproduction.

`circuits.protocol.build_physical_inmodule(deformation, rounds=10)` resets
explicit edge data, executes merged signed checks, reads the split edges and
verifies original BB checks. Its raw instrument has no detectors or observables
and requires caller-supplied encoded input. `build_physical_x1` remains a strict
X1 compatibility entry point. The schedule contains native CX/CY/CZ, physical
Bell preparation and both Bell readouts; ideal MPP occurs only in the separately
labelled input/terminal benchmark harness. Gross C=10 counts merged rounds and
surgery rates would be per operation, with no division by C.

XX and Y use the same 23 vertices, 47 edge-data sites, 19 selected cycles, 90
installed LPU qubits and 378 total physical sites. The active Pauli labels,
dressing and couplers change within the same installed connectivity. Y is the
single signed Hermitian target i X1 Z1: its common support combines into Y in
one port, with CY on the fixed physical Bell half. It is never lowered to
sequential X/Z measurements. XX retains coherence between its separate factors.

`flows.harness.build_benchmark` accepts operation `X1*X7` or `Y1` and the exact
same-block signed deformation. Use `rounds=10` for the gross reference profile.
Its ideal logical Clifford basis puts the requested target in slot one and
prepares the other eleven logical slots entangled with ideal references. It
scores all 23 named centralizer generators; software/active split modes realize
the same instrument and joint fault signatures. Active corrections are noiseless
validation only: the noise API continues to require software frames, since no
active-correction noise policy is defined. Original-check dependencies, Bell
XORs and terminal closure remain explicit in symbolic records.

The inherited scheduler produces 13 ticks per full-LPU round (130 merged ticks
for C10, 141 total including reset/split/original verification), versus the
paper's reported 12C coloring depth. This mismatch is recorded rather than
retuned silently. Include-all equal-q N is 439380 for XX and 438480 for Y;
Table-6 N is 398717 and 400117, giving deltas +40663 and +38363. Both
include-all and joint-zero-excluded counts are exported.

The inherited independent noise policy includes native gate faults (including
the Bell CNOT), every unoccupied live data/prepared-ancilla tick, edge reset and
split readout. Encoding, references, final original verification and terminal
MPP are noiseless. The equal-q ledger preserves multiplicities 15/5/1 and joint
X/Z columns. Admission/grouping require explicit choices. No N padding or
conversion of compact DEM count into primitive population is permitted.

Validation uses C10 encoded +/- and random-outcome Choi trajectories, a complete
rank-156 data/reference stabilizer witness, composite signed readout tableaus,
full schedule/connectivity checks, nested full-Bell repeats, strict ideal flows,
all 24 input logical Pauli signatures, full active/frame raw-column equality
and independent deterministic primitive strata across
phase/gate/role/tensor word and first/middle/last rounds, with both Bell halves named explicitly. C10 exact strict-DEM/reference-record
flow evidence for both split modes is tested and exported; the acceptance tests combine
C10 strict-DEM/reference-sign proofs with independent two-round signed
affine proofs and mutation checks. The exact reference parity check uses actual
raw records, since detector sampler flips alone would conceal constant - signs.
Tiny inherited tests
exhaust gate-template fault classes. Large location checks are stratified,
not exhaustive independent tests of every location. Bounded noiseless trajectories
and probability-one fault injections are unit-test oracles, not noisy rates.

Run from the supplied feature worktree in `tour_de_gross`:

```bash
conda run --no-capture-output -n tour_de_gross python -m pytest -q tests/test_inmodule_xx_y.py
conda run --no-capture-output -n tour_de_gross python tools/audit_inmodule_xx_y.py --output-dir evidence/phase07/artifacts
```

The export saves circuits, physical/Bell/dressing/frame ledgers, named observable
parities, complete native copy/admission/group arrays, joint sparse H/Lambda,
three distinct noisy profiles and explicit Table-6 N deltas for gross XX/Y.
These are circuit audits, not observed failure probabilities.

O1 (inter K23), O2 (historical Relay/prior/columns), O3 (paper-exact serialized
schedule/lowering/boundaries), O4 (Table-6 fault population/admission/merging) and
O5 (original statistical data) remain open. None is needed to define this named
independent construction. They block an exact-reproduction claim; strict paper
manifests remain fail-closed. No decoder, distance solver, shifts, inter-module
operation or noisy production sampling is validated by this phase.

Follow `docs/VALIDATION_WORKFLOW.md`. The exporter uses content-addressed native
numeric artifacts; legacy JSON/NPZ is opt-in. Its index records initial cache
state and model, warm-read, changed-p and first/reused export timings. Warm and
changed-p reads must preserve both matrices, joint signatures and every copy,
admission and grouping map. Relevant implementation changes invalidate numerical
keys; test/doc edits do not. Large strata use representative joint words, with
explicit phase/gate/role/round coverage. See STATUS for actual validation results.
