"""Reproducible exact rational random probes, including near-axis wall poses."""
from fractions import Fraction as F
from math import lcm
from pathlib import Path
import argparse,json,random,hashlib,time
from probe_external_integer_bridge import read
from score import square,contains

def run(path,targets,count,seed):
    native,span,W,pts=read(path);rng=random.Random(seed);specs=[]
    for i in range(count):
        t=F(rng.randrange(500001),1000000) if i%3 else F(rng.randrange(1,101),10**rng.randrange(4,8))
        ux,uy=F(rng.randrange(1000001),1000000),F(rng.randrange(1000001),1000000)
        if i%5==0:ux=F(0)
        elif i%5==1:uy=F(0)
        specs.append((t,ux,uy))
    records=[]
    for L in targets:
        start=time.monotonic();scores=[];violations=[]
        for i,(t,ux,uy) in enumerate(specs):
            p,q=t.numerator,t.denominator;a=q*q-p*p;b=2*p*q;r=q*q+p*p;h=F(a+b,2*r)
            cx=h+(L-2*h)*ux;cy=h+(L-2*h)*uy
            H=lcm(L.denominator,cx.denominator,cy.denominator);A=int(L*H);X0=int(span*cx*H);Y0=int(span*cy*H);limit=r*span*H
            mass=sum(w for x,y,w in pts if 2*abs(a*(x*A-X0)+b*(y*A-Y0))<=limit and 2*abs(a*(y*A-Y0)-b*(x*A-X0))<=limit)
            rec=dict(index=i,cx=str(cx),cy=str(cy),t=str(t),score=str(F(mass,W)));scores.append((mass,rec))
            if mass<W:violations.append(rec)
        mass,worst=min(scores,key=lambda row:row[0]);poly=square(F(worst['cx']),F(worst['cy']),F(1),F(worst['t']))
        assert all(0<=x<=L and 0<=y<=L for x,y in poly)
        exact=sum((F(w,W) for x,y,w in pts if contains(poly,(F(x)*L/span,F(y)*L/span))),F(0));assert exact==F(mass,W)
        record=dict(L=str(L),poses=count,minimum=worst,violations=violations,minimum_polygon_replayed=True,uniform_rescale_mass=str(F(sum(w for x,y,w in pts),mass)),seconds=time.monotonic()-start)
        records.append(record);print(str(L),float(exact),'violations',len(violations),'rescaled mass',float(F(record['uniform_rescale_mass'])),'seconds',record['seconds'],flush=True)
    return dict(file=str(path),sha256=hashlib.sha256(path.read_bytes()).hexdigest(),seed=seed,count=count,records=records,general_coverage_verified=False)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('certificate',type=Path);p.add_argument('out',type=Path);p.add_argument('targets',nargs='+');p.add_argument('--count',type=int,default=4096);p.add_argument('--seed',type=int,default=9279700);a=p.parse_args();assert not a.out.exists();a.out.write_text(json.dumps(run(a.certificate,list(map(F,a.targets)),a.count,a.seed),indent=2))
