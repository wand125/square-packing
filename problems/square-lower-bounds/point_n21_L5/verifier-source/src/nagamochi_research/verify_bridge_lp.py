"""Rebuild exact finite dual witnesses; does not verify global coverage."""
from fractions import Fraction as F
import json
from itertools import combinations
from bridge_lp import ROOT, transform, row_from_hits, hits_exact


def verify(root=ROOT):
    d=json.loads((root/'results.json').read_text());pts=[tuple(map(F,p)) for p in d['points']]
    rules=d['rules'];po=d['point_orbits'];ro=d['rule_orbits'];costs=d['costs']
    assert len(pts)==len(set(pts))
    def key(rule):return tuple(sorted(tuple(sorted(pts[i] for i in bag)) for bag in rule))
    keys=[key(r) for r in rules];assert len(keys)==len(set(keys))
    for rule in rules:
        assert len(set(i for bag in rule for i in bag))==6
        assert all(len(set(bag))==3 for bag in rule)
        assert all(set(a)&set(b) for a,b in combinations(rule,2))
    assert sorted(i for o in po for i in o)==list(range(len(pts)))
    assert sorted(i for o in ro for i in o)==list(range(len(rules)))
    for o in po:
        assert {pts[i] for i in o}=={transform(pts[o[0]],g) for g in range(8)}
    for o in ro:
        assert {keys[i] for i in o}=={tuple(sorted(tuple(sorted(transform(p,g) for p in bag)) for bag in keys[o[0]])) for g in range(8)}
    assert costs==[36]+[len(o) for o in po]+[2*len(o) for o in ro]+[len(o) for o in ro]
    count=0
    reports=[d['results']]
    if all('combined' in r for r in d['results'].values()):
        reports.append({n:r['combined'] for n,r in d['results'].items()})
    contact=root/'contact-results.json'
    if contact.exists():reports.append(json.loads(contact.read_text())['results'])
    for report in reports:
        for name,r in report.items():
            cols=d['models'][name];loads=[F(0) for _ in cols];total=F(0)
            for witness in r['dual']:
                x,y,t=map(F,witness['pose']);c=(1-t*t)/(1+t*t);s=2*t/(1+t*t)
                radius=(abs(c)+abs(s))/2
                assert radius<=x<=6-radius and radius<=y<=6-radius
                weight=F(witness['weight']);assert weight>=0;total+=weight
                row=row_from_hits(hits_exact((x,y,t),pts),rules,po,ro)
                for j,col in enumerate(cols):loads[j]+=weight*row[col]
            assert all(load<=costs[col] for load,col in zip(loads,cols))
            assert total==F(r['exact_finite_lower_bound']);count+=1
    result=dict(status='VERIFIED_FINITE_DUALS_AND_D4_BUDGETS',comparisons=count,distinct_rules=len(rules),rule_orbits=len(ro),scope='Finite model lower bounds only; primal weights and global cover are not certified.')
    (root/'check.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))

if __name__=='__main__':
    import sys
    from pathlib import Path
    verify(Path(sys.argv[1]) if len(sys.argv)>1 else ROOT)
