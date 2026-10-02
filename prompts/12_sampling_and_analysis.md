# Sampling, spectra and reproducible result records

Read `AGENTS.md` and `STATUS.md` first. Complete only this phase, update the status log, and stop.

Use the Anaconda environment `tour_de_gross` for every Python install, build and test (`conda activate tour_de_gross`, or `conda run --no-capture-output -n tour_de_gross ...`). Read `docs/DEVELOPMENT.md` for setup. Keep external source checkouts under `/home/quantum_teresheys/workspace/tour_de_gross_design_bundle/external_libs` (repository-relative `external_libs/` on other machines); install their Python dependencies into this environment. Before modifying any external library, fork it under the user's GitHub account and work from that fork; retain upstream attribution, licenses, exact commits and source hashes. Put main simulation code under `src/gross_design_bandle/`, with benchmark code in its separate `bench/` namespace. These paths supersede the earlier proposed `bb_surgery` / `bb_surgery_bench` layout; they do not introduce implemented simulation APIs.

## Branch and publication workflow

Implement this phase on a dedicated `feature/<phase-stem>` branch in a separate Git worktree created from validated `main`. Switch the working directory to that worktree before editing and testing; keep the main checkout clean. Under the tmux pipeline, the controller provides the branch/worktree and owns Git publication: finish the phase and its validation, then stop so it can rerun acceptance tests, commit the feature, merge it to `main`, and atomically push the feature branch and `main` to `origin`. Outside the pipeline, perform that same sequence yourself after validation passes. Do not merge or publish failed/incomplete work, force-push, discard existing edits, or push external upstream repositories. Preserve the feature worktree on failure for review. Record the branch, worktree, validation commands and publication outcome in the handoff.

## Task

Implement independent Bernoulli and exact-uniform fixed-weight samplers over the identical admitted primitive catalogue. Use chunked sparse XOR syndrome/logical accumulation and compiled batch decoding. Add append-only result storage, deterministic per-chunk stream derivation, resume deduplication and controlled decoder threading. Implement the Table-6 ansatz, binomial integration, publication-compatible selection, bootstrap and separately labeled likelihood fits.

## Tests and scope limit

Implement F03--F05. First exhaustively check tiny models. Then run only a smoke pilot of at most 256 shots per selected point and at most three accessible points, with a wall-time cap and explicit indication that it is not performance evidence. Zero failures remain upper bounds. Preserve all Y w>80 and all w<w0 events.

## Acceptance

Samplers agree on tiny exact cases; normalization and finite-tail bounds correct; data/chunks and priors reproducible; no target-fit numbers inserted as observations.

## Handoff

Summarize files changed, commands actually run, evidence paths, failures and unresolved scientific assumptions. Update `STATUS.md` with the next prompt and a short reproducible command sequence. Do not mark skipped or planned tests as passed. Do not run a later phase automatically.
