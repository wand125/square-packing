import json
from fractions import Fraction as F
import pytest
from robust_conflict_cover import verify,overlap_gap
from test_dual_conflict_probe import record


def inputs(tmp_path,second):
    p=tmp_path/'poses.json';c=tmp_path/'cover.json'
    p.write_text(json.dumps([dict(square=record(F(1,2),F(1,2),0)),dict(square=record(second,F(1,2),0))]))
    c.write_text(json.dumps(dict(cliques=[[0,1]],numerators=[1],denominator=1,finite_upper='1')))
    return p,c


def test_continuous_cover_replay_and_gap(tmp_path):
    p,c=inputs(tmp_path,F(1));out=tmp_path/'result.json';verify(p,c,out)
    d=json.loads(out.read_text());assert d['integer_upper']==1 and F(d['radius'])==F(1,112)
    h=F(d['radius'])
    for sign in [-1,1]:
        a=record(F(1,2)-h,F(1,2)+h,sign*h)
        b=record(1+h,F(1,2)-h,-sign*h)
        assert overlap_gap(a,b)[0]>0


def test_touching_pair_cannot_be_a_robust_conflict(tmp_path):
    p,c=inputs(tmp_path,F(3,2))
    with pytest.raises(AssertionError):verify(p,c,tmp_path/'result.json')


def test_missing_cover_is_rejected(tmp_path):
    p,c=inputs(tmp_path,F(1));d=json.loads(c.read_text());d['cliques']=[[0]];c.write_text(json.dumps(d))
    with pytest.raises(AssertionError):verify(p,c,tmp_path/'result.json')
