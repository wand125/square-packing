"""Geometric conflict graph -> Boolean union charge with certified rank budget.
One firing event is selected per disjoint square. These events form an
independent set, so an exact independent-set bound is a global charge budget.
"""
import os
for k in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','VECLIB_MAXIMUM_THREADS'):os.environ[k]='1'
from pathlib import Path
from itertools import combinations
from fractions import Fraction as F
from time import perf_counter
import random,json
from assignment_pilot import points,groups,hull,SCALE
from assignment_conflicts import intersects

ROOT=Path('runs/conflict_rank_20260926')

def independence(edges,n):
    valid=[mask for mask in range(1<<n) if all(not(mask>>a&1 and mask>>b&1) for a,b in edges)]
    return max(mask.bit_count() for mask in valid)

def induced_cycles(adj,count=8):
    rng=random.Random(92726);found=set();n=len(adj)
    for _ in range(100000):
        path=[rng.randrange(n)]
        for step in range(4):
            opts=[j for j in adj[path[-1]] if j not in path and all((j not in adj[p]) for p in path[:-1] if not(step==3 and p==path[0])) and (step!=3 or j in adj[path[0]])]
            if not opts:break
            path.append(rng.choice(sorted(opts)))
        if len(path)==5:
            found.add(tuple(sorted(path)))
            if len(found)>=count:break
    return sorted(found)

def main():
    start=perf_counter();ROOT.mkdir(exist_ok=False)
    d=json.loads(Path('runs/bentz_assignment_20260926/results.json').read_text());rp,bp=points(0),points(1);rg,bg=groups(rp),groups(bp)
    bags=[sorted(set([rp[i] for i in rg[a]]+[bp[j] for j in bg[b]])) for a,b in d['compatible_pairs']]
    shapes=[hull(b) for b in bags];boxes=[(min(x for x,y in h),max(x for x,y in h),min(y for x,y in h),max(y for x,y in h)) for h in shapes]
    adj=[set() for _ in shapes]
    for i,j in combinations(range(len(shapes)),2):
        a,b=boxes[i],boxes[j]
        if a[0]>b[1] or b[0]>a[1] or a[2]>b[3] or b[2]>a[3]:continue
        if intersects(shapes[i],shapes[j]):adj[i].add(j);adj[j].add(i)
    cycles=induced_cycles(adj);records=[]
    for ids in cycles:
        edges=[(a,b) for a,b in combinations(range(5),2) if ids[b] in adj[ids[a]]]
        assert len(edges)==5 and all(sum(i in e for e in edges)==2 for i in range(5))
        budget=independence(edges,5);assert budget==2
        records.append(dict(source_ids=ids,bags=[[[str(F(x,SCALE)),str(F(y,SCALE))] for x,y in bags[i]] for i in ids],edges=edges,budget=budget))
    result=dict(events=len(bags),edges=sum(map(len,adj))//2,cycles=records,seconds=perf_counter()-start,scope='Global rank budgets for Boolean union charges; covering efficacy not yet certified.')
    (ROOT/'rules.json').write_text(json.dumps(result,indent=2));print(json.dumps({k:v for k,v in result.items() if k!='cycles'}),len(records),flush=True)

if __name__=='__main__':main()
