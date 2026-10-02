"""Phase-01 reproducible exact algebra evidence; no simulation or distance search.

The independent delivered audit remains in audit_reference.py and is never
implemented in terms of this production layer.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path

from gross_design_bandle.algebra import gf2
from gross_design_bandle.algebra.logical_basis import derive_shift_action
from gross_design_bandle.codes import load_reference_code, small_debug_code
from gross_design_bandle.codes.reference_profiles import FROZEN_SHA256


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    results = []
    for code in (load_reference_code('gross', 'block_a'), load_reference_code('two_gross', 'block_a'), small_debug_code()):
        actions = {}
        for axis, delta in (('x', (1, 0)), ('y', (0, 1))):
            action = derive_shift_action(code, *delta)
            actions[axis] = {'row_matrix': action.matrix.tolist(),
                             'phase_offsets': list(action.phase_offsets),
                             'stabilizer_coefficients': action.stabilizer_coefficients.tolist(),
                             'witness_check_ids': list(code.check_ids)}
        results.append({'code_id': code.id, 'spec_id': code.spec.id, 'code': code.to_dict(),
                        'rank_hx': gf2.rank(code.hx), 'rank_hz': gf2.rank(code.hz),
                        'k': code.k, 'shift_actions': actions})
    evidence = {'scope': 'phase 01 exact algebra only; no physical circuit, decoder, sampling or distance proof',
                'pauli_convention': 'i**phase X**x Z**z in ordered block-qualified register',
                'row_action_convention': "c_prime=c M; column action is M.T",
                'fixture_sha256': FROZEN_SHA256,
                'independent_audit_source_sha256': sha256((root / 'tools/audit_reference.py').read_bytes()).hexdigest(),
                'delivered_audit_sha256': sha256((root / 'evidence/algebra_audit.json').read_bytes()).hexdigest(),
                'results': results}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(evidence, indent=2) + '\n')
    print(f"saved {args.output}: gross 66/66, two-gross 138/138, debug18 7/7 (k=4)")


if __name__ == '__main__':
    main()
