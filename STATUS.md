# Project status

Baseline date: 2026-10-02. Target: arXiv:2506.03094v1 PDF.

## Completed in this delivery

The theory/design report, module architecture, reproduction contract, validation plan and staged Codex prompts have been written. Gross and two-gross polynomials, logical bases, selected cycles, shared vertices and bridge paths have been transcribed into reference JSON. The independent algebra audit checks code ranks, canonical logical pairing, selected-cycle validity, omitted-cycle membership in the combined binary stabilizer span, commutation and one-logical-loss ranks for X, XX, Y and an inter-XX graph reconstruction. It also derives x/y shift logical actions from the physical support permutation. Nine utility tests pass; see `evidence/pytest_reference.txt` and `evidence/algebra_audit.json`.

`evidence/reference_fits.csv` contains evaluations of rounded Table-6 fit parameters only. These are not sampled data or a reproduction of the published confidence bands.

## Not implemented / not run

Phase 04 now supplies physical noiseless gross X1 circuits, single/Bell primitives and independently validated schedules. No production noisy surgery benchmark, detector/observable compiler, distance proof, reproduction Relay adapter or Monte Carlo reproduction has been completed. The original delivery did not install or execute Stim, qLDPC or Relay; phase 00 subsequently pinned and tested tiny backend APIs. Phases 01--02 implemented signed algebra and deformations; phase 03 now validates an ideal measurement instrument through gross X1, with explicit limits recorded below. The delivered algebra audit is not a circuit-distance certification and its rank calculations are phase-blind.

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

Phase 04 is complete for physical primitives, staggered BB memory, legal
staged-coloring schedules and the gross X1 noiseless physical instrument.
Next prompt: `prompts/05_flows_and_harness.md`, only in a new controller-authorized
session after phase-04 acceptance and publication. This session stops at 04;
strict paper-equivalent sampling remains blocked by O1--O5.

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

## Phase 01 algebra and codes completed (2026-10-02)

Branch: `feature/01_algebra_and_codes`. Worktree:
`/home/quantum_teresheys/workspace/tour_de_gross_design_bundle/.codex-pipeline/tour-de-gross/worktrees/01_algebra_and_codes`.
Main checkout: `/home/quantum_teresheys/workspace/tour_de_gross_design_bundle`.
Publication outcome: **not attempted; controller owns acceptance rerun, commit,
merge and atomic push**. The feature worktree was initially clean. No reference,
AGENTS, pipeline-control or independent-audit edits, external patches, network
writes, solvers, physical scheduling, sampling or cluster jobs occurred.

Implemented strict GF(2) rank/RREF/kernel/solve/inverse/span and centralizer
quotient primitives; signed Pauli multiplication/dagger/commutation and Clifford
conjugation; immutable `BBCodeSpec`/`CodeData`, block-qualified qubit/check IDs,
canonical JSON identities and validated serialization; frozen gross/two-gross
loading and reconstruction of the four base logicals and all twelve pairs;
explicit independently verified qubit/X-check/Z-check convention maps; and full
24x24 physical-support shift actions with exact signed stabilizer witnesses.
The independent delivered audit remains unchanged. The 18-qubit debugging
fixture is a local 3x3 BB construction with ranks 7/7 and four derived pairs,
labels 1--4; it explicitly rejects X7 and claims no distance or LPU geometry.

Provenance and semantics are in `docs/ALGEBRA_CONVENTIONS.md` and
`locks/algebra-sources.json`. New implementation code is independently written;
no donor implementation was copied. Actual pinned qLDPC BBCode matrices were
constructed and checked in both x/y and y/x dictionary orders, including the
nonidentity column/check permutations. The inspected source is
`src/qldpc/codes/quantum.py` at commit
`60fc2cf465e880d6e64afacc933d33455d787bf4`, Git blob
`00f28e469a9efb0d4253f083100695bc72b4cdbb`; SHA-256 and inspected Apache-2.0
license/COPYRIGHT hashes are recorded. The source checkout remains in the
canonical shared external directory. No SlidingWindowDecoder code was reused.
The paper was read from the already downloaded pinned v1 PDF, specifically
Eqs. (27)--(38); no source-backed fixture correction was identified.

Commands actually run from this feature worktree in `tour_de_gross`:

