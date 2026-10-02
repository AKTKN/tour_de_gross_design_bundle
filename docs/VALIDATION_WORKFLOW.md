# Efficient validation and numerical artifact reuse

This policy implements the user's 2026-10-02 request before resuming phase 07.
It changes work allocation, not the physical/scientific contracts. O1--O5 remain
open. Do not delete detectors, discard fault copies or loosen a wrong expected
observable to pass a test.

## Minimal required coverage

Keep one meaningful test per changed behavior and a negative test for its
material failure mode. Combine related assertions in the same fixture. Test
semantics rather than literal REPEAT spelling, JSON whitespace, cache directory
names or redundant seeds. Do not add a new exhaustive suite for an inherited
primitive whose implementation is unchanged.

* Small signed Pauli/Bell fixtures: exact phases, joint measurement/coherence,
  both halves, representative negative sign and frame omission. Existing tiny
  exhaustive oracles remain; do not repeat them for every large operation.
* Each new physical operation: collision/overlap checks, intended signed check
  readout, one + input, one - input, and one encoded Choi trajectory checking
  all preserved logical generators. Extra random seeds do not constitute proof.
* Benchmark: complete named logical rows, strict DEM with gauge disabled,
  and raw reference-record parity signs. Use Stim for C10/C18. Retain the
  independent signed tracker on small fixtures and short changed boundaries.
* Fault catalogue: aligned joint H/Lambda, multiplicities/admission/group maps,
  zero-H/logical-only faults and joint-zero policy. Validate gate templates on
  tiny circuits, then bounded deterministic phase/gate/role/boundary strata.
  Large two-qubit strata use IX, ZI, XX and YZ, covering both operand sides,
  joint faults and Y; unchanged tiny templates cover every word. An explicit
  `word_policy='all_words'` audit is available when needed.
  Do not independently inject every expanded copy into a large circuit.
* Decoder/sampling: inconsistent corrections and nonconvergence are failures;
  use tiny deterministic vectors/subsets and preserve scientific profile labels.

## Run order and failures

1. Run the changed negative test or smallest reproducer with `pytest -xq NODE`.
2. Run the phase's minimal mapped nodes, sharing expensive module fixtures.
3. After source stabilizes, run the final regression once and the artifact export
   once. The controller independently reruns every required mapped node.

On a failure, fix and rerun the failed node first (`--lf` is useful locally).
Run the affected phase afterward. Restart a broad regression/export only if the
source change invalidates it. Do not run identical phase, full-suite and exporter
jobs concurrently: they duplicate fixture work and compete for memory/CPU.
Never cache a pytest pass or relabel an incomplete log as passed. If a check
takes over 60 seconds, record its duration and inspect/profile its hot path
before launching another copy. Preserve failed/partial logs under unique names.

## Fault cache

`build_fault_model(..., cache_dir=PATH)` enables explicit numerical reuse;
`GROSS_DESIGN_CACHE_DIR` provides a process default. `cache_dir=False` disables
it for a cold comparison. The controller shares `cache/faults` in the canonical
checkout between feature worktrees. Imports perform no file or network I/O.

Keys include the exact Stim circuit (including detector/observable/record
annotations), full location provenance, storage version, relevant implementation
file hashes and Stim/NumPy/SciPy versions. Model keys additionally include profile,
admission and grouping; probability p is separate. Test/doc edits do not invalidate
numerical work. A different physical circuit/location or implementation does.

There are two levels: raw joint fault signatures, reused across population
profiles, and the full structural model, reused across p values. Changed p only
recomputes primitive and grouped XOR probabilities. Cold construction performs
the full model checks. Warm reads check every stored file checksum and identity;
they do not regenerate the matrices merely to compare them with themselves.
Acceptance tests still execute. Changed independent-oracle code reruns its checks.

Writes use a private directory and atomic rename after completion, with per-key
process locks. Missing manifests/checksum failures cause quarantine and rebuild;
cache hits never accept partial output. Cold tests check misses, invalidation,
corruption, interruption and equality with uncached results.

## Artifact format

`bench.artifacts.save_fault_model` / `load_fault_model` store a small manifest,
the circuit/location provenance and native `.npy` arrays. H and Lambda use CSC
data/indices/indptr; all copy/admission/group/probability maps are preserved.
Raw/group signatures are sparse set-bit indices and column pointers, not repeated large hex JSON strings.
Primitive words are deterministically reconstructed from the locations/profile.
No pickle or object arrays are loaded. Reads verify SHA256 and support read-only
memory mapping; full scientific validation is the default for standalone loads.

Uncompressed arrays avoid repeated ZIP compression and allow mmap. They may
use more disk than compressed NPZ; this is a deliberate development-speed tradeoff.
Use legacy compressed JSON/NPZ only for a specific consumer (`--legacy-json` in
the noise exporter), or compress an immutable delivery once. Model artifacts are
content-addressed and reused by the exporter. They are not an independent oracle
or scientific fixtures, and are never written into `reference/`.

## Time limits and stopped-chain recovery

Defaults are 10800 seconds per implementation phase and 1800 seconds per
controller test run. Overrides remain available. These do not enlarge the
phase-12 pilot (120s) or a phase-13 user campaign budget; no automatic retry.

Control/prompt edits invalidate the old controller signature intentionally.
After reviewed publication, use `--revalidate --reviewed-controls
--revalidate-only` to recheck prior mapped nodes and record the reviewed new
signature without launching Codex. A changed reference fixture still fails.
The previous accepted record is archived before replacement. Pending phase work
must be carried into a fresh worktree based on the new validated main, preserving
the original stopped worktree and logs. Do not silently resume against an old
base, reset edits, erase acceptance history or mark phase 07 complete.
