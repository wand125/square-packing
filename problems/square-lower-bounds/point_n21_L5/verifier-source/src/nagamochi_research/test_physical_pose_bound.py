from fractions import Fraction as F
from physical_pose_bound import restrict_centres,physical_lower_bound
from correlated_pose_core import correlated_lower_bound
from pose_symmetry import images


def test_closed_wall_contact_is_retained():
    t=F(1,3);h=F(7,10)
    box=(h,h,h,h,t,t)
    assert restrict_centres(F(4),box)==box
    assert restrict_centres(F(4),(F(1,2),F(3,5),h,h,t,t)) is None
    assert restrict_centres(F(4),(F(1,2),F(1,2),F(1,2),F(1,2),F(0),F(0))) is not None


def test_wall_restriction_strengthens_and_preserves_d4():
    model=(F(4),F(9,10),[(F(0),F(0),F(4),F(4),F(1))],[],F(16),'test')
    box=tuple(map(F,['1/2','4/5','3/2','8/5','1/4','1/3']))
    value=physical_lower_bound(model,*box)
    assert value>correlated_lower_bound(model,*box)
    assert all(physical_lower_bound(model,*b)==value for b in images(box,F(4)))


def test_adaptive_physical_preserves_d4_and_parent():
    from physical_pose_bound import adaptive_physical_lower_bound
    from full_pose_low_cover import lower_function
    model=(F(4),F(9,10),[(F(0),F(0),F(4),F(4),F(1))],[],F(16),'test')
    box=tuple(map(F,['1/2','4/5','3/2','8/5','1/4','1/3']))
    value=adaptive_physical_lower_bound(model,*box)
    assert value>=physical_lower_bound(model,*box)
    assert all(adaptive_physical_lower_bound(model,*b)==value for b in images(box,F(4)))
    assert lower_function('physical-adaptive1') is adaptive_physical_lower_bound


def test_second_level_is_monotone_and_d4():
    from physical_pose_bound import adaptive_physical_lower_bound,adaptive2_physical_lower_bound
    model=(F(4),F(9,10),[(F(0),F(0),F(4),F(4),F(1))],[],F(16),'test')
    box=tuple(map(F,['1/2','4/5','3/2','8/5','1/4','1/3']))
    value=adaptive2_physical_lower_bound(model,*box)
    assert value>=adaptive_physical_lower_bound(model,*box)
    assert all(adaptive2_physical_lower_bound(model,*b)==value for b in images(box,F(4)))
