"""Independent denser/time holdout and triangle-edge audit for elastic paths."""
from fractions import Fraction as F
from itertools import combinations
from math import sqrt
from pathlib import Path
from collections import Counter
from time import perf_counter
import json
from motion_pilot import rows,strict_contains,probe
from score import square
from elastic_motion import snapshot,frozen_row_for
from support_pilot import holdout


def near_pair_hole(points):
    for i,j in combinations(range(len(points)),2):
        a,b=points[i],points[j];dx,dy=b[0]-a[0],b[1]-a[1];norm=dx*dx+dy*dy
        if not 1<norm<F(121,100):continue
        if dx<0:dx,dy=-dx,-dy
        t=F(float(dy)/(sqrt(float(norm))+float(dx))).limit_denominator(10**10)
        poly=square((a[0]+b[0])/2,(a[1]+b[1])/2,1+F(1,10**10),t)
        if all(0<=x<=6 and 0<=y<=6 for x,y in poly) and not any(strict_contains(poly,p) for p in points):
            return dict(cx=(a[0]+b[0])/2,cy=(a[1]+b[1])/2,delta=F(1,10**10),t=t)
    return None


def triangle_edges(colour):
    base=rows(6,colour=colour);edges=set()
    rowids=[[i for i,p in enumerate(base) if p[1]==F(457,500)+r*F(1043,1250)] for r in range(6)]
    for r in range(5):
        short,long=(rowids[r],rowids[r+1]) if len(rowids[r])==5 else (rowids[r+1],rowids[r])
        for j in range(5):
            tri=(short[j],long[j],long[j+1]);edges.update(tuple(sorted(e)) for e in combinations(tri,2))
        for j in range(4):
            tri=(short[j],short[j+1],long[j+1]);edges.update(tuple(sorted(e)) for e in combinations(tri,2))
    return sorted(edges)


def main():
    start=perf_counter();root=Path('runs/bentz_local_motion_20260926');out=[]
    checks=holdout(6,713982)+holdout(6,168253)
    for c in (0,1):
        edges=triangle_edges(c)
        for focus in range(6):
            record=dict(colour=c,focus=focus,compression=F(1,1000),snapshots=[],status='FINITE_PASS_NOT_PROOF')
            for phase in ('vertical','row-left','leftmost-right'):
                if phase!='vertical' and (c+focus)%2==0:continue
                for time in (F(1,7),F(1,3),F(2,3),F(6,7),F(1)):
                    ps=snapshot(c,focus,F(1,1000),time,phase)
                    maxedge=max(sum((ps[i][a]-ps[j][a])**2 for a in (0,1)) for i,j in edges)
                    pose=near_pair_hole(ps)
                    if pose is None:
                        test=probe(ps,checks)
                        if test['status']=='EXACT_EMPTY_OPEN_SQUARE':pose=test['pose']
                    e=dict(phase=phase,time=time,max_triangle_edge_sq=maxedge)
                    if pose is not None:
                        e['empty_pose']=pose;record['snapshots'].append(e);record['status']='EXACT_REJECTED';break
                    e['holdout_samples']=len(checks);record['snapshots'].append(e)
                if record['status']=='EXACT_REJECTED':break
            out.append(record)
    data=dict(records=out,seconds=perf_counter()-start,counts=dict(Counter(r['status'] for r in out)))
    (root/'elastic-audit.json').write_text(json.dumps(data,default=str,indent=2))
    print(json.dumps({k:v for k,v in data.items() if k!='records'}))


if __name__=='__main__':main()
