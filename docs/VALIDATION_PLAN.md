# Validation and acceptance tests

A test should identify its oracle, scope, expected result and failure artifact. A passing rank test is not a distance proof; a passing noiseless test is not a logical-error-rate reproduction.

## Delivered tests

`python -m pytest -q tests/test_reference.py` currently runs nine tests. `tools/audit_reference.py` checks the two code definitions, 12-pair logical bases, selected graph cycles and omitted-cycle membership in the combined binary span, commutation and one-logical-loss ranks for X, XX, Y and the algebraic inter-XX reconstruction, and physical-shift-induced logical matrices. Results are in `evidence/algebra_audit.json`. These utilities use NumPy; Stim, Relay and qLDPC were not installed or executed in this environment. The delivered audit is phase-blind for the deformed-check rank calculations and does not implement the ideal instrument or the physical Bell schedule.

## Level A: algebra and reference geometry (fast CI)

A01. Exhaustive one- and two-qubit signed Pauli multiplication, conjugation and commutation; XZ=-iY, Y=iXZ. Hermitian checks square to I; reject imaginary-phase checks.

A02. BB Hx Hz^T=0 and ranks 66/66 for gross, 138/138 for two-gross. Logical bases satisfy Hx Lz^T=0, Hz Lx^T=0, Lx Lz^T=I_12. Validate explicit convention adapters by qubit/check permutations, not only matching parameters.

A03. Port weights 12 for gross and 20 for two-gross. Validate the four support/adjacent-check conditions in A.1. The half-LPU graph has 12 vertices/18 edges (gross) or 20/32 (two-gross). Full graph: 23/47/19 selected cycles or 39/81/37. The full physical LPU census is 90 or 158, counting the shared Bell check as two measurement qubits.

A04. BC^T=0, graph connectivity, signed product_v g_v=L, BT^T=a, all deformed checks commute. Generate omitted-cycle span witnesses against the **combined** group and verify phases. Verify no -I is generated. Arbitrary deletion of a required cycle must fail a span or logical-dimension test.

A05. Merged dimension k_in-1; in-module expected 11, two-module expected 23. Calculate the actually fixed input logical subspace. Negative test: independently measuring X1 and X7 must fail the XX-only specification even though their parity is available.

A06. Derive physical shift action on the complete logical basis by symplectic pairing. Verify inverses, commuting x/y actions, logical sixth powers and row-convention conversion. Physical x^6 need not be the identity permutation. Do not hard-code a tensor product of printed 6x6 matrices as a 12x12 binary action.

## Level B: ideal instrument (small exact tests, then stabilizer/Choi tests)

B01. Two-vertex/one-edge toy graph: g1=P1 Xa, g2=P2 Xa. Enumerate all allowed outcome branches and compare the corrected Kraus map to the projector onto P1 P2. Include both signs and non-eigenstate inputs.

B02. Repeat for a triangle (one cycle), a graph with a dummy zero-port vertex, and a Bell-split check. Different root/path choices must give the same corrected channel. Test intentional sign inversion and omitted frame application.

B03. On an 18-qubit BB test code, choose a verified nontrivial logical and a generic graph with a full cycle basis. This is a debugging fixture, not a geometrically scaled TdG LPU. Do not assume its logical labels include X7. Check all branches where feasible and use reference-qubit stabilizer tests otherwise.

B04. Gross X1, XX=X1 X7 and Y1: test + and - eigenstates, inputs with random target outcome, an encoded entangled reference for every preserved logical degree of freedom, and coherence inside the measured eigenspaces. The circuit must measure only the requested product. Test the ideal output state and measurement outcome, not only syndrome determinism.

B05. For inter XX, test two independent code blocks, an entangled cross-block input, both outcome signs and residual logical preservation. Enforce explicit block IDs. Assert the Fig. 13(b) adapter has no active in-module triangular bridge cycles.

B06. Shifts: compare the real two-CNOT transfers and recorded Pauli frame with an ideal permutation oracle on arbitrary stabilizer inputs. Propagate both X and Z Paulis through role changes and all measured vacated sources.

## Level C: schedule and circuit lowering

C01. Every time slice is conflict-free. Every algebraic check's physical sequence measures the intended signed Pauli, verified by a tableau oracle. Bell-state preparation precedes both halves' interactions.

C02. Validate Eq. (67) for every anticommuting overlap. Inject a deliberately reversed ordering on one of two overlapping data qubits; the validation must fail even though the schedule remains collision-free.

C03. Reconstruct the staggered BB round: 8 C + 1 timing, reset/readout offsets and all A/B edge layers. Compare translated schedules from the donor and the paper only after their index mapping is established.