```bash
conda run --no-capture-output -n tour_de_gross python -m pip install --no-build-isolation -e .
conda run --no-capture-output -n tour_de_gross python -m pytest -q tests/test_algebra.py tests/test_codes.py tests/test_shifts.py
conda run --no-capture-output -n tour_de_gross python tools/audit_algebra.py --output evidence/phase01/code-algebra.json
conda run --no-capture-output -n tour_de_gross python tools/audit_reference.py --output evidence/phase01/independent-audit.json
conda run --no-capture-output -n tour_de_gross python -m pytest -q tests/test_algebra.py tests/test_codes.py tests/test_shifts.py tests/test_reference.py tests/test_pipeline.py tests/test_backends.py tests/test_source_audit.py tests/test_manifest.py
conda run --no-capture-output -n tour_de_gross python -m pytest --collect-only -q tests/test_algebra.py tests/test_codes.py tests/test_shifts.py
conda run --no-capture-output -n tour_de_gross python -m pip check
conda run --no-capture-output -n tour_de_gross python /tmp/phase01_handoff.py
git diff --check
```

Also ran two bounded `conda run --no-capture-output -n tour_de_gross python -`
heredocs: an initial rank/shift/qLDPC matrix/debug-fixture probe (all successful),
and the read-only source-hash/provenance lock writer. Read-only shell inspection
used `cat`, `rg`, `sed`, `git status/branch/rev-parse/ls-tree` for the contracts,
local paper text, delivered oracle and pinned donor. The handoff helper verifies
protected bytes against clean main, external tree cleanliness, import paths,
source/PDF hashes, exact collected node coverage, evidence and the unchanged
controller's result schema/gate validation; it does not run or publish a phase.

Actual validation: initial **24 passed in 49.67s**; after adding provenance and
shift-certificate serialization/negative cases, final **111 passed in 83.53s**,
with no skips/xfails. This is 26 new phase tests plus all 85 phase-00/reference/
pipeline regressions. A01 independently checks all signed one-/two-qubit products
and supported Clifford conjugations against dense matrices, Hermitian squares,
and all 2x3 GF(2) maps/RHS vectors. A02 checks 66/66 and 138/138 ranks, all twelve
canonical pairs, serialized identities, block separation, both actual donor
orders and independent check-row maps. A06 checks full X/Z actions, signed
quotient witnesses, inverses, commuting x/y shifts, sixth powers and row/column
conventions. Physical x^6 remains a nonidentity permutation on ell=12 while
its logical quotient is identity. Negative cases reject imaginary checks,
nonbinary inputs, malformed code/register/schema/convention data, corrupted
frozen fixtures, incorrect data/check permutations and invalid shift inputs.
No implementation/validation test failed. Pip reports no broken requirements;
whitespace checking passes. Existing backend regressions retain their tiny
phase-00 scope; they do not establish production Stim/Relay integration here.

Nonempty local evidence: `evidence/phase01/{pytest-phase01.txt,pytest-final.txt,
collected-nodeids.txt,code-algebra.json,independent-audit.json,audit-algebra.txt,
audit-reference.txt,pip-check.txt,guards.json,acceptance-gates.json,result.json,
handoff-validation.json}`. Algebra evidence includes complete serialized code
data and signed shift span witnesses. The independent audit matches the delivered
JSON exactly. All four gates A01/A02/A06/negative_tests map to existing exact
pytest node IDs in `acceptance-gates.json` and the completion JSON. Generated
evidence remains local/ignored under the existing policy.

O1--O5 remain unresolved: O1 inter-module published K23 observable generators;
O2 historical Relay semantics/priors/columns; O3 physical scheduling, shift
representative, lowering and boundaries; O4 primitive multiplicities/admission;
O5 original data/counts/grids/bootstrap. None is assumed resolved or required
for this independent algebra phase. Strict paper manifests remain blocked by
all five. Donor memory-builder reuse licensing also remains open. The new
18-qubit fixture has no claimed code-distance lower bound. No physical circuit,
ideal surgery instrument or Figure-15 sampling is implemented or claimed here.

Short rerun: execute the two audit commands, the full eight-file pytest command
and pip check above from this worktree in `tour_de_gross`. Stop after phase 01.
Next prompt: `prompts/02_graphs_and_deformation.md` only in a subsequent
controller-authorized session after phase-01 validation/publication. No later
phase was started by this session.

## Phase 02 graphs and deformation completed (2026-10-02)

