"""Disjunctive LP search for saturated axis cells plus rotated centres.

Numerical feasibility guides branching; infeasible leaves carry exact Farkas
certificates. A node limit leaves a pending branch, never an exclusion.
"""
from fractions import Fraction as F
from itertools import combinations
from pathlib import Path
import json,time
import numpy as np
from scipy.optimize import linprog
from joint_angle_lp import rotation
from exact_lp_rows import weighted_columns
from saturated_axis_cells import build


def model(L,t,k,chosen,axis_inner=F(1),rot_inner=F(1),rot_half=None,missing=()):
    pieces,_=build(L,t,k,axis_inner,rot_inner,rot_half,missing);d=(L-1)/(k-1);H=(L-1)/2;polys=[];angles=[];cell_index={}
    for i in range(k-1):
        for j in range(k-1):
            if i*(k-1)+j in missing:continue
            cell_index[i*(k-1)+j]=len(polys)
            x=-H+i*d;y=-H+j*d;polys.append([(x,y),(x+d,y),(x+d,y+d),(x,y+d)]);angles.append(F(0))
    polys.extend(pieces[i] for i in chosen);angles.extend([t]*len(chosen));n=len(polys);A=[];b=[]
    sides=[axis_inner]*len(cell_index)+[rot_inner]*len(chosen)
    forced=[]
    # Neighbours in one centre-cell row have y-distance<1, forcing x order;
    # the corresponding column argument forces y order.
    for i in range(k-1):
        for j in range(k-1):
            idx=i*(k-1)+j
            for other,axis in ((idx+k-1,0),(idx+1,1)):
                if (axis==0 and i==k-2) or (axis==1 and j==k-2):continue
                if idx not in cell_index or other not in cell_index:continue
                row=[F(0)]*(2*n);row[2*cell_index[idx]+axis]=1;row[2*cell_index[other]+axis]=-1;forced.append((row,-axis_inner))
    return assemble_model(polys,angles,sides,forced)


def assemble_model(polys,angles,sides,forced,guaranteed_sides=None,strict_separation=False):
    """Build SAT disjunctions from exact convex centre domains and forced rows."""
    n=len(polys);A=[];b=[]
    if guaranteed_sides is None:guaranteed_sides=sides
    assert len(guaranteed_sides)==n and all(a>=b for a,b in zip(guaranteed_sides,sides))
    for i,p in enumerate(polys):
        assert len(p)>=3
        for (x,y),(X,Y) in zip(p,p[1:]+p[:1]):
            a,bb=Y-y,x-X;row=[F(0)]*(2*n);row[2*i]=a;row[2*i+1]=bb;A.append(row);b.append(a*x+bb*y)
    for row,rhs in forced:A.append(row);b.append(rhs)
    pairs=[];rot=list(map(rotation,angles))
    for i,j in combinations(range(n),2):
        c,s=rot[i];C,S=rot[j];relative=abs(c*C+s*S)+abs(c*S-s*C)
        own=(sides[i]+sides[j]*relative)/2;other=(sides[j]+sides[i]*relative)/2
        max_own=(guaranteed_sides[i]+guaranteed_sides[j]*relative)/2
        max_other=(guaranteed_sides[j]+guaranteed_sides[i]*relative)/2
        options={};guaranteed=False
        for u,v,threshold,max_threshold in ((c,s,own,max_own),(-s,c,own,max_own),(C,S,other,max_other),(-S,C,other,max_other)):
            for sign in (-1,1):
                a,bb=sign*u,sign*v
                P=[a*x+bb*y for x,y in polys[i]];Q=[a*x+bb*y for x,y in polys[j]]
                if (min(Q)-max(P)>max_threshold if strict_separation else min(Q)-max(P)>=max_threshold):guaranteed=True
                if (max(Q)-min(P)<=threshold if strict_separation else max(Q)-min(P)<threshold):continue
                row=[F(0)]*(2*n);row[2*i]=a;row[2*i+1]=bb;row[2*j]=-a;row[2*j+1]=-bb
                options[tuple(row)]=(row,-threshold)
        if not guaranteed:pairs.append(dict(i=i,j=j,options=list(options.values())))
    return A,b,pairs,polys,angles


