"""Binary case splitting with exact dual leaf proofs, including empty branches.

The LP solver only proposes multipliers/branch variables. Replay uses rational
arithmetic and checks both branches. OPEN leaves never imply certification.
"""
import os
for key in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS'):os.environ[key]='1'
from fractions import Fraction as F
import numpy as np
from scipy.sparse import coo_matrix
from scipy.optimize import linprog
from predicate_lp_capture import rational_bound,replay_certificate
from predicate_conflict import replay_strengthened


def solve(cost,rows):
    rr=[];cc=[];vv=[]
    for k,row in enumerate(rows):
        for j,v in row['terms']:rr.append(k);cc.append(j);vv.append(-float(v))
    matrix=coo_matrix((vv,(rr,cc)),shape=(len(rows),len(cost))).tocsr()
    s=linprog(list(map(float,cost)),A_ub=matrix,b_ub=[-float(r['rhs']) for r in rows],bounds=(0,1),method='highs',options={'threads':1})
    if not s.success:return s,None
    multipliers=[F(round(max(0.,-float(v))*10**12),10**12) for v in s.ineqlin.marginals]
    lower,penalty=rational_bound(cost,rows,multipliers)
    return s,dict(multipliers=list(map(str,multipliers)),lower=str(lower),penalty=str(penalty))


def slack_model(n,rows):
    # Every x in [0,1]^n admits enough slack, each normalized slack is in [0,1].
    relaxed=[]
    for k,row in enumerate(rows):
        merged={}
        for j,v in row['terms']:merged[j]=merged.get(j,F(0))+F(v)
        maximum=max(F(0),F(row['rhs'])-sum((min(F(0),v) for v in merged.values()),F(0)))
        relaxed.append(dict(terms=list(merged.items())+[(n+k,maximum)],rhs=F(row['rhs'])))
    return [F(0)]*n+[F(1)]*len(rows),relaxed


def replay_dual(cost,rows,proof):
    lower,penalty=rational_bound(cost,rows,list(map(F,proof['multipliers'])))
    if str(lower)!=proof['lower'] or str(penalty)!=proof['penalty']:raise ValueError('Dual bound mismatch')
    return lower


def solve_tree(cost,rows,baseline=F(0),target=F(1),max_depth=6,max_nodes=127,cut_proposer=None,cut_verifier=None):
    if max_depth<0 or max_nodes<1:raise ValueError('Invalid branch budget')
    if cut_proposer is not None and cut_verifier is None:raise ValueError('Cuts need verifier')
    cost=list(map(F,cost));baseline=F(baseline);target=F(target);visited=0
    if target<1:raise ValueError('Target below unit capture')
    def visit(active,fixed,depth):
        nonlocal visited
        if visited>=max_nodes:return dict(kind='OPEN',reason='NODE_LIMIT')
        visited+=1;s,proof=solve(cost,active)
        if proof is None:
            if s.status!=2:raise RuntimeError(s.message)
            sc,sr=slack_model(len(cost),active);ss,empty=solve(sc,sr)
            if empty is None:raise RuntimeError('Slack model solve failed')
            return dict(kind='EMPTY' if F(empty['lower'])>0 else 'OPEN_EMPTY_UNVERIFIED',proof=empty)
        lower=baseline+F(proof['lower'])
        node=dict(kind='BOUND',proof=proof,lower=str(lower))
        if lower>=target:return node
        if cut_proposer is not None:
            cut=cut_proposer(s.x)
            if cut is not None:
                row=cut_verifier(cut)
                if sum(float(v)*s.x[j] for j,v in row['terms'])<row['rhs']-1e-9:
                    return dict(kind='CUT',cut=cut,child=visit(active+[row],fixed,depth))
        if depth>=max_depth:node.update(kind='OPEN_BOUND',reason='DEPTH_LIMIT');return node
        fractional=[j for j,x in enumerate(s.x) if j not in fixed and 1e-7<x<1-1e-7]
        if not fractional:node.update(kind='OPEN_BOUND',reason='INTEGRAL_RELAXATION');return node
        j=min(fractional,key=lambda j:abs(float(s.x[j])-.5))
        return dict(kind='BRANCH',variable=j,children={str(value):visit(active+[dict(terms=[(j,1 if value else -1)],rhs=value)],fixed|{j},depth+1) for value in (0,1)})
    tree=visit(rows,set(),0)
    replay=replay_tree(cost,rows,baseline,target,tree,cut_verifier=cut_verifier)
    return dict(tree=tree,visited_nodes=visited,baseline=str(baseline),target=str(target),replay=replay)


def replay_tree(cost,rows,baseline,target,tree,cut_verifier=None):
    cost=list(map(F,cost));baseline=F(baseline);target=F(target);counts={}
    if target<1:raise ValueError('Target below unit capture')
    def visit(node,active,fixed):
        kind=node['kind'];counts[kind]=counts.get(kind,0)+1
        if kind=='CUT':
            if cut_verifier is None:raise ValueError('Missing geometric cut verifier')
            row=cut_verifier(node['cut'])
            return visit(node['child'],active+[row],fixed)
        if kind=='BRANCH':
            j=node['variable']
            if type(j) is not int or not 0<=j<len(cost) or j in fixed or set(node['children'])!={'0','1'}:raise ValueError('Incomplete or invalid branch')
            results=[visit(node['children'][str(v)],active+[dict(terms=[(j,1 if v else -1)],rhs=v)],fixed|{j}) for v in (0,1)]
            return all(results)
        if kind=='OPEN':return False
        if kind in ('EMPTY','OPEN_EMPTY_UNVERIFIED'):
            sc,sr=slack_model(len(cost),active);bound=replay_dual(sc,sr,node['proof'])
            if kind=='EMPTY' and bound<=0:raise ValueError('Unproved empty branch')
            return bound>0
        if kind in ('BOUND','OPEN_BOUND'):
            bound=baseline+replay_dual(cost,active,node['proof'])
            if str(bound)!=node['lower']:raise ValueError('Leaf lower mismatch')
            if kind=='BOUND' and bound<target:raise ValueError('Unproved capture leaf')
            return bound>=target
        raise ValueError('Unknown node kind')
    certified=visit(tree,rows,set())
    return dict(certified_unit_capture=certified,target=str(target),node_counts=counts,general_coverage_verified=False)


def replay_model(points,record):
    if 'base' in record:
        replay_strengthened(points,record);base=record['base'];rows=base['rows']+[cut['row'] for cut in record['cuts']]
    else:
        replay_certificate(points,record['box'],record);base=record;rows=base['rows']
    return list(map(F,base['cost'])),rows,F(base['baseline'])


def cut_callbacks(points,record):
    import json
    from predicate_conflict import geometry_polynomials,find_conflict,verify_sum
    base=record['base'] if 'base' in record else record
    polynomials=geometry_polynomials(points,base,record['box'])
    def propose(x):
        return find_conflict(polynomials,[int(v>=.5) for v in x[:base['predicates']]],record['box'])
    def verify(cut):
        row=verify_sum(polynomials,cut['pattern'],record['box'],cut['multipliers'])
        if json.loads(json.dumps(row))!=json.loads(json.dumps(cut['row'])):raise ValueError('Cut mismatch')
        return row
    return propose,verify
