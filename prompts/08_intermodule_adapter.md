# One-to-one Bell code-code adapter

Read `AGENTS.md` and `STATUS.md` first. Complete only this phase, update the status log, and stop.

Use the Anaconda environment `tour_de_gross` for every Python install, build and test (`conda activate tour_de_gross`, or `conda run --no-capture-output -n tour_de_gross ...`). Read `docs/DEVELOPMENT.md` for setup. Keep external source checkouts under `/home/quantum_teresheys/workspace/tour_de_gross_design_bundle/external_libs` (repository-relative `external_libs/` on other machines); install their Python dependencies into this environment. Before modifying any external library, fork it under the user's GitHub account and work from that fork; retain upstream attribution, licenses, exact commits and source hashes. Put main simulation code under `src/gross_design_bandle/`, with benchmark code in its separate `bench/` namespace. These paths supersede the earlier proposed `bb_surgery` / `bb_surgery_bench` layout; they do not introduce implemented simulation APIs.

## Task

Implement Fig. 13(b) for X1 on two distinct gross blocks. Keep both sets of bridge data qubits; add Bell-mediated identifying X checks and joint cycle checks. Omit the two in-module triangular bridge checks. Validate the physical partition of each cross-module check and its readout XOR. Build the full-two-block-centralizer K47 profile and implement the printed K23 profile only after its actual rows are source-verified.

## Tests and scope limit

Implement B05, C-level Bell connectivity checks and D-level inter-boundary tests. Check k_merged=23 but do not confuse that dimension with the action-matrix row count. Generate a C=10 circuit and explicit active/installed resource ledgers. Do not measure each module's logical separately.

## Acceptance

Correct joint projector, preservation of remaining logical information, legal Bell schedule, explicit observable-profile provenance and transparent O1 status.

## Handoff

Summarize files changed, commands actually run, evidence paths, failures and unresolved scientific assumptions. Update `STATUS.md` with the next prompt and a short reproducible command sequence. Do not mark skipped or planned tests as passed. Do not run a later phase automatically.
