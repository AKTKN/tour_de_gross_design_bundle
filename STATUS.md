# Project status

Baseline date: 2026-10-02. Target: arXiv:2506.03094v1 PDF.

## Completed in this delivery

The theory/design report, module architecture, reproduction contract, validation plan and staged Codex prompts have been written. Gross and two-gross polynomials, logical bases, selected cycles, shared vertices and bridge paths have been transcribed into reference JSON. The independent algebra audit checks code ranks, canonical logical pairing, selected-cycle validity, omitted-cycle membership in the combined binary stabilizer span, commutation and one-logical-loss ranks for X, XX, Y and an inter-XX graph reconstruction. It also derives x/y shift logical actions from the physical support permutation. Nine utility tests pass; see `evidence/pytest_reference.txt` and `evidence/algebra_audit.json`.

`evidence/reference_fits.csv` contains evaluations of rounded Table-6 fit parameters only. These are not sampled data or a reproduction of the published confidence bands.

## Not implemented / not run

Phase 04 supplies physical noiseless gross X1 circuits, single/Bell primitives and independently validated schedules. Phase 05 supplies an exact signed detector/observable compiler and ideal gross memory/X1 benchmark harness. Phase 06 supplies three distinct noise channels, primitive catalogues, joint H/Lambda matrices and gross memory/X1 audit exports. Phases 07--08 now supply direct gross XX/Y and Fig. 13(b) two-block C10 instruments, independent noisy harnesses and compact joint fault exports; phase 08 uses the full named K47 profile and leaves published inter K23 unavailable on O1. Phase 09 supplies physical gross shifts; phase 10 exercises the shared implementation on two-gross C18 idle/shift/in-module surgery and explicit inter C17/C18 extensions, with bounded A.8 inputs prepared but no solver launched. Phase 11 supplies a source-pinned current-Relay joint adapter with float32/float64 fixed-vector validation, auditable priors/parameters, explicit graph profiles and counted failures. Historical Table-7 compatibility remains unresolved on O2. No distance proof or Monte Carlo reproduction has been completed. The original delivery did not install or execute Stim, qLDPC or Relay; phase 00 subsequently pinned and tested tiny backend APIs. Phases 01--02 implemented signed algebra and deformations; phase 03 validates an ideal measurement instrument through gross X1, with explicit limits recorded below. The delivered algebra audit is not a circuit-distance certification and its rank calculations are phase-blind.

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

Phase 11 supplies a validated current-Relay joint adapter; historical Table-7
compatibility remains open. Next prompt: `prompts/12_sampling_and_analysis.md`,
only after phase-11 controller validation/publication and a new explicit
authorization beyond the current through-11 interval, with its pilot budget.
This session stops at 11. Strict paper-equivalent sampling remains blocked
by O1--O5; no later phase, pilot or Git publication was run.

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


## Phase 05 flows and ideal harness completed (2026-10-02)

Branch: `feature/05_flows_and_harness`. Worktree:
`/home/quantum_teresheys/workspace/tour_de_gross_design_bundle/.codex-pipeline/tour-de-gross/worktrees/05_flows_and_harness`.
Main checkout: `/home/quantum_teresheys/workspace/tour_de_gross_design_bundle`,
verified clean. Publication outcome: **not attempted; the outer controller owns
acceptance rerun, feature commit, validated merge and atomic push**. The supplied
feature was initially clean and all existing source/configuration/reference
fixtures were preserved. No AGENTS/controller changes, external-source edits,
network writes, sampling pilot/campaign, distance solver, cluster work or later
phase was run. The existing `tour_de_gross` import resolves to this worktree.

Added `src/gross_design_bandle/flows/`: absolute outcome records, scoped nested
repeats with explicit cross-iteration carry aliases, signed affine constants,
final rec-offset lowering, an exact signed mixed-state stabilizer flow oracle,
named logical Clifford bases, explicit ideal boundaries, the gross memory/X1
harness and an independent joint X/Z fixed-fault signature oracle. Source and
API documentation: `docs/FLOWS_AND_HARNESS.md`; provenance and scoped assumptions:
`locks/flows-and-harness-sources.json`. Export tool:
`tools/audit_flows_and_harness.py`; meaningful positive/negative tests:
`tests/test_flows_and_harness.py`. No donor implementation was copied. Canonical
external checkouts remain pinned and unchanged; their inherited inspected
licenses/hashes are retained. The immutable paper PDF was downloaded read-only,
its locked SHA256 rechecked and canonical A.7 pp. 58--59 inspected.

Every measurement, including deterministic affine MPAD bits, has an absolute
ID. Bell checks use both physical outcomes. Nested carry tests begin with a
random sign and transport it across both repeat levels; compressed and unrolled
circuits preserve identical parities and records. Missing/future/duplicate IDs,
out-of-history offsets, unsupported instructions and coverage gaps fail closed.
The exact oracle tracks i^p X^x Z^z and affine eigenvalues; resets partially trace
an entangled qubit before preparing it. Exhaustive signed Clifford tests compare
it to an independent exact Stim tableau. It never uses the randomized signed
`has_flow` method and never silently ignores stochastic noise.

The harness prepares twelve encoded Bell pairs for memory (K24), or the + X1
slot and eleven encoded Bell pairs for X1 (K23). The rows have semantic names,
physical Pauli representatives, logical-coordinate ranks, exact physical scoring
parities and terminal joint readout Paulis. All 24 input logical Pauli generators
were injected independently before each physical body: the observed signatures
match their symplectic pairing with every named row, have zero syndrome and
rank 24/23. Logical CX(1,7) and S(1) adapters support future X1*X7 and signed
Y1=i X1 Z1 targets algebraically; their physical benchmarks are still later work.
Published inter K23 is explicitly rejected under O1, with no unnamed subset or
claim of a two-block K47 physical harness.

Initial dressed/cycle parities follow encoded stabilizers and reset edge Z.
Random individual first-round vertex outcomes are not detectors. Repeated
readouts, selected split cycle parity, retained old/dressed/Z-dressing relations
and final original-check closure each have saved signed justifications. The X1
score is the last-round vertex XOR; final X1 has a consistency detector. Other
scores are final logical/reference Bell correlations with all software-frame
terms recorded. Both correction modes keep the same detectors and semantic rows.
The frame is a linear tree rule on raw bits, while cycle detectors expose non-cut
faults; the ideal-only `SplitFrame.evaluate` cut check is not misused on noisy
records. The separate raw `TruthTableInstrument` has no decoding annotations;
its full encoded Choi input yields an exactly nonconstant target outcome.

This named independent boundary policy uses ideal input encoding, a noise-free
physical original-check verification round after split and ideal terminal MPP
closure. These boundaries are separately labelled and their input/output
constraints saved. No MPP occurs in the physical operation body. Active split
corrections use real record-controlled Pauli instructions in that body; software
corrections modify the terminal/syndrome parities. Three-round gross stratified
joint-fault signatures agree exactly between the two modes. Small Bell negative
YY tests exhaust joint tensor faults on physical operands and verify both XOR
halves and CY/Y signs; a separate signed Y-frame fixture checks active tracking.
These are probability-one oracle injections, not sampled logical-error rates or
an O4 primitive catalogue. No dropped/gauge detectors or altered hidden boundaries
were used. Deliberate offset corruption fails both exact flow and strict DEM;
omitted frame/Bell-half, inverted terminal sign and missing middle observable
also fail their appropriate checks.

C10 exported memory has 300 qubits (12 ideal references), 1608 outcomes,
1584 detectors and K24; each X1 mode has 334 qubits (11 ideal references), 1939
outcomes, 1892 detectors and K23. All declared benchmark detectors/observables
are exactly zero in the noiseless harness. Each export passes exact signed flows,
strict Stim DEM extraction with `allow_gauge_detectors=False`, four bounded
noiseless oracle trajectories and deterministic fixed-fault comparisons.
Generated source/artifact hashes are checked and the exporter fails if source
bytes change during export. These counts are not Table-6 N and do not imply a
circuit-distance result or paper-exact serialization.

Commands actually run (all Python installs/builds/tests use `tour_de_gross`;
no install/build was needed):

```bash
conda run --no-capture-output -n tour_de_gross python -m pytest -q tests/test_flows_and_harness.py --junitxml=evidence/phase05/pytest-initial.xml
conda run --no-capture-output -n tour_de_gross python -m pytest -q tests/test_flows_and_harness.py::test_D04_Y_frame_and_Bell_XOR_signed_flows
conda run --no-capture-output -n tour_de_gross python -m pytest -q tests/test_flows_and_harness.py --junitxml=evidence/phase05/pytest-phase05.xml
conda run --no-capture-output -n tour_de_gross python -m pytest -q tests/test_flows_and_harness.py::test_D01_nested_repeat_carries_random_stabilizer_sign_across_iterations
conda run --no-capture-output -n tour_de_gross python -m pytest -q tests/test_flows_and_harness.py --junitxml=evidence/phase05/pytest-phase05-final.xml
conda run --no-capture-output -n tour_de_gross python -m pytest -q tests/test_flows_and_harness.py::test_D05_physical_parities_realize_complete_named_logical_action
conda run --no-capture-output -n tour_de_gross python -m pytest -q --junitxml=evidence/phase05/pytest-final.xml
conda run --no-capture-output -n tour_de_gross python tools/audit_flows_and_harness.py --output-dir evidence/phase05/artifacts
conda run --no-capture-output -n tour_de_gross python tools/audit_reference.py --output evidence/phase05/independent-audit.json
conda run --no-capture-output -n tour_de_gross python -m pytest --collect-only -q tests/test_flows_and_harness.py
conda run --no-capture-output -n tour_de_gross python -m pip check
curl --fail --location --silent --show-error https://arxiv.org/pdf/2506.03094v1 --output evidence/phase05/paper-v1.pdf
sha256sum evidence/phase05/paper-v1.pdf
pdftotext -f 58 -l 59 -layout evidence/phase05/paper-v1.pdf evidence/phase05/paper-a7.txt
conda run --no-capture-output -n tour_de_gross python /tmp/phase05_handoff.py
git diff --check
```

Read-only Python heredoc probes in the same environment inspected local Stim
flow API documentation/imports and constructed two-round memory/frame/active
X1 harnesses. File-edit helper scripts also used that environment. Initial phase
validation had **1 failed, 10 passed in 62.34s**: a new toy frame fixture attached
an unrelated random bit to data. Adding the actual controlled-Y interaction
corrected the fixture; its focused test passed. Subsequent phase runs passed
**12 in 63.19s**, then **13 in 109.96s**. The nested carry and full physical logical
signature focused tests passed. Final phase rerun, reusing the initial command,
passed **14 in 110.99s** on the final source. The original failing log/XML were
preserved as `pytest-initial-failed.{txt,xml}` before that rerun.

The broad suite passed **183 in 321.17s**, no skips/xfails. Its collection preceded
the final observable coverage guard and final new logical-signature test; the
14-node final phase rerun covers these changes. The inherited regression source
was not modified. The C10 export was rerun after final source guards, retaining
its first successful log/index separately. The independent reference audit
matches the delivered JSON exactly; pip check has no broken requirements.
No failure remains unresolved. Controller acceptance will rerun the final tree.

Gate mappings are in `evidence/phase05/acceptance-gates.json`: exactly D01, D02,
D04, D05 and negative_tests, with existing exact pytest nodes covering all 14
phase tests. D03 small fault/signature oracle coverage is included under D02;
large active/frame comparisons are D04. No optional/backend implementation is
claimed as newly validated beyond the actual bounded oracles described here.

Nonempty evidence: `evidence/phase05/{pytest-initial.txt,pytest-initial.xml,
pytest-initial-failed.txt,pytest-initial-failed.xml,pytest-toy-fix.txt,
pytest-repeat-carry.txt,pytest-phase05.txt,pytest-phase05.xml,
pytest-phase05-final.txt,pytest-phase05-final.xml,pytest-logical-signatures.txt,
pytest-final.txt,pytest-final.xml,collected-nodeids.txt,audit-flows.txt,
audit-flows-first.txt,index-first-export.json,audit-reference.txt,
independent-audit.json,pip-check.txt,paper-sha256.txt,paper-a7.txt,
acceptance-gates.json,handoff-validation.json,result.json}`. Under
`evidence/phase05/artifacts/`, each `gross_memory_C10_frame`,
`gross_X1_C10_frame` and `gross_X1_C10_active` has `.stim`, `.json` and
`_fixed_faults.json`, with byte/source hashes and validations in `index.json`.
Evidence remains local under the established ignored-output policy. The handoff
helper checks branch/worktree, clean main, protected contracts/fixtures/source
locks, external commits/source hashes/cleanliness, feature imports, paper hash,
independent audit equality, artifact/source hashes, all mapped JUnit passes and
the unchanged controller schema/gate/evidence validation.

