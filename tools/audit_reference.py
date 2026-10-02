"""Independent algebraic audit of the transcribed Tour de gross fixtures.

Uses NumPy only. These checks do NOT certify circuit/phenomenological distance,
Stim detector correctness, a physical schedule, or Monte Carlo reproduction.
"""
from __future__ import annotations
import argparse
from collections import deque
from dataclasses import dataclass
import json
from pathlib import Path
import re
import numpy as np

ROOT=Path(__file__).resolve().parents[1]

def rank(a: np.ndarray) -> int:
    a=np.asarray(a,dtype=np.uint8) % 2
    pivots: dict[int,int]={}
    for row in a:
        x=int.from_bytes(np.packbits(row,bitorder='little').tobytes(),'little')
        while x:
            p=x.bit_length()-1
            if p in pivots: x ^= pivots[p]
            else:
                pivots[p]=x
                break
    return len(pivots)

def kernel_basis(a: np.ndarray) -> np.ndarray:
    """Return a row basis for the binary right kernel (small reference matrices)."""
    r=np.asarray(a,dtype=np.uint8).copy()%2
    pivots=[]; row=0
    for col in range(r.shape[1]):
        hits=np.flatnonzero(r[row:,col])
        if not len(hits):continue
        pivot=row+int(hits[0]);r[[row,pivot]]=r[[pivot,row]]
        for i in range(len(r)):
            if i!=row and r[i,col]:r[i]^=r[row]
        pivots.append(col);row+=1
        if row==len(r):break
    free=[i for i in range(r.shape[1]) if i not in pivots]
    out=np.zeros((len(free),r.shape[1]),dtype=np.uint8)
    for i,f in enumerate(free):
        out[i,f]=1
        for j,p in enumerate(pivots):out[i,p]=r[j,f]
    assert not (np.asarray(a,dtype=np.uint8)@out.T%2).any()
    return out

def parse_label(label: str, spec: dict) -> int:
    side=label[-1]; s=label[:-1]
    if side not in ('L','R'): raise ValueError(label)
    pattern=r'(?:(x)(\d*))?(?:(y)(\d*))?'
    if s=='1': i=j=0
    else:
        m=re.fullmatch(pattern,s)
        if not m or not s: raise ValueError(label)
        i=(int(m[2]) if m[2] else 1) if m[1] else 0
        j=(int(m[4]) if m[4] else 1) if m[3] else 0
    return (side=='R')*spec['ell']*spec['m']+(i%spec['ell'])*spec['m']+j%spec['m']

def shift(v: np.ndarray, dx: int, dy: int, spec: dict) -> np.ndarray:
    return np.roll(np.roll(v.reshape(2,spec['ell'],spec['m']),dx,axis=1),dy,axis=2).reshape(-1)

def dual(v: np.ndarray, spec: dict) -> np.ndarray:
    out=np.zeros_like(v); cells=spec['ell']*spec['m']
    for q in np.flatnonzero(v):
        side,c=divmod(int(q),cells);i,j=divmod(c,spec['m'])
        q2=(1-side)*cells+((1-i)%spec['ell'])*spec['m']+(1-j)%spec['m']
        out[q2]^=1
    return out

def code_data(spec: dict):
    ell,m=spec['ell'],spec['m'];c=ell*m;n=2*c
    hx=np.zeros((c,n),dtype=np.uint8);hz=hx.copy()
    for i in range(ell):
        for j in range(m):
            t=i*m+j
            for dx,dy in spec['A']:
                hx[t,((i+dx)%ell)*m+(j+dy)%m]^=1
                hz[t,c+((i-dx)%ell)*m+(j-dy)%m]^=1
            for dx,dy in spec['B']:
                hx[t,c+((i+dx)%ell)*m+(j+dy)%m]^=1
                hz[t,((i-dx)%ell)*m+(j-dy)%m]^=1
    def op(p,q):
        v=np.zeros(n,dtype=np.uint8)
        for off,key in [(0,p),(c,q)]:
            for i,j in spec[key]:v[off+(i%ell)*m+j%m]^=1
        return v
    x1,x7=op('p','q'),op('r','s');z1,z7=dual(x7,spec),dual(x1,spec)
    lx=np.array([shift(x1,*a,spec) for a in spec['alpha']]+[shift(x7,-b[0],-b[1],spec) for b in spec['beta']])
    lz=np.array([shift(z1,*b,spec) for b in spec['beta']]+[shift(z7,-a[0],-a[1],spec) for a in spec['alpha']])
    return hx,hz,lx,lz

