# Signed Pauli algebra and BB conventions

Read `AGENTS.md` and `STATUS.md` first. Complete only this phase, update the status log, and stop.

Use the Anaconda environment `tour_de_gross` for every Python install, build and test (`conda activate tour_de_gross`, or `conda run --no-capture-output -n tour_de_gross ...`). Read `docs/DEVELOPMENT.md` for setup. Keep external source checkouts under `/home/quantum_teresheys/workspace/tour_de_gross_design_bundle/external_libs` (repository-relative `external_libs/` on other machines); install their Python dependencies into this environment. Before modifying any external library, fork it under the user's GitHub account and work from that fork; retain upstream attribution, licenses, exact commits and source hashes. Put main simulation code under `src/gross_design_bandle/`, with benchmark code in its separate `bench/` namespace. These paths supersede the earlier proposed `bb_surgery` / `bb_surgery_bench` layout; they do not introduce implemented simulation APIs.

## Task

Extend the existing `src/gross_design_bandle/` scaffold with exact GF(2)/signed symplectic primitives. Implement BBCodeSpec, CodeData and a convention adapter. Load the frozen gross/two-gross fixtures and reconstruct the four base logicals and all twelve pairs. Provide JSON serialization, immutable IDs and explicit block labels. Add a small verified BB fixture for debugging, deriving its own logical labels instead of assuming X7 exists.

## Tests and scope limit

Implement A01/A02/A06 in VALIDATION_PLAN. Compare with the independent delivered audit; do not replace it with calls into the new implementation. Check donor check/qubit permutations explicitly. No physical scheduling yet.

## Acceptance

Ranks 66/66 and 138/138; canonical 12-pair bases; signed Pauli truth tables and shift quotient tests pass; malformed or mismatched conventions are rejected.

## Handoff

Summarize files changed, commands actually run, evidence paths, failures and unresolved scientific assumptions. Update `STATUS.md` with the next prompt and a short reproducible command sequence. Do not mark skipped or planned tests as passed. Do not run a later phase automatically.