O1--O5 remain open: O1 inter K23 generators, O2 historical Relay/prior/column
semantics, O3 paper-exact schedule/shift/lowering/boundaries, O4 primitive
multiplicities/admission/merging and O5 original grids/counts/bootstrap. The named
independent boundary policy supplies all assumptions required by this phase;
strict paper manifests remain fail-closed. Inherited donor-builder reuse licensing
also remains open, with no donor code copied. XX/Y physical harnesses, inter K47,
shifts, actual fault catalogues, decoder integration, distances and sampled rates
are later work; none was launched in this session.

Short rerun: use the final phase command, flow export, independent audit, full
pytest and pip check above from this worktree. Stop after phase 05. Next prompt:
`prompts/06_noise_and_fault_model.md`, only in a new controller-authorized session
after acceptance/publication. The controller owns publication; no later phase
was started.

## Phase 06 independent noise and primitive catalogue completed (2026-10-02)

Branch: `feature/06_noise_and_fault_model`. Worktree:
`/home/quantum_teresheys/workspace/tour_de_gross_design_bundle/.codex-pipeline/tour-de-gross/worktrees/06_noise_and_fault_model`.
Main checkout: `/home/quantum_teresheys/workspace/tour_de_gross_design_bundle`,
verified clean. Publication outcome: **not attempted; the outer controller owns
acceptance rerun, feature commit, validated merge and atomic push**. The supplied
feature was initially clean. Existing source, fixtures, controls and source locks
were preserved. No AGENTS/pipeline changes, external-source modifications,
network writes, solver/cluster work, benchmark Monte Carlo or later phase ran.
The `tour_de_gross` package import resolves to this feature worktree.

Added `src/gross_design_bandle/noise/`, `bench/columns.py` and
`validation/faults.py`: explicit physical locations, the three distinct profiles,
primitive lowering, a reverse binary sensitivity sweep, joint sparse H/Lambda,
copy/admission/grouping provenance and independent fault validation. Tests are
in `tests/test_noise_and_fault_model.py`; export tool is
`tools/audit_noise_and_fault_model.py`. API/scientific policy documentation is
`docs/NOISE_AND_FAULT_MODEL.md`; provenance is
`locks/noise-and-fault-sources.json`. No donor code was copied. Inherited source
pins/licenses/hashes remain unchanged in the canonical shared `external_libs`.
The locked v1 PDF hash was verified; Section 2.6 and A.7 were inspected locally.

`a7_uniform_expanded` uses independent q=p/15 copies with multiplicities 15 for
preparation/readout, 5 for each idle Pauli and 1 for each tensor two-qubit Pauli.
`paper_linearized_unequal` keeps independent p, p/3, p/15 primitives.
`standard_categorical_depolarizing` emits ordinary DEPOLARIZE1/2 under its own
comparison ID and is rejected by the independent Bernoulli catalogue API.
Independent emission uses separate CORRELATED_ERROR terms, never ELSE branches.
Reset faults follow reset; readout flips precede measurement. Native CX/CY/CZ
and Bell preparation CNOTs receive joint 15-term faults. The named independent
v1 physical policy includes every unoccupied live data/prepared-ancilla tick,
without active-gate idles or extra free Clifford conversion layers. Ideal input,
reference qubits, X1's final original verification and terminal MPP remain
noise-free. Software split frames are classical; active correction mode is
explicitly rejected until a separately defined correction noise policy exists.

Admission and grouping arguments have no defaults. `include_all` and
`exclude_joint_zero` retain every zero-H/nonzero-Lambda fault; the latter removes
only joint-zero columns. Every raw term has physical location, qubits, boundary,
time, phase, round, role, tensor Pauli, probability and multiplicity. Exported
copy ordinals, copy-to-raw, admission mask, admitted-to-copy and
admitted-to-group maps are reversible. H and Lambda keep the same admitted-copy
ordering. Grouping compares both sectors together; hyperedges are never split.
Explicit XOR grouping uses (1-product(1-2p_i))/2 and preserves the unconditional
joint channel, not the original fixed-weight population. Sampler N remains
admitted copies; decoder group count and compact DEM count are separate fields.

Tiny circuits exhaust every primitive and compare the reverse sweep to the
independent forward Pauli oracle and Stim probability-one injections, including
joint X/Z tensor faults, signed negative YY Bell checks, X/Y preparations and
readouts, classical Y feedforward and nested repeats. E01 enumerates all tiny
subsets, verifies two-copy cancellation analytically, checks O(p²) equalization
error, and compares exact channel probabilities to 32768 bounded Stim and
catalogue Bernoulli draws. These are tiny-channel unit tests, not production
benchmark rates or a pilot. E02 covers duplicate columns, detector-zero logical
faults, joint-zero masks, hyperedges, observable-only terms, repeat identities,
joint grouping and saved physical maps. Negative tests reject unknown profiles,
implicit/incorrect admission, categorical misuse, invalid locations, overlapping
batched gates, nondeterministic detectors and corrupted maps/probabilities/
signatures. A deliberate signature corruption saves its counterexample before
failure. No gauge flags, dropped detectors or graphlike approximation are used.

C10 gross memory and X1 audits export ideal and all three noisy-profile circuits,
four independent full compressed catalogues, sparse H/Lambda matrices, source
and artifact hashes and N discrepancy reports. The strict detector/observable
counts are respectively 1584/K24 and 1892/K23. Memory has 141552 raw primitives
and 218160 expanded copies; X1 has 177190 raw primitives and 346710 copies.
The `include_all` export policy is explicit. Excluding joint-zero copies would
give 215280 and 342599. Published N is 210960 and 324526, so include-all deltas
are +7200 and +22184. Neither policy resolves O4. Reports break down copies by
kind/phase/role and preserve the physical/boundary decisions; no padding or
forced merging was used. Compact expanded DEM sizes are 59472/64801, whereas
joint XOR group counts are 59473/64802, including the joint-zero group.
These counts are audits of this implementation, not sampled Table-6 data.

Every large raw column is generated by the independently validated gate/Pauli
templates. Deterministic large-circuit checks span each phase/gate/role/tensor
Pauli in first/middle/last rounds: 66 memory and 137 X1 raw strata agree exactly
with the forward oracle and Stim. This is stratified coverage, not exhaustive
independent validation of every large-circuit location. X1's half-LPU has no
shared Bell check; Bell coverage comes from the exhaustive primitive fixture.
All six noisy exports pass strict DEM extraction without disjoint approximation.

Commands actually run (every Python install/build/test uses `tour_de_gross`;
no install/build was needed):

```bash
conda run --no-capture-output -n tour_de_gross python -m pytest -q tests/test_noise_and_fault_model.py --junitxml=evidence/phase06/pytest-initial.xml
conda run --no-capture-output -n tour_de_gross python -m pytest -q tests/test_noise_and_fault_model.py --junitxml=evidence/phase06/pytest-phase06.xml
conda run --no-capture-output -n tour_de_gross python -m pytest -q --junitxml=evidence/phase06/pytest-final.xml
conda run --no-capture-output -n tour_de_gross python tools/audit_noise_and_fault_model.py --output-dir evidence/phase06/artifacts
conda run --no-capture-output -n tour_de_gross python tools/audit_reference.py --output evidence/phase06/independent-audit.json
conda run --no-capture-output -n tour_de_gross python -m pytest --collect-only -q tests/test_noise_and_fault_model.py
conda run --no-capture-output -n tour_de_gross python -m pip check
conda run --no-capture-output -n tour_de_gross python -c 'import gross_design_bandle, stim; print(gross_design_bandle.__file__); print(stim.__version__)'
curl --fail --location --silent --show-error https://arxiv.org/pdf/2506.03094v1 --output evidence/phase06/paper-v1.pdf
sha256sum evidence/phase06/paper-v1.pdf
pdftotext -f 58 -l 59 -layout evidence/phase06/paper-v1.pdf evidence/phase06/paper-a7.txt
pdftotext -layout evidence/phase06/paper-v1.pdf evidence/phase06/paper-text.txt
conda run --no-capture-output -n tour_de_gross python /tmp/phase06_handoff.py
conda run --no-capture-output -n tour_de_gross python /tmp/phase06_result.py
git diff --check
```

A read-only Python heredoc in the same environment saved `audit-summary.json`.
The first phase run had **2 failed, 6 passed in 45.64s**. The fixture emitted two
consecutive identical gates, which Stim merged into an overlapping batch; adding
a TICK made the intended insertion boundary explicit. A second assertion
incorrectly expected a Bell preparation in the X1 half-LPU; it now checks the
actual edge-data role, while the Bell fixture retains exhaustive coverage.
Original failed logs/XML are preserved as `pytest-initial-failed.{txt,xml}`.
The corrected phase run passed **8 in 46.56s**. The initial command was rerun on
the final source, passing **8 in 58.58s**; its latest log/XML are the passing
`pytest-initial.{txt,xml}`. No failing execution is counted as a pass.

Final full suite: **192 passed in 398.42s**, no skips/xfails, including reference
and pipeline regressions. The independent reference audit equals the delivered
JSON; pip check has no broken requirements. No failure remains unresolved.
The handoff helper verifies branch/worktree/import, clean main, unchanged
protected fixtures/controls/source locks, canonical external commits/files and
cleanliness, the paper hash, exported source/artifact hashes, every saved
H/Lambda column and copy/group map, and all mapped JUnit passes. The result
helper validates the completion JSON against the unchanged controller schema,
gate coverage and nonempty evidence requirements. The controller will rerun
acceptance on the final tree and owns publication.

Gate mappings: `evidence/phase06/acceptance-gates.json`, exactly D03, E01, E02 and
negative_tests, covering the eight exact nodes in
`evidence/phase06/collected-nodeids.txt`. Nonempty evidence includes
`evidence/phase06/{pytest-initial.txt,pytest-initial.xml,pytest-initial-failed.txt,
pytest-initial-failed.xml,pytest-phase06.txt,pytest-phase06.xml,pytest-final.txt,
pytest-final.xml,audit-noise.txt,audit-summary.json,independent-audit.json,
audit-reference.txt,pip-check.txt,imports.txt,paper-sha256.txt,paper-a7.txt,
acceptance-gates.json,collected-nodeids.txt,handoff-validation.json,
handoff-validation.txt,result.json,result-validation.txt}`. Under
`evidence/phase06/artifacts/`, each gross C10 benchmark has its ideal circuit,
physical-location JSON, three noisy profile circuits, two independent catalogue
JSON.gz files and corresponding H/Lambda NPZ files, fixed-fault trials and N
discrepancy report. `index.json` records their nonempty sizes and hashes.
Evidence remains local under the established ignored-output policy.

O1--O5 remain open: O1 published inter K23 generators; O2 historical Relay,
priors and columns; O3 paper-exact schedule/shift/lowering/boundaries; O4 exact
Table-6 population/admission/merging; O5 original grids/counts/bootstrap.
The explicit independent noise/physical/admission policies supply all definitions
required by this phase; strict paper manifests remain fail-closed. Inherited
donor-builder reuse licensing remains open, with no donor code copied here.
XX/Y physical benchmarks, inter-module construction, shifts, decoder integration,
distance and benchmark sampling are later work and were not launched.

Short rerun: from this worktree use the phase pytest command, noise exporter,
independent reference audit, full pytest and pip check above. Stop after phase
06. Next prompt: `prompts/07_inmodule_XX_Y.md`, only in a new
controller-authorized session after acceptance/publication.


## Validation/cache maintenance completed (2026-10-02)

User-authorized preparation before resuming phase 07; scope prompt:
`prompts/maintenance_validation_cache.md`. Branch `feature/validation-cache`,
worktree `.codex-pipeline/tour-de-gross/worktrees/validation-cache`, based on clean
validated main `02f7f2f`. Canonical main was kept clean during implementation.
The original failed phase-07 worktree and all its edits/logs remain preserved.

Added explicit two-level fault caching: physical joint signatures reusable across
profiles, and structural models reusable across p. Keys include circuit/records,
locations, population policies, relevant implementation bytes and library versions.
Cold models are validated before atomic publication; warm reads verify identity
and all checksums. Interrupted/corrupt entries are quarantined/rebuilt. Test
passes are never cached. The controller supplies a canonical shared cache.

Native artifacts preserve sparse H/Lambda, all copy/admission/group/probability
maps and sparse signature set-bit arrays, with non-pickle, read-only mmap loads.
The noise exporter uses content-addressed reusable numeric artifacts by default;
expanded JSON/NPZ is opt-in. Tiny negative tests cover invalidation, interrupted
writes, corrupted matrices/signatures, p changes, logical-only and joint-zero
columns. No correlations, copies, detectors or observables were dropped.

Large benchmark flow validation now uses strict Stim determinacy and raw
reference signs; the independent signed tracker remains available for small
oracles. Constant wrong signs and random/offset-corrupt parities are rejected.
Removed duplicate first-round tableau checks and repeated large random seeds.
Large fault strata retain every phase/gate/role and first/middle/last round, using
four representative joint words; unchanged tiny gate/Bell fixtures still exhaust
all words. The optional all_words audit remains. Arbitrary sample-count thresholds
were replaced by actual stratum coverage. No unproved distance claim was added.

