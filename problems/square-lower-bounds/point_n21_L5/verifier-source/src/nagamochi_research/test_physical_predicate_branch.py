import copy,json
from fractions import Fraction as F
import pytest
from predicate_lp_capture import certify
from predicate_partition import replay_capture_record
from physical_predicate_conflict import strengthen
from physical_predicate_branch import branch,replay


def fixture():
    points=[(F(1),F(1,2),F(1)),(F(11,10),F(1,2),F(1,10))]
    box=list(map(F,['2/5','3/5','49/100','51/100','0','0']))
    plain=certify(points,box);plain['box']=list(map(str,box))
    return points,strengthen(points,plain,box,2,max_cuts=0)


def test_physical_tree_derives_wall_cut_and_checks_context():
    points,base=fixture();assert F(base['lower'])==0
    saved=json.loads(json.dumps(branch(points,base,2)))
    assert saved['tree']['kind']=='CUT'
    assert replay(points,saved,2)['certified_unit_capture']
    with pytest.raises(ValueError,match='context'):replay_capture_record(points,saved)
    with pytest.raises(ValueError,match='container'):replay(points,saved,3)
    bad=copy.deepcopy(saved);bad['tree']['cut']['pattern'][-4]=0
    with pytest.raises(ValueError,match='walls'):replay(points,bad,2)
    bad=copy.deepcopy(saved);bad['tree']['cut']['row']['rhs']+=1
    with pytest.raises(ValueError,match='cut mismatch'):replay(points,bad,2)
    bad=copy.deepcopy(saved);bad['box'][1]='7/10'
    with pytest.raises(ValueError,match='box'):replay(points,bad,2)


def test_physical_tree_budget_keeps_open_leaf_and_base_bound():
    points,base=fixture()
    result=branch(points,base,2,max_nodes=1)
    checked=replay(points,json.loads(json.dumps(result)),2)
    assert not checked['certified_unit_capture']
    assert checked['node_counts']['OPEN']==1 and checked['lower']==base['lower']


def test_both_physical_branches_and_empty_child_are_required():
    from physical_predicate_branch import checked_model,callbacks
    from predicate_branch import solve_tree
    points,base=fixture();cost,rows,B,polys,n=checked_model(points,base,2)
    propose,verify=callbacks(polys,n,base['box']);children={}
    for value in (0,1):
        fixed=dict(terms=[(0,1 if value else -1)],rhs=value)
        children[str(value)]=solve_tree(cost,rows+[fixed],B,cut_proposer=propose,cut_verifier=verify)['tree']
    record=dict(proof_type='PHYSICAL_PREDICATE_TREE',L='2',box=base['box'],base=base,target='1',
                tree=dict(kind='BRANCH',variable=0,children=children))
    saved=json.loads(json.dumps(record));checked=replay(points,saved,2)
    assert checked['certified_unit_capture'] and checked['node_counts']['EMPTY']==1
    del saved['tree']['children']['0']
    with pytest.raises(ValueError,match='Incomplete'):replay(points,saved,2)