@dataclass
class Graph:
    labels: list[str]
    edges: list[tuple[str,str]]
    cycles: list[list[str]]
    port_x: np.ndarray
    port_z: np.ndarray

def half_components(spec: dict, half: str, hz: np.ndarray, support: np.ndarray):
    prefix=half+':'
    labels=[prefix+str(q) for q in np.flatnonzero(support)]
    edges=[]
    for check in hz:
        hits=np.flatnonzero(check & support)
        if len(hits)==2:edges.append((prefix+str(hits[0]),prefix+str(hits[1])))
        elif len(hits)!=0:raise AssertionError('Expected zero or two support intersections')
    edges += [tuple(prefix+str(parse_label(s,spec)) for s in edge) for edge in spec['extra_edges_'+half]]
    cycles=[[prefix+str(parse_label(s,spec)) for s in cyc] for cyc in spec['cycles_'+half]]
    assert len({frozenset(e) for e in edges})==len(edges), 'Unexpected parallel edges: retain edge IDs instead'
    return labels,edges,cycles

def surgery_graph(spec: dict, kind: str) -> Graph:
    hx,hz,lx,lz=code_data(spec);n=spec['n']
    ls,le,lc=half_components(spec,'l',hz,lx[0]);rs,re_,rc=half_components(spec,'r',hz,lx[6])
    if kind=='X':
        labels,edges,cycles=ls,le,lc
        px=np.zeros((len(labels),n),dtype=np.uint8);pz=px.copy()
        for v,s in enumerate(labels):px[v,int(s[2:])]=1
        return Graph(labels,edges,cycles,px,pz)
    if kind=='inter_XX':
        # Fig. 13(b) algebraic graph: each cross-block bridge is subdivided by
        # a zero-data-port X check acting on the two physical bridge qubits.
        left=['a'+s for s in ls];right=['b'+s for s in ls]
        labels=left+right+[f'adapter:{i}' for i in range(len(spec['bridge_l']))]
        edges=[('a'+u,'a'+v) for u,v in le]+[('b'+u,'b'+v) for u,v in le]
        cycles=[['a'+s for s in c] for c in lc]+[['b'+s for s in c] for c in lc]
        path=['l:'+str(parse_label(s,spec)) for s in spec['bridge_l']]
        for i,v in enumerate(path):edges.extend([('a'+v,f'adapter:{i}'),('b'+v,f'adapter:{i}')])
        for i in range(len(path)-1):
            cycles.append(['a'+path[i],'a'+path[i+1],f'adapter:{i+1}','b'+path[i+1],'b'+path[i],f'adapter:{i}','a'+path[i]])
        px=np.zeros((len(labels),2*n),dtype=np.uint8);pz=px.copy()
        for v,s in enumerate(left):px[v,int(s[3:])]=1
        for v,s in enumerate(right,start=len(left)):px[v,n+int(s[3:])]=1
        return Graph(labels,edges,cycles,px,pz)
    if kind not in ('XX','Y'):raise ValueError(kind)
    shared_l='l:'+str(parse_label(spec['identified_vertices'][0],spec))
    shared_r='r:'+str(parse_label(spec['identified_vertices'][1],spec))
    alias=lambda s:'shared' if s in (shared_l,shared_r) else s
    labels=list(dict.fromkeys(map(alias,ls+rs)))
    edges=[(alias(u),alias(v)) for u,v in le+re_]
    cycles=[[alias(s) for s in c] for c in lc+rc]
    lp=[alias('l:'+str(parse_label(s,spec))) for s in spec['bridge_l']]
    rp=[alias('r:'+str(parse_label(s,spec))) for s in spec['bridge_r']]
    edges+=list(zip(lp,rp))
    cycles += [[lp[i],lp[i+1],rp[i+1],rp[i],lp[i]] for i in range(len(lp)-1)]
    cycles += [['shared',lp[0],rp[0],'shared']]
    px=np.zeros((len(labels),n),dtype=np.uint8);pz=px.copy();index={s:i for i,s in enumerate(labels)}
    for s in ls:px[index[alias(s)],int(s[2:])]^=1
    for s in rs:
        q=int(s[2:]);v=index[alias(s)]
        if kind=='XX':px[v,q]^=1
        else:
            a=np.zeros(n,dtype=np.uint8);a[q]=1
            pz[v] ^= dual(a,spec)
    return Graph(labels,edges,cycles,px,pz)

