# Staged implementation and simulation integration

## Work sequence

The first vertical slice is a fully validated gross **X1** operation, even though the requested measurement target is XX/Y/inter-module. X1 needs only one half-LPU and is an additional Figure-15 control. It isolates code/port/dressing/boundary errors before introducing a shared Bell check, a full-LPU bridge or a two-module logical-action convention.

Phases 00--03 establish source compatibility, signed algebra, geometry and ideal measurement semantics. Phases 04--06 produce a real scheduled gross X1/memory circuit and a primitive fault model. Phases 07--10 extend that generator to XX, Y, Bell-connected modules, physical shifts and two-gross. Phases 11--13 integrate Relay and execute carefully bounded statistical work. The decoder adapter can be developed in parallel with physical-operation extensions after the H/Lambda schema is frozen, but no large benchmark should run before the circuit validation gates pass.

| Prompt | Deliverable | Principal gate |
|---|---|---|
| 00 | Source/environment lock and capability audit | No guessed upstream API or silent unresolved strict field |
| 01 | Exact Pauli/GF(2) engine, BB definitions and convention maps | Canonical logical bases and signed truth tables |
| 02 | Reference LPUs, ports, dressing and certificates | Correct logical loss and cycle redundancy |
| 03 | Ideal protocol and frame | Correct conditional projector, preserved coherence |
| 04 | Physical check primitives and schedules | Legal schedule and frozen BB round |
| 05 | Flows, detector/observable compiler, ideal harness | Strict deterministic A.7 experiments |
| 06 | Independent noise and primitive faults | Signature/probability equivalence |
| 07 | Gross XX and Y generation | One intended measurement, full-LPU correctness |
| 08 | Gross inter-module adapter | Bell realization and explicit K-profile |
| 09 | Physical shifts | Transfer/frame/permutation equivalence |
| 10 | Two-gross and extension circuits | Size-independent implementation |
| 11 | Relay backend | Joint decoding and historical/current compatibility |
| 12 | Samplers, storage, fits and bootstrap | Tiny exact tests and bounded smoke run |
| 13 | Approved replication campaign | Auditable points and correctly qualified claims |

## Generated artifact contract

Every compiled experiment should export `circuit.stim`, `manifest.json`, `code.json`, `graph.json`, `deformed_checks.json`, `schedule.json`, `measurements.json`, `flows.json`, `observables.json`, `noise_locations.parquet`, `fault_population.parquet`, `H.npz`, `Lambda.npz`, `priors.npy`, and a SHA-256 index. A stored Stim DEM is useful for cross-checking; it is not the only record of primitive faults.

Every run references the immutable artifact hash and adds a decoder manifest plus append-only chunks. Store total shots, failure counts, residual-syndrome failures, per-observable failures, sample mode and p/w, seeds, CPU/elapsed time, iteration/termination statistics, and normalization divisor. Full shot traces are optional except for deterministic diagnostic counterexamples. Avoid putting large generated data in Git.

## Worker and sampling organization

Use process-level parallelism over deterministic chunks and one explicit thread policy for Relay. Initialize the read-only H/Lambda structure once per worker or use a documented shared memory representation. Avoid simultaneously requesting many processes and unconstrained Rayon threads. Build a decoder once for a fixed prior/configuration rather than once per shot.

Fixed-weight sampling can XOR the sparse signatures of w selected columns without constructing an N-bit dense error for every shot. Bernoulli sampling can use validated Stim detector sampling or a sparse exact sampler; a Poisson approximation to the fault count is a different optional sampler and is not the reference. Paired-error comparisons should reuse explicit sampled fault sets when comparing decoder implementations, while independent random streams control decoder randomness.

A complete decoder graph on millions of expanded copies may be inefficient. The architecture supports retaining the primitive sampling catalogue while passing a grouped detector graph to Relay, but grouping must preserve both detector and logical signatures and its effect on BP's factor graph must be evaluated. It is a distinct profile unless the original grouping is recovered. Do not implement a performance shortcut first and discover later that it changed the target decoder.

## Measurement quality and confidence

Begin at accessible p and weights near the observed failure transition. Allocate a pilot to estimate cost/failure frequency, then request a compute budget. Stop points using both a minimum shot count and a desired failure-count/interval-width target; store the stopping rule. Do not demand 10^-20 direct Monte Carlo. The rare-event extrapolation is evaluated through the failure-spectrum model and held-out accessible-p checks.

Exact reconstruction of rounded published lines is possible from Table 6 and is provided as an analysis utility. Independent statistical replication requires new samples. Replication of the precise published points and bootstrap bands additionally requires the original trial counts and fitting conventions. These are three different completion criteria.

## Future interfaces (not currently implemented)

```bash
bb-surgery inspect --profile tdg_v1_gross
bb-surgery build --config configs/gross_XX.json --out artifacts/<hash>
bb-surgery validate --artifact artifacts/<hash> --level physical
bb-surgery-bench run --artifact artifacts/<hash> --config configs/pilot.json
bb-surgery-bench fit --run runs/<hash> --profile tdg_v1
```

Keep the default CLI action read-only or validation-only. The production run command should require an explicit profile and compute budget and show whether it is a strict reconstruction, current-backend replication or new extension.
