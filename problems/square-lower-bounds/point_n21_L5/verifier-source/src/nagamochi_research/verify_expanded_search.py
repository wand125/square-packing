"""Check saved finite LP solutions and exact costs of added OR charges."""
import json
from fractions import Fraction as F
from itertools import combinations
import numpy as np
from expanded_search_pilot import ROOT, load

def verify(n):
    out=ROOT/f'n{n}';d=json.loads((out/'results.json').read_text());z=np.load(out/'replay.npz')
    mapping=d['mapping'];pts=[tuple(map(F,p)) for p in mapping['points']]
    lf=F(str(d['L']));assert all(0<=x<=lf and 0<=y<=lf for x,y in pts)
    for rule,images in zip(d['rules'],mapping['rule_images']):
        bags=rule['bags']
        winning=[mask for mask in range(64) if any(all(mask>>j&1 for j in bag) for bag in bags)]
        assert winning and all(a&b for a,b in combinations(winning,2))
        # Two disjoint boxes cannot each contain a winning mask.
        assert rule['cost']==1
        sites=[tuple(map(F,p)) for p in rule['sites']]
        assert len(images)==8
        for g,image in enumerate(images):
            assert len(image)==6
            for p,i in zip(sites,image):
                x,y=p
                if g>=4:x,y=y,x
                expected=(lf-x if g%4&1 else x,lf-y if g%4&2 else y)
                assert pts[i]==expected
    for orbit in mapping['point_orbits']:assert len(orbit)==8
    for name,m in d['models'].items():
        w=z['weights_'+name];a=z['matrix'][:,:len(w)]
        assert np.all(w>=0)
        assert np.min(a@w)>=d['rhs']-1e-8
        assert abs(float(sum(w))-m['refit']['mass'])<1e-8
    for name,check in d['full_saved_audit'].items():
        v=np.load(out/('saved_coverage_'+name+'.npy'))
        assert len(v)==d['total_saved_rows']
        assert abs(v.min()-check['minimum'])<1e-12
        assert abs(np.maximum(d['rhs']-v,0).sum()-check['deficit_sum'])<1e-10
    repair_checks=[]
    for file in sorted(out.glob('repair*.json')):
        rd=json.loads(file.read_text());rz=np.load(out/(file.stem+'-replay.npz'))
        for name,m in rd['models'].items():
            w=rz['weights_'+name];a=rz['matrix'][:,:len(w)]
            # Early exploratory runs used the solver's default 1e-7 tolerance;
            # final repair3 was rerun at 1e-9 primal/dual tolerance.
            tolerance=1e-8 if file.stem=='repair3' else 1e-7
            assert np.all(w>=0) and np.min(a@w)>=d['rhs']-tolerance
            assert abs(sum(w)-m['mass'])<1e-8
            coverage=rz['coverage_'+name]
            assert len(coverage)==d['total_saved_rows']
            assert abs(min(coverage)-m['full_saved_minimum'])<1e-12
        repair_checks.append(file.stem)
    result=dict(repairs_replayed=repair_checks,n=n,rule_budgets_verified=len(d['rules']),finite_primal_replayed=True,
                scope='Combinatorial costs exact; LP geometry and residuals numerical. No global proof.')
    (out/'verified.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))
if __name__=='__main__':
    for n in (12,21):verify(n)
