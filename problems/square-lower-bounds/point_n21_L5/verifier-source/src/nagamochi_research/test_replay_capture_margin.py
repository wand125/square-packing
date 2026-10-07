from fractions import Fraction as F
import copy
import pytest
from predicate_branch import solve_tree
from replay_capture_margin import replay_tree_margin


def test_recovers_margin_and_rejects_modified_saved_lower():
    rows=[dict(terms=[(0,1)],rhs=1)];p=solve_tree([F(3,2)],rows)
    assert replay_tree_margin([F(3,2)],rows,0,1,p['tree'])['lower']=='3/2'
    bad=copy.deepcopy(p['tree']);bad['lower']='2'
    with pytest.raises(ValueError):replay_tree_margin([F(3,2)],rows,0,1,bad)


def test_open_branch_is_not_deleted_and_both_children_are_required():
    rows=[dict(terms=[(i,1),(j,1)],rhs=1) for i,j in [(0,1),(0,2),(1,2)]]
    p=solve_tree([1,1,1],rows,target=2,max_nodes=2)
    assert replay_tree_margin([1,1,1],rows,0,2,p['tree'])['lower']=='0'
    bad=copy.deepcopy(p['tree']);del bad['children']['1']
    with pytest.raises(ValueError):replay_tree_margin([1,1,1],rows,0,2,bad)


def test_empty_requires_exact_infeasibility_and_negative_cost_rejected():
    rows=[dict(terms=[(0,1)],rhs=1),dict(terms=[(0,-1)],rhs=0)]
    p=solve_tree([0],rows)
    assert replay_tree_margin([0],rows,0,1,p['tree'])['vacuous']
    bad=copy.deepcopy(p['tree']);bad['proof']['lower']='0'
    with pytest.raises(ValueError):replay_tree_margin([0],rows,0,1,bad)
    with pytest.raises(ValueError):replay_tree_margin([-1],rows,0,1,p['tree'])
