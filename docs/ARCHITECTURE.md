# Architecture: generalized BB surgery to Stim and Relay-BP

Target: the **PDF version arXiv:2506.03094v1**, Appendix A.7 / Figure 15. PDF equation numbers are used throughout. This is a proposed software architecture, not an assertion that the physical simulator already exists. The delivered executable code is an independent algebraic reference audit.

## 1. Separate scientific objects

Use the installable `gross-design-bandle` distribution (import `gross_design_bandle`) with construction and validation modules under `src/gross_design_bandle/` and decoding, sampling and analysis under its separate `bench/` namespace. Construction modules must not import Relay, Sinter, pandas, plotting packages or a job scheduler. Both layers may depend on a shared, small schema layer. The package currently contains only a scaffold; the layers below are planned. Python is adequate for construction; sampled/decoded hot paths should use Stim and Relay's compiled implementations.

The dependency direction is:

`BBCodeSpec -> CodeData -> AuxiliaryGraph + PortMap -> DeformedCode -> CheckImplementation -> ScheduleIR -> CircuitFragment -> BenchmarkHarness -> FaultModel -> DecoderAdapter -> Sampler -> Analysis`.

These are different objects. In particular, an auxiliary graph vertex represents an algebraic check, whereas a Bell check uses two physical measurement qubits. Code dimension, number of logical-action observables, graph degree and physical connectivity degree have distinct fields.

## 2. Suggested tree

```text
src/gross_design_bandle/
  algebra/{gf2,pauli,logical_basis,certificates}.py
  codes/{bb,conventions,reference_profiles}.py
  surgery/{graph,ports,dressing,cycles,protocol,frame}.py
  lpu/{gross,two_gross,selection,code_code_adapter}.py
  circuits/{ir,check_primitives,bell_checks,memory,shift,schedule,emit_stim}.py
  flows/{records,stabilizer_flows,detectors,observables,boundaries}.py
  noise/{profiles,locations,uniform_expansion}.py
  validation/{algebra,instrument,schedule,connectivity,distance}.py
  integrations/{qldpc,sliding_window_donor}.py
src/gross_design_bandle/bench/
  {manifest,dem,columns,decoder,sampling,spectrum,fit,bootstrap,results,cli}.py
reference/     # immutable paper transcriptions, not decoder tuning data
configs/       # explicit reconstruction and extension profiles
artifacts/     # generated circuits, schedules, matrices, hashes
runs/          # append-only sampling chunks and manifests
```

## 3. Contracts

| Object | Required contents | Rejection conditions / invariants |
|---|---|---|
| `BBCodeSpec` | ell, m, A/B ordered terms, qubit/check indexing, source version | Invalid torus coordinates, unknown convention |
| `CodeData` | Hx, Hz, signed logical basis, physical labels, basis maps | Noncommuting checks; basis not symplectic; wrong rank |
| `AuxiliaryGraph` | stable vertex and **edge IDs**, incidence B, selected cycles C, embedding | Disconnected graph; cycles with BC^T != 0; duplicate IDs |
| `PortMap` | signed data Pauli P_v for each vertex; explicit block identity | Port product differs from requested signed L; noncommuting ports |
| `DeformedCode` | old-check dressing T, vertex/cycle checks, rank/span witnesses | BT^T != a; noncommutation; wrong logical loss; unjustified cycle omissions |
| `CheckImplementation` | one algebraic check, one or two measurement qubits, support partition, readout parity | Bell halves overlap data; a physical check is confused with an algebraic generator |
| `ScheduleIR` | operations by integer time, durations, qubit roles/lifetimes, gate provenance | Collision; violated anticommuting-overlap ordering; unmodelled active idle |
| `CircuitFragment` | Stim body, symbolic outcomes, input/output flows, frame update, gate/noise ledger | Hidden ideal logical measurement in noisy gadget; unresolved physical gate policy |
| `BenchmarkHarness` | ideal input/terminal operations, named logical-action rows, detector parities | Nondeterministic declared detector/observable; wrong measurement target |
| `FaultModel` | H, Lambda, probabilities, primitive fault provenance, expansion and admission maps | Column mismatch; lost correlations; unknown N convention |
| `RunManifest` | source commits, hashes, seed derivation, settings, observable/noise/schedule profiles | Unknown strict-profile fields; changed hash on resume |

