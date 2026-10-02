# Physical checks, BB memory and legal schedules

Read `AGENTS.md` and `STATUS.md` first. Complete only this phase, update the status log, and stop.

Use the Anaconda environment `tour_de_gross` for every Python install, build and test (`conda activate tour_de_gross`, or `conda run --no-capture-output -n tour_de_gross ...`). Read `docs/DEVELOPMENT.md` for setup. Keep external source checkouts under `/home/quantum_teresheys/workspace/tour_de_gross_design_bundle/external_libs` (repository-relative `external_libs/` on other machines); install their Python dependencies into this environment. Before modifying any external library, fork it under the user's GitHub account and work from that fork; retain upstream attribution, licenses, exact commits and source hashes. Put main simulation code under `src/gross_design_bandle/`, with benchmark code in its separate `bench/` namespace. These paths supersede the earlier proposed `bb_surgery` / `bb_surgery_bench` layout; they do not introduce implemented simulation APIs.

## Branch and publication workflow

Implement this phase on a dedicated `feature/<phase-stem>` branch in a separate Git worktree created from validated `main`. Switch the working directory to that worktree before editing and testing; keep the main checkout clean. Under the tmux pipeline, the controller provides the branch/worktree and owns Git publication: finish the phase and its validation, then stop so it can rerun acceptance tests, commit the feature, merge it to `main`, and atomically push the feature branch and `main` to `origin`. Outside the pipeline, perform that same sequence yourself after validation passes. Do not merge or publish failed/incomplete work, force-push, discard existing edits, or push external upstream repositories. Preserve the feature worktree on failure for review. Record the branch, worktree, validation commands and publication outcome in the handoff.

## Task

Implement single-check and Bell-check physical primitives with documented basis/noise policy. Extract the SlidingWindowDecoder CNOT schedule through a convention adapter; reproduce the staggered memory round. Implement the paper staged-coloring surgery schedule and Eq. (67) validation. Preserve algebraic-check versus physical-ancilla identities. Generate gross X1 physical noiseless circuits, retaining a complete schedule ledger.

## Tests and scope limit

Implement C01--C05 and Bell oracle tests. Test a collision-free but anticommuting-overlap-invalid schedule. Validate 8C+1 memory timing and account separately for deformed cycles, initialization/split and terminal harness. Do not optimize with ILP or silently change cycle bases.

## Acceptance

Physical primitive tableau checks pass; all schedule constraints checked; gross X1 noisy-body placeholder is replaced by actual controlled-Pauli/check circuits, without invoking the decoder.

## Handoff

Summarize files changed, commands actually run, evidence paths, failures and unresolved scientific assumptions. Update `STATUS.md` with the next prompt and a short reproducible command sequence. Do not mark skipped or planned tests as passed. Do not run a later phase automatically.
