"""Exact centre-cell search at fixed rational angles for the mass-32 candidate.
Searches interiors of capture cells and replays every reported deficit exactly.
No claim of coverage over all angles.
"""
from fractions import Fraction as F
from pathlib import Path
from time import perf_counter
import json
import numpy as np
from score import square,contains,area

ROOT=Path('runs/endpoint_cells_20260926')

def clip_linear(poly,a,b,h):
    out=[]
    for p,q in zip(poly,poly[1:]+poly[:1]):
        vp=a*p[0]+b*p[1]-h;vq=a*q[0]+b*q[1]-h
        if vp>=0:out.append(p)
        if (vp<0<vq) or (vq<0<vp):
            z=vp/(vp-vq);out.append(tuple(p[i]+z*(q[i]-p[i]) for i in (0,1)))
    return out

def scan(pts,ws,t,delta,k=6):
    side=1+delta;c=(1-t*t)/(1+t*t);s=2*t/(1+t*t);r=side*(abs(c)+abs(s))/2
    uv=[(c*x+s*y,-s*x+c*y) for x,y in pts]
    domain=[(c*x+s*y,-s*x+c*y) for x,y in [(r,r),(k-r,r),(k-r,k-r),(r,k-r)]]
    axes=[]
    for dim in (0,1):
        low=min(p[dim] for p in domain);high=max(p[dim] for p in domain)
        axes.append(sorted({low,high}|{p[dim]+sgn*side/2 for p in uv for sgn in (-1,1) if low<p[dim]+sgn*side/2<high}))
    us,vs=axes;um=[(a+b)/2 for a,b in zip(us,us[1:])];vm=[(a+b)/2 for a,b in zip(vs,vs[1:])]
    hu=np.asarray([[int(abs(u-p[0])<side/2) for p in uv] for u in um],dtype=np.int64)
    hv=np.asarray([[int(abs(v-p[1])<side/2) for p in uv] for v in vm],dtype=np.int64)
    costs=(hu*np.asarray([int(4*w) for w in ws]))@hv.T
    tested=0
    for i,j in np.argwhere(costs<4):
        poly=[(us[i],vs[j]),(us[i+1],vs[j]),(us[i+1],vs[j+1]),(us[i],vs[j+1])]
        for a,b,h in [(c,-s,r),(-c,s,-(k-r)),(s,c,r),(-s,-c,-(k-r))]:
            poly=clip_linear(poly,a,b,h)
            if not poly:break
        if not poly or area(poly)==0:continue
        u=sum(p[0] for p in poly)/len(poly);v=sum(p[1] for p in poly)/len(poly);x=c*u-s*v;y=s*u+c*v
        q=square(x,y,side,t);value=sum(w for p,w in zip(pts,ws) if contains(q,p));tested+=1
        assert all(0<=a<=k and 0<=b<=k for a,b in q)
        if value<1:return dict(t=str(t),delta=str(delta),cx=str(x),cy=str(y),side=str(side),score=str(value),cell_count=int(costs.size))
    return dict(t=str(t),delta=str(delta),status='NO_DEFICIT_IN_FULL_DIMENSIONAL_CENTRE_CELLS',cell_count=int(costs.size))

def main():
    start=perf_counter();ROOT.mkdir(exist_ok=False);d=json.loads(Path('runs/endpoint_route_20260926/results.json').read_text())
    pts=[tuple(map(F,p['point'])) for p in d['point_weights']];ws=[F(p['weight']) for p in d['point_weights']];records=[]
    for delta in (F(1,1000),F(1,10**6),F(1,10**9)):
        for t in (F(0),F(1,1000),F(1,19),F(1,10),F(2,13),F(1,4),F(1,3),F(2,5),F(41,100)):
            r=scan(pts,ws,t,delta);records.append(r);print(json.dumps(r),flush=True)
            if 'score' in r:break
    (ROOT/'results.json').write_text(json.dumps(dict(records=records,seconds=perf_counter()-start,scope='Exact fixed-angle deficits or cell checks; not all-angle coverage.'),indent=2))

if __name__=='__main__':main()