Remaining prompts 07--13 and the common footer now require smallest-failure-first,
then affected-phase, then one final sequential regression/export; no concurrent
identical heavy jobs. Default phase/test timeouts are 10800s/1800s (3h/30min).
Pilot/campaign budgets and fail-closed O1--O5 are unchanged. Reviewed control
migration reruns prior gates, archives old accepted records and can stop without
launching Codex. A revalidation bug was fixed: local prior evidence is checked
in its retained original worktree, while tests execute on current main.

Actual validation, all Python in tour_de_gross with PYTHONPATH=$PWD/src:

- `python -m pytest -xq tests/test_fault_cache.py --durations=10`: 17 passed.
- `python -m pytest -xq tests/test_fault_cache.py tests/test_pipeline.py tests/test_ideal_protocol.py tests/test_physical_scheduling.py --durations=10 --junitxml=evidence/validation_cache/focused.xml`: 97 passed in 75.88s.
- `python -m pytest -xq tests/test_fault_cache.py tests/test_noise_and_fault_model.py --durations=10 --junitxml=evidence/validation_cache/cache-noise.xml`: 25 passed in 34.61s.
- `python -m pytest -xq --durations=15 --junitxml=evidence/validation_cache/final.xml`: 212 passed in 250.82s, no skips/xfails. This preceded the last controller-only retained-evidence fix.
- `python -m pytest -xq tests/test_pipeline.py --junitxml=evidence/validation_cache/controller-final.xml`: 53 passed in 26.44s on final controller source.
- `python tools/benchmark_fault_cache.py --output evidence/validation_cache/c10-cache-timing.json`: cold/warm equality on gross memory C10, N=218160. Cold 13.10s, warm 1.85s, p-only change 2.73s; harness/locations separately 12.80s. First numeric export 0.80s, intact reuse 0.32s. Numeric output 26383199 bytes versus the retained dense-signature development baseline 60672700 bytes. These timings do not establish XX/Y or end-to-end pipeline speed.
- `python tools/audit_noise_and_fault_model.py --output-dir evidence/validation_cache/artifacts --cache-dir /home/quantum_teresheys/workspace/tour_de_gross_design_bundle/cache/faults`: completed memory/X1 C10, all three strict noise-profile DEMs, two independent populations each and bounded independent fault strata; all indexed file sizes/hashes verified. No rates were sampled.
- `python tools/audit_reference.py --output evidence/validation_cache/independent-audit.json`: exactly matches delivered independent audit.
- `python -m pip check`: no broken requirements. Feature import path/Stim 1.16.0 saved in imports.txt.
- `bash -n` for all pipeline shell scripts; `git diff --check`; normal read-only fetch confirmed synchronized main.

Evidence is local under `evidence/validation_cache/`, including each actual log/XML,
C10 dense-baseline and final timing JSON, native artifacts/index, independent audit,
pip/import checks and the recovery-preparation script. Small tracked report:
`validation/maintenance_validation_cache.json`. No external checkout/dependency or
scientific fixture was modified. No Monte Carlo, solver, cluster, next model phase
or tmux restart ran. O1--O5 and phase-07 final acceptance remain unresolved.

Publication at handoff preparation: validated feature candidate, normal commit,
main merge and atomic push next; actual outcome recorded in the local
`evidence/validation_cache/publication.json`. Preserve the failed worktree. Carry
its source into a fresh reviewed-main worktree and revalidate prior controller
gates with `--revalidate --reviewed-controls --revalidate-only`, without launching
an implementation session. Next phase is still `prompts/07_inmodule_XX_Y.md`;
stop after this maintenance task. Phase 07 has not passed acceptance.

Maintenance follow-up before final handoff: the cache manifest itself is now
checksummed, so valid-JSON corruption of probability/shape metadata cannot reuse
old numeric arrays as fresh evidence. The affected cache tests passed **18 in
2.16s** on this source (`python -m pytest -xq tests/test_fault_cache.py
--junitxml=evidence/validation_cache/cache-final.xml`). The C10 benchmark command
was rerun for this storage change: cold **12.84s**, warm **1.78s**, changed p
**2.43s**, first/reused export **0.69s/0.27s**, numeric storage **26383264 bytes**.
The earlier timing reports are retained. Completed export arrays were reused:
after verifying all original index hashes, four manifest hash files were added,
with writer provenance in the index. No fault matrix was regenerated for that
migration. The controller separately revalidated **143 prior mapped tests in
224.76s** on the first maintenance merge, with no model session launched. The
final source delta after that run is the manifest checksum/cache negative test,
covered by the 18-node affected run. Normal final publication and reviewed
controller revalidation follow; phase 07 remains unaccepted and unlaunched.

## Phase 07 pre-resume preparation (2026-10-02)

Stopped phase-07 edits were carried into feature/07_inmodule_XX_Y_resume on reviewed maintenance main. The original worktree, logs, draft STATUS and diff remain under .codex-pipeline/tour-de-gross. Stim-first validation, numerical caching, native export and minimal meaningful test coverage were integrated. This is preparation only: phase 07 is not accepted, and no controller/model session was launched. Its final acceptance/export must still run under prompts/07_inmodule_XX_Y.md. O1--O5 remain open.

Pre-resume smoke checks on final maintenance base: 20 passed in 0.49s (cache, signed-cache invalidation and Stim/reference sign cross-check); compileall and export --help passed. This is not phase-07 acceptance. Maintenance feature/main atomic publication verified; final prior controller revalidation: 143 passed in 220.31s, with no new model session. The original stopped worktree is unchanged.

## Phase 07 completed: independent physical in-module XX/Y (2026-10-02)

Branch: `feature/07_inmodule_XX_Y_resume`. Worktree:
`/home/quantum_teresheys/workspace/tour_de_gross_design_bundle/.codex-pipeline/tour-de-gross/worktrees/07_inmodule_XX_Y_resume`.
Preserved the supplied staged/unstaged work; its starting tracked diff and status
are saved in `evidence/phase07/preserved-{edits.diff,status.txt}`. The original
stopped worktree and logs remain intact. Canonical main stayed clean. Publication
was **not attempted**: the controller owns acceptance rerun, feature commit,
validated main merge and atomic push. This session stops after phase 07.

Extended the existing physical protocol, harness and physical noise ledger to
gross `X1*X7` and `Y1`, using C=10. The same installed full LPU has 23 vertices,
47 edge-data sites, 19 selected cycles, 90 LPU sites and 378 total physical sites.
Active couplers, signed ports and old-check dressing differ between operations.
Y is the single Hermitian `i X1 Z1`, including CY on the shared-support Bell
half. It is never a sequence of X/Z measurements. Physical gates, explicit
Bell preparation/partition/XOR, split edge measurements and software frames
remain in the full instrument. Ideal MPP occurs only in the labelled benchmark
input/terminal boundary. `build_physical_x1` retains its previous strict scope
and default; `build_physical_inmodule` defaults to ten rounds.

The Bell tableau oracle now proves nondemolition on its prepared ancilla
subspace, retaining exact signs, instead of demanding a bare operator identity
on arbitrary ancilla inputs. The independent signed tracker caches its full
immutable signed/affine rows; phase, value and state changes invalidate it.
The corresponding missing-preparation and stale-sign negative tests pass.
All 23 named centralizer rows, old-check dependencies and closure records are
preserved. Active split corrections are ideal validation only; noise construction
continues to reject that mode without an active-correction noise definition.

Changed coverage is the minimal shared-fixture phase suite: one encoded +, one
encoded - and one Choi trajectory per operation, with a complete rank-156
data/reference stabilizer witness and retained eigenspace coherence. Separate
XX factors or sequential X/Z destroy the required coherence. Complete composite
signed check tableaus, collision/Eq. (67) checks and installed couplers are
verified. Nested Bell repeats compare all flattened records/parities; tests no
longer assert REPEAT spelling. Both C10 split modes pass strict DEM and raw
reference-record signs; two-round independent signed affine checks and corrupt
offset/half/frame/sign/controlled-Pauli mutations remain. D04 compares every
raw joint column between active and software frames, then checks independent
phase/gate/role/boundary strata; actual stratum sets replace a count threshold.
D05 injects all 24 input logical Paulis and proves the named action rank is 23.
Unchanged tiny gate/Bell/Y fixtures exhaust primitive classes in the regression;
large independent checks use IX/ZI/XX/YZ and first/middle/last round strata.
No independent exhaustive large-location or distance lower-bound claim is made.

Final exported C10 results:

| operation | raw primitives | include-all copies N | excluding joint-zero N | joint decoder groups | independent raw strata | H rows / logical rows | Table-6 N / delta |
|---|---:|---:|---:|---:|---:|---:|---:|
| XX | 211968 | 439380 | 433175 | 73769 | 119 | 2145 / 23 | 398717 / +40663 |
| Y | 211668 | 438480 | 432280 | 73679 | 131 | 2145 / 23 | 400117 / +38363 |

All three named noisy profiles pass strict DEM extraction for each operation,
with gauge disabled and no disjoint approximation. Compact DEM error counts
are 73768/73678, distinct from both sampler N and joint decoder groups. Joint
X/Z tensor signatures, multiplicities 15/5/1, admission masks and complete
copy/group maps are retained. No padding or forced N match was performed.
The native schedule is 13 ticks per merged round (130 for C10, 141 including
reset/split/original verification), versus the paper's reported 12C coloring.
These counts describe the explicit independent policy, not paper equivalence.

Numerical cache/export evidence is in `artifacts/index.json` and the compact
`audit-summary.json`. Both export models started cold: XX construction 24.72s,
warm read 2.66s, changed-p read/reweight 3.73s; Y 25.48s / 2.61s / 3.54s.
Harness/location/ledger construction separately took 20.67s/21.35s. First/reused
native exports took XX 1.25s/0.59s and Y 1.22s/0.60s. Both matrices, signatures
and every copy/admission/group map agree after warm and p-only reuse. The index
checksums 65 artifact files totaling 189608509 bytes. No expanded catalogue JSON
or ZIP was generated; legacy export remains opt-in. Relevant implementation,
circuit, records and location changes invalidate keys; test/doc changes do not.
The full cache negative regressions (corruption/interruption/invalidation and
joint-zero/logical-only policy) executed and passed. Test passes are not cached.

All Python commands used `tour_de_gross` and `PYTHONPATH="$PWD/src"` so imports
resolve to this feature. `GROSS_DESIGN_CACHE_DIR="$PWD/cache/faults"` explicitly
uses a writable worktree cache because the controller's canonical cache path is
outside this session's writable roots. External sources still use the canonical
`/home/quantum_teresheys/workspace/tour_de_gross_design_bundle/external_libs`;
none was changed, fetched or copied. Frozen commits, source hashes and clean
external working trees were checked. The local pinned v1 PDF hash was verified
and Appendix A.3--A.5/A.7 inspected. Provenance is
`locks/inmodule-xx-y-sources.json`; API/policy documentation is
`docs/INMODULE_XX_Y.md`. AGENTS, pipeline controls and scientific fixtures are
unchanged. No network writes, solver, cluster, production Monte Carlo, decoder
integration or later-phase implementation ran.

Actual validation commands, from this worktree:

```bash
export PYTHONPATH="$PWD/src"
export GROSS_DESIGN_CACHE_DIR="$PWD/cache/faults"
conda run --no-capture-output -n tour_de_gross python -m pytest -xq tests/test_inmodule_xx_y.py::test_negative_joint_Bell_preparation_subspace_required --junitxml=evidence/phase07/reproducer.xml
conda run --no-capture-output -n tour_de_gross python -m pytest -xq tests/test_inmodule_xx_y.py --durations=15 --junitxml=evidence/phase07/affected.xml
conda run --no-capture-output -n tour_de_gross python -m pytest -xq 'tests/test_inmodule_xx_y.py::test_D02_C10_strict_harness_every_boundary_and_raw_API[Y1]' --durations=5 --junitxml=evidence/phase07/c10-both-modes.xml
conda run --no-capture-output -n tour_de_gross python -m pytest -xq --durations=20 --junitxml=evidence/phase07/final.xml
conda run --no-capture-output -n tour_de_gross python tools/audit_inmodule_xx_y.py --output-dir evidence/phase07/artifacts --cache-dir "$PWD/cache/faults"
conda run --no-capture-output -n tour_de_gross python tools/audit_reference.py --output evidence/phase07/independent-audit.json
conda run --no-capture-output -n tour_de_gross python -m pytest --collect-only -q tests/test_inmodule_xx_y.py
conda run --no-capture-output -n tour_de_gross python -m pip check
conda run --no-capture-output -n tour_de_gross python -c 'import gross_design_bandle, stim; print(gross_design_bandle.__file__); print(stim.__version__)'
conda run --no-capture-output -n tour_de_gross python -m compileall -q src/gross_design_bandle tests/test_inmodule_xx_y.py tools/audit_inmodule_xx_y.py
sha256sum evidence/phase07/paper-v1.pdf
pdftotext -f 45 -l 59 -layout evidence/phase07/paper-v1.pdf evidence/phase07/paper-appendix.txt
conda run --no-capture-output -n tour_de_gross python /tmp/phase07_handoff.py
conda run --no-capture-output -n tour_de_gross python /tmp/phase07_result.py
git diff --check
```

