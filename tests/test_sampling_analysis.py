"""F03--F05: tiny exact catalogue, bounded pilot, and material rejections."""
from itertools import combinations, product
from types import SimpleNamespace

import numpy as np
import pytest
from scipy import sparse
from scipy.stats import binom

from gross_design_bandle.bench.analysis import (failure_ansatz, integrate_ansatz,
    spectrum, spectrum_from_chunks, point_summaries, select_fit_rows, fit_spectrum,
    bootstrap_predictions, evaluate_holdout)
from gross_design_bandle.bench.results import append_chunk, read_chunks
from gross_design_bandle.bench.sampling import (PilotBudget, run_chunk, sample_indices,
    sparse_xor, stream_seed)
from gross_design_bandle.bench.relay import JointRelayAdapter, RelayConfig
from gross_design_bandle.bench.relay import summarize
from gross_design_bandle.codes.reference_profiles import load_reference_code
from gross_design_bandle.flows.harness import build_benchmark
from gross_design_bandle.noise import NoiseProfile, build_fault_model
from gross_design_bandle.noise.locations import benchmark_locations


@pytest.fixture(scope='module')
def tiny():
    H = sparse.csc_matrix([[1, 1, 0], [0, 1, 1]], dtype=np.uint8)
    L = sparse.csc_matrix([[1, 0, 1], [0, 1, 1]], dtype=np.uint8)
    return H, L


def test_F03_exact_subsets_and_bernoulli_mixture(tiny):
    H, L = tiny
    q = .23
    fixed = []
    for w in range(4):
        outcomes = []
        for subset in combinations(range(3), w):
            s, l = sparse_xor(H, L, [np.array(subset, dtype=int)])
            dense = np.zeros(3, dtype=np.uint8); dense[list(subset)] = 1
            assert np.array_equal(s[0], np.asarray(H @ dense).ravel() % 2)
            assert np.array_equal(l[0], np.asarray(L @ dense).ravel() % 2)
            outcomes.append(int(l[0].any()))
        fixed.append(np.mean(outcomes))
    direct = sum(q**sum(bits)*(1-q)**(3-sum(bits)) * int(((L @ np.array(bits)) % 2).any())
                 for bits in product((0, 1), repeat=3))
    assert sum(binom.pmf(w, 3, q)*fixed[w] for w in range(4)) == pytest.approx(direct)
    rng = np.random.default_rng(12)
    draws = sample_indices(3, 12000, 'fixed_weight', 2, rng)
    observed = {tuple(x) for x in draws}
    assert observed == set(combinations(range(3), 2))
    frequencies = [sum(tuple(x) == c for x in draws) for c in observed]
    assert max(frequencies)-min(frequencies) < 350
    bernoulli = sample_indices(3, 12000, 'bernoulli', q, np.random.default_rng(13))
    assert abs(np.mean([len(x) for x in bernoulli])-3*q) < .03


def test_F03_gross_idle_deterministic_joint_path():
    """Physical gross catalogue to compiled Relay, with no rate sampling."""
    code = load_reference_code('gross', 'phase12_idle')
    harness = build_benchmark(code, operation='memory', rounds=1)
    locations, policy = benchmark_locations(code, harness, operation='memory', rounds=1)
    model = build_fault_model(harness.circuit, locations,
        NoiseProfile('a7_uniform_expanded', .001),
        admission_policy='include_all', grouping_policy='preserve_copies')
    assert policy['paper_exact'] is False and model.N > 0
    joint_nonzero = np.flatnonzero(np.diff(model.H.indptr) + np.diff(model.Lambda.indptr))
    assert len(joint_nonzero) > 0
    selected = [np.array([], dtype=int), np.array([joint_nonzero[0]], dtype=int)]
    syndromes, truth = sparse_xor(model.H, model.Lambda, selected)
    for i, cols in enumerate(selected):
        error = np.zeros(model.N, dtype=np.uint8); error[cols] = 1
        assert np.array_equal(syndromes[i], np.asarray(model.H @ error).ravel() % 2)
        assert np.array_equal(truth[i], np.asarray(model.Lambda @ error).ravel() % 2)
    config = RelayConfig(pre_iter=2, num_sets=1, set_max_iter=2,
                         explicit_gammas=np.full((1, model.N), .1))
    decoder = JointRelayAdapter.from_fault_model(model, np.full(model.N, .003),
        logical_names=tuple(harness.logical_generators['names']), config=config)
    outcomes = decoder.decode_batch(syndromes)
    counts = summarize(outcomes, truth)
    assert counts['shots'] == 2 and 0 <= counts['failures'] <= 2
    assert counts['failures'] >= counts['nonconvergence']
    assert np.all(decoder.priors == .003)


