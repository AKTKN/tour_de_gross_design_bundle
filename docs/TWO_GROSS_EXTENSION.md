# Two-gross physical profiles (phase 10)

`bench.two_gross.build_two_gross(name)` exercises the shared BB algebra,
physical check/schedule, ideal instrument, harness and joint noise generators
against unchanged `reference/two_gross.json`. No donor implementation was copied
or modified. Source attribution and frozen hashes are in
`locks/two-gross-extension-sources.json` and the inherited locks.

| Name | Operation | C | Logical rows | Reporting | Figure 15 |
| --- | --- | --- | --- | --- | --- |
| `two_gross_idle` | memory | 18 | K24 | P/C | published series reconstruction |
| `two_gross_shift` | physical x shift | 18 | K24 | P/C | published series reconstruction |
| `two_gross_X_C18_extension` | X1 | 18 | K23 | P | extension |
| `two_gross_XX_C18_extension` | X1 X7 | 18 | K23 | P | extension |
| `two_gross_Y_C18_extension` | direct Y1 | 18 | K23 | P | extension |
| `two_gross_inter_XX_C17_extension` | X1 tensor X1 | 17 | full K47 | P | extension |
| `two_gross_inter_XX_C18_extension` | X1 tensor X1 | 18 | full K47 | P | extension |

The chosen X1/X7/Z1/Z7 ports remain weight 20, despite the published code
distance 18. Each half retains 20 vertices, 32 edges, two expansion edges and
its selected cycles. The full LPU retains 39 vertices, 81 edges (17 bridge
edges), 37 selected cycles and 158 physical LPU sites. Omitted graph cycles
are certified in the combined signed deformed group. The inter graph has
57 vertices, 98 edges and 38 selected cycles; its adapter has 17 identifying
Bell checks and 16 joint six-edge cycle checks. Triangular checks are inactive.
The published inter K23 profile remains unavailable on O1.

The two-gross shift uses `two_gross_B1_B0_x_plus_measure_prepare_v1` with the
same verified B1/B0 Tanner routing as gross. The destination/source roles,
both real two-CNOT transfers, vacated-source readouts, carried frames and all
following syndrome gates are explicit. Memory has 8C+1=145 ticks; shift has
14C+1=253 ticks. The inherited one-tick MX/R bundle retains separate readout
and reset noise locations. This is an O3 reconstruction assumption, not a new
claim of paper-exact device timing. Surgery uses the inherited native
controlled-Pauli staged-coloring schedule with its actual tick ledger.

Large C17/C18 harnesses use strict Stim DEM with gauge disabled and raw
reference-record signs. Complete signed encoded-state witnesses cover +/−
targets, random outcomes and every preserved logical correlation. A complete
288-data Choi check validates shift routing outside the code space. Material
negatives cover separate-factor measurements, a missing Bell preparation,
wrong record offsets, cycle deletion, imaginary Y, wrong routing/profile/block
IDs and unresolved paper profiles. Large fault checks use bounded
phase/gate/role/first-middle-last strata with IX/ZI/XX/YZ joint words; earlier
small exhaustive primitive evidence is reused. They do not exhaust every
expanded copy. Every catalogue retains joint X/Z columns, multiplicities,
admission masks and grouping maps. Table-6 counts are comparison fixtures,
never generated observations or a reason to pad the population.

`validation.phenomenological.prepare_phenomenological_jobs` prepares A.8 Eq.
(84) input matrices. Spatial q rows form a complete 2k quotient basis of the
deformed code. Temporal M includes dressed old and selected cycle checks,
omits all vertex checks, and does not add L; temporal q is L. The objective is
sum(x OR z), so Y counts once. Each family declares a 120-second aggregate
wall cap, 10000 aggregate nodes, 5 seconds/1000 nodes per job, one worker and
zero retries. C17/C18 share the same intrinsic job inputs. Export saves native
binary arrays with hashes and a result contract requiring bounds, gap,
termination and independently checked witnesses. No solver backend, optimum,
lower bound or circuit-distance search is executed or certified. A candidate
witness supplies only an upper bound. In particular, this phase does not claim
all two-gross surgery has circuit distance 18.

Reproduce in `tour_de_gross` with `PYTHONPATH="$PWD/src"` and a writable
`GROSS_DESIGN_CACHE_DIR="$PWD/cache/faults"`:

```bash
conda run --no-capture-output -n tour_de_gross python -m pytest -q tests/test_two_gross_extension.py
conda run --no-capture-output -n tour_de_gross python tools/audit_two_gross_extension.py --output-dir evidence/phase10/export --cache-dir "$PWD/cache/faults"
```

The exporter writes compact native CSC/signature/map artifacts through
`bench.artifacts.export_fault_model`, verifies warm/p-change numerical reuse,
and hashes source and output artifacts. Tests/docs do not invalidate numerical
keys. The circuit/location ledger and relevant numerical implementation do.
No test pass is cached. The acceptance node IDs and actual timings/results are
recorded in STATUS and phase evidence.

For an unmodified public-builder model, large fault audits use
`validate_model=False`: cold construction already performed the full structural
checks, and warm reads verify every saved file hash and model identity. All
selected forward/Stim trials execute again. Standalone or mutated models retain
the default full revalidation. The numerical observations are saved under
`evidence/phase10/fault_checks/`; export verifies their model key and oracle
source hashes before packaging them, without using them to skip a test.

O1–O5 remain open: published inter rows; historical Relay semantics; exact
schedule/lowering/shift/boundary conventions; paper primitive population;
original statistical grids/counts/bootstrap data. These do not supply a
missing definition for the named independent constructions. Strict paper
mode remains blocked. No sampling or decoder integration belongs to phase 10.
