# Maintenance phase: validation and fault-artifact reuse

Implement only the user-requested preparation before resuming phase 07. Preserve
the stopped worktree; do not complete XX/Y or launch the pipeline in this session.

Add explicit, content-addressed fault-model caching and a compact, non-pickle
numeric artifact format. Reuse signatures across probability changes, retain
joint H/Lambda and all population maps, and invalidate on physical inputs,
policies, relevant implementation bytes or dependency versions. Publish cache
entries atomically; incomplete/corrupt entries must never become passed evidence.

Prefer Stim for large-circuit checks; keep independent signed/template oracles
small. Remove duplicated work within tests, not scientific checks. Run failures
first, then the changed phase, then one final regression. Cache artifacts, never
pytest success. Update remaining prompts, bounded timeouts and recovery guidance.

Acceptance: cache cold/warm equivalence, invalidation, interrupted/corrupt entry
recovery, probability reuse, compact round-trip/mmap and preserved joint-zero
columns; existing noise/flow/reference/controller regressions. Save actual
commands, timings and limitations in STATUS. Commit/merge/atomic publication
follow AGENTS.md; stop after this maintenance phase.