Branch: `feature/02_graphs_and_deformation`. Worktree:
`/home/quantum_teresheys/workspace/tour_de_gross_design_bundle/.codex-pipeline/tour-de-gross/worktrees/02_graphs_and_deformation`.
Main checkout: `/home/quantum_teresheys/workspace/tour_de_gross_design_bundle`.
Publication outcome: **not attempted; controller owns acceptance rerun, commit,
merge and atomic push**. The supplied feature worktree was initially clean and
existing tracked files were preserved. No reference, AGENTS, pipeline-control or
independent-audit changes, external patches, source downloads/network writes,
solvers, sampling, physical circuits or cluster jobs occurred.

Implemented immutable edge-ID auxiliary graphs, selected edge-ID cycles,
incidence matrices, signed block-qualified ports, exact reference half/full LPUs
with the identified shared vertex, and the two-block inter-XX algebraic adapter.
A.1's four requirements and the shifted ZX-dual adjacent-check isomorphism are
checked on actual supports. A reference-only guard also rejects otherwise valid
canonical bases whose labels/signs differ from the literal published shifts.
The full-LPU graph counts are 23/47/19 for gross and 39/81/37 for two-gross;
installed census is 90/158 when the shared Bell check counts as two measurement
qubits. The half counts remain 12/18 and 20/32. The inter-XX active algebraic
counts are 35/58/20 and 57/98/38, with degree-two identity-port subdivision
vertices and six-edge joint bridge cycles, and no triangular bridge cycles.
They are distinct from the installed full-LPU census.

The default paper dressing admits only one direct adjacent edge per nonzero
old-check boundary; there is no spanning-tree/path fallback. The generic GF(2)
dressing and full-cycle-basis oracle have separate explicit profiles. Original
selected cycles and ladders are retained. Signed generators validate Hermiticity,
commutation, the vertex product, and every binary identity relation, rejecting
-I. Y uses the shared Hermitian port +Y = i X Z. Certificates include old-check
Paulis, edge dressing masks and phases, incidence/boundary equations, ordered
signed generators, identity relations, and omitted-cycle complement witnesses in
the combined signed group. Missing complements have dimensions 2 (X control),
6 (full XX/Y), and 4 (inter XX) in both sizes. Together with the measured cycles,
these span the full graph cycle space.

The fixed input logical subspace is explicitly computed from the edge-free
intersection of the deformed group with data Paulis, then mapped to the input
logical quotient. It is exactly the one-dimensional span of X1, X1 X7, Y1 or
block_a:X1 times block_b:X1 as requested. Remaining dimensions are 11 in-module
and 23 inter-module. Separate X1/X7 measurements have rank-two fixed input
constraints and are rejected for the XX-only specification. Tests also reject
unjustified cycle deletion, imaginary/wrong signed Y, -I, phase-blind span
witnesses, invalid/disconnected graphs, ambiguous parallel path edges, odd
boundaries, missing local dressing edges and duplicate inter block IDs.

Provenance: `docs/DEFORMATION_CERTIFICATES.md` and
`locks/deformation-sources.json`. Implementations are independently written;
no donor source was copied or modified. Read the preserved pinned PDF at
`/tmp/phase00-resume-tdg.pdf` (SHA256 matches the phase-00 lock), especially A.1's
four numbered conditions, A.3 Eqs. (39)--(64) and A.4/Fig. 13(b). Immutable
fixture hashes match delivery; no fixture correction is needed. The unchanged
delivered binary audit remains a separate oracle. Signed tests independently
multiply witnesses through `Pauli.__mul__` rather than the new group's product
implementation. Certificate signs describe a consistent +1 generator sector;
actual outcomes and instrument coherence remain phase-03 work.

Commands actually run in the supplied worktree:

```bash
conda run --no-capture-output -n tour_de_gross python -m pip install --no-build-isolation -e .
conda run --no-capture-output -n tour_de_gross python -m pytest -q tests/test_deformation.py
conda run --no-capture-output -n tour_de_gross python -m pytest -q tests/test_deformation.py::test_nonreference_logical_basis_is_rejected
conda run --no-capture-output -n tour_de_gross python tools/audit_deformation.py --output-dir evidence/phase02/certificates
conda run --no-capture-output -n tour_de_gross python tools/audit_reference.py --output evidence/phase02/independent-audit.json
conda run --no-capture-output -n tour_de_gross python -m pytest -q
conda run --no-capture-output -n tour_de_gross python -m pytest --collect-only -q tests/test_deformation.py
conda run --no-capture-output -n tour_de_gross python -m pip check
conda run --no-capture-output -n tour_de_gross python /tmp/phase02_handoff.py
git diff --check
```

