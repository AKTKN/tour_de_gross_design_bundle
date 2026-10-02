"""Independent sampled spectra and explicitly labeled statistical fits."""
from math import log

import numpy as np
from scipy.optimize import least_squares, minimize
from scipy.stats import beta, binom


def failure_ansatz(weights, log_f0, gamma, w0, K):
    w = np.asarray(weights, dtype=float)
    if not np.isfinite(w).all() or np.any(w < 0) or not np.isfinite(log_f0) or not np.isfinite(gamma) or gamma <= 0 or type(w0) is not int or w0 < 1 or type(K) is not int or K < 1:
        raise ValueError('invalid ansatz inputs')
    a = 1 - 2.0**(-K)
    out = np.zeros_like(w)
    mask = w >= w0
    exponent = np.clip(log_f0 - np.log(a) + gamma * np.log(w[mask] / w0), -745, 700)
    out[mask] = -a * np.expm1(-np.exp(exponent))
    return out


def integrate_ansatz(N, p, log_f0, gamma, w0, K, divisor=1, log_tail=-180):
    if type(N) is not int or N < 1 or not np.isfinite(p) or not 0 <= p <= 1 or type(divisor) is not int or divisor < 1 or log_tail >= 0:
        raise ValueError('invalid binomial integration inputs')
    q = p / 15
    lo, hi = 0, N
    while lo < hi:
        mid = (lo + hi) // 2
        if binom.logsf(mid, N, q) <= log_tail:
            hi = mid
        else:
            lo = mid + 1
    upper = lo
    w = np.arange(upper + 1)
    rate = float(np.dot(binom.pmf(w, N, q), failure_ansatz(w, log_f0, gamma, w0, K))) / divisor
    bound = float(binom.sf(upper, N, q)) / divisor
    return {'rate': rate, 'absolute_tail_bound': bound, 'max_weight_summed': upper,
            'normalization': 'per_instruction' if divisor > 1 else 'per_operation'}


def spectrum(rows):
    """Retain every observed stratum, including failures below fit threshold."""
    result = {}
    for row in rows:
        w, shots, fails = (row[k] for k in ('weight', 'shots', 'failures'))
        if type(w) is not int or w < 0 or type(shots) is not int or shots < 1 or type(fails) is not int or not 0 <= fails <= shots:
            raise ValueError('invalid observed count')
        a = result.setdefault(w, {'weight': w, 'shots': 0, 'failures': 0})
        a['shots'] += shots; a['failures'] += fails
    for a in result.values():
        k, n = a['failures'], a['shots']
        a['estimate'] = k / n
        a['upper_95_one_sided'] = 1.0 if k == n else float(beta.ppf(.95, k+1, n-k))
    return [result[w] for w in sorted(result)]


def spectrum_from_chunks(chunks):
    """Build f(w) inputs from every shot, including off-threshold failures."""
    rows = []
    for chunk in chunks:
        if len(chunk['weights']) != chunk['counts']['shots'] or len(chunk['shot_results']) != chunk['counts']['shots']:
            raise ValueError('incomplete per-shot spectrum record')
        for weight, result in zip(chunk['weights'], chunk['shot_results']):
            rows.append({'weight': int(weight), 'shots': 1, 'failures': int(result['failure'])})
    return spectrum(rows)


def point_summaries(chunks):
    """Aggregate all chunks at each sampled point without dropping decoder failures."""
    totals = {}
    fields = ('shots', 'failures', 'invalid_returns', 'nonconvergence',
              'residual_syndrome_failures', 'observable_failures')
    for chunk in chunks:
        key = (chunk['series'], chunk['mode'], chunk['point_index'])
        point = totals.setdefault(key, {'series': key[0], 'mode': key[1],
            'point_index': key[2], 'point_value': chunk['point_value'],
            **{name: 0 for name in fields}})
        if point['point_value'] != chunk['point_value']:
            raise ValueError('conflicting point values')
        counts = chunk['counts']
        if any(type(counts[name]) is not int or counts[name] < 0 for name in fields):
            raise ValueError('invalid point counters')
        if any(counts[name] > counts['shots'] for name in fields[1:]):
            raise ValueError('point counter exceeds shots')
        for name in fields:
            point[name] += counts[name]
    for point in totals.values():
        n, k = point['shots'], point['failures']
        if n == 0:
            raise ValueError('empty point')
        point['failure_rate'] = k / n
        point['nonconvergence_rate'] = point['nonconvergence'] / n
        point['failure_upper_95_one_sided'] = 1.0 if k == n else float(beta.ppf(.95, k+1, n-k))
    return [totals[key] for key in sorted(totals)]


