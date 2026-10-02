"""Deterministic bounded sampling of admitted primitive faults."""
from dataclasses import dataclass
import hashlib
import json
import time
from pathlib import Path

import numpy as np


def run_manifest(model, decoder, *, series, profile_label):
    """Bind sampled columns, fixed priors, backend, circuit and policies."""
    from gross_design_bandle.bench.relay import array_identity, matrix_identity
    if not series or not profile_label:
        raise ValueError('series and profile label required')
    manifest = {'schema_version': 1, 'series': series, 'profile_label': profile_label,
        'paper_exact': False, 'open_items': ['O1', 'O2', 'O3', 'O4', 'O5'],
        'sampler_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'circuit_sha256': hashlib.sha256(str(model.circuit).encode()).hexdigest(),
        'noise_profile': model.profile.name, 'model_p': model.profile.p,
        'raw_catalogue_sha256': hashlib.sha256(json.dumps(model.raw, sort_keys=True).encode()).hexdigest(),
        'locations_sha256': hashlib.sha256(json.dumps([x.to_dict() for x in model.locations], sort_keys=True).encode()).hexdigest(),
        'admission_policy': model.admission_policy,
        'grouping_policy': model.grouping_policy, 'N': model.N,
        'admitted_to_copy': array_identity(model.admitted_to_copy),
        'copy_to_raw': array_identity(model.copy_to_raw),
        'copy_ordinal': array_identity(model.copy_ordinal),
        'H': matrix_identity(model.H), 'Lambda': matrix_identity(model.Lambda),
        'decoder': decoder.manifest(), 'pilot_only': True, 'performance_evidence': False}
    encoded = json.dumps(manifest, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()
    manifest['run_hash'] = hashlib.sha256(encoded).hexdigest()
    return manifest


def stream_seed(run_hash, series, mode, point_index, chunk_index, kind):
    if not run_hash or not series or mode not in ('bernoulli', 'fixed_weight') or kind not in ('faults', 'decoder', 'bootstrap'):
        raise ValueError('invalid stream identity')
    if any(type(i) is not int or i < 0 for i in (point_index, chunk_index)):
        raise ValueError('indices must be nonnegative integers')
    payload = json.dumps(['gross-sampling-v1', run_hash, series, mode, point_index, chunk_index, kind], separators=(',', ':')).encode()
    return int.from_bytes(hashlib.sha256(payload).digest()[:8], 'little')


def sample_indices(n, shots, mode, value, rng):
    if type(n) is not int or n < 1 or type(shots) is not int or shots < 1:
        raise ValueError('positive catalogue and shots required')
    if mode == 'fixed_weight':
        if type(value) is not int or not 0 <= value <= n:
            raise ValueError('weight outside catalogue')
        return tuple(np.sort(rng.choice(n, size=value, replace=False)) for _ in range(shots))
    if mode == 'bernoulli':
        if not np.isfinite(value) or not 0 <= value <= 1:
            raise ValueError('Bernoulli probability outside [0,1]')
        return tuple(np.flatnonzero(row) for row in rng.random((shots, n)) < value)
    raise ValueError('unknown sampling mode')


def sparse_xor(H, Lambda, chosen):
    """Accumulate CSC columns by GF(2) XOR without densifying the catalogue."""
    H = H.tocsc(); Lambda = Lambda.tocsc()
    if H.shape[1] != Lambda.shape[1]:
        raise ValueError('joint column count mismatch')
    s = np.zeros((len(chosen), H.shape[0]), dtype=np.uint8)
    l = np.zeros((len(chosen), Lambda.shape[0]), dtype=np.uint8)
    for i, cols in enumerate(chosen):
        cols = np.asarray(cols)
        if cols.ndim != 1 or cols.dtype.kind not in 'iu' or len(np.unique(cols)) != len(cols) or np.any(cols >= H.shape[1]) or np.any(cols < 0):
            raise ValueError('fault indices must be distinct in-range integers')
        for j in cols:
            a, b = H.indptr[j:j+2]
            s[i, H.indices[a:b]] ^= H.data[a:b]
            a, b = Lambda.indptr[j:j+2]
            l[i, Lambda.indices[a:b]] ^= Lambda.data[a:b]
    return s, l


@dataclass
class PilotBudget:
    max_shots_per_point: int = 256
    max_points: int = 3
    max_seconds: float = 120.0

    def __post_init__(self):
        if not (0 < self.max_shots_per_point <= 256 and 0 < self.max_points <= 3 and 0 < self.max_seconds <= 120):
            raise ValueError('pilot budget exceeds authorization')
        self.started = time.monotonic()
        self.points = {}

    def check(self, point, shots):
        if time.monotonic() - self.started >= self.max_seconds:
            raise TimeoutError('pilot wall-time budget exhausted')
        if type(shots) is not int or shots < 1 or self.points.get(point, 0) + shots > self.max_shots_per_point:
            raise ValueError('pilot shots per point exceeded')
        if point not in self.points and len(self.points) >= self.max_points:
            raise ValueError('pilot point count exceeded')
        self.points[point] = self.points.get(point, 0) + shots


def run_chunk(model, decoder, *, run_hash, series, mode, point_index, point_value,
              chunk_index, shots, budget, max_decoder_threads=1):
    """One independently seeded chunk; failed decoder returns remain scored."""
    from gross_design_bandle.bench.relay import summarize
    if max_decoder_threads != 1:
        raise ValueError('pinned Relay batch has no audited internal thread cap; use one thread')
    if mode == 'bernoulli' and (not np.isfinite(point_value) or not 0 <= point_value <= 1):
        raise ValueError('physical p outside [0,1]')
    if model.H.shape[1] != model.N or model.Lambda.shape[1] != model.N:
        raise ValueError('model catalogue is not aligned')
    if decoder.graph_profile != 'preserve_columns' or decoder.H.shape != model.H.shape or decoder.Lambda.shape != model.Lambda.shape or (decoder.H != model.H).nnz or (decoder.Lambda != model.Lambda).nnz:
        raise ValueError('decoder must address identical admitted columns')
    budget.check((series, mode, point_index), shots)
    rng = np.random.default_rng(stream_seed(run_hash, series, mode, point_index, chunk_index, 'faults'))
    q = point_value / 15 if mode == 'bernoulli' else point_value
    chosen = sample_indices(model.N, shots, mode, q, rng)
    syndromes, truth = sparse_xor(model.H, model.Lambda, chosen)
    base = stream_seed(run_hash, series, mode, point_index, chunk_index, 'decoder')
    ids = [int.from_bytes(hashlib.sha256(f'{base}:{i}'.encode()).digest()[:8], 'little') for i in range(shots)]
    if len(set(ids)) != shots:
        raise ValueError('decoder stream collision')
    t0 = time.monotonic()
    outcomes = decoder.decode_batch(syndromes, stream_ids=ids)
    elapsed = time.monotonic() - t0
    if time.monotonic() - budget.started > budget.max_seconds:
        raise TimeoutError('pilot wall-time budget exhausted during decoding')
    shot_results = []
    for expected, outcome in zip(truth, outcomes):
        logical_mismatch = outcome.logical_prediction is not None and not np.array_equal(outcome.logical_prediction, expected)
        shot_results.append({'failure': bool(not outcome.success or logical_mismatch),
            'invalid_return': bool(outcome.invalid_return),
            'nonconvergence': bool(not outcome.backend_success),
            'residual_syndrome': bool(outcome.residual_syndrome is not None and outcome.residual_syndrome.any()),
            'observable_mismatch': bool(logical_mismatch)})
    return {'run_hash': run_hash, 'series': series, 'mode': mode, 'point_index': point_index,
            'point_value': point_value, 'chunk_index': chunk_index, 'N': model.N,
            'fault_stream_seed': stream_seed(run_hash, series, mode, point_index, chunk_index, 'faults'),
            'decoder_stream_seed': base, 'decoder_threads': 1,
            'weights': [len(x) for x in chosen], 'shot_results': shot_results,
            'counts': summarize(outcomes, truth),
            'decoder_seconds': elapsed, 'iterations': [x.iterations for x in outcomes],
            'pilot_only': True, 'performance_evidence': False}