Also ran two bounded `conda run --no-capture-output -n tour_de_gross python -`
smoke heredocs: all eight graph/census builds, then all eight signed deformation
constructions with merged/subspace ranks (both successful). Collection ran
before and after the final basis guard. Full regressions ran first before that
guard (**140 passed in 138.94s**) and again after it (**141 passed in 131.44s**).
The initial phase-only run was **29 passed in 50.27s**; the additional guard was
**1 passed in 8.98s**. There were no failed implementation checks, skips or
xfails. Final coverage is 30 new phase nodes plus 111 prior regressions. Existing
tiny Stim/qLDPC/Relay backend regressions retain their phase-00 scope; no surgery
circuit or reproduction decoder backend is claimed tested. Pip has no broken
requirements. Read-only inspection used `cat`, `rg`, `sed`, `ls`, `sha256sum`
and Git status/branch/source reads; no Git publication commands were run.

Nonempty actual evidence: `evidence/phase02/{pytest-phase02.txt,
pytest-reference-basis-guard.txt,pytest-regression-before-guard.txt,
pytest-final.txt,collected-nodeids.txt,independent-audit.json,pip-check.txt,
certificate-verification.json,guards.json,acceptance-gates.json,
handoff-validation.json,result.json}`. Eight complete certificates and their
SHA256 index are under `evidence/phase02/certificates/`:
`{gross,two_gross}-{X,XX,Y,inter_XX}.json` and `index.json`. Saved witnesses
were independently reloaded and multiplied; old boundary equations, omitted
cycle signs, identity signs and target products were checked against the saved
bytes. The independent audit exactly matches delivered `evidence/algebra_audit.json`.
The handoff helper verifies the feature branch/worktree, clean main, feature
import path, unchanged protected fixtures/contracts/controller/source locks,
clean canonical external checkouts, source PDF hash and all collected node IDs;
it validates the completion result using the unchanged controller's schema and
gate/evidence checks. A03/A04/A05/negative_tests each occurs exactly once, with
exact existing pytest node IDs covering all 30 phase tests. Evidence is retained
locally under the existing ignored-output policy.

O1--O5 remain unresolved: O1 published inter K23 action generators (merged code
k23 is not that observable definition); O2 historical Relay semantics and
priors/columns; O3 schedule, shift representative, lowering and boundaries; O4
primitive multiplicities/admission; O5 original counts/grids/bootstrap. None is
assumed resolved or required for independent phase-02 algebra. Strict paper
manifests remain fail-closed. Donor memory-builder reuse licensing remains open;
no donor implementation is used by this phase. No distance lower bound,
physical Bell partition/schedule, measurement-instrument coherence or Figure-15
sampling is claimed.

Short rerun: execute the two audit commands, `python -m pytest -q`, the
collection command and pip check above in `tour_de_gross`. Publication remains
with the controller. Stop after phase 02. Next prompt:
`prompts/03_ideal_protocol.md`, only in a new controller-authorized session after
phase-02 validation/publication. No later phase was started.

## Phase 03 ideal protocol completed (2026-10-02)

Branch: `feature/03_ideal_protocol`. Worktree:
`/home/quantum_teresheys/workspace/tour_de_gross_design_bundle/.codex-pipeline/tour-de-gross/worktrees/03_ideal_protocol`.
Main checkout: `/home/quantum_teresheys/workspace/tour_de_gross_design_bundle`,
verified clean. Publication outcome: **not attempted; the outer controller owns
acceptance rerun, feature commit, validated merge and atomic push**. The supplied
feature worktree was initially clean; existing code and scientific fixtures
were preserved. No AGENTS/pipeline changes, external source patches, downloads,
network writes, noisy sampling, solver searches or cluster work occurred. The
editable package was pointed to this feature worktree in `tour_de_gross`.

Implemented an ideal-only prepare/merge/repeat/split/complete state machine,
absolute symbolic IDs for every measurement, logical-outcome XOR, rooted
spanning-tree edge parities and signed data frame Q. Frame evaluation checks
B^T t=z on all edges and rejects noncuts or missing/invalid outcomes. Invalid
state transitions and root/path validation fail without accepting an incomplete
protocol. Stim lowering uses explicitly ideal MPPs, including signed Y and
negative checks; there is no noisy logical MPP substitute or physical schedule.
Original checks are read after edge Z, before correction; the tests verify their
frame-dependent outcomes and restoration of the original +1 sector. Reference
selected cycles and signed omitted-cycle certificates are preserved.