`Lambda` is the logical-action matrix called A in Appendix A.7. Avoid reusing the name A for both a BB polynomial and a decoder matrix.

A proposed public API is:

```python
code = build_bb_code(profile="tdg_v1_gross")
lpu = build_reference_lpu(code, profile="tdg_v1")
operation = LogicalMeasurement(blocks=("block_0",), pauli="X1*X7")
deformation = compile_surgery(code, lpu, operation)
fragment = compile_physical_fragment(deformation, schedule_profile="tdg_v1_coloring")
experiment = attach_benchmark_harness(fragment, observable_profile="a7_single_block")
artifact = emit_stim(experiment, noise_profile="a7_uniform_expanded")
```

These function names are proposed local interfaces, **not existing upstream APIs**. Use explicit block IDs rather than Python object identity to distinguish in-module from inter-module operations.

## 4. Algebraic engine

Represent a Pauli as `(phase_mod_4, x_bits, z_bits)`, with a documented multiplication convention and Hermitian conversion. Use integer/GF(2) rank, never floating-point rank. For a logical L factorized into mutually commuting signed ports P_v on a connected graph G, form vertex checks `g_v = P_v X(B[v,:])`. For every original stabilizer s_j, set `a_j[v] = symp(s_j,P_v)` and solve `B t_j = a_j`. The dressed check is `s_j Z(t_j)`. Cycle checks are `Z(c_u)` with `B c_u = 0`.

For the paper fixtures, retain the short, prescribed dressing: an adjacent original check normally gains only one edge qubit. A spanning-tree path solution is useful for a generic oracle but can change check weights and the dependencies that justify the reduced cycle set. It must not silently replace the reference dressing.

The algebraic result must include a certificate of which logical constraint was added. For one independent measurement, the merged stabilizer code should encode k_in - 1 logical qubits. Rank alone is an initial check, not an instrument proof. Test the induced measurement and preservation of all remaining logical degrees of freedom separately.

## 5. Immutable reference profiles

`reference/gross.json` and `reference/two_gross.json` contain A/B, p/q/r/s, alpha/beta, added expansion edges, selected cycles, identified vertices and bridge ladders. Each field is tied to PDF Eqs. (27)--(64). These are intentionally richer than a pair of parity-check matrices.

The gross full graph has V=23, E=47 and 19 explicitly measured cycle checks; its graph cycle space has dimension 25. The two-gross full graph has V=39, E=81 and 37 measured cycle checks, versus cycle-space dimension 43. The omitted checks must be implied **in the combined deformed stabilizer group**, not by the selected graph cycles alone. A production certificate should export explicit GF(2) span witnesses and phase checks. Do not replace the selected set with an arbitrary minimum cycle basis when reproducing Figure 15.

Choose X1 as a construction control, then X1 X7 and Y1. A half-LPU accesses <X1,Z7> or <X7,Z1>; the latter two targets require the full LPU. Y1 is the Hermitian Pauli i X1 Z1. It is measured directly through mixed-Pauli checks, not by sequential X1 and Z1 measurements.

Two-gross uses weight-20 port representatives although d=18. It has two extra expansion edges per half and 17 bridge edges. Replacing the selected port by an arbitrary weight-18 representative invalidates the reference geometry.

## 6. Inter-module physical adapter

Implement the one-to-one Bell-check adapter in Fig. 13(b), not the alternative in Fig. 13(c). Each selected half-LPU retains its bridge data qubits. A new Bell-mediated X check couples each corresponding pair of bridge data qubits, and the square bridge-cycle checks are joined across the two modules through Bell measurements. The triangular bridge checks used for an in-module full LPU are absent in this inter-module construction.

An algebraic way to represent the X1 tensor X1 adapter is to subdivide each inter-half graph edge into two physical bridge edges, introducing a zero-data-port degree-two vertex. The associated vertex check is X on the two bridge data qubits. Neighboring ladders have a six-edge Z cycle (one half-LPU path edge and two physical bridge qubits on each module). This is one joint Z check implemented by Bell halves, not two independently measured local products. The delivered algebra audit uses this graph representation and verifies one logical loss for both code sizes; physical Bell partition/scheduling remains to implement.

