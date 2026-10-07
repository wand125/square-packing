"""Exact lower certificates for a finite predicate LP on a whole pose box.

Floating LP only proposes nonnegative multipliers. Rational residual accounting
certifies the bound on [0,1] variables. Failure of the relaxation is not a pose.
"""
from fractions import Fraction as F
from itertools import product
from pathlib import Path
import os,json,hashlib,time
for key in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS'):
    os.environ[key]='1'
import numpy as np
from scipy.optimize import linprog
from scipy.sparse import coo_matrix
from closed_cover_bridge import predicate,quad_max
from compile_box_capture_rows import geometry


def polynomial_max(polys,lo,hi):
    return max(quad_max(*p,lo,hi) for p in polys)


def combine(a,b,coefficient):
    return [tuple(x+coefficient*y for x,y in zip(p,q)) for p,q in zip(a,b)]


def rational_bound(cost,rows,multipliers):
    """For A x >= b and 0<=x<=1: lambda*b + sum min(0,c-A^T lambda)."""
    residual=list(map(F,cost));lower=F(0)
    if len(rows)!=len(multipliers):raise ValueError('Multiplier count mismatch')
    for row,weight in zip(rows,multipliers):
        weight=F(weight)
        if weight<0:raise ValueError('Negative multiplier')
        lower+=weight*row['rhs']
        for i,v in row['terms']:
            residual[i]-=weight*v
    penalty=sum((min(F(0),r) for r in residual),F(0))
    return lower+penalty,penalty


