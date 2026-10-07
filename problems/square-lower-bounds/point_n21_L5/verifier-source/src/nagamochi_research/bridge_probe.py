"""Two concrete bridges: closed-cover accounting and incidence -> charge atom.
No continuous cover verification or new packing bound is performed here.
"""
from fractions import Fraction as F
from itertools import combinations
from pathlib import Path
from collections import Counter
import hashlib,json,random
from assignment_pilot import hull,inside,cross,points,groups,SCALE
from assignment_conflicts import segments

ROOT=Path('runs/exact_rational_bridge_20260926')


def intersection(a,b):
    ps={p for p in a if inside(b,p)}|{p for p in b if inside(a,p)}
    for u,v in segments(a):
        for p,q in segments(b):
            d=(v[0]-u[0],v[1]-u[1]);e=(q[0]-p[0],q[1]-p[1]);den=d[0]*e[1]-d[1]*e[0]
            if not den:continue
            w=(p[0]-u[0],p[1]-u[1]);t=F(w[0]*e[1]-w[1]*e[0],den);s=F(w[0]*d[1]-w[1]*d[0],den)
            if 0<=t<=1 and 0<=s<=1:ps.add((u[0]+t*d[0],u[1]+t*d[1]))
    return hull(ps) if ps else []


def charge_atom(seed=62671):
    data=json.loads(Path('runs/bentz_assignment_20260926/results.json').read_text());rp,bp=points(0),points(1);rg,bg=groups(rp),groups(bp)
    shapes=[hull([rp[i] for i in rg[a]]+[bp[i] for i in bg[b]]) for a,b in data['compatible_pairs']]
    rng=random.Random(seed);cache={}
    def meet(i,j):
        key=tuple(sorted((i,j)))
        if key not in cache:cache[key]=intersection(shapes[i],shapes[j])
        return cache[key]
    for attempt in range(1500):
        selected=[rng.randrange(len(shapes))]
        for j in rng.sample(range(len(shapes)),len(shapes)):
            if j not in selected and all(meet(i,j) for i in selected):selected.append(j)
            if len(selected)==4:break
        if len(selected)<4:continue
        common=shapes[selected[0]]
        for i in selected[1:]:
            common=intersection(common,shapes[i]) if common else []
        if common:continue
        witnesses=[];winning=[[] for i in range(4)]
        for i,j in combinations(range(4),2):
            poly=meet(selected[i],selected[j]);pt=tuple(sum(F(p[a]) for p in poly)/len(poly) for a in (0,1))
            if pt in witnesses:break
            index=len(witnesses);witnesses.append(pt);winning[i].append(index);winning[j].append(index)
        if len(witnesses)!=6:continue
        assert all(set(a)&set(b) for a,b in combinations(winning,2))
        assert not set.intersection(*(set(a) for a in winning))
        assert all(inside(shapes[selected[i]],witnesses[j]) for i,bag in enumerate(winning) for j in bag)
        # Four winning traces weighted 1/2 use every virtual site exactly once.
        # Thus additive weights covering all four traces cost >=2; clique budget=1.
        assert all(sum(j in bag for bag in winning)==2 for j in range(6))
        return dict(original_incidence_pairs=[data['compatible_pairs'][i] for i in selected],
                    original_hulls=[[[str(F(x,SCALE)),str(F(y,SCALE))] for x,y in shapes[i]] for i in selected],
                    sites=[[str(x/SCALE),str(y/SCALE)] for x,y in witnesses],winning_subsets=winning,
                    budget=1,three_of_six_budget=2,additive_trace_cover_lower_bound=2,
                    scope='Valid rational intersecting-rule candidate. Coverage, D4 orbit and LP usefulness are not yet verified.')
    raise RuntimeError('No suitable clique found in bounded search')


def cover_accounting():
    path=ROOT/'external/evand/s12/certificates/rung2/s13_closed_cover_4.txt';tokens=list(map(int,path.read_text().split()))
    a,b,d,w,n=tokens[:5];assert (a,b,d,w,n)==(4,1,1000,10**9,3621) and len(tokens)==5+3*n
    pts=[tuple(tokens[i:i+3]) for i in range(5,len(tokens),3)]
    assert all(0<=x<=4*d and 0<=y<=4*d and v>=0 for x,y,v in pts)
    total=F(sum(v for x,y,v in pts),w);assert total==F(2591194431,200000000)
    closed=[];eroded=[];eps=F(1,10**8)
    for i in range(4):
        for j in range(4):
            closed.append(F(sum(v for x,y,v in pts if i*d<=x<=(i+1)*d and j*d<=y<=(j+1)*d),w))
            eroded.append(F(sum(v for x,y,v in pts if F(i)+eps<=F(x,d)<=F(i+1)-eps and F(j)+eps<=F(y,d)<=F(j+1)-eps),w))
    multiplicity=Counter()
    for x,y,v in pts:
        count=sum(i*d<=x<=(i+1)*d and j*d<=y<=(j+1)*d for i in range(4) for j in range(4))
        multiplicity[count]+=v
    assert sum(closed)==sum(F(k*v,w) for k,v in multiplicity.items())
    return dict(sha256=hashlib.sha256(path.read_bytes()).hexdigest(),points=n,total=total,
                minimum_closed_tile=min(closed),minimum_eroded_tile=min(eroded),eroded_side=1-2*eps,
                eroded_argmin_tile=[eroded.index(min(eroded))//4,eroded.index(min(eroded))%4],closed_tile_sum=sum(closed),
                mass_by_tile_multiplicity={k:F(v,w) for k,v in multiplicity.items()},
                scope='Exact file accounting and 16 tile probes only. External full-domain audits were not rerun.')


if __name__=='__main__':
    ROOT.mkdir(parents=True,exist_ok=True)
    result=dict(closed_cover=cover_accounting(),charge_atom=charge_atom())
    (ROOT/'bridge-results.json').write_text(json.dumps(result,default=str,indent=2))
    print(json.dumps(result,default=str,indent=2))
