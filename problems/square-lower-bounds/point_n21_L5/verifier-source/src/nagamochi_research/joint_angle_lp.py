"""Fixed rational angles and separation branches: exact LP bound replay.

The selected branches do not cover all packings. Never use a branch result
as an unconditional lower bound on s(n).
"""
from fractions import Fraction as F
from itertools import combinations
from pathlib import Path
import argparse,json
from scipy.optimize import linprog


def rotation(t):
    t=F(t);return (1-t*t)/(1+t*t),2*t/(1+t*t)


def four_same_angle(t):
    c,s=rotation(t)
    assert 0<s<c
    step=1/c;w=c+s
    # Horizontal/vertical centre neighbours separate along an own edge.
    # For diagonal neighbours max projection is step*(c+s)>1.
    assert step*c==1 and step*(c+s)>1 and w-step>0
    return dict(t=str(t),centres=[[str(i*step),str(j*step)] for i,j in ((0,0),(1,0),(0,1),(1,1))],
                xy_overlap_margin=str(w-step),container_side=str(w+step))


def model(grid,angles):
    n=len(grid);rot=[rotation(t) for t in angles];nv=2*n+1
    A=[];b=[]
    for i,(c,s) in enumerate(rot):
        h=(abs(c)+abs(s))/2
        for v in range(2):
            row=[F(0)]*nv;row[2*i+v]=-1;A.append(row);b.append(-h)
            row=[F(0)]*nv;row[2*i+v]=1;row[-1]=-1;A.append(row);b.append(-h)
    for i,j in combinations(range(n),2):
        c,s=rot[i];C,S=rot[j]
        h=(1+abs(c*C+s*S)+abs(c*S-s*C))/2
        # Preserve column order; in a column preserve row order.
        axis=(c,s) if grid[i][0]!=grid[j][0] else (-s,c)
        v=0 if grid[i][0]!=grid[j][0] else 1
        sign=1 if grid[j][v]>grid[i][v] else -1
        row=[F(0)]*nv
        for v in range(2):row[2*i+v]=sign*axis[v];row[2*j+v]=-sign*axis[v]
        A.append(row);b.append(-h)
    return A,b


def replay(A,b,dual,primal):
    assert len(dual)==len(b) and len(primal)==len(A[0])
    assert all(y<=0 for y in dual)
    for k in range(len(primal)):
        assert sum(row[k]*y for row,y in zip(A,dual))==(1 if k==len(primal)-1 else 0)
    assert all(sum(a*x for a,x in zip(row,primal))<=rhs for row,rhs in zip(A,b))
    lower=sum(y*rhs for y,rhs in zip(dual,b));assert lower==primal[-1]
    return lower


def solve(grid,angles):
    A,b=model(grid,angles)
    return solve_system(A,b)


def solve_system(A,b):
    nv=len(A[0])
    result=linprog([0]*(nv-1)+[1],A_ub=[[float(x) for x in r] for r in A],
                   b_ub=list(map(float,b)),bounds=[(None,None)]*nv,method='highs')
    if not result.success:return dict(status='NUMERICAL_FAILURE',message=result.message)
    for limit in (10**6,10**9,10**12):
        dual=[F(float(y)).limit_denominator(limit) for y in result.ineqlin.marginals]
        primal=[F(float(x)).limit_denominator(limit) for x in result.x]
        try:lower=replay(A,b,dual,primal)
        except AssertionError:continue
        return dict(status='EXACT_BRANCH_OPTIMUM',lower=str(lower),lower_float=float(lower),
                    dual=list(map(str,dual)),primal=list(map(str,primal)))
    # Recover the active linear systems exactly instead of rounding large
    # denominator rationals one coordinate at a time. All recovered values
    # must still pass replay; a numerical active set is only a proposal.
    import sympy as sp
    def exact_solution(matrix,rhs):
        values,params=sp.Matrix(matrix).gauss_jordan_solve(sp.Matrix(rhs))
        values=values.subs({p:0 for p in params})
        return [F(int(v.p),int(v.q)) for v in values]
    support=[i for i,y in enumerate(result.ineqlin.marginals) if y<0]
    try:
        values=exact_solution([[A[i][k] for i in support] for k in range(nv)],[0]*(nv-1)+[1])
        dual=[F(0)]*len(b)
        for i,y in zip(support,values):dual[i]=y
        for tol in (1e-8,1e-9,1e-10):
            active=[i for i,v in enumerate(result.ineqlin.residual) if abs(v)<tol]
            try:
                primal=exact_solution([A[i] for i in active],[b[i] for i in active])
                lower=replay(A,b,dual,primal)
            except (ValueError,AssertionError):continue
            return dict(status='EXACT_BRANCH_OPTIMUM',lower=str(lower),lower_float=float(lower),
                        reconstruction='exact_active_system',dual=list(map(str,dual)),primal=list(map(str,primal)))
    except (ValueError,AssertionError):pass
    return dict(status='RATIONAL_RECONSTRUCTION_FAILED',numerical_lower=float(result.fun))


def run(out):
    cases=[]
    for n,grid in [(12,[(x,y) for x in range(4) for y in range(3)]),
                   (21,[(x,y) for x in range(5) for y in range(5) if not(x>=3 and y>=3)])]:
        for t in [F(0),F(1,1000),F(1,100),F(1,20),F(1,10),F(1,3)]:
            for pattern in ('same','checker','columns'):
                angles=[t if pattern=='same' or (x+y if pattern=='checker' else x)%2==0 else -t for x,y in grid]
                result=solve(grid,angles)
                cases.append(dict(n=n,t=str(t),pattern=pattern,grid=grid,angles=list(map(str,angles)),**result))
    payload=dict(status='COMPLETED_CONDITIONAL_BRANCH_EXPERIMENT',cases=cases,
                 four_same_angle=[four_same_angle(F(1,1000)),four_same_angle(F(1,3))],
                 limitation='Fixed angles and one selected separation topology per case. Not exhaustive over angles or branches; not a proof of s(12)=4 or s(21)=5.')
    out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(payload,indent=2))
    for c in cases:print(c['n'],c['t'],c['pattern'],c['status'],c.get('lower_float',c.get('numerical_lower')))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('out',type=Path);a=p.parse_args();run(a.out)