The first negative reproducer passed **1 in 1.54s**. The affected suite passed
**20 in 277.93s**, followed by the strengthened both-mode C10 Y check passing
**1 in 44.41s**. The one final sequential regression passed **234 in 427.03s**,
with no skips/xfails, on final implementation/test/export source. No failed or
incomplete run is relabelled passed. Its slowest setup was 34.68s; the affected
cold model/ledger setup was 64.95s, reduced to 17.99s with cache reuse in the
final run. The inspected hot path is physical-ledger construction plus validated
matrix/copy/group creation; no concurrent full suite/export or expensive retry
was launched. The one final exporter completed both operations. The independent
algebra audit exactly matches delivery; compilation, whitespace, imports (Stim
1.16.0) and pip dependency checks pass. No implementation failure remains.

Gate mappings are `evidence/phase07/acceptance-gates.json`: exactly B04_XX_Y,
D01, D02, D03, D04, D05 and negative_tests, using 22 distinct exact passed nodes
(20 phase nodes plus the inherited tiny gate/Bell oracle and corrupt-signature
negative test). The
handoff verifies their final JUnit results, all source/artifact hashes, frozen
external sources, clean main and protected files. The result helper checks the
unchanged controller schema and all nonempty evidence paths. Logs/XML and
collected nodes, imports/pip checks, source inspection, independent audit,
summary, handoff checks and completion JSON are local in `evidence/phase07/`.
Physical circuits, Bell/dressing/frame/observable/record/location ledgers,
native CSC/signature/map arrays, fixed-fault trials and N reports are in
`evidence/phase07/artifacts/`, indexed by size and SHA256.

O1--O5 remain open: O1 published inter K23 generators; O2 historical Relay,
priors and columns; O3 paper-exact serialized schedule/lowering/boundaries;
O4 exact Table-6 fault population/admission/merging; O5 original statistical
grids/counts/bootstrap. The independent policies specify all definitions needed
here. The remaining depth/N mismatches prevent an exact-reproduction claim;
strict paper manifests remain fail-closed. No reference correction is proposed.

Short reproducible rerun: set the two environment variables above, run the
phase test command, then the export command sequentially. Next prompt:
`prompts/08_intermodule_adapter.md`, only in a new controller-authorized session
after independent acceptance and publication. Stop here.

## Phase 08 completed: one-to-one gross Bell adapter (2026-10-02/03 JST)

Branch: `feature/08_intermodule_adapter`. Worktree:
`/home/quantum_teresheys/workspace/tour_de_gross_design_bundle/.codex-pipeline/tour-de-gross/worktrees/08_intermodule_adapter`.
The supplied worktree was clean at entry; existing scientific fixtures, AGENTS,
pipeline controls and external checkouts were preserved. Main is clean. Git
publication was **not performed**: the outer controller owns independent
acceptance, the feature commit, validated main merge and atomic push of both refs.
This session stops at phase 08; no phase 09 job was launched.

Implemented `CodeBlocks`, `build_physical_inter`, the two-block logical CX basis
and `full_two_block_centralizer_K47` harness, extending the inherited scheduler,
physical protocol and noise-location engine. `lpu/code_code_adapter.py` supplies
module ownership, Bell support partitions/readout XORs and active/installed
connectivity. Added `tests/test_intermodule_adapter.py`, the compact-array
exporter `tools/audit_intermodule_adapter.py`, `docs/INTERMODULE_ADAPTER.md` and
`locks/intermodule-adapter-sources.json`. No donor implementation was copied or
modified. The pinned v1 PDF hash was verified and Fig. 13(b), A.4 (including
footnote 14), A.5 and A.7/Table 6 were inspected from the retained phase-07 PDF.
Local extracted text: `evidence/phase08/paper-v1.txt`.

Both sets of eleven bridge data qubits remain physical. Eleven identifying X
checks and ten six-edge joint Z cycles use module-local Bell halves; the latter
reuse installed bridge-square measurement sites. Neither module's triangular
bridge check is active. The active algebraic graph has V/E/cycles = 35/58/20;
merged k = 23, distinct from the **47 named logical-action rows**. There are 710
active/allocated qubits and 778 installed sites, with 68 inactive installed sites
and maximum degree seven. An independent handoff check constrains every added
installed coupler to the identifying links or cross-module Bell links, using
the two inherited full-LPU installed graphs as the oracle.

The independently chosen schedule has 13 ticks per deformed round, C=10, and
141 physical ticks including reset, split and noiseless original verification;
the reported paper cycle is 12 ticks. Native controlled Paulis, the shared
half's installed left check site, live idle accounting and ideal boundaries are
explicit policies. The raw physical instrument has no MPP. Ideal terminal MPPs
are confined to the harness. Only the joint target is measured physically;
`published_inter_K23` fails closed until its actual rows are source-verified.

Coverage: one complete encoded-state test checks the + and - sectors and
independent encoded Choi inputs, comparing a full rank-312 data/reference
stabilizer group with the joint projector. Both individual X1 expectations
remain random. Separate factor measurements destroy a retained cross-block
coherence witness. Every physical check has an exact signed composite-tableau
readout oracle; collision and Eq. (67) checks pass. Negative cases reject wrong
module partitions, missing Bell preparation, a dropped Bell readout half,
reused/single block IDs, wrong target ordering, invalid rounds and unresolved
K23. Both C10 correction modes pass strict Stim DEM and raw reference-record
sign checks. Joint faults retain both X/Z components and are checked on both
Bell families and halves, first/middle/last rounds and every changed phase/role.
The unchanged small exhaustive gate/Bell and signed-flow oracles execute in
regression. The inter noisy circuit was checked with `a7_uniform_expanded`;
other inter noise profiles were not separately exported or claimed validated.

Actual validation commands (every Python invocation used tour_de_gross and,
where relevant, `PYTHONPATH="$PWD/src"`; the cache was the writable local
`GROSS_DESIGN_CACHE_DIR="$PWD/evidence/phase08/cache"`):

```bash
conda run --no-capture-output -n tour_de_gross python -m pytest -xq tests/test_intermodule_adapter.py::test_negative_blocks_profiles_and_rounds_fail_closed --junitxml=evidence/phase08/negative.xml
conda run --no-capture-output -n tour_de_gross python -m pytest -xq tests/test_intermodule_adapter.py --durations=10 --junitxml=evidence/phase08/phase-initial.xml
conda run --no-capture-output -n tour_de_gross python -m pytest -xq tests/test_intermodule_adapter.py::test_C_Bell_partition_XOR_schedule_and_resource_census --junitxml=evidence/phase08/resource-final.xml
conda run --no-capture-output -n tour_de_gross python -m pytest -xq --durations=15 --junitxml=evidence/phase08/final.xml
conda run --no-capture-output -n tour_de_gross python -m pytest -xq tests/test_flows_and_harness.py::test_negative_missing_unknown_duplicate_records_and_unresolved_profiles --junitxml=evidence/phase08/scope-fix.xml
conda run --no-capture-output -n tour_de_gross python -m pytest -xq tests/test_intermodule_adapter.py --durations=10 --junitxml=evidence/phase08/phase-final.xml
conda run --no-capture-output -n tour_de_gross python -m pytest -xq --durations=15 --junitxml=evidence/phase08/final.xml
conda run --no-capture-output -n tour_de_gross python tools/audit_intermodule_adapter.py --output-dir evidence/phase08/artifacts --cache-dir evidence/phase08/cache
conda run --no-capture-output -n tour_de_gross python tools/audit_reference.py --output evidence/phase08/independent-audit.json
conda run --no-capture-output -n tour_de_gross python -m compileall -q src/gross_design_bandle tools/audit_intermodule_adapter.py
conda run --no-capture-output -n tour_de_gross python -m pip check
conda run --no-capture-output -n tour_de_gross python -m pytest --collect-only -q tests/test_intermodule_adapter.py
conda run --no-capture-output -n tour_de_gross python /tmp/phase08_gates.py
conda run --no-capture-output -n tour_de_gross python /tmp/phase08_handoff.py
conda run --no-capture-output -n tour_de_gross python /tmp/phase08_result.py
git diff --check
```

The first negative node passed **1 in 5.40s**; the initial phase passed **8 in
297.99s**, before the installed-count clarification and input guard. The resource
clarification passed **1 in 54.20s**. The first broader regression stopped at
**83 passed / 1 failed in 57.70s**: supplying one CodeData to the inter harness
raised TypeError instead of a scope ValueError. That failed/partial run is
retained as `evidence/phase08/regression-initial-failed.{txt,xml}` and is not
counted as a pass. The fixed smallest node passed **1 in 7.15s**, then the final
affected phase passed **8 in 229.35s**. The one completed regression on corrected
source passed **242 in 702.42s**, no skips/xfails. Its largest changed check was
82.81s for bounded fixed-fault/active-frame/strict-noise validation. No concurrent
full suite/export or repeated solver/benchmark retry was launched.

Cold combined inter model/location setup was 101.17s; numerical reuse reduced
it to 27.13s in the affected rerun (27.55s in final regression). The inspected
hot paths are live-location construction, validated copy/group matrix creation,
and the bounded independent forward/fixed-fault sweep. The changed
`noise/locations.py` implementation conservatively invalidated prior model keys;
new inter circuit/role/observable inputs have their own key. Test/doc edits and
the scope guard do not invalidate numerical kernels. Final export found that
key intact: model load 4.96s, warm 5.47s, p-only change 7.46s, first native export
2.75s and intact reuse 1.39s. Matrices, signatures and all copy/admission/group
maps match across p changes; only probabilities are reweighted. Construction,
harnesses and serialized ledgers took 88.15s; stratified fault validation took
47.51s and noisy emission/strict DEM 33.84s. No pytest result was cached.
Timings and reuse are in `evidence/phase08/timing-summary.json` and the artifact
index. Existing tiny cache tests also exercise corruption, interruption and
invalidation in the final regression.

The final exporter ran once, sequentially after regression. It produced
392344 raw joint primitives, **817080 admitted equal-q copies**, 135606 decoder
groups, H shape **3992 x 817080** and Lambda shape **47 x 817080**. Two hundred
three representative fixed raw faults agree across reverse signatures,
independent forward propagation and probability-one Stim injection. Strict
noisy DEM has 3992 detectors, 47 observables and 135605 compact errors; that
compact count is not the sampling population. Table-6 N=743456 differs by
**+73624**, transparently reported without padding or dropping faults.
No rates, fits, decoder performance or distance bounds were generated.

Evidence: `evidence/phase08/{final.txt,final.xml,phase-final.txt,negative.txt,
resource-final.txt,scope-fix.txt,acceptance-gates.json,collected-nodeids.txt,
independent-audit.json,imports.txt,pip-check.txt,audit-export.txt,
timing-summary.json,handoff-checks.json,completion.json}`. Artifact index
`evidence/phase08/artifacts/index.json` checksums 31 files: raw/ideal/noisy
circuits, signed deformation, physical/active/installed ledgers, named frame and
active harness parities, locations, native CSC/sparse-signature/copy/admission/
group arrays, fixed trials and N discrepancy. No legacy expanded catalogue JSON
or repeated ZIP output was used. The handoff verifies all artifact/source hashes,
all eight exact mapped passed nodes for B05, C_Bell, D_inter, K47_vs_K23 and
negative_tests, independent installed-coupler additions, unchanged protected
paths, clean main and equality of the independent algebra audit to delivery.
Compilation, phase08 imports (Stim 1.16.0), dependency and whitespace checks pass.
The result helper validates the unchanged controller completion schema. Helper
sources are retained under `evidence/phase08/*-script.py`.

O1--O5 remain open: published inter K23 generators; historical Relay/prior/
column semantics; exact serialized schedule/lowering/boundaries; exact Table-6
fault population/admission/merging; original grids/counts/bootstrap. This
construction explicitly fixes every definition it requires. The K47, cycle-depth
and population differences prevent a paper-exact claim. No reference correction
is proposed. Strict sampling remains fail-closed. No long sampling, distance
solver, cluster submission, external modification or Git publication was run;
regression includes inherited tiny backend/unit sampling oracles, not a
production decoder or rate campaign.

Short reproducible rerun: set PYTHONPATH and the local cache variable as above;
run the eight-node phase command, then the exporter sequentially in tour_de_gross.
Next prompt: `prompts/09_shift_automorphism.md`, only in a new controller session
after independent acceptance and publication. Stop here.

## Phase 09 physical gross shift (2026-10-03)

