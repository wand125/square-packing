from fractions import Fraction as F
from mixed_density_check import expand
from robust_pose_core import best_lower_bound
from pose_symmetry import images,cached_bound


def test_signed_pose_images_preserve_exact_bounds_and_cache_once():
    model=expand(dict(n=30,L='4',B='9/10',rectangles=[dict(rectangle=['1/3','1/4','3/2','5/4'],mass='5')],points=[],total_mass='5'))
    box=(F(1),F(11,10),F(3,2),F(8,5),F(1,100),F(1,20))
    bounds=[best_lower_bound(model,*b) for b in images(box,F(4))]
    assert len(images(box,F(4)))==8 and len(set(bounds))==1
    f,cache=cached_bound(model,best_lower_bound,'D4')
    assert all(f(*b)==bounds[0] for b in images(box,F(4)))
    assert len(cache)==1