The tiny oracle directly contracts vertex/cycle projectors against |0> edges
and all final Z branches. The independent expected instrument is projection by
the requested signed data Pauli. Two vertices exhaust eight branches (XX, YZ
and negative XX); triangle tests exhaust 64 candidate branches, including 32
zero noncuts, for every root and all three spanning trees; a dummy identity
port exhausts 32 branches for every root. All include arbitrary complex and
maximally reference-entangled inputs, normalization and repeated measurements.
An ideal Bell-check wavefunction oracle controls disjoint signed data halves
and contracts both X readouts, with separate outcome IDs and explicit XOR.
Every Bell branch preserves the expected reference coherence. Negative tests
detect a missing split frame, XZ substituted for Y=iXZ, a self-consistent wrong
-Y target, invalid cut/path/outcome data, invalid state transitions and
unsupported Bell support overlap. Literal independent Stim Pauli words/signs
check all signed one/two-register Pauli words, including identity readouts.

The 18-qubit BB debugging fixture uses its verified nontrivial derived X1,
six single-qubit ports, generic dressing and a ring with its full one-cycle
basis. It is not a scaled TdG LPU, has no X7 label and has no distance claim.
Exact stabilizer postselection tests every one of 2,048 allowed vertex/cut
branches with two rounds and four logical reference qubits; corrected full
states and branch probabilities agree with direct logical projection, and each
outcome's probabilities sum to 1/2. Gross X1 uses the actual half-LPU and
prescribed cycles with three ideal rounds. Twelve deterministic seeds for each
of + eigenstate, - eigenstate and twelve-logical-qubit encoded Choi input yield
36 bounded ideal stabilizer trajectories. Full data/reference/edge states agree
with direct X1 projection; all eleven preserved logical X/Z reference pairs and
all original checks are verified. Every root is compared on every resulting
branch. Gross branch enumeration is exponential and was not performed; the
general signed branch identity, documented in `docs/IDEAL_PROTOCOL.md`, proves
the corrected projector semantics on arbitrary reference-entangled states.
Gross XX/Y and inter XX instrument checks are not claimed by B04_X1.

Provenance: `locks/ideal-protocol-sources.json` and
`docs/IDEAL_PROTOCOL.md`. All implementation is independently written; no donor
source was copied or modified. Read the existing pinned PDF
`/tmp/phase00-resume-tdg.pdf`, especially A.4 steps 1--4 (printed p. 51), and
verified its SHA256 against phase 00. Stim 1.16.0 is used only through the
previously pinned public APIs. The unchanged delivered reference audit remains
an independent oracle and its output matches the delivery exactly.

Commands actually run (redirected logs are under `evidence/phase03/`):

```bash
conda run --no-capture-output -n tour_de_gross python -m pip install --no-build-isolation -e .
conda run --no-capture-output -n tour_de_gross python -c 'from gross_design_bandle.codes import small_debug_code; import gross_design_bandle; c=small_debug_code(); print(gross_design_bandle.__file__); print(c.k, c.logical("X","1").x)'
conda run --no-capture-output -n tour_de_gross python -m pytest -q tests/test_ideal_protocol.py
conda run --no-capture-output -n tour_de_gross python -m pytest -q tests/test_ideal_protocol.py::test_signed_mpp_lowering_matches_pauli_oracle
conda run --no-capture-output -n tour_de_gross python -m pytest -q --junitxml=evidence/phase03/pytest-final.xml
conda run --no-capture-output -n tour_de_gross python tools/audit_ideal_protocol.py --output-dir evidence/phase03/oracles
conda run --no-capture-output -n tour_de_gross python tools/audit_reference.py --output evidence/phase03/independent-audit.json
conda run --no-capture-output -n tour_de_gross python -m pytest --collect-only -q tests/test_ideal_protocol.py
conda run --no-capture-output -n tour_de_gross python -m pip check
conda run --no-capture-output -n tour_de_gross python /tmp/phase03_handoff.py
git diff --check
```

