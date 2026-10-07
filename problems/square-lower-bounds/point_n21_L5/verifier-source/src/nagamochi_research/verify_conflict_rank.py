"""Replay hull conflicts, rank budgets, D4 orbits and finite dual bounds."""
import json
from fractions import Fraction as F
from itertools import combinations
from pathlib import Path
from assignment_pilot import hull
from assignment_conflicts import intersects
from conflict_rank import ROOT,independence
from conflict_rank_lp import canon,orbit
from bridge_lp import hits_exact,row_from_hits


def verify():
    data=json.loads((ROOT/'rules.json').read_text())
    for cycle in data['cycles']:
        bags=[[tuple(map(F,p)) for p in b] for b in cycle['bags']]
        edges=[(i,j) for i,j in combinations(range(5),2) if intersects(hull(bags[i]),hull(bags[j]))]
        assert edges==[tuple(e) for e in cycle['edges']]
        assert independence(edges,5)==cycle['budget']==2
        # Edge relaxation feasible at 1/2 each; summing 5 edges proves <=5/2.
        assert len(edges)==5 and all(sum(i in e for e in edges)==2 for i in range(5))
    lp=json.loads((ROOT/'lp.json').read_text());base=json.loads(Path(lp['base']).read_text());pts=[tuple(map(F,p)) for p in base['points']]
    for j,o in enumerate(lp['new_orbits']):
        keys=[canon([[pts[i] for i in bag] for bag in r]) for r in o]
        assert set(keys)==orbit(keys[0]) and len(keys)==len(set(keys))
        rank=1 if j<lp['pair_orbits'] else 2
        for rule in keys:
            edges=[(i,j) for i,j in combinations(range(len(rule)),2) if intersects(hull(rule[i]),hull(rule[j]))]
            assert independence(edges,len(rule))==rank
        assert lp['costs'][len(base['costs'])+j]==rank*len(o)
    for name,result in lp['results'].items():
        cols=lp['models'][name];loads=[F(0) for _ in cols];total=F(0)
        rank_loads=[F(0) for _ in range(lp['rank_orbits'])]
        for w in result['dual']:
            x,y,t=map(F,w['pose']);c=(1-t*t)/(1+t*t);s=2*t/(1+t*t);rad=(abs(c)+abs(s))/2
            assert rad<=x<=6-rad and rad<=y<=6-rad
            h=hits_exact((x,y,t),pts);row=row_from_hits(h,base['rules'],base['point_orbits'],base['rule_orbits'])
            row += [sum(any(all(h[i] for i in bag) for bag in rule) for rule in o) for o in lp['new_orbits']]
            y=F(w['weight']);assert y>=0;total+=y
            loads=[v+y*row[j] for v,j in zip(loads,cols)]
            if name=='pair_cliques':
                start=len(base['costs'])+lp['pair_orbits']
                rank_loads=[v+y*row[start+j] for j,v in enumerate(rank_loads)]
        assert total==F(result['lower_bound']) and all(v<=lp['costs'][j] for v,j in zip(loads,cols))
        if name=='pair_cliques':
            pricing=json.loads((ROOT/'pricing.json').read_text())
            for j,p in enumerate(pricing):
                assert F(p['dual_load'])==rank_loads[j]
                assert p['cost']==lp['costs'][len(base['costs'])+lp['pair_orbits']+j]
                assert F(p['reduced_cost'])==p['cost']-rank_loads[j]
    result=dict(status='VERIFIED_GEOMETRIC_RANK_BUDGETS_AND_FINITE_DUALS',cycles=len(data['cycles']),pair_orbits=lp['pair_orbits'],rank_orbits=lp['rank_orbits'],duals=len(lp['results']),scope='Global validity of charge budgets, not global coverage or new packing bound.')
    (ROOT/'check.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))

if __name__=='__main__':verify()
