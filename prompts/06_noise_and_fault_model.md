# Independent noise and primitive-fault catalogue

Read `AGENTS.md` and `STATUS.md` first. Complete only this phase, update the status log, and stop.

Use the Anaconda environment `tour_de_gross` for every Python install, build and test (`conda activate tour_de_gross`, or `conda run --no-capture-output -n tour_de_gross ...`). Read `docs/DEVELOPMENT.md` for setup. Keep external source checkouts under `/home/quantum_teresheys/workspace/tour_de_gross_design_bundle/external_libs` (repository-relative `external_libs/` on other machines); install their Python dependencies into this environment. Before modifying any external library, fork it under the user's GitHub account and work from that fork; retain upstream attribution, licenses, exact commits and source hashes. Put main simulation code under `src/gross_design_bandle/`, with benchmark code in its separate `bench/` namespace. These paths supersede the earlier proposed `bb_surgery` / `bb_surgery_bench` layout; they do not introduce implemented simulation APIs.

## Task

Implement the three noise profiles in REPRODUCTION_SPEC. Lower independent Pauli faults and retain location/probability/multiplicity metadata before any DEM compaction. Build H and Lambda together and export maps between raw locations, equal-q copies, admitted sampling variables and any decoder grouping. Choose no zero-column admission rule silently; keep O4 explicit until Table-6 N is explained.

## Tests and scope limit

Implement D03 and E01/E02. Exhaustively compare tiny-circuit fault signatures to Stim and analytically validate duplicate cancellation. Add tests for zero-detector logical faults, both-sector correlations and nested repeats. Generate gross memory and X1 audit artifacts. No production Monte Carlo.

## Acceptance

Each primitive fault has independently checked signatures; all copies/admission decisions traceable; categorical and independent models cannot share a misleading profile ID; N discrepancy reports are informative.

## Handoff

Summarize files changed, commands actually run, evidence paths, failures and unresolved scientific assumptions. Update `STATUS.md` with the next prompt and a short reproducible command sequence. Do not mark skipped or planned tests as passed. Do not run a later phase automatically.