def certify(points,box,lambdas=(F(1),F(1,2),F(2)),*,multipliers=None,endpoint_screen=True):
    """points are (x,y,weight), all rational, in physical coordinates."""
    lambdas=tuple(map(F,lambdas))
    box=tuple(map(F,box));points=[tuple(map(F,p)) for p in points]
    if len(box)!=6 or any(box[i]>box[i+1] for i in (0,2,4)) or not 0<=box[4]<=box[5]<=F(1,2):
        raise ValueError('Invalid pose box')
    if any(w<0 for x,y,w in points):raise ValueError('Negative mass')
    if any(F(lam)<=0 for lam in lambdas):raise ValueError('Need positive coefficients')
    x0,x1,y0,y1,t0,t1=box;corners=list(product((x0,x1),(y0,y1)))
    predicates=[];point_records=[];baseline=F(0);dropped=0
    for index,(x,y,w) in enumerate(points):
        # Dropping nonnegative mass is safe even if the coarse filter is loose.
        if not w or x<x0-F(3,4) or x>x1+F(3,4) or y<y0-F(3,4) or y>y1+F(3,4):
            dropped+=1;continue
        uncertain=[];always=[];impossible=False
        for kind in range(4):
            polys=[predicate((x,y),kind,cx,cy,F(1)) for cx,cy in corners]
            upper=polynomial_max(polys,t0,t1)
            lower=-polynomial_max([tuple(-a for a in p) for p in polys],t0,t1)
            if lower>0:impossible=True;break
            if upper<=0:always.append(kind)
            else:uncertain.append((kind,polys))
        if impossible:continue
        if not uncertain:baseline+=w;continue
        ids=[]
        for kind,polys in uncertain:
            ids.append(len(predicates));predicates.append(dict(point=index,kind=kind,polys=polys))
        point_records.append(dict(point=index,weight=w,predicates=ids,always=always))
    cost=[F(0)]*len(predicates);rows=[]
    def row(terms,rhs,**provenance):
        rows.append(dict(terms=terms,rhs=rhs,**provenance))
    for rec in point_records:
        ids=rec['predicates']
        if len(ids)==1:cost[ids[0]]+=rec['weight']
        else:
            y=len(cost);cost.append(rec['weight'])
            row([(y,1)]+[(i,-1) for i in ids],1-len(ids),kind='point_and',point=rec['point'])
    # A positive value at a corner/angle endpoint disproves an everywhere
    # nonpositive relation. Exact screening only rejects candidates; survivors
    # still undergo the original full quadratic maximum test, including vertices.
    endpoint_values=[[a+b*t+c*t*t for a,b,c in p['polys'] for t in (t0,t1)]
                     for p in predicates] if endpoint_screen else None
    def possible(i,j,coefficient,reverse=False):
        if endpoint_values is None:return True
        if reverse:return all(a+coefficient*b>=0 for a,b in zip(endpoint_values[i],endpoint_values[j]))
        return all(a+coefficient*b<=0 for a,b in zip(endpoint_values[i],endpoint_values[j]))
    for i,pi in enumerate(predicates):
        for j in range(i):
            pj=predicates[j];forward=possible(i,j,F(-1));backward=possible(i,j,F(-1),True)
            difference=combine(pi['polys'],pj['polys'],F(-1)) if forward or backward else None
            if forward and polynomial_max(difference,t0,t1)<=0:
                row([(i,1),(j,-1)],0,kind='implication',left=i,right=j)
            if backward and polynomial_max([tuple(-a for a in p) for p in difference],t0,t1)<=0:
                row([(j,1),(i,-1)],0,kind='implication',left=j,right=i)
            for lam in lambdas:
                if not possible(i,j,lam):continue
                total=combine(pi['polys'],pj['polys'],F(lam))
                if polynomial_max(total,t0,t1)<=0:
                    row([(i,1),(j,1)],1,kind='opposed',left=i,right=j,coefficient=str(lam));break
    if not cost or not rows:
        if multipliers is not None and len(multipliers):raise ValueError('Unexpected multipliers')
        return dict(lambda_candidates=list(map(str,lambdas)),status='EXACT_PREDICATE_LP_BOX_LOWER',baseline=str(baseline),lower=str(baseline),
                    predicates=len(predicates),variables=len(cost),constraints=len(rows),dropped_points=dropped,
                    certified_unit_capture=baseline>=1,general_coverage_verified=False,rows=rows,multipliers=[],residual_penalty='0')
    numerical_objective=None
    if multipliers is None:
        rr=[];cc=[];vv=[]
        for k,record in enumerate(rows):
            for i,v in record['terms']:rr.append(k);cc.append(i);vv.append(-v)
        matrix=coo_matrix((vv,(rr,cc)),shape=(len(rows),len(cost))).tocsr()
        solution=linprog(list(map(float,cost)),A_ub=matrix,b_ub=[-r['rhs'] for r in rows],bounds=(0,1),method='highs',options={'threads':1})
        if not solution.success:raise RuntimeError('LP proposal failed: '+solution.message)
        multipliers=[F(round(max(0.,-v)*10**12),10**12) for v in solution.ineqlin.marginals]
        numerical_objective=float(solution.fun)
    else:multipliers=list(map(F,multipliers))
    increment,penalty=rational_bound(cost,rows,multipliers);lower=baseline+increment
    return dict(lambda_candidates=list(map(str,lambdas)),status='EXACT_PREDICATE_LP_BOX_LOWER',baseline=str(baseline),lower=str(lower),
                predicates=len(predicates),variables=len(cost),constraints=len(rows),dropped_points=dropped,
                certified_unit_capture=lower>=1,general_coverage_verified=False,
                numerical_lp_objective=numerical_objective,rows=rows,multipliers=list(map(str,multipliers)),
                residual_penalty=str(penalty),cost=list(map(str,cost)),
                predicate_ids=[dict(point=r['point'],kind=r['kind']) for r in predicates],point_records=[dict(r,weight=str(r['weight'])) for r in point_records])


def replay_certificate(points,box,record):
    rebuilt=certify(points,box,lambdas=tuple(map(F,record['lambda_candidates'])),
                    multipliers=record['multipliers'])
    for field in ('baseline','lower','rows','cost','predicate_ids','point_records','residual_penalty'):
        if json.loads(json.dumps(rebuilt.get(field)))!=json.loads(json.dumps(record.get(field))):
            raise ValueError('Certificate mismatch: '+field)
    return dict(geometry_and_rows_recomputed=True,rational_bound_recomputed=True,
                lower=rebuilt['lower'],certified_unit_capture=rebuilt['certified_unit_capture'])


def run(candidate,boxes,out):
    if out.exists():raise FileExistsError(out)
    L,coordinates,weights,_=geometry(candidate);points=[(x,y,w) for (x,y),w in zip(coordinates,weights)];records=[]
    for label,box in boxes:
        start=time.monotonic();record=certify(points,box);record['replay']=replay_certificate(points,box,record);record.update(label=label,box=list(map(str,box)),seconds=time.monotonic()-start);records.append(record)
        print({k:v for k,v in record.items() if k in ('label','baseline','lower','variables','constraints','seconds','certified_unit_capture')},flush=True)
    result=dict(candidate_sha256=hashlib.sha256(candidate.read_bytes()).hexdigest(),L=str(L),records=records,general_coverage_verified=False)
    out.write_text(json.dumps(result,indent=2));return result
