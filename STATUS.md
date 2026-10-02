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

Acceptance checks require valid structured results, exact configured gate coverage, evidence files, an updated STATUS and independently rerun pytest node IDs. A skipped, xfailed, missing or failed mapped test cannot pass. The controller preserves unique run logs, locks concurrent runs, guards source/control/reference hashes and detects changed workspace state on resume; explicit `--revalidate` reruns prior acceptance checks after edits. Pilot 12 needs `--allow-pilot` with 256 shots per point / 3 points / 120 seconds total pilot time; campaign 13 needs a validated positive JSON compute budget. Workload shot/profile limits must be enforced by the future sampler; the controller bounds child process groups and does not prove scientific test sufficiency or resolve O1–O5. That initial runner revision did not perform commits or pushes; the branch/publication workflow below supersedes that behavior. No scientific fixture edits or production implementation jobs have been run.

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

## Feature branches and publication implemented (2026-10-02)

All fourteen phase prompts now require a dedicated feature branch and separate Git worktree, validation before merge, and commit/push after successful implementation. Added the same contract to AGENTS and the pipeline footer. Under automation the controller owns publication; standalone phase work follows the same sequence. The JSON config specifies `main`, `origin` and `feature/` explicitly.

The controller now requires clean synchronized main, runs Codex and acceptance checks in `.codex-pipeline/tour-de-gross/worktrees/<phase-stem>/`, saves a tracked `validation/phase_<id>.json` report and refreshes source checksums before committing. It creates a non-fast-forward merge, checks the merged tree against the validated candidate, atomically pushes feature/main and verifies both remote hashes before accepting a phase. Main/remote divergence, dirty main, fixture/control changes or commit-hook changes stop progression. Failed worktrees and branches are preserved; `--resume-feature` explicitly continues reviewed unfinished work. `--retry-publish` retries a validated candidate without rerunning Codex. Failed remote publication can leave a validated local merge pending, but does not silently count the phase accepted.

This workflow change was implemented on `feature/phase-branch-workflow` in `/home/quantum_teresheys/workspace/tour_de_gross_design_bundle_worktrees/phase-branch-workflow`. The prior uncommitted automation was first preserved in local commit `03cfc5a` on `feature/tmux-automation`, included in this feature's history. Production phase 00 remains unstarted and O1–O5 remain unresolved.

Verification: **56 passed in 37.57s**, with no skips. Bash syntax, Python compilation and the read-only phase-plan check passed. Acceptance command: `conda run --no-capture-output -n tour_de_gross python -m pytest -q tests/test_pipeline.py tests/test_reference.py`. Tests run real Git operations against temporary local bare remotes, fake Codex, and an isolated tmux server. They cover independent phase branches/worktrees, clean main, validation-before-merge, remote refs, failed validation, atomic push rejection/retry, commit-hook mutation and remote advancement. No live implementation model request, scientific sampling or upstream donor write was run. Logs are local under `evidence/branch_workflow/`.

## Per-run model and reasoning override (2026-10-02)

Added `--reasoning-effort {low,medium,high,xhigh,max}` alongside the existing `--model` option. For this request use `--model gpt-6.1-sol --reasoning-effort high`; `hard` is not an accepted effort value. The runner forwards an explicit `model_reasoning_effort="high"` CLI override and records model/effort overrides in run metadata. Omitted values inherit Codex settings. The user's global config remains unchanged (observed model `gpt-6.1-sol`, effort `medium`). Installed CLI now reports 0.160.0; its local model cache lists Sol and high reasoning. Local cache/login information does not establish live model access.

Implemented in the separate `feature/model-reasoning` worktree. Verification: `conda run --no-capture-output -n tour_de_gross python -m pytest -q tests/test_pipeline.py tests/test_reference.py` — **58 passed in 25.03s**, no skips. New tests check actual CLI argument forwarding/metadata with fake Codex and reject `hard` before launch. `--dry-run --through 00 --model gpt-6.1-sol --reasoning-effort high` passed. Local evidence: `evidence/model_reasoning/pytest.txt`. No live model request or implementation phase was launched; O1–O5 remain open and prompt 00 is still next.

## Next action

Phase 00 is complete for source/import auditing and algebra-only declarations. Next implementation prompt is `prompts/01_algebra_and_codes.md`, only in a new controller-authorized session after phase-00 acceptance and publication. This session stops at 00; strict paper-equivalent sampling remains blocked by O1--O5.

## Phase 00 source audit completed (2026-10-02)