def test_F04_spectrum_tails_selection_and_fits():
    rows = spectrum([{'weight': 2, 'shots': 20, 'failures': 1},
                     {'weight': 5, 'shots': 100, 'failures': 0},
                     {'weight': 10, 'shots': 100, 'failures': 5},
                     {'weight': 20, 'shots': 100, 'failures': 22},
                     {'weight': 81, 'shots': 20, 'failures': 15}])
    assert rows[0]['failures'] == 1 and rows[1]['estimate'] == 0
    assert 0 < rows[1]['upper_95_one_sided'] < .04
    assert [r['weight'] for r in select_fit_rows(rows, 'gross_Y', 5)] == [5, 10, 20]
    assert [r['weight'] for r in select_fit_rows(rows, 'gross_XX', 5)] == [5, 10, 20, 81]
    assert failure_ansatz([0, 4], -4, 2, 5, 3).tolist() == [0, 0]
    exact = integrate_ansatz(12, .3, -4, 2, 5, 3, 10)
    full = sum(binom.pmf(w, 12, .3/15)*failure_ansatz([w], -4, 2, 5, 3)[0] for w in range(13))/10
    assert exact['rate'] == pytest.approx(full, rel=1e-12, abs=1e-20)
    assert exact['absolute_tail_bound'] >= 0 and exact['normalization'] == 'per_instruction'
    chi = fit_spectrum(rows, series='gross_Y', w0=5, K=3)
    likelihood = fit_spectrum(rows, series='gross_Y', w0=5, K=3, method='binomial_likelihood')
    assert chi['method'] == 'chi_squared' and likelihood['method'] == 'binomial_likelihood'
    assert chi['selected_weights'] == [5, 10, 20]
    boot = bootstrap_predictions(rows, series='gross_Y', w0=5, K=3, N=100,
                                 p_grid=[.1, .2], replicates=8, seed=7)
    assert len(boot['bootstrap_prediction_sd']) == 2
    assert all(x >= 0 for x in boot['bootstrap_prediction_sd'])
    holdout = evaluate_holdout(chi, declared_p_grid=[.1, .2],
        observations=[{'p': .1, 'shots': 20, 'failures': 0},
                      {'p': .2, 'shots': 20, 'failures': 1}], N=100)
    assert holdout['declared_p_grid'] == [.1, .2]
    assert holdout['comparison'][0]['observed_rate'] == 0
    assert holdout['comparison'][0]['observed_upper_95_one_sided'] > 0
    assert all(item['prediction_tail_bound'] >= 0 for item in holdout['comparison'])


