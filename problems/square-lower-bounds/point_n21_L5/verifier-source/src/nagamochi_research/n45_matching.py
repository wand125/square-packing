"""Conditional n45 incidence relaxation, with exact hull conflict replay.
Every hypothetical box must capture >=1 red and >=1 blue point strictly.
This premise is NOT proved here. SAT is not a square packing.
"""
from collections import Counter
from functools import lru_cache
from itertools import combinations
from pathlib import Path
from time import perf_counter
import argparse
import json
import random
from fractions import Fraction as F
from motion_pilot import rows
from n45_small_motion import heights
from assignment_pilot import hull, inside, match
from assignment_conflicts import intersects, solve, replay

ROOT = Path('runs/n45_matching_20260926')
SCALE = 1000
DIAMETER_SQ = 2 * 1010**2


def orientation_impossible(ps, depth=12):
    """Certify NO orientation with projection spans < 1010 (integer units).

    Rational t=tan(theta/2) in [-1/2,1/2] covers square orientations
    theta in [-pi/4,pi/4]. A branch dies only when one necessary strict
    quadratic inequality is nonnegative throughout it (Bernstein bound).
    Undecided branches are retained. This ignores container constraints.
    """
    polys=[]
    for a,b in combinations(ps,2):
        dx,dy=a[0]-b[0],a[1]-b[1]
        for x,y in ((dx,dy),(dy,-dx)):
            for sign in (-1,1):
                polys.append((sign*x-1010,2*sign*y,-sign*x-1010))
    def excluded(lo,hi):
        for c,b,a in polys:
            q0=c+b*lo+a*lo*lo
            q1=q0+(hi-lo)*(b+2*a*lo)/2
            q2=c+b*hi+a*hi*hi
            if min(q0,q1,q2)>=0: return True
        return False
    def visit(lo,hi,d):
        if excluded(lo,hi): return True
        mid=(lo+hi)/2
        # One exact feasible orientation suffices to retain this bag.
        if all(c+b*mid+a*mid*mid<0 for c,b,a in polys): return False
        if d==0: return False
        return visit(lo,mid,d-1) and visit(mid,hi,d-1)
    return visit(F(-1,2),F(1,2),depth)


def model(focus=None, geometry=False):
    ys = None if focus is None else heights(focus)[0]
    def integral(p):
        p = tuple(v*SCALE for v in p)
        assert all(v.denominator == 1 for v in p)
        return tuple(int(v) for v in p)
    rp, bp = [list(map(integral, rows(7, ys, c))) for c in (0, 1)]
    assert (len(rp), len(bp)) == (45, 46)
    def close(ps):
        return all(sum((a[j]-b[j])**2 for j in (0,1)) < DIAMETER_SQ
                   for a,b in combinations(ps, 2))
    bg = [(i,) for i in range(46)] + [p for p in combinations(range(46),2)
                                     if close([bp[i] for i in p])]
    cases = [dict(empty=[i],pair=[],groups=[j for j in range(46) if j != i]) for i in range(46)]
    cases += [dict(empty=[],pair=list(g),groups=[j for j in range(46) if j not in g]+[b])
              for b,g in enumerate(bg) if len(g)==2]
    shapes = {}
    for a in range(45):
        for b,g in enumerate(bg):
            ps = [rp[a]] + [bp[i] for i in g]
            if not close(ps): continue
            h = hull(ps)
            if any(inside(h,p) for i,p in enumerate(rp) if i != a): continue
            if any(inside(h,p) for i,p in enumerate(bp) if i not in g): continue
            if geometry and orientation_impossible(ps): continue
            shapes[a,b] = h
    @lru_cache(None)
    def conflict(a,b): return intersects(shapes[a], shapes[b])
    return rp,bp,bg,cases,shapes,conflict


def run(focus=None, limit=256, geometry=False, restarts=0):
    start = perf_counter()
    rp,bp,bg,cases,shapes,conflict = model(focus, geometry)
    records=[]; counts=Counter()
    for i,case in enumerate(cases):
        domains={a:[b for b in case['groups'] if (a,b) in shapes] for a in range(45)}
        assignment,hall=match(domains,range(45))
        if hall:
            assert set(hall['neighbors']) == {b for a in hall['left'] for b in domains[a]}
            assert len(hall['neighbors']) < len(hall['left'])
            result=dict(status='HALL_UNSAT',hall=hall)
        else:
            result=solve(domains,conflict,limit)
            total_nodes=result['nodes']; retries=0
            rng=random.Random(945000+i)
            while result['status']=='UNKNOWN' and retries<restarts:
                shuffled={a:rng.sample(bs,len(bs)) for a,bs in domains.items()}
                result=solve(shuffled,conflict,256)
                total_nodes+=result['nodes']; retries+=1
                if result['status']=='UNSAT': replay(result['proof_tree'],shuffled,conflict)
            result['total_nodes']=total_nodes;result['retries']=retries
            if result['status']=='UNSAT' and retries==0: replay(result['proof_tree'],domains,conflict)
            if result['status']=='SAT':
                edges=[tuple(e) for e in result['assignment']]
                assert len(edges)==45 and len({a for a,b in edges})==45 and len({b for a,b in edges})==45
                assert all(b in domains[a] for a,b in edges)
                assert not any(conflict(a,b) for a,b in combinations(edges,2))
            result['matching_conflicts']=sum(conflict(a,b) for a,b in combinations(list(assignment.items()),2))
        result.update(case=i,empty=case['empty'],pair=case['pair'])
        records.append(result); counts[result['status']]+=1
    output=dict(focus=focus, geometry=geometry,side_upper='101/100',points_scale=SCALE,
                premise='Every box contains at least one red and one blue point strictly; not proved here.',
                scope='Separate static layouts. SAT is disjoint hulls only; UNKNOWN is unresolved. No motion links imposed.',
                cases=len(cases),compatible_edges=len(shapes),node_limit=limit,restarts=restarts,counts=dict(counts),
                seconds=perf_counter()-start,records=records)
    ROOT.mkdir(exist_ok=True)
    name='baseline' if focus is None else f'focus{focus}'
    (ROOT/f'{name}-geom{int(geometry)}-limit{limit}-retry{restarts}.json').write_text(json.dumps(output,indent=2))
    print(json.dumps({k:v for k,v in output.items() if k!='records'}),flush=True)
    return output

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--focus',type=int);p.add_argument('--limit',type=int,default=256)
    p.add_argument('--geometry',action='store_true')
    p.add_argument('--restarts',type=int,default=0)
    a=p.parse_args();run(a.focus,a.limit,a.geometry,a.restarts)
