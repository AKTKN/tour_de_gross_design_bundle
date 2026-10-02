"""Thin joint-fault adapter for the audited current Relay implementation.

Historical Table-7 settings are deliberately not an executable profile. Imports
do no I/O; the optional backend is imported and checked only at construction.
"""
from dataclasses import dataclass, fields
from functools import lru_cache
import hashlib
import importlib.metadata

import numpy as np
from scipy import sparse

SOURCE_COMMIT = 'd185194ba0cb4101ced4340d82b2ee6d42f225f0'
BINARY_PATH = 'relay_bp/_relay_bp.cpython-311-x86_64-linux-gnu.so'
BINARY_SHA256 = '988e5d39fbfa697144bdc48bc38a2ec17bc3d7fa1ff41c198fe2023a15e80de8'


def array_identity(value):
    value = np.ascontiguousarray(value)
    return {'shape': list(value.shape), 'dtype': value.dtype.str,
            'sha256': hashlib.sha256(value.tobytes()).hexdigest()}


def _binary(value, shape, name):
    value = np.asarray(value)
    if value.shape != shape or value.dtype.kind not in 'biu' or np.any((value != 0) & (value != 1)):
        raise ValueError(f'{name}: expected binary integer/bool array of shape {shape}')
    return np.ascontiguousarray(value, dtype=np.uint8)


def _matrix(value, name):
    if not sparse.issparse(value) or value.ndim != 2:
        raise ValueError(f'{name}: expected joint sparse binary matrix')
    coordinates = value.tocoo(copy=True)
    if value.dtype.kind not in 'biu' or np.any((coordinates.data != 0) & (coordinates.data != 1)):
        raise ValueError(f'{name}: nonbinary matrix')
    # Repeated sparse coordinates are algebraic sums, not new fault variables.
    result = sparse.csc_matrix(coordinates, dtype=np.int64, copy=True)
    result.sum_duplicates()
    result.data %= 2
    result.eliminate_zeros()
    result.sort_indices()
    return result.astype(np.uint8)


def matrix_identity(value):
    return {'shape': list(value.shape), **{k: array_identity(getattr(value, k))
                                         for k in ('data', 'indices', 'indptr')}}


def _priors(value, n):
    result = np.array(value, dtype=np.float64, copy=True)
    if result.shape != (n,) or not np.isfinite(result).all() or np.any((result <= 0) | (result >= .5)):
        raise ValueError('priors: require a fixed length-N vector with 0 < q < 1/2')
    result.flags.writeable = False
    return result


@lru_cache(maxsize=1)
def verify_backend():
    dist = importlib.metadata.distribution('relay-bp')
    actual = hashlib.sha256(dist.locate_file(BINARY_PATH).read_bytes()).hexdigest()
    if dist.version != '0.2.2' or actual != BINARY_SHA256:
        raise ValueError('Relay backend differs from audited source build; review a new lock')
    return {'distribution': 'relay-bp', 'version': dist.version,
            'source_commit': SOURCE_COMMIT, 'binary_sha256': actual}


@dataclass(frozen=True)
class RelayConfig:
    precision: str = 'float32'
    alpha: float = 1.0
    alpha_iteration_scaling_factor: float = 1.0
    gamma0: float = .1
    pre_iter: int = 80
    num_sets: int = 300
    set_max_iter: int = 60
    gamma_dist_interval: tuple = (-.24, .66)
    explicit_gammas: object = None
    stop_nconv: int = 1
    stopping_criterion: str = 'nconv'
    candidate_selection: str = 'minimum_prior_cost'
    seed: int = 0

    def __post_init__(self):
        if self.precision not in ('float32', 'float64'):
            raise ValueError('precision must be float32 or float64')
        for name in ('pre_iter', 'set_max_iter', 'stop_nconv', 'num_sets', 'seed'):
            x = getattr(self, name)
            minimum = 0 if name in ('num_sets', 'seed') else 1
            if type(x) is not int or x < minimum or x >= 2**64:
                raise ValueError(f'invalid {name}')
        if self.iteration_cap >= 2**64:
            raise ValueError('iteration cap exceeds backend integer range')
        for name in ('alpha', 'alpha_iteration_scaling_factor', 'gamma0'):
            x = getattr(self, name)
            if isinstance(x, (bool, str)) or not np.isfinite(x):
                raise ValueError(f'invalid {name}')
        if not 0 <= self.alpha <= 1 or self.alpha_iteration_scaling_factor <= 0:
            raise ValueError('invalid alpha/scaling factor')
        interval = np.asarray(self.gamma_dist_interval, dtype=np.float64)
        if interval.shape != (2,) or not np.isfinite(interval).all() or interval[0] >= interval[1]:
            raise ValueError('invalid gamma interval')
        object.__setattr__(self, 'gamma_dist_interval', tuple(interval.tolist()))
        if self.stopping_criterion not in ('nconv', 'all', 'pre_iter'):
            raise ValueError('unknown stopping criterion')
        if self.candidate_selection != 'minimum_prior_cost':
            raise ValueError('current Relay supports only minimum_prior_cost candidate selection')
        if self.explicit_gammas is not None:
            gammas = np.array(self.explicit_gammas, dtype=np.float64, copy=True)
            if gammas.ndim != 2 or not gammas.shape[0] or not np.isfinite(gammas).all():
                raise ValueError('explicit gammas must be a nonempty finite 2D array')
            gammas.flags.writeable = False
            object.__setattr__(self, 'explicit_gammas', gammas)

    @property
    def iteration_cap(self):
        return self.pre_iter + self.num_sets * self.set_max_iter