def test_F05_chunk_streams_resume_and_priors(tiny, tmp_path):
    H, L = tiny
    model = SimpleNamespace(H=H, Lambda=L, N=3)
    config = RelayConfig(pre_iter=3, num_sets=1, set_max_iter=3,
                         explicit_gammas=np.array([[.1,.1,.1]]))
    decoder = JointRelayAdapter(H, [.003]*3, L, logical_names=('X','Z'), config=config)
    prior = decoder.priors.copy()
    budget = PilotBudget(max_shots_per_point=16, max_points=1, max_seconds=10)
    args = dict(run_hash='tiny-model-and-decoder-hash', series='tiny', mode='fixed_weight',
                point_index=0, point_value=1, chunk_index=0, shots=8)
    row = run_chunk(model, decoder, budget=budget, **args)
    assert row['counts']['shots'] == 8 and row['weights'] == [1]*8
    strata = spectrum_from_chunks([row])
    assert strata[0]['weight'] == 1 and strata[0]['shots'] == 8
    assert strata[0]['failures'] == row['counts']['failures']
    points = point_summaries([row])
    assert points[0]['nonconvergence_rate'] == row['counts']['nonconvergence'] / 8
    assert points[0]['failure_rate'] == row['counts']['failures'] / 8
    assert row['decoder_threads'] == 1 and row['performance_evidence'] is False
    assert np.array_equal(decoder.priors, prior)
    path = tmp_path/'chunks.jsonl'
    assert append_chunk(path, row) and not append_chunk(path, row)
    assert len(read_chunks(path)) == 1
    assert stream_seed('h', 's', 'bernoulli', 0, 0, 'faults') != stream_seed('h', 's', 'bernoulli', 0, 0, 'decoder')
    # A fresh process budget gives the same sampled data and decoder outcomes.
    again = run_chunk(model, decoder, budget=PilotBudget(16, 1, 10), **args)
    for field in ('weights', 'counts', 'iterations', 'fault_stream_seed', 'decoder_stream_seed'):
        assert row[field] == again[field]


def test_bounded_pilot_enforcement(tiny):
    H, L = tiny
    b = PilotBudget(2, 1, 10)
    b.check(('s', 'fixed_weight', 0), 2)
    with pytest.raises(ValueError, match='shots'):
        b.check(('s', 'fixed_weight', 0), 1)
    with pytest.raises(ValueError, match='point count'):
        b.check(('s', 'bernoulli', 1), 1)
    with pytest.raises(ValueError, match='budget'):
        PilotBudget(257, 3, 120)
    with pytest.raises(ValueError, match='budget'):
        PilotBudget(256, 4, 120)
    with pytest.raises(ValueError, match='budget'):
        PilotBudget(256, 3, 121)


def test_negative_sampling_and_result_corruption(tiny, tmp_path):
    H, L = tiny
    with pytest.raises(ValueError, match='distinct'):
        sparse_xor(H, L, [np.array([1, 1])])
    with pytest.raises(ValueError, match='weight'):
        sample_indices(3, 1, 'fixed_weight', 4, np.random.default_rng(1))
    with pytest.raises(ValueError, match='probability'):
        sample_indices(3, 1, 'bernoulli', 1.1, np.random.default_rng(1))
    with pytest.raises(ValueError, match='invalid observed'):
        spectrum([{'weight': 0, 'shots': 2, 'failures': 3}])
    with pytest.raises(ValueError, match='incomplete'):
        spectrum_from_chunks([{'weights':[1], 'shot_results':[], 'counts':{'shots':1}}])
    fit = {'source': 'independent observed counts, never Table-6 target fit',
           'log_f0': -4., 'gamma': 2., 'w0': 2, 'K': 1}
    with pytest.raises(ValueError, match='declared holdout p grid'):
        evaluate_holdout(fit, declared_p_grid=[.1, .1], observations=[], N=3)
    with pytest.raises(ValueError, match='must match'):
        evaluate_holdout(fit, declared_p_grid=[.1],
                         observations=[{'p': .2, 'shots': 10, 'failures': 1}], N=3)
    with pytest.raises(ValueError, match='independently fitted'):
        evaluate_holdout({**fit, 'source': 'Table-6 target fit'},
                         declared_p_grid=[.1],
                         observations=[{'p': .1, 'shots': 10, 'failures': 1}], N=3)
    payload = {'run_hash':'h','series':'s','mode':'fixed_weight','point_index':0,'chunk_index':0,'counts':{'shots':1}}
    path = tmp_path/'chunks.jsonl'
    assert append_chunk(path, payload)
    with pytest.raises(ValueError, match='conflicts'):
        append_chunk(path, {**payload, 'counts': {'shots': 2}})
    path.write_bytes(path.read_bytes().replace(b'"shots":1', b'"shots":2'))
    with pytest.raises(ValueError, match='checksum'):
        read_chunks(path)
