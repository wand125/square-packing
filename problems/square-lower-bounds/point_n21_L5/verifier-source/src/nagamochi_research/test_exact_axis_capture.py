from fractions import Fraction as F
import pytest
from exact_axis_capture import setup,lower_grid
from mixed_density_check import evaluate


def test_integer_lower_grid_matches_across_limbs_and_bounds_exact_values():
    d=dict(n=12,L='4',B='1/2',total_mass='3',rectangles=[dict(rectangle=['1/2','1','3/2','2'],mass='2')],points=[dict(point=['2','2'],mass='1')])
    model,knots=setup(d);a,den=lower_grid(model,knots,8,12,4);b,den2=lower_grid(model,knots,8,12,3)
    assert den==den2 and (a==b).all()
    for i,x in enumerate(knots):
        for j,y in enumerate(knots):assert F(int(a[i,j]),den)<=F(evaluate(model,x,y,F(0))['score'])
    # Point on a core edge is deliberately excluded from the lower bound.
    i=knots.index(F(7,4));j=knots.index(F(2))
    assert F(evaluate(model,knots[i],knots[j],F(0))['score'])-F(int(a[i,j]),den)>=1


def test_overflow_and_unproved_symmetry_are_rejected():
    d=dict(n=12,L='4',B='1/2',total_mass='1',rectangles=[],points=[dict(point=['1','1'],mass='1')])
    with pytest.raises(ValueError,match='D4'):setup(d)
    d.update(points=[],rectangles=[dict(rectangle=['1','1','2','2'],mass='1')])
    m,k=setup(d)
    with pytest.raises(ValueError,match='overflow'):lower_grid(m,k,26,32,20)
