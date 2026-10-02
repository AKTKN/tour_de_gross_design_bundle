"""Instruction normalization, independent of a future decoder/sampler."""
from math import isfinite


def shift_rate(p_circuit, instructions):
    if type(instructions) is not int or instructions<1:
        raise ValueError('instructions must be a positive integer')
    if isinstance(p_circuit,bool) or not isinstance(p_circuit,(int,float)) or not isfinite(p_circuit) or not 0<=p_circuit<=1:
        raise ValueError('circuit failure probability must be finite in [0,1]')
    return p_circuit/instructions
