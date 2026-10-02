# Detectors, observables and ideal boundaries

Read `AGENTS.md` and `STATUS.md` first. Complete only this phase, update the status log, and stop.

Use the Anaconda environment `tour_de_gross` for every Python install, build and test (`conda activate tour_de_gross`, or `conda run --no-capture-output -n tour_de_gross ...`). Read `docs/DEVELOPMENT.md` for setup. Keep external source checkouts under `/home/quantum_teresheys/workspace/tour_de_gross_design_bundle/external_libs` (repository-relative `external_libs/` on other machines); install their Python dependencies into this environment. Before modifying any external library, fork it under the user's GitHub account and work from that fork; retain upstream attribution, licenses, exact commits and source hashes. Put main simulation code under `src/gross_design_bandle/`, with benchmark code in its separate `bench/` namespace. These paths supersede the earlier proposed `bb_surgery` / `bb_surgery_bench` layout; they do not introduce implemented simulation APIs.

## Task

Implement symbolic measurement records and signed stabilizer flows across reset, merge, repeated deformed rounds, split and final closure. Build the single-block A.7-style ideal harness with named logical-action generators. A logical Clifford basis adapter should support X1 X7 and Y1 targets later. Store which physical parity realizes each logical generator. Keep truth-table instruments with random outcomes separate from deterministic decoding experiments.

## Tests and scope limit

Implement D01--D05 for gross memory and X1. Require strict Stim DEM extraction; no gauge-detector workaround. Test that active split correction and a tracked frame produce identical signatures. Preserve K=24/23 rather than copying a one-observable donor harness.

## Acceptance

Noiseless benchmark detectors/observables deterministic; all boundary parities justified; record-offset corruption detected; logical generator ranks and semantic names saved.

## Handoff

Summarize files changed, commands actually run, evidence paths, failures and unresolved scientific assumptions. Update `STATUS.md` with the next prompt and a short reproducible command sequence. Do not mark skipped or planned tests as passed. Do not run a later phase automatically.