Branch: `feature/00_source_audit`. Worktree: `/home/quantum_teresheys/workspace/tour_de_gross_design_bundle/.codex-pipeline/tour-de-gross/worktrees/00_source_audit`. Main checkout: `/home/quantum_teresheys/workspace/tour_de_gross_design_bundle`, unchanged/clean. Publication outcome: **not attempted; controller owns acceptance rerun, commit, merge and atomic push**. No fixture/control/AGENTS changes, external source patches, network writes, production circuits, solver searches, sampling or cluster work occurred. External read-only checkouts are at `/home/quantum_teresheys/workspace/tour_de_gross_design_bundle/external_libs/{qLDPC,SlidingWindowDecoder,relay,bicycle-architecture-compiler}`, with clean source trees and detached pinned HEADs. No fork was needed for read-only inspection/unmodified builds.

Deliverables: `docs/BACKEND_AUDIT.md`, `locks/source-lock.json`, `locks/environment-lock.json`, `locks/package-artifacts.json`, `locks/paper-sources.json`, `locks/requirements-phase00.txt`, `locks/conda-phase00-linux-64.explicit.txt`; read-only verification/import tools, a phase-00 manifest declaration validator under `src/gross_design_bandle/bench/`, and positive/negative source/API/manifest tests. All five fixture-pinned Git blobs match their commits and checkout bytes. Source lock additionally hashes inspected licenses, APIs, build metadata and Relay history. The observed environment imports Stim 1.16.0, qLDPC 0.4.0 from commit `60fc2cf465e880d6e64afacc933d33455d787bf4`, and Relay 0.2.2 built from commit `d185194ba0cb4101ced4340d82b2ee6d42f225f0` with its Cargo lock. Python 3.11.17 / NumPy 2.4.6 / SciPy 1.17.1 were preserved. qLDPC-installed source hashes also match the pinned checkout; installed backend binary/Python hashes are recorded separately. These are import/source locks, not circuit or decoder-equivalence certification.

Commands actually run for source acquisition, compatibility and installation (source reads/downloads authorized by phase 00):

```bash
conda run --no-capture-output -n tour_de_gross python -V
conda run --no-capture-output -n tour_de_gross python -m pip list
git clone --filter=blob:none --no-checkout https://github.com/qLDPCOrg/qLDPC.git /home/quantum_teresheys/workspace/tour_de_gross_design_bundle/external_libs/qLDPC
git -C /home/quantum_teresheys/workspace/tour_de_gross_design_bundle/external_libs/qLDPC checkout --detach 60fc2cf465e880d6e64afacc933d33455d787bf4
git clone --filter=blob:none --no-checkout https://github.com/trmue/relay.git /home/quantum_teresheys/workspace/tour_de_gross_design_bundle/external_libs/relay
git -C /home/quantum_teresheys/workspace/tour_de_gross_design_bundle/external_libs/relay checkout --detach d185194ba0cb4101ced4340d82b2ee6d42f225f0
git clone --filter=blob:none --no-checkout https://github.com/gongaa/SlidingWindowDecoder.git /home/quantum_teresheys/workspace/tour_de_gross_design_bundle/external_libs/SlidingWindowDecoder
git -C /home/quantum_teresheys/workspace/tour_de_gross_design_bundle/external_libs/SlidingWindowDecoder checkout --detach 05d6b1f478f2b044effdc7477278647dfb99db07
git clone --filter=blob:none --no-checkout https://github.com/qiskit-community/bicycle-architecture-compiler.git /home/quantum_teresheys/workspace/tour_de_gross_design_bundle/external_libs/bicycle-architecture-compiler
git -C /home/quantum_teresheys/workspace/tour_de_gross_design_bundle/external_libs/bicycle-architecture-compiler checkout --detach c99eb046f10b38de2412468ccded14ca38f1ee4c
curl -L --fail https://arxiv.org/pdf/2506.03094v1 -o /tmp/tour-de-gross-v1.pdf
pdftotext -layout /tmp/tour-de-gross-v1.pdf /tmp/tour-de-gross-v1.txt
curl -L --fail https://arxiv.org/pdf/2506.01779v1 -o /tmp/relay-bp-v1.pdf
pdftotext -layout /tmp/relay-bp-v1.pdf /tmp/relay-bp-v1.txt
conda run --no-capture-output -n tour_de_gross python -m pip install --dry-run --report evidence/phase00/install-plan.json /home/quantum_teresheys/workspace/tour_de_gross_design_bundle/external_libs/qLDPC relay-bp==0.2.2
conda run --no-capture-output -n tour_de_gross python -m pip install --report evidence/phase00/install.json /home/quantum_teresheys/workspace/tour_de_gross_design_bundle/external_libs/qLDPC maturin==1.12.6
CARGO_HOME=/tmp/phase00-cargo CARGO_TARGET_DIR=/tmp/phase00-relay-target conda run --no-capture-output -n tour_de_gross maturin build --release --locked --jobs 2 --manifest-path /home/quantum_teresheys/workspace/tour_de_gross_design_bundle/external_libs/relay/crates/relay_bp_py/Cargo.toml --out /tmp/phase00-relay-wheels
conda run --no-capture-output -n tour_de_gross python -m pip install --report evidence/phase00/relay-install.json /tmp/phase00-relay-wheels/relay_bp-0.2.2-cp311-cp311-manylinux_2_34_x86_64.whl
conda run --no-capture-output -n tour_de_gross python -m pip install --no-build-isolation -e .
conda run --no-capture-output -n tour_de_gross python tools/lock_sources.py
conda run --no-capture-output -n tour_de_gross python -m pip freeze --exclude-editable
conda list -n tour_de_gross --explicit
```

