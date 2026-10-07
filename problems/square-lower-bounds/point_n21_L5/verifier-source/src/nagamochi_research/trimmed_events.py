"""Finite event samples aligned to both rotated squares of an octagonal core."""
import numpy as np
from fractions import Fraction as F
from unified_measure import orbit
from trimmed_core import parameters


def event_poses(primitives,weights,L,B,step,margin,per_angle=32768,seed=0):
    L=float(L);B=float(B);h,g=map(float,parameters(step,margin));points=[]
    for p,w in zip(primitives,weights):
        if w<=1e-9 or p['kind'] not in ('point','segment','rectangle'):continue
        for q in orbit(p['kind'],p['geometry'],F(str(L))):
            points.append(list(map(float,q[:2])))
            if len(q)==4:points.append(list(map(float,q[2:])))
    if not points:return np.empty((0,3))
    xy=np.unique(np.round(points,13),axis=0);rng=np.random.default_rng(seed);rows=[]
    half=h/np.sqrt(1+g*g);shift=np.arctan(g)
    for t in (0.,1e-7,1e-5,.001,.005,.02,.1,.3,.414213562373095):
        theta=2*np.arctan(t);a=B*(np.cos(theta)+np.sin(theta))/2
        for sign in (-1,1):
            c=np.cos(theta+sign*shift);s=np.sin(theta+sign*shift)
            u=c*xy[:,0]+s*xy[:,1];v=-s*xy[:,0]+c*xy[:,1]
            corners=np.array([[a,a],[a,L-a],[L-a,a],[L-a,L-a]])
            uu=c*corners[:,0]+s*corners[:,1];vv=-s*corners[:,0]+c*corners[:,1]
            U=np.unique(np.r_[u-half,u+half,uu.min(),uu.max()]);V=np.unique(np.r_[v-half,v+half,vv.min(),vv.max()])
            U=(U[:-1]+U[1:])/2;V=(V[:-1]+V[1:])/2;size=len(U)*len(V)
            if not size:continue
            ids=np.arange(size) if size<=per_angle//2 else rng.choice(size,per_angle//2,replace=False)
            ux=U[ids//len(V)];vy=V[ids%len(V)];x=c*ux-s*vy;y=s*ux+c*vy
            ok=(x>=a)&(x<=L-a)&(y>=a)&(y<=L-a);rows.extend(np.c_[x[ok],y[ok],np.full(np.sum(ok),t)])
    return np.asarray(rows).reshape(-1,3)
