"""Exact pair-angle diagnostics; sample counts are not full-domain proofs."""
from fractions import Fraction as F
from random import Random
import argparse, hashlib, json
from pathlib import Path


def constraints(s, t):
    x,y,d,a,b,r=s[:6]; X,Y,D,A,B,R=t[:6]
    assert d>0 and D>0 and r>0 and R>0
    assert a*a+b*b==r*r and A*A+B*B==R*R
    dx,dy=F(X,D)-F(x,d),F(Y,D)-F(y,d)
    angle_sum=F(abs(a*A+b*B)+abs(a*B-b*A),r*R)
    threshold=(1+angle_sum)/2
    projection=max(abs((a*dx+b*dy)/r),abs((-b*dx+a*dy)/r),
                   abs((A*dx+B*dy)/R),abs((-B*dx+A*dy)/R))
    half_span=(F(abs(a)+abs(b),r)+F(abs(A)+abs(B),R))/2
    return dict(angle_sum=angle_sum,threshold=threshold,projection=projection,
                distance_squared=dx*dx+dy*dy,
                distance_reject=dx*dx+dy*dy<threshold*threshold,
                compatible=projection>=threshold,
                xy_overlap=abs(dx)<half_span and abs(dy)<half_span)


def run(source, out, samples=30000):
    poses=json.loads(source.read_text())['endpoint']; rng=Random(20260927)
    pairs=set()
    while len(pairs)<min(samples,len(poses)*(len(poses)-1)//2):
        i,j=sorted(rng.sample(range(len(poses)),2));pairs.add((i,j))
    counts=dict(pairs=0,conflicts=0,distance_reject=0,oblique_only_compatible=0,
                equal_angle_oblique_only=0,near_compatible=0)
    examples={}
    for i,j in sorted(pairs):
        q=constraints(poses[i],poses[j]);counts['pairs']+=1
        counts['conflicts']+=not q['compatible']
        counts['distance_reject']+=q['distance_reject']
        assert not (q['distance_reject'] and q['compatible'])
        if q['compatible'] and q['xy_overlap']:
            counts['oblique_only_compatible']+=1
            if q['angle_sum']==1:
                counts['equal_angle_oblique_only']+=1
                examples.setdefault('equal_angle_oblique_only',[i,j])
        if q['compatible'] and q['projection']<=F(101,100):
            counts['near_compatible']+=1
            assert q['angle_sum']<=F(51,50)
    result=dict(status='EXACT_SAMPLED_PAIR_DIAGNOSTIC',counts=counts,examples=examples,
                source=str(source),sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
                limitation='Endpoint pose samples only. Distance rejection is necessary, not sufficient; exact angle criterion is the existing SAT rewritten, not a stronger certificate.')
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(result,indent=2));print(json.dumps(result))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('source',type=Path);p.add_argument('out',type=Path)
    a=p.parse_args();run(a.source,a.out)
