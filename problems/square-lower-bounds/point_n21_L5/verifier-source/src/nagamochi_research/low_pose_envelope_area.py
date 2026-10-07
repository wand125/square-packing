"""Area of an outer union confines low-capture physical unit squares.

No common-core covering is needed. Area is an upper bound on the number of
interior-disjoint unit squares lying entirely in the union, not on centres.
"""
from pathlib import Path
from fractions import Fraction as F
from collections import defaultdict
import argparse,json,hashlib,time
from correlated_pose_core import coefficient_vertices


def envelope(L,box):
    x0,x1,y0,y1,t0,t1=box
    # Max of the convex function |c|+|s| over the coefficient polygon is
    # attained at a vertex; the actual rotation arc is contained in it.
    radius=max(abs(c)+abs(s) for c,s in coefficient_vertices(t0,t1))/2
    return max(F(0),x0-radius),min(L,x1+radius),max(F(0),y0-radius),min(L,y1+radius)


def union_area(rectangles):
    events=defaultdict(list)
    for a,b,c,d in set(rectangles):
        if a>=b or c>=d:continue
        events[a].append(((c,d),1));events[b].append(((c,d),-1))
    active=defaultdict(int);previous=None;total=F(0)
    for x in sorted(events):
        if previous is not None:
            length=F(0);end=None
            for a,b in sorted(k for k,v in active.items() if v):
                if end is None or a>end:length+=b-a;end=b
                elif b>end:length+=b-end;end=b
            total+=(x-previous)*length
        for interval,delta in events[x]:
            active[interval]+=delta
            assert active[interval]>=0
            if not active[interval]:del active[interval]
        previous=x
    assert not active
    return total


def run(candidate,cover_path,out,thresholds):
    from mixed_density_check import expand
    model=expand(json.loads(candidate.read_text()));q=json.loads(cover_path.read_text())
    assert q['digest']==model[-1];L=model[0];start=time.monotonic();records=[]
    for threshold in thresholds:
        paths=[p for p,r in q['leaves'].items() if r['kind']!='OUTSIDE' and F(r['lower'])<threshold]
        rectangles=[envelope(L,tuple(map(F,q['leaves'][p]['box']))) for p in paths]
        value=union_area(rectangles)
        records.append(dict(threshold=str(threshold),cells=len(paths),area=str(value),capacity=value.numerator//value.denominator))
        print(records[-1],flush=True)
    result=dict(source_sha256=hashlib.sha256(cover_path.read_bytes()).hexdigest(),records=records,
                seconds=time.monotonic()-start,scope='Exact envelope union calculation; source pose-cover replay is a separate required premise.',general_packing_exclusion=False)
    out.write_text(json.dumps(result,indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser()
    for name in ('candidate','cover','out'):p.add_argument(name,type=Path)
    p.add_argument('--thresholds',nargs='+',type=F,default=[F(3,10),F(1,2),F(7,10),F(4,5)])
    a=p.parse_args();run(a.candidate,a.cover,a.out,a.thresholds)