C04. Count installed qubits, active qubits, live data intervals, noisy locations by kind, and Bell couplers separately. Changes to a basis-conversion policy or idle accounting invalidate the circuit hash and require new noise fingerprints.

C05. Verify the full-LPU physical connectivity census (degree <=7 for the published installed layout), not simply the degree of the auxiliary graph. Bell-check implementation details matter for this test.

## Level D: detector and observable integrity

D01. Symbolic records lower correctly through nested repeats; flattening and unrolling preserve all parities. Deliberately shift one `rec` offset and require a failing flow test.

D02. All declared detectors/observables are deterministic in the ideal **benchmark harness**. Raw logical-measurement truth-table circuits may intentionally have random outcomes and are a separate API. No `allow_gauge_detectors=True` workaround.

D03. For each primitive fault in small circuits, independently propagate its Pauli and compare its detector and logical signatures against Stim. For large circuits, exhaustively validate gate-template fault classes and use deterministic stratified samples across every phase, gate kind, boundary and role change. Export counterexample location and expected/actual signatures.

D04. Verify identical signatures when the split correction is actively applied versus recorded in a software frame. Check Y phases, Bell measurement XORs, retained old-check dependencies and noiseless terminal closure.

D05. Single-block K24/K23 must match named generator ranks. Full two-block centralizer K47 is a separate profile. Strict K23 inter reference stays unresolved until O1 is answered. Do not regard a one-observable PPM circuit as an A.7 channel benchmark.

## Level E: noise and decoder

E01. Build a tiny independent-Pauli circuit where two fault copies cancel. Compare analytic event probabilities, direct Stim sampling and catalogue sampling. Verify the equal-q replacement versus the unequal independent model differs only at the claimed order in p. Show that categorical depolarization is a different named profile.

E02. Every sampler column maps to a physical fault, and H/Lambda columns align. Test duplicate columns, zero-H/nonzero-Lambda columns, zero/zero columns, repeat blocks, observable-only terms and hyperedges. Never decompose a correlated fault into independent graph edges for Relay.

E03. Require Hc=sigma for successful correction outputs. Count residual-syndrome failures/nonconvergence explicitly. Synthetic tests cover no-fault, single fault, logical-only fault, and inconsistent decoder return shape/dtype. No discard-by-default.

E04. Current Relay vs historical Table-7 mapping: inspect the actual recurrence and run fixed explicit-gamma tests on a small H. Compare initialization, each hard-decision trajectory where accessible, candidate cost and stopping. Log float precision, input ordering, duplicate handling and all caps.

E05. Same deterministic test syndromes through scalar and batch APIs must agree when randomness is fixed. Reproducible independent decoder streams must be invariant to worker allocation, or the manifest must document the supported weaker reproducibility guarantee.

## Level F: distance and statistical evidence (non-CI jobs)

F01. Reproduce A.8's two phenomenological optimization problems: spatial distance of the deformed code and temporal distance using the explicit A.8 constraint set (deformed checks with vertex checks omitted). The measured L must not be added to this temporal commuting set, since the candidate is required to anticommute with L. Use that operational constraint set instead of blindly taking a generic group center that may include the measured central element. Optimize Pauli weight as sum(x OR z), not sum(x+z). Save solver optimum, lower bound, gap, termination reason and an independently checked witness. Timeout is not proof.

F02. Circuit-distance search solves H e=0 with a selected nonzero logical action; any verified witness gives only an upper bound. Test witnesses independently. Absence of a smaller witness does not prove a lower bound. For small fixtures, exact enumeration can establish both.

F03. Exhaustively enumerate all error subsets on tiny catalogue models to validate fixed-weight sampling, f(w), Bernoulli mixtures and rate normalization. Bernoulli- and fixed-weight-derived estimates must agree within uncertainty on accessible gross pilot points.

F04. Always preserve observed failures below w0, gross-Y w>80 observations, zero-failure confidence bounds and nonconvergence rates. Use a non-adaptive holdout p grid for checking extrapolation. The ansatz is a model, not a certification of 10^-20 logical error rates.

F05. Resume/chunk tests: deterministic seeds derived from (run hash, series, sample mode, p/w index, chunk index, stream kind); no shared RNG under fork; no oversubscription of Relay internal threads; no duplicate chunks on resume. Run manifests and sampled errors must be auditable.

## Acceptance levels

`algebra_validated` -> `ideal_instrument_validated` -> `physical_circuit_validated` -> `decoder_integrated` -> `statistical_replication` -> `paper_exact_configuration`.

Each level requires its own evidence paths. Matching Table-6 N and a visually similar line are necessary checks in a reproduction workflow, not substitutes for the earlier levels. None of the delivered files is marked as a completed Figure-15 replication.
