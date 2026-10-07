"""Remove central strips while preserving geometry relative to each wall.

Restriction then translation, not coordinate rescaling. Split segments and
rectangles retain their original density before global mass normalization.
Radial supports intersecting a cut are dropped whole, never silently clipped
into a disk. This constructs initial measures, not inherited certificates.
"""
from fractions import Fraction as F
import math
import numpy as np


def trim_template(ps, weights, L0, L1, target):
    L0,L1=F(str(L0)),F(str(L1));weights=np.asarray(weights,float)
    if not 0<L1<=L0 or not np.isfinite(target) or target<=0:
        raise ValueError('invalid trim dimensions/budget')
    if weights.ndim!=1 or len(ps)!=len(weights) or not np.isfinite(weights).all() or np.any(weights<0):
        raise ValueError('invalid weights')
    delta=L0-L1;half=L1/2
    intervals=[(F(0),half,F(0)),(L0-half,L0,delta)] if delta else [(F(0),L0,F(0))]
    result=[];ws=[];dropped_radial=0
    for p,w in zip(ps,weights):
        if w==0:continue
        kind=p['kind'];g=tuple(map(F,p['geometry']));kept=False
        for a,b,dx in intervals:
            for c,d,dy in intervals:
                ratio=F(1);new=None
                if kind=='point':
                    x,y=g
                    if a<=x<=b and c<=y<=d:new=(x-dx,y-dy)
                elif kind=='rectangle':
                    x,y,X,Y=g
                    if not x<X or not y<Y:raise ValueError('degenerate rectangle')
                    l,r=max(x,a),min(X,b);lo,hi=max(y,c),min(Y,d)
                    if l<r and lo<hi:
                        new=(l-dx,lo-dy,r-dx,hi-dy)
                        ratio=(r-l)*(hi-lo)/((X-x)*(Y-y))
                elif kind=='segment':
                    x,y,X,Y=g;lo,hi=F(0),F(1)
                    if x==X and y==Y:raise ValueError('degenerate segment')
                    for v,s,lower,upper in ((x,X-x,a,b),(y,Y-y,c,d)):
                        if not s:
                            if not lower<=v<=upper:hi=F(-1)
                        else:
                            t0,t1=sorted(((lower-v)/s,(upper-v)/s));lo=max(lo,t0);hi=min(hi,t1)
                    if lo<hi:
                        new=(x+lo*(X-x)-dx,y+lo*(Y-y)-dy,x+hi*(X-x)-dx,y+hi*(Y-y)-dy)
                        ratio=hi-lo
                elif kind in ('disk','bump','annulus'):
                    x,y,r=g[:3]
                    if a<=x-r and x+r<=b and c<=y-r and y+r<=d:new=(x-dx,y-dy)+g[2:]
                else:raise ValueError('unsupported primitive')
                if new is not None:
                    result.append(dict(kind=kind,geometry=list(map(str,new)),family='outer_trim'))
                    ws.append(float(w)*float(ratio));kept=True
        if kind in ('disk','bump','annulus') and not kept:dropped_radial+=1
    ws=np.asarray(ws,float);raw=float(ws.sum())
    if raw<=0:raise ValueError('trim removed every support')
    ws*=target/raw
    return result,ws,dict(raw_mass=raw,renormalization=target/raw,
                         removed_mass=float(weights.sum())-raw,dropped_radial_columns=dropped_radial)


def resize_template(ps,weights,L0,L1,target):
    """Trim on contraction; extend endpoint-anchored shapes on expansion.

    On expansion supports crossing the centre are lengthened; centres of
    points/radial supports move with their half-board, radii stay unchanged.
    This is a candidate generator, not the inverse of lost-support trimming.
    """
    L0,L1=F(str(L0)),F(str(L1))
    if L1<=L0:return trim_template(ps,weights,L0,L1,target)
    weights=np.asarray(weights,float)
    if L0<=0 or not np.isfinite(target) or target<=0 or weights.ndim!=1 or len(ps)!=len(weights) or not np.isfinite(weights).all() or np.any(weights<0):
        raise ValueError('invalid extension')
    def coord(x):
        if not 0<=x<=L0:raise ValueError('coordinate outside source')
        return x if x<L0/2 else x+L1-L0 if x>L0/2 else L1/2
    out=[];ws=[]
    for p,w in zip(ps,weights):
        if w==0:continue
        g=list(map(F,p['geometry']));kind=p['kind'];ratio=1.
        if kind in ('rectangle','segment'):
            new=list(map(coord,g))
            if kind=='rectangle':ratio=float((new[2]-new[0])*(new[3]-new[1])/((g[2]-g[0])*(g[3]-g[1])))
            else:ratio=math.hypot(float(new[2]-new[0]),float(new[3]-new[1]))/math.hypot(float(g[2]-g[0]),float(g[3]-g[1]))
        elif kind in ('point','disk','bump','annulus'):new=[coord(g[0]),coord(g[1])]+g[2:]
        else:raise ValueError('unsupported primitive')
        out.append(dict(kind=kind,geometry=list(map(str,new)),family='outer_extend'));ws.append(w*ratio)
    ws=np.asarray(ws,float);raw=float(ws.sum())
    if raw<=0:raise ValueError('empty extension')
    ws*=target/raw
    return out,ws,dict(raw_mass=raw,renormalization=target/raw,removed_mass=float(weights.sum())-raw,dropped_radial_columns=0)


def endpoint_resize_template(ps,weights,L0,L1,target):
    """Endpoint trimming with seam retention for point/radial supports.

    Unlike restriction, atoms in the removed strip are placed on the seam;
    radial kernels retain radius and mass. Rectangle/segment mass scales with
    new area/length. This remains a heuristic for mixed-template continuation.
    """
    L0,L1=F(str(L0)),F(str(L1))
    if L1>=L0:return resize_template(ps,weights,L0,L1,target)
    weights=np.asarray(weights,float)
    if L1<=0 or not np.isfinite(target) or target<=0 or weights.ndim!=1 or len(ps)!=len(weights) or not np.isfinite(weights).all() or np.any(weights<0):
        raise ValueError('invalid endpoint trim')
    def coord(x):
        if not 0<=x<=L0:raise ValueError('coordinate outside source')
        return min(x,L1/2) if x<=L0/2 else max(L1/2,x-(L0-L1))
    out=[];ws=[]
    for p,w in zip(ps,weights):
        if w==0:continue
        g=list(map(F,p['geometry']));kind=p['kind'];ratio=1.
        if kind in ('rectangle','segment'):
            new=list(map(coord,g))
            if kind=='rectangle':ratio=float((new[2]-new[0])*(new[3]-new[1])/((g[2]-g[0])*(g[3]-g[1])))
            else:ratio=math.hypot(float(new[2]-new[0]),float(new[3]-new[1]))/math.hypot(float(g[2]-g[0]),float(g[3]-g[1]))
        elif kind in ('point','disk','bump','annulus'):new=[coord(g[0]),coord(g[1])]+g[2:]
        else:raise ValueError('unsupported primitive')
        if ratio<=0:continue
        out.append(dict(kind=kind,geometry=list(map(str,new)),family='endpoint_trim'));ws.append(w*ratio)
    ws=np.asarray(ws,float);raw=float(ws.sum())
    if raw<=0:raise ValueError('empty endpoint trim')
    ws*=target/raw
    return out,ws,dict(raw_mass=raw,renormalization=target/raw,removed_mass=float(weights.sum())-raw,dropped_radial_columns=0)
