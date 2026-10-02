"""Staggered BB memory: Z reset/read 0/7, X reset/read 1/8; 8C+1."""
from dataclasses import replace
from gross_design_bandle.integrations.sliding_window import adapted_edges
from .checks import Check
from .schedule import Op, Schedule, finish_checks, validate


def memory_checks(code, register=None):
    from gross_design_bandle.surgery.ports import embed
    return tuple(Check.single(id, embed(p,register) if register else p,
                              basis='X' if i<code.spec.cells else 'Z')
                 for i,(id,p) in enumerate(zip(code.check_ids,code.checks)))


def memory_schedule(code, cycles=1):
    if not isinstance(cycles,int) or isinstance(cycles,bool) or cycles<1:
        raise ValueError('cycles must be a positive integer')
    checks = memory_checks(code)
    by_id = {c.id:c for c in checks}
    edges,adapter = adapted_edges(code)
    gates = tuple(Op(t,*by_id[id].interaction(q),id,q) for t,id,q in edges)
    one = finish_checks(checks,gates,phase='memory')
    ops = tuple(replace(o,time=o.time+8*r,round=r,
                        outcome_id=f'memory/{r}/{o.check_id}/0' if o.outcome_id else None)
                for r in range(cycles) for o in one)
    out = Schedule(code.qubit_ids,checks,ops,8*cycles+1,'tdg_fig4b_staggered_v1')
    validate(out)
    return out
