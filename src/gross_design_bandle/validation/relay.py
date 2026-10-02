"""Small independent scalar oracle for the audited min-sum recurrence.

Mathematical source: Relay paper 2506.01779v1 Eqs. (1)--(4), Algorithm 1.
Current implementation conventions (ties, gamma indexing, failed candidate)
are explicitly distinguished in docs/RELAY_ADAPTER.md. No donor code copied.
This diagnostic is bounded and never used as a decoding fallback.
"""
import numpy as np


def trace_current_relay(H, priors, syndrome, config):
    H = np.asarray(H, dtype=np.uint8)
    if H.ndim != 2 or max(H.shape) > 64 or config.iteration_cap > 10000:
        raise ValueError('oracle is restricted to small bounded fixtures')
    if config.explicit_gammas is None:
        raise ValueError('oracle requires fixed explicit gammas')
    dtype = np.dtype(config.precision).type
    odds64 = np.log((1-np.asarray(priors))/np.asarray(priors))
    odds = odds64.astype(dtype)
    posterior = odds.copy()
    check_neighbors = [np.flatnonzero(row) for row in H]
    variable_neighbors = [np.flatnonzero(col) for col in H.T]
    traces = []; candidates = []; selected = None; initial = None
    total = 0; converged_count = 0
    for leg in range(config.num_sets+1):
        gamma = (np.full(H.shape[1], config.gamma0, dtype=dtype) if leg == 0 else
                 config.explicit_gammas[leg % len(config.explicit_gammas)].astype(dtype))
        messages = np.zeros(H.shape, dtype=dtype)
        messages[H.astype(bool)] = np.broadcast_to(odds, H.shape)[H.astype(bool)]
        cap = config.pre_iter if leg == 0 else config.set_max_iter
        success = False
        for t in range(1, cap+1):
            alpha = dtype(config.alpha if config.alpha != 0 else 1-2**(-t/config.alpha_iteration_scaling_factor))
            incoming = np.zeros(H.shape, dtype=dtype)
            for i, neighbors in enumerate(check_neighbors):
                for j in neighbors:
                    others = [messages[i, k] for k in neighbors if k != j]
                    sign = (-1 if syndrome[i] else 1) * (-1 if sum(x < 0 for x in others) % 2 else 1)
                    magnitude = min((abs(x) for x in others), default=np.finfo(dtype).max)
                    incoming[i, j] = dtype(sign)*dtype(alpha*magnitude)
            bias = (dtype(1)-gamma)*odds + gamma*posterior
            posterior = bias.copy()
            next_messages = np.zeros_like(messages)
            for j, neighbors in enumerate(variable_neighbors):
                for i in neighbors:
                    posterior[j] = dtype(posterior[j]+incoming[i,j])
                for i in neighbors:
                    value = bias[j]
                    for k in neighbors:
                        if k != i:
                            value = dtype(value+incoming[k,j])
                    next_messages[i,j] = value
            messages = next_messages
            correction = (posterior <= 0).astype(np.uint8)
            success = np.array_equal(H @ correction % 2, syndrome)
            total += 1
            traces.append({'leg': leg, 'iteration': t, 'correction': correction.copy(),
                           'posterior': posterior.copy(), 'success': success})
            if success:
                break
        candidate = {'correction': correction.copy(), 'posterior': posterior.copy(),
                     'success': success, 'cost': float(odds64 @ correction), 'max_iter': cap}
        if leg == 0:
            initial = candidate
        if success:
            candidates.append(candidate)
            converged_count += 1
            if selected is None or candidate['cost'] < selected['cost']:
                selected = candidate
            if ((leg == 0 and config.stopping_criterion == 'pre_iter') or
                (config.stopping_criterion == 'nconv' and converged_count >= config.stop_nconv)):
                break
    # The current backend retains the first-leg failure if no leg converges.
    return {**(selected or initial), 'iterations': total,
            'trace': traces, 'candidates': candidates}
