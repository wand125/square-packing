"""Exact box-wide no-good clauses from nonnegative signed-predicate sums.

A numeric LP proposes multipliers; exact quadratic maxima validate the clause.
The model may fail to find a conflict even when the pattern is unrealizable.
"""
import os
for key in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS'):os.environ[key]='1'
from fractions import Fraction as F
from itertools import product
import numpy as np
from scipy.optimize import linprog
from closed_cover_bridge import predicate,quad_max


def bernstein(poly,lo,hi):
    a,b,c=poly;d=hi-lo
    v=a+b*lo+c*lo*lo;linear=d*(b+2*c*lo)
    return (v,v+linear/2,v+linear+c*d*d)


def verify_sum(polynomials,pattern,box,multipliers):
    """Each predicate is four centre-corner quadratics; z=1 iff g<=0."""
    pattern=list(pattern);multipliers=list(map(F,multipliers));box=list(map(F,box))
    if len(polynomials)!=len(pattern) or len(pattern)!=len(multipliers):raise ValueError('Length mismatch')
    if any(z not in (0,1) for z in pattern) or any(v<0 for v in multipliers):raise ValueError('Invalid pattern or multiplier')
    support=[i for i,v in enumerate(multipliers) if v]
    if not support:raise ValueError('Empty sum')
    sums=[tuple(sum((multipliers[i]*(1 if pattern[i]==0 else -1)*F(polynomials[i][corner][j]) for i in support),F(0)) for j in range(3)) for corner in range(4)]
    upper=max(quad_max(*p,box[4],box[5]) for p in sums)
    strict=any(pattern[i]==0 for i in support)
    if not (upper<0 or (upper==0 and strict)):raise ValueError('Signed sum does not exclude pattern')
    terms=[(i,1 if pattern[i]==0 else -1) for i in support]
    return dict(terms=terms,rhs=1-sum(pattern[i] for i in support),kind='signed_conflict',
                maximum=str(upper),strict_outside_used=strict,support=support)


def find_conflict(polynomials,pattern,box):
    box=list(map(F,box));n=len(pattern)
    if not n:return None
    if len(polynomials)!=n or any(z not in (0,1) for z in pattern):raise ValueError('Invalid pattern')
    values=[]
    for corner in range(4):
        coeffs=[bernstein(tuple(F(x)*(1 if pattern[i]==0 else -1) for x in poly[corner]),box[4],box[5]) for i,poly in enumerate(polynomials)]
        for j in range(3):values.append([float(c[j]) for c in coeffs]+[1.])
    sol=linprog([0.]*n+[-1.],A_ub=values,b_ub=np.zeros(12),A_eq=[([1.]*n)+[0.]],b_eq=[1.],bounds=[(0,None)]*n+[(None,None)],method='highs',options={'threads':1})
    if not sol.success:return None
    proposals=[[F(round(max(0.,float(v))*10**12),10**12) for v in sol.x[:n]]]
    # At a closed-boundary equality, decimal rounding can destroy exact
    # cancellation (e.g. 2/3 versus 1/3). Try rational reconstruction, but
    # accept only a sum that passes the same exact geometry verification.
    proposals.extend([[F(max(0.,float(v))).limit_denominator(limit) for v in sol.x[:n]]
                      for limit in (10**6,10**9)])
    for multipliers in proposals:
        try:row=verify_sum(polynomials,pattern,box,multipliers)
        except ValueError:continue
        return dict(pattern=list(pattern),multipliers=list(map(str,multipliers)),row=row,numerical_margin=float(sol.x[-1]))
    return None


def geometry_polynomials(points,record,box):
    b=list(map(F,box));corners=list(product((b[0],b[1]),(b[2],b[3])))
    return [[predicate(tuple(map(F,points[r['point']][:2])),r['kind'],x,y,F(1)) for x,y in corners] for r in record['predicate_ids']]


def strengthen(points,base,box,max_cuts=16):
    from scipy.sparse import coo_matrix
    from predicate_lp_capture import replay_certificate,rational_bound
    if not isinstance(max_cuts,int) or max_cuts<0:raise ValueError('Invalid cut limit')
    replay_certificate(points,box,base)
    polynomials=geometry_polynomials(points,base,box)
    rows=list(base['rows']);cost=list(map(F,base['cost']));cuts=[];history=[]
    for iteration in range(max_cuts+1):
        rr=[];cc=[];vv=[]
        for k,row in enumerate(rows):
            for j,v in row['terms']:rr.append(k);cc.append(j);vv.append(-v)
        matrix=coo_matrix((vv,(rr,cc)),shape=(len(rows),len(cost))).tocsr()
        sol=linprog(list(map(float,cost)),A_ub=matrix,b_ub=[-r['rhs'] for r in rows],bounds=(0,1),method='highs',options={'threads':1})
        if not sol.success:raise RuntimeError(sol.message)
        multipliers=[F(round(max(0.,-float(v))*10**12),10**12) for v in sol.ineqlin.marginals]
        increment,penalty=rational_bound(cost,rows,multipliers);lower=F(base['baseline'])+increment
        history.append(dict(iteration=iteration,lower=str(lower)))
        if lower>=1:
            stop_reason='CERTIFIED';break
        if iteration==max_cuts:
            stop_reason='CUT_LIMIT';break
        pattern=[int(v>=.5) for v in sol.x[:base['predicates']]]
        cut=find_conflict(polynomials,pattern,box)
        if cut is None:
            stop_reason='NO_CONFLICT_CERTIFICATE';break
        row=cut['row']
        if sum(float(v)*sol.x[j] for j,v in row['terms'])>=row['rhs']-1e-9:
            stop_reason='CUT_NOT_VIOLATED';break
        rows.append(row);cuts.append(cut)
    return dict(base=base,box=list(map(str,box)),cuts=cuts,multipliers=list(map(str,multipliers)),
                lower=str(lower),residual_penalty=str(penalty),history=history,stop_reason=stop_reason,
                certified_unit_capture=lower>=1,general_coverage_verified=False)


def replay_strengthened(points,record):
    import json
    from predicate_lp_capture import replay_certificate,rational_bound
    base=record['base'];box=record['box'];replay_certificate(points,box,base)
    polynomials=geometry_polynomials(points,base,box);rows=list(base['rows'])
    for cut in record['cuts']:
        row=verify_sum(polynomials,cut['pattern'],box,cut['multipliers'])
        if json.loads(json.dumps(row))!=json.loads(json.dumps(cut['row'])):raise ValueError('Conflict row mismatch')
        rows.append(row)
    increment,penalty=rational_bound(list(map(F,base['cost'])),rows,list(map(F,record['multipliers'])))
    lower=F(base['baseline'])+increment
    if str(lower)!=record['lower'] or str(penalty)!=record['residual_penalty']:raise ValueError('Bound mismatch')
    return dict(lower=str(lower),certified_unit_capture=lower>=1,conflicts_replayed=len(record['cuts']),general_coverage_verified=False)
