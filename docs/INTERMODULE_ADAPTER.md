# Phase 08: physical one-to-one code-code adapter

This independent gross construction implements the Fig. 13(b) geometry on two
explicit distinct module IDs. It does not establish paper-exact Figure 15 rates.
The pinned v1 PDF (SHA256 in `locks/paper-sources.json`) was inspected at Fig. 13,
A.4, A.5 and A.7/Table 6. No donor implementation is copied or modified.

`build_reference_lpu(a, 'inter_XX', b)` supplies the inherited signed graph.
`build_physical_inter(deformation, rounds=10)` retains each module's 18 half-LPU
edges and 11 physical bridge data qubits. Its active graph has 35 vertices,
58 edges and 20 selected cycles. The 11 degree-two zero-port vertices measure
X on corresponding bridge pairs. Ten six-edge Z cycles each contain a local
half-LPU path edge and two bridge qubits per module. Both families use Bell
checks with disjoint module-local support, one preparation CX, and two MX
outcomes whose XOR is the single algebraic check result. No triangular bridge
check is active, and no module's X1 is measured separately.

The two frozen BB rounds run simultaneously at the inherited offsets. The
staged schedule preserves collision and Eq. (67) ordering constraints. Native
controlled Paulis and the inherited initialization/split/ideal terminal policy
are explicit independent choices; their depth is not certified paper-exact.
Bell generation is a physical operation with joint faults, not an ideal MPP.
The local selected half's shared check uses its installed left measurement site;
the unused shared right site stays installed and inactive.

`adapter_connectivity(protocol)` records each physical qubit's module, all
cross-module check partitions and readout XORs, and separate active/installed
connectivity. The installed capability is two full LPUs (including inactive
halves and triangular checks) plus 22 new identifying measurement sites. Joint
cycle halves reuse installed bridge-square measurement sites. Thus 710 sites
are active and 778 installed; maximum installed degree is at most seven.
The protocol ledger distinguishes its allocated fragment register from installed
capability. Inactive sites have no live noisy intervals.

`build_benchmark((a,b), operation='inter_XX', deformation=df, rounds=10)` uses
`full_two_block_centralizer_K47`. A logical CX basis maps the designated X to
`a:X1*b:X1`, retains `b:X1`, and maps `b:Z1` to `a:Z1*b:Z1`. There are 24 X
and 23 Z action rows, each named, of exact GF(2) rank 47. Twenty-three ideal
reference qubits retain all remaining logical information. Only the joint
product is physically read out. MPPs belong exclusively to the ideal terminal
closure. The merged code dimension 23 is distinct from the 47-row action matrix.
`published_inter_K23` fails closed on O1; no arbitrary subset is supplied.

The C10 harness has explicit merge, repeat, split and final closure parities,
including both Bell records. Active and software split corrections are tested
with the same physical faults. The inherited catalogue keeps joint X/Z,
primitive multiplicities, admission masks and copy/group maps. Native CSC and
sparse-signature artifacts are exported with checksummed manifests. The
Table-6 population 743456 is only a comparison fingerprint, never fabricated
observations or a constraint for padding/dropping faults.

O1 published K23 rows, O2 historical Relay/prior policy, O3 exact serialized
schedule/boundaries, O4 published fault admission/multiplicity/merging, and O5
raw statistical grids/counts/bootstrap remain unresolved. These are not missing
definitions of this explicitly labelled independent construction. No distance
search, production Relay integration or Monte Carlo rate job is included.

Reproduce locally, sequentially, with `tour_de_gross` and `PYTHONPATH=$PWD/src`:

```bash
python -m pytest -xq tests/test_intermodule_adapter.py --durations=10
python tools/audit_intermodule_adapter.py --output-dir evidence/phase08/artifacts --cache-dir evidence/phase08/cache
```
