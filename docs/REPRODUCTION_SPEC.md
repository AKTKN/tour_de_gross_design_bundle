# Figure-15 reproduction contract

## Published targets

Freeze arXiv:2506.03094v1, PDF pp. 58--61, Tables 6--7. The eight series are transcribed in `reference/table6.csv`. The requested measurement representatives are in-module X1 X7, in-module Y1, and inter-module X1 tensor X1. Include X1 and idle as controls. Two-gross contributes idle and shift curves in Figure 15; two-gross surgery is a new benchmark extension, not an omitted published series.

For idle and shift, Appendix A.7 runs C=10 instructions for gross or C=18 for two-gross and reports circuit failure probability divided by C. For surgery the result is per operation; C denotes merged-code syndrome rounds, not a divisor. The published gross surgery uses C=10. Two-gross in-module uses C=18. For two-gross inter-module, use C=17 as the initial distance-bound-matched **extension** profile and optionally compare C=18; explicitly label both choices because Figure 15 supplies no such curve.

## Noise contract

The baseline is the paper's linearized independent Pauli circuit model and, for failure-spectrum sampling, its equal-q expansion with q=p/15. Preparations/readouts have flip probability p, and each idle Pauli has probability p/3. Each nonidentity two-qubit Pauli fault has probability p/15. In the equal-q expansion, an mp/15 event is replaced by m independent copies. This replacement agrees at first order, not exactly at finite p.

Use three named profiles rather than one overloaded parameter:

* `a7_uniform_expanded`: the intended figure reproduction model.
* `paper_linearized_unequal`: independent p, p/3 and p/15 primitives before equalization, for model comparison.
* `standard_categorical_depolarizing`: ordinary Stim DEPOLARIZE1/2, an explicitly different comparison.

For equal-q emission, independent `CORRELATED_ERROR(q)` Pauli terms or repeated single-Pauli error instructions can retain independence. Do not use `ELSE_CORRELATED_ERROR` for independent terms. Fifteen mutually exclusive branches in DEPOLARIZE2 are a different channel from fifteen independent Bernoulli faults.

Maintain a full physical location catalogue and a separately versioned A.7 sampling catalogue. Record the admission policy for faults with both zero detector and zero logical signature. Including or excluding such faults leaves unconditional channel statistics unchanged but changes N and the conditioned spectrum f(w). Preserve multiplicities and establish which catalogue matches Table 6. A compact Stim DEM is not an unambiguous catalogue: it can merge equivalent mechanisms and omit ineffective terms. Compare both H and Lambda when grouping columns. Never force N to match by padding with dummy faults.

The raw quantum circuit gate policy, treatment of active idles, Bell preparation errors, non-CNOT controlled-Pauli lowering, and boundary locations must be represented in the ledger. Match every discrepancy in N to these explicit decisions.

## Observable contract

A.7 jointly decodes X/Z effects. Its H has detector rows and primitive-fault columns; its A (called Lambda here) contains logical-action rows. Single-block unitary benchmarks have K=24. The stated centralizer construction for one measured logical Pauli on a 12-logical-qubit block gives K=23.

Construct and name the logical-action generators, not merely K anonymous bits. The ideal harness should prepare the relevant encoded Bell/reference states, with a logical Clifford basis change when needed to put the requested Pauli in the designated measured slot. First/last readout conventions and frame contributions must be stored. Test a full noiseless measurement instrument separately from this scoring convention.

**Open specification item O1:** Table 6 prints K=23 for gross inter-module X1 tensor X1. Applying the same centralizer prescription to two complete 12-logical-qubit blocks gives 2*24-1=47 independent Pauli labels. The text reviewed here does not identify a 23-row inter-module subset that resolves this discrepancy. Store the published K=23 in reference data without treating it as an implemented observable profile. Support a full-two-block-centralizer K=47 validation profile, but label it non-equivalent to the table until original observable definitions or author clarification are available. Do not simply drop 24 rows or change the published fit's K to 47. The delivered algebra audit's merged k=23 is a **code dimension**, not a justification for a 23-row action matrix.

