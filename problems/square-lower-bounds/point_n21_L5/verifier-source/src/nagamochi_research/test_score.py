from fractions import Fraction as F
from score import square,score,features,template,WEIGHTS,segment_length


def test_central_square_and_total():
    assert score(6,square(3,3,F(101,100),0))==F(101,100)**2
    for k in range(3,11):
        assert sum(c*w for c,w in zip(template(k)[3],WEIGHTS))==k*k-2


def test_corner_exact_components():
    side=F(101,100)
    row=features(4,square(side/2,side/2,side,0))
    assert row==[F(1,10000),F(11,50),F(2),F(0)]
    assert sum(a*b for a,b in zip(row,WEIGHTS))==F(10101,10000)


def test_rational_rotation_and_line_intersection():
    # t=1/3 => cos=4/5, sin=3/5. Horizontal central chord has length 5/4.
    p=square(3,3,1,F(1,3))
    assert segment_length(p,(F(0),F(3)),(F(6),F(3)))==F(5,4)
    assert features(6,p)[0]==1


def test_four_obstruction_witnesses_exact_formulas():
    for k in (4,10):
        for d in (F(1,100),F(1,1000000)):
            side=1+d
            centers=[(side/2,side/2),(F(3,2)-d,side/2),
                     (F(3,2)+d,side/2),(F(3,2)+d,F(3,2)+d)]
            expected=[[d*d,F(1,5)+2*d,2,0],
                      [d*(1-d/2),F(11,10)+2*d,1,0],
                      [d*side,side,0,1],[side*side,0,0,0]]
            assert [features(k,square(x,y,side,0)) for x,y in centers]==expected
