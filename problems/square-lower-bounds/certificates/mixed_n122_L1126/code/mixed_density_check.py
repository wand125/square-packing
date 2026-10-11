"""Exact local scoring for nonnegative rectangle density + point masses.
No finite list of local checks is a global packing certificate.
"""
from fractions import Fraction as F
from pathlib import Path
import hashlib,json
from score import square,clip,area,contains


def expand(data):
    L,B=F(data['L']),F(data['B']);rects=[];total=F(0)
    if not (0<B<1 and L>1):raise ValueError('Invalid core/container')
    for rec in data['rectangles']:
        x0,y0,x1,y1=map(F,rec['rectangle']);m=F(rec['mass'])
        if not(0<=x0<x1<=L and 0<=y0<y1<=L and m>=0):raise ValueError('Invalid rectangle')
        total+=m;rho=m/(8*(x1-x0)*(y1-y0))
        for swap in (False,True):
            a,b,c,d=(y0,x0,y1,x1) if swap else (x0,y0,x1,y1)
            for sx,sy in ((1,1),(1,-1),(-1,1),(-1,-1)):
                u,v=(a,c) if sx==1 else (L-c,L-a)
                w,z=(b,d) if sy==1 else (L-d,L-b)
                rects.append((u,w,v,z,rho))
    points=[]
    for rec in data['points']:
        x,y=map(F,rec['point']);w=F(rec['mass'])
        if not(0<=x<=L and 0<=y<=L and w>=0):raise ValueError('Invalid point')
        points.append(((x,y),w));total+=w
    if total!=F(data['total_mass']):raise ValueError('Mixed budget mismatch')
    if total>=data['n']:raise ValueError('Budget not below n')
    semantic={k:data[k] for k in ('n','L','B','rectangles','points','total_mass')}
    if 'proof_net' in data:semantic['proof_net']=data['proof_net']
    digest=hashlib.sha256(json.dumps(semantic,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    return L,B,rects,points,total,digest


def polygon_score(poly,rects,points):
    if not poly or area(poly)==0:return F(0),F(0)
    xmin=min(p[0] for p in poly);xmax=max(p[0] for p in poly)
    ymin=min(p[1] for p in poly);ymax=max(p[1] for p in poly)
    density=F(0)
    for x0,y0,x1,y1,rho in rects:
        if not rho or x1<=xmin or x0>=xmax or y1<=ymin or y0>=ymax:continue
        q=poly
        for axis,bound,greater in ((0,x0,True),(0,x1,False),(1,y0,True),(1,y1,False)):
            q=clip(q,axis,bound,greater)
        density+=rho*area(q)
    atoms=sum((w for p,w in points if contains(poly,p)),F(0))
    return density,atoms


def evaluate(model,cx,cy,t):
    L,B,rects,points,total,digest=model
    poly=square(cx,cy,B,t)
    if not all(0<=x<=L and 0<=y<=L for x,y in poly):raise ValueError('Core outside container')
    density,atoms=polygon_score(poly,rects,points)
    return dict(cx=str(cx),cy=str(cy),t=str(t),side=str(B),density=str(density),point_score=str(atoms),score=str(density+atoms),candidate_digest=digest)


def centre_lower_bound(model,x0,x1,y0,y1,t):
    """Common core of every centre in a rectangle at ONE exact angle."""
    from endpoint_cells import clip_linear
    L,B,rects,points,total,digest=model;c=(1-t*t)/(1+t*t);s=2*t/(1+t*t)
    if x0>x1 or y0>y1:raise ValueError('Reversed centre interval')
    corners=[(x,y) for x in (x0,x1) for y in (y0,y1)]
    if any(not all(0<=u<=L and 0<=v<=L for u,v in square(x,y,B,t)) for x,y in corners):raise ValueError('Invalid centre cell')
    u=[c*x+s*y for x,y in corners];v=[-s*x+c*y for x,y in corners]
    common=[(F(0),F(0)),(L,F(0)),(L,L),(F(0),L)]
    for a,b,h in ((c,s,max(u)-B/2),(-c,-s,-min(u)-B/2),(-s,c,max(v)-B/2),(s,-c,-min(v)-B/2)):
        common=clip_linear(common,a,b,h)
    density,atoms=polygon_score(common,rects,points)
    return density+atoms


def pose_lower_bound(model,x0,x1,y0,y1,t0,t1):
    """Exact lower bound for a centre rectangle AND rational half-angle interval.

    A smaller square at the midpoint lies in every core in the parameter box.
    It is safe to include inadmissible container poses in this relaxation.
    This proves only the requested parameter box, never global coverage.
    """
    if x0>x1 or y0>y1 or not F(-1,2)<=t0<=t1<=F(1,2):
        raise ValueError('Invalid pose interval')
    L,B,rects,points,total,digest=model
    tm=(t0+t1)/2;cm=(1-tm*tm)/(1+tm*tm);sm=2*tm/(1+tm*tm)
    cs=[(1-t*t)/(1+t*t) for t in (t0,t1)]
    cmin=min(cs);cmax=F(1) if t0<=0<=t1 else max(cs)
    smin=2*t0/(1+t0*t0);smax=2*t1/(1+t1*t1)
    dc=max(abs(cmin-cm),abs(cmax-cm));ds=max(abs(smin-sm),abs(smax-sm))
    sa=max(abs(smin),abs(smax));dx=(x1-x0)/2;dy=(y1-y0)/2
    # Midpoint-square coordinate offsets are <= B, a rational upper bound.
    error=B*(dc+ds)+max(cmax*dx+sa*dy,sa*dx+cmax*dy)
    side=B-2*error
    if side<=0:return F(0)
    poly=square((x0+x1)/2,(y0+y1)/2,side,tm)
    density,atoms=polygon_score(poly,rects,points)
    return density+atoms