The phase-only command ran three times: initially **10 failed, 4 passed,
1 error** (empty root parity rejected by strict binary conversion, and a wrong
local test spelling of the existing generic dressing profile), then **2 failed,
13 passed** (the test attempted to compare a nested collection of differently
sized arbitrary/Choi matrices), then **15 passed in 31.21s** after fixes.
Initial failure logs are retained, not relabeled as successes. The final full
regression run passed **156 tests in 165.22s**, with no skips or xfails. An
additional independent literal Pauli-word assertion was added during that run
and its targeted final test passed **1 test in 0.22s**; the controller will
rerun the final mapped tree. All fifteen phase nodes are collected and mapped
exactly to B01, B02, B03, B04_X1 and negative_tests. These successful final runs
supersede the resolved development failures. The audit checked eight tiny
branches with zero maximum amplitude and completeness residual. Pip reports
no broken requirements. Prior tiny backend regressions retain their limited
phase-00 scope; no physical surgery or reproduction Relay backend is claimed.

Actual nonempty evidence: `evidence/phase03/{pytest-initial.txt,
pytest-after-empty-parity-fix.txt,pytest-phase03.txt,pytest-literal-pauli.txt,
pytest-final.txt,pytest-final.xml,collected-nodeids.txt,audit-ideal.txt,
audit-reference.txt,independent-audit.json,pip-check.txt,guards.json,
acceptance-gates.json,handoff-validation.json,result.json}`. Symbolic protocols
and ideal Stim oracle bodies are in `evidence/phase03/oracles/`:
`two_vertex_YZ.{json,stim}`, `gross_X1.{json,stim}` and `index.json`, including
byte hashes and actual branch residuals. Evidence remains local under the
existing ignored-output policy. The handoff helper checks worktree/branch,
feature import path, clean main, protected source/fixture/control bytes,
canonical external checkout cleanliness, pinned PDF hash, collected node IDs,
actual JUnit outcomes and the unchanged controller's result validation.

O1--O5 remain open: O1 published inter K23 action generators; O2 historical
Relay semantics/priors/columns; O3 concrete schedule, shift representative,
lowering and ideal/noisy boundaries; O4 primitive multiplicities and
admission/merging convention; O5 original counts/grids/bootstrap. None is
assumed resolved or required for this independent ideal instrument. Strict
paper manifests remain fail-closed. Donor memory-builder reuse licensing also
remains open and no donor code is used here. Three ideal gross rounds are a
validation fixture, not the published C=10 noisy benchmark. No physical Bell
partition/schedule, detector integrity, circuit distance or Figure-15 sampled
rates are delivered.

Short rerun: from this worktree, run the phase pytest command, ideal export,
independent reference audit, full pytest and pip check above in `tour_de_gross`.
Stop after phase 03. Next prompt: `prompts/04_physical_scheduling.md`, only in a
new controller-authorized session after validation/publication. No later phase
was started; publication remains with the controller.

## Phase 04 physical scheduling completed (2026-10-02)

Branch: `feature/04_physical_scheduling`. Worktree:
`/home/quantum_teresheys/workspace/tour_de_gross_design_bundle/.codex-pipeline/tour-de-gross/worktrees/04_physical_scheduling`.
Main checkout: `/home/quantum_teresheys/workspace/tour_de_gross_design_bundle`,
verified clean. Publication outcome: **not attempted; the outer controller owns
acceptance rerun, feature commit, validated merge and atomic push**. Initial
feature status was clean; existing code/configuration and reference fixtures
were preserved. No AGENTS/controller edits, external source patches, network
writes, long sampling, distance solver, cluster work or later phase was run.
The inherited `tour_de_gross` editable import resolves to this feature worktree;
no install or build was needed in this phase.

Added physical signed single-check and Bell-check identities, integer-tick IR,
physical-to-algebraic readout XORs, native basis policy, exact tableau validation,
staggered memory, bipartite Delta coloring and A.5 staged/ASAP scheduling. The
validator checks physical ownership, complete support/gate identity, all qubit
collisions, reset/readout/sign consistency, Bell preparation order and Eq. (67)
on every anticommuting overlap. It rejects a collision-free reversed-overlap
schedule; exact inverse tableau propagation independently reveals its unwanted
ancilla input factor. No ideal MPP occurs in the physical body. The earlier
ideal MPP protocol remains an explicitly separate oracle.

