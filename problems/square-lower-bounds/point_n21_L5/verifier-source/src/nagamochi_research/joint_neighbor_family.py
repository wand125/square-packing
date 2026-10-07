"""Relax the separation topology to grid neighbours, replay symbolic duals.

Bernstein signs are checked exactly in Q(sqrt(2)) over t in [0,sqrt(2)-1].
These are conditional exclusions, not full packing theorems.
"""
from fractions import Fraction as F
from itertools import combinations
from math import comb
from pathlib import Path
import argparse,json,time
import sympy as sp
from joint_angle_lp import model,solve_system


def bernstein(poly,t):
    z=sp.Symbol('z');end=sp.sqrt(2)-1
    p=sp.Poly(sp.expand(poly.subs(t,end*z)),z)
    degree=p.degree()
    if p.is_zero:return [sp.Integer(0)]
    powers=[sp.simplify(p.nth(i)) for i in range(degree+1)]
    return [sp.simplify(sum(powers[i]*sp.Rational(comb(k,i),comb(degree,i))
                            for i in range(k+1))) for k in range(degree+1)]


def nonnegative(expr,t,strict=False):
    num,den=sp.fraction(sp.cancel(expr))
    if den.subs(t,0)<0:num,den=-num,-den
    num_coeff=bernstein(num,t);den_coeff=bernstein(den,t)
    assert all(x.is_nonnegative is True for x in num_coeff)
    assert all(x.is_nonnegative is True for x in den_coeff)
    assert den_coeff[0].is_positive is True and den_coeff[-1].is_positive is True
    if strict:
        # Strict in the OPEN interval; endpoint equality is permitted.
        assert any(x.is_positive is True for x in num_coeff)
    return dict(numerator=list(map(str,num_coeff)),denominator=list(map(str,den_coeff)))


def prove(parent):
    start=time.monotonic();n=parent['n'];k=parent['k'];g=parent['grid'];nv=2*n+1
    pairs=list(combinations(range(n),2));A,b=model(g,[F(1,10)]*n)
    keep=list(range(4*n))+[4*n+e for e,(i,j) in enumerate(pairs)
                          if abs(g[i][0]-g[j][0])+abs(g[i][1]-g[j][1])==1]
    exact=solve_system([A[i] for i in keep],[b[i] for i in keep])
    assert exact['status']=='EXACT_BRANCH_OPTIMUM'
    support=[keep[i] for i,y in enumerate(exact['dual']) if F(y)]
    t=sp.Symbol('t');c=(1-t*t)/(1+t*t);s=2*t/(1+t*t);w=c+s
    rows=[];rhs=[]
    for row in support:
        if row<4*n:rows.append(A[row]);rhs.append(-w/2)
        else:
            i,j=pairs[row-4*n];axis=(c,s) if g[i][0]!=g[j][0] else (-s,c)
            r=[0]*nv
            for v in range(2):r[2*i+v]=axis[v];r[2*j+v]=-axis[v]
            rows.append(r);rhs.append(-1)
    # Clear common denominators before polynomial-domain elimination. Generic
    # expression-matrix elimination expands fractions needlessly on n21.
    M=sp.Matrix(rows).T
    polynomial=M.applyfunc(lambda x:sp.cancel(x*(1+t*t)).expand())
    objective=sp.Matrix([0]*(nv-1)+[1+t*t])
    dm,db=polynomial.to_DM().unify(objective.to_DM())
    numer,den=dm.solve_den(db)
    denominator=dm.domain.to_sympy(den)
    dual=[sp.cancel(y/denominator) for y in numer.to_Matrix()]
    assert all(sp.cancel(v)==0 for v in M*sp.Matrix(dual)-sp.Matrix([0]*(nv-1)+[1]))
    signs=[nonnegative(-y,t) for y in dual]
    lower=sp.cancel(sum(y*v for y,v in zip(dual,rhs)))
    gap_proof=nonnegative(lower-k,t,strict=True)
    vertices=set();separations=[]
    for row in support:
        if row<4*n:vertices.add(row//4)
        else:
            i,j=pairs[row-4*n];vertices.update((i,j))
            separations.append(dict(i=i,j=j,axis='u' if g[i][0]!=g[j][0] else 'v',axis_owner=i,sign=1))
    return dict(n=n,k=k,grid=g,status='EXACT_NEIGHBOUR_SYMBOLIC_EXCLUSION',
                interval='0 <= t <= sqrt(2)-1; 0 <= theta <= pi/4',
                lower=str(sp.factor(lower)),gap=str(sp.factor(lower-k)),
                sparse_rows=support,dual=list(map(str,dual)),sign_proofs=signs,gap_proof=gap_proof,
                relevant_boxes=sorted(vertices),required_separations=separations,
                seed_model_rows=keep,seed_proof=exact,seconds=time.monotonic()-start)


def run(source,out):
    parents=json.loads(source.read_text())['cases'];results=[]
    for parent in parents:
        q=prove(parent);results.append(q)
        print(q['n'],q['lower'],len(q['required_separations']),q['seconds'],flush=True)
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(dict(cases=results,limitation='Required directed neighbour relations and common angle only; occurrence in arbitrary packings is not proved.'),indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('source',type=Path);p.add_argument('out',type=Path)
    a=p.parse_args();run(a.source,a.out)
