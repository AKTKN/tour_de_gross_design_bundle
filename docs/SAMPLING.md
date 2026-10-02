# Phase 12 sampling and analysis

The sampler addresses `FaultModel.admitted_to_copy` columns. A fixed-weight draw
chooses `w` distinct admitted copies uniformly; a Bernoulli draw tests every
admitted copy independently at `q=p/15`. Both use the same joint `H` and
`Lambda`, so Y and other correlated detector/logical effects remain one
primitive. CSC columns are XORed into detector and logical rows per chunk.
Relay's sequential compiled `decode_detailed_batch` is used through the
phase-11 adapter. The sampler permits one decoder thread; no parallel Relay
entry point or worker pool is called. Fixed input priors are recorded in the
decoder manifest and never updated from sampling `p` or `w`.

`run_manifest` hashes the physical circuit, locations/raw catalogue, maps,
joint matrices, decoder provenance/settings and sampler implementation. Each
fault and decoder stream is derived from the run hash, series, mode, point and
chunk. The decoder stream gives stable per-shot IDs. Result chunks are
append-only checksummed JSONL; a repeated identical chunk is skipped and a
conflicting duplicate is rejected. Incomplete or corrupted chunks fail read.
The run manifest must be retained next to chunks. A resume must first read
existing chunks and count their shots/points against the pilot budget.

Each chunk stores every sampled weight, each shot's failure flags, aggregate
overlapping failure counters, iteration counts and decoder time. Consequently
observed failures below a fit threshold and gross-Y weights above 80 remain
in the spectrum. A zero-failure stratum reports a one-sided exact binomial
upper bound, not a zero true rate. Failed decoder returns and nonconvergence
count as circuit failures.

`point_summaries` aggregates the overlapping per-chunk counters and reports
failure and nonconvergence rates. For extrapolation checks,
`evaluate_holdout` takes an explicitly declared p grid and independent direct
Bernoulli counts. Freeze the grid before collecting holdout data; the function
rejects missing, duplicate or changed points and never refits on holdout
counts. The tiny Bell pilot contains no holdout comparison.

The Table-6-shaped ansatz and binomial integration are numerical models applied
to independent observed counts. The integration returns an absolute omitted
tail bound and a series divisor. The `gross_Y` weight-above-80 exclusion is
applied only to published-style fitting. The chi-squared fit uses an explicitly
documented Jeffreys-smoothed variance to keep zero counts, since the original
paper's exact variance prescription and raw data are O5. A separately labeled
binomial-likelihood fit and binomial bootstrap are available. Bootstrap bands
are standard deviations of predicted rates. Neither fit imports Table-6
printed parameters as observations or certifies tiny extrapolated rates.

`tools/audit_sampling.py` is a 3-point, 32-shot-per-point tiny Bell smoke pilot,
with a 120-second cap, explicit cache, native fault export and immutable result
records. It is not Figure-15 performance evidence. The standalone tool is
deliberately bounded; a full statistical campaign belongs to phase 13 and
requires separate authorization. O1--O5 remain open for paper equivalence.

F03 acceptance uses exhaustive tiny-catalogue enumeration for the Bernoulli and
fixed-weight mixture identity. It also uses fixed zero and nonzero admitted
error vectors on a physical gross idle model to check joint H/Lambda evaluation
and compiled Relay batch decoding. These vectors are deterministic integration
checks, not a gross rate estimate. The existing tiny Bell pilot cannot establish
agreement of two gross estimators. That statistical comparison is deferred to a
separately budgeted job with a prespecified stopping rule, failure counts and
an explicit inconclusive outcome when precision is inadequate.