Branch: `feature/09_shift_automorphism`. Worktree:
`/home/quantum_teresheys/workspace/tour_de_gross_design_bundle/.codex-pipeline/tour-de-gross/worktrees/09_shift_automorphism`.
Main checkout: `/home/quantum_teresheys/workspace/tour_de_gross_design_bundle`.
Publication: **not attempted; controller owns acceptance rerun, commit, merge
and atomic push**. The worktree was initially clean. No reference fixtures,
AGENTS, pipeline controls or external source checkouts were modified. External
sources remain in the canonical shared `external_libs` directory. No long
sampling, solver, cluster submission, decoder integration or later phase ran.

Deliverables: `circuits/shift.py`, `flows/shift.py`, `noise/shift.py`,
`bench/rates.py`, `tests/test_physical_shifts.py`,
`tools/audit_physical_shifts.py`, `docs/PHYSICAL_SHIFTS.md` and
`locks/shift-sources.json`. The existing source lock and independent scientific
fixtures are retained. The source paper was read at its v1 URL, specifically
§2.2 and A.2; A.7 and the repository contracts define the channel/normalization.
No donor code was copied or modified.

Profile `gross_B1_B0_x_plus_measure_prepare_v1` uses real installed data/check
sites and verified B1/B0 Tanner routes, implementing physical x translation.
Each transfer has two actual CX layers and a vacated-source Z readout. Transfer
detectors, intermediate check-site data roles, data/check frames and the physical
site permutation are explicit. Readout reuse tracks the **output destination
site's** prior measurement. Every ordinary Fig.4b syndrome CNOT follows the
transfers; repeated syndrome detectors transport the preceding check before
comparison. All 24 named input logical degrees are scored against transported
output Paulis and noiseless reference qubits. Every physical X/Z fault remains
a joint column with all primitive multiplicities/admission/group maps.

Timing is 14 body ticks per instruction, plus one initial noisy check-preparation
tick: C10 has **141 ticks**. The reconstruction declares one-tick terminal
X-check MX/R measure/prepare bundles, with **separate** readout and reset noise
locations. Z checks reuse their measured state with an X frame. This bundle's
device duration and paper-exact lowering remain O3, and are not a claim of a
uniquely sourced original circuit. A device taking two ticks for the bundle
requires a distinct timing profile. `paper_exact` fails closed. Reporting is
`P_circuit/C`; the normalization test uses synthetic input, never Table-6 fit
rates or fabricated observations.

Coverage: exact signed transfer propagation and small full Choi tests include
X/Z/Y, both signs, nonzero destination states and a changed vacated-site bit.
The production gross routes are also checked on all 144 physical data degrees
using 288 independent Choi correlations outside the BB codespace. Material
negatives omit a reverse CX/frame, corrupt a flow offset, remove a physical
gate or request invalid routing/profile/boundaries. C10 uses strict Stim DEM
with gauge disabled plus raw record-sign checks. Every transfer fault has a
computed signature; independent forward/probability-one Stim injection uses
first/middle/last phase/gate/role strata and IX/ZI/XX/YZ joint words. This is
bounded large-circuit coverage, not exhaustive injection of every expanded
copy. All 1440 first-transfer readout-flip primitives must retain zero logical
signature after the recorded reuse correction. The inherited A06 tests cover
complete logical actions, signed quotient witnesses, inverses, commuting x/y,
logical sixth powers and row/column conventions.

Completed validation: first negative node **1 passed in 4.50s**. Initial small
attempts failed: a signed conjugation expectation was wrong, and the nonzero
destination Choi oracle then exposed the real reused-site frame bug. The
corrected smallest B06 reproducer passed **1 in 0.21s**. A C10 attempt then
stopped with **1 passed / 1 setup error in 10.72s** because the inherited
controller cache was read-only in this sandbox. No test pass was inferred from
that incomplete run. With a writable local cache, the cold timing node passed
**1 in 41.80s**, then the affected phase/A06 run passed **13 in 114.34s**.
After adding all-144-data Choi coverage, its smallest node passed **1 in 0.71s**.
The final source also checks all 1440 reused-readout zero-logical signatures.

The single completed final regression passed **246 in 858.68s**, with no skips
or xfails. It includes all eight exact acceptance node IDs, reference and
pipeline regressions, unchanged small exhaustive gate/Bell oracles and the
cache corruption/interruption/invalidation tests. The final shift fault node
took 63.69s; inspection identified model copy/group validation, forward Pauli
propagation/per-fault Stim compilation and three profile emissions/strict DEMs
as its hot paths. No identical suite/export jobs ran concurrently and no
expensive solver or benchmark retry occurred. Earlier failed/partial logs are
retained, not counted as passes.

Final export ran once, sequentially after regression. It contains **241776 raw
joint primitives**, **403920 include-all equal-q copies**, **70993 decoder
groups**, H **4464 x 403920** and Lambda **24 x 403920**. All 106 representative
raw faults agree with independent forward propagation and probability-one
Stim injection. All three noise profiles have strict gauge-disabled DEMs with
4464 detectors and 24 observables. Table-6 gross-shift N=483840 differs by
**-79920**; excluding joint-zero copies would instead give 389880. Counts by
primitive kind, phase and role are exported. No population padding, forced
merging, discarded X/Z correlations or sampled rates were introduced.

Cold timing-node setup/check was 41.80s; its warm counterpart in regression
was 14.31s. These are combined harness/location/model/check timings, not pure
model timings. Export found the existing numerical key intact: initial model
load 2.81s, warm load 3.00s, changed-p reweight 4.01s, native array export 1.47s.
Export harness/location/validation took 11.94s and independent fault strata
22.15s. Across p changes, H/Lambda, raw/group signatures and every copy,
ordinal/admission/group map are identical; only probabilities change. The new
shift circuit and location/role/frame ledger create their own key. Test/doc
edits do not invalidate numerical work; the inherited tiny cache regressions
validate changed inputs/implementations and damaged/partial artifacts. No
pytest result was cached. The controller's canonical cache path was read-only
here, so all completed local work uses `GROSS_DESIGN_CACHE_DIR="$PWD/cache/faults"`.

Actual validation commands used `tour_de_gross`; prepend
`PYTHONPATH="$PWD/src"` for feature imports and the writable cache variable
above for model tests. Commands with superseded failures are listed as such:

```bash
# Positive constructor/schedule, toy-frame debugging, JUnit inspection and
# import-origin probes also ran as conda Python stdin scripts.
conda run --no-capture-output -n tour_de_gross python -m pytest -xq tests/test_physical_shifts.py::test_negative_shift_profiles_routing_frame_and_noise_boundaries
conda run --no-capture-output -n tour_de_gross python -m pytest -xq tests/test_physical_shifts.py  # initial failed signed/Choi attempt
conda run --no-capture-output -n tour_de_gross python -m pytest -xq tests/test_physical_shifts.py::test_B06_two_transfer_Choi_signed_Paulis_and_recorded_frame  # failed first; corrected reruns passed
conda run --no-capture-output -n tour_de_gross python -m pytest -xq tests/test_physical_shifts.py tests/test_shifts.py  # initial failed/partial; completed writable-cache rerun passed
conda run --no-capture-output -n tour_de_gross python -m pytest -xq tests/test_physical_shifts.py::test_shift_timing_C10_real_permutation_roles_K24_and_rate
conda run --no-capture-output -n tour_de_gross python -m pytest -xq --durations=15 --junitxml=evidence/phase09/final.xml
conda run --no-capture-output -n tour_de_gross python tools/audit_physical_shifts.py --output-dir evidence/phase09/export --cache-dir "$PWD/cache/faults"
conda run --no-capture-output -n tour_de_gross python -m compileall -q src/gross_design_bandle tools/audit_physical_shifts.py
conda run --no-capture-output -n tour_de_gross python -m pip check
conda run --no-capture-output -n tour_de_gross python /tmp/phase09_handoff.py
git diff --check
git diff --exit-code -- reference AGENTS.md prompts/scripts
```

Evidence is local, nonempty and repository-relative:
`evidence/phase09/{negative_first.txt,phase_first.txt,B06_rerun.txt,
phase_rerun.txt,B06_rerun_2.txt,phase_rerun_2.txt,timing_cache_rerun.txt,
phase_local_cache.txt,B06_full_physical.txt,final.txt,final.xml,
acceptance-gates.json,audit-export.txt,imports.txt,pip-check.txt,
handoff-checks.json,handoff-checks.txt,timing-summary.json}`.
`evidence/phase09/export/index.json` hashes 30 artifacts, including raw/ideal/
noisy circuits, role/frame/location ledgers, logical action, joint sparse
native CSC matrices/signatures/maps and the N discrepancy. Handoff validation
matched source hashes, all export checksums and every mapped node to completed
JUnit passes; main is clean and fixtures/controls/AGENTS unchanged. Compilation,
feature-module imports, dependency consistency and whitespace checks passed.

O1: published inter K23 rows remain undefined. O2: historical Relay parameters,
priors and columns remain unverified. O3: the chosen shift representative,
one-tick cross-basis bundle, serialized scheduling/lowering and boundary noise
are an explicit reconstruction, not frozen paper equivalence. O4: Table-6
primitive population/admission policy is unresolved; the -79920 discrepancy
is not repaired by changing fixtures. O5: original statistical grids/counts/
bootstrap data are unavailable. None supplies a missing definition for this
named independent gross construction. No rate, decoder or distance claim is
made, and strict paper-exact mode remains blocked.

Short reproducible sequence: export PYTHONPATH and the local cache as above;
run `python -m pytest -q tests/test_physical_shifts.py tests/test_shifts.py`,
then `python tools/audit_physical_shifts.py --output-dir evidence/phase09/export
--cache-dir "$PWD/cache/faults"`, both with `conda run --no-capture-output -n
tour_de_gross`. Next prompt: `prompts/10_two_gross_extension.md`, only in a new
controller session after independent acceptance and publication. Stop at 09.


## Phase 10 two-gross extension (2026-10-03)

Branch: `feature/10_two_gross_extension`. Worktree:
`/home/quantum_teresheys/workspace/tour_de_gross_design_bundle/.codex-pipeline/tour-de-gross/worktrees/10_two_gross_extension`.
Validated base at entry: `36df268b9ae3d9affdbf07b5b251c38a88af767e`.
Main checkout: `/home/quantum_teresheys/workspace/tour_de_gross_design_bundle`,
still clean. The feature worktree was initially clean. Publication: **not
attempted; the controller owns acceptance rerun, commit, merge and atomic push**.
No reference fixtures, AGENTS, pipeline controls or external sources changed.
The canonical external directory remains
`/home/quantum_teresheys/workspace/tour_de_gross_design_bundle/external_libs`;
no donor implementation was copied or modified, so no fork was needed.
The pinned locally cached v1 PDF was read for A.3/A.4/A.7/A.8; its SHA256
matches `locks/paper-sources.json`. No source download or network write occurred.

Deliverables: `bench/two_gross.py`, `validation/phenomenological.py`,
`tests/test_two_gross_extension.py`, `tools/audit_two_gross_extension.py`,
`docs/TWO_GROSS_EXTENSION.md`, `locks/two-gross-extension-sources.json`, and
the shared code/block/harness/shift adapters. The same physical BB generators
now accept either reference code without gross-size simulation hardcoding.
Every in-module surgery has C18; idle and real shift have 18 repetitions;
inter C17 and C18 are separate **extensions**, neither a Figure-15 series.
Idle/shift reporting is P/C; surgery reporting is P. Rate tests use synthetic
input only. All surgery profiles record `circuit_distance=None`.

The unchanged chosen X1/X7/Z1/Z7 supports have weight 20. Both halves retain
their two expansion edges, 20 vertices and 32 edges. Full LPU geometry retains
17 bridge edges and its reduced 37 selected cycles (39 vertices, 81 edges,
158 installed LPU sites). Omitted-cycle redundancy has signed witnesses in
the complete deformed group. The inter graph retains 57 vertices, 98 edges
and 38 cycles; its one-to-one Bell adapter has 17 identifying and 16 joint
six-edge cycle checks, no active triangles, and 1502 installed physical sites.
All named K24/K23/full-K47 rows are retained. Published inter K23 fails on O1.
Direct Y uses iXZ, never sequential X/Z measurements.

Changed coverage shares lazy geometry/harness fixtures and one large catalogue
at a time. It includes complete signed +/- and encoded Choi trajectories for
all five surgery profiles, every preserved logical correlation, and a full
288-data physical Choi transfer check outside the BB codespace. Schedules
check every signed physical readout with a composite Clifford tableau, Bell
XORs/preparation, collisions, Eq.67 ordering and installed connectivity. C17/C18
flows use strict Stim DEM (gauge disabled) plus raw reference-record signs.
Material negatives reject deleted bridge cycles, imaginary Y, separate-factor
measurements, omitted Bell preparation, wrong routing/record offsets, invalid
blocks/profile/boundaries and undefined paper profiles. Existing small signed
propagation, exhaustive Bell/gate oracles and reference/pipeline tests are reused.

