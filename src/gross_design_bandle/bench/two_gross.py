"""Explicit two-gross controls/extensions using the shared physical generators.

Figure 15 supplies only idle and shift series for this code. Every surgery
profile below is an independent extension, with no circuit-distance assertion.
"""
from dataclasses import dataclass, replace
from math import isfinite

from gross_design_bandle.codes.reference_profiles import load_reference_code
from gross_design_bandle.circuits.memory import memory_schedule
from gross_design_bandle.circuits.shift import shift_sequence
from gross_design_bandle.circuits.protocol import build_physical_inmodule, build_physical_inter
from gross_design_bandle.flows.harness import build_benchmark
from gross_design_bandle.flows.shift import build_shift_benchmark
from gross_design_bandle.lpu.reference import build_reference_lpu
from gross_design_bandle.surgery.deformation import compile_deformation
from gross_design_bandle.noise.locations import benchmark_locations
from gross_design_bandle.noise.shift import shift_locations


@dataclass(frozen=True)
class TwoGrossProfile:
    name: str
    operation: str
    rounds: int
    blocks: int

    @property
    def published_series(self):
        return self.name if self.operation in ('memory', 'shift') else None

    @property
    def divisor(self):
        return self.rounds if self.published_series else 1

    def to_dict(self):
        return {'name': self.name, 'code': 'two_gross', 'operation': self.operation,
                'C': self.rounds, 'blocks': self.blocks, 'rate_divisor': self.divisor,
                'classification': 'published_series_reconstruction' if self.published_series else 'extension',
                'Figure15_series': self.published_series,
                'observable_profile': 'full_two_block_centralizer_K47' if self.blocks == 2 else
                                      'single_block_a7_ideal_v1',
                'paper_exact': False, 'open_items': ['O1', 'O2', 'O3', 'O4', 'O5'],
                'circuit_distance': None, 'distance_status': 'not searched or certified'}

    def report_rate(self, p_circuit):
        if (isinstance(p_circuit, bool) or not isinstance(p_circuit, (int, float)) or
                not isfinite(p_circuit) or not 0 <= p_circuit <= 1):
            raise ValueError('circuit failure probability must be finite in [0,1]')
        return p_circuit / self.divisor


PROFILES = (
    TwoGrossProfile('two_gross_idle', 'memory', 18, 1),
    TwoGrossProfile('two_gross_shift', 'shift', 18, 1),
    TwoGrossProfile('two_gross_X_C18_extension', 'X1', 18, 1),
    TwoGrossProfile('two_gross_XX_C18_extension', 'X1*X7', 18, 1),
    TwoGrossProfile('two_gross_Y_C18_extension', 'Y1', 18, 1),
    TwoGrossProfile('two_gross_inter_XX_C17_extension', 'inter_XX', 17, 2),
    TwoGrossProfile('two_gross_inter_XX_C18_extension', 'inter_XX', 18, 2),
)


def profile_named(name):
    for profile in PROFILES:
        if profile.name == name:
            return profile
    raise ValueError('unknown two-gross profile; paper-exact O1--O5 remain unresolved')


@dataclass(frozen=True)
class TwoGrossConstruction:
    profile: TwoGrossProfile
    codes: tuple
    deformation: object
    physical: object
    harness: object

    def locations(self):
        p = self.profile
        if p.operation == 'shift':
            return shift_locations(self.codes[0], self.harness, p.rounds)
        code = self.codes if p.blocks == 2 else self.codes[0]
        return benchmark_locations(code, self.harness, operation=p.operation,
                                   rounds=p.rounds, deformation=self.deformation)


def build_two_gross(name, *, block_ids=None, split_mode='frame', observable_profile=None):
    """Construct a fixed, named profile; never infer a published inter subset."""
    profile = profile_named(name)
    block_ids = tuple(block_ids) if block_ids is not None else tuple(
        f'module_{i}' for i in range(profile.blocks))
    if len(block_ids) != profile.blocks or len(set(block_ids)) != profile.blocks:
        raise ValueError('profile needs the correct number of distinct explicit blocks')
    if split_mode not in ('frame', 'active') or (profile.operation in ('memory', 'shift') and split_mode != 'frame'):
        raise ValueError('invalid split mode for profile')
    if observable_profile is not None and profile.blocks != 2:
        raise ValueError('explicit observable profile is supported for inter only')
    codes = tuple(load_reference_code('two_gross', id) for id in block_ids)
    code = codes[0]; df = None
    if profile.operation == 'shift':
        physical = shift_sequence(code, profile.rounds)
        h = build_shift_benchmark(code, profile.rounds)
    else:
        if profile.operation == 'memory':
            physical = memory_schedule(code, profile.rounds)
        else:
            operation = {'X1': 'X', 'X1*X7': 'XX', 'Y1': 'Y', 'inter_XX': 'inter_XX'}[profile.operation]
            df = compile_deformation(build_reference_lpu(code, operation, codes[1] if profile.blocks == 2 else None))
            physical = (build_physical_inter if profile.blocks == 2 else build_physical_inmodule)(df, profile.rounds)
        h = build_benchmark(codes if profile.blocks == 2 else code, operation=profile.operation,
                            rounds=profile.rounds, deformation=df, split_mode=split_mode,
                            observable_profile=observable_profile)
    h = replace(h, boundary_policy={**h.boundary_policy, 'benchmark_profile': profile.to_dict()})
    return TwoGrossConstruction(profile, codes, df, physical, h)
