"""Exact convex-hull nonintersection constraints on distinct hypothetical boxes.
Search is bounded; incomplete search is UNKNOWN, never a rejection.
"""
from itertools import combinations
from functools import lru_cache
from pathlib import Path
from collections import Counter
from time import perf_counter
import json
from assignment_pilot import points,groups,cases,hull,inside,cross,compatible


def segments(h):
    if len(h)==1:return [(h[0],h[0])]
    if len(h)==2:return [(h[0],h[1])]
    return list(zip(h,h[1:]+h[:1]))


def intersects(a,b):
    if any(inside(a,p) for p in b) or any(inside(b,p) for p in a):return True
    for u,v in segments(a):
        for p,q in segments(b):
            c1,c2=cross(u,v,p),cross(u,v,q);c3,c4=cross(p,q,u),cross(p,q,v)
            if c1*c2<0 and c3*c4<0:return True
    return False


def solve(domains,conflict,limit=256):
    nodes=0
    def visit(ds):
        nonlocal nodes
        nodes+=1
        if nodes>limit:return 'UNKNOWN',None
        if not ds:return 'SAT',[]
        a=min(ds,key=lambda x:(len(ds[x]),x));options=ds[a]
        if not options:return 'UNSAT',dict(row=a,children=[])
        children=[]
        for b in options:
            nd={x:[y for y in ys if y!=b and not conflict((a,b),(x,y))] for x,ys in ds.items() if x!=a}
            status,payload=visit(nd)
            if status=='SAT':return status,[(a,b)]+payload
            if status=='UNKNOWN':return status,None
            children.append(dict(blue=b,tree=payload))
        return 'UNSAT',dict(row=a,children=children)
    status,payload=visit(domains)
    return dict(status=status,nodes=nodes,assignment=payload if status=='SAT' else None,
                proof_tree=payload if status=='UNSAT' else None)


def replay(tree,domains,conflict):
    row=tree['row'];assert row in domains
    children=tree['children'];assert [v['blue'] for v in children]==domains[row]
    for child in children:
        b=child['blue'];nd={x:[y for y in ys if y!=b and not conflict((row,b),(x,y))] for x,ys in domains.items() if x!=row}
        replay(child['tree'],nd,conflict)


def model(data):
    rp,bp=points(0),points(1);rg,bg=groups(rp),groups(bp)
    comp={tuple(pair) for pair in data['compatible_pairs']}
    shapes={edge:hull([rp[i] for i in rg[edge[0]]]+[bp[i] for i in bg[edge[1]]]) for edge in comp}
    @lru_cache(None)
    def conflict(a,b):return intersects(shapes[a],shapes[b])
    return cases(rg,32),cases(bg,32),comp,conflict


def domains_for(entry,rc,bc,comp):
    r,b=rc[entry['red_case']],bc[entry['blue_case']];forced=entry['links']
    return {a:[bb for bb in b['groups'] if (a,bb) in comp and all((a!=x and bb!=y) or (a==x and bb==y) for x,y in forced)] for a in r['groups']}


def main():
    started=perf_counter();root=Path('runs/bentz_assignment_20260926');data=json.loads((root/'results.json').read_text())
    rc,bc,comp,conflict=model(data);records=[];stats=Counter()
    for entry in data['results'][1]['records']:
        if entry['status']!='UNRESOLVED':continue
        domains=domains_for(entry,rc,bc,comp)
        result=solve(domains,conflict)
        if result['status']=='UNSAT':replay(result['proof_tree'],domains,conflict)
        elif result['status']=='SAT':
            pairs=[tuple(x) for x in result['assignment']]
            assert len(pairs)==32 and len({b for a,b in pairs})==32
            assert all(b in domains[a] for a,b in pairs)
            assert not any(conflict(a,b) for a,b in combinations(pairs,2))
        result.update(red_case=entry['red_case'],blue_case=entry['blue_case']);records.append(result);stats[result['status']]+=1
    result=dict(seconds=perf_counter()-started,counts=dict(stats),records=records,
                scope='SAT is only a disjoint-hull incidence assignment, not square packability. UNSAT inherits conditional motion premises. UNKNOWN remains unresolved.')
    (root/'conflicts.json').write_text(json.dumps(result,indent=2))
    print(json.dumps({k:v for k,v in result.items() if k!='records'}),flush=True)


if __name__=='__main__':main()
