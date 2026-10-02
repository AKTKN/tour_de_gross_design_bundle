# Agent instructions for the BB surgery reproduction project

## Development environment and dependency ownership

Use the Anaconda environment `tour_de_gross` for every Python install, build and test (`conda activate tour_de_gross`, or `conda run --no-capture-output -n tour_de_gross ...`). Read `docs/DEVELOPMENT.md` for setup. Keep external source checkouts under `/home/quantum_teresheys/workspace/tour_de_gross_design_bundle/external_libs` (repository-relative `external_libs/` on other machines); install their Python dependencies into this environment. Before modifying any external library, fork it under the user's GitHub account and work from that fork; retain upstream attribution, licenses, exact commits and source hashes. Put main simulation code under `src/gross_design_bandle/`, with benchmark code in its separate `bench/` namespace. These paths supersede the earlier proposed `bb_surgery` / `bb_surgery_bench` layout; they do not introduce implemented simulation APIs.

## Scope and scientific contract

Build physical Stim generators and a Relay-BP benchmark for arXiv:2506.03094v1 Appendix A.7 / Figure 15. Read `docs/ARCHITECTURE.md`, `docs/REPRODUCTION_SPEC.md`, `docs/VALIDATION_PLAN.md` and `STATUS.md` before editing. PDF equation numbering is canonical. Follow one prompt in `prompts/` at a time.

The repository currently contains a design, reference transcriptions and algebra-audit utilities. It does not contain a validated production simulator. Do not describe planned APIs as existing. Do not import printed Table-6 rates as simulated observations.

## Non-negotiable invariants

1. Keep code/convention, graph/ports, signed Pauli algebra, physical schedule, detector flows, noise catalogue and benchmark observables separate.
2. Use exact GF(2) arithmetic and signed Paulis for scientific validation. Y1 is i X1 Z1; a Y measurement is not sequential X and Z measurements.
3. Preserve the selected reference LPU cycles. Prove omitted-cycle redundancy in the full deformed group; do not demand a full independent graph cycle basis or silently add one.
4. Use the one-to-one Bell-check adapter, explicit physical qubits, Bell readout XORs and real noisy shifts. Do not substitute ideal MPPs or metadata permutations inside noisy operations.
5. Never hide detector mistakes with gauge-detector flags, dropped detectors or unrecorded changed boundary conditions.
6. Keep joint X/Z fault correlations. Preserve and document primitive multiplicities and admission masks. Compact DEM size is not Table-6 N by definition.
7. Strict paper configuration must fail closed on unresolved O1--O5 fields. Full-two-block K47 and published inter K23 are distinct profiles. Do not manufacture an unnamed 23-row subset.
8. Do not silently translate historical Relay parameters by name, append OSD, discard nonconvergence or tune a reproduction decoder against target rates.
9. Tests must not assert an unproved distance lower bound. Save solver bounds and independently checked witnesses.
10. No long Monte Carlo jobs, cluster submissions, network writes or upstream repository changes without an explicit user request. A small local pilot is permitted only by its phase prompt and with a fixed budget.

## Workflow

Make small cohesive changes. Write the relevant negative test before or together with a fix. After each phase, run its acceptance tests, update `STATUS.md` with commands and evidence paths, list unresolved issues and stop. Each Codex session must stop after its phase. When the user explicitly launches `prompts/scripts/run_codex_pipeline.sh` or its tmux wrapper for a bounded phase interval, the outer controller may submit the next prompt in a new session after its acceptance gates pass. This is the user-requested automation exception; it does not authorize phases outside that interval, an unapproved pilot/campaign, or automatic expensive retries. Do not repeatedly retry an expensive solver or benchmark to make a test pass.

Preserve existing user code and configuration. Read donor licenses before copying; retain attribution and source commit/path. Prefer a thin adapter when possible. Keep network/GAP/distance-search side effects out of imports and default CI. Freeze external versions and record source blob hashes; do not treat a mutable main branch as a lockfile.

`reference/*.json` and `reference/table6.csv` are scientific fixtures. Modify them only with a source-backed correction, an explicit explanation and an updated audit. Avoid regenerating them from the same new code being tested; keep a genuinely independent oracle.

## Currently runnable commands

```bash
python -m pip install -r requirements-audit.txt
python -m pytest -q tests/test_reference.py
python tools/audit_reference.py --output evidence/algebra_audit.json
python tools/reconstruct_fits.py --output evidence/reference_fits.csv
cd report && pdflatex -interaction=nonstopmode -halt-on-error report.tex
```

Commands for the proposed `bb-surgery` CLI in the plan are future interfaces until implemented. Do not report skipped Stim/Relay tests as executed tests. This environment's delivered evidence is NumPy/SciPy-only.

## Definition of done for a phase

Code/imports pass; specified positive and negative tests pass; scientific assumptions are explicit; all changed artifacts have provenance; logs distinguish actual results from placeholders; STATUS records the next prompt and blockers. A phase can be complete while strict paper-equivalent sampling remains blocked. Never fabricate a passed gate or a missing source definition.
