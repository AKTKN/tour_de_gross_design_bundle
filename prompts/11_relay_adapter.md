# Joint Relay-BP integration

Read `AGENTS.md` and `STATUS.md` first. Complete only this phase, update the status log, and stop.

Use the Anaconda environment `tour_de_gross` for every Python install, build and test (`conda activate tour_de_gross`, or `conda run --no-capture-output -n tour_de_gross ...`). Read `docs/DEVELOPMENT.md` for setup. Keep external source checkouts under `/home/quantum_teresheys/workspace/tour_de_gross_design_bundle/external_libs` (repository-relative `external_libs/` on other machines); install their Python dependencies into this environment. Before modifying any external library, fork it under the user's GitHub account and work from that fork; retain upstream attribution, licenses, exact commits and source hashes. Put main simulation code under `src/gross_design_bandle/`, with benchmark code in its separate `bench/` namespace. These paths supersede the earlier proposed `bb_surgery` / `bb_surgery_bench` layout; they do not introduce implemented simulation APIs.

## Task

Implement a thin Relay adapter accepting the joint sparse H, priors and Lambda mapping. Source-verify O2 before exposing a historical Table-7 backend. Retain raw paper parameters and resolved backend parameters in the manifest. Support explicit float precision, gamma randomness, maximum sets/iterations, candidate selection and nonconvergence reporting. Record any variable merging as a separate decoder-graph profile.

## Tests and scope limit

Implement E03--E05 with synthetic and small circuit faults. Test scalar/batch equivalence and Hc=sigma. Do not add OSD fallback or separate-sector decoding in the reference profile. Verify the fixed-weight decoder prior policy, including any claimed uniform-prior scaling invariance.

## Acceptance

Decoder semantics and parameters auditable; invalid corrections counted; both X/Z correlations retained; fixed test vectors and source evidence establish the compatibility label.

## Handoff

Summarize files changed, commands actually run, evidence paths, failures and unresolved scientific assumptions. Update `STATUS.md` with the next prompt and a short reproducible command sequence. Do not mark skipped or planned tests as passed. Do not run a later phase automatically.