Also inspected source signatures, licenses, Relay Git history and paper PDF text with read-only `cat`, `rg`, `git show`, `git log` and `git ls-tree`; used arXiv/web release-link discovery. A local Conda Python heredoc saved pip artifact provenance, PDF/fixture hashes and Relay testdata filename inventory. Outputs are in the lock files and `evidence/phase00/`. Pip dry-run included registry Relay only to check dependency compatibility; the actual Relay install was built from the exact source commit, not that registry wheel. Rust build completed in 1m06s with two jobs. Optional decoder/Stim integration, compiler, gridsynth, GAP and upstream Monte Carlo examples were not run.

Validation commands actually run:

```bash
conda run --no-capture-output -n tour_de_gross python tools/audit_sources.py --output evidence/phase00/source-verification.json
conda run --no-capture-output -n tour_de_gross python tools/audit_backends.py --output evidence/phase00/backend-imports.json --environment-output locks/environment-lock.json
conda run --no-capture-output -n tour_de_gross python tools/audit_backends.py --output evidence/phase00/backend-imports.json
conda run --no-capture-output -n tour_de_gross python -m pytest -q tests/test_backends.py tests/test_source_audit.py tests/test_manifest.py tests/test_reference.py
conda run --no-capture-output -n tour_de_gross python -m pytest -q tests/test_pipeline.py tests/test_reference.py
conda run --no-capture-output -n tour_de_gross python -m pytest -q tests/test_backends.py tests/test_source_audit.py tests/test_manifest.py tests/test_reference.py tests/test_pipeline.py
conda run --no-capture-output -n tour_de_gross python tools/audit_reference.py --output evidence/phase00/algebra-audit.json
conda run --no-capture-output -n tour_de_gross python -m pip check
git diff --check
```

Final verification: **85 passed in 31.44s**, no skips/xfails. This includes all nine delivered utility tests and 27 new source/backend/manifest cases. Separate baseline regression run: **58 passed in 23.45s**. An intermediate phase run passed 35 tests before the final installed-source check was added. Initial failure is retained: the import probe assumed the README's nonexistent `RelayDecoderF32.par_decode_batch`, so its environment lock was not generated and the first pytest attempt had **1 failed, 34 passed**. Corrected the probe, added an explicit API absence assertion and reran validation. No failure was counted as a pass. The tiny deterministic Relay test uses a 2x3 matrix, explicit gammas, and a 12-iteration maximum per decode; it is not historical trace equivalence or production decoder integration. Stim tests strictly reject a random detector; no sampled shots were generated. The algebra audit remains phase-blind and is not a distance certificate. Pip and whitespace checks passed. Final checks found main and all external donor trees clean; fixture hashes were preserved.

Nonempty evidence: `evidence/phase00/{source-verification.json,backend-imports.json,pytest-initial.txt,pytest-phase00.txt,pytest-regressions.txt,pytest-final.txt,pip-check.txt,algebra-audit.json,fixture-hashes.json,relay-circuit-inventory.json,install-plan.json,install-plan.txt,install.json,install.txt,relay-build.txt,relay-install.json,relay-install.txt,editable-install.txt,pip-freeze.txt,initial-imports.txt}`. Generated evidence is intentionally local/ignored under the existing policy; locks, audit documentation and tests are tracked. Gate mapping is in the completion JSON and local `evidence/phase00/acceptance-gates.json`.

