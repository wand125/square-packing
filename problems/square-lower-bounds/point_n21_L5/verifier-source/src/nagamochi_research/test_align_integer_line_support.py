from fractions import Fraction as F
import pytest
from align_integer_line_support import project,run
from probe_external_integer_bridge import read


def test_reflection_and_swap_include_rounding_ties():
    for q in [80,160]:
        for j in range(5*q):
            x,y=F(2*j+1,2*q),F(2)
            a,b=project(x,y,5,q)
            assert project(5-x,y,5,q)==(5-a,b)
            assert project(y,x,5,q)==(b,a)
    with pytest.raises(ValueError):project(F(1,2),1,5,3)


def test_preserves_off_line_points_and_integer_intersections():
    assert project(F(101,100),F(202,100),5,80)==(F(101,100),F(202,100))
    assert project(2,3,5,80)==(2,3)


def test_collision_preserves_mass_and_d4(tmp_path):
    points=set()
    for x,y in [(1000,1001),(1000,1002)]:
        for a,b in [(x,y),(y,x)]:
            points.update([(a,b),(5000-a,b),(a,5000-b),(5000-a,5000-b)])
    p=tmp_path/'source.txt';p.write_text('\n'.join(['5 1','1000','100',str(len(points))]+[f'{x} {y} 7' for x,y in sorted(points)])+'\n')
    out=tmp_path/'aligned.txt';result=run(p,out,80);L,span,W,pts=read(out)
    assert len(pts)<len(points) and sum(w for x,y,w in pts)==7*len(points)
    assert result['total_mass']==str(F(7*len(points),100))