def matrices(g: Graph):
    v,e=len(g.labels),len(g.edges);idx={s:i for i,s in enumerate(g.labels)}
    b=np.zeros((v,e),dtype=np.uint8);emap={}
    for j,(s,t) in enumerate(g.edges):
        assert s!=t
        b[idx[s],j]=b[idx[t],j]=1
        key=frozenset((s,t));assert key not in emap;emap[key]=j
    cycles=np.zeros((len(g.cycles),e),dtype=np.uint8)
    for i,path in enumerate(g.cycles):
        assert path[0]==path[-1]
        for s,t in zip(path,path[1:]):
            if frozenset((s,t)) not in emap:raise AssertionError(f'Missing edge: {s}, {t}')
            cycles[i,emap[frozenset((s,t))]]^=1
    assert not (b@cycles.T%2).any()
    assert rank(b)==v-1, 'Graph must be connected'
    return b,cycles

def solve_boundary(b: np.ndarray, a: np.ndarray) -> np.ndarray:
    # Deterministic spanning-tree solve B t = a; used only for the algebra audit.
    # Production must use the prescribed local old-check/edge incidence.
    if int(a.sum())%2:raise ValueError('Odd boundary')
    v,e=b.shape;adj=[[] for _ in range(v)]
    for j in range(e):
        x,y=np.flatnonzero(b[:,j]);adj[x].append((int(y),j));adj[y].append((int(x),j))
    parent=[None]*v;parent[0]=(-1,-1);order=[0]
    for x in order:
        for y,j in adj[x]:
            if parent[y] is None:parent[y]=(x,j);order.append(y)
    t=np.zeros(e,dtype=np.uint8);parity=a.copy()
    for y in reversed(order[1:]):
        x,j=parent[y]
        if parity[y]:t[j]=1;parity[x]^=1
    assert not parity[0]
    return t

def local_dress(b: np.ndarray, a: np.ndarray) -> np.ndarray:
    # Preserve a direct edge when exactly two vertices anticommute. Choosing
    # arbitrary long paths can change which reduced cycle checks are redundant.
    hits=np.flatnonzero(a)
    if len(hits)==0:return np.zeros(b.shape[1],dtype=np.uint8)
    if len(hits)==2:
        matches=np.flatnonzero(np.all(b==a[:,None],axis=0))
        if len(matches):
            out=np.zeros(b.shape[1],dtype=np.uint8);out[matches[0]]=1;return out
    return solve_boundary(b,a)

