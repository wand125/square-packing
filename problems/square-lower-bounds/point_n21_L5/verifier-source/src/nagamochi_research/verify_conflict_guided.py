"""Replay retained dual-guided candidates independently of heuristic search."""
from fractions import Fraction as F
from itertools import combinations
from pathlib import Path
import json,sys
from assignment_pilot import hull
from assignment_conflicts import intersects
from conflict_rank import independence
from conflict_rank_lp import orbit
from bridge_lp import hits_exact


def verify(root):
    d=json.loads((root/'results.json').read_text());base=json.loads(Path('runs/bridge_selected_20260926/results.json').read_text());lp=json.loads(Path('runs/conflict_rank_20260926/lp.json').read_text())
    pts=[tuple(map(F,p)) for p in base['points']];idx={p:i for i,p in enumerate(pts)}
    dual=[(tuple(map(F,w['pose'])),F(w['weight'])) for w in lp['results']['rank_cycles']['dual']]
    for r in d['best']:
        bags=[[tuple(map(F,p)) for p in bag] for bag in r['bags']]
        edges=[(i,j) for i,j in combinations(range(len(bags)),2) if intersects(hull(bags[i]),hull(bags[j]))]
        assert edges==[tuple(e) for e in r['edges']]
        rank=independence(edges,len(bags));images=orbit(bags);load=F(0)
        assert rank==r['rank'] and rank*len(images)==r['cost'] and len(images)==r['orbit_size']
        for image in images:
            for pose,w in dual:
                h=hits_exact(pose,pts)
                if any(all(h[idx[p]] for p in bag) for bag in image):load+=w
        assert load==F(r['dual_load']) and r['cost']-load==F(r['reduced_cost'])
    result=dict(status='VERIFIED_RETAINED_RANKS_AND_DUAL_LOADS',retained=len(d['best']),improving=sum(F(r['reduced_cost'])<0 for r in d['best']),scope='No exhaustive pricing or global coverage claim.')
    (root/'check.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))

if __name__=='__main__':verify(Path(sys.argv[1]) if len(sys.argv)>1 else Path('runs/conflict_guided_20260926'))
