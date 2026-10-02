# Project status

Baseline date: 2026-10-02. Target: arXiv:2506.03094v1 PDF.

## Completed in this delivery

The theory/design report, module architecture, reproduction contract, validation plan and staged Codex prompts have been written. Gross and two-gross polynomials, logical bases, selected cycles, shared vertices and bridge paths have been transcribed into reference JSON. The independent algebra audit checks code ranks, canonical logical pairing, selected-cycle validity, omitted-cycle membership in the combined binary stabilizer span, commutation and one-logical-loss ranks for X, XX, Y and an inter-XX graph reconstruction. It also derives x/y shift logical actions from the physical support permutation. Nine utility tests pass; see `evidence/pytest_reference.txt` and `evidence/algebra_audit.json`.

`evidence/reference_fits.csv` contains evaluations of rounded Table-6 fit parameters only. These are not sampled data or a reproduction of the published confidence bands.

## Not implemented / not run

No production `gross_design_bandle` simulation implementation, physical Stim surgery circuit, Bell schedule, detector/observable compiler, signed instrument verification, distance proof, Relay adapter or Monte Carlo reproduction has been completed. Stim, qLDPC and Relay were not installed or executed in the delivery environment. The algebra audit is not a circuit-distance certification and its rank calculations are phase-blind.

## Specification blockers for exact reproduction

O1: define the paper's inter-module 23-row logical-action observable profile; the full two-block centralizer has rank 47.
O2: source-verify historical Table-7 parameters against the chosen Relay implementation and prior/column policy.
O3: freeze concrete scheduling, shift representative, gate lowering and ideal/noisy boundary details.
O4: establish the primitive fault catalogue and admission/merging convention that yield Table-6 N.
O5: obtain original data/counts/grids/bootstrap settings for exact point-and-band replication.

These blockers need not stop independent construction and validation. Two-gross surgery remains an explicitly new extension of Figure 15.

## Setup completed (2026-10-02)

Created Anaconda environment `tour_de_gross`: Python 3.11.17, NumPy 2.4.6, SciPy 1.17.1 and pytest 9.1.1. Added an editable `gross-design-bandle` 0.0.1 distribution at `src/gross_design_bandle/`; it contains only a docstring scaffold and no simulation API. Updated AGENTS, all fourteen prompts and the architecture with the environment, package namespace and external-library policy. External checkouts belong in `external_libs/` and must be forked before edits; none were fetched or installed during setup.

Added `environment.yml`, a resolved pip audit lock and a Linux-64 explicit Conda artifact lock. Added ignore rules for simulation outputs, caches, secrets, external checkouts and report build products, retaining the four curated delivery evidence files. Preserved the original delivery checksums as `SHA256SUMS.delivery.txt` (its report PDF was absent from the supplied workspace); the current index is `SHA256SUMS.txt`.

Commands actually run:

```bash
conda create -n tour_de_gross python=3.11 pip -y
conda run --no-capture-output -n tour_de_gross python -m pip install -r requirements-audit.txt
conda list -n tour_de_gross --explicit > locks/conda-linux-64.explicit.txt
conda run --no-capture-output -n tour_de_gross python -m pip freeze > requirements-audit-lock.txt
conda run --no-capture-output -n tour_de_gross python -m pip install --no-build-isolation -e .
conda run --no-capture-output -n tour_de_gross python -m pytest -q tests/test_reference.py
conda run --no-capture-output -n tour_de_gross python tools/audit_reference.py --output evidence/setup/algebra_audit.json
conda run --no-capture-output -n tour_de_gross python tools/reconstruct_fits.py --output evidence/setup/reference_fits.csv
conda run --no-capture-output -n tour_de_gross python -m pip check
```

Verification: **9 passed in 2.03s**; package and NumPy/SciPy imports passed from the named environment; pip reports no broken requirements. Algebra audit exactly matches delivery JSON. Published-fit evaluation exited successfully and matches delivery within relative tolerance 1e-14 (four values differ in the final floating-point digits); the curated CSV is unchanged. Eight ignored-path and five retained-path checks passed, and all five reference fixture hashes match the delivery manifest. Local logs and outputs: `evidence/setup/{pytest_reference.txt,imports.txt,pip_check.txt,gitignore_and_fixtures.txt,algebra_audit.json,reference_fits.csv}`. New generated evidence is ignored; these results are recorded here for GitHub review.