For gross this algebraic inter graph has V=35,E=58 and 20 selected cycles. For two-gross it has V=57,E=98 and 38 selected cycles. These are **derived active-graph counts**, not the installed full-LPU census in Fig. 5.

## 7. Circuit layer and time

Compile one physical check using a verified controlled-Pauli primitive. A Bell check is prepared with one |+> and one |0> ancilla and a CNOT; each half controls its disjoint share of the check; both ancillas are measured in X and their XOR is the check result. CNOT/CZ/CY basis conversions must have an explicit timing/noise policy. An ideal local-Clifford equivalence does not automatically justify adding free physical layers to a reproduction circuit.

Use the paper's staged coloring construction: Bell preparation; LPU-check to BB-data gates; frozen BB memory schedule; internal LPU X and Z phases; BB-check to LPU-data gates; then legal ASAP compaction. Enforce no qubit collision and Eq. (67) for anticommuting overlaps. In these constructions overlaps have size zero or two. For size two, the order of the two checks must agree on both shared data qubits. Plain edge coloring does not enforce this by itself.

The baseline memory schedule has 8 C + 1 time steps with staggered X/Z resets/readouts. Reference deformed cycles use the graph-coloring schedule, quoted as 12 C time steps, with preparation, split and terminal conventions separately accounted for. Do not use an ILP-improved schedule under the same baseline label.

Implement a shift as two real transfers through check-qubit sites. Each transfer into a |0> destination uses two CNOTs, followed by measurement of the vacated source. Update state roles, measurement records and Pauli frames. The two transfer layers use four CNOT layers and two measurement layers; a following syndrome cycle gives the quoted 14-step instruction. A noiseless permutation is only a unit-test oracle.

## 8. Flows and detector compilation

Every measurement gets an absolute symbolic outcome ID. Bell checks map one algebraic check ID to two physical outcomes. Emit relative Stim `rec[-k]` references only at the final lowering pass. Store first-round, repeated-round, merge, split, final and transfer-measurement flow classes explicitly.

Repeated measurement of a stable check gives a familiar two-round parity. At a deformation boundary, the correct parity may involve old checks, dressed checks, cycle checks and edge Z measurements. Derive it by signed stabilizer propagation; do not join checks merely because their names match. Random first-round vertex outcomes are not detectors. Only proven deterministic combinations may become detectors.

The split frame is computed from graph-path parities of edge readouts, and composed with decoder frame updates and any shift permutation. Test different roots and spanning trees: the corrected instrument must agree, with a possible difference by the measured L that acts trivially on the projected state.

Use strict DEM extraction with `allow_gauge_detectors=False`. Do not make an incorrect detector pass by deleting it. Logical terminal measurements and ideal MPPs are allowed in the **explicitly ideal harness**, not as a substitute for physical noisy surgery.

## 9. Existing libraries

Current `qLDPC` has `qldpc.experimental.surgery.build_gadget`, `build_bridge`, `build_single_ppm_circuit` and `build_joint_ppm_circuit`. The reviewed circuit layer uses CSSCode, X/Z-basis gadgets and a measurement-oriented observable convention. Its README explicitly describes the API as unstable and not independently expert-reviewed. Reuse it behind an adapter and compare algebraic results; do not assume it implements the TdG fixed LPU, Bell adapter, Y circuit or Appendix-A.7 observable set. In particular, do not inherit `keep_only_observable(...,0)` into the multi-observable A.7 benchmark. Sinter supports multiple observables; an upstream comment claiming otherwise is not a benchmark requirement.

`SlidingWindowDecoder/src/build_circuit.py::build_circuit` provides a concrete BB CNOT schedule and Stim memory circuit. It uses a conventional depolarizing profile, basis-specific preparation/readout and optional both-sector detectors. Extract its schedule into an adapter; replace the initial/final harness and noise ledger. Its `use_both=True` does not by itself give the 24-observable logical-channel test. Sliding-window decoding is not part of the A.7 baseline.

`bicycle-architecture-compiler` is useful at the logical ISA/resource-estimation layer. Its README does not establish a physical Stim surgery generator. Keep it optional until physical instructions are validated.

`relay-bp` supplies the decoder backend. Bind it directly to the joint H and Lambda matrices and log all parameter semantics. Neither OSD nor a separate X/Z decoder is a silent fallback for the reproduction profile.
