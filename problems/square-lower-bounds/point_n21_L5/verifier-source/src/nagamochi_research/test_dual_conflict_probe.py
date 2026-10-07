from fractions import Fraction as F
from math import lcm
import random
from dual_conflict_probe import separated, intersection
from endpoint_joint_probe import separation
from score import square


def record(x,y,t):
    x,y,t=map(F,(x,y,t));p,q=t.numerator,t.denominator
    d=lcm(x.denominator,y.denominator)
    return (int(x*d),int(y*d),d,q*q-p*p,2*p*q,q*q+p*p)


def test_exact_sat_matches_polygon_separating_axes():
    rng=random.Random(123)
    for _ in range(100):
        args=[(F(rng.randrange(1,40),10),F(rng.randrange(1,40),10),F(rng.randrange(-4,5),10)) for _ in range(2)]
        polys=[square(x,y,1,t) for x,y,t in args]
        assert separated(*(record(*v) for v in args))==(separation(*polys) is not None)


def test_boundary_contact_is_compatible_but_positive_overlap_is_not():
    a=record(0,0,0)
    assert separated(a,record(1,0,0))
    assert not separated(a,record(F(999,1000),0,0))
    assert intersection(square(0,0,1,0),square(1,0,1,0))
    assert not intersection(square(0,0,1,0),square(F(1001,1000),0,1,0))
