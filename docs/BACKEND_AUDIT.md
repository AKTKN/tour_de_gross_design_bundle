# Phase 00: source and backend capability audit

Audit date: 2026-10-02. Target: [arXiv:2506.03094v1 PDF](https://arxiv.org/pdf/2506.03094v1), Appendix A.7, Figure 15, Tables 6–7. Equation numbering below explicitly identifies which PDF it belongs to. This phase establishes source provenance, imports and declaration rejection. It does not validate any physical gross circuit, distance, decoder equivalence or simulated rate.

Worktree: `/home/quantum_teresheys/workspace/tour_de_gross_design_bundle/.codex-pipeline/tour-de-gross/worktrees/00_source_audit`; branch: `feature/00_source_audit`. Main remains controller-owned. External checkouts are unmodified, detached, under `/home/quantum_teresheys/workspace/tour_de_gross_design_bundle/external_libs`. No external fork was needed because no source changes or donor code copying occurred. Building/installing unmodified sources generated artifacts in `/tmp`, not source patches.

## Verified provenance and licenses

`locks/source-lock.json` records exact commits, tree IDs, Git blob IDs, SHA-256 hashes, byte counts and inspected license paths. All five blob IDs originally supplied in `reference/sources.json` agree with their pinned commits and the checkout bytes. The lock additionally covers inspected API, build, license and Relay-history files. `tools/audit_sources.py` verifies these offline, with Git network protocols disabled; it never fetches or imports a backend. Reference fixtures were preserved.

| Source | Locked commit | License evidence and phase use |
|---|---|---|
| [qLDPC](https://github.com/qLDPCOrg/qLDPC/tree/60fc2cf465e880d6e64afacc933d33455d787bf4) | `60fc2cf465e880d6e64afacc933d33455d787bf4` | Apache-2.0, `LICENSE` and `COPYRIGHT`; installed unmodified source, imports and negative basis test executed |
| [SlidingWindowDecoder](https://github.com/gongaa/SlidingWindowDecoder/tree/05d6b1f478f2b044effdc7477278647dfb99db07) | `05d6b1f478f2b044effdc7477278647dfb99db07` | No repository-level license or license notice in `src/build_circuit.py`. `src/utils.py` has NVIDIA Apache-2.0 attribution; `src/include/COPYRIGHT` grants Radford Neal permissive reuse with notice/changes retained and mentions GNU routines. These notices do not establish a license for the memory builder. Imported for signature inspection only; do not copy it pending clarification |
| [Relay](https://github.com/trmue/relay/tree/d185194ba0cb4101ced4340d82b2ee6d42f225f0) | `d185194ba0cb4101ced4340d82b2ee6d42f225f0` | Apache-2.0, `LICENSE.txt` and IBM source headers; built unmodified with pinned `Cargo.lock`, imported and tiny deterministic decode executed |
| [Bicycle architecture compiler](https://github.com/qiskit-community/bicycle-architecture-compiler/tree/c99eb046f10b38de2412468ccded14ca38f1ee4c) | `c99eb046f10b38de2412468ccded14ca38f1ee4c` | Apache-2.0, `LICENSE`; source inspected only, Rust compiler and optional gridsynth **not built/tested** |

## Environment actually exercised

Reused Conda `tour_de_gross`: CPython 3.11.17, NumPy 2.4.6 and SciPy 1.17.1. Before installation, pip dry-run resolved the pinned qLDPC requirements without replacing these existing versions. qLDPC requires Python >=3.11, SciPy >=1.14.1, Stim/Sinter >=1.16; this environment meets those requirements. Relay requires Python >=3.8 and NumPy/SciPy. Installed Stim 1.16.0, Sinter 1.16.0, qLDPC 0.4.0 from its source commit, and Relay 0.2.2 built from its source commit. Relay's version string alone is insufficient: this commit follows the 0.2.2 release and includes SIMD and syndrome-pruning changes.

`locks/environment-lock.json` contains every observed installed distribution version and SHA-256 hashes of installed backend Python/binary files. `locks/requirements-phase00.txt` pins third-party packages, excluding the editable project and the two source backends; install those from the commit lock. `locks/conda-phase00-linux-64.explicit.txt` freezes the Conda layer. `locks/package-artifacts.json` records pip artifact URLs/hashes, the locally built wheel hash and Rust/Cargo versions. `locks/paper-sources.json` hashes both inspected v1 PDFs; PDFs are not redistributed. The earlier audit-only locks remain intact. Pip check passed. These locks certify an observed import environment, not a validated reproduction stack.

## Actual API surface and limitations

Signatures are captured by executing imports in `evidence/phase00/backend-imports.json`. Python annotation strings are omitted below for readability; keyword-only markers and defaults are retained.

```python
from qldpc.experimental.surgery import (
    build_gadget, build_bridge, build_single_ppm_circuit,
    build_joint_ppm_circuit, logical_state_init, keep_only_observable,
)
build_gadget(code, x, *, basis)
build_bridge(g_l, g_r, *, port_subset_l=None, port_subset_r=None,
             spanning_tree_root_l=0, spanning_tree_root_r=0,
             cellulate_max_len=None)
build_single_ppm_circuit(gadget, *, rounds, noise_model=None, data_init=None)
build_joint_ppm_circuit(g_l, g_r, bridge, *, rounds, noise_model=None, data_init=None)
logical_state_init(code, state, *, log_idx)
keep_only_observable(circuit, keep_idx)
```

The [gadget implementation](https://github.com/qLDPCOrg/qLDPC/blob/60fc2cf465e880d6e64afacc933d33455d787bf4/src/qldpc/experimental/surgery/gadget.py) accepts qubit stabilizer CSS codes and X/Z support vectors. The negative test executes rejection of `basis="Y"`. The bridge requires matching bases. These are generic gadgets/bridges; their existence does not establish the selected TdG LPU cycles, signed mixed-Pauli Y instrument, Bell-check adapter or noisy shift.

The [circuit implementation](https://github.com/qLDPCOrg/qLDPC/blob/60fc2cf465e880d6e64afacc933d33455d787bf4/src/qldpc/experimental/surgery/circuit.py) returns a Stim circuit for single PPM and `(circuit, CSSCode)` for joint PPM. Its two observables are a last-QEC-round PPM readout and a destructive support readout cross-check. Documentation recommends retaining only observable 0 for LER. This is incompatible with assuming the A.7 K24/K23/K47 logical-action harness. Joint public API chooses shared/disjoint blocks using code object identity; the local design requires explicit block IDs. The upstream statement that Sinter expects exactly one observable is not adopted as a local benchmark constraint. The [experimental warning](https://github.com/qLDPCOrg/qLDPC/blob/60fc2cf465e880d6e64afacc933d33455d787bf4/experiments/lattice_surgery/README.md) requires independent validation. No donor surgery circuit was generated in this phase.

SlidingWindowDecoder is not an installed Python distribution. Its exact file API is imported by file location:

```python
# external_libs/SlidingWindowDecoder/src/build_circuit.py
build_circuit(code, A_list, B_list, p, num_repeat,
              z_basis=True, use_both=False, HZH=False)
```

It expects the donor's code fields (including `N` and logical supports), three A and three B permutation matrices, and emits a Stim memory circuit. Inspection shows seven CNOT interaction slots, then staggered X-check readout/reset, with Z-check readout/reset in slot 7; basis-dependent preparation/readout, optional both-sector detectors, and conventional `DEPOLARIZE1/2`. X interactions traverse A2, B2, B1, B3, A1, A3, while Z interactions traverse A1-transpose, A3-transpose, B1-transpose, B2-transpose, B3-transpose, A2-transpose. This is a schedule donor candidate, not evidence of a mapped convention, joint A.7 channel harness, independent equal-q catalogue or validated 8C+1 local circuit. The builder was imported but **not called**.

```python
from relay_bp import RelayDecoderF32, ObservableDecoderRunner
RelayDecoderF32(check_matrix, error_priors, alpha=None,
    alpha_iteration_scaling_factor=1.0, gamma0=0.1,
    data_scale_value=None, max_data_value=None,
    pre_iter=80, num_sets=300, set_max_iter=60,
    gamma_dist_interval=(-0.24, 0.66), explicit_gammas=None,
    stop_nconv=1, stopping_criterion="nconv", logging=False, seed=0)
decoder.decode(detectors)
decoder.decode_detailed(detectors)
decoder.decode_batch(detectors)
ObservableDecoderRunner(decoder, observable_error_matrix,
                        include_decode_result=False)
```

PyO3 inspection displays `Ellipsis` for the tuple/string defaults; the defaults above are from the locked Rust binding. `decode_detailed` exposes `decoding`, `decoded_detectors`, `posterior_ratios`, `success`, `iterations`, `max_iter`, and quality information. Sparse H and a separate observable-error matrix can preserve joint fault columns. This does not validate a local production adapter, priors, grouping or nonconvergence policy. The README's `RelayDecoderF32.par_decode_batch` **does not exist**. The actual `decode_batch` signature has no parallel flag; `ObservableDecoderRunner` has separate batch methods with `parallel`, `progress_bar` and `leave_progress_bar_on_finish`. Only imports/signatures and a 2x3 syndrome test with explicit gammas, at most 12 BP iterations per call, were exercised. No F64/integer/fixed-point decoder, batch equivalence, optional beliefmatching/Stim Relay integration or historical decoder was tested.

Stim's executed scope is import plus tiny deterministic/invalid-detector DEM checks with `allow_gauge_detectors=False`. No sampling was performed. The compiler README describes logical PBC-to-ISA compilation and additive resource/error estimation; it supplies no established physical Stim generator API.

## Historical update equations and Table-7 mapping

TdG Table 7 itself supplies parameter values, not update equations. Its cited [Relay paper v1 PDF](https://arxiv.org/pdf/2506.01779v1), pp. 2–3 Eqs. (1)–(4) and p. 8 Algorithm 1, supplies the following mathematical recurrence (this is **Relay PDF numbering**, not TdG numbering). Put `ell_j = log((1-p_j)/p_j)`:

```text
mu_(i->j)(t) = (-1)^sigma_i product_(j' != j) sign(nu_(j'->i)(t-1))
               * min_(j' != j) abs(nu_(j'->i)(t-1))
b_j(t)       = (1-gamma_j)*ell_j + gamma_j*M_j(t-1)
nu_(j->i)(t) = b_j(t) + sum_(i' != i) mu_(i'->j)(t)
M_j(t)       = b_j(t) + sum_i mu_(i->j)(t)
```

The paper initializes messages/biases to prior log odds; the first leg's marginals start at those odds, later legs retain preceding final marginals. A converged candidate satisfies Hc=sigma; selection minimizes sum(c_j*ell_j) among converged candidates and stops after S solutions or the leg cap. This recovers an algorithm family, not the exact meaning of every historical Table-7 key.

Current `crates/relay_bp/src/bp/min_sum.rs` implements the same prior/posterior interpolation form, with memory strengths selected by `gamma0` then per-variable gammas. It adds a check-message scaling `alpha`, defaulting to an iteration ramp `1 - 2^(-iteration/alpha_iteration_scaling_factor)`; explicit `alpha=1` removes that ramp. Current hard decisions use posterior <=0 as bit 1, including zero. The code clears check messages, initializes variable messages to priors, resets ordered memory at each decode, carries posteriors between legs, and samples `Uniform::new(low, high)` with seeded StdRng unless explicit gammas are supplied. Current Relay caps are `pre_iter + num_sets*set_max_iter`; convergence counts include the initial leg. No guessed gamma/rng-width transformation is applied.

The first public code release `1290a2cae83a5f8a16dca09456681159288b8dd6` is dated 2025-07-28, after the June v1 papers. History inspection found posterior-reset fix `1b41b689ad27128274fc7d0bb93c6ed50135c507` (2025-09-19) and memory-reset fix `3f9a80109343f07155598596973f5e98a34dbd5a` (2025-09-25). Relevant historical blobs are locked. Historical numerical parameter names also occur in notebook history, but no executable old-key recurrence was established. The current binding rejects `ewainit_discount_factor`. In particular, the meaning of the historical 0.875 discount relative to the separate Table-7 gamma/rng_width, the extra `max_iter`, exact prior/column policy, and trace equivalence remain unresolved. O2 stays open.

## Public physical-circuit/data search and open items

Inspected the canonical TdG v1 PDF and arXiv abstract/HTML release links, searched for the paper's public code/data, inspected the pinned compiler README/tree and Relay testdata inventory. The public [compiler releases](https://github.com/qiskit-community/bicycle-architecture-compiler/releases) identify the paper's logical compiler, which does not establish an original Figure-15 physical-circuit/data release. The cited Relay paper links `trmue/relay`; its pinned testdata contains BB memory X/Z/Choi-XZ circuits and surface/color memory circuits. The filename inventory is saved in `evidence/phase00/relay-circuit-inventory.json`; these stored circuits were not executed. No original Figure-15 surgery/shift circuit archive, trial counts or bootstrap data was established in this bounded search. This is not a claim that no such release exists.

| Item | State after phase 00 | Evidence needed to resolve |
|---|---|---|
| O1 | Open | Named published inter K23 logical-action rows; full-two-block K47 is a separate independent profile |
| O2 | Open, partial recurrence recovered | Exact historical parameter semantics and executable/trace equivalence, priors and column policy |
| O3 | Open | Concrete coloring, shift representative, lowering and noisy/ideal boundary choices or original circuits |
| O4 | Open | Original primitive multiplicities, zero/zero admission and merging policy producing Table-6 N |
| O5 | Open | Original grids, shots/failures, fitting variance and bootstrap settings/data |

No current-phase source definition is assumed resolved. The license question prevents copying the SlidingWindowDecoder builder; independently deriving the schedule from the paper remains possible. O1–O5 block strict paper-equivalent sampling but do not block phase 01 independent algebra work.

## Manifest policy and executed validation

`gross_design_bandle.bench.manifest.validate_manifest` is a phase-00 declaration validator. It accepts `schema_version=1, mode="algebra_only"` with omitted/null benchmark sections. It rejects unknown top-level and section fields, unknown versions/modes, fabricated O1–O5 resolution, and every `paper_exact` request while definitions remain open. Algebra mode cannot certify arbitrary physical/decoder profiles either. Later phases must extend the schema with independently validated definitions; passing this validator is not authorization to sample.

Acceptance tests are in `tests/test_source_audit.py`, `tests/test_backends.py`, `tests/test_manifest.py`; the delivered nine tests remain in `tests/test_reference.py`. Exact gate-to-node mapping is supplied in the phase completion JSON. Evidence and commands are recorded in STATUS. The initial API probe failed on the nonexistent README batch method; the first test run consequently lacked its generated environment lock (1 failed, 34 passed). The probe and negative API test were corrected, then required validation rerun. No failed run is counted as a pass.

To revalidate this worktree with the existing environment/checkouts:

```bash
conda run --no-capture-output -n tour_de_gross python tools/audit_sources.py --output evidence/phase00/source-verification.json
conda run --no-capture-output -n tour_de_gross python tools/audit_backends.py --output evidence/phase00/backend-imports.json
conda run --no-capture-output -n tour_de_gross python -m pytest -q tests/test_backends.py tests/test_source_audit.py tests/test_manifest.py tests/test_reference.py tests/test_pipeline.py
conda run --no-capture-output -n tour_de_gross python -m pip check
```

On another machine, create the Conda layer from its explicit lock, install `locks/requirements-phase00.txt`, fetch the four commit-pinned checkouts to the canonical external directory (or set `TOUR_DE_GROSS_EXTERNAL_LIBS`), install qLDPC from that unmodified checkout, build/install Relay using `maturin build --release --locked` and its pinned Cargo manifest, then install this project editable. Generated backend binary hashes are platform/build specific: the environment lock describes this observed machine; regenerate and review a distinct lock for another build. Do not install registry qLDPC/Relay versions as replacements for the commit lock. No optional compiler, gridsynth, GAP or upstream experiment is part of the acceptance command.
