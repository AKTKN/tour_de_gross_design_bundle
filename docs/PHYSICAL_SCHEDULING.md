# Phase 04 physical construction

This phase implements physical signed single and Bell checks, the staggered BB
memory schedule, the Appendix A.5 staged coloring construction, and a complete
noiseless gross X1 prepare/merge/repeat/split body. It is an independent physical
construction, not a paper-exact noisy benchmark. Encoding and logical scoring
are separate harness responsibilities; no decoder or detector compiler is used.
The existing ideal protocol remains an independent oracle.

## Basis and location policy

`native_controlled_pauli_v1` treats RX, R, MX, M, CX, CY and CZ as native one-tick
operations. An X-basis single ancilla controls the literal X/Y/Z factor on each
data qubit, then is read in X. A negative Hermitian check inverts its physical
readout. The stored signed Pauli convention is i^phase X^x Z^z; CY measures Y,
including its phase, rather than performing X and Z measurements sequentially.

Pure BB Z checks use R, data-to-ancilla CX, M, matching the donor memory's CNOT
orientation. This is the same check instrument as the X-ancilla/CZ construction,
but it is a distinct physical basis policy and is recorded per check. Mixed
checks use the X-ancilla primitive. No free basis-conversion gates are inserted.
Unsupported changed basis/location policies fail when lowered. A changed policy,
operation, register or timing changes the schedule hash. Any future lowering or
idle change requires new location/noise fingerprints.

A Bell check has one algebraic ID and two distinct physical ancilla IDs. Its
support is partitioned without overlap. RX/R precedes a physical CX preparing
the Bell pair; that CX precedes every interaction on either half. Both ancillas
are read in X and the algebraic result is their XOR. A sign inversion is placed
on one readout. The shared installed in-module Bell pair preserves its fixed
BB couplers under ZX duality; its internal edge couplers follow the original
left/right auxiliary halves. No local half product is measured independently.

Ledgers record operations, symbolic readouts, live data and ancilla intervals,
candidate locations by gate kind and phase, active/installed counts and Bell
couplers separately. An idle is counted for each unoccupied tick of a live data
or prepared ancilla. Measured auxiliary edge data cease to be live after split;
unprepared check sites are not idles. There is no fault expansion or stochastic
noise emitted here. These counts are not O4 primitive multiplicities, compact
DEM sizes or Table-6 N. The original-check verification round is a separately
counted physical boundary, not an anonymous terminal logical harness.

## Memory convention and source extraction

The read-only adapter parses the pinned SlidingWindowDecoder builder AST for its
twelve CNOT-layer facts, checks its SHA256, and never imports/executes the donor
builder. `build_circuit.py` has no license notice or repository-level license;
no donor source is copied, patched or redistributed. The local code implements
the construction independently. Pinned attribution and license observations are
in `locks/physical-scheduling-sources.json` and `locks/source-lock.json`.

The donor accepts arbitrary A_list/B_list permutation matrices. This adapter
supplies literal monomial matrices in the paper's existing xy/LR convention,
with donor A1/A2/A3 and B1/B2/B3 corresponding to fixture term indices (2,0,1).
Figures 3 and 4 independently identify these as long-range/near/far edges. An
explicit identity target-to-source ConventionAdapter verifies the source Hx/Hz
against the target matrices before gates are translated. This does not assert a
map from the donor's separate default code factory or logical basis.

The literal Figure-4b schedule has Z gates at t=1,...,6, Z reset/read at 0/7,
X gates at t=2,...,7, X reset/read at 1/8. Repeating gates at offsets 8r yields
8C+1 ticks, including staggered reset/readout overlap between adjacent cycles.
Initialization of input encoded data and terminal logical readout are outside
that duration. The donor's H preparation, depolarizing channel, first/final
harness, detectors and decoder are not reused.

## Surgery schedule and constraints

The initial gate order is Bell preparation, LPU-check to BB-data, frozen BB gate
layers, internal LPU X coloring, internal LPU Z coloring, BB-check to LPU-data.
Each bipartite phase is optimally Delta-colored by regular multigraph completion
and perfect matchings; dummy coloring edges never become physical operations.
The selected reference cycles are preserved exactly. No ILP or added cycle
basis is used.

ASAP compaction preserves each physical qubit's staged order and every
anticommuting-overlap ordering. Seven BB anchors retain all original gate
relative offsets with a single Delta_BB. Resets occur as late as possible and
readouts as early as possible. Validators check collisions (65), Bell order (66),
the product of time differences in (67), support completeness, actual gate and
ancilla identity, signed readout and lifecycle. In these fixtures overlaps have
size two, so their check ordering must agree on both shared data qubits.

For gross X1, the coloring has 1/3/5/1 layers in its four unfrozen phases,
Delta_BB=1, and compacts to the paper's reported 12 ticks per deformed cycle.
The complete exported C=10 body counts 1 edge-initialization tick, 120 deformed
ticks, 1 split tick and 9 original-check verification ticks: 131 total. The
input/terminal logical harness contributes zero here because it is external.
Gross memory C=10 is separately 81 ticks. The deterministic coloring does not
reproduce a unique published serialization: gross XX/Y schedules are 13 ticks,
and two-gross X/XX/Y are 14/15/15 ticks under this choice. They are legal tested
schedule constructions, not claims of the published 12C duration for those
operations. Complete physical instrument validation is scoped to gross X1.

## Oracles and remaining limits

Exact signed Stim Clifford tableaus propagate physical readout products backward
and evaluate the initialized ancilla stabilizers. Tests validate every gross X1
check alone and in the simultaneously scheduled round. Dense Bell Choi tests
contract every physical branch of negative YZ, XX and ZY checks against the
independent projector. Tiny signed checks exhaust all two-qubit Pauli words and
both signs. Gross X1 tests prepare both target eigenstates and a full encoded
Choi input, execute two physical rounds and split, apply the symbolic frame,
and check a complete data/reference stabilizer basis. They use twelve bounded
noiseless stabilizer trajectories, not performance sampling. The negative
collision-free overlap schedule fails (67) and its exact tableau oracle.

Installed connectivity uses the union of X and ZX-dual Z port/dressing
couplers, including inactive ones and the Bell coupler. Figure-5 aggregate LPU
degree histograms match independently transcribed counts for gross and
two-gross: 90/158 LPU sites, maximum degree seven, degree five per Bell half.
This is physical connectivity, not just auxiliary graph degree.

O1 (published inter K23 generators), O2 (historical Relay semantics/prior/columns),
O3 (paper-exact coloring, shift representative, lowering and boundaries), O4
(primitive multiplicities and admission/merging), and O5 (original statistical
inputs) remain open. The local independent policy fixes what is needed to
construct this phase, without resolving strict paper equivalence. Shifts,
inter-module physical scheduling, detector compilation, fault models and noisy
benchmark observations are subsequent phases. No circuit-distance claim is made.