O1--O5 remain open. Recovered Relay-paper v1 Eqs. (1)--(4) / Algorithm 1, but Table-7 mapping (including 0.875 discount and gamma/rng_width), exact priors/columns and historical executable remain unverified. No original Figure-15 surgery/shift circuit/raw-data release was established in the bounded search; Relay supplies separate memory testdata, and the bicycle compiler is logical/resource software. The SlidingWindowDecoder memory builder has unresolved reuse licensing; no code was copied. Independent schedule derivation remains possible. These limitations do not block the next independent algebra phase, but every strict paper manifest currently fails closed; algebra-only declarations remain permitted. No source-backed fixture correction was identified or applied.

Reproducible short rerun: execute the source audit, import audit without `--environment-output`, full five-file pytest command and pip check shown above, from this feature worktree in `tour_de_gross`. Stop after this phase. Next prompt: `01_algebra_and_codes.md`; production construction/sampling is still future work.

## Phase log template

| Phase | State | Commands actually run | Evidence | Unresolved items |
|---|---|---|---|---|
| Delivery reference audit | passed | pytest + audit_reference + reconstruct_fits | evidence/ | scope limited as above |
| Development setup | passed | Conda create, editable install, nine tests, algebra audit, fit reconstruction, pip/ignore/fixture checks | evidence/setup/ (local), locks/, this status | O1--O5; prompt 00 remains next |
| Prompt automation | passed | infrastructure/reference pytest, Bash syntax, CLI preflight, list/dry-run, isolated tmux with fake Codex | evidence/pipeline/ (local), prompts/scripts/README.md | O1--O5; implementation not launched |
| Branch/worktree publication | passed | infrastructure/reference tests with real local Git remotes and fake Codex | evidence/branch_workflow/ (local), prompts/scripts/README.md | O1--O5; implementation not launched |
| 00 source audit | passed within source/import/manifest scope; publication pending controller | source/backend audits, locked imports, full pytest (85 passed), pip/whitespace checks | docs/BACKEND_AUDIT.md, locks/, evidence/phase00/ (local) | O1--O5; donor memory-builder reuse license; exact physical/data release not established; next prompt 01 |

## Phase 00 stopped-pipeline report repair (2026-10-02)

Investigated run `20261002T143701-260a48d3` on `feature/00_source_audit` in the existing phase worktree. The controller rejected the completion JSON before executing acceptance tests: `validate_result` rejects every reported `failed` command, including optional attempts. The JSON retained two superseded failures (the backend API probe and its dependent initial pytest run) alongside successful reruns. This was a completion-report failure; the earlier failures and fixes remain accurately documented above.

Preserved the original JSON as `runs/20261002T143701-260a48d3/00/result.before-repair.json` under the canonical `.codex-pipeline/tour-de-gross/` directory. Consolidated identical command entries to their final passed outcomes, retaining every attempt's outcome and explanation in notes. No failed outcome was relabeled as passed, no validator was weakened, and no pipeline controls, scientific fixtures or external sources were changed. Reproduced the original validator rejection before verifying the repaired report's schema, evidence and exact gate coverage. Local repair evidence: `evidence/phase00/recovery-gates.json` and `recovery-result.json`; original initial-failure logs are preserved.

Commands actually run in `tour_de_gross`: `python /tmp/tour_de_gross_repair_result.py` (report repair, negative rejection check, existing controller validation and acceptance rerun); `python tools/audit_sources.py --output evidence/phase00/recovery-source-verification.json`; `python -m pip check`; `git diff --check`. The repair helper invokes the existing `prompts/scripts/pipeline_check_tests.py` with `tests/test_reference.py`, `tests/test_pipeline.py` and all 27 mapped exact node IDs. Actual acceptance: **85 passed in 30.27s**, with every mapped setup/call/teardown passed and no skips or xfails. Canonical run evidence: `00/recovery-pytest.json` and `00/recovery-pytest.log`. Source verification and pip compatibility passed.

Publication outcome: not attempted; the original controller state remains stopped and phase 00 is not recorded as accepted/published. Controller-owned resume is `prompts/scripts/start_codex_pipeline_tmux.sh --through 00 --resume-feature --model gpt-6.1-sol --reasoning-effort high` (the retained dead tmux session must first be removed if it still exists). This resumes only phase 00 and reruns controller acceptance before commit/merge/push. O1--O5 and the phase-00 scientific limitations remain unchanged. No subsequent phase was started.

## Phase 00 resumed validation (2026-10-02, run 20261002T152609-6aa225c2)

Preserved and reviewed the existing phase-00 implementation and stopped-run history in branch `feature/00_source_audit`, worktree `/home/quantum_teresheys/workspace/tour_de_gross_design_bundle/.codex-pipeline/tour-de-gross/worktrees/00_source_audit`. Read AGENTS, STATUS, development instructions and all scientific contracts before validation. Rechecked the actual pinned qLDPC surgery, SlidingWindowDecoder memory-builder and Relay binding/recurrence/history files and license notices. No new dependency installation or source modification was needed. The source/environment locks and capability audit remain the preserved phase-00 deliverables.

