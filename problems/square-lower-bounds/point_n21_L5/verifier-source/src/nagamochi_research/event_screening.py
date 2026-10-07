"""Numerical capture-event samples supplement random coverage checks.

Midpoints of capture-coordinate intervals expose thin gaps. This is bounded
sampling, not exhaustive arrangement verification or a proof.
"""
import numpy as np
from fractions import Fraction as F
from unified_measure import orbit


def event_poses(primitives,weights,L,B,per_angle=8192,seed=20280000):
    L=float(L);B=float(B);points=[]
    for p,w in zip(primitives,weights):
        if w<=1e-9 or p['kind'] not in ('point','segment','rectangle'):continue
        for g in orbit(p['kind'],p['geometry'],F(str(L))):
            points.append(list(map(float,g[:2])))
            if len(g)==4:points.append(list(map(float,g[2:])))
    if not points:return np.empty((0,3))
    xy=np.unique(np.round(points,13),axis=0);rng=np.random.default_rng(seed);result=[]
    for t in (0.,1e-7,1e-5,.001,.005,.02,.1,.3,.414213562373095):
        c=(1-t*t)/(1+t*t);s=2*t/(1+t*t);a=B*(c+s)/2
        u=c*xy[:,0]+s*xy[:,1];v=-s*xy[:,0]+c*xy[:,1]
        us=np.unique(np.r_[u-B/2,u+B/2,a*(c+s),(L-a)*(c+s)])
        vs=np.unique(np.r_[v-B/2,v+B/2,-s*(L-a)+c*a,-s*a+c*(L-a)])
        um=(us[:-1]+us[1:])/2;vm=(vs[:-1]+vs[1:])/2
        size=len(um)*len(vm)
        if not size:continue
        ids=np.arange(size) if size<=per_angle else rng.choice(size,per_angle,replace=False)
        U=um[ids//len(vm)];V=vm[ids%len(vm)];x=c*U-s*V;y=s*U+c*V
        ok=(x>=a)&(x<=L-a)&(y>=a)&(y<=L-a)
        result.extend(np.c_[x[ok],y[ok],np.full(np.sum(ok),t)])
    return np.asarray(result,float).reshape(-1,3)
