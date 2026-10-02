# Two-gross generation and extension profiles

Read `AGENTS.md` and `STATUS.md` first. Complete only this phase, update the status log, and stop.

Use the Anaconda environment `tour_de_gross` for every Python install, build and test (`conda activate tour_de_gross`, or `conda run --no-capture-output -n tour_de_gross ...`). Read `docs/DEVELOPMENT.md` for setup. Keep external source checkouts under `/home/quantum_teresheys/workspace/tour_de_gross_design_bundle/external_libs` (repository-relative `external_libs/` on other machines); install their Python dependencies into this environment. Before modifying any external library, fork it under the user's GitHub account and work from that fork; retain upstream attribution, licenses, exact commits and source hashes. Put main simulation code under `src/gross_design_bandle/`, with benchmark code in its separate `bench/` namespace. These paths supersede the earlier proposed `bb_surgery` / `bb_surgery_bench` layout; they do not introduce implemented simulation APIs.

## Branch and publication workflow

Implement this phase on a dedicated `feature/<phase-stem>` branch in a separate Git worktree created from validated `main`. Switch the working directory to that worktree before editing and testing; keep the main checkout clean. Under the tmux pipeline, the controller provides the branch/worktree and owns Git publication: finish the phase and its validation, then stop so it can rerun acceptance tests, commit the feature, merge it to `main`, and atomically push the feature branch and `main` to `origin`. Outside the pipeline, perform that same sequence yourself after validation passes. Do not merge or publish failed/incomplete work, force-push, discard existing edits, or push external upstream repositories. Preserve the feature worktree on failure for review. Record the branch, worktree, validation commands and publication outcome in the handoff.

## Task

Exercise the same implementation with the two-gross reference fixture. Retain the weight-20 chosen logical supports, two extra edges in each half, 17-edge bridge and reduced 37-cycle full LPU. Generate idle/shift with 18 repetitions and in-module surgery with C=18. Add explicit extension profiles for inter surgery at C=17 and C=18; neither is a Figure-15 series.

## Tests and scope limit

Run all fast algebra/ideal/schedule/flow tests and stratified large-circuit fault checks. Compare two-gross idle/shift catalogue counts against Table 6. Prepare bounded A.8 phenomenological solver jobs; do not launch an unconstrained exact circuit-distance search.

## Acceptance

Two-gross uses no gross-size hardcoding; published versus extended benchmarks are distinguished; no copied claim that all two-gross surgery has circuit distance 18.

## Handoff

Summarize files changed, commands actually run, evidence paths, failures and unresolved scientific assumptions. Update `STATUS.md` with the next prompt and a short reproducible command sequence. Do not mark skipped or planned tests as passed. Do not run a later phase automatically.