Commands actually run for this resume:

```bash
conda run --no-capture-output -n tour_de_gross python tools/audit_sources.py --output evidence/phase00/resume-source-verification.json
conda run --no-capture-output -n tour_de_gross python tools/audit_backends.py --output evidence/phase00/resume-backend-imports.json
conda run --no-capture-output -n tour_de_gross python -m pytest -q tests/test_backends.py tests/test_source_audit.py tests/test_manifest.py tests/test_reference.py tests/test_pipeline.py
conda run --no-capture-output -n tour_de_gross python -m pip check
curl -L --fail --max-time 45 https://arxiv.org/pdf/2506.03094v1 -o /tmp/phase00-resume-tdg.pdf
curl -L --fail --max-time 45 https://arxiv.org/pdf/2506.01779v1 -o /tmp/phase00-resume-relay.pdf
pdftotext -layout /tmp/phase00-resume-tdg.pdf /tmp/phase00-resume-tdg.txt
pdftotext -layout /tmp/phase00-resume-relay.pdf /tmp/phase00-resume-relay.txt
conda run --no-capture-output -n tour_de_gross python /tmp/phase00_resume_verify.py
git diff --check
```

Also used read-only `cat`, `sed`, `rg`, `git status`, `git branch` and `git log` for contracts, upstream sources and local history, and arXiv HTML link discovery. Earlier temporary PDFs had been removed; fresh downloads match both PDF byte counts and SHA-256 hashes in `locks/paper-sources.json`. Rechecked Relay v1 PDF Eqs. (1)--(4) and p. 8 Algorithm 1 against the documented recurrence, and TdG Table 7 against its unresolved historical mapping. No scientific fixture correction was identified or applied.

Actual result: **85 passed in 34.98s**, including the nine delivered utility tests and all 27 mapped phase-00 cases, with no skips/xfails. Source verification checked all four pinned repositories and inspected license/API/history blobs offline. Backend tests confirmed installed versions/bytes, pinned qLDPC source correspondence and actual signatures; deterministic tiny Relay and strict Stim detector checks passed within their documented scope. Pip reports no broken requirements (only a nonwritable-cache warning). Main is clean, external trees are clean, and reference/AGENTS/pipeline-control bytes match main. The manifest package imports from this feature worktree. Whitespace checking passed.

Fresh nonempty evidence: `evidence/phase00/resume-source-verification.json`, `resume-backend-imports.json`, `resume-pytest.txt`, `resume-pip-check.txt`, and `resume-guards.json`. The guards evidence includes protected-file/PDF hashes, branch/worktree, clean main/donors, package path and exact gate mapping. The temporary read-only guard helper is `/tmp/phase00_resume_verify.py`. All four required gates (`source_lock`, `backend_capabilities`, `strict_manifest`, `negative_tests`) are mapped to existing exact pytest nodes in `evidence/phase00/acceptance-gates.json` and the completion JSON; the controller independently reruns them before publication. Generated evidence remains local/ignored according to the existing repository policy.

Additionally ran `conda run --no-capture-output -n tour_de_gross python /tmp/phase00_validate_handoff.py`: the unchanged controller's read-only `validate_result` accepted the completion schema, nonempty evidence and all four gates (27 exact nodes). It did not execute the pipeline or publish Git refs. Local report/evidence: `evidence/phase00/resume-result.json` and `resume-handoff-validation.json`. Historical failures remain in the earlier status/logs; this completion report records the current passed reruns.

O1--O5 remain open as documented in BACKEND_AUDIT: inter K23 generators; historical Relay semantics/priors/columns; physical schedule/shift/lowering/boundaries; primitive population/multiplicity/admission; original data/grids/bootstrap. No original Figure-15 physical surgery/shift release was established, and the memory-builder reuse license remains unresolved. These items prevent strict paper-equivalent sampling; none is assumed resolved or required to complete this source/import/declaration phase. Optional compiler/GAP/integration backends, production circuits, solvers and sampling were not run.

Publication outcome: **not attempted; controller owns acceptance, commit, merge and atomic push**. This session stops after phase 00. Next prompt is `prompts/01_algebra_and_codes.md` only in a subsequent authorized session after controller acceptance/publication; this run authorizes phases through 00 only. To reproduce validation, rerun the first four commands above from the same feature worktree with the preserved environment/checkouts. No later phase was started.
