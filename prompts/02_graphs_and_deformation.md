# Graphs, ports and deformation certificates

Read `AGENTS.md` and `STATUS.md` first. Complete only this phase, update the status log, and stop.

Use the Anaconda environment `tour_de_gross` for every Python install, build and test (`conda activate tour_de_gross`, or `conda run --no-capture-output -n tour_de_gross ...`). Read `docs/DEVELOPMENT.md` for setup. Keep external source checkouts under `/home/quantum_teresheys/workspace/tour_de_gross_design_bundle/external_libs` (repository-relative `external_libs/` on other machines); install their Python dependencies into this environment. Before modifying any external library, fork it under the user's GitHub account and work from that fork; retain upstream attribution, licenses, exact commits and source hashes. Put main simulation code under `src/gross_design_bandle/`, with benchmark code in its separate `bench/` namespace. These paths supersede the earlier proposed `bb_surgery` / `bb_surgery_bench` layout; they do not introduce implemented simulation APIs.

## Task

Implement stable edge IDs, incidence matrices, port maps, dressing and cycle checks. Load the exact selected cycles and ladders in the reference JSON. Construct half/full LPUs with their identified shared vertex. Implement a generic full-cycle-basis oracle separately from the paper profile. Export explicit old-check dressing and omitted-cycle span certificates, including phases, and compute the input logical subspace fixed by the deformation.

## Tests and scope limit

Implement A03--A05. Test X1, X1 X7 and Y1 algebra for both code sizes without creating physical circuits. Construct the two-block inter-XX graph as an algebraic object only. Reject unjustified cycle deletions and extra measured logical factors.

## Acceptance

Published full-LPU counts reproduced; all commutations/products/spans verified; single measurement fixes exactly one requested logical degree of freedom; actual certificate files saved.

## Handoff

Summarize files changed, commands actually run, evidence paths, failures and unresolved scientific assumptions. Update `STATUS.md` with the next prompt and a short reproducible command sequence. Do not mark skipped or planned tests as passed. Do not run a later phase automatically.
