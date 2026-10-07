"""New rational duals on a fully replayed, weight-independent physical tree.

The support/order and container stay fixed. New uncertain positive points
absent from the old model are safely omitted; all always-captured points may
contribute to the new baseline. No saved source success flags are trusted.
"""
from fractions import Fraction as F
import hashlib,json
from compile_box_capture_rows import contains_all
from replay_capture_margin import replay_capture_margin
from physical_predicate_branch import checked_model
from predicate_branch import solve,replay_dual


def _digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,default=str).encode()).hexdigest()


def _compile(old_points,new_points,source,L):
    old=[tuple(map(F,p)) for p in old_points];new=[tuple(map(F,p)) for p in new_points]
    if any(len(p)!=3 for p in old+new) or [p[:2] for p in old]!=[p[:2] for p in new]:raise ValueError('Changed support/order')
    if any(p[2]<0 for p in old+new):raise ValueError('Negative weight')
    if source.get('proof_type')!='PHYSICAL_PREDICATE_TREE':raise ValueError('Need physical predicate tree')
    checked=replay_capture_margin(old,source,L=L)
    old_cost,rows,baseline,_,_=checked_model(old,source['base'],L)
    plain=source
    while 'base' in plain:plain=plain['base']
    mapped=[F(0)]*len(old_cost);cost=[F(0)]*len(old_cost);next_y=plain['predicates']
    for rec in plain['point_records']:
        ids=rec['predicates'];j=ids[0] if len(ids)==1 else next_y
        if len(ids)>1:next_y+=1
        mapped[j]+=old[rec['point']][2];cost[j]+=new[rec['point']][2]
    if next_y!=len(cost) or mapped!=old_cost:raise ValueError('Source cost mapping mismatch')
    always=[i for i,p in enumerate(old) if contains_all(p[:2],source['box'])]
    if set(always)&{rec['point'] for rec in plain['point_records']}:raise ValueError('Overlapping baseline and uncertain costs')
    if sum((old[i][2] for i in always),F())!=baseline:raise ValueError('Baseline mapping mismatch')
    B=sum((new[i][2] for i in always),F())
    binding=dict(L=str(F(L)),box=source['box'],source_proof_sha256=_digest(source),
                 old_points_sha256=_digest(old),new_points_sha256=_digest(new))
    return cost,rows,B,binding,checked


def _replay_tree(source,tree,cost,rows,B):
    k=source['kind']
    if k=='CUT':
        if tree['kind']!='CUT':raise ValueError('Changed cut structure')
        return _replay_tree(source['child'],tree['child'],cost,rows+[source['cut']['row']],B)
    if k=='BRANCH':
        j=source['variable']
        if tree['kind']!='BRANCH' or tree['variable']!=j or set(tree['children'])!={'0','1'}:raise ValueError('Changed or incomplete branches')
        values=[_replay_tree(source['children'][str(t)],tree['children'][str(t)],cost,rows+[dict(terms=[(j,1 if t else -1)],rhs=t)],B) for t in (0,1)]
        values=[v for v in values if v is not None];return min(values) if values else None
    if k=='EMPTY':
        if tree['kind']!='SOURCE_EMPTY':raise ValueError('Changed empty branch')
        return None
    if tree['kind']!='BOUND':raise ValueError('Unproved new leaf')
    value=B+replay_dual(cost,rows,tree['dual'])
    if str(value)!=tree['lower']:raise ValueError('New lower mismatch')
    return value


def reoptimize(old_points,new_points,source,L):
    cost,rows,B,binding,_=_compile(old_points,new_points,source,L)
    def visit(node,active):
        k=node['kind']
        if k=='CUT':return dict(kind=k,child=visit(node['child'],active+[node['cut']['row']]))
        if k=='BRANCH':
            j=node['variable'];return dict(kind=k,variable=j,children={str(t):visit(node['children'][str(t)],active+[dict(terms=[(j,1 if t else -1)],rhs=t)]) for t in (0,1)})
        if k=='EMPTY':return dict(kind='SOURCE_EMPTY')
        solution,dual=solve(cost,active)
        if dual is None:raise RuntimeError('No verified new dual: '+solution.message)
        return dict(kind='BOUND',dual=dual,lower=str(B+replay_dual(cost,active,dual)))
    tree=visit(source['tree'],rows);q=_replay_tree(source['tree'],tree,cost,rows,B)
    return dict(binding=binding,tree=tree,baseline=str(B),cost=list(map(str,cost)),
                lower=str(q) if q is not None else None,vacuous=q is None,general_coverage_verified=False)


def replay(old_points,new_points,source,L,artifact):
    cost,rows,B,binding,checked=_compile(old_points,new_points,source,L)
    if artifact['binding']!=binding or artifact['cost']!=list(map(str,cost)) or artifact['baseline']!=str(B):raise ValueError('Changed weight/geometry binding')
    q=_replay_tree(source['tree'],artifact['tree'],cost,rows,B)
    if artifact['lower']!=(str(q) if q is not None else None):raise ValueError('Global lower mismatch')
    return dict(lower=artifact['lower'],vacuous=q is None,certified_unit_capture=q is None or q>=1,
                source_replay=checked,new_duals_replayed=True,general_coverage_verified=False)