Large faults use deterministic phase/gate/role/first-middle-last strata and
IX/ZI/XX/YZ joint words. They are not exhaustive injection of the full large
population. All 5184 first-transfer readout-flip signatures retain zero logical
action. Representative Bell/Y/split signatures agree in active/frame modes.
Joint H/Lambda, multiplicities and every admission/group map remain aligned;
include-all admits joint-zero terms. The native exports have these actual counts:

| Profile | Raw terms | Include-all copies | Decoder groups | Logical rows | Independent raw trials |
| --- | ---: | ---: | ---: | ---: | ---: |
| two_gross_idle | 508896 | 781920 | 213409 | 24 | 33 |
| two_gross_shift | 869472 | 1447200 | 254881 | 24 | 106 |
| two_gross_X_C18_extension | 665164 | 1400100 | 231558 | 23 | 71 |
| two_gross_XX_C18_extension | 782802 | 1733670 | 260298 | 23 | 119 |
| two_gross_Y_C18_extension | 782046 | 1730970 | 260153 | 23 | 140 |
| two_gross_inter_XX_C17_extension | 1371336 | 3041460 | 454110 | 47 | 203 |
| two_gross_inter_XX_C18_extension | 1451788 | 3219180 | 480866 | 47 | 203 |

Two-gross idle has N=781920 vs Table-6 N=762912 (**+19008**). Shift has
N=1447200 vs Table-6 N=1748736 (**-301536**). Excluding joint-zero terms would
give idle 771552 and shift 1399536, respectively. These are explicit O3/O4
population discrepancies, not corrected fixtures, padding, forced merging,
sampled observations or evidence that Table-6 fit rates were reproduced.
Memory has 145 ticks; physical shift has 253 ticks. The inherited B1/B0 x
route and one-tick MX/R bundle (separate readout/reset fault sites), native
controlled-Pauli schedule, ideal encoded/terminal boundaries and include-all
equal-q population are named reconstruction choices, not paper-exact claims.

A.8 Eq.84 inputs are prepared for X, XX, Y and inter-XX. Spatial q is a full
2k quotient basis (22 one-block / 46 two-block jobs); temporal q is L and M
omits every vertex check without adding L. Pauli OR weight counts Y once.
C17/C18 share intrinsic inputs, not a duplicate job. Each family declares a
120s/10000-node aggregate cap, 5s/1000 nodes per job, one worker and no retries.
Native M/q arrays and job manifests are hashed. Independently checked temporal
weight-20 and spatial candidate witnesses supply **upper bounds only**;
solver lower bounds are null. No solver/backend, exact circuit-distance search,
decoder integration, sampling, campaign, cluster job or later phase ran.
There is no claim that all two-gross surgery has circuit distance 18.

Validation history (every Python command used `tour_de_gross` with feature
imports): the first negative node passed **1 in 0.46s**. Early attempts were
interrupted (exit 130), with no completed JUnit report or invented pass:
`changed-small.txt`, `construction-profile.txt`, `affected.txt`,
`phase-stable.txt`, `affected-faults.txt`. Diagnostic stacks exposed repeated
support computation/Clifford compilation and Stim circuit property scans.
The fixes retain every check: sort/readout grouping and supports are computed
once; one compiled composite inverse checks all separate signed readouts;
location operands and circuit qubit/detector counts are hoisted out of loops;
the repeated physical cycle is compiled/remapped once. Numerical inputs and
validation semantics are unchanged by these performance fixes.

Completed scoped checks: labels **1 in 27.64s**; changed inter-C18 physical
readout plus inherited positive/negative primitive tests **3 in 39.51s**;
location/admission/signature negative **1 in 1.61s**; exhaustive small joint
gate/Bell and corruption checks **2 in 2.39s**. The cold affected fault/A.8
subset passed **8, 23 deselected in 1487.56s**. Its inter-C17/C18 calls took
410.19/426.49s, including redundant full expanded matrix revalidation. This
is whole-check cold timing, not a pure model-build timing. The new trusted
audit flag's tiny positive and corrupt-raw negative test passed **1 in 0.48s**.
Default standalone/mutated validation remains full; large unmodified public
builder models avoid repeating structural checks already performed cold or
verified by warm checksums. All independent forward/Stim trials still execute.

After source stabilized, the one full-regression attempt was stopped before
its 1800s bound (exit 130). Its ordered pytest console output records **276
completed passes**, but it has no completed JUnit report and is **not reported
as a passed command**. The unchanged collection has 278 cases. Only the two
unfinished nodes (inter-C18 faults and A.8) were continued, sequentially, and
passed **2 in 381.47s** with JUnit. C18 took 325.86s; A.8 took 54.53s because
its other constructions were fresh in that process. `final-coverage.json`
records the exact console-progress/collection basis, hashes and continuation
outcomes. All 278 collected cases are covered without restarting earlier
completed tests; no skips/xfails or earlier phase pass reports are substituted.
The controller still independently reruns every mapped node and regressions.

The artifact exporter ran once, sequentially after that continuation, and
checked every source/output hash. No identical suite/export ran concurrently.
It packages the actual numerical fault observations, not cached pytest passes;
model-key and oracle-source hashes must match. Native CSC/signature/map arrays
use `bench.artifacts.export_fault_model`; no expanded fault JSON or repeated
ZIP export is generated. No solver or benchmark was retried.

Export initial loads found all seven numerical keys intact. Warm same-p and
p=.002 reuse have identical H/Lambda, raw/group signatures and every copy,
ordinal/admission/group array, verified by a complete structural checksum.
Only probabilities change. Actual pure load/export timings in seconds:

| Profile | Initial existing-key load | Warm load | Changed-p load | Native export |
| --- | ---: | ---: | ---: | ---: |
| two_gross_idle | 6.71 | 6.13 | 7.74 | 3.45 |
| two_gross_shift | 12.83 | 11.70 | 14.32 | 8.98 |
| two_gross_X_C18_extension | 8.69 | 8.40 | 11.29 | 5.35 |
| two_gross_XX_C18_extension | 10.70 | 10.28 | 13.71 | 6.48 |
| two_gross_Y_C18_extension | 10.32 | 10.62 | 13.60 | 6.72 |
| two_gross_inter_XX_C17_extension | 21.49 | 20.47 | 26.03 | 15.06 |
| two_gross_inter_XX_C18_extension | 22.88 | 21.81 | 28.24 | 16.50 |

Changes to `noise/locations.py` and `noise/signatures.py` invalidated the old
implementation keys before the completed cold subset; old artifacts were
preserved. Physical signatures remain reusable across populations/p values;
structures across p values. Tests/docs do not invalidate numerical keys or
cache a pass. The controller cache is outside sandbox write roots, so local
runs explicitly use `GROSS_DESIGN_CACHE_DIR="$PWD/cache/faults"`.
Compilation, feature import origin, dependency consistency, output checksums,
seven gate mappings, clean main, branch and fixture/control guards passed.

Actual commands (prepend `PYTHONPATH="$PWD/src"` and the cache variable above
to Python validation commands). Interrupted diagnostic attempts are included
and are not counted as passed checks:

```bash
conda run --no-capture-output -n tour_de_gross python -m pytest -xq tests/test_two_gross_extension.py::test_negative_profiles_blocks_and_paper_claims
conda run --no-capture-output -n tour_de_gross python -m pytest -xq tests/test_two_gross_extension.py -k 'not joint_fault' --durations=10 --junitxml=evidence/phase10/changed-small.xml  # interrupted
conda run --no-capture-output -n tour_de_gross python -m cProfile -o evidence/phase10/construction.pstats -m pytest -xq tests/test_two_gross_extension.py::test_extension_labels_and_normalization -o faulthandler_timeout=60 --durations=5  # interrupted; pstats not completed
conda run --no-capture-output -n tour_de_gross python -m pytest -xq tests/test_two_gross_extension.py::test_extension_labels_and_normalization -o faulthandler_timeout=60 --durations=5 --junitxml=evidence/phase10/construction-fast.xml
timeout 1800s conda run --no-capture-output -n tour_de_gross python -m pytest -xq tests/test_two_gross_extension.py --durations=15 --junitxml=evidence/phase10/affected.xml -o faulthandler_timeout=180  # interrupted
conda run --no-capture-output -n tour_de_gross python -m pytest -xq 'tests/test_two_gross_extension.py::test_two_gross_schedule_and_physical_readout[two_gross_inter_XX_C18_extension]' tests/test_physical_scheduling.py::test_C01_signed_single_and_bell_tableau_oracles tests/test_physical_scheduling.py::test_negative_bad_sign_gate_bell_preparation_and_collision --durations=5 --junitxml=evidence/phase10/readout-fast.xml
timeout 1800s conda run --no-capture-output -n tour_de_gross python -m pytest -xq tests/test_two_gross_extension.py --durations=15 --junitxml=evidence/phase10/phase-stable.xml -o faulthandler_timeout=180  # interrupted
conda run --no-capture-output -n tour_de_gross python -m pytest -xq tests/test_noise_and_fault_model.py::test_negative_profiles_admission_maps_and_corrupt_signatures --junitxml=evidence/phase10/locations-negative.xml
timeout 1800s conda run --no-capture-output -n tour_de_gross python -m pytest -xq tests/test_two_gross_extension.py -k 'joint_fault or bounded_A8' --durations=12 --junitxml=evidence/phase10/affected-faults.xml -o faulthandler_timeout=180  # interrupted
conda run --no-capture-output -n tour_de_gross python -m pytest -xq tests/test_noise_and_fault_model.py::test_D03_exhaustive_gate_templates_and_joint_Bell_faults tests/test_noise_and_fault_model.py::test_negative_profiles_admission_maps_and_corrupt_signatures --junitxml=evidence/phase10/signatures-small.xml
timeout 1800s conda run --no-capture-output -n tour_de_gross python -m pytest -xq tests/test_two_gross_extension.py -k 'joint_fault or bounded_A8' --durations=12 --junitxml=evidence/phase10/affected-faults-fast.xml -o faulthandler_timeout=180
conda run --no-capture-output -n tour_de_gross python -m pytest -xq tests/test_two_gross_extension.py::test_fault_audit_revalidation_contract_and_corrupt_raw_oracle --junitxml=evidence/phase10/audit-contract.xml
timeout 1800s conda run --no-capture-output -n tour_de_gross python -m pytest -xq --durations=20 --junitxml=evidence/phase10/final.xml -o faulthandler_timeout=240  # interrupted; final.xml absent
conda run --no-capture-output -n tour_de_gross python -m pytest --collect-only -q
timeout 1800s conda run --no-capture-output -n tour_de_gross python -m pytest -xq 'tests/test_two_gross_extension.py::test_two_gross_joint_fault_strata_and_catalogue[two_gross_inter_XX_C18_extension]' tests/test_two_gross_extension.py::test_bounded_A8_jobs_and_independent_witness_checks --durations=5 --junitxml=evidence/phase10/final-continuation.xml -o faulthandler_timeout=240
timeout 1800s conda run --no-capture-output -n tour_de_gross python tools/audit_two_gross_extension.py --output-dir evidence/phase10/export --cache-dir "$PWD/cache/faults"
conda run --no-capture-output -n tour_de_gross python -m compileall -q src/gross_design_bandle tools/audit_two_gross_extension.py
conda run --no-capture-output -n tour_de_gross python -m pip check
conda run --no-capture-output -n tour_de_gross python evidence/phase10/validate_handoff.py
git diff --check
git diff --exit-code -- reference AGENTS.md prompts/scripts
```

Feature-import and progress/fault-count probes additionally ran as bounded
conda Python `-c` commands; their actual outputs are saved. Evidence:
`evidence/phase10/` completed/partial `.txt` logs, scoped JUnit `.xml` files,
`final-collection.txt`, `partial-outcomes.txt`, `final-continuation.xml`,
`final-coverage.json`, `fault_checks/*.json`, `fault-oracle-counts.json`,
`environment.txt`, `imports.txt`, `export.txt`, `export/index.json`, all seven
profile summaries/population/physical/circuit/model manifests/native arrays,
four `export/A8_*/` job families/candidate witnesses, `acceptance-gates.json`
and `handoff-checks.json`. The index verifies nonempty file sizes/checksums;
gate mapping names existing exact positive/negative pytest node IDs.

Unresolved paper-exact items: **O1** published inter K23 row selection;
**O2** historical Relay semantics/priors/columns; **O3** original scheduling,
lowering, timing/shift/boundaries; **O4** Table-6 primitive population/admission;
**O5** original statistical grids/counts/bootstrap data. None is silently
filled by a fixture change or a fabricated source definition. The named
independent profiles have all definitions needed for this phase; strict paper
configuration stays closed. Solver and circuit-distance results remain absent.

Short reproduction from this worktree (no later phase, sampling or solver):

