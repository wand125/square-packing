"""Repair approximate Farkas multipliers with explicit variable bound rows.

All sign, cancellation, and negative-sum checks are exact rationals.
Approximate infeasibility itself is never a certificate.
"""
from fractions import Fraction as F
from scipy.optimize import linprog
from exact_lp_rows import weighted_columns


def repair(A,b,weights):
    nv=len(A[0]);weights={i:F(y) for i,y in weights.items() if y}
    assert all(y>=0 for y in weights.values())
    bound={}
    for i,row in enumerate(A):
        nz=[j for j,v in enumerate(row) if v]
        if len(nz)!=1:continue
        j=nz[0];key=(j,1 if row[j]>0 else -1)
        if key not in bound or b[i]/abs(row[j])<b[bound[key]]/abs(A[bound[key]][j]):bound[key]=i
    residual=weighted_columns(A,list(weights),list(weights.values()))
    for j,r in enumerate(residual):
        if not r:continue
        key=(j,-1 if r>0 else 1);assert key in bound
        i=bound[key];weights[i]=weights.get(i,F(0))-r/A[i][j]
    assert all(y>=0 for y in weights.values())
    assert not any(weighted_columns(A,list(weights),list(weights.values())))
    total=sum(b[i]*y for i,y in weights.items());assert total<0
    ids=sorted(weights)
    return dict(rows=ids,weights=[str(weights[i]) for i in ids],negative_sum=str(total))


def certificate(A,b):
    nv=len(A[0]);scales=[F(max(map(abs,row)) or 1) for row in A]
    AA=[[float(v/s) for v in row]+[-1.] for row,s in zip(A,scales)]
    bb=[float(v/s) for v,s in zip(b,scales)]
    for method,presolve in (('highs',True),('highs-ds',False)):
        r=linprog([0]*nv+[1],A_ub=AA,b_ub=bb,bounds=[(None,None)]*nv+[(0,None)],method=method,
                  options={'presolve':presolve,'primal_feasibility_tolerance':1e-10,'dual_feasibility_tolerance':1e-10})
        if not r.success or r.fun<=0:continue
        for denominator in (10**9,10**12):
            y={i:F(float(-v)).limit_denominator(denominator)/scales[i] for i,v in enumerate(r.ineqlin.marginals) if v<0}
            try:return repair(A,b,y)
            except AssertionError:pass
    raise AssertionError('No exact negative sum after bound correction')
