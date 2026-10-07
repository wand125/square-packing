"""Test moving the 0.4 endpoint increase out of eight 0.1 line tails.
Numerical search only; exact deficit replay disproves a candidate, never proves it.
"""
import os
os.environ['OPENBLAS_NUM_THREADS']='1';os.environ['OMP_NUM_THREADS']='1'
import argparse,json,math
from pathlib import Path
from fractions import Fraction as F
import numpy as np
from scipy.optimize import differential_evolution
from score import clip,area,segment_length,template,cross,sub,square


def resource(k,trim=True,exact=False,cutoff=F(1)):
    lines,q,p,_=template(k)
    if trim:
        r=F(cutoff)
        if not F(9,10)<=r<=1:raise ValueError('Cutoff must lie in [0.9,1]')
        lines=[((r,1),(k-r,1)),((r,k-1),(k-r,k-1)),((1,r),(1,k-r)),((k-1,r),(k-1,k-r))]
    conv=F if exact else float
    return [tuple(tuple(conv(z) for z in v) for v in line) for line in lines],[tuple(conv(z) for z in v) for v in q+p]


def strict_score(k,poly,res):
    lines,points=res;central=poly
    for axis in (0,1):central=clip(clip(central,axis,1,True),axis,k-1,False)
    a=area(central);length=0
    for u,v in lines:
        # A positive-length segment on the square's boundary contributes zero.
        if any(cross(sub(b,a),sub(u,a))==0 and cross(sub(b,a),sub(v,a))==0 for a,b in zip(poly,poly[1:]+poly[:1])):continue
        length+=segment_length(poly,u,v)
    points_inside=sum(all(cross(sub(b,a),sub(p,a))>0 for a,b in zip(poly,poly[1:]+poly[:1])) for p in points)
    return a+length*F(1,2)+F(points_inside,2)


def run(out,k=4):
    out.mkdir(parents=True,exist_ok=False);res=resource(k);results=[]
    for delta in ('0.000001','0.0001','0.01'):
        side=1+float(delta)
        def poly_float(z):
            u,v,t=z;c=(1-t*t)/(1+t*t);s=2*t/(1+t*t);r=side*(c+s)/2
            cx=r+u*(k/2-r);cy=r+v*(k/2-r)
            return [(cx+side/2*(c*x-s*y),cy+side/2*(s*x+c*y)) for x,y in [(-1,-1),(1,-1),(1,1),(-1,1)]]
        def fun(z):return float(strict_score(k,poly_float(z),res))
        for seed in range(3):
            fit=differential_evolution(fun,[(0,1),(0,1),(0,math.sqrt(2)-1)],seed=926000+seed,popsize=10,maxiter=160,tol=1e-10,polish=False,workers=1)
            u,v,t=[F(float(x)).limit_denominator(10**10) for x in fit.x];lam=1+F(delta);c=(1-t*t)/(1+t*t);s=2*t/(1+t*t);r=lam*(c+s)/2;cx=r+u*(F(k,2)-r);cy=r+v*(F(k,2)-r);poly=square(cx,cy,lam,t)
            assert all(0<=x<=k and 0<=y<=k for x,y in poly)
            val=strict_score(k,poly,resource(k,exact=True));original_repaired=strict_score(k,poly,resource(k,trim=False,exact=True))
            item=dict(k=k,delta=delta,seed=seed,nfev=fit.nfev,numeric=float(fit.fun),score=str(val),score_decimal=float(val),untrimmed_half_score=str(original_repaired),cx=str(cx),cy=str(cy),t=str(t),side=str(lam),status='EXACT_DEFICIT' if val<1 else 'FINITE_CHECK_ONLY')
            results.append(item);(out/'results.json').write_text(json.dumps(results,indent=2));print(json.dumps({q:item[q] for q in ('delta','seed','nfev','numeric','score_decimal','status')}),flush=True)
            if val<1:return
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);p.add_argument('--k',type=int,default=4);a=p.parse_args();run(a.out,a.k)