## Relay contract

Table 7 is retained verbatim as numerical data in `reference/relay_table7.json`. At the reviewed current commit, public examples use `gamma0`, `pre_iter`, `num_sets`, `set_max_iter`, `gamma_dist_interval`, `stop_nconv`, and `RelayDecoderF32`. The paper uses an earlier set of names including `gamma`, `rng_width`, `ewainit_discount_factor`, `set_num_iters`, `max_iter`, and `ms_scaling_factor`.

**Open item O2:** map old and current recurrences, initialization, iteration caps, random-strength distributions and candidate selection by inspecting the implementation/history. Similar names do not establish equal algorithms. If the historical backend cannot be reconstructed, publish a current-Relay replication with its own label. Candidate parameters and any guessed gamma transformation stay outside strict manifests until verified by source or trace equivalence.

Fix and log the decoder's prior policy for f(w). Changing priors with p, conditioning on the true sampled weight, retuning settings, or changing stochastic decoder randomness changes the decoding function. With a p-dependent decoder the exact identity uses f(w;p), not one universal f(w). Uniform-prior scaling invariance may simplify min-sum, but establish it for the chosen implementation and precision instead of assuming it.

## Sampling and analysis

For e in {0,1}^N, sigma=H e and lambda=Lambda e. Require syndrome consistency H c=sigma, then compare Lambda c with lambda. Keep a separate nonconvergence count and a documented rule for its contribution to total failures. Never silently discard undecoded shots. An OSD comparison is a separate decoder profile.

Direct sampling draws independent Bernoulli(q) bits or uses an equivalent validated Stim circuit. Fixed-weight sampling selects exactly w distinct indices uniformly from the **same** catalogue. Sampling with replacement changes the experiment. Store failure count, shot count, residual-syndrome failures, observable-bit failures and decoder timing/iterations per batch.

Use the published ansatz (natural logarithm in Table 6):

`a = 1 - 2**(-K)`

`f(w) = 0 for w < w0`

`f(w) = a * (1 - exp(-(exp(log_f0)/a)*(w/w0)**gamma_fit)) otherwise`.

Then P(p) = sum_w Binomial(N,w) (p/15)^w (1-p/15)^(N-w) f(w), followed by the series-specific divisor. Published w0 is 5 for gross and 9 for two-gross. These are fit assumptions associated with circuit-distance estimates, not a proven minimum failing weight of Relay. Retain and report failures below w0; do not erase them to enforce the fit.

Fit only with the stated selection rule: for gross Y exclude w>80 from the published-style fit but preserve/display those data. Use chi-squared fitting and binomial bootstrap for paper compatibility, recording the exact variance prescription and treatment of zero counts. A binomial-likelihood fit is a useful separately labeled robustness analysis. The published shaded bands are the standard deviation of the bootstrap predictions, not generic 95% confidence intervals. Reconstructing these bands requires trial counts/raw data; Table 6 alone gives neither the data points nor the published uncertainty bands.

`tools/reconstruct_fits.py` evaluates the rounded published central-fit parameters and writes CSV. It is an analysis reference, **not Monte Carlo replication**, and should never be used to fabricate observed points. It includes a numerical binomial-tail bound, not a confidence interval.

## Remaining reconstruction items

O3: the concrete scheduling/coloring choices, initial/terminal boundary lowering and chosen shift representative must be fixed. The paper describes how to construct valid circuits but does not make the reviewed high-level text a unique serialized noisy circuit.

O4: recover the exact primitive-fault population and any column merging/zero-column admission policy. N is a necessary fingerprint, not a sufficient circuit equivalence test.

O5: obtain original shot counts, weight/p grids, seeds, fitted-data selection details and bootstrap settings for point-and-band replication. Until then, run an independently sampled and clearly labeled statistical replication.

These open items prevent claiming exact Figure-15 equivalence; they do not prevent implementing and testing the construction or generating new valid circuit benchmarks.
