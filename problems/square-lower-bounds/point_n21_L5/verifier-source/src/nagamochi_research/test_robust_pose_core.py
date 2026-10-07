from fractions import Fraction as F
from mixed_density_check import expand,evaluate
from robust_pose_core import common_polygon,polygon_lower_bound
from score import square,contains


def model():
    return expand(dict(n=20,L='4',B='9/10',rectangles=[dict(rectangle=['0','0','4','4'],mass='16')],points=[],total_mass='16'))


def test_common_polygon_inside_every_sampled_core_across_signed_band():
    m=model();box=(F(1),F(11,10),F(1),F(11,10),F(-1,20),F(1,20))
    poly=common_polygon(m,*box);assert poly
    for x in (box[0],sum(box[:2])/2,box[1]):
        for y in (box[2],sum(box[2:4])/2,box[3]):
            for i in range(9):
                t=box[4]+(box[5]-box[4])*i/8
                assert all(contains(square(x,y,m[1],t),p) for p in poly)


def test_fixed_pose_reproduces_exact_score():
    m=model();x,y,t=F(2),F(2),F(-1,3)
    assert polygon_lower_bound(m,x,x,y,y,t,t)==F(evaluate(m,x,y,t)['score'])
