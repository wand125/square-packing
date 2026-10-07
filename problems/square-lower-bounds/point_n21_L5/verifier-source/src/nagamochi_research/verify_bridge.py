"""Exact bridge artifact checks; no claim of global geometric coverage."""
from fractions import Fraction as F
from itertools import combinations
from pathlib import Path
import json
from bridge_probe import intersection,cover_accounting
from assignment_pilot import inside


def mobius(winning,n):
    values=[int(any(all(mask>>i&1 for i in bag) for bag in winning)) for mask in range(1<<n)]
    coeff=values[:]
    for i in range(n):
        for mask in range(1<<n):
            if mask>>i&1:coeff[mask]-=coeff[mask^(1<<i)]
    for mask in range(1<<n):
        assert sum(c for subset,c in enumerate(coeff) if subset&mask==subset)==values[mask]
    assert all(not (values[a] and values[b]) for a in range(1<<n) for b in range(1<<n) if a&b==0)
    return [dict(sites=[i for i in range(n) if mask>>i&1],coefficient=c) for mask,c in enumerate(coeff) if c]


def verify():
    root=Path('runs/exact_rational_bridge_20260926');data=json.loads((root/'bridge-results.json').read_text());a=data['charge_atom']
    sites=[tuple(map(F,p)) for p in a['sites']];shapes=[[tuple(map(F,p)) for p in h] for h in a['original_hulls']];bags=a['winning_subsets']
    assert len(sites)==len(set(sites))==6 and len(bags)==4
    assert all(set(x)&set(y) for x,y in combinations(bags,2))
    assert all(inside(shapes[i],sites[j]) for i,bag in enumerate(bags) for j in bag)
    common=shapes[0]
    for shape in shapes[1:]:common=intersection(common,shape) if common else []
    assert not common
    assert all(sum(j in bag for bag in bags)==2 for j in range(6))
    assert a['budget']==1 and a['three_of_six_budget']==2
    terms=mobius(bags,6)
    total=cover_accounting();assert total['sha256']==data['closed_cover']['sha256']
    assert total['total']==F(data['closed_cover']['total'])
    result=dict(status='VERIFIED_RULE_BUDGET_AND_GEOMETRIC_IMPLICATION',boolean_patterns=64,
                signed_terms=terms,term_count=len(terms),absolute_coefficient_sum=sum(abs(t['coefficient']) for t in terms),
                scope='Rule budget and finite exact implication only; not a covering certificate or speedup result.')
    (root/'rule-check.json').write_text(json.dumps(result,indent=2));return result


if __name__=='__main__':print(json.dumps(verify()))
