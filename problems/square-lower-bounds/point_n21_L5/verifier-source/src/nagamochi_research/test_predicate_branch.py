import copy,json
from fractions import Fraction as F
import pytest
from predicate_branch import solve_tree,replay_tree,slack_model


def triangle():
    return [dict(terms=[(i,1),(j,1)],rhs=1) for i,j in [(0,1),(0,2),(1,2)]]


def test_fractional_triangle_closes_by_binary_branch():
    rows=triangle();proof=json.loads(json.dumps(solve_tree([1,1,1],rows,target=2)))
    assert proof['tree']['kind']=='BRANCH' and proof['replay']['certified_unit_capture']
    assert replay_tree([1,1,1],rows,0,2,proof['tree'])['certified_unit_capture']
    del proof['tree']['children']['1']
    with pytest.raises(ValueError):replay_tree([1,1,1],rows,0,2,proof['tree'])


def test_infeasible_branch_requires_positive_rational_slack_bound():
    rows=[dict(terms=[(0,1)],rhs=1),dict(terms=[(0,-1)],rhs=0)]
    proof=solve_tree([0],rows)
    assert proof['tree']['kind']=='EMPTY' and proof['replay']['certified_unit_capture']
    bad=copy.deepcopy(proof['tree']);bad['proof']['lower']='0'
    with pytest.raises(ValueError):replay_tree([0],rows,0,1,bad)


def test_budget_and_integral_countermodel_remain_open():
    assert not solve_tree([1,1,1],triangle(),target=2,max_depth=0)['replay']['certified_unit_capture']
    assert not solve_tree([1,1,1],triangle(),target=2,max_nodes=1)['replay']['certified_unit_capture']
    p=solve_tree([F(1,2)],[dict(terms=[(0,1)],rhs=1)])
    assert p['tree']['reason']=='INTEGRAL_RELAXATION' and not p['replay']['certified_unit_capture']


def test_geometric_cut_inside_tree_is_replayed():
    from predicate_conflict import verify_sum
    polys=[[(-F(1),F(0),F(0))]*4];box=[0,1,0,1,0,1]
    cut=dict(pattern=[0],multipliers=['1'],row=verify_sum(polys,[0],box,[1]))
    propose=lambda x:cut
    verify=lambda c:verify_sum(polys,c['pattern'],box,c['multipliers'])
    rows=[dict(terms=[(0,1)],rhs=0)]
    proof=solve_tree([1],rows,cut_proposer=propose,cut_verifier=verify)
    assert proof['tree']['kind']=='CUT' and proof['replay']['certified_unit_capture']
    with pytest.raises(ValueError):replay_tree([1],rows,0,1,proof['tree'])
    bad=copy.deepcopy(proof['tree']);bad['cut']['multipliers']=['-1']
    with pytest.raises(ValueError):replay_tree([1],rows,0,1,bad,cut_verifier=verify)
