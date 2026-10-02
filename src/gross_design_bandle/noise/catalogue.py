"""Primitive lowering before DEM compaction, plus faithful Stim emission."""
from itertools import product
import os
import numpy as np
import stim
from .locations import validate_locations
from .signatures import joint_signatures
from .profiles import MULTIPLICITIES, parity_probability


def primitive_terms(location):
    if location.kind in ('preparation','readout'):
        # An anticommuting flip: X for Z reset/readout, Z for X or Y.
        words = ('X',) if location.gate in ('R','M') else ('Z',)
    elif location.kind == 'idle':
        words = ('X','Y','Z')
    else:
        words = tuple(''.join(w) for w in product('IXYZ',repeat=2) if w != ('I','I'))
    for word in words:
        x = sum(1<<q for q,a in zip(location.qubits,word) if a in 'XY')
        z = sum(1<<q for q,a in zip(location.qubits,word) if a in 'YZ')
        yield word,x,z


def raw_population(locations, profile):
    """Deterministic primitive/copy provenance, also used by numeric artifact reads."""
    raw = []; faults = []; copy_to_raw = []; ordinal = []
    for j,loc in enumerate(locations):
        for word,x,z in primitive_terms(loc):
            r = len(raw); copies = profile.copies(loc.kind)
            raw.append({'id':f'{loc.id}/{word}','location_index':j,'pauli_word':word,
                'x':x,'z':z,'probability':profile.probability(loc.kind),
                'unequal_probability':MULTIPLICITIES[loc.kind]*profile.p/15,
                'equal_q_multiplicity':MULTIPLICITIES[loc.kind],'copies':copies})
            faults.append((loc.after_instruction,x,z))
            copy_to_raw.extend([r]*copies); ordinal.extend(range(copies))
    return raw, faults, copy_to_raw, ordinal


def build_fault_model(circuit, locations, profile, *, admission_policy, grouping_policy, cache_dir=None):
    """Admission/grouping have no defaults: O4 must be a deliberate choice."""
    from gross_design_bandle.bench.columns import FaultModel, ADMISSION, GROUPING, matrix_from_signatures
    if not profile.independent:
        raise ValueError('categorical channel cannot use an independent Bernoulli catalogue')
    if admission_policy not in ADMISSION or grouping_policy not in GROUPING:
        raise ValueError('unknown admission/grouping policy')
    locations = tuple(locations)
    if cache_dir is None:
        cache_dir = os.environ.get('GROSS_DESIGN_CACHE_DIR') or None
    if cache_dir is False:
        cache_dir = None
    if cache_dir is not None:
        from .cache import cached_model
        return cached_model(cache_dir, circuit, locations, profile, admission_policy, grouping_policy,
                            lambda: _build_fault_model(circuit, locations, profile, admission_policy,
                                                       grouping_policy, cache_dir))
    return _build_fault_model(circuit, locations, profile, admission_policy, grouping_policy, None)


def _build_fault_model(circuit, locations, profile, admission_policy, grouping_policy, cache_dir):
    from gross_design_bandle.bench.columns import FaultModel, matrix_from_signatures
    validate_locations(circuit,locations)
    # Strict ideal detector integrity is required even for an empty population.
    circuit.detector_error_model(allow_gauge_detectors=False)
    raw, faults, copy_to_raw, ordinal = raw_population(locations, profile)
    if cache_dir is None:
        signatures = joint_signatures(circuit,faults)
    else:
        from .cache import cached_signatures
        signatures = cached_signatures(cache_dir, circuit, locations, faults, joint_signatures)
    copy_to_raw = np.array(copy_to_raw,dtype=np.int64); ordinal = np.array(ordinal,dtype=np.int64)
    mask = np.array([admission_policy=='include_all' or bool(signatures[r]) for r in copy_to_raw],dtype=bool)
    admitted = np.flatnonzero(mask)
    selected = [signatures[copy_to_raw[c]] for c in admitted]
    full = matrix_from_signatures(selected,circuit.num_detectors+circuit.num_observables)
    probabilities = np.array([raw[copy_to_raw[c]]['probability'] for c in admitted])
    groups = []; to_group = []; lookup = {}; group_probs = []
    for s,p in zip(selected,probabilities):
        if grouping_policy=='preserve_copies' or s not in lookup:
            lookup[s] = len(groups); groups.append(s); group_probs.append([])
        g = lookup[s]; to_group.append(g); group_probs[g].append(p)
    model = FaultModel(circuit.copy(),profile,locations,tuple(raw),signatures,copy_to_raw,ordinal,mask,admitted,
        np.array(to_group,dtype=np.int64),tuple(groups),full[:circuit.num_detectors].tocsc(),
        full[circuit.num_detectors:].tocsc(),probabilities,np.array([parity_probability(ps) for ps in group_probs]),
        admission_policy,grouping_policy)
    model.validate()
    return model


def emit_noise(circuit, locations, profile):
    """Emit the full physical channel, including joint-zero faults.

    A sampling admission mask never alters the physical circuit. Categorical
    DEPOLARIZE channels are emitted only under their distinct comparison ID.
    """
    locations = tuple(locations); validate_locations(circuit,locations)
    additions = {}
    for loc in locations:
        additions.setdefault(loc.after_instruction,[]).append(loc)
    out = stim.Circuit()
    def append_at(boundary):
        for loc in additions.get(boundary,()):
            if not profile.independent and loc.kind in ('idle','two_qubit'):
                out.append('DEPOLARIZE1' if loc.kind=='idle' else 'DEPOLARIZE2',loc.qubits,profile.p)
            else:
                for _,x,z in primitive_terms(loc):
                    targets = [(stim.target_y if (x>>q&1) and (z>>q&1) else stim.target_x if x>>q&1 else stim.target_z)(q)
                               for q in loc.qubits if (x|z)>>q&1]
                    for _ in range(profile.copies(loc.kind)):
                        out.append('CORRELATED_ERROR',targets,profile.probability(loc.kind))
    append_at(-1)
    for i,op in enumerate(circuit.flattened()):
        out.append(op); append_at(i)
    return out
