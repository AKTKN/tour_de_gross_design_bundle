"""Read gate-layer facts from the pinned donor AST; never import its builder.

The source has no license notice for build_circuit.py. No source text is copied
or redistributed. Only the ordered (sector, side, monomial) scheduling data are
read. The donor accepts arbitrary permutation matrices A_list/B_list; we supply
literal matrices in the verified paper convention, not its default code factory.
"""
import ast
from hashlib import sha256
from pathlib import Path
import numpy as np
from gross_design_bandle.codes.conventions import ConventionAdapter
from gross_design_bandle.codes.bb import check_matrices

DONOR_SHA256 = 'ba0e867dd6d59035fc41fc2e35b5158a69001c3616e4b62d8f86c4a5abacdb74'
CANONICAL_EXTERNAL = Path('/home/quantum_teresheys/workspace/tour_de_gross_design_bundle/external_libs')


def extract_layers(path=None):
    path = Path(path) if path else CANONICAL_EXTERNAL/'SlidingWindowDecoder/src/build_circuit.py'
    raw = path.read_bytes()
    if sha256(raw).hexdigest() != DONOR_SHA256:
        raise ValueError('donor schedule source hash mismatch')
    tree = ast.parse(raw)
    builder = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'build_circuit')
    block = next(n for n in builder.body if isinstance(n, ast.FunctionDef) and n.name == 'append_blocks')
    time, layers = 1, []
    # Literal operands must have exactly the pinned offset + lookup[i] shape.
    def operand(n):
        if isinstance(n, ast.BinOp) and isinstance(n.op, ast.Add) and isinstance(n.left, ast.Name):
            if isinstance(n.right, ast.Name) and n.right.id == 'i':
                return n.left.id, None
            if isinstance(n.right, ast.Subscript) and isinstance(n.right.value, ast.Name) and isinstance(n.right.slice, ast.Name) and n.right.slice.id == 'i':
                return n.left.id, n.right.value.id
        raise ValueError('unrecognized pinned donor operand')
    for node in block.body:
        if isinstance(node, ast.For):
            for call in ast.walk(node):
                if isinstance(call, ast.Call) and isinstance(call.func, ast.Attribute) and call.func.attr == 'append' and call.args and isinstance(call.args[0], ast.Constant) and call.args[0].value == 'CNOT':
                    control, target = map(operand, call.args[1].elts)
                    if control == ('X_check_offset', None) and target[0] in ('L_data_offset', 'R_data_offset'):
                        sector, side, term = 'X', target[0][0], target[1]
                    elif target == ('Z_check_offset', None) and control[0] in ('L_data_offset', 'R_data_offset'):
                        sector, side, term = 'Z', control[0][0], control[1]
                    else:
                        raise ValueError('unrecognized donor CNOT roles')
                    layers.append((time, sector, side, term))
        elif isinstance(node, ast.Expr) and isinstance(node.value, ast.Call) and node.value.args and isinstance(node.value.args[0], ast.Constant) and node.value.args[0].value == 'TICK':
            time += 1
    if len(layers) != 12 or time != 9:
        raise ValueError('unexpected donor syndrome layer structure')
    return tuple(layers)


def monomial(spec, delta):
    out = np.zeros((spec.cells, spec.cells), dtype=np.uint8)
    for cell in range(spec.cells):
        i, j = divmod(cell, spec.m)
        out[cell, spec.qubit_index('L', i+delta[0], j+delta[1])] = 1
    return out


def adapted_edges(code, layers=None):
    """Figure 4b long-range/near/far orders are A=(2,0,1), B=(2,0,1).

    Verify source check matrices under the explicit target-to-source identity map
    before expanding the extracted layer facts. There is no parameter-only map.
    """
    spec = code.spec
    if len(spec.A) != 3 or len(spec.B) != 3:
        raise ValueError('staggered memory needs three A and three B terms')
    matrices = {f'{poly}{i+1}': monomial(spec, terms[k])
                for poly, terms in (('A', spec.A), ('B', spec.B)) for i,k in enumerate((2,0,1))}
    a = sum(matrices[f'A{i}'] for i in (1,2,3)) % 2
    b = sum(matrices[f'B{i}'] for i in (1,2,3)) % 2
    adapter = ConventionAdapter(spec, 'explicit_permuted_tdg', tuple(range(spec.n)),
                                tuple(range(spec.cells)), tuple(range(spec.cells)))
    adapter.adapt_checks(np.hstack((a,b)), np.hstack((b.T,a.T)))
    assert all(np.array_equal(x,y) for x,y in zip(check_matrices(spec), (code.hx,code.hz)))
    edges = []
    for time, sector, side, term in extract_layers() if layers is None else layers:
        transpose = term.endswith('_T')
        matrix = matrices[term.removesuffix('_T')]
        if transpose:
            matrix = matrix.T
        for cell in range(spec.cells):
            qcell = int(np.flatnonzero(matrix[cell])[0])
            q = code.qubit_ids[qcell + (side == 'R')*spec.cells]
            check = code.check_ids[cell + (sector == 'Z')*spec.cells]
            edges.append((time, check, q))
    return tuple(edges), adapter
