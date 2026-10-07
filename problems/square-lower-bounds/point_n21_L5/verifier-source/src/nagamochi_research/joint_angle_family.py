"""Symbolic dual replay over the full common-angle interval [0, pi/2].

Conditional on the column/row separation branch of joint_angle_lp.model.
No assertion that arbitrary packings have that branch or a common angle.
"""
import argparse,json,hashlib
from pathlib import Path
from fractions import Fraction as F
from itertools import combinations
import sympy as sp


def verify_case(case):
    n=case['n'];k={12:4,21:5}[n];grid=case['grid'];nv=2*n+1
    assert case['pattern']=='same' and case['t']=='1/10'
    t=sp.Symbol('t',real=True);c=(1-t*t)/(1+t*t);s=2*t/(1+t*t);w=c+s
    terms=dict(c=c,s=s,cc=c*c,ss=s*s,cs=c*s,one=sp.Integer(1))
    # Each dual coefficient is -one of these nonnegative monomials / w.
    # On 0<=t<=1, c,s>=0 and w>0, so all multipliers are nonpositive.
    labels={F(str(sp.cancel(-v/w).subs(t,sp.Rational(1,10)))):name for name,v in terms.items()}
    dual=[];sparse=[]
    for i,value in enumerate(case['dual']):
        y=F(value)
        if not y:dual.append(sp.Integer(0));continue
        name=labels[y];dual.append(-terms[name]/w);sparse.append(dict(row=i,weight=name))
    A=[];b=[]
    for i in range(n):
        for v in range(2):
            row=[0]*nv;row[2*i+v]=-1;A.append(row);b.append(-w/2)
            row=[0]*nv;row[2*i+v]=1;row[-1]=-1;A.append(row);b.append(-w/2)
    for i,j in combinations(range(n),2):
        v=0 if grid[i][0]!=grid[j][0] else 1
        assert grid[i][v]<grid[j][v]
        axis=(c,s) if v==0 else (-s,c);row=[0]*nv
        for a in range(2):row[2*i+a]=axis[a];row[2*j+a]=-axis[a]
        A.append(row);b.append(-1)
    assert len(A)==len(dual)
    for v in range(nv):
        assert sp.cancel(sum(row[v]*y for row,y in zip(A,dual))-(1 if v==nv-1 else 0))==0
    lower=sp.cancel(sum(y*rhs for y,rhs in zip(dual,b)))
    assert sp.cancel(lower-((k-1)*w+1/w))==0
    assert sp.cancel(lower-k-(w-1)*((k-1)*w-1)/w)==0
    # c²+s²=1 gives w²=1+2cs>=1; hence w>=1. Both factors
    # in lower-k are nonnegative for k>=2. Equal only if w=1.
    assert sp.cancel(c*c+s*s-1)==0
    # Unequal-angle extension, assuming L<=k for contradiction. If every
    # half-angle parameter differs from nominal t by <=h, each boundary
    # row relaxes by <=2h, and each selected separation row by <=4*k*h.
    # This uses |cos'|,|sin'|<=2, |dx|,|dy|<=k, and the true pair threshold
    # >=1, irrespective of relative angle. The nominal dual remains valid
    # for this relaxed system; sum boundary |y|=2.
    boundary_sum=sp.cancel(-sum(dual[:4*n]));pair_sum=sp.cancel(-sum(dual[4*n:]))
    assert boundary_sum==2 and sp.cancel(pair_sum-(lower-w))==0
    penalty=sp.cancel(2*boundary_sum+4*k*pair_sum)
    cones=[]
    for nominal in (sp.Rational(1,1000),sp.Rational(1,100),sp.Rational(1,10),sp.Rational(1,3)):
        value=sp.cancel(lower.subs(t,nominal));cost=sp.cancel(penalty.subs(t,nominal))
        radius=sp.cancel((value-k)/(2*cost));assert radius>0
        bound=sp.cancel(value-cost*radius);assert bound>k
        cones.append(dict(nominal_t=str(nominal),each_t_radius=str(radius),
                          radius_float=float(radius),conditional_lower=str(bound)))
    pairs=list(combinations(range(n),2));vertices=set();required=[];boundaries=[]
    for entry in sparse:
        row=entry['row']
        if row<4*n:
            i=row//4;vertices.add(i)
            boundaries.append(dict(box=i,side=('left','right','bottom','top')[row%4]))
        else:
            i,j=pairs[row-4*n];vertices.update((i,j))
            axis='u' if grid[i][0]!=grid[j][0] else 'v'
            required.append(dict(i=i,j=j,axis_owner=i,axis=axis,sign=1))
    return dict(n=n,k=k,grid=grid,dual_terms=sparse,
                relevant_boxes=sorted(vertices),required_separations=required,
                used_container_boundaries=boundaries,
                sparse_scope='Only these boxes need the angle condition and only these selected separations are required. All other boxes and pair separation choices are unrestricted.',
                angle_interval='0 <= theta <= pi/2; t=tan(theta/2) in [0,1]',
                lower=f'{k-1}*w+1/w',w='cos(theta)+sin(theta)',
                strict_for='0 < theta < pi/2',
                unequal_angle_cones=cones,
                unequal_angle_theorem='For the same actual separation branch and L<=k, independent |t_i-t|<=h imply L>=B-C*h; B=(k-1)*w+1/w, C=4+4*k*(B-w). Choose h=(B-k)/(2*C) to contradict L<=k.',
                status='EXACT_SYMBOLIC_CONDITIONAL_LOWER_BOUND')


def run(source,out):
    data=json.loads(source.read_text());cases=[]
    for n in (12,21):
        case=next(q for q in data['cases'] if q['n']==n and q['t']=='1/10' and q['pattern']=='same')
        cases.append(verify_case(case))
    result=dict(cases=cases,source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
                limitation='Specified separation branch only. Common orientations and quantified independent perturbations are covered; arbitrary relative angles and other branch topologies remain unproved.')
    out.write_text(json.dumps(result,indent=2));print(json.dumps(result))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('source',type=Path);p.add_argument('out',type=Path)
    a=p.parse_args();run(a.source,a.out)
