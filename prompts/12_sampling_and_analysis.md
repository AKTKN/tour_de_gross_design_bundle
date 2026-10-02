# Sampling, spectra and reproducible result records

Read `AGENTS.md` and `STATUS.md` first. Complete only this phase, update the status log, and stop.

Use the Anaconda environment `tour_de_gross` for every Python install, build and test (`conda activate tour_de_gross`, or `conda run --no-capture-output -n tour_de_gross ...`). Read `docs/DEVELOPMENT.md` for setup. Keep external source checkouts under `/home/quantum_teresheys/workspace/tour_de_gross_design_bundle/external_libs` (repository-relative `external_libs/` on other machines); install their Python dependencies into this environment. Before modifying any external library, fork it under the user's GitHub account and work from that fork; retain upstream attribution, licenses, exact commits and source hashes. Put main simulation code under `src/gross_design_bandle/`, with benchmark code in its separate `bench/` namespace. These paths supersede the earlier proposed `bb_surgery` / `bb_surgery_bench` layout; they do not introduce implemented simulation APIs.

## Branch and publication workflow

Implement this phase on a dedicated `feature/<phase-stem>` branch in a separate Git worktree created from validated `main`. Switch the working directory to that worktree before editing and testing; keep the main checkout clean. Under the tmux pipeline, the controller provides the branch/worktree and owns Git publication: finish the phase and its validation, then stop so it can rerun acceptance tests, commit the feature, merge it to `main`, and atomically push the feature branch and `main` to `origin`. Outside the pipeline, perform that same sequence yourself after validation passes. Do not merge or publish failed/incomplete work, force-push, discard existing edits, or push external upstream repositories. Preserve the feature worktree on failure for review. Record the branch, worktree, validation commands and publication outcome in the handoff.

## Task

Implement independent Bernoulli and exact-uniform fixed-weight samplers over the identical admitted primitive catalogue. Use chunked sparse XOR syndrome/logical accumulation and compiled batch decoding. Add append-only result storage, deterministic per-chunk stream derivation, resume deduplication and controlled decoder threading. Implement the Table-6 ansatz, binomial integration, publication-compatible selection, bootstrap and separately labeled likelihood fits.

## Tests and scope limit

Implement F03--F05 as revised in `docs/VALIDATION_PLAN.md`. First exhaustively check tiny models and their Bernoulli/binomial-mixture identity. Then check a physical gross idle model deterministically through the joint H/Lambda matrices and compiled Relay batch path using fixed zero and nonzero error vectors. This gross check is an integration test, not a sampled rate estimate. A smoke pilot, if run, is limited to at most 256 shots per selected point, three selected points and 120 seconds total, and must be labeled as non-performance evidence. The earlier stopped attempt already used three tiny Bell pilot points; retain those records and do not silently reset or extend its budget. Zero failures remain upper bounds. Preserve all Y w>80 and all w<w0 events. Do not require statistical agreement of Bernoulli and fixed-weight estimators from this pilot; reserve that comparison for a separately budgeted later job with prespecified precision or target failures and a maximum shot/time cap.

## Efficient validation and artifact reuse

Read `docs/VALIDATION_WORKFLOW.md` before writing tests. Use the minimum set of
meaningful tests for this phase: one positive behavior check and its material
negative cases, sharing expensive fixtures. Avoid assertions about serialization
spelling, duplicate random seeds and re-exhausting unchanged primitives.

Use strict Stim DEM plus raw reference-record signs for large C10/C18 harnesses;
keep independent signed propagation and exhaustive Bell/gate oracles on small
fixtures. Preserve all named logical rows, joint X/Z faults and admission maps.
Run the smallest failing node with `pytest -xq` first, then the affected phase.
Run final regression and export once after source stabilizes, sequentially.
Do not repeatedly restart a full suite/export after an unrelated assertion fix.
Cache numerical artifacts, never a test pass. Do not mark incomplete runs passed.

Use `build_fault_model(..., cache_dir=...)` or the controller-provided
`GROSS_DESIGN_CACHE_DIR`. Reuse physical signatures across probabilities/profiles
and structural matrices across p changes. Export with
`bench.artifacts.export_fault_model`; native CSC/sparse-signature/map arrays and
checksummed manifests replace expanded catalogue JSON and repeated ZIP writes.
Keep legacy JSON/NPZ opt-in for a real consumer. Hash relevant numerical inputs
and implementations, not all test/doc files for numerical-cache invalidation.
Record cold/warm timing, cache reuse/invalidation and changed coverage in STATUS.
Implementation/test limits are 10800s/1800s; these never enlarge pilot/campaign
budgets or authorize automatic retries.

## Acceptance

Tiny exact enumeration proves the sampling mixture identity and rate normalization; a physical gross idle model reaches joint H/Lambda evaluation and Relay batch decoding with fixed error vectors; normalization and finite-tail bounds are correct; data/chunks and priors are reproducible; no target-fit numbers are inserted as observations. The bounded smoke pilot and any zero-failure strata are reported with their uncertainty, without an estimator-agreement claim.
Map both `test_F03_exact_subsets_and_bernoulli_mixture` and `test_F03_gross_idle_deterministic_joint_path` to the F03 controller gate in the structured handoff; a tiny-only F03 mapping is incomplete.

## Handoff

Summarize files changed, commands actually run, evidence paths, failures and unresolved scientific assumptions. Update `STATUS.md` with the next prompt and a short reproducible command sequence. Do not mark skipped or planned tests as passed. Do not run a later phase automatically.
