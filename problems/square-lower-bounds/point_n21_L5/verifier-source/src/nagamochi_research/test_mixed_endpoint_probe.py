from fractions import Fraction as F
from mixed_density_check import expand, polygon_score
from mixed_endpoint_probe import axis_score, dilate
from score import square


def test_axis_probe_matches_polygon_and_keeps_boundary_atoms_separate():
    data=dict(n=21,L='5',B='9/10',rectangles=[dict(rectangle=['1/3','1/4','9/2','14/3'],mass='10')],points=[dict(point=['1','1'],mass='1/2')],total_mass='21/2')
    model=expand(data)
    for x,y,s in ((F(3,2),F(3,2),F(1)),(F(7,4),F(9,4),F(11,10))):
        q=axis_score(model,x,y,s);d,p=polygon_score(square(x,y,s,F(0)),model[2],model[3])
        assert F(q['density'])==d and F(q['closed_score'])==d+p
    q=axis_score(model,F(3,2),F(3,2),F(1))
    assert F(q['closed_atoms'])==F(1,2) and F(q['interior_atoms'])==0
    moved=expand(dilate(data,F(6)))
    assert moved[-2]==model[-2] and moved[3][0][0]==(F(6,5),F(6,5))
