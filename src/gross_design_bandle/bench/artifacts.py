"""Atomic, checksummed numeric fault artifacts; no pickle or expanded JSON lists."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import tempfile

import numpy as np
from scipy import sparse

FORMAT_VERSION = 2


def file_hash(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def pack_signatures(values, bits):
    # Fault signatures are sparse. Dense packed bits would still cost
    # rows*columns/8, mostly zeros. Store only set-bit indices and column pointers.
    indices = []; indptr = [0]
    for v in values:
        v = int(v)
        if v < 0 or v.bit_length() > bits:
            raise ValueError('signature outside joint row range')
        while v:
            bit = v & -v
            indices.append(bit.bit_length() - 1)
            v ^= bit
        indptr.append(len(indices))
    dtype = np.int32 if max(bits, len(indices)) < 2**31 else np.int64
    return np.array(indices, dtype=dtype), np.array(indptr, dtype=dtype)


def unpack_signatures(indices, indptr, bits):
    if (indices.ndim != 1 or indptr.ndim != 1 or not len(indptr)
            or indptr[0] != 0 or indptr[-1] != len(indices)
            or (np.diff(indptr) < 0).any()
            or (indices < 0).any() or (indices >= bits).any()):
        raise ValueError('invalid sparse signature arrays')
    return tuple(sum(1 << int(row) for row in indices[a:b]) for a,b in zip(indptr[:-1], indptr[1:]))


def write_bundle(path, metadata, arrays):
    """Write to a private sibling, then rename; refuse to overwrite evidence."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(tempfile.mkdtemp(prefix='.' + path.name + '-', dir=path.parent))
    try:
        files = {}
        for name, value in arrays.items():
            if not name.isidentifier():
                raise ValueError('invalid numeric artifact name')
            value = np.asarray(value)
            if value.dtype.hasobject:
                raise ValueError('object arrays are not supported')
            target = temporary / (name + '.npy')
            np.save(target, value, allow_pickle=False)
            files[target.name] = {'sha256': file_hash(target), 'bytes': target.stat().st_size}
        record = {'format_version': FORMAT_VERSION, 'metadata': metadata, 'files': files}
        (temporary / 'manifest.json').write_text(json.dumps(record, sort_keys=True) + '\n')
        # No in-place updates: readers see either no entry or the complete entry.
        os.rename(temporary, path)
    finally:
        if temporary.exists():
            shutil.rmtree(temporary)


def read_bundle(path, *, mmap_mode='r'):
    path = Path(path)
    try:
        record = json.loads((path / 'manifest.json').read_text())
        if record['format_version'] != FORMAT_VERSION or not record['files']:
            raise ValueError('unsupported or empty numeric artifact')
        arrays = {}
        for name, info in record['files'].items():
            if Path(name).name != name or not name.endswith('.npy') or not name[:-4].isidentifier():
                raise ValueError('invalid numeric artifact filename')
            target = path / name
            if target.stat().st_size != info['bytes'] or file_hash(target) != info['sha256']:
                raise ValueError('numeric artifact checksum mismatch')
            arrays[name[:-4]] = np.load(target, mmap_mode=mmap_mode, allow_pickle=False)
        return record['metadata'], arrays
    except (OSError, KeyError, TypeError, json.JSONDecodeError) as exc:
        raise ValueError('incomplete or invalid numeric artifact') from exc


def save_fault_model(path, model, *, validate=True):
    if validate:
        model.validate()
    arrays = {name: getattr(model, name) for name in (
        'copy_to_raw', 'copy_ordinal', 'admission_mask', 'admitted_to_copy',
        'admitted_to_group', 'probabilities', 'decoder_probabilities')}
    bits = model.circuit.num_detectors + model.circuit.num_observables
    for name, values in (('raw_signatures', model.raw_signatures), ('group_signatures', model.group_signatures)):
        arrays[name + '_indices'], arrays[name + '_indptr'] = pack_signatures(values, bits)
    for name in ('H', 'Lambda'):
        matrix = getattr(model, name).tocsc()
        for field in ('data', 'indices', 'indptr'):
            arrays[name + '_' + field] = getattr(matrix, field)
    metadata = {'circuit': str(model.circuit), 'profile': model.profile.name, 'p': model.profile.p,
                'locations': [l.to_dict() for l in model.locations],
                'admission_policy': model.admission_policy, 'grouping_policy': model.grouping_policy,
                'H_shape': list(model.H.shape), 'Lambda_shape': list(model.Lambda.shape),
                'N_raw': len(model.raw), 'N': model.N, 'joint_bits': bits,
                'bit_order': 'detectors then logical actions', 'validated_before_save': True}
    write_bundle(path, metadata, arrays)


def load_fault_model(path, *, mmap_mode='r', validate=True):
    import stim
    from gross_design_bandle.bench.columns import FaultModel
    from gross_design_bandle.noise.catalogue import raw_population
    from gross_design_bandle.noise.locations import Location
    from gross_design_bandle.noise.profiles import NoiseProfile
    metadata, arrays = read_bundle(path, mmap_mode=mmap_mode)
    try:
        circuit = stim.Circuit(metadata['circuit'])
        profile = NoiseProfile(metadata['profile'], metadata['p'])
        locations = tuple(Location(**{**l, 'qubits': tuple(l['qubits']),
                                     'repeat_path': tuple(l['repeat_path'])}) for l in metadata['locations'])
        raw, _, _, _ = raw_population(locations, profile)
        matrices = {}
        for name in ('H', 'Lambda'):
            matrices[name] = sparse.csc_matrix(tuple(arrays[name + '_' + k] for k in
                                                     ('data', 'indices', 'indptr')),
                                               shape=tuple(metadata[name + '_shape']), copy=False)
            matrices[name].check_format(full_check=True)
        model = FaultModel(circuit, profile, locations, tuple(raw),
            unpack_signatures(arrays['raw_signatures_indices'], arrays['raw_signatures_indptr'], metadata['joint_bits']), arrays['copy_to_raw'], arrays['copy_ordinal'],
            arrays['admission_mask'], arrays['admitted_to_copy'], arrays['admitted_to_group'],
            unpack_signatures(arrays['group_signatures_indices'], arrays['group_signatures_indptr'], metadata['joint_bits']), matrices['H'], matrices['Lambda'],
            arrays['probabilities'], arrays['decoder_probabilities'],
            metadata['admission_policy'], metadata['grouping_policy'])
        if len(raw) != metadata['N_raw'] or model.N != metadata['N']:
            raise ValueError('fault artifact population mismatch')
        if validate:
            model.validate()
        return model
    except (KeyError, TypeError, IndexError) as exc:
        raise ValueError('invalid fault artifact structure') from exc


def export_fault_model(output_dir, stem, model):
    """Reuse an intact immutable export; a changed input gets a new directory."""
    from gross_design_bandle.noise.cache import key_for
    key = key_for(model.circuit, model.locations, artifact='export', profile=model.profile.name,
                  p=model.profile.p, admission=model.admission_policy, grouping=model.grouping_policy)
    path = Path(output_dir) / (stem + '_model') / key
    if path.exists():
        try:
            read_bundle(path)
            return path
        except ValueError:
            # Preserve corrupt output for diagnosis, rebuild under the same key.
            import uuid
            path.rename(path.with_name(path.name + '.invalid-' + uuid.uuid4().hex))
    save_fault_model(path, model, validate=False)  # public builders validate cold entries
    return path