```bash
export PYTHONPATH="$PWD/src"
export GROSS_DESIGN_CACHE_DIR="$PWD/cache/faults"
timeout 1800s conda run --no-capture-output -n tour_de_gross python -m pytest -xq tests/test_two_gross_extension.py
timeout 1800s conda run --no-capture-output -n tour_de_gross python tools/audit_two_gross_extension.py --output-dir evidence/phase10/export --cache-dir "$GROSS_DESIGN_CACHE_DIR"
```

Next prompt: `prompts/11_relay_adapter.md`, submitted by the controller only
after phase-10 validation/publication. This session stops at phase 10.

## Phase 11 joint Relay integration completed (2026-10-03)

Branch: `feature/11_relay_adapter`. Worktree:
`/home/quantum_teresheys/workspace/tour_de_gross_design_bundle/.codex-pipeline/tour-de-gross/worktrees/11_relay_adapter`.
Main checkout: `/home/quantum_teresheys/workspace/tour_de_gross_design_bundle`,
verified clean. The initial feature worktree was clean; no existing edits were
replaced. Publication: **not attempted; controller owns rerun, commit, merge and
atomic push**. External source remains unmodified in the canonical shared
`/home/quantum_teresheys/workspace/tour_de_gross_design_bundle/external_libs`.
No external fork was needed for this thin binding and independent mathematical
oracle. No reference fixtures, AGENTS or pipeline controls changed.

Implemented `bench/relay.py`: joint sparse H, fixed priors and named Lambda
rows; audited backend/binary pin; float32/float64; gamma0/explicit or seeded
gammas; maximum sets/iterations; supported stopping and minimum-prior-cost
candidate selection; independent Hc=sigma verification; counted malformed,
residual-syndrome, nonconvergence and logical failures with no discard/fallback.
Separate `preserve_columns` and `joint_signature_xor` decoder-graph profiles
retain an explicit input-to-decoder map. Sampling still addresses the original
admitted copies. Group priors XOR-compose the fixed input vector rather than
following the sampling probability. All joint X/Z and logical-only columns
remain represented; equal H with different Lambda cannot be merged.

`validation/relay.py` is a bounded independent recurrence oracle, derived from
Relay v1 PDF Eqs. (1)--(4)/Algorithm 1; no donor code copied. Tests compare every
accessible first-leg prefix and selected returned posteriors/corrections,
candidate cost replacement/ties, caps and stopping on a four-variable trap.
Later-leg intermediate states are oracle-only because the binding does not
expose them. Explicit gamma row indexing starts at leg 1, modulo row count.
Seeded streams hash (root seed, stable shot ID) into independent Rust seeds and
reconstruct each shot's backend; scalar/batch/reordered worker allocation
agree, with distinct random posterior outputs for the same syndrome under
independent IDs. Explicit mode exercises the actual native detailed batch API.

`docs/RELAY_ADAPTER.md`, `locks/relay-adapter-sources.json` and
`tools/audit_relay_adapter.py` document and verify licenses, seven exact source
blobs/hashes, installed build, raw Table-7 data and actual current settings.
**Source-backed prose correction:** phase-00 documentation described the
alpha default as a ramp; actual source has alpha=None -> 1 and alpha=0 -> ramp.
The new documentation and a ramp vector record the correction; fixtures are
unchanged. The historical ewainit/gamma/rng_width/extra max_iter/prior/column
mapping remains unproved. A historical or paper-exact adapter request fails
closed on O2. No guessed historical translation is exposed.

Decoder priors are fixed and copied/read-only, with no weight/p update API.
Evidence uses a fixed .003 vector at sampling p=.03 and .04. This is an
independent policy, not a recovered paper prior. Uniform scaling is homogeneous
in exact real arithmetic for the unclipped equations. Two finite-prior vectors
are checked for both precisions, without asserting universal floating-point
invariance. Manifests explicitly retain this limitation.

Changed coverage: five meaningful phase nodes cover E03/E04/E05 and material
negative cases, using one shared small Bell-reference fault fixture. Fixed
injections cover no fault, X/Y/Z and an undetectable logical-only fault. These
are deterministic test vectors, not random sampling or rate observations.
The circuit export scores all five vectors: one observable failure (the
logical-only fault), no discarded shot, invalid return or nonconvergence.
Negative vectors independently demonstrate contradictory/inconsistent returns
and an unsatisfiable syndrome with capped nonconvergence.

Completed runs, all using `tour_de_gross` and feature imports: first negative
**1 passed in 0.58s**; initial affected phase **5 in 0.31s**; strengthened
recurrence **1 in 0.28s**; strengthened stream test **1 in 0.65s**; affected
stable **5 in 0.67s**; source-build negative **1 in 0.64s**; final affected
**5 in 0.33s**. One final scoped regression **115 passed in 31.76s**, no skips
or xfails, then one sequential artifact export passed. No failing/interrupted
run or expensive retry occurred. The regression includes phase 11, reference,
pipeline, backend/source/manifest, fault-cache/storage and small independent
signed Bell/gate and joint-population checks. Unchanged large C10/C18 physical
harnesses were not re-exhausted: no physical/noise implementation changed.
Pipeline tests use isolated temporary repositories/fake commands, not project
publication. Compilation and pip dependency consistency passed.

Compact export uses `bench.artifacts.export_fault_model` plus checksummed native
arrays for decoder priors/gammas, grouped CSC H/Lambda and variable maps. The
39 nonempty files in `export/index.json` have verified hashes and source
identities; no expanded catalogue JSON/NPZ or repeated ZIP writes were added.
Pure uncached tiny model: **0.002802s**; initial existing-key read **0.003897s**;
warm **0.003700s**; changed-p **0.003504s**; native export **0.003253s**. The
initial numerical key was already present from phase tests. Warm/changed-p H,
Lambda, signatures and every copy/admission/group map agree; only probabilities
change. Adapter/test/doc changes do not invalidate physical fault keys. The
regression executes inherited cold/warm, physical/implementation invalidation,
corruption and interruption tests; cached numerical arrays never cache a test
pass. Local cache was explicitly `$PWD/cache/faults`, within the writable
feature worktree, rather than the controller cache outside writable roots.

Actual validation commands (the shell invocations prepended
`PYTHONPATH="$PWD/src" GROSS_DESIGN_CACHE_DIR="$PWD/cache/faults"` where
applicable; outputs were saved under `evidence/phase11/`):

```bash
conda run --no-capture-output -n tour_de_gross python -m pytest -xq tests/test_relay_adapter.py::test_E03_negative_returns_and_nonconvergence --junitxml=evidence/phase11/negative-first.xml
conda run --no-capture-output -n tour_de_gross python -m pytest -xq tests/test_relay_adapter.py --durations=6 --junitxml=evidence/phase11/affected.xml
conda run --no-capture-output -n tour_de_gross python -m pytest -xq tests/test_relay_adapter.py::test_E04_fixed_gamma_recurrence_candidates_and_prior_policy --junitxml=evidence/phase11/recurrence-strengthened.xml
conda run --no-capture-output -n tour_de_gross python -m pytest -xq tests/test_relay_adapter.py::test_E05_scalar_native_batch_and_independent_streams --junitxml=evidence/phase11/streams-strengthened.xml
conda run --no-capture-output -n tour_de_gross python -m pytest -xq tests/test_relay_adapter.py --durations=6 --junitxml=evidence/phase11/affected-stable.xml
conda run --no-capture-output -n tour_de_gross python -m pytest -xq tests/test_relay_adapter.py::test_negative_parameters_profiles_and_graphs --junitxml=evidence/phase11/backend-pin-negative.xml
conda run --no-capture-output -n tour_de_gross python -m pytest -xq tests/test_relay_adapter.py --durations=6 --junitxml=evidence/phase11/affected-final.xml
 timeout 1800s conda run --no-capture-output -n tour_de_gross python -m pytest -xq tests/test_relay_adapter.py tests/test_backends.py tests/test_source_audit.py tests/test_manifest.py tests/test_reference.py tests/test_pipeline.py tests/test_fault_cache.py tests/test_noise_and_fault_model.py::test_D03_exhaustive_gate_templates_and_joint_Bell_faults tests/test_noise_and_fault_model.py::test_E02_admission_logical_only_zero_columns_hyperedges_and_joint_grouping tests/test_noise_and_fault_model.py::test_negative_profiles_admission_maps_and_corrupt_signatures --durations=12 --junitxml=evidence/phase11/regression-final.xml
conda run --no-capture-output -n tour_de_gross python tools/audit_relay_adapter.py --output-dir evidence/phase11/export --cache-dir "$PWD/cache/faults"
conda run --no-capture-output -n tour_de_gross python -m compileall -q src/gross_design_bandle/bench/relay.py src/gross_design_bandle/validation/relay.py tools/audit_relay_adapter.py
conda run --no-capture-output -n tour_de_gross python -m pip check
conda run --no-capture-output -n tour_de_gross python evidence/phase11/validate_handoff.py
git diff --check
git diff --exit-code -- reference AGENTS.md prompts/scripts
```

Three bounded conda Python `-c` diagnostic probes examined trap/candidate
trajectories before the strengthened test vectors; they ran no solver or
Monte Carlo. A conda Python stdin provenance script wrote the new source lock
from the inspected pinned Git blobs. The exporter independently re-verifies
those blobs and the retained Table-7 fixture hash; neither diagnostic is
substituted for an acceptance test.

Evidence: `evidence/phase11/` scoped JUnit files and `.txt` logs,
`regression-final.xml`, `regression-final.txt`, `export.txt`, `pip-check.txt`,
`acceptance-gates.json`, `handoff-checks.json`; `export/index.json`,
`export/source-verification.json`, `export/cache-and-timing.json`,
`export/small-circuit-scoring.json`, both precision recurrence artifacts,
`export/decoder_inputs/`, `export/grouped_decoder_inputs/`, and native
`export/small_Bell_model/` arrays/manifests. Exact gates name all five existing
pytest nodes; all are present and passed in the final regression.

O1: published inter K23 named rows unresolved. O2: original historical
Table-7 executable/parameters, priors and column policy unresolved; only the
current implementation is verified. O3: original schedule/lowering/shift and
boundary choices unresolved. O4: original Table-6 primitive population and
admission/merging unresolved. O5: original grids/counts/bootstrap data unresolved.
These do not require an assumption for this independently labeled adapter.
Strict paper configuration remains closed. No integer/fixed-point/historical
Relay, optional compiler, statistical campaign, solver, cluster job, network
write or later phase was executed.

Short reproduction (no sampling or subsequent phase):

```bash
export PYTHONPATH="$PWD/src"
export GROSS_DESIGN_CACHE_DIR="$PWD/cache/faults"
conda run --no-capture-output -n tour_de_gross python -m pytest -xq tests/test_relay_adapter.py
conda run --no-capture-output -n tour_de_gross python tools/audit_relay_adapter.py --output-dir evidence/phase11/export --cache-dir "$GROSS_DESIGN_CACHE_DIR"
```

Next prompt is `prompts/12_sampling_and_analysis.md`, requiring a new explicit
phase-12 authorization and the bounded pilot context after controller
acceptance/publication. The present through-11 authorization ends here.

## Phase 12 sampling and analysis candidate (2026-10-03; incomplete gross pilot)

Branch `feature/12_sampling_and_analysis`; worktree
`/home/quantum_teresheys/workspace/tour_de_gross_design_bundle/.codex-pipeline/tour-de-gross/worktrees/12_sampling_and_analysis`.
The controller owns commit, merge and atomic push; publication was **not
attempted**. The main checkout and external sources were not edited. No
reference fixture, AGENTS or pipeline control was changed.

Added `bench/sampling.py`, `bench/results.py`, `bench/analysis.py`,
`tools/audit_sampling.py`, `docs/SAMPLING.md` and five mapped tests in
`tests/test_sampling_analysis.py`. The same admitted copy columns feed
independent Bernoulli `q=p/15` and uniform without-replacement fixed-weight
draws. Sparse CSC accumulation retains joint H/Lambda bits. The pinned Relay
adapter's sequential compiled batch path uses fixed priors and one thread;
every invalid return/nonconvergence remains a failure. Run manifests hash
circuits, raw catalogue/maps, joint matrices, decoder settings and sampler
source. Chunk seeds identify faults and decoder streams separately. Checksummed
append-only JSONL records deduplicate identical resumes and reject conflicting
ones. Each shot retains weight and failure flags, including below `w0` and
gross-Y above 80. Zero failures receive exact one-sided binomial upper bounds.
The Table-6-shaped ansatz, binomial integration/tail bound, gross-Y-only fit
selection, chi-squared/Jeffreys-variance bootstrap and separately labeled
likelihood fit use only new observed counts, never printed Table-6 rates.

