"""Exhaustive/stratified forward and Stim checks with saved counterexamples."""
import json
from pathlib import Path
import numpy as np
from gross_design_bandle.flows.signatures import fault_signature, inject_fixed_fault


def validate_faults(model, *, exhaustive, counterexample_path, word_policy='representative'):
    """Check every raw term on small circuits, deterministic strata on large.

    Equal-q copies inherit the checked identical Pauli/boundary; copies are
    checked structurally by FaultModel.validate, not sampled as new mechanisms.
    Large strata span every phase/gate/role and first/middle/last round, using
    X/Y/Z idle faults and four representative joint words per two-qubit gate.
    All gate-template words are independently exhausted in small fixtures.
    Use word_policy='all_words' for an explicitly requested deeper audit.
    Individual omitted large locations are not
    claimed as independently checked.
    """
    if word_policy not in ('representative', 'all_words'):
        raise ValueError('unknown stratified fault word policy')
    model.validate()
    chosen = []; strata = {}; rounds = sorted({l.round for l in model.locations})
    anchors = {rounds[0],rounds[len(rounds)//2],rounds[-1]} if rounds else set()
    for j,r in enumerate(model.raw):
        loc = model.locations[r['location_index']]
        if exhaustive:
            chosen.append(j)
        else:
            if loc.round not in anchors:
                continue
            if word_policy == 'representative' and loc.kind == 'two_qubit' and r['pauli_word'] not in ('IX','ZI','XX','YZ'):
                continue
            key = (loc.phase,loc.gate,loc.role,loc.round,r['pauli_word'])
            strata.setdefault(key,[]).append(j)
    if not exhaustive:
        chosen = [js[len(js)//2] for js in strata.values()]
    trials = []
    for j in chosen:
        r = model.raw[j]; loc = model.locations[r['location_index']]
        forward = fault_signature(model.circuit,loc.after_instruction,r['x'],r['z'])
        actual = tuple(a[0].astype(np.uint8) for a in inject_fixed_fault(model.circuit,loc.after_instruction,r['x'],r['z'])
            .compile_detector_sampler(seed=601).sample(1,separate_observables=True))
        packed = sum(int(b)<<k for k,b in enumerate(np.concatenate(forward)))
        trial = {'raw_index':j,'raw_id':r['id'],'location':loc.to_dict(),'pauli_word':r['pauli_word'],
            'reverse_hex':hex(model.raw_signatures[j]),'forward_hex':hex(packed),
            'forward_detectors':np.flatnonzero(forward[0]).tolist(),'forward_logicals':np.flatnonzero(forward[1]).tolist(),
            'stim_detectors':np.flatnonzero(actual[0]).tolist(),'stim_logicals':np.flatnonzero(actual[1]).tolist()}
        if packed != model.raw_signatures[j] or any(not np.array_equal(a,b) for a,b in zip(forward,actual)):
            path = Path(counterexample_path); path.parent.mkdir(parents=True,exist_ok=True)
            path.write_text(json.dumps(trial,indent=2)+'\n')
            raise ValueError(f'primitive fault signature counterexample: {path}')
        trials.append(trial)
    return {'scope':'exhaustive raw primitives' if exhaustive else 'deterministic stratified raw primitives; not exhaustive large circuit',
        'word_policy':'all_words' if exhaustive else word_policy,
        'checked_raw_primitives':len(trials),'raw_primitives':len(model.raw),'trials':trials,
        'oracles':['independent forward joint Pauli propagation','Stim probability-one joint fault injection'],
        'all_agree':True,'Monte_Carlo_rates':False}
