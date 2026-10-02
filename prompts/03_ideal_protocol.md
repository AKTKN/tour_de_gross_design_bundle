# Ideal measurement protocol and split frame

Read `AGENTS.md` and `STATUS.md` first. Complete only this phase, update the status log, and stop.

Use the Anaconda environment `tour_de_gross` for every Python install, build and test (`conda activate tour_de_gross`, or `conda run --no-capture-output -n tour_de_gross ...`). Read `docs/DEVELOPMENT.md` for setup. Keep external source checkouts under `/home/quantum_teresheys/workspace/tour_de_gross_design_bundle/external_libs` (repository-relative `external_libs/` on other machines); install their Python dependencies into this environment. Before modifying any external library, fork it under the user's GitHub account and work from that fork; retain upstream attribution, licenses, exact commits and source hashes. Put main simulation code under `src/gross_design_bandle/`, with benchmark code in its separate `bench/` namespace. These paths supersede the earlier proposed `bb_surgery` / `bb_surgery_bench` layout; they do not introduce implemented simulation APIs.

## Task

Implement the merge/repeat/split state machine and symbolic edge-readout frame. Build ideal-oracle circuits or exact tiny Kraus maps with explicit signed Paulis. For a connected graph, solve B^T t=z using a chosen root and track Q=product P_v^t_v. Test the corrected instrument on arbitrary states, including reference-entangled states. Ideal MPP is allowed in this oracle module and must be marked as ideal-only.

## Tests and scope limit

Implement B01--B04 initially on two vertices, a triangle and a small BB code; then gross X. Include negative tests for a missing split frame and a Y phase error. Do not create a noisy logical MPP substitute.

## Acceptance

Projector semantics and preservation of unmeasured logical coherence verified; root/path choices agree; all outcomes and frame terms have symbolic IDs.

## Handoff

Summarize files changed, commands actually run, evidence paths, failures and unresolved scientific assumptions. Update `STATUS.md` with the next prompt and a short reproducible command sequence. Do not mark skipped or planned tests as passed. Do not run a later phase automatically.
