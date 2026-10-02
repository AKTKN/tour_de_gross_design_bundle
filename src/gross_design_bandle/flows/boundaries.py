"""Explicit noiseless encoded input and commuting final logical Bell readouts."""
import stim
from gross_design_bandle.surgery.protocol import to_stim_pauli
from .observables import correlation


def mpp(pauli, register):
    ps = to_stim_pauli(pauli, register)
    targets = []
    for q, axis in enumerate(ps):
        if axis:
            if targets:
                targets.append(stim.target_combiner())
            targets.append((stim.target_x, stim.target_y, stim.target_z)[axis-1](q,
                           invert=ps.sign == -1 and not targets))
    circuit = stim.Circuit()
    if targets:
        circuit.append('MPP', targets)
    else:
        circuit.append('MPAD', [int(ps.sign == -1)])
    return circuit


def input_boundary(code, basis, physical_register):
    measured = basis.target != 'memory'
    refs = {i:f'ideal_ref:{code.block_id}:{i+1}' for i in range(code.k) if not (measured and i == 0)}
    register = tuple(physical_register)+tuple(refs.values())
    stabs = [to_stim_pauli(p, register) for p in code.checks]
    for i in range(code.k):
        if measured and i == 0:
            stabs.append(to_stim_pauli(basis.x[i], register))
        else:
            stabs += [to_stim_pauli(correlation(p, axis, refs[i], register))
                      for p, axis in ((basis.x[i], 'X'), (basis.z[i], 'Z'))]
    tableau = stim.Tableau.from_stabilizers(stabs, allow_redundant=True, allow_underconstrained=True)
    circuit = stim.Circuit()
    circuit.append('R', list(range(len(register))))
    circuit += tableau.to_circuit()
    return circuit, register, refs
