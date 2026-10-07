"""Numerical search coefficients; exact acceptance is in unified_measure.
Import with the selected frozen rectangle engine's fast_geometry on sys.path.
"""
import numpy as np
from numba import njit
from fast_geometry import overlap
from unified_measure import orbit
from radial_measure import disk_integral
QUAD_NODES,QUAD_WEIGHTS=np.polynomial.legendre.leggauss(128)

def expand_primitives(primitives,L):
    rows=[]
    codes={'rectangle':0,'point':1,'segment':2,'disk':3,'bump':4,'annulus':5}
    for p in primitives:
        for g in orbit(p['kind'],p['geometry'],L):
            q=list(map(float,g))
            if len(q)==2:q+=q
            if len(q)==3:q+=[0.]
            rows.append([codes[p['kind']],*q])
    return np.asarray(rows,float).reshape(-1,5)

@njit(cache=True)
def matrix(poses,B,expanded):
    # pose=(cx,cy,tan(theta/2)), with rational values serialized separately.
    out=np.zeros((len(poses),len(expanded)//8))
    for i in range(len(poses)):
        cx,cy,t=poses[i];c=(1-t*t)/(1+t*t);s=2*t/(1+t*t)
        uc=c*cx+s*cy;vc=-s*cx+c*cy
        for j in range(len(expanded)):
            kind,x0,y0,x1,y1=expanded[j];v=0.
            if kind==0:
                v=overlap(expanded[j,1:],cx,cy,c,s,B)/((x1-x0)*(y1-y0))
            elif kind==1:
                u=c*x0+s*y0;z=-s*x0+c*y0
                v=1. if abs(u-uc)<=B/2 and abs(z-vc)<=B/2 else 0.
            elif kind==2:
                lo=0.;hi=1.
                for axis in range(2):
                    a=(c*x0+s*y0-uc) if axis==0 else (-s*x0+c*y0-vc)
                    b=(c*x1+s*y1-uc) if axis==0 else (-s*x1+c*y1-vc)
                    slope=b-a
                    if slope==0:
                        if abs(a)>B/2:hi=-1.;break
                    else:
                        p=(-B/2-a)/slope;q=(B/2-a)/slope
                        lo=max(lo,min(p,q));hi=min(hi,max(p,q))
                v=max(0.,hi-lo)
            else:
                u=c*(x0-cx)+s*(y0-cy);z=-s*(x0-cx)+c*(y0-cy);R=x1;q=y1
                value=disk_integral(u,z,R,B,kind==4,QUAD_NODES,QUAD_WEIGHTS);norm=np.pi*R*R
                if kind==4:norm/=2
                if kind==5:
                    value-=disk_integral(u,z,R*q,B,False,QUAD_NODES,QUAD_WEIGHTS);norm*=1-q*q
                v=value/norm
            out[i,j//8]+=v/8
    return out
