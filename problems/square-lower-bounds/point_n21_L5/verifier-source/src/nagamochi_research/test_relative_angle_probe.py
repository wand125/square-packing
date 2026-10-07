from fractions import Fraction as F
from random import Random
from math import lcm
from relative_angle_probe import constraints
from endpoint_joint_probe import separation
from score import square


def record(x,y,t):
    c=(1-t*t)/(1+t*t);s=2*t/(1+t*t)
    d=lcm(x.denominator,y.denominator);r=lcm(c.denominator,s.denominator)
    return [int(x*d),int(y*d),d,int(c*r),int(s*r),r]


def test_against_independent_polygon_projection():
    rng=Random(17)
    for _ in range(200):
        poses=[(F(rng.randrange(-20,21),10),F(rng.randrange(-20,21),10),
                F(rng.randrange(-10,11),10)) for j in range(2)]
        q=constraints(*(record(*p) for p in poses))
        assert q['compatible']==(separation(*(square(x,y,1,t) for x,y,t in poses)) is not None)
        assert not(q['distance_reject'] and q['compatible'])


def test_touching_equal_angle_oblique_pair():
    q=constraints(record(F(0),F(0),F(1,3)),record(F(4,5),F(3,5),F(1,3)))
    assert q['compatible'] and q['xy_overlap'] and q['angle_sum']==1
    assert q['projection']==q['threshold']==1


def test_relative_rotation_cost_and_distance_filter_not_sufficient():
    q=constraints(record(F(0),F(0),F(0)),record(F(1),F(0),F(1,3)))
    assert q['angle_sum']==F(7,5) and q['threshold']==F(6,5)
    assert q['distance_reject'] and not q['compatible']
    q=constraints(record(F(0),F(0),F(0)),record(F(4,5),F(4,5),F(0)))
    assert not q['distance_reject'] and not q['compatible']
