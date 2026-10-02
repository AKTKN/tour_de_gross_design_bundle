# Phase 06 independent circuit noise and primitive catalogue

Maintenance update: fault builders accept `cache_dir` (or
`GROSS_DESIGN_CACHE_DIR`; `False` forces cold construction). Numerical artifacts
use `bench.artifacts` CSC/map arrays, sparse joint signatures and checksummed
manifests, with read-only mmap loading. The exporter defaults to this reusable
format; `--legacy-json` explicitly requests the older expanded JSON/NPZ too.
See `docs/VALIDATION_WORKFLOW.md` for invalidation, validation and retry policy.

This implementation constructs joint detector/logical-action matrices for the
independent gross memory and X1 benchmarks. It does not establish Figure-15
equivalence, Table-6 population equivalence, distance or logical error rates.
It uses the inherited native physical schedule and ideal encoded Bell harness.
All code is independently written; no external implementation was copied.
Scientific sources are REPRODUCTION_SPEC and arXiv:2506.03094v1 Section 2.6 and
Appendix A.7, printed pp. 58–59. Backend provenance is in the inherited source
lock and `locks/noise-and-fault-sources.json`.

`NoiseProfile` requires one of three distinct IDs:

| Profile | Preparation/readout | Each idle Pauli | Each two-qubit Pauli |
|---|---|---|---|
| `paper_linearized_unequal` | one independent p flip | one independent p/3 term | one independent p/15 term |
| `a7_uniform_expanded` | 15 independent q copies | 5 independent q copies | one independent q copy |
| `standard_categorical_depolarizing` | one p flip | DEPOLARIZE1(p) | DEPOLARIZE2(p) |

Here q=p/15. A reset flip follows reset, and a readout flip precedes readout.
For Z preparation/readout it is X, for X/Y preparation/readout it is Z. A native
CX, CY or CZ receives all 15 nonidentity tensor Paulis AFTER the gate. This
includes the real Bell preparation CNOT. There are no additional free basis
conversions or active-gate idle errors. Every unoccupied live BB data, edge data
or prepared measurement qubit receives X/Y/Z idle faults at the tick's end.
The full installed qubit register is distinct from these live intervals.
Encoding, reference qubits, the last original-check verification after X1,
terminal MPP closure and classical software frame processing are noise-free.
`benchmark_locations` rejects active correction mode pending a separate
physical correction noise policy. X1 edge initialization and split each receive
their own data-idle and reset/readout population. These explicit independent
decisions are versioned as `native_schedule_independent_noise_v1`; O3 is open.

`build_fault_model` requires explicit `admission_policy` and `grouping_policy`.
`include_all` keeps zero/zero columns; `exclude_joint_zero` excludes only columns
zero in BOTH H and Lambda. Detector-zero logical faults are retained. H and
Lambda always have the same admitted-copy ordering. No term is decomposed into
independent X/Z sectors or graph edges; hyperedges remain intact. The categorical
profile is deliberately rejected by the independent Bernoulli matrix API.
`emit_noise` supports all three profiles and emits the complete physical
population regardless of admission. It uses separate CORRELATED_ERROR terms,
never ELSE_CORRELATED_ERROR, for independent terms.

Each raw primitive retains physical location, gate, time, phase, round, role,
boundary, tensor Pauli, unequal probability, equal-q multiplicity and emitted
copy count. Exports provide raw-to-copy through `copy_to_raw` and `copy_ordinal`,
`admission_mask`, `admitted_to_copy` and `admitted_to_group`; raw records point
back to physical locations. Generic `Location.repeat_path` can retain nested
iteration identities while boundaries always refer to the flattened circuit.
The generated gross schedule is unrolled with explicit rounds, not compressed
Stim repeats. The supplied nested-repeat fixture checks both forms.

`preserve_copies` makes decoder groups one-to-one with sampler columns.
`joint_signature_xor` groups only equal COMBINED H/Lambda signatures. Its exact
group probability is (1-product(1-2p_i))/2. It preserves the unconditional joint
channel but does not preserve the original conditioned weight distribution.
Any future fixed-weight sampler must use the admitted copies, not group count.
H/Lambda exports remain admitted-copy matrices even when decoder grouping is
requested; grouped signatures and XOR probabilities are separately exported.
A compact Stim DEM is diagnostic and never defines N.

The reverse binary sweep computes every raw signature in one pass without
using a DEM. Small gate templates, negative YY Bell checks and nested repeats
are exhaustively checked against a separate forward Pauli oracle and Stim
probability-one joint injection. Larger gross memory/X1 circuits check every
phase/gate/role/tensor-Pauli stratum in first/middle/last rounds, selecting the
middle physical location deterministically. These are stratified validations,
not exhaustive checks of every large-circuit location. Counterexamples retain
the location and all three signatures before failure. Feedforward and both
sectors remain joint. The base harness must pass strict detector extraction;
gauge flags and graphlike decomposition are never used.

Tiny E01 channel tests enumerate all subsets, prove two-copy cancellation,
compare exact XOR probabilities to bounded Stim/catalogue Bernoulli draws and
check the O(p²) difference from unequal primitives. These 32768-shot tiny
channel unit tests are not benchmark Monte Carlo or a pilot. Gross artifacts
use only deterministic fixed-fault checks and strict DEM extraction.

The exporter saves C10 ideal/noisy circuits for all three profiles, full
compressed catalogue JSON, sparse H/Lambda matrices, deterministic validation
trials, source/artifact hashes and N discrepancy reports. Each report includes
both admission counts, logical-only population, copies by kind/phase/role and
the explicit physical decisions. Counts are measurements of this implementation,
not transcribed Table-6 observations. No population is padded to match N.

```bash
conda run --no-capture-output -n tour_de_gross python -m pytest -q tests/test_noise_and_fault_model.py
conda run --no-capture-output -n tour_de_gross python tools/audit_noise_and_fault_model.py --output-dir evidence/phase06/artifacts
```

O1 inter K23, O2 historical Relay/prior/column semantics, O3 paper-exact
serialization, O4 admission/multiplicity/population identity and O5 original
sampling data remain open. Their unresolved status prevents strict paper
sampling but does not require an unstated assumption for this independent
construction. No decoder, shift generator, XX/Y benchmark, solver or later
phase is invoked here.
