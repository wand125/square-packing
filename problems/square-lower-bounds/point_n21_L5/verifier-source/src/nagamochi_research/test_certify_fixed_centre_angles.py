from fractions import Fraction as F
from certify_fixed_centre_angles import run,polynomials


def test_shifted_capture_polynomial():
    cx,cy,t0=F(3,2),F(3,2),F(1,4)
    walls,rows=polynomials(cx,cy,t0,-1,F(3),[(F(2),F(7,4))])
    u=F(1,1000);t=t0-u
    evaluate=lambda p:sum(c*u**i for i,c in enumerate(p))
    expected=2*((1-t*t)*F(1,2)+2*t*F(1,4))-(1+t*t)
    assert evaluate(rows[0][0]) == expected
    assert all(evaluate(p)>0 for p in walls)


def test_closed_corner_capture_differs_from_both_open_sides(tmp_path):
    # D4 orbit of corners of a unit square at t=1/4, plus its centre.
    points={(51,51)}
    for a,b in [(7,23),(23,7)]:
        for sx in (-1,1):
            for sy in (-1,1):points.add((51+sx*a,51+sy*b))
    source=tmp_path/'candidate.txt'
    source.write_text('\n'.join(['3 1','34','1',str(len(points))]+
                               [f'{x} {y} 1' for x,y in sorted(points)])+'\n')
    result=run(source,tmp_path/'result.json',F(3,2),F(3,2),F(1,4))
    assert F(result['nominal_capture']) == 5
    assert all(F(b['capture'])==1 for b in result['branches'])
    assert F(result['minimum_capture']) == 1
    assert result['all_centres_verified'] is False
