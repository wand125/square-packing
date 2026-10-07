"""Exact replay of augmented rank budgets and finite LP dual witnesses."""
import json,sys
from pathlib import Path
from fractions import Fraction as F
from itertools import combinations
from assignment_pilot import hull
from assignment_conflicts import intersects
from conflict_rank import independence
from conflict_rank_lp import orbit,canon
from bridge_lp import hits_exact,row_from_hits


def verify(root):
    d=json.loads((root/'results.json').read_text());base=json.loads(Path(d['base']).read_text());pts=[tuple(map(F,p)) for p in base['points']]
    assert d['costs']==base['costs']+[r*len(o) for r,o in zip(d['ranks'],d['orbits'])]
    for rank,images in zip(d['ranks'],d['orbits']):
        keys=[canon([[pts[i] for i in b] for b in rule]) for rule in images]
        assert len(keys)==len(set(keys)) and set(keys)==orbit(keys[0])
        for rule in keys:
            edges=[(i,j) for i,j in combinations(range(len(rule)),2) if intersects(hull(rule[i]),hull(rule[j]))]
            assert independence(edges,len(rule))==rank
    for name,r in d['results'].items():
        cols=r['columns'];loads=[F(0) for _ in cols];total=F(0)
        for w in r['dual']:
            pose=tuple(map(F,w['pose']));x,y,t=pose;c=(1-t*t)/(1+t*t);s=2*t/(1+t*t);radius=(abs(c)+abs(s))/2
            assert radius<=x<=6-radius and radius<=y<=6-radius
            h=hits_exact(pose,pts);row=row_from_hits(h,base['rules'],base['point_orbits'],base['rule_orbits'])
            row += [sum(any(all(h[i] for i in bag) for bag in rule) for rule in o) for o in d['orbits']]
            weight=F(w['weight']);assert weight>=0;total+=weight;loads=[v+weight*row[j] for v,j in zip(loads,cols)]
        assert total==F(r['lower_bound']) and all(v<=d['costs'][j] for v,j in zip(loads,cols))
    result=dict(status='VERIFIED_AUGMENTED_RANK_BUDGETS_AND_FINITE_DUALS',orbits=len(d['orbits']),duals=len(d['results']),scope='Fixed finite model only; no global coverage proof.')
    (root/'check.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))

if __name__=='__main__':verify(Path(sys.argv[1]) if len(sys.argv)>1 else Path('runs/conflict_refit_20260926'))
