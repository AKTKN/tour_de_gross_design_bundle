# Source audit and locked capabilities

Read `AGENTS.md` and `STATUS.md` first. Complete only this phase, update the status log, and stop.

Use the Anaconda environment `tour_de_gross` for every Python install, build and test (`conda activate tour_de_gross`, or `conda run --no-capture-output -n tour_de_gross ...`). Read `docs/DEVELOPMENT.md` for setup. Keep external source checkouts under `/home/quantum_teresheys/workspace/tour_de_gross_design_bundle/external_libs` (repository-relative `external_libs/` on other machines); install their Python dependencies into this environment. Before modifying any external library, fork it under the user's GitHub account and work from that fork; retain upstream attribution, licenses, exact commits and source hashes. Put main simulation code under `src/gross_design_bandle/`, with benchmark code in its separate `bench/` namespace. These paths supersede the earlier proposed `bb_surgery` / `bb_surgery_bench` layout; they do not introduce implemented simulation APIs.

## Branch and publication workflow

Implement this phase on a dedicated `feature/<phase-stem>` branch in a separate Git worktree created from validated `main`. Switch the working directory to that worktree before editing and testing; keep the main checkout clean. Under the tmux pipeline, the controller provides the branch/worktree and owns Git publication: finish the phase and its validation, then stop so it can rerun acceptance tests, commit the feature, merge it to `main`, and atomically push the feature branch and `main` to `origin`. Outside the pipeline, perform that same sequence yourself after validation passes. Do not merge or publish failed/incomplete work, force-push, discard existing edits, or push external upstream repositories. Preserve the feature worktree on failure for review. Record the branch, worktree, validation commands and publication outcome in the handoff.

## Task

Read all project contracts and inspect the pinned upstream files in reference/sources.json. Reuse the setup environment `tour_de_gross`; check Python and dependency compatibility before installing additional backends. The audit-only setup lock is not a validated Stim/qLDPC/Relay lock. Verify each observed blob against its pinned commit. Inspect qLDPC experimental surgery, the SlidingWindowDecoder memory builder and Relay bindings/history; write docs/BACKEND_AUDIT.md with actual import paths/signatures, licenses, supported operations and mismatches. Identify any public original physical-circuit/data release linked by the paper; do not assume the logical architecture compiler contains it. Extract the historical Table-7 update equations where possible. Record O1--O5 as resolved only with evidence.

## Tests and scope limit

Create a source lock and environment lock; confirm the nine delivered utility tests. Add a strict-manifest validator that rejects unknown observable, schedule, fault-population and decoder-mapping fields, but permits algebra-only development. Do not begin production circuit construction or run Monte Carlo.

## Acceptance

Pinned dependencies import; observed source hashes checked; unknown fields fail closed; capability report identifies the exact upstream APIs rather than guessed names.

## Handoff

Summarize files changed, commands actually run, evidence paths, failures and unresolved scientific assumptions. Update `STATUS.md` with the next prompt and a short reproducible command sequence. Do not mark skipped or planned tests as passed. Do not run a later phase automatically.
