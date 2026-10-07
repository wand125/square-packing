"""Finite-pose, nonadditive clique cuts. Never a continuous packing proof."""
import argparse
from fractions import Fraction as F
import hashlib
import importlib.util
from itertools import combinations
import json
from pathlib import Path
import time


def separated(s, t):
    """Exact SAT for unit squares in dual_exact's integer record format.

    Touching boundaries are allowed: separation uses >=, not >.
    """
    x,y,d,a,b,r = s[:6]
    X,Y,D,A,B,R = t[:6]
    dx,dy,den = X*d-x*D, Y*d-y*D, d*D
    dot,cross = abs(a*A+b*B), abs(a*B-b*A)
    rhs = den*(r*R+dot+cross)
    return (2*abs(a*dx+b*dy)*R >= rhs or
            2*abs(-b*dx+a*dy)*R >= rhs or
            2*abs(A*dx+B*dy)*r >= rhs or
            2*abs(-B*dx+A*dy)*r >= rhs)


def polygon(s):
    return [(F(x,s[7]),F(y,s[7])) for x,y in s[6]]


def intersection(poly, other):
    for a,b in zip(other,other[1:]+other[:1]):
        if not poly: break
        def side(p): return (b[0]-a[0])*(p[1]-a[1])-(b[1]-a[1])*(p[0]-a[0])
        out=[]
        for p,q in zip(poly,poly[1:]+poly[:1]):
            u,v=side(p),side(q)
            if u>=0:out.append(p)
            if u*v<0:
                z=u/(u-v);out.append(tuple(p[k]+z*(q[k]-p[k]) for k in (0,1)))
        poly=out
    return poly


def run(checker, support, out, gap=F(0)):
    from robust_conflict_cover import overlap_gap
    assert gap>=0
    out.mkdir(parents=True,exist_ok=False)
    started=time.monotonic()
    def save(stage, **extra):
        record=dict(operation='nonadditive_probe',status='RUNNING',stage=stage,updated_epoch=time.time());record.update(extra)
        (out/'progress.json').write_text(json.dumps(dict(records=[record]),indent=2))
        print(json.dumps(record),flush=True)
    spec=importlib.util.spec_from_file_location('external_dual',checker)
    ext=importlib.util.module_from_spec(spec);spec.loader.exec_module(ext);ext.set_t(F(4))
    unique={}
    M=F(1999999999,2000000000)
    for p,q,x,y,m in ext.read_exact_support(support):
        for X,Y,P,Q in ext.images(p,q,x,y):
            square=ext.make_square(X,Y,P,Q,0)
            key=(square[7],tuple(sorted(square[6])))
            if key not in unique:unique[key]=[square,F(0)]
            unique[key][1]+=m/8/M
    data=sorted(unique.values(),key=lambda v:v[1],reverse=True)
    squares=[v[0] for v in data];weights=[v[1] for v in data];n=len(data)
    assert sum(weights)==F(24537607710,1999999999)
    save('exact_pair_graph',vertices=n)
    conflicts=[0]*n;edges=0
    for i in range(n):
        for j in range(i):
            if gap:
                num,den=overlap_gap(squares[i],squares[j])
                conflict=num*gap.denominator>=gap.numerator*den
            else:
                conflict=not separated(squares[i],squares[j])
            if conflict:
                conflicts[i]|=1<<j;conflicts[j]|=1<<i;edges+=1
    (out/'poses.json').write_text(json.dumps([dict(square=s,dual_weight=str(w)) for s,w in data]))
    (out/'conflicts.json').write_text(json.dumps([hex(v) for v in conflicts]))
    save('greedy_conflict_cliques',vertices=n,conflict_edges=edges)
    cliques=set()
    # Each seed gives a pairwise-overlapping clique, prioritizing dual mass.
    for seed in range(n):
        chosen=[seed];remaining=conflicts[seed]
        while remaining:
            bit=remaining & -remaining;v=bit.bit_length()-1
            chosen.append(v);remaining &= conflicts[v]
        cliques.add(tuple(sorted(chosen)))
    cliques=sorted(cliques)
    loads=[sum(weights[v] for v in c) for c in cliques]
    best=max(range(len(cliques)),key=lambda i:loads[i]);cut=cliques[best]
    assert all(not separated(squares[i],squares[j]) for i,j in combinations(cut,2))
    common=polygon(squares[cut[0]])
    for v in cut[1:]:common=intersection(common,polygon(squares[v]))
    if loads[best]>1:assert not common,'Violates the externally rechecked point-load bound'
    (out/'cliques.json').write_text(json.dumps(cliques))
    (out/'strongest-cut.json').write_text(json.dumps(dict(vertices=cut,normalized_dual_load=str(loads[best]),pairwise_overlap_rechecked=True,common_intersection_empty=not common,rule='At most one of these fixed poses may occur in a packing.'),indent=2))
    save('finite_clique_cover_lp',cliques=len(cliques),violated_cuts=sum(v>1 for v in loads),strongest_load=float(loads[best]))
    # Cover every finite pose by pair-conflict cliques. Rational round-up of
    # nonnegative LP weights gives an exact upper bound on finite packings.
    import numpy as np
    from scipy.optimize import linprog
    from scipy.sparse import coo_matrix
    rows=[];cols=[]
    for j,c in enumerate(cliques):
        for i in c:rows.append(i);cols.append(j)
    a=coo_matrix((np.ones(len(rows)),(rows,cols)),shape=(n,len(cliques))).tocsc()
    fit=linprog(np.ones(len(cliques)),A_ub=-a,b_ub=-np.ones(n),bounds=(0,None),method='highs',options={'time_limit':60})
    assert fit.success,fit.message
    # Correct even a tiny primal residual using exact integer coverage.
    den=10**9;nums=[max(0,int(np.ceil(x*den))) for x in fit.x]
    coverage=[0]*n
    for c,w in zip(cliques,nums):
        for i in c:coverage[i]+=w
    floor=min(coverage);assert floor>0
    bound=F(sum(nums),floor)
    (out/'cover.json').write_text(json.dumps(dict(numerators=nums,denominator=floor,coverage_numerators=coverage,finite_upper_bound=str(bound)),indent=2))
    result=dict(status='FINITE_POSE_REVIEW_REQUIRED',vertices=n,conflict_edges=edges,required_gap=str(gap),
                point_dual_mass=str(sum(weights)),cliques=len(cliques),violated_cuts=sum(v>1 for v in loads),
                strongest_load=str(loads[best]),finite_upper_bound=str(bound),finite_upper_float=float(bound),
                integer_upper=bound.numerator//bound.denominator,seconds=time.monotonic()-started,
                limitation='Only the saved finite poses. No covering of all centres/angles, no proof of s(12)=4.',
                inputs={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in (checker,support)})
    (out/'result.json').write_text(json.dumps(result,indent=2))
    save('complete',status='STOPPED_FINITE_POSE_REVIEW',result=result)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--checker',type=Path,required=True);p.add_argument('--support',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--gap',type=F,default=F(0));a=p.parse_args();run(a.checker,a.support,a.out,a.gap)
