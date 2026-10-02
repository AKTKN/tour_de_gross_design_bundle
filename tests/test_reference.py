"""Tests for delivered reference-audit utilities, not the planned simulator."""
from pathlib import Path
import copy,json,sys
import numpy as np
import pytest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from audit_reference import audit,code_data,surgery_graph,matrices,rank,parse_label
from reconstruct_fits import failure_ansatz,reference_rate

@pytest.mark.parametrize('name',['gross','two_gross'])
def test_full_algebra_audit(name):
    spec=json.loads((ROOT/'reference'/f'{name}.json').read_text())
    result=audit(spec)
    assert result['logical_qubits']==12

@pytest.mark.parametrize('name',['gross','two_gross'])
def test_reduced_cycles_are_not_a_standalone_full_basis(name):
    spec=json.loads((ROOT/'reference'/f'{name}.json').read_text())
    graph=surgery_graph(spec,'XX');b,c=matrices(graph)
    assert rank(c)<len(graph.edges)-rank(b)

@pytest.mark.parametrize('name',['gross','two_gross'])
def test_corrupted_cycle_is_rejected(name):
    spec=json.loads((ROOT/'reference'/f'{name}.json').read_text())
    graph=surgery_graph(spec,'XX')
    graph.cycles[0][1]='not-a-vertex'
    with pytest.raises((AssertionError,KeyError)):matrices(graph)

def test_ansatz_cutoff_and_monotonicity():
    w=np.arange(200,dtype=int)
    f=failure_ansatz(w,-19.49,4.65,5,23)
    assert np.all(f[:5]==0) and np.all(np.diff(f)>=0)
    assert np.all(f<1) and f[5]>0

def test_reference_probability_validation():
    with pytest.raises(ValueError):reference_rate({},0.0)

def test_label_parser():
    spec={'ell':12,'m':6}
    assert parse_label('xyL',spec)==7
    assert parse_label('1R',spec)==72
    with pytest.raises(ValueError):parse_label('bad',spec)
