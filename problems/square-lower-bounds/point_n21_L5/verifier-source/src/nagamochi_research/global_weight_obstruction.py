"""Exact dual for necessary limits of global weights and symmetric line trimming.
Variables: area density a, line density b, u=b*(1-r), Q weight q, P weight p.
This proves a lower bound for this restricted resource family, not for all methods.
"""
from fractions import Fraction as F
from pathlib import Path
import json


def audit(k):
    assert isinstance(k,int) and k>=4
    A=[[F(x) for x in row] for row in [(1,0,0,0,0),(0,1,0,0,1),(0,1,0,1,0),(0,0,2,2,0),(0,F(9,10),2,1,0)]]
    cost=list(map(F,[(k-2)**2,4*(k-2),8,8,4*(k-3)]))
    dual=[F((k-2)**2),F(4*(k-3)),F(40,19),F(36,19),F(40,19)]
    assert all(y>=0 for y in dual)
    assert [sum(y*row[j] for y,row in zip(dual,A)) for j in range(5)]==cost
    lower=sum(dual);assert lower==k*k-F(36,19)>k*k-2
    weights=[F(1),F(10,19),F(1,38),F(9,19),F(9,19)]
    assert all(sum(x*a for x,a in zip(weights,row))==1 for row in A)
    assert 0<=weights[2]<=weights[1]/10
    assert 1-weights[2]/weights[1]==F(19,20)
    assert sum(x*c for x,c in zip(weights,cost))==lower
    return dict(k=k,cost=list(map(str,cost)),dual=list(map(str,dual)),lower=str(lower),gap_above_original_budget=str(lower-(k*k-2)),relaxed_primal=list(map(str,weights)),cutoff='19/20',scope='Optimum of necessary limit inequalities only; not a universal coverage certificate.')


def main():
    out=Path('runs/global_weight_obstruction_20260926');out.mkdir(exist_ok=True)
    rows=[audit(k) for k in range(4,11)]
    (out/'dual-audit.json').write_text(json.dumps(dict(status='EXACT_DUAL_IDENTITIES_VERIFIED',variables=['a','b','u=b*(1-r)','q','p'],rows=rows),indent=2)+'\n')
    print(json.dumps(dict(lower='k^2 - 36/19',gap='2/19',checked_k=list(range(4,11)),scope='restricted resource family')))
if __name__=='__main__':main()
