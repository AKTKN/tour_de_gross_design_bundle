"""Explicit local cache of numerical work, never of pytest passes."""
from contextlib import contextmanager
from dataclasses import replace
import fcntl
import hashlib
import json
import logging
from pathlib import Path
import uuid

import numpy as np
import scipy
import stim
from gross_design_bandle.bench.artifacts import (
    FORMAT_VERSION, file_hash, load_fault_model, save_fault_model,
    pack_signatures, unpack_signatures, read_bundle, write_bundle)
from .profiles import parity_probability

LOG = logging.getLogger(__name__)


def implementation_identity():
    root = Path(__file__).resolve().parents[1]
    paths = ('noise/catalogue.py', 'noise/signatures.py', 'noise/profiles.py',
             'noise/locations.py', 'noise/cache.py', 'bench/columns.py', 'bench/artifacts.py')
    return {'format': FORMAT_VERSION, 'stim': stim.__version__, 'numpy': np.__version__,
            'scipy': scipy.__version__, 'source': {p: file_hash(root / p) for p in paths}}


def key_for(circuit, locations, **policies):
    value = {'implementation': implementation_identity(), 'circuit': str(circuit),
             'locations': [l.to_dict() for l in locations], **policies}
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


@contextmanager
def entry_lock(root, key):
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    with (root / (key + '.lock')).open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        yield root / key


def quarantine(path, exc):
    LOG.warning('Rebuilding invalid fault cache %s: %s', path, exc)
    path.rename(path.with_name(path.name + '.invalid-' + uuid.uuid4().hex))


def cached_signatures(root, circuit, locations, faults, compute):
    key = key_for(circuit, locations, artifact='raw_joint_signatures')
    with entry_lock(Path(root) / 'signatures', key) as path:
        if path.exists():
            try:
                meta, arrays = read_bundle(path)
                if meta['key'] != key or len(arrays['indptr']) != len(faults) + 1:
                    raise ValueError('signature cache identity mismatch')
                return unpack_signatures(arrays['indices'], arrays['indptr'], meta['bits'])
            except (ValueError, KeyError) as exc:
                quarantine(path, exc)
        result = compute(circuit, faults)
        bits = circuit.num_detectors + circuit.num_observables
        indices, indptr = pack_signatures(result, bits)
        write_bundle(path, {'key': key, 'bits': bits}, {'indices': indices, 'indptr': indptr})
        return result


def reweight(model, profile):
    if model.profile == profile:
        return model
    raw = tuple({**r, 'probability': profile.probability(model.locations[r['location_index']].kind),
                 'unequal_probability': profile.p * r['equal_q_multiplicity'] / 15} for r in model.raw)
    probabilities = np.array([raw[model.copy_to_raw[c]]['probability'] for c in model.admitted_to_copy])
    members = [[] for _ in model.group_signatures]
    for p, g in zip(probabilities, model.admitted_to_group):
        members[g].append(p)
    return replace(model, profile=profile, raw=raw, probabilities=probabilities,
                   decoder_probabilities=np.array([parity_probability(ps) for ps in members]))


def cached_model(root, circuit, locations, profile, admission, grouping, compute):
    key = key_for(circuit, locations, artifact='fault_model', profile=profile.name,
                  admission=admission, grouping=grouping)
    with entry_lock(Path(root) / 'models', key) as path:
        if path.exists():
            try:
                # A cold entry was fully validated before atomic publication.
                # Warm reads verify every file hash and identity, not rebuild H/Lambda.
                model = load_fault_model(path, validate=False)
                if (str(model.circuit) != str(circuit) or model.locations != locations
                        or model.profile.name != profile.name
                        or model.admission_policy != admission or model.grouping_policy != grouping):
                    raise ValueError('fault cache identity mismatch')
                return reweight(model, profile)
            except ValueError as exc:
                quarantine(path, exc)
        model = compute()
        save_fault_model(path, model, validate=False)  # compute() already validates
        return model
