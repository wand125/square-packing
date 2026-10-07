from fractions import Fraction as F
import numpy as np
from axis_breakpoint_probe import scores,grid
from mixed_density_check import expand,evaluate


def test_axis_density_and_closed_atoms_match_exact_geometry():
    model=expand(dict(n=12,L='4',B='1/2',total_mass='3',
        rectangles=[dict(rectangle=['1/2','1','3/2','2'],mass='2')],
        points=[dict(point=['1','1'],mass='1')]))
    xs=list(map(F,['1/2','3/4','1','5/4','3/2']))
    actual=scores(model,xs,xs)
    expected=np.array([[float(F(evaluate(model,x,y,F(0))['score'])) for y in xs] for x in xs])
    assert np.max(np.abs(actual-expected))<1e-12
    g,_=grid(model);assert min(g)==F(1,2) and max(g)==F(2)
    assert F(3,4) in g and F(5,4) in g
