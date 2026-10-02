#!/usr/bin/env python3
"""One cold/warm local construction measurement, no sampling or decoder."""
import argparse
import json
from pathlib import Path
import tempfile
from time import perf_counter

from gross_design_bandle.codes.reference_profiles import load_reference_code
from gross_design_bandle.flows.harness import build_benchmark
from gross_design_bandle.noise import NoiseProfile, build_fault_model
from gross_design_bandle.noise.locations import benchmark_locations
from gross_design_bandle.bench.artifacts import export_fault_model


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--rounds', type=int, default=10)
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    times = {}
    t = perf_counter()
    code = load_reference_code('gross', 'cache_benchmark')
    harness = build_benchmark(code, operation='memory', rounds=args.rounds)
    harness.validate()
    locations, _ = benchmark_locations(code, harness, operation='memory', rounds=args.rounds)
    times['harness_and_locations_seconds'] = perf_counter() - t
    with tempfile.TemporaryDirectory(prefix='fault-cache-', dir=args.output.parent) as temporary:
        root = Path(temporary)
        models = []
        for name, p in (('cold', .001), ('warm', .001), ('changed_p', .002)):
            t = perf_counter()
            model = build_fault_model(harness.circuit, locations, NoiseProfile('a7_uniform_expanded', p),
                admission_policy='include_all', grouping_policy='joint_signature_xor', cache_dir=root / 'cache')
            times[name + '_seconds'] = perf_counter() - t
            models.append(model)
        cold, warm, changed = models
        assert cold.raw == warm.raw and cold.raw_signatures == warm.raw_signatures == changed.raw_signatures
        assert (cold.H != warm.H).nnz == (cold.Lambda != warm.Lambda).nnz == 0
        assert (cold.H != changed.H).nnz == (cold.Lambda != changed.Lambda).nnz == 0
        paths = []
        for name in ('first_export', 'reused_export'):
            t = perf_counter()
            paths.append(export_fault_model(root / 'export', 'gross_memory', warm))
            times[name + '_seconds'] = perf_counter() - t
        assert paths[0] == paths[1]
        sizes = {'numeric_export_bytes': sum(p.stat().st_size for p in paths[0].rglob('*') if p.is_file())}
        result = {'scope': 'gross memory construction/cache I/O only; no Monte Carlo or phase-07 acceptance',
                  'rounds': args.rounds, 'H_shape': list(cold.H.shape), 'Lambda_shape': list(cold.Lambda.shape),
                  'N': cold.N, 'cold_warm_equal': True, 'timings': times, 'storage': sizes}
        args.output.write_text(json.dumps(result, indent=2) + '\n')
        print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