The read-only SlidingWindowDecoder adapter extracts twelve gate-layer facts
from the pinned builder AST without importing/executing or copying that builder.
The source builder has no license notice or repository-level license; its reuse
license remains open. Local implementations are independently written. The
donor's arbitrary A_list/B_list input is populated with literal permutation
matrices in the paper xy/LR convention, with monomial order (2,0,1); a concrete
identity ConventionAdapter verifies Hx/Hz before translating gates. Figures 3/4
supply an independent geometric/coordinate oracle. This does not assert a map
from the donor's separate default factory/logical basis. The canonical external
checkouts remain unchanged and pinned. Provenance and inspected license/hash
facts: `locks/physical-scheduling-sources.json`, plus unchanged phase-00 locks.
The pinned PDF hash was rechecked and Figures 3--5/A.5 Eqs. (65)--(68) read.

The physical policy uses native one-tick RX/R/MX/M and CX/CY/CZ. Pure BB Z checks
use data-to-ancilla CNOTs with Z-basis preparation/readout; mixed checks use an
X-basis ancilla. Y is directly controlled with its signed phase. Bell halves
have disjoint support and one algebraic identity/two physical identities. A
negative check inverts one physical outcome. Unsupported policy changes fail
closed at lowering; policies, operations, time and live-idle accounting affect
the schedule hash. Candidate location counts retain idles on all live data and
prepared ancillas, including boundaries; split edges cease to be live. They are
not an O4 primitive fault catalogue or Table-6 N. No stochastic noise or decoder
is emitted/invoked by the new APIs.

Gross X1 has 161 algebraic/physical single checks, 323 active fragment qubits,
707 anticommuting overlap pairs, Delta_BB=1 and a 12-tick deformed cycle. Its
per-cycle candidate census is CX=930, CZ=23, RX=89, R=72, MX=89, M=72 and
IDLE=1004. The C=10 physical export contains 1 edge-init + 120 deformed + 1
split + 9 original-check verification ticks = 131; the external ideal logical
input/terminal harness is separately accounted as absent (zero). Gross memory
C=10 is 81 ticks; tests verify 8C+1, Z reset/read offsets 0/7 and X offsets 1/8
for both code sizes and repeated cycles. Complete operation/outcome/location
ledgers, data/ancilla live intervals, policy and circuit/schedule hashes are
saved. Physical original-check readouts predict the split-frame syndrome;
applying the recorded frame restores every original stabilizer.

The independent installed full-LPU connectivity union includes both X and
ZX-dual Z port/dressing couplers and inactive installed links. It reproduces
Figure-5 LPU counts 90/158 and degree histograms for gross/two-gross, maximum
physical degree seven, degree five per shared Bell half. Algebraic graph degree,
physical ancilla count, active fragment count and installed layout count remain
separate. The selected reference cycles are unchanged and no ILP was used.
Gross XX/Y schedules also pass all constraints and per-check tableau checks;
this coloring choice has 13-tick cycles. Two-gross construction probes yield
X/XX/Y depths 14/15/15. These choices do not establish the reported 12C timing
or complete instrument semantics for those targets; the complete physical
instrument delivered in this phase is scoped to gross X1.

Exact signed Stim Clifford tableaus check every gross X1 primitive alone and
its readout in the simultaneous scheduled round. Tiny primitives exhaust all
16 two-qubit Pauli words, both signs and single/Bell implementations. Dense
Bell Choi tests exhaust every physical branch for negative YZ, XX and ZY,
checking the projector and coherence of both reference qubits. Gross X1 uses
12 bounded noiseless stabilizer trajectories: four seeds each for + eigenstate,
- eigenstate and full encoded Choi input, two physical rounds, split and frame.
A complete data/reference stabilizer basis verifies target outcome and all
preserved logical coherence. This is an instrument test, not a noisy pilot or
sampled logical-error rate. Installed connectivity checks include two-gross;
no complete two-gross instrument, inter-module schedule or shift is claimed.

Commands actually run (all Python commands in `tour_de_gross`):

```bash
conda run --no-capture-output -n tour_de_gross python -c 'import gross_design_bandle,stim; print(gross_design_bandle.__file__); print(stim.__version__)'
conda run --no-capture-output -n tour_de_gross python -m pytest -q tests/test_physical_scheduling.py
conda run --no-capture-output -n tour_de_gross python -m pytest -q tests/test_physical_scheduling.py --junitxml=evidence/phase04/pytest-phase04.xml
conda run --no-capture-output -n tour_de_gross python -m pytest -q tests/test_physical_scheduling.py --junitxml=evidence/phase04/pytest-phase04-final.xml
conda run --no-capture-output -n tour_de_gross python -m pytest -q --junitxml=evidence/phase04/pytest-final.xml
conda run --no-capture-output -n tour_de_gross python tools/audit_physical_scheduling.py --output-dir evidence/phase04/artifacts
conda run --no-capture-output -n tour_de_gross python tools/audit_reference.py --output evidence/phase04/independent-audit.json
conda run --no-capture-output -n tour_de_gross python -m pytest --collect-only -q tests/test_physical_scheduling.py
conda run --no-capture-output -n tour_de_gross python -m pip check
conda run --no-capture-output -n tour_de_gross python /tmp/phase04_handoff.py
git diff --check
```

