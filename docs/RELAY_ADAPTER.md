# Phase 11: joint current-Relay adapter

`gross_design_bandle.bench.relay.JointRelayAdapter` accepts sparse joint H,
fixed decoder priors, Lambda, and the names of all Lambda rows. It binds to
[Relay commit d185194](https://github.com/trmue/relay/tree/d185194ba0cb4101ced4340d82b2ee6d42f225f0),
the unmodified Apache-2.0 source build locked in phase 00. Float32 and float64
are exercised. Integer/fixed-point, historical Table-7, OSD and separate-sector
backends are unavailable. Construction verifies the installed binary SHA256;
another platform/build needs a reviewed lock. Imports do no source/network I/O.
No external source was changed or copied; no fork/publication was needed.

```python
from gross_design_bandle.bench.relay import JointRelayAdapter, RelayConfig, summarize
import numpy as np

decoder = JointRelayAdapter(
    H, np.full(H.shape[1], .003), Lambda,
    logical_names=logical_names,
    config=RelayConfig(precision='float32', seed=91),
)
results = decoder.decode_batch(syndromes, stream_ids=unique_stable_shot_ids)
counts = summarize(results, true_logical_actions)
manifest = decoder.manifest(historical_raw_parameters=raw_table7_fixture)
```

This is an independently chosen decoder profile, not a claim that .003 was
the paper's fixed-weight prior. Keep the same constructed decoder/prior vector
for all weights and sampling probabilities when measuring one f(w). The API
has no weight/p-dependent prior update or tuning argument. Caller arrays are
copied; priors/gammas are read-only. A p-dependent prior defines f(w;p) instead.

## Audited recurrence and current conventions

The mathematical source is the [Relay v1 paper](https://arxiv.org/pdf/2506.01779v1),
PDF pp. 2--3 Eqs. (1)--(4) and p. 8 Algorithm 1. Messages start at prior log
odds; check messages start at zero. The first leg starts with marginals equal
to log odds and memory strength gamma0. Subsequent legs reset messages and
retain the preceding final marginals. Bias is
`(1-gamma_j)*ell_j + gamma_j*M_j(previous)`. Check messages use signed minimum
absolute incoming magnitude; variable messages exclude their recipient check.
Hard decision is 1 for posterior <=0 (including exact zero).

The inspected current Rust binding/core are pinned, with blobs and SHA256 in
`locks/relay-adapter-sources.json`. Details necessary for reproducible tests:

* `alpha=1` is unscaled min-sum. **Correction to phase-00 audit prose:** current
  `alpha=None` also means 1, while `alpha=0` requests the ramp
  `1-2**(-iteration/alpha_iteration_scaling_factor)`. Source and a ramp vector
  verify this. The historical fixture is unchanged.
* First-leg cap is pre_iter, followed by at most num_sets legs, each capped by
  set_max_iter. Total cap is their sum. A converged leg stops on its first
  syndrome-consistent iterate. `nconv` counts every converged leg including
  the initial one, not distinct corrections. `all` runs every leg. `pre_iter`
  returns early only if the initial leg converges; otherwise current source
  still runs the later legs. Backend max_iter is the selected leg's cap;
  manifest iteration_cap is the overall cap. Iterations report total work.
* Current explicit gammas use `row = leg % number_of_rows`, where the first
  disordered leg is leg **1**. Row zero is not the first disordered leg unless
  there is one row. Arrays may wrap; their shape/hash and this indexing are
  recorded. First leg always uses gamma0.
* Random gammas use Rust StdRng with independent Uniform(low,high) draws in
  column order. Seeded adapter calls construct a fresh backend per shot using
  SHA256 of `gross-relay-stream-v1:root_seed:stream_id`, with the first eight
  bytes interpreted little endian. Stable unique IDs give scalar/batch and
  worker allocation invariance on this pinned binary. IDs must identify shots
  globally; caller reuse intentionally repeats a stream. Explicit mode reuses
  the supplied gamma rows every shot and calls the native detailed batch API.
  No backend internal parallel API or cross-version RNG guarantee is claimed.
* Selection minimizes sum(c_j*log((1-q_j)/q_j)) over converged legs; an equal
  cost retains the earlier candidate. If all legs fail, current Relay returns
  its initial-leg failed candidate with total iterations, not the last leg's
  vector. The adapter retains and scores this failure.

`validation.relay.trace_current_relay` is a bounded independent scalar
recurrence diagnostic, never a decoding fallback. Tests compare returned
corrections, posteriors, candidate costs, replacement/ties and stopping for
fixed explicit gammas. Prefix runs expose each first-leg decision before
convergence. The native API does not expose every internal later-leg iterate;
exported later-leg trajectories are labeled oracle-only, while selected
outputs and total work are compared to the backend. These checks certify the
current conventions on small vectors, not historical trace equivalence.

With finite positive uniform log odds and no clipping, these equations are
homogeneous in exact real arithmetic. Scaling all odds by a positive constant
preserves signs, stopping and cost order there. Tests check two uniform priors
on a trap vector for both float precisions. Rounding, ties, overflow and
clipping prevent inferring universal finite-precision scaling invariance.
The manifest explicitly declines that universal claim; priors remain fixed.

## Joint graph and scoring

Sorted CSC indices preserve supplied variable order and all named Lambda rows.
Duplicate sparse coordinates XOR over GF(2). Duplicate *columns*, ineffective
columns, logical-only columns and joint X/Z hyperedges remain separate in
`preserve_columns`. The adapter never splits a fault into independent sectors.
`from_fault_model` preserves the admitted physical copy population even when
an upstream model also supplies optional groups.

Explicit `joint_signature_xor` constructs a separate decoder graph using both
H and Lambda. It saves the complete input-to-decoder map and XOR-composed
**fixed** priors. Original sampling columns/admission/multiplicity maps remain
in the fault model. Grouping preserves the unconditional channel, but defines
a different decoding function and must not be substituted silently in a
fixed-weight spectrum. Correction bits in this profile address decoder groups;
score their logical prediction directly, rather than choosing arbitrary copies.

Every successful adapter outcome requires an independently recomputed Hc=sigma.
Correction shape/dtype/binary range, decoded detectors, finite posteriors,
success flag and iteration counts are checked. Malformed or contradictory
returns are counted as invalid failures. Backend nonconvergence is a failure
even with a syndrome-consistent vector. Logical mismatch is also a failure,
including logical-only faults with zero syndrome. No shot is discarded.
Summary counters can overlap; observable failures count available predictions,
and malformed predictions still count in total failures.

## O2 and scientific limits

TdG v1 PDF Table 7 p. 61 and the independently locked fixture retain gamma,
rng_width, ewainit_discount_factor, set_num_iters, max_iter and
ms_scaling_factor. The cited Relay paper supplies a recurrence and examples,
including initial gamma=.125, but does not establish how the TdG historical
keys map to the current implementation. The inspected first public code
release postdates both June v1 papers and later posterior/memory reset fixes
altered state initialization. We have not established the original Table-7
executable, extra max_iter semantics, prior vector or column policy. The
tempting `1-.875` and interval transformations are not installed as mappings.
Manifests retain raw Table-7 data separately from actual resolved current
settings; requests for historical/paper-exact profiles fail closed on O2.

O1 (published inter K23 rows), O2 (historical decoding), O3 (original physical
schedule/boundaries), O4 (Table-6 population/admission), and O5 (original
statistical data) remain open. Independent phase-11 construction has no missing
definition; this phase does not authorize sampling, a pilot or phase 12.

Reproduce with `PYTHONPATH="$PWD/src"` and local
`GROSS_DESIGN_CACHE_DIR="$PWD/cache/faults"` in the feature worktree:

```bash
conda run --no-capture-output -n tour_de_gross python -m pytest -xq tests/test_relay_adapter.py
conda run --no-capture-output -n tour_de_gross python tools/audit_relay_adapter.py --output-dir evidence/phase11/export --cache-dir "$GROSS_DESIGN_CACHE_DIR"
```

E03 maps to joint/scoring and malformed/nonconvergence nodes, E04 to the
recurrence/candidate/prior node, E05 to scalar/native-batch/stream allocation,
and negative_tests to malformed/nonconvergence and parameter/profile/graph
nodes in `tests/test_relay_adapter.py`. Exact mappings are in the handoff.
