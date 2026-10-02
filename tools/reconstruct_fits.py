"""Evaluate published Table-6 ansatz parameters; this is NOT a simulation.

Example: python tools/reconstruct_fits.py --p 0.001 0.0001 --output evidence/reference_fits.csv
The binomial tail is bounded by exp(-180) in absolute circuit failure probability.
"""
from __future__ import annotations
import argparse
import csv
from pathlib import Path
import numpy as np
from scipy.stats import binom
ROOT=Path(__file__).resolve().parents[1]

def failure_ansatz(w: np.ndarray, log_f0: float, gamma: float, w0: int, k: int) -> np.ndarray:
    w=np.asarray(w,dtype=float)
    if w0<1 or k<1 or gamma<=0: raise ValueError('Invalid ansatz parameters')
    a=1.0-2.0**(-k);out=np.zeros_like(w);mask=w>=w0
    log_h=log_f0-np.log(a)+gamma*np.log(w[mask]/w0)
    out[mask]=-a*np.expm1(-np.exp(np.clip(log_h,-745,700)))
    return out

def upper_weight(n: int, q: float, log_tail: float=-180.0) -> int:
    lo=0;hi=min(n,max(32,int(n*q+12*np.sqrt(n*q*(1-q))+32)))
    while hi<n and binom.logsf(hi,n,q)>log_tail:hi=min(n,2*hi)
    while lo<hi:
        mid=(lo+hi)//2
        if binom.logsf(mid,n,q)<=log_tail:hi=mid
        else:lo=mid+1
    return hi

def reference_rate(row: dict[str,str], p: float) -> tuple[float,float,int]:
    if not 0<p<1:raise ValueError('Require 0 < p < 1')
    n=int(row['N_expanded']);q=p/15;max_w=upper_weight(n,q)
    w=np.arange(max_w+1,dtype=int)
    f=failure_ansatz(w,float(row['log_f0']),float(row['gamma_fit']),int(row['w0']),int(row['K_published']))
    rate=float(np.dot(binom.pmf(w,n,q),f))/int(row['rate_divisor'])
    bound=float(binom.sf(max_w,n,q))/int(row['rate_divisor'])
    return rate,bound,max_w

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--p',nargs='+',type=float,default=[0.001,0.0001])
    parser.add_argument('--output',type=Path,default=ROOT/'evidence/reference_fits.csv')
    args=parser.parse_args()
    with (ROOT/'reference/table6.csv').open() as f:rows=list(csv.DictReader(f))
    with args.output.open('w',newline='') as f:
        out=csv.writer(f);out.writerow(['series','p','published_ansatz_rate_NOT_simulated','absolute_tail_bound','max_weight_summed'])
        for row in rows:
            for p in args.p:out.writerow([row['series'],p,*reference_rate(row,p)])
    print(f'Published-fit evaluations only: {args.output}')
if __name__=='__main__':main()
