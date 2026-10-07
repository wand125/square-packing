"""Exact counterexamples and one-parameter limit for symmetric line trimming."""
from fractions import Fraction as F
from pathlib import Path
import json
from score import cross,sub
from trimmed_line_pilot import resource,strict_score


def family(t,d):
    c=(1-t*t)/(1+t*t);s=2*t/(1+t*t);lam=1+t*t;b=(1-d+c,F(0))
    return [(b[0]-lam*c,lam*s),b,(b[0]+lam*s,lam*c),(b[0]+lam*(-c+s),lam*(s+c))],lam


def audit(out):
    out.mkdir(parents=True,exist_ok=True);records=[]
    for k in range(4,11):
        for t in (F(1,1000),F(1,10000),F(1,100000)):
            poly,lam=family(t,F(999,10000))
            edges=[sub(poly[(i+1)%4],poly[i]) for i in range(4)]
            assert all(sum(z*z for z in e)==lam*lam for e in edges)
            assert all(sum(edges[i][j]*edges[(i+1)%4][j] for j in range(2))==0 for i in range(4))
            assert all(0<=x<=k and 0<=y<=k for x,y in poly)
            for cutoff in (F(9,10),F(19,20),F(24,25),F(1)):
                res=resource(k,exact=True,cutoff=cutoff);val=strict_score(k,poly,res)
                assert isinstance(val,F)
                atoms=[p for p in res[1] if all(cross(sub(b,a),sub(p,a))>0 for a,b in zip(poly,poly[1:]+poly[:1]))]
                assert atoms==[(F(1),F(9,10))]
                if cutoff>=F(24,25):assert val<1
                records.append(dict(k=k,t=str(t),shift='999/10000',side=str(lam),cutoff=str(cutoff),score=str(val),score_decimal=float(val),status='EXACT_DEFICIT' if val<1 else 'FINITE_CHECK_ONLY',vertices=[list(map(str,p)) for p in poly]))
    endpoint_records=[]
    for t in (F(1,10000),F(1,1000000)):
        c=(1-t*t)/(1+t*t);s=2*t/(1+t*t);bx=2-F(9,10)*s/c-t**3;lam=1+t**4
        poly=[(bx-lam*c,lam*s),(bx,F(0)),(bx+lam*s,lam*c),(bx+lam*(-c+s),lam*(s+c))]
        res=resource(4,trim=False,exact=True)
        atoms=[p for p in res[1] if all(cross(sub(b,a),sub(p,a))>0 for a,b in zip(poly,poly[1:]+poly[:1]))]
        assert atoms==[(F(1),F(9,10))]
        assert all(0<=x<=4 and 0<=y<=4 for x,y in poly)
        for q in (F(49,100),F(499,1000)):
            val=strict_score(4,poly,res)-F(1,2)+q
            assert val<1
            endpoint_records.append(dict(t=str(t),q=str(q),side=str(lam),score=str(val),score_decimal=float(val),vertices=[list(map(str,p)) for p in poly]))
    result=dict(status='TRIMMING_BOUND_AND_EXACT_DEFICITS',records=records,count=len(records),endpoint_records=endpoint_records,necessary_cutoff_at_half_weight='19/20',maximum_budget_recovery='1/5',two_parameter_budget_lower_bound='k^2 - 9/5',scope='Necessary conditions q>=1/2 and q>=r-9/20 within fixed density/point positions; no sufficiency at cutoff 19/20. See accompanying analytic limit argument.')
    (out/'family-audit.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(dict(count=len(records),deficits=sum(r['status']=='EXACT_DEFICIT' for r in records),last=[{k:r[k] for k in ('cutoff','score_decimal','status')} for r in records[-4:]])))
if __name__=='__main__':audit(Path('runs/trimmed_line_20260926'))