@dataclass(frozen=True)
class DecodeOutcome:
    correction: object
    logical_prediction: object
    residual_syndrome: object
    backend_success: bool
    success: bool
    invalid_return: bool
    reason: str
    iterations: object
    backend_max_iter: object
    candidate_cost: object
    posterior_ratios: object
    stream_seed: int


def summarize(outcomes, logical_truth):
    """Score every shot, including malformed returns and nonconvergence."""
    outcomes = tuple(outcomes)
    truth = np.asarray(logical_truth)
    if truth.ndim != 2 or len(truth) != len(outcomes):
        raise ValueError('logical truth must have one row per shot')
    truth = _binary(truth, truth.shape, 'logical truth')
    counts = dict(shots=len(outcomes), failures=0, invalid_returns=0,
                  nonconvergence=0, residual_syndrome_failures=0, observable_failures=0)
    for result, expected in zip(outcomes, truth):
        if result.logical_prediction is not None and result.logical_prediction.shape != expected.shape:
            raise ValueError('logical truth row mismatch')
        logical_failed = result.logical_prediction is not None and not np.array_equal(result.logical_prediction, expected)
        counts['invalid_returns'] += int(result.invalid_return)
        counts['nonconvergence'] += int(not result.backend_success)
        counts['residual_syndrome_failures'] += int(result.residual_syndrome is not None and result.residual_syndrome.any())
        counts['observable_failures'] += int(logical_failed)
        counts['failures'] += int(not result.success or logical_failed)
    return counts


