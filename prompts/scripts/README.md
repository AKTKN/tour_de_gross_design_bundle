# Tour de gross Codex/tmux pipeline

Adapted from the five user-supplied shell/schema/footer files previously used by a different package. Their decoder checkout, theory filename, six stages and checkpoint commits have been replaced with this repository's fourteen bounded phases. No upstream code was copied. The runner is development orchestration, not a simulation API.

The JSON configuration lists prompts 00–13, scoped gate IDs from `docs/VALIDATION_PLAN.md`, required phase-00 audit artifacts, and pilot/campaign permissions. Bash wrappers launch a Python controller in the `tour_de_gross` Conda environment. Each phase gets a separate `codex exec` invocation, an assembled prompt, a schema-constrained final result and a durable log. Each feature phase uses a new branch and separate worktree from `main`. After each session stops, the controller reruns acceptance checks, commits the validated feature, merges it into `main`, and atomically pushes both branches to `origin` before submitting the next authorized prompt. Launching the controller authorizes that explicit phase interval; creating these scripts does not launch implementation.

Run the controller from the canonical `main` checkout. It requires a clean working tree, a configured Git identity and `origin`, and local `main` equal to fetched `origin/main`. It preserves user edits by stopping if the main checkout is dirty or divergent; it never stashes, resets or force-pushes them.

For phase 00, for example, it creates `feature/00_source_audit` under `.codex-pipeline/tour-de-gross/worktrees/00_source_audit/`, switches the Codex working directory to that worktree, and supplies its `src/` directory on PYTHONPATH for validation. The terminal runner stays in the canonical checkout. External source checkouts remain in the canonical checkout's shared `external_libs/` directory; the controller supplies that path and writable access to it. Failed and completed worktrees are retained for inspection. Do not start another controller from a feature worktree.

After validation it saves `validation/phase_00.json`, refreshes source checksums, stages the feature changes, and commits. It uses a normal `--no-ff` merge and checks that the merged source tree exactly matches the validated feature commit. If main or its remote advanced meanwhile, it stops for review. One `git push --atomic` publishes the feature branch and main together; a push rejected by remote branch protection or another remote change stops progression. Feature branches are retained; no automatic branch deletion occurs. Only verified publication marks a phase accepted.

From the repository root, check local availability:

```bash
conda activate tour_de_gross
command -v codex
codex --version
codex login status
codex exec --help
command -v tmux
tmux -V
prompts/scripts/run_codex_pipeline.sh --preflight
```

If CLI authentication is missing, run `codex login` or `codex login --device-auth`. Saved authentication is reused by `codex exec`. Preflight inspects the installed CLI flags, authentication and Conda imports without a model request. Observed during setup: codex-cli 0.157.1, tmux 3.2a, ChatGPT authentication. The CLI is installed through Node/NVM, outside Conda; it must remain on PATH after activating Conda. The launcher preserves the current PATH even if a tmux server was created with an older environment.

An optional live availability check makes a model request, without running implementation:

```bash
codex exec --sandbox read-only -c 'approval_policy="never"' --ephemeral \
  'Do not call tools or edit files. Reply exactly CODEX_OK.'
```

Model/account access is not established by `--version` or login status. A login check only establishes stored authentication.

Inspect the plan before launching:

```bash
prompts/scripts/run_codex_pipeline.sh --list --through 13
prompts/scripts/start_codex_pipeline_tmux.sh --dry-run --through 11
```

When ready to implement, start phase 00 alone:

```bash
prompts/scripts/start_codex_pipeline_tmux.sh --through 00
```

To authorize automatic progression through decoder integration, use:

```bash
prompts/scripts/start_codex_pipeline_tmux.sh --through 11
```

With no arguments, the controller resumes at the first unaccepted phase and stops after 11. `--from 00` (also a prompt filename or stem) specifies the next pending phase; it cannot skip unaccepted prerequisites or rerun accepted phases. A failed phase stops immediately and keeps the feature branch, worktree and logs. After inspecting or fixing that worktree, use `--resume-feature` to run its pending phase again; it is never retried automatically. If you intentionally changed main after an accepted phase, first validate, commit and push those main changes yourself, then use `--revalidate` to rerun all prior mapped acceptance tests before a new phase. Revalidation does not commit a dirty main checkout. Revalidation cannot accept modified reference fixtures, pipeline controls or prompts. For a deliberate control/prompt revision, review and archive the state directory before starting a fresh chain; existing source work is preserved and earlier phases must be rechecked.

Inspect the detached session and logs:

```bash
tmux attach -t codex-tour-de-gross
# Detach with Ctrl-b d.
prompts/scripts/codex_pipeline_status.sh
tail -f .codex-pipeline/tour-de-gross/pipeline.log
```