Read-only Python heredoc probes also inspected Stim flow API semantics,
constructed gross memory/X1, and checked installed counts/valid schedule depths
for both sizes. File-edit helper scripts ran with the same environment. The
final oracle deliberately uses exact Tableau arithmetic, avoiding signed
Circuit.has_flow's documented randomized implementation. No external builder
or production Relay backend was invoked by this phase.

Validation history: initial phase run **1 failed, 13 passed in 38.05s**, because
the tick-count test inspected an unflattened Stim REPEAT block. After correcting
that assertion and adding the exact composite tableau oracle, **14 passed in
52.80s**. The ledger/policy verification run passed **14 in 53.25s**. A final
physical-ownership guard and negative tests were added while the full suite
was running; the final phase command passed **14 in 53.09s** on the final source.
The broad regression command passed **170 in 169.27s**, no skips/xfails. Its
phase tests were loaded before the last ownership guard, so the final phase
JUnit run is the evidence for that change. Both results are retained accurately;
the controller will rerun the final mapped tree. No failure remains unresolved.
The physical export checks 161 exact signed tableaus and all 707 overlap pairs.
The independent reference audit matches the delivered audit exactly. Pip check
reports no broken requirements.

Gate mappings are saved in `evidence/phase04/acceptance-gates.json`: C01 physical
primitive/Bell/projector/gross checks, C02 overlap/coloring constraints and the
reversed-overlap negative, C03 donor/paper/convention and staggered timing,
C04 complete location/live-interval/policy/Bell ledgers and gross instrument,
C05 installed physical connectivity, and negative_tests for sign/gate/Bell
ordering/collision/missing interaction/ownership/invalid-round failures. Every
gate occurs exactly once with exact existing pytest nodes; all 14 phase nodes
are covered. See `tests/test_physical_scheduling.py` for independent oracles.

Nonempty local evidence: `evidence/phase04/{pytest-initial.txt,
pytest-after-fix.txt,pytest-phase04.txt,pytest-phase04.xml,
pytest-phase04-final.txt,pytest-phase04-final.xml,pytest-final.txt,
pytest-final.xml,collected-nodeids.txt,audit-physical.txt,audit-reference.txt,
independent-audit.json,pip-check.txt,acceptance-gates.json,
handoff-validation.json,result.json}`. Exported artifacts under
`evidence/phase04/artifacts/`: `gross_X1_C10.{stim,json}`,
`gross_memory_C10.{stim,json}`, `bell_negative_YZ.{stim,json}`,
`exact_tableau_checks.json`, `{gross,two_gross}_installed_connectivity.json`
and `index.json` with byte hashes. The handoff helper checks branch/worktree,
main cleanliness, protected tracked fixtures/contracts/source locks, canonical
external source commits/cleanliness, feature imports, pinned PDF, independent
reference audit, artifact hashes, exact JUnit node outcomes and the unchanged
controller schema/gate/evidence validation. Generated evidence follows the
existing ignored-output policy; the controller saves its tracked validation.

O1--O5 remain open: O1 published inter K23 action generators; O2 historical Relay
semantics/prior/column policy; O3 paper-exact schedule/coloring, shift, gate/noise
lowering and boundaries; O4 primitive multiplicities and admission/merging;
O5 original grids/counts/bootstrap. The named independent native policy fixes
what this phase needs without assuming paper equivalence. Donor builder reuse
licensing remains open; only source facts were read. Strict paper manifests
remain fail-closed. Detector/observable integrity, actual stochastic fault
catalogues, shifts, inter scheduling, distances and sampled rates are later work.

Short rerun: from this worktree use the final phase pytest command, physical
export, independent reference audit, full pytest and pip check above in
`tour_de_gross`. Publication remains with the controller. Stop after phase 04.
Next prompt: `prompts/05_flows_and_harness.md`, only in a new controller-authorized
session after validation/publication. No later phase was started.
