"""Extend a finite conflict clique to a rigorously bounded union of pose cells."""
import json,argparse
from pathlib import Path
from fractions import Fraction as F
from itertools import combinations
from dual_conflict_probe import polygon,intersection,separated


def margin(s,q):
    x,y,d,a,b,r=s[:6];dx=q[0]-F(x,d);dy=q[1]-F(y,d)
    return min(F(1,2)-abs(a*dx+b*dy)/r,F(1,2)-abs(-b*dx+a*dy)/r)


def rule(source,out):
    poses=json.loads((source/'poses.json').read_text())
    cut=json.loads((source/'strongest-cut.json').read_text())['vertices']
    chosen=[];weight=F(0)
    for i in sorted(cut,key=lambda i:F(poses[i]['dual_weight']),reverse=True):
        chosen.append(i);weight+=F(poses[i]['dual_weight'])
        if weight>1:break
    assert weight>1
    squares=[poses[i]['square'] for i in chosen];witnesses=[];m=F(1,2)
    for i,j in combinations(range(len(squares)),2):
        a,b=squares[i],squares[j];assert not separated(a,b)
        poly=intersection(polygon(a),polygon(b));assert poly
        q=tuple(sum(p[k] for p in poly)/len(poly) for k in (0,1))
        slack=min(margin(a,q),margin(b,q));assert slack>0
        m=min(m,slack)
        witnesses.append(dict(i=i,j=j,q=list(map(str,q)),slack=str(slack)))
    h=m/36
    # For cos(t)=(1-t²)/(1+t²), sin(t)=2t/(1+t²), both derivatives
    # have absolute value <=2 for all real t. With original q,c in [0,4]²,
    # |projection change| <= 2h + 2h*(|qx-cx|+|qy-cy|) <=18h.
    # Thus each saved q remains strictly inside BOTH independently moved
    # squares for |dcx|,|dcy|,|dt|<=h. For two squares in the same cell,
    # use the original centre q and slack 1/2. Therefore at most one square
    # can lie in the union of these pose cells, including boundary poses.
    assert 18*h<m and h<F(1,36)
    cells=[]
    for i,s in zip(chosen,squares):
        x,y,d,a,b,r=s[:6];assert r+a!=0
        cells.append(dict(pose=i,cx=str(F(x,d)),cy=str(F(y,d)),t=str(F(b,r+a))))
    result=dict(status='EXACT_LOCAL_NONADDITIVE_RULE',cells=cells,coordinate_radius=str(h),minimum_slack=str(m),dual_load=str(weight),pair_witnesses=witnesses,
                theorem='At most one unit square with (cx,cy,t) in this union of closed coordinate cubes may occur in an interior-disjoint packing.',
                scope='All real parameters inside these cells, not all container poses. No global n12 packing bound.')
    out.write_text(json.dumps(result,indent=2));print(json.dumps(dict(cells=len(cells),radius=float(h),dual_load=float(weight))))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('source',type=Path);p.add_argument('out',type=Path);a=p.parse_args();rule(a.source,a.out)
