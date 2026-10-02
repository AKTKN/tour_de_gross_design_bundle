"""Exact signed Clifford tableau oracle for a physical check readout."""
from gross_design_bandle.surgery.protocol import to_stim_pauli


def check_tableau(schedule, check, *, composite=False):
    """Pull readout XOR backward through actual gates, evaluate reset Paulis.

    Stim.Tableau arithmetic is exact. This does not use Circuit.has_flow's
    randomized signed check. Intended signed Paulis are an independent input.
    """
    import stim
    register = schedule.register
    unitary = stim.Circuit()
    ops = [o for o in schedule.ordered_ops() if composite or o.check_id==check.id]
    if len({o.round for o in ops})!=1:
        raise ValueError('oracle needs one physical check round')
    for o in ops:
        if o.gate in ('CX','CY','CZ'):
            unitary.append(o.gate,[register.index(q) for q in o.qubits])
    # Pad tableau to the complete register, including identity-only targets.
    unitary.append('I',[len(register)-1])
    readout = stim.PauliString(len(register))
    for o in ops:
        if o.gate in ('M','MX') and o.check_id==check.id:
            readout[register.index(o.qubits[0])] = 1 if o.gate=='MX' else 3
            if o.invert:
                readout *= -1
    tableau = stim.Tableau.from_circuit(unitary)
    backward = tableau.inverse()(readout)
    for o in ops:
        if o.gate in ('R','RX'):
            q = register.index(o.qubits[0])
            if backward[q] not in (0,1 if o.gate=='RX' else 3):
                raise ValueError('readout has nondeterministic ancilla input factor')
            backward[q] = 0
    expected = to_stim_pauli(check.pauli,register)
    if backward != expected:
        raise ValueError(f'physical readout measures wrong signed Pauli: {check.id}')
    # A Bell-mediated check is nondemolition on the prepared ancilla
    # subspace. Its bare data Pauli can acquire Z on BOTH Bell halves under
    # the interactions; after undoing Bell preparation this is a known +Z
    # reset factor. Requiring a bare operator identity on arbitrary ancilla
    # inputs would incorrectly reject such a valid joint measurement.
    preserved = tableau.inverse()(expected)
    for o in ops:
        if o.gate in ('R','RX'):
            q = register.index(o.qubits[0])
            if preserved[q] not in (0,1 if o.gate=='RX' else 3):
                raise ValueError('physical check does not preserve its measured Pauli on prepared ancillas')
            preserved[q] = 0
    if preserved != expected:
        raise ValueError('physical check does not preserve its measured Pauli')
    return {'check_id':check.id,'signed_readout_matches':True,'nondemolition':True,
            'oracle':'exact Stim signed Clifford tableau, inverse readout propagation'}
