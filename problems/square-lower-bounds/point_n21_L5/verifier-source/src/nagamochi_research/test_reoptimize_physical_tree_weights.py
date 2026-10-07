from fractions import Fraction as F
import copy,json
import pytest
from test_physical_predicate_branch import fixture
from physical_predicate_branch import branch
from reoptimize_physical_tree_weights import reoptimize,replay


def test_reweights_without_losing_wall_cut_and_replays_saved_artifact():
    old,base=fixture();source=branch(old,base,2);new=[(*old[0][:2],F(6,5)),(*old[1][:2],F(0))]
    artifact=json.loads(json.dumps(reoptimize(old,new,source,2)))
    assert replay(old,new,source,2,artifact)['lower']=='6/5'
    assert artifact['tree']['kind']=='CUT'
    bad=copy.deepcopy(artifact);bad['lower']='2'
    with pytest.raises(ValueError):replay(old,new,source,2,bad)


def test_zero_weights_keep_the_same_model_and_negative_or_moved_support_rejected():
    old,base=fixture();source=branch(old,base,2);new=[(*p[:2],F(0)) for p in old]
    artifact=reoptimize(old,new,source,2);assert replay(old,new,source,2,artifact)['lower']=='0'
    with pytest.raises(ValueError):reoptimize(old,[(*p[:2],F(-1)) for p in old],source,2)
    with pytest.raises(ValueError):reoptimize(old,[(p[0]+1,p[1],p[2]) for p in old],source,2)


def test_source_cut_and_changed_new_weights_are_checked():
    old,base=fixture();source=branch(old,base,2);artifact=reoptimize(old,old,source,2)
    bad=copy.deepcopy(source);bad['tree']['cut']['row']['rhs']+=1
    with pytest.raises(ValueError):replay(old,old,bad,2,artifact)
    with pytest.raises(ValueError):replay(old,[(x,y,w*2) for x,y,w in old],source,2,artifact)
