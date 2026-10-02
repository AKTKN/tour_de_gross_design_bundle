# Phase 05: symbolic flows and the ideal single-block harness

This independently implemented construction validates gross memory and physical
X1 surgery, with the phase-04 native physical schedule. It provides no stochastic
noise catalogue, decoder, sampling campaign or paper-exact configuration.
The scientific source is [arXiv:2506.03094v1](https://arxiv.org/pdf/2506.03094v1),
PDF Appendix A.4 and A.7, printed pp. 51 and 58--59. Source/implementation
provenance is in `locks/flows-and-harness-sources.json`; no external source was
copied or modified. The canonical external directory remains
`/home/quantum_teresheys/workspace/tour_de_gross_design_bundle/external_libs`.

`flows/records.py` holds absolute physical outcome IDs and annotated signed
parities. A Bell algebraic readout is the XOR of both physical identities.
Nested repeats instantiate separate scopes. Explicit carry aliases bind the
first iteration to a prior outcome and later iterations to the previous body
output; nested carry dependencies preserve random stabilizer signs. Lowering retains a Stim REPEAT
only when all instantiated bodies, including their relative offsets, agree;
otherwise it unrolls them. Affine constants lower to deterministic MPAD bits,
which also acquire absolute IDs. Missing/future/duplicate records fail closed.
The phase-04 staggered memory and surgery schedules keep their timing: the
record layer adds no physical ticks. The exported physical body includes active
feedforward when selected, and has no ideal MPPs.

`flows/stabilizer_flows.py` uses exact signed stabilizer rows, bitset GF(2)
support and affine outcome bits. It propagates i^p X^x Z^z through Clifford
gates, resets, measurements and record-controlled Paulis. Resets take a partial
trace before adding the prepared axis; they cannot invent a known sign for an
entangled partner. Random outcomes remain symbolic. Declared detector and
observable parity expressions must reduce to zero, including their signs.
Unsupported gates/noise fail closed. This oracle does not use Stim's randomized
signed `has_flow` check. Strict `detector_error_model(allow_gauge_detectors=False)`
is an additional independent check, never a replacement for the signed test.

`flows/harness.py::build_benchmark` prepares encoded logical Bell pairs with
ideal reference qubits. Memory retains all twelve Bell pairs and K=24 named
logical generators. X1 prepares the measured data slot in its + eigenstate and
retains eleven Bell pairs. Its K=23 rows are X1, X2--X12 and Z2--Z12.
The X1 score is the XOR of vertex outcomes in the last deformed round; final
X1 readout closes that parity with a detector. Other scores are final
logical/reference correlations. Software-frame contributions are attached to
all affected readouts. This records both classical target accuracy and the
preserved logical channel; it never inherits a one-observable donor harness.

For an old check s_j, the dressed check is s_j Z(t_j). Initial dressed/cycle
outcomes follow the encoded input and reset edge Z constraints. Individual
initial vertex outcomes are random and are not detectors. Repeat detectors
compare the same signed physical parity. At split, selected cycle edge-Z
parities compare with the last cycle outcome. Retained old-check dependencies
compare the following original check to the last dressed check and split
Z(t_j), with the appropriate port-frame anticommutation term. Both active and
tracked modes retain these dependencies. The scoring frame is a linear rooted
tree rule on arbitrary raw bits; cycle detectors diagnose non-cut faults. This
does not pass noisy raw data to the earlier ideal-only `SplitFrame.evaluate`
API, which requires every chord to satisfy the cut constraints. A final explicitly noiseless original
physical round and ideal MPP closure justify terminal stabilizers. The final
logical/reference MPPs commute jointly. The complete physical parities,
justifications, reset output constraints, input correlations, terminal readout
Paulis, semantic names and exact logical-coordinate ranks are exported.

The physical original round after split is a noise-free boundary in this named
independent policy. Ideal input encoding and final MPPs are outside the noisy
operation body. Phase 06 must preserve these boundary labels when assigning
fault locations. No claim is made that this particular coloring or serialized
boundary lowering equals the unpublished simulation circuit (O3).

`TruthTableInstrument` is a separate wrapper around the physical protocol:
encoded input is supplied externally and target outcomes may be random. It
has no decoding observables/detectors. Exact affine analysis confirms a random
X1 result on a full encoded Choi input; deterministic benchmark experiments
must use `BenchmarkHarness` instead.

`LogicalBasisAdapter.single_block` additionally constructs canonical logical
bases for X1*X7 (logical CX from 1 to 7) and Y1 (logical S on 1). The latter is
i X1 Z1 with the full signed phase. These are tested algebraic adapters for
later physical target validation. They do not enable an XX/Y physical benchmark.
Inter-module published K23 is rejected as unresolved O1; a K47 physical harness
is outside this gross single-block phase. No anonymous 23-row subset is created.

`flows/signatures.py` independently propagates a single joint X/Z fault through
gates, resets, measurements and active feedback to detector/observable bits.
Tests exhaust nonidentity tensor faults on the physical operands of a small
negative-YY Bell circuit and use fixed deterministic representatives across
gross construction phases. These are probability-one oracle injections, not
Monte Carlo observations. Counterexamples include location and expected/actual
signatures. This is a template/boundary integrity check, not a primitive fault
catalogue or Table-6 N calculation.

The export command is:

```bash
conda run --no-capture-output -n tour_de_gross python -m pytest -q tests/test_flows_and_harness.py
conda run --no-capture-output -n tour_de_gross python tools/audit_flows_and_harness.py --output-dir evidence/phase05/artifacts
```

O1 published inter K23 generators, O2 historical Relay semantics, O3 exact
schedule/shift/lowering/boundaries, O4 primitive multiplicities/admission and
O5 original data/grids/bootstrap remain open. Their unresolved paper-exact
fields are not assumptions in this independent ideal construction.
