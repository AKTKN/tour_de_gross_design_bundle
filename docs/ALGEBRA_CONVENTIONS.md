# Phase 01 algebra and convention contract

The implemented layer is exact GF(2), signed Pauli algebra, BB code data and
physical-support translation on the logical quotient. Physical shifts, surgery,
schedules, detector compilation and production sampling remain future work.

`algebra/pauli.py` stores `i**phase X**x Z**z` in an ordered register of immutable
qubit IDs. Thus `XZ=-iY` and `Y=iXZ`. Hermiticity requires
`phase-sum(x*z)` to be even. Multiplication includes the `2*z_left*x_right`
phase. Clifford conjugation acts on the signed X/Z generators in order. Register
mismatches and imaginary-phase measurement checks raise `ValueError`.
Dense one-/two-qubit matrices independently verify all products, commutation,
daggers, and the supported local and two-qubit Clifford conjugations.

`algebra/gf2.py` accepts binary integer arrays, without rounding or coercing
nonbinary values modulo two. It provides RREF, rank, row/kernel bases, solve,
inverse and checked span coefficients. Tests independently enumerate all 2x3
maps and RHS vectors. These are exact algebra checks, not distance assertions.

`codes/bb.py` orders columns `(L/R, i, j)` with `i*m+j` within each side.
X check `(i,j)` has support `+(A,B)` and Z has support `-(B,A)`.
Equivalently `Hx=[A,B]`, `Hz=[B.T,A.T]` over GF(2).
Torus exponents are integers reduced modulo ell/m; duplicate terms after
reduction are rejected. Terms retain source order. Code matrices must match
the declared polynomial/convention exactly. Signed logicals must commute with
checks and have the canonical pairing. Check and qubit names include a caller
supplied block ID. Spec/code/adapter IDs are SHA-256 of canonical JSON;
code IDs include the block and signed basis. Frozen dataclasses, tuple fields
and bytes-backed arrays prevent mutation of identity-bearing data.

`codes/reference_profiles.py` reads the unchanged delivered fixture bytes and
checks their delivered SHA-256 hashes before use. TdG v1 PDF Eq. (27) specifies
the polynomials; Eqs. (31)--(33) give the four base logicals and duality shift;
Eqs. (34)--(36) give all twelve pairs. The delivered transcriptions and
`tools/audit_reference.py` remain independent of the new implementation.
The small debug fixture has ell=m=3, A=1+x+y, B=1+x^2+y^2 and n=18.
Its checked ranks are 7/7, hence k=4. Its logicals come from the centralizer
quotient and are paired by an exact inverse; labels 1--4 are local labels.
It has no X7, geometric LPU, measured instrument or claimed distance.

`codes/conventions.py` uses explicit **target-to-source** permutations, separately
for data columns, X rows and Z rows. It verifies both donor matrices entry by
entry against the declared target. Parameters, rank or row-span agreement
alone do not pass. qLDPC's actual BBCode matrices are tested for both insertion
orders of its orders dictionary: `{x:ell,y:m}` and `{y:m,x:ell}`. The latter
uses source cell `j*ell+i` and has nonidentity data/check permutations.
Tests also exercise independently shuffled X/Z rows and signed Pauli conversion.
No donor code was copied or modified. Source provenance and inspected license
hashes are recorded in `locks/algebra-sources.json`; phase-00 backend pins remain
in `locks/source-lock.json` and `locks/environment-lock.json`. The unlicensed
SlidingWindowDecoder implementation is not imported or copied by this layer.

`algebra/logical_basis.py` derives a 24x24 logical action by pairing each
physically shifted basis Pauli against all dual logicals. Row i contains the
coefficients of transformed generator i; row coefficients transform as `c M`
and column coefficients as `M.T c`. The printed 6x6 matrices are comparison
oracles, not inputs to the action construction. Every residual has explicit
stabilizer coefficients and a signed phase offset. Tests reconstruct the
exact Pauli, including for a changed signed basis. Inverses, commuting x/y
actions, symplectic preservation and sixth powers are checked. Physical x^6
on the ell=12 torus remains nonidentity; only its logical quotient is identity.

The default frozen fixture path is the source checkout's `reference/` directory
in this editable development installation. Other installations can supply an
explicit `reference_dir`; fixtures are not regenerated or embedded in a wheel.
Code JSON loading validates schemas and algebra rather than trusting serialized
claims. Shift certificates validate their schema and dimensions on load and
require signed witness replay against their identified code, as the tests do.
There are no network, GAP or distance-search side effects on import.

O1--O5 remain unresolved: inter-module K23 action rows; historical Relay
parameters/prior/column policy; physical scheduling/shift/lowering/boundaries;
primitive multiplicities/admission; original data/counts/grids/bootstrap.
None is needed for this independent algebra construction. Strict paper
manifests continue to reject them through the phase-00 manifest layer.