def farkas(A,b):
    nv=len(A[0]);scales=[F(max(map(abs,row)) or 1) for row in A]
    normalized=[[x/scale for x in row] for row,scale in zip(A,scales)]
    r=linprog([0]*nv+[1],A_ub=[[float(x) for x in row]+[-1] for row in normalized],
              b_ub=[float(rhs/scale) for rhs,scale in zip(b,scales)],
              bounds=[(None,None)]*nv+[(0,None)],method='highs',
              options={'primal_feasibility_tolerance':1e-9,'dual_feasibility_tolerance':1e-9})
    assert r.success and r.fun>0
    indices=[i for i,y in enumerate(r.ineqlin.marginals) if y<0]
    def valid(weights):
        return all(y>=0 for y in weights) and not any(weighted_columns(A,indices,weights)) and sum(b[i]*y for i,y in zip(indices,weights))<0
    weights=[F(float(-r.ineqlin.marginals[i])).limit_denominator(10**9)/scales[i] for i in indices]
    if not valid(weights):
        import sympy as sp
        M=sp.Matrix([[normalized[i][j] for i in indices] for j in range(nv)]+[[1]*len(indices)])
        values,params=M.gauss_jordan_solve(sp.Matrix([0]*nv+[1]));values=values.subs({p:0 for p in params})
        weights=[F(int(v.p),int(v.q))/scales[i] for i,v in zip(indices,values)]
    assert valid(weights)
    return dict(rows=indices,weights=list(map(str,weights)),negative_sum=str(sum(b[i]*y for i,y in zip(indices,weights))))


def search(L,t,k,chosen,node_limit=3000,axis_inner=F(1),rot_inner=F(1),rot_half=None,missing=()):
    result=search_model(model(L,t,k,chosen,axis_inner,rot_inner,rot_half,missing),node_limit)
    result.update(L=str(L),t=str(t),k=k,chosen=chosen,missing=list(missing),
                  axis_inner=str(axis_inner),rot_inner=str(rot_inner),rot_half=None if rot_half is None else str(rot_half))
    return result


def nonpositive_bound(A,b,marginals,index):
    """Exact dual certificate that coordinate index is <= 0."""
    nv=len(A[0]);scales=[F(max(map(abs,row)) or 1) for row in A]
    ids=[i for i,y in enumerate(marginals) if y<0]
    target=[F(int(j==index)) for j in range(nv)]
    def valid(weights):
        return all(y>=0 for y in weights) and weighted_columns(A,ids,weights)==target and sum(b[i]*y for i,y in zip(ids,weights))<=0
    weights=[F(float(-marginals[i])).limit_denominator(10**9)/scales[i] for i in ids]
    if not valid(weights):
        import sympy as sp
        M=sp.Matrix([[F(A[i][j])/scales[i] for i in ids] for j in range(nv)])
        values,params=M.gauss_jordan_solve(sp.Matrix(target));values=values.subs({p:0 for p in params})
        weights=[F(int(v.p),int(v.q))/scales[i] for i,v in zip(ids,values)]
    assert valid(weights)
    return dict(rows=ids,weights=list(map(str,weights)),upper_bound=str(sum(b[i]*y for i,y in zip(ids,weights))),index=index)