Git initialized with `main`. Published to the user-approved private repository `https://github.com/AKTKN/tour_de_gross_design_bundle` using `gh repo create AKTKN/tour_de_gross_design_bundle --private --source=. --remote=origin --push` (with a description). Verified `isPrivate=true`, default branch `main`, and matching local/remote commit via `gh repo view` and `git ls-remote`. Git whitespace checking passed with `cr-at-eol` enabled for the preserved CSV fixtures. Current checksums passed. Setup does not complete phase 00. O1--O5 remain unresolved, external licenses/blob hashes are not newly audited, and no Stim/Relay tests or sampling were run. See `docs/DEVELOPMENT.md` for setup on another machine.

## Prompt automation implemented (2026-10-02)

Adapted the five user-supplied files in `prompts/scripts/` for this repository. Added a standard-library Python controller, pytest outcome reporter and JSON configuration for phases 00–13; updated the result schema and footer. The tmux runner uses `tour_de_gross`, root package paths and local external-library policy. AGENTS now records the user-requested exception permitting the outer controller to submit subsequent prompts in separate sessions within an explicitly launched interval. Each phase session still stops on completion.

Acceptance checks require valid structured results, exact configured gate coverage, evidence files, an updated STATUS and independently rerun pytest node IDs. A skipped, xfailed, missing or failed mapped test cannot pass. The controller preserves unique run logs, locks concurrent runs, guards source/control/reference hashes and detects changed workspace state on resume; explicit `--revalidate` reruns prior acceptance checks after edits. Pilot 12 needs `--allow-pilot` with 256 shots per point / 3 points / 120 seconds total pilot time; campaign 13 needs a validated positive JSON compute budget. Workload shot/profile limits must be enforced by the future sampler; the controller bounds child process groups and does not prove scientific test sufficiency or resolve O1–O5. No commits, pushes, fixture edits or implementation jobs are performed by the runner.

Commands actually run for infrastructure verification:

```bash
conda run --no-capture-output -n tour_de_gross python -m pytest -q tests/test_pipeline.py tests/test_reference.py
for script in prompts/scripts/*.sh; do bash -n "$script"; done
prompts/scripts/run_codex_pipeline.sh --preflight
prompts/scripts/run_codex_pipeline.sh --list --through 13
prompts/scripts/start_codex_pipeline_tmux.sh --dry-run --through 11
codex --version
codex login status
codex exec --help
tmux -V
```

Verification: **51 passed in 18.44s**, with no skips; Bash syntax checks, local preflight and both plan commands passed. Evidence: `evidence/pipeline/pytest.txt` and local CLI/preflight/plan logs under `evidence/pipeline/`. Infrastructure tests use fake model commands and temporary repositories; the tmux smoke test ran a real isolated temporary server with fake Codex and confirmed duplicate-session rejection and a retained completed pane. No paid model request, production implementation session, solver, Stim/Relay execution or Monte Carlo was launched. CLI observed: `codex-cli 0.157.1`, tmux `3.2a`, `Logged in using ChatGPT`; these establish local installation/authentication, not live model access. Usage and exact controls are documented in `prompts/scripts/README.md`.

Prompt 00 remains unstarted. When ready, launch only that phase with `prompts/scripts/start_codex_pipeline_tmux.sh --through 00`, or explicitly authorize automatic progression through decoder integration with `--through 11`.

## Next action

Run `prompts/00_source_audit.md` in the target development repository. Do not skip to a long simulation prompt. Record a source-lock check and backend capability matrix first.

## Phase log template

| Phase | State | Commands actually run | Evidence | Unresolved items |
|---|---|---|---|---|
| Delivery reference audit | passed | pytest + audit_reference + reconstruct_fits | evidence/ | scope limited as above |
| Development setup | passed | Conda create, editable install, nine tests, algebra audit, fit reconstruction, pip/ignore/fixture checks | evidence/setup/ (local), locks/, this status | O1--O5; prompt 00 remains next |
| Prompt automation | passed | infrastructure/reference pytest, Bash syntax, CLI preflight, list/dry-run, isolated tmux with fake Codex | evidence/pipeline/ (local), prompts/scripts/README.md | O1--O5; implementation not launched |
| 00 source audit | not started | — | — | O1--O5 |