def select_fit_rows(rows, series, w0):
    if type(w0) is not int or w0 < 1:
        raise ValueError('invalid threshold')
    # Exclusion is only for fitting; the source spectrum remains intact.
    return [r for r in rows if r['weight'] >= w0 and not (series == 'gross_Y' and r['weight'] > 80)]


def fit_spectrum(rows, *, series, w0, K, method='chi_squared'):
    chosen = select_fit_rows(rows, series, w0)
    if len(chosen) < 2 or method not in ('chi_squared', 'binomial_likelihood'):
        raise ValueError('at least two selected strata and a known fit method required')
    w = np.array([r['weight'] for r in chosen]); n = np.array([r['shots'] for r in chosen]); k = np.array([r['failures'] for r in chosen])
    if np.any(n <= 0) or np.any(k < 0) or np.any(k > n):
        raise ValueError('invalid fit counts')
    def probability(x):
        return np.clip(failure_ansatz(w, x[0], x[1], w0, K), 1e-300, 1-1e-12)
    start = np.array([log(max((k.sum()+.5)/(n.sum()+1), 1e-8)), 1.])
    bounds = ([-100, .01], [10, 30.])
    if method == 'chi_squared':
        # Jeffreys-smoothed variance is explicit and finite for zero counts.
        center = (k + .5) / (n + 1)
        variance = center * (1-center) / (n+1)
        opt = least_squares(lambda x: (probability(x)-k/n)/np.sqrt(variance), start, bounds=bounds)
        prescription = 'Pearson residual using Jeffreys-smoothed binomial variance; zeros retained'
    else:
        opt = minimize(lambda x: float(-np.sum(k*np.log(probability(x))+(n-k)*np.log1p(-probability(x)))), start,
                       bounds=list(zip(*bounds)), method='L-BFGS-B')
        prescription = 'binomial negative log likelihood; zeros retained'
    if not opt.success:
        raise RuntimeError('fit did not converge')
    return {'method': method, 'series': series, 'log_f0': float(opt.x[0]), 'gamma': float(opt.x[1]),
            'w0': w0, 'K': K, 'selected_weights': w.tolist(), 'variance_policy': prescription,
            'source': 'independent observed counts, never Table-6 target fit'}


def bootstrap_predictions(rows, *, series, w0, K, N, p_grid, divisor=1, replicates=100, seed=0):
    if type(replicates) is not int or replicates < 2:
        raise ValueError('at least two bootstrap replicates required')
    base = fit_spectrum(rows, series=series, w0=w0, K=K)
    rng = np.random.default_rng(seed)
    predictions = []
    for _ in range(replicates):
        replica = [{**r, 'failures': int(rng.binomial(r['shots'], r['failures']/r['shots']))} for r in rows]
        fit = fit_spectrum(replica, series=series, w0=w0, K=K)
        predictions.append([integrate_ansatz(N, p, fit['log_f0'], fit['gamma'], w0, K, divisor)['rate'] for p in p_grid])
    values = np.asarray(predictions)
    return {'fit': base, 'p_grid': list(p_grid), 'bootstrap_prediction_sd': values.std(axis=0, ddof=1).tolist(),
            'replicates': replicates, 'seed': seed, 'band_definition': 'standard deviation of binomial bootstrap predictions'}


def evaluate_holdout(fit, *, declared_p_grid, observations, N, divisor=1):
    """Compare a fixed, predeclared p grid with independently sampled direct counts."""
    grid = tuple(declared_p_grid)
    if not grid or len(set(grid)) != len(grid) or any(not np.isfinite(p) or not 0 <= p <= 1 for p in grid):
        raise ValueError('invalid declared holdout p grid')
    observed = tuple(observations)
    if len(observed) != len(grid) or any(row['p'] != p for p, row in zip(grid, observed)):
        raise ValueError('holdout observations must match the declared p grid')
    if fit.get('source') != 'independent observed counts, never Table-6 target fit':
        raise ValueError('holdout requires an independently fitted spectrum')
    result = []
    for p, row in zip(grid, observed):
        n, k = row['shots'], row['failures']
        if type(n) is not int or n < 1 or type(k) is not int or not 0 <= k <= n:
            raise ValueError('invalid holdout counts')
        prediction = integrate_ansatz(N, p, fit['log_f0'], fit['gamma'],
                                      fit['w0'], fit['K'], divisor)
        result.append({'p': p, 'shots': n, 'failures': k, 'observed_rate': k/n,
            'observed_upper_95_one_sided': 1.0 if k == n else float(beta.ppf(.95, k+1, n-k)),
            'predicted_rate': prediction['rate'],
            'prediction_tail_bound': prediction['absolute_tail_bound']})
    return {'declared_p_grid': list(grid), 'comparison': result,
            'source': 'independent direct Bernoulli holdout; no refit on holdout counts'}
