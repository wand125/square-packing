"""Dual-guided search of geometric event cliques and induced five-cycles.
Float scores only guide search; retained budgets and loads use exact arithmetic.
"""
from pathlib import Path
from fractions import Fraction as F
from itertools import combinations
from time import perf_counter
import json,random
import numpy as np
from conflict_rank import independence
from assignment_pilot import points,groups,hull,SCALE
from assignment_conflicts import intersects
from bridge_lp import hits_exact,transform
from conflict_rank_lp import canon,orbit

ROOT=Path('runs/conflict_guided_20260926')

def main():
    import argparse
    ap=argparse.ArgumentParser();ap.add_argument("--mode",choices=["incidence","dual"],default="incidence");ap.add_argument("--keep",type=int,default=1);args=ap.parse_args()
    root=ROOT if args.mode=="incidence" else Path("runs/conflict_guided_dual_20260926")
    if args.keep>1:root=root.with_name(root.name+"_batch")
    start=perf_counter();root.mkdir(exist_ok=False)
    base=json.loads(Path('runs/bridge_selected_20260926/results.json').read_text());lp=json.loads(Path('runs/conflict_rank_20260926/lp.json').read_text());data=json.loads(Path('runs/bentz_assignment_20260926/results.json').read_text())
    pts=[tuple(map(F,p)) for p in base['points']];idx={p:i for i,p in enumerate(pts)}
    dual=[(tuple(map(F,w['pose'])),F(w['weight'])) for w in lp['results']['rank_cycles']['dual']]
    hit=np.asarray([hits_exact(p,pts) for p,w in dual],dtype=bool);weights=np.asarray([float(w) for p,w in dual])
    rp,bp=points(0),points(1);rg,bg=groups(rp),groups(bp)
    ibags=[sorted(set([rp[i] for i in rg[a]]+[bp[j] for j in bg[b]])) for a,b in data['compatible_pairs']]
    bags=[[(F(x,SCALE),F(y,SCALE)) for x,y in bag] for bag in ibags]
    if args.mode=='dual':
        pool=set()
        for h in hit:
            captured=[i for i,v in enumerate(h) if v]
            for size in (2,3):
                pool.update(tuple(c) for c in combinations(captured,size))
        rng_pool=random.Random(92802)
        pool=sorted(pool)
        if len(pool)>1200:pool=sorted(rng_pool.sample(pool,1200))
        bags=[[pts[i] for i in bag] for bag in pool]
        ibags=bags
        print('dual-derived events',len(bags),flush=True)
    shapes=[hull(b) for b in ibags];bounds=[(min(x for x,y in h),max(x for x,y in h),min(y for x,y in h),max(y for x,y in h)) for h in shapes];adj=[set() for _ in bags]
    for i,j in combinations(range(len(bags)),2):
        a,b=bounds[i],bounds[j]
        if a[0]>b[1] or b[0]>a[1] or a[2]>b[3] or b[2]>a[3]:continue
        if intersects(shapes[i],shapes[j]):adj[i].add(j);adj[j].add(i)
    captures=np.asarray([[np.all(hit[:,[idx[transform(p,g)] for p in bag]],axis=1) for g in range(8)] for bag in bags])
    node_scores=np.sum(captures*weights,axis=(1,2));rng=random.Random(92801)
    best={};seen=set();tested=0
    def record(ids,kind,rank):
        nonlocal tested
        ids=tuple(sorted(ids))
        if ids in seen:return
        seen.add(ids);tested+=1
        # Eight images counted with multiplicity in scout; ratio unchanged for stabilizers.
        load=float(np.sum(np.any(captures[list(ids)],axis=0)*weights));ratio=load/(8*rank)
        entries=best.setdefault(kind,[]);entries.append((ratio,ids));entries.sort(reverse=True);del entries[args.keep:]
    for attempt in range(12000):
        first=rng.choices(range(len(bags)),weights=node_scores+.05,k=1)[0];path=[first]
        for step in range(4):
            opts=[j for j in adj[path[-1]] if j not in path and all(j not in adj[p] for p in path[:-1] if not(step==3 and p==path[0])) and (step!=3 or j in adj[path[0]])]
            if not opts:break
            opts.sort();candidate=rng.choices(opts,weights=[node_scores[j]+.1 for j in opts],k=1)[0];path.append(candidate)
        if len(path)==5:record(path,'cycle5',2)
        if attempt<2000:
            clique=[first];opts=set(adj[first])
            while opts and len(clique)<6:
                choices=sorted(opts);j=rng.choices(choices,weights=[node_scores[j]+.1 for j in choices],k=1)[0];clique.append(j);opts&=adj[j]
                record(clique,'clique',1)
    retained=[]
    for kind,entries in best.items():
      for ratio,ids in entries:
          edges=[(i,j) for i,j in combinations(range(len(ids)),2) if ids[j] in adj[ids[i]]];rank=independence(edges,len(ids))
          rule=[bags[i] for i in ids];images=sorted(orbit(rule));load=F(0)
          for image in images:
              for pose,w in dual:
                  h=hits_exact(pose,pts)
                  if any(all(h[idx[p]] for p in bag) for bag in image):load+=w
          cost=rank*len(images)
          retained.append(dict(kind=kind,source_ids=ids,bags=[[[str(x),str(y)] for x,y in b] for b in rule],edges=edges,rank=rank,orbit_size=len(images),cost=cost,dual_load=str(load),reduced_cost=str(cost-load),ratio=float(load/cost)))
    out=dict(mode=args.mode,keep=args.keep,events=len(bags),dual_poses=len(dual),nonzero_event_scores=int(sum(node_scores>0)),tested_unique=tested,attempts=12000,best=retained,seconds=perf_counter()-start,scope='Bounded heuristic candidate search with exact retained loads and ranks; no complete pricing or coverage claim.')
    (root/'results.json').write_text(json.dumps(out,indent=2));print(json.dumps({k:v for k,v in out.items() if k!='best'}));print(json.dumps([{k:v for k,v in r.items() if k not in ('bags','edges','source_ids')} for r in retained]))

if __name__=='__main__':main()