class JointRelayAdapter:
    def __init__(self, H, priors, Lambda, *, logical_names, config=None,
                 profile='current_relay_joint', graph_profile='preserve_columns',
                 input_to_decoder=None):
        if profile != 'current_relay_joint':
            raise ValueError('O2 unresolved: historical Table-7 / paper-exact backend unavailable')
        if graph_profile not in ('preserve_columns', 'joint_signature_xor'):
            raise ValueError('unknown decoder graph profile')
        self.H = _matrix(H, 'H')
        self.Lambda = _matrix(Lambda, 'Lambda')
        n = self.H.shape[1]
        if not n or self.Lambda.shape[1] != n:
            raise ValueError('H/Lambda column alignment mismatch or empty variables')
        self.logical_names = tuple(logical_names)
        if (len(self.logical_names) != self.Lambda.shape[0] or
            any(not isinstance(x, str) or not x for x in self.logical_names) or
            len(set(self.logical_names)) != len(self.logical_names)):
            raise ValueError('logical names must identify every Lambda row uniquely')
        self.priors = _priors(priors, n)
        self.config = config or RelayConfig()
        if not isinstance(self.config, RelayConfig):
            raise ValueError('config must be RelayConfig; historical keys are not translated')
        if self.config.explicit_gammas is not None and self.config.explicit_gammas.shape[1] != n:
            raise ValueError('explicit gamma column count mismatch')
        dtype = np.dtype(self.config.precision)
        numerical = [np.log((1-self.priors)/self.priors), np.array([self.config.gamma0]),
                     self.config.explicit_gammas if self.config.explicit_gammas is not None else np.asarray(self.config.gamma_dist_interval)]
        if any(not np.isfinite(np.asarray(x, dtype=dtype)).all() for x in numerical):
            raise ValueError('parameters not representable in selected float precision')
        if graph_profile == 'preserve_columns':
            mapping = np.arange(n, dtype=np.int64)
            if input_to_decoder is not None and not np.array_equal(input_to_decoder, mapping):
                raise ValueError('preserve_columns requires identity variable map')
        else:
            mapping = np.asarray(input_to_decoder)
            if (mapping.ndim != 1 or mapping.dtype.kind not in 'iu' or
                np.any(mapping < 0) or np.any(mapping >= n) or len(np.unique(mapping)) != n):
                raise ValueError('joint_signature_xor requires a complete input-to-decoder map')
            mapping = mapping.astype(np.int64, copy=True)
        mapping.flags.writeable = False
        self.input_to_decoder = mapping
        self.graph_profile = graph_profile
        self.backend_provenance = verify_backend().copy()
        import relay_bp
        self._backend_class = getattr(relay_bp, 'RelayDecoderF32' if self.config.precision == 'float32' else 'RelayDecoderF64')
        self._backend = self._make_backend(self.config.seed) if self.config.explicit_gammas is not None else None

    @classmethod
    def from_fault_model(cls, model, fixed_priors, *, logical_names, config=None,
                         graph_profile='preserve_columns'):
        """Grouping is an explicit decoder graph; sampling columns stay intact."""
        model.validate()
        priors = _priors(fixed_priors, model.N)
        if graph_profile == 'preserve_columns':
            return cls(model.H, priors, model.Lambda, logical_names=logical_names, config=config)
        if graph_profile != 'joint_signature_xor':
            raise ValueError('unknown decoder graph profile')
        from gross_design_bandle.noise.profiles import parity_probability
        from gross_design_bandle.bench.columns import matrix_from_signatures
        signatures = [model.raw_signatures[model.copy_to_raw[c]] for c in model.admitted_to_copy]
        groups = {}; mapping = []
        for signature in signatures:
            if signature not in groups:
                groups[signature] = len(groups)
            mapping.append(groups[signature])
        mapping = np.asarray(mapping, dtype=np.int64)
        joint = matrix_from_signatures(tuple(groups), model.H.shape[0]+model.Lambda.shape[0])
        grouped_priors = [parity_probability(priors[mapping == g]) for g in range(len(groups))]
        return cls(joint[:model.H.shape[0]], grouped_priors, joint[model.H.shape[0]:],
                   logical_names=logical_names, config=config, graph_profile=graph_profile,
                   input_to_decoder=mapping)

    def _make_backend(self, seed):
        c = self.config
        return self._backend_class(self.H, self.priors, alpha=c.alpha,
            alpha_iteration_scaling_factor=c.alpha_iteration_scaling_factor,
            gamma0=c.gamma0, pre_iter=c.pre_iter, num_sets=c.num_sets,
            set_max_iter=c.set_max_iter, gamma_dist_interval=c.gamma_dist_interval,
            explicit_gammas=c.explicit_gammas, stop_nconv=c.stop_nconv,
            stopping_criterion=c.stopping_criterion, logging=False, seed=seed)

    def _seed(self, stream_id):
        if type(stream_id) is not int or not 0 <= stream_id < 2**64:
            raise ValueError('seeded decoding requires an explicit uint64 stream_id per shot')
        payload = f'gross-relay-stream-v1:{self.config.seed}:{stream_id}'.encode()
        return int.from_bytes(hashlib.sha256(payload).digest()[:8], 'little')

    def decode(self, syndrome, *, stream_id=None):
        syndrome = _binary(syndrome, (self.H.shape[0],), 'syndrome')
        seed = self.config.seed if self._backend is not None else self._seed(stream_id)
        backend = self._backend if self._backend is not None else self._make_backend(seed)
        return self.validate_result(backend.decode_detailed(syndrome), syndrome, seed=seed)

    def decode_batch(self, syndromes, *, stream_ids=None):
        values = np.asarray(syndromes)
        if values.ndim != 2:
            raise ValueError('syndrome batch must be 2D')
        values = _binary(values, (len(values), self.H.shape[0]), 'syndrome batch')
        if self._backend is not None:
            raw = self._backend.decode_detailed_batch(values)
            if len(raw) != len(values):
                raise ValueError('backend batch return count mismatch')
            return tuple(self.validate_result(r, s, seed=self.config.seed) for r, s in zip(raw, values))
        if stream_ids is None or len(stream_ids) != len(values):
            raise ValueError('seeded batch requires stream_ids for every shot')
        seeds = [self._seed(i) for i in stream_ids]
        if len(set(seeds)) != len(seeds):
            raise ValueError('duplicate stream_ids in batch')
        return tuple(self.decode(s, stream_id=i) for s, i in zip(values, stream_ids))

    def validate_result(self, raw, syndrome, *, seed=0):
        """Treat malformed/inconsistent backend output as a counted failure."""
        syndrome = _binary(syndrome, (self.H.shape[0],), 'syndrome')
        try:
            correction = _binary(raw.decoding, (self.H.shape[1],), 'correction')
            detectors = _binary(raw.decoded_detectors, syndrome.shape, 'decoded detectors')
            posterior = np.asarray(raw.posterior_ratios, dtype=np.float64)
            if posterior.shape != correction.shape or not np.isfinite(posterior).all():
                raise ValueError('invalid posterior ratios')
            if type(raw.success) is not bool:
                raise ValueError('invalid backend success flag')
            for name in ('iterations', 'max_iter'):
                x = getattr(raw, name)
                if type(x) is not int or not 1 <= x <= self.config.iteration_cap:
                    raise ValueError(f'invalid backend {name}')
            decoded = np.asarray(self.H @ correction).ravel() % 2
            residual = decoded ^ syndrome
            invalid = not np.array_equal(decoded, detectors) or (raw.success and bool(residual.any()))
            reason = 'inconsistent correction/detector claim' if invalid else ('converged' if raw.success else 'nonconverged')
            prediction = np.asarray(self.Lambda @ correction).ravel() % 2
            cost = float(np.dot(correction, np.log((1-self.priors)/self.priors)))
            return DecodeOutcome(correction, prediction, residual, raw.success,
                raw.success and not invalid, invalid, reason, raw.iterations,
                raw.max_iter, cost, posterior.copy(), seed)
        except (ValueError, TypeError, AttributeError) as error:
            return DecodeOutcome(None, None, None, False, False, True,
                                 str(error), None, None, None, None, seed)

    def manifest(self, *, historical_raw_parameters=None):
        resolved = {f.name: getattr(self.config, f.name) for f in fields(self.config)
                    if f.name != 'explicit_gammas'}
        resolved['explicit_gammas'] = None if self.config.explicit_gammas is None else array_identity(self.config.explicit_gammas)
        return {'schema_version': 1, 'profile': 'current_relay_joint', 'paper_exact': False,
            'open_items': ['O1', 'O2', 'O3', 'O4', 'O5'], 'backend': self.backend_provenance.copy(),
            'historical_raw_parameters': historical_raw_parameters,
            'historical_mapping': 'unresolved; retained for audit only, never translated',
            'resolved_backend_parameters': resolved, 'iteration_cap': self.config.iteration_cap,
            'candidate_selection': 'minimum sum(c_j * log((1-q_j)/q_j)) among converged legs; first equal-cost candidate retained',
            'explicit_gamma_indexing': 'relay leg r=1..num_sets uses row r % number_of_rows; first leg uses gamma0',
            'randomness': 'fixed explicit gamma rows' if self._backend is not None else 'independent per-shot Rust StdRng seed from SHA256(gross-relay-stream-v1:root_seed:stream_id), first 8 bytes little endian',
            'reproducibility': 'scalar/batch and worker allocation invariant for unique stable stream_ids with this pinned binary; explicit mode uses identical gammas on every shot',
            'decoder_graph': {'profile': self.graph_profile, 'H': matrix_identity(self.H),
                'Lambda': matrix_identity(self.Lambda), 'input_to_decoder': array_identity(self.input_to_decoder),
                'duplicate_columns': 'preserved' if self.graph_profile == 'preserve_columns' else 'grouped only by full joint H/Lambda signature',
                'fixed_weight_limit': 'sample original admitted copies; grouping defines a separate decoding function'},
            'logical_names': list(self.logical_names),
            'prior_policy': {'profile': 'fixed_input_vector_for_all_weights_and_p',
                'priors': array_identity(self.priors), 'uniform': bool(np.all(self.priors == self.priors[0])),
                'uniform_q': float(self.priors[0]) if np.all(self.priors == self.priors[0]) else None,
                'true_weight_conditioned': False, 'sampling_p_dependent': False,
                'uniform_scaling_invariance': 'not assumed; finite test vectors only, no universal finite-precision claim'},
            'failure_policy': 'every invalid return, residual syndrome or backend nonconvergence counts as failure; logical mismatch also counts; overlapping counters',
            'fallback': None, 'sector_policy': 'joint X/Z fault columns',
            'input_order': 'sorted CSC row indices; supplied column and Lambda row order retained; duplicate sparse coordinates XOR'}
