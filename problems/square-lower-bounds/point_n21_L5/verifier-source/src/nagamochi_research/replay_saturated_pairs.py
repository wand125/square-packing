"""Replay conditional two-band saturation bounds using exact arithmetic.

Unproved pair cases remain compatible. No numerical solver is called during
replay; saved Farkas trees are checked against regenerated geometric models.
"""
from fractions import Fraction as F
from itertools import combinations
import json
from pathlib import Path
from fixed_orientation_cover import angle_envelope
from joint_angle_lp import rotation
from saturated_axis_cells import build
from saturated_joint_search import replay_case


def static_exclusions(pieces,t,R):
    c,s=rotation(t)
    spans=[[(min(a*x+b*y for x,y in p),max(a*x+b*y for x,y in p))
            for a,b in ((c,s),(-s,c))] for p in pieces]
    return { (i,j) for i,j in combinations(range(len(pieces)),2)
        if all(max(spans[i][v][1]-spans[j][v][0],spans[j][v][1]-spans[i][v][0])<R for v in (0,1)) }


def clique_upper(N,excluded):
    # Dynamic exhaustive subset enumeration with exact integer bit masks.
    compatible=[sum(1<<j for j in range(N) if j!=i and tuple(sorted((i,j))) not in excluded) for i in range(N)]
    if N>20:
        best=0
        def visit(candidates,count):
            nonlocal best
            best=max(best,count)
            while candidates and count+candidates.bit_count()>best:
                bit=candidates&-candidates;candidates^=bit;i=bit.bit_length()-1
                visit(candidates&compatible[i],count+1)
        visit((1<<N)-1,0)
        return best
    clique=[False]*(1<<N);clique[0]=True;upper=0
    for mask in range(1,1<<N):
        bit=mask&-mask;rest=mask^bit;i=bit.bit_length()-1
        if clique[rest] and not (rest&~compatible[i]):
            clique[mask]=True;upper=max(upper,mask.bit_count())
    return upper


def verify(q):
    k=q['k']; L=F(q['L']); t=F(q['t'])
    A=F(q.get('axis_inner','1')); R=F(q.get('rot_inner','1'))
    H=None if q.get('rot_half') is None else F(q['rot_half'])
    assert 0<R<=1 and (L-1)/(k-1)<A
    if 'axis_h' in q:
        ah=F(q['axis_h']); rh=F(q['rot_h'])
        assert 0<=ah<=F(2,5) and rh>=0
        E,span=angle_envelope(t,rh)
        assert A*(1+2*ah)<1 and R*E<1
        assert H is not None and H>=(L-span)/2
    else:
        assert A==R==1 and H is None
    missing=q.get('missing',[])
    pieces,_=build(L,t,k,A,R,H,missing); N=len(pieces)
    assert N==q['regions']
    c,s=rotation(t)
    for p in pieces:
        # A point belongs to at least one residual piece. Two boxes cannot
        # share any piece, even when the closed pieces overlap at boundaries.
        for a,b in ((c,s),(-s,c)):
            vals=[a*x+b*y for x,y in p]
            assert max(vals)-min(vals)<R
    excluded=static_exclusions(pieces,t,R) if q.get('use_static_exclusions',False) else set();seen=set()
    for case in q['cases']:
        edge=tuple(case['chosen'])
        assert len(edge)==2 and 0<=edge[0]<edge[1]<N and edge not in seen
        seen.add(edge)
        assert case['k']==k and F(case['L'])==L and F(case['t'])==t
        assert case.get('missing',[])==missing
        assert F(case.get('axis_inner','1'))==A and F(case.get('rot_inner','1'))==R
        assert (None if case.get('rot_half') is None else F(case['rot_half']))==H
        if replay_case(case):excluded.add(edge)
    assert excluded==set(map(tuple,q['excluded_pairs']))
    # Exhaustive finite check independent of the search's clique algorithm.
    upper=clique_upper(N,excluded)
    assert upper==q.get('rotated_count_upper',q.get('maximum_possible_rotated_count'))
    return dict(k=k,L=str(L),missing=missing,regions=N,exact_excluded_pairs=len(excluded),rotated_count_upper=upper)


if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('files',type=Path,nargs='+');args=p.parse_args()
    for path in args.files:
        print(json.dumps(dict(file=str(path),**verify(json.loads(path.read_text())))),flush=True)