def search_model(data,node_limit=3000,positive_index=None,branch_rule='gap',certificate_solver=None):
    A,b,pairs,polys,angles=data;nv=len(A[0]);nodes=0;leaves=0;start=time.monotonic()
    assert branch_rule in ('gap','fewest','ordered')
    objective=np.zeros(nv)
    if positive_index is not None:
        assert type(positive_index) is int and 0<=positive_index<nv
        objective[positive_index]=-1
    def visit(A,b,remaining):
        nonlocal nodes,leaves
        if nodes>=node_limit:return dict(status='PENDING_NODE_LIMIT')
        nodes+=1
        AA=np.array(A,dtype=float);scales=np.max(np.abs(AA),axis=1);scales[scales==0]=1
        r=linprog(objective,A_ub=AA/scales[:,None],b_ub=np.array(b,dtype=float)/scales,
                  bounds=[(None,None)]*nv,method='highs',
                  options={'primal_feasibility_tolerance':1e-9,'dual_feasibility_tolerance':1e-9})
        if positive_index is not None and r.status not in (0,2):
            r=linprog(objective,A_ub=AA/scales[:,None],b_ub=np.array(b,dtype=float)/scales,
                      bounds=[(None,None)]*nv,method='highs-ds',
                      options={'presolve':False,'primal_feasibility_tolerance':1e-9,'dual_feasibility_tolerance':1e-9})
        if r.status==2:
            try:cert=(certificate_solver or farkas)(A,b)
            except (AssertionError,ValueError):return dict(status='UNVERIFIED_INFEASIBLE')
            leaves+=1;return dict(status='EXACT_INFEASIBLE',farkas=cert)
        if not r.success:return dict(status='NUMERICAL_FAILURE',message=r.message)
        if positive_index is not None and r.fun>=-1e-8:
            try:cert=nonpositive_bound(A,b,r.ineqlin.marginals,positive_index)
            except (AssertionError,ValueError):pass
            else:
                leaves+=1;return dict(status='EXACT_NONPOSITIVE_COORDINATE',bound=cert)
        candidate=None;gap=1e-8;fewest=None
        for p in remaining:
            options=pairs[p]['options']
            if not options:return dict(status='EXACT_NO_SEPARATION_OPTION',pair=p)
            violation=min(np.dot(np.array(row,dtype=float),r.x)-float(rhs) for row,rhs in options)
            if branch_rule=='ordered' and violation>1e-8:
                candidate=p;break
            if branch_rule=='gap':
                if violation>gap:gap=violation;candidate=p
            elif violation>1e-8:
                key=(len(options),-violation,p)
                if fewest is None or key<fewest:fewest=key;candidate=p
        if candidate is None:return dict(status='NUMERICAL_PACKING_CANDIDATE',centres=r.x.tolist())
        children=[]
        for row,rhs in pairs[candidate]['options']:
            child=visit(A+[row],b+[rhs],[p for p in remaining if p!=candidate]);children.append(child)
            if child['status'] not in ('EXACT_INFEASIBLE','EXACT_NO_SEPARATION_OPTION','EXACT_BRANCH_EXCLUDED','EXACT_NONPOSITIVE_COORDINATE'):
                return dict(status='UNRESOLVED_BRANCH',pair=candidate,children=children)
        return dict(status='EXACT_BRANCH_EXCLUDED',pair=candidate,children=children)
    tree=visit(A,b,list(range(len(pairs))))
    return dict(n=len(polys),nodes=nodes,leaves=leaves,
                seconds=time.monotonic()-start,status=tree['status'],tree=tree)


def run(out):
    L=F(3999,1000);t=F(1,100);pieces,_=build(L,t,4);assert len(pieces)==4
    results=[]
    for chosen in combinations(range(4),3):
        q=search(L,t,4,list(chosen));results.append(q)
        print(chosen,q['status'],q['nodes'],q['leaves'],q['seconds'],flush=True)
        out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(dict(cases=results),indent=2))
    return results


def replay_case(q):
    return replay_model(model(F(q['L']),F(q['t']),q['k'],q['chosen'],F(q.get('axis_inner','1')),F(q.get('rot_inner','1')),None if q.get('rot_half') is None else F(q['rot_half']),q.get('missing',())),q['tree'])


def replay_model(data,tree,positive_index=None):
    A,b,pairs,polys,angles=data
    def replay(node,A,b,remaining):
        status=node['status']
        if status=='EXACT_NONPOSITIVE_COORDINATE':
            assert positive_index is not None and 0<=positive_index<len(A[0])
            cert=node['bound'];assert cert['index']==positive_index
            ids=cert['rows'];weights=list(map(F,cert['weights']))
            assert len(ids)==len(weights) and len(ids)==len(set(ids))
            assert all(type(i) is int and 0<=i<len(A) for i in ids) and all(y>=0 for y in weights)
            assert weighted_columns(A,ids,weights)==[int(j==positive_index) for j in range(len(A[0]))]
            total=sum(b[i]*y for i,y in zip(ids,weights));assert total<=0 and total==F(cert['upper_bound'])
            return True
        if status=='EXACT_INFEASIBLE':
            cert=node['farkas'];ids=cert['rows'];weights=list(map(F,cert['weights']))
            assert len(ids)==len(weights) and len(ids)==len(set(ids))
            assert all(type(i) is int and 0<=i<len(A) for i in ids) and all(y>=0 for y in weights)
            assert not any(weighted_columns(A,ids,weights))
            total=sum(b[i]*y for i,y in zip(ids,weights));assert total<0 and total==F(cert['negative_sum'])
            return True
        if status=='EXACT_NO_SEPARATION_OPTION':
            assert node['pair'] in remaining and not pairs[node['pair']]['options'];return True
        if status=='EXACT_BRANCH_EXCLUDED':
            p=node['pair'];assert p in remaining and len(node['children'])==len(pairs[p]['options'])
            return all(replay(child,A+[row],b+[rhs],[j for j in remaining if j!=p])
                       for child,(row,rhs) in zip(node['children'],pairs[p]['options']))
        return False
    return replay(tree,A,b,list(range(len(pairs))))


if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('out',type=Path);a=p.parse_args();run(a.out)