Detailed model and test logs are in `.codex-pipeline/tour-de-gross/runs/<run-id>/<phase>/`. The overview log shows controller events and links to each result; model output is in `codex.log`. `accepted.json` records accepted stages, prompt/control/workspace hashes, protected reference hashes and independently rerun test reports. `active.json` and `exit-code` record state; `current-feature.json` identifies a preserved feature workspace and `pending-publication.json` records a validated commit awaiting merge/push. The Git command log is `.codex-pipeline/tour-de-gross/git.log`. Accepted entries include feature/base/merge commit hashes and verified publication status. Small validation reports are tracked under `validation/`; full transcripts and local state remain ignored. All pipeline state is ignored by Git. Each run has a unique directory; stale results cannot satisfy a new invocation. A file lock prevents simultaneous controllers in one checkout. Existing tmux sessions are refused. Completed panes stay visible (`remain-on-exit`); the status command distinguishes a running pane from a completed one. Close a completed session with `tmux kill-session -t codex-tour-de-gross` before starting another. Killing an active pane or Ctrl-C interrupts the controller and terminates the current child process group; inspect logs and edits before resuming.

To use another session name, set `CODEX_TMUX_SESSION`, for example `CODEX_TMUX_SESSION=tour-gross-00 prompts/scripts/start_codex_pipeline_tmux.sh --through 00`. Use the same variable for the status wrapper. This does not permit concurrent controllers in the same checkout.

Acceptance requires a valid result schema, matching stage ID, explicit success, no blocking issue, all required reported commands passed, exact coverage of configured gates, existing nonempty evidence and an updated STATUS. The controller reruns each mapped exact pytest node ID, reference regressions and pipeline regressions in `tour_de_gross`. Every mapped node must have passed setup/call/teardown; skips, xfails, missing nodes, timeouts and failures stop advancement. Positive and negative scientific tests must be meaningful and mapped to the correct phase scope. The mechanical gate verifies execution, coverage and reported artifacts; it cannot prove the tests' scientific adequacy or exact paper equivalence. O1–O5 can remain open for independent construction; a source definition needed by the current phase must block it. No Table-6 fit evaluation is treated as sampled data.

Defaults bound each Codex phase to 3600 seconds and each controller test run to 600 seconds; override with `--stage-timeout SECONDS` and `--test-timeout SECONDS`. These are process-group timeouts, not automatic retries. Use `--model NAME` only when you want to override the installed Codex configuration.

The default sandbox is `workspace-write`, with this Conda environment added as a writable directory and network access enabled for source inspection/downloads. External source checkouts remain under `external_libs/`; fork before modifying them. Phase agents must leave Git commits, merges and publication to the controller. They still cannot write external upstream repositories, rewrite history, change pipeline controls, or run unbounded work. Sandbox execution can still fail because of host policies; choose `--sandbox` explicitly if your environment requires another supported mode. The scripts do not automatically bypass the sandbox. Feature commits and pushes are explicitly authorized by this workflow. Scientific fixture modifications remain blocked. Unauthorized control/fixture/history edits stop acceptance, and the controller preserves them for review.

If a validated merge/push failed, inspect the Git log and resolve the external cause, then run:

```bash
prompts/scripts/run_codex_pipeline.sh --retry-publish
```

This retries only the immutable validated candidate, verifies the merged tree and both remote refs, and exits. It does not call Codex or begin another phase. Local main may already contain its validated merge while remote main is unchanged; pending state makes that explicit. Unexpected source/history/control changes stop publication. If a process stopped during branch creation or a commit hook changed the candidate, inspect the retained worktree/history manually rather than discarding it.

Phase 12 requires an explicit bounded pilot launch:

```bash
prompts/scripts/start_codex_pipeline_tmux.sh --through 12 --allow-pilot
```

The phase prompt fixes at most 256 shots per point, three accessible points and 120 seconds total pilot wall time. The sampler must enforce these limits; phase timeout separately bounds the overall implementation session. A phase result cannot replace actual validation or counts.

Phase 13 additionally requires a user-authored JSON budget file:

```json
{
  "max_shots": 1000,
  "max_wall_seconds": 300,
  "profile": "SOURCE_VERIFIED_PROFILE_NAME",
  "series": ["EXPLICIT_VALIDATED_SERIES_NAME"]
}
```

Those names are illustrative placeholders, not runnable scientific profiles or permission to reproduce Figure 15. Supply real validated names and limits, then pass `--campaign-budget /path/to/budget.json` with `--through 13` (and `--allow-pilot` if phase 12 is still pending). Positive limits, profile and series are required; phase 13's model process is capped by the lesser of the stage timeout and budget wall time. Workload shot/series/profile limits must also be enforced by the implementation. Unmet scientific prerequisites stop the campaign regardless of budget.

Verify this infrastructure locally without Codex model calls:

```bash
conda run --no-capture-output -n tour_de_gross python -m pytest -q \
  tests/test_pipeline.py tests/test_reference.py
for script in prompts/scripts/*.sh; do bash -n "$script"; done
```

Tests use fake Codex/Conda commands, temporary repositories and local bare Git remotes to exercise success, failures, skips, timeouts, protected-file changes, resume/revalidation, duplicate-run locks, atomic push failure/recovery, dirty main, commit-hook mutations and remote advancement. The tmux test uses a separate temporary server and fake Codex. It does not run implementation, simulation or paid model requests. See [official non-interactive documentation](https://learn.chatgpt.com/docs/non-interactive-mode) for structured outputs and saved CLI authentication, and [CLI commands](https://learn.chatgpt.com/docs/developer-commands?surface=cli) for login checks. Local `codex exec --help` is the compatibility authority for the installed version.
