# Phase 03 ideal measurement instrument

`surgery/protocol.py` implements an **ideal-only** state machine:
new -> prepared -> merged -> split -> complete. `prepare` initializes edge
qubits in |0>; `merge` measures signed vertex checks, selected cycle checks and
the dressed original checks; `repeat` adds a fresh set of absolute outcome IDs;
`split` measures edge Z and original-code checks; `finish` records the data
Pauli correction. The Stim lowering uses ideal MPPs and has no noise argument.
This is an instrument oracle, not the physical surgery circuit or an A.7
benchmark harness. The frame is tracked in software and is applied explicitly
by the validation tests.

The source is the pinned arXiv:2506.03094v1 PDF, Appendix A.4 steps 1--4
(PDF printed p. 51), with the phase-02 signed deformations. Original checks
and edge Z commute, so this oracle reads edges before the original checks.
Original check results before correction can be negative: the frame restores
their input +1 sector. Vertex outcomes in the first round are individually
random and are not detectors. Subsequent ideal rounds repeat their outcomes.
No record parity here is declared a physical detector.

## Signed branch derivation

Let B be the connected graph's vertex-edge incidence matrix over GF(2), and
let commuting Hermitian ports satisfy product_v P_v = L, including its sign.
The vertex checks are g_v = P_v X(B[v,:]). For vertex bits s and edge-Z bits z,
expanding their projectors gives

```
K(s,z) = <z| product_v [I + (-1)^s_v g_v]/2 |0>
       = 2^(-V) sum_{a: B^T a = z} (-1)^(s.a) product_v P_v^a_v.
```

If z is a cut, choose t satisfying B^T t=z with the root component zero.
Connectedness implies the only solutions are t and t+1. Hence, with
m=XOR_v s_v, Q=product_v P_v^t_v and Pi_m=(I+(-1)^m L)/2,

```
K(s,z) = 2^(1-V) (-1)^(s.t) Q Pi_m.
Q K(s,z) = 2^(1-V) (-1)^(s.t) Pi_m.
```

Because the ports commute and square to identity, Q^2=I including phase.
There are 2^(V-1) choices of s at fixed m and 2^(V-1) cuts, so summing corrected
branch density matrices gives exactly Pi_m rho Pi_m, with Born probability
Tr(Pi_m rho). The identity holds after tensoring an arbitrary reference system;
it preserves all coherence inside either measured eigenspace. Noncut z has a
zero Kraus map. Dressed and cycle projectors are initially +1 and commute with
all vertex checks on the input codespace; repeats do not change the instrument.
Omitted cycles follow the full signed deformed-group certificates, not an added
graph cycle basis in the reference LPU.

`surgery/frame.py` stores each t_v as a parity of named edge outcomes along an
explicit rooted spanning tree. Its serialized terms include vertex IDs, port
Paulis and outcome parities. Evaluation checks B^T t=z on **every** edge and
rejects a noncut readout. A different root can change Q by L, which acts as a
scalar on the projected state. Different tree paths agree when all cycle
parities vanish. This strict cut check is only an ideal oracle policy; a future
noisy frame must first incorporate the decoder's inferred faults.

Y is represented by its explicit XZ phase: Y=iXZ. Replacing Y by XZ is rejected
as non-Hermitian. Consistent changes to -Y still fail an oracle requesting +Y.

## Executed oracle scope

`validation/instrument.py` contracts numerical matrices of the exact signed
Pauli projectors directly, without using the cut-frame formula. Dense branch
contraction is bounded at eight total qubits; complex amplitudes are compared
with absolute tolerance 1e-12. Binary arithmetic and Pauli phases are exact.
Two-vertex tests exhaust all eight branches, including mixed Y/Z ports and a
negative target sign. Triangle tests exhaust all 64 candidate branches,
including 32 forbidden noncuts, for every root and all three spanning trees.
The identity-port dummy fixture exhausts all 32 branches for every root.
Repeated measurements and arbitrary complex and maximally entangled inputs
are checked. Missing-frame and sign-inversion tests distinguish the resulting
incorrect instruments even when logical outcome parity remains available.

`IdealBellCheck` names both physical X readouts and uses their XOR. Its tiny
matrix oracle actually prepares the Bell wavefunction, controls the disjoint
left and right data Paulis, and contracts both X readouts. All four branches
are checked on a maximally entangled data/reference state. No Bell schedule,
gate durations, physical noise or inter-module circuit is claimed.

The independently defined 18-qubit BB debug code uses its own logical X1,
six single-qubit ports, a ring graph with its **full** one-dimensional cycle
basis, and generic GF(2) dressing. It is not a scaled TdG LPU and has no X7
label. Exact stabilizer postselection exhausts all 2,048 allowed (s,z) branches
with two merged rounds, including original-check readouts and branch
probabilities. Four logical reference qubits make this a full encoded Choi
test. The probabilities sum to 1/2 for each target sign.

Gross X1 retains the prescribed half-LPU graph and selected cycles. Three
merged rounds are tested on + and - eigenstates with eleven preserved logical
Bell pairs, and on a full twelve-logical-qubit encoded Choi state with random
target outcome. Twelve deterministic seeds per input mode produce 36 bounded
ideal stabilizer trajectories. Every output is compared to direct projection
by the requested X1, including the reference and all edge states; all eleven
preserved logical pairs and original stabilizers are checked explicitly.
Every root is compared on each resulting branch. Gross's exponentially many
individual branches are not enumerated; the general branch identity above,
signed deformation certificates and these exact stabilizer checks supply the
construction validation. Gross XX/Y and inter XX instruments are outside the
required B04_X1 gate and are not claimed validated.

## Limits and provenance

All implementation is independently written. No external source was copied or
modified; Stim 1.16.0 is used through the phase-00 pinned public API. See
`locks/ideal-protocol-sources.json`. No reference fixture was changed.

O1 (inter K23 logical-action generators), O2 (historical Relay semantics and
priors), O3 (schedule, shift representative, lowering and boundaries), O4
(primitive multiplicities/admission), and O5 (original counts/grids/bootstrap)
remain open. None is required for this ideal instrument definition. Choosing
three gross rounds here is a validation fixture, not a reproduction of the
paper's C=10 noisy gross operation. Strict paper manifests remain blocked.

Run from the phase feature worktree in `tour_de_gross`:

```bash
conda run --no-capture-output -n tour_de_gross python -m pytest -q tests/test_ideal_protocol.py
conda run --no-capture-output -n tour_de_gross python tools/audit_ideal_protocol.py --output-dir evidence/phase03/oracles
```

Phase 04 physical check primitives require a separate controller-authorized
session. No noisy MPP, detector, distance or performance result is delivered
by phase 03.