def audit_surgery(spec: dict, kind: str) -> dict:
    hx,hz,lx,lz=code_data(spec);n=spec['n'];g=surgery_graph(spec,kind)
    if kind=='inter_XX':
        zero=np.zeros_like(hx);hx=np.block([[hx,zero],[zero,hx]]);hz=np.block([[hz,zero],[zero,hz]]);n*=2
    b,c=matrices(g);v,e=b.shape
    sx=np.vstack([hx,np.zeros_like(hz)]);sz=np.vstack([np.zeros_like(hx),hz])
    anticommutation=(sx@g.port_z.T+sz@g.port_x.T)%2
    t=np.array([local_dress(b,a) for a in anticommutation],dtype=np.uint8)
    assert np.array_equal(b@t.T%2,anticommutation.T)
    gx=np.block([[sx,np.zeros((len(sx),e),dtype=np.uint8)],[g.port_x,b],[np.zeros((len(c),n+e),dtype=np.uint8)]])
    gz=np.block([[sz,t],[g.port_z,np.zeros((v,e),dtype=np.uint8)],[np.zeros((len(c),n),dtype=np.uint8),c]])
    assert not ((gx@gz.T+gz@gx.T)%2).any(), 'Noncommuting deformed checks'
    rank_stab=rank(np.hstack([gx,gz]));remaining=n+e-rank_stab
    assert remaining==(23 if kind=='inter_XX' else 11), (spec['name'],kind,remaining)
    # Check all omitted edge-only cycles against the combined binary rowspace.
    # A production signed exporter must also retain coefficient/phase witnesses.
    full_cycles=kernel_basis(b)
    cycle_paulis=np.zeros((len(full_cycles),2*(n+e)),dtype=np.uint8)
    cycle_paulis[:,n+e+n:]=full_cycles
    assert rank(np.vstack([np.hstack([gx,gz]),cycle_paulis]))==rank_stab, \
        'Omitted graph-cycle constraints are not implied by the deformed group'
    portx=np.bitwise_xor.reduce(g.port_x,axis=0);portz=np.bitwise_xor.reduce(g.port_z,axis=0)
    expectedx=lx[0].copy();expectedz=np.zeros(spec['n'],dtype=np.uint8)
    if kind=='XX':expectedx^=lx[6]
    elif kind=='Y':expectedz=lz[0].copy()
    elif kind=='inter_XX':expectedx=np.concatenate([lx[0],lx[0]]);expectedz=np.zeros(n,dtype=np.uint8)
    assert np.array_equal(portx,expectedx) and np.array_equal(portz,expectedz)
    return dict(operation=kind,vertices=v,edge_qubits=e,selected_cycle_checks=len(c),cycle_rank=rank(c),full_graph_cycle_rank=e-v+1,merged_logical_qubits=remaining,all_checks_commute=True,all_graph_cycles_in_binary_stabilizer_span=True)

def audit(spec: dict) -> dict:
    hx,hz,lx,lz=code_data(spec)
    assert not (hx@hz.T%2).any()
    assert not (hx@lz.T%2).any() and not (hz@lx.T%2).any()
    assert np.array_equal(lx@lz.T%2,np.eye(12,dtype=np.uint8))
    assert spec['n']-rank(hx)-rank(hz)==12
    assert set(hx.sum(axis=1))=={6} and set(hz.sum(axis=1))=={6}
    weight=12 if spec['name']=='gross' else 20
    assert all(int(x.sum())==weight for x in [lx[0],lx[6],lz[0],lz[6]])
    for name,delta in [('x',(1,0)),('y',(0,1))]:
        # Row-action conventions must be derived from the literal Eq. (34) basis.
        # Its two six-qubit blocks give M.T and M for the printed matrices.
        action=np.array([shift(x,*delta,spec)@lz.T%2 for x in lx],dtype=np.uint8)
        m=np.array(spec['logical_M'+name],dtype=np.uint8)
        expected=np.block([[m.T,np.zeros_like(m)],[np.zeros_like(m),m]])
        assert np.array_equal(action,expected), (spec['name'],name,'basis orientation mismatch')
        power=np.eye(12,dtype=np.uint8)
        for _ in range(6):power=power@action%2
        assert np.array_equal(power,np.eye(12,dtype=np.uint8))
    checks=[audit_surgery(spec,k) for k in ['X','XX','Y','inter_XX']]
    full=checks[1];expected=spec['expected_full_graph']
    assert full['vertices']==expected['vertices'] and full['edge_qubits']==expected['edges']
    assert full['selected_cycle_checks']==expected['selected_cycle_checks']
    assert full['vertices']+1+full['edge_qubits']+full['selected_cycle_checks']==expected['physical_lpu_qubits']
    return dict(code=spec['name'],n=spec['n'],rank_Hx=rank(hx),rank_Hz=rank(hz),logical_qubits=12,chosen_port_weight=weight,logical_shift_matrices_match=True,row_X_action_convention='diag(M_transpose, M), derived from PDF Eq. 34 basis',surgery_checks=checks)

def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path);args=p.parse_args()
    report={'scope':'Algebraic fixture audit only; no Stim circuits, distance certification, or decoding executed.', 'results':[audit(json.loads((ROOT/'reference'/f'{name}.json').read_text())) for name in ['gross','two_gross']]}
    text=json.dumps(report,indent=2)+'\n';print(text)
    if args.output:args.output.write_text(text)
if __name__=='__main__': main()
