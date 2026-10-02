# Phase 09 physical gross shift

`circuits.shift`, `flows.shift` and `noise.shift` implement the named
`gross_B1_B0_x_plus_measure_prepare_v1` reconstruction. This is independent
construction, not a frozen Figure-15 circuit. O3 remains open. The original
source is arXiv:2506.03094v1 PDF §2.2, A.2 and A.7; the pinned paper digest is
in `locks/paper-sources.json`. No donor implementation was copied or modified.

The first transfer sends each L data site through its adjacent Z check along
B1, and each R data site through an X check along B0. The return paths use B0
and B1 respectively. Both operands are real installed qubits, and both transfer
stages consist of source-to-destination CX, destination-to-source CX, and
vacated-source Z measurement. All edges are checked against the BB Tanner
graph. The resulting support permutation is x, derived from physical routes
and compared with the existing target-to-source permutation oracle. There are
144 data and 144 check sites; no LPU or new transfer qubits are installed.

For destination state |b>, the two CXs give
`(|psi>, |b>) -> (|b>, X^b |psi>)`. The vacated-source measurement prepares
its site for reuse with a recorded X frame. Importantly, the second transfer
reuses the *output destination site's* first readout, which need not be the
input source site's readout. The intermediate data frame moves through the
check site, then the final data frame includes that reused-site bit. Transfer
detectors compare each vacated source with its destination's recorded initial
Z state. These are classical parities, not ideal SWAPs in the noisy body.

The sequence records instantaneous source/destination roles, intermediate
check-site data frames, final data X/Z frames, check-site Z states and the
physical-to-input-site permutation at every completed instruction. Z frames
are zero for the declared transfers; arbitrary untracked X/Z/Y physical faults
remain joint columns in the fault model. The following ordinary Fig.4b
syndrome cycle includes every inherited CNOT edge/order, with the reused
Z-ancilla bit and the data frame included in each readout parity. At each
repeat, the previous check is transported by the physical shift before it
is compared with the current check. Terminal logical readouts transport all
24 named input logical generators, with ideal references retained.

## Timing and explicit reconstruction choice

There is one initial, noisy check-site Z-preparation tick. Each instruction
then uses four transfer-CX ticks, two vacated-source measurement ticks, and
eight syndrome ticks: 14 body ticks. C10 therefore has **141 physical ticks**,
including initialization, rather than pretending the cold boundary is free.
Stage-2 Z measurements prepare the Z-check sites in their recorded Z state;
there is no Z reset at the start of the syndrome cycle. X checks use the
ordinary RX. The X-check terminal MX followed by R is explicitly an ordered,
one-tick cross-basis measure/prepare bundle, readying the check site for the
next transfer. Its readout and reset faults are separate locations. This
native bundle is a reconstruction timing assumption; its duration and noisy
lowering are part of O3, not established by the quoted paper accounting. A
device requiring two ticks for this bundle needs a differently named timing
profile and would not have this 14-tick body. No extra Clifford is hidden.

Every unoccupied live physical site gets the declared X/Y/Z idle channel,
including data held on check sites and vacated sites waiting for reuse.
Initial checks, transfers, both vacated readouts, syndrome readouts and the
cross-basis resets are noisy. Encoding, reference qubits, terminal stabilizer
MPP closure and logical/reference MPP readouts are explicitly ideal. All
three inherited noise profiles have strict, gauge-disabled DEM validation.
All primitive copies, admission maps, grouping and joint X/Z signatures are
preserved. Table-6 N is a comparison fingerprint, not a forced population.

`bench.rates.shift_rate` reports P_circuit/C. Tests use a synthetic probability
only to check normalization. No physical rate, decoder result, Monte Carlo,
distance lower bound or published-fit reproduction is produced in this phase.

## Validation and rerun

Small Choi transfer tests use both signs, Y correlations, nonzero destination
states and a changed reused-site readout, with independent signed propagation.
Material negative cases omit a reverse CX/frame or corrupt a flow offset.
The gross C10 test uses strict Stim DEM and raw reference-record signs. Every
transfer primitive receives a valid reverse-propagated signature; independent
forward/fixed-Stim checks use first/middle/last phase/gate/role strata with
IX, ZI, XX, YZ joint words, not exhaustive injection into the large circuit.
Unchanged small gate-template exhaustive oracles remain in the regression.

```bash
export PYTHONPATH="$PWD/src"
export GROSS_DESIGN_CACHE_DIR="$PWD/cache/faults"
conda run --no-capture-output -n tour_de_gross python -m pytest -q tests/test_physical_shifts.py tests/test_shifts.py
conda run --no-capture-output -n tour_de_gross python tools/audit_physical_shifts.py --output-dir evidence/phase09/export --cache-dir "$GROSS_DESIGN_CACHE_DIR"
```

O1 inter K23, O2 historical Relay/prior policy, O3 paper-exact representative,
timing/lowering/boundaries, O4 Table-6 population and O5 original statistical
data remain unresolved. The selected profile is explicit and fail-closed for
`paper_exact`; no phase10 two-gross physical construction is claimed here.
