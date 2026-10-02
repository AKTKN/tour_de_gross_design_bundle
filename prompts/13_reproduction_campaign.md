# Controlled Figure-15 replication campaign

Read `AGENTS.md` and `STATUS.md` first. Complete only this phase, update the status log, and stop.

Use the Anaconda environment `tour_de_gross` for every Python install, build and test (`conda activate tour_de_gross`, or `conda run --no-capture-output -n tour_de_gross ...`). Read `docs/DEVELOPMENT.md` for setup. Keep external source checkouts under `/home/quantum_teresheys/workspace/tour_de_gross_design_bundle/external_libs` (repository-relative `external_libs/` on other machines); install their Python dependencies into this environment. Before modifying any external library, fork it under the user's GitHub account and work from that fork; retain upstream attribution, licenses, exact commits and source hashes. Put main simulation code under `src/gross_design_bandle/`, with benchmark code in its separate `bench/` namespace. These paths supersede the earlier proposed `bb_surgery` / `bb_surgery_bench` layout; they do not introduce implemented simulation APIs.

## Branch and publication workflow

Implement this phase on a dedicated `feature/<phase-stem>` branch in a separate Git worktree created from validated `main`. Switch the working directory to that worktree before editing and testing; keep the main checkout clean. Under the tmux pipeline, the controller provides the branch/worktree and owns Git publication: finish the phase and its validation, then stop so it can rerun acceptance tests, commit the feature, merge it to `main`, and atomically push the feature branch and `main` to `origin`. Outside the pipeline, perform that same sequence yourself after validation passes. Do not merge or publish failed/incomplete work, force-push, discard existing edits, or push external upstream repositories. Preserve the feature worktree on failure for review. Record the branch, worktree, validation commands and publication outcome in the handoff.

## Task

Assemble a preflight report for every series: code/basis, schedule, frame/observable profile, noise catalogue, N/K/divisor, Relay compatibility, all validation levels, and open O1--O5 decisions. Read STATUS and reject production jobs whose scientific prerequisites are unmet. Build a small pilot-based shot allocation plan with a user-approved compute budget; the paper reports a substantial compute campaign, so no automatic full sweep.

## Tests and scope limit

Produce a manuscript-quality comparison of new raw points, confidence intervals and reconstructed published fits, keeping each clearly labeled. Include gross inter/XX/Y/shift, X/idle controls and two-gross idle/shift. Two-gross measurements appear in a separate extension figure. Require held-out accessible-p agreement and model sensitivity analysis before low-p extrapolation claims.

## Acceptance

Every plotted observation has a run manifest and counts; fits have bootstrap/provenance; deviations are explained; exact or statistical reproduction claims match actual evidence and resolved specifications.

## Handoff

Summarize files changed, commands actually run, evidence paths, failures and unresolved scientific assumptions. Update `STATUS.md` with the next prompt and a short reproducible command sequence. Do not mark skipped or planned tests as passed. Do not run a later phase automatically.
