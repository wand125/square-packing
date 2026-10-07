from fractions import Fraction as F
from correlated_pose_core import coefficient_vertices,correlated_polygon,rotation
from robust_pose_core import common_polygon
from score import contains,area


def test_rational_arc_and_old_core_inclusion():
    for lo,hi in [(F(-5,12),F(5,12)),(F(1,10),F(1,3)),(F(-1,3),F(-1,10))]:
        coefficients=coefficient_vertices(lo,hi)
        for i in range(33):assert contains(coefficients,rotation(lo+(hi-lo)*i/32))
        box=(F(3,2),F(8,5),F(7,4),F(9,5),lo,hi)
        old=common_polygon((F(4),F(99,100)),*box)
        new=correlated_polygon((F(4),F(99,100)),*box)
        assert area(new)>=area(old)
        assert all(contains(new,p) for p in old)


def test_single_angle_and_chord_identity():
    for a,b,t in [(F(-1,3),F(1,4),F(1,7)),(F(1,10),F(1,3),F(1,5))]:
        u=rotation(a);v=rotation(b);p=rotation(t)
        gap=sum((u[i]+v[i])*p[i]-u[i]*v[i] for i in range(2))-1
        assert gap==4*(t-a)*(b-t)*(1+a*b)/((1+a*a)*(1+b*b)*(1+t*t))
    assert coefficient_vertices(F(1,3),F(1,3))==[rotation(F(1,3))]


def test_adaptive_bound_commutes_with_d4():
    from correlated_pose_core import adaptive_lower_bound,correlated_lower_bound
    from pose_symmetry import images
    model=(F(4),F(9,10),[(F(0),F(0),F(4),F(4),F(1))],[],F(16),'test')
    box=tuple(map(F,['1','6/5','3/2','8/5','1/20','1/10']))
    bound=adaptive_lower_bound(model,*box)
    assert bound>=correlated_lower_bound(model,*box)
    assert all(adaptive_lower_bound(model,*image)==bound for image in images(box,F(4)))