Tiny exact subsets, Bernoulli mixture, distribution sanity, negative inputs,
result corruption, stream separation, fixed priors and pilot limits passed.
An initial F03 test failed because its *test oracle* omitted GF(2) reduction;
the oracle was fixed and the smallest node then passed. The affected phase
passed **5/5**, followed by one final scoped regression of **90/90** including
Relay, fault-cache, reference and pipeline tests (28.06s). Compilation,
dependency check and Git whitespace/fixture-control guards passed.

The tiny Bell smoke pilot used three points: fixed weights 1 and 2, and
Bernoulli p=.03. An initial diagnostic ran 32 shots per point before the final
per-shot schema; after source stabilized, the final export ran 32 additional
shots at those same three points. Total: **64 shots per point, three points,
well under 120 seconds combined pilot wall time** (the two recorded inner
times are 0.057s and 0.077s). The final 96-shot export has failure counts
14/32 at w=1, 13/32 at w=2, and 0/32 direct Bernoulli; the last is an upper
bound, not a zero rate. These are tiny Bell smoke observations, **not gross or
Figure-15 performance evidence**. No further pilot points were run. The
standalone exporter uses `bench.artifacts.export_fault_model` and native
checksummed arrays; it did not create expanded JSON/NPZ. Initial model build
0.0101s and warm read 0.0056s; final existing-key read 0.00685s and warm
read 0.00356s. The sampler changes did not invalidate physical signatures;
the scoped cache tests covered cold/warm, changed-p, corruption and relevant
implementation invalidation. No solver, long sampling or upstream write ran.

**Acceptance gap:** F03 calls for direct Bernoulli versus fixed-weight
estimates on accessible *gross* pilot points. The authorized three selected
points were spent on the tiny Bell smoke case, so that gross comparison was
not run. This phase is therefore a preserved candidate, **not complete and
not safe for controller progression**. Do not count the passing tiny F03 node
as gross pilot evidence. A new explicit pilot budget or reviewed replacement
evidence is needed before this requirement can pass. O1--O5 remain open for
paper-exact replication: inter K23 rows, historical Relay semantics, original
schedule/boundaries, Table-6 N convention, and original grids/counts/bootstrap
settings. The independent phase-12 implementation needs no invented values
for these fields.

Commands actually run in this feature worktree (Python commands used
`tour_de_gross`; source imports used `PYTHONPATH="$PWD/src"`, and exporter used
`GROSS_DESIGN_CACHE_DIR="$PWD/cache/faults"`):

```bash
conda run --no-capture-output -n tour_de_gross python -m pytest -xq tests/test_sampling_analysis.py::test_negative_sampling_and_result_corruption
conda run --no-capture-output -n tour_de_gross python -m pytest -xq tests/test_sampling_analysis.py  # first run failed at test oracle; later affected run 5 passed
conda run --no-capture-output -n tour_de_gross python -m pytest -xq tests/test_sampling_analysis.py::test_F03_exact_subsets_and_bernoulli_mixture
conda run --no-capture-output -n tour_de_gross python -m pytest -xq tests/test_sampling_analysis.py::test_negative_sampling_and_result_corruption
conda run --no-capture-output -n tour_de_gross python -m pytest -xq tests/test_sampling_analysis.py
timeout 120s conda run --no-capture-output -n tour_de_gross python tools/audit_sampling.py --output-dir evidence/phase12/export --cache-dir "$PWD/cache/faults"
timeout 1800s conda run --no-capture-output -n tour_de_gross python -m pytest -xq tests/test_sampling_analysis.py tests/test_relay_adapter.py tests/test_fault_cache.py tests/test_reference.py tests/test_pipeline.py --junitxml=evidence/phase12/regression.xml
timeout 120s conda run --no-capture-output -n tour_de_gross python tools/audit_sampling.py --output-dir evidence/phase12/export-final --cache-dir "$PWD/cache/faults"
conda run --no-capture-output -n tour_de_gross python -c "from gross_design_bandle.bench.results import read_chunks; from gross_design_bandle.bench.analysis import spectrum_from_chunks; ..."
conda run --no-capture-output -n tour_de_gross python -m compileall -q src/gross_design_bandle/bench/sampling.py src/gross_design_bandle/bench/results.py src/gross_design_bandle/bench/analysis.py tools/audit_sampling.py
conda run --no-capture-output -n tour_de_gross python -m pip check
git diff --check
git diff --exit-code -- reference AGENTS.md prompts/scripts
```

Evidence: `evidence/phase12/regression.xml`, `regression.txt`,
`export/pilot-report.json`, `export-final/pilot-report.json`,
`export-final/run-manifest.json`, `export-final/chunks.jsonl`, and the native
fault model directory named in the final report. The pilot records distinguish
actual observations from model fits and unpublished targets. No source-backed
fixture correction was needed. Short reproduction of completed checks:

```bash
export PYTHONPATH="$PWD/src"
export GROSS_DESIGN_CACHE_DIR="$PWD/cache/faults"
conda run --no-capture-output -n tour_de_gross python -m pytest -xq tests/test_sampling_analysis.py
```

The next planned prompt is `prompts/13_statistical_campaign.md`, **only after**
the phase-12 gross pilot requirement is resolved and controller acceptance and
publication succeed. This session stops at phase 12.

## Phase 12 F03 acceptance revision (2026-10-03; local validation complete)

This entry supersedes the acceptance-gap conclusion above; the original failed
attempt and its pilot records remain preserved. Branch:
`feature/12_sampling_and_analysis`. Worktree:
`/home/quantum_teresheys/workspace/tour_de_gross_design_bundle/.codex-pipeline/tour-de-gross/worktrees/12_sampling_and_analysis`.
The canonical `main` checkout remains clean at `ab1ffe0`.

The user-supplied review identified that the former F03 gross estimator
agreement criterion could not be established by a 256-shot smoke pilot,
especially with zero failures. Revised `docs/VALIDATION_PLAN.md` and
`prompts/12_sampling_and_analysis.md` now require exact tiny-catalogue
enumeration and a deterministic physical gross idle joint H/Lambda-to-Relay
integration check. `tests/test_sampling_analysis.py` adds fixed zero and
nonzero admitted error vectors on the one-round gross idle physical harness,
checks their independent sparse matrix products and executes compiled Relay
batch decoding. This uses no new Monte Carlo shots and makes no gross rate or
Bernoulli-versus-fixed-weight statistical agreement claim. `docs/SAMPLING.md`
records the revised evidence scope. A gross estimator comparison is a later
separately budgeted statistical job with prespecified stopping, precision and
inconclusive-result rules. It must not be inferred from the earlier tiny Bell
pilot. O1--O5 remain unresolved; strict paper-equivalent rates remain blocked.

Commands actually run from this worktree, with `PYTHONPATH="$PWD/src"` and
`GROSS_DESIGN_CACHE_DIR=/home/quantum_teresheys/workspace/tour_de_gross_design_bundle/cache/faults`:

```bash
conda run --no-capture-output -n tour_de_gross python -m pytest -xq tests/test_sampling_analysis.py::test_F03_gross_idle_deterministic_joint_path  # 1 passed, 3.39s
conda run --no-capture-output -n tour_de_gross python -m pytest -xq tests/test_sampling_analysis.py::test_negative_sampling_and_result_corruption  # 1 passed
conda run --no-capture-output -n tour_de_gross python -m pytest -xq tests/test_sampling_analysis.py  # 6 passed, 2.86s
timeout 1800s conda run --no-capture-output -n tour_de_gross python -m pytest -xq tests/test_sampling_analysis.py tests/test_relay_adapter.py tests/test_fault_cache.py tests/test_reference.py tests/test_pipeline.py --junitxml=evidence/phase12/revised-regression.xml  # 91 passed, 31.23s
conda run --no-capture-output -n tour_de_gross python -m compileall -q src/gross_design_bandle/bench/sampling.py src/gross_design_bandle/bench/results.py src/gross_design_bandle/bench/analysis.py tools/audit_sampling.py tests/test_sampling_analysis.py
git diff --check
git diff --exit-code -- reference AGENTS.md prompts/scripts
```

Evidence: `evidence/phase12/revised-regression.xml` and the retained
`evidence/phase12/export-final/` pilot artifacts described above. The test
evidence is deterministic gross integration; the earlier pilot is a tiny Bell
smoke run. Neither supplies a statistically precise gross comparison. No new
sampling pilot, solver, cluster job, external source edit or network write ran.
No fixture correction was needed. Local phase validation passes under the
revised F03 criterion; the controller has not yet rerun acceptance or
published this feature. Publication outcome: **not attempted; controller owns
acceptance rerun, commit, merge and atomic push**. Next prompt after controller
acceptance/publication is `prompts/13_reproduction_campaign.md`, subject to a
separate explicit campaign budget. Stop at Phase 12.

## Phase 12 final local review (2026-10-03)

Branch `feature/12_sampling_and_analysis`, worktree
`/home/quantum_teresheys/workspace/tour_de_gross_design_bundle/.codex-pipeline/tour-de-gross/worktrees/12_sampling_and_analysis`.
The controller still owns acceptance, commit, merge and atomic push; none was
attempted here. The earlier bounded tiny Bell pilot was retained with no new
shots or points. Added point summaries with explicit nonconvergence rates and
one-sided zero-failure upper bounds, plus an extrapolation check that requires
an explicitly declared holdout p grid and independent direct counts. The
holdout implementation was tested with synthetic counts; no real holdout
sampling or extrapolation validation was claimed. `docs/SAMPLING.md` records
that limit. Existing O1--O5 remain unresolved for paper equivalence, but no
unresolved definition was used to construct or validate this phase's
independent sampler.

Validation commands actually run in this review:

```bash
conda run --no-capture-output -n tour_de_gross python -m pytest -xq tests/test_sampling_analysis.py::test_negative_sampling_and_result_corruption  # first failed on a test regex, then 1 passed
conda run --no-capture-output -n tour_de_gross python -m pytest -xq tests/test_sampling_analysis.py  # first stopped on inherited read-only main-cache path
GROSS_DESIGN_CACHE_DIR="$PWD/cache/faults" conda run --no-capture-output -n tour_de_gross python -m pytest -xq tests/test_sampling_analysis.py::test_F03_gross_idle_deterministic_joint_path  # 1 passed
GROSS_DESIGN_CACHE_DIR="$PWD/cache/faults" conda run --no-capture-output -n tour_de_gross python -m pytest -xq tests/test_sampling_analysis.py  # 6 passed
GROSS_DESIGN_CACHE_DIR="$PWD/cache/faults" timeout 1800s conda run --no-capture-output -n tour_de_gross python -m pytest -xq tests/test_sampling_analysis.py tests/test_relay_adapter.py tests/test_fault_cache.py tests/test_reference.py tests/test_pipeline.py --junitxml=evidence/phase12/final-regression.xml > evidence/phase12/final-regression.txt 2>&1  # 91 passed, 29.44s
conda run --no-capture-output -n tour_de_gross python -c 'import json; from pathlib import Path; from gross_design_bandle.bench.results import read_chunks; from gross_design_bandle.bench.analysis import point_summaries, spectrum_from_chunks; base=Path("evidence/phase12/export-final"); rows=list(read_chunks(base/"chunks.jsonl").values()); output={"source":"existing tiny Bell pilot chunks; no new shots", "performance_evidence":False, "point_summaries":point_summaries(rows), "spectrum":spectrum_from_chunks(rows)}; (base/"analysis-summary.json").write_text(json.dumps(output, indent=2, sort_keys=True)+"\n")'
conda run --no-capture-output -n tour_de_gross python -m compileall -q src/gross_design_bandle/bench/analysis.py src/gross_design_bandle/bench/results.py src/gross_design_bandle/bench/sampling.py tools/audit_sampling.py tests/test_sampling_analysis.py
git diff --check
git diff --exit-code -- reference AGENTS.md prompts/scripts
```

Evidence: `evidence/phase12/final-regression.xml`,
`evidence/phase12/final-regression.txt`, and the retained
`evidence/phase12/export-final/{run-manifest.json,chunks.jsonl,pilot-report.json,analysis-summary.json}`.
The existing 32-shot Bernoulli point had zero observed failures and a 95%
one-sided upper bound of 0.08937; it is tiny Bell execution evidence only.
The final regression exercised warm physical fault reuse via the worktree
cache; the earlier phase-12 export records cold/warm timings (0.0101s/0.0056s
initial; 0.00685s/0.00356s final). Cache tests cover changed-p reuse and
implementation invalidation. No new native fault export was needed because
the phase-12 analysis addition does not change physical signatures or the
existing exported model. Changed coverage: declared holdout grid validation,
point-level nonconvergence rates, zero-failure point bounds, plus the retained
F03 gross deterministic batch path and F05 resume/budget negatives.

Short reproduction without new sampling:

```bash
export GROSS_DESIGN_CACHE_DIR="$PWD/cache/faults"
conda run --no-capture-output -n tour_de_gross python -m pytest -xq tests/test_sampling_analysis.py
```

Next prompt after controller acceptance/publication:
`prompts/13_reproduction_campaign.md`, only with a separate explicit campaign
budget. Stop at phase 12.
