from fractions import Fraction as F
import pytest
from mixed_density_check import expand,evaluate,centre_lower_bound


def example():
    return dict(n=21,L='4',B='1/2',rectangles=[dict(rectangle=['0','0','4','4'],mass='16')],points=[dict(point=['2','2'],mass='1')],total_mass='17')


def test_uniform_density_and_atom_at_rotated_centres():
    m=expand(example())
    for t in (F(0),F(1,3),F(-2,5)):
        r=evaluate(m,F(2),F(2),t)
        assert F(r['density'])==F(1,4)
        assert F(r['point_score'])==1
    assert F(evaluate(m,F(9,4),F(2),F(0))['point_score'])==1


def test_common_core_is_lower_bound_and_has_exact_axis_value():
    m=expand(example())
    assert centre_lower_bound(m,F(19,10),F(21,10),F(19,10),F(21,10),F(0))==F(109,100)
    for t in (F(0),F(1,3)):
        lower=centre_lower_bound(m,F(19,10),F(21,10),F(19,10),F(21,10),t)
        for x in (F(19,10),F(2),F(21,10)):
            assert lower<=F(evaluate(m,x,F(2),t)['score'])


def test_budget_and_digest_cover_points():
    d=example();before=expand(d)[-1];d['points'][0]['point']=['2','9/4']
    assert expand(d)[-1]!=before
    d['points'][0]['mass']='2'
    with pytest.raises(ValueError,match='budget'):expand(d)


def test_pose_interval_lower_bound_includes_rotations():
    from mixed_density_check import pose_lower_bound
    m=expand(example());lo=F(19,10);hi=F(21,10)
    for t0,t1 in ((F(1,5),F(1,3)),(F(-1,3),F(1,5))):
        lower=pose_lower_bound(m,lo,hi,lo,hi,t0,t1)
        for t in (t0,(t0+t1)/2,t1):
            for x in (lo,F(2),hi):
                assert lower<=F(evaluate(m,x,F(2),t)['score'])
    assert pose_lower_bound(m,F(2),F(2),F(2),F(2),F(1,3),F(1,3))==F(5,4)
    with pytest.raises(ValueError):pose_lower_bound(m,lo,hi,lo,hi,F(1,3),F(1,5))
