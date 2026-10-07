from fractions import Fraction as F
import random
import pytest
from certify_near_axis_sweep import sweep, Signs
from exact_fixed_angle_separator import separate


def test_symbolic_sweep_matches_fixed_angle_on_entire_test_grid():
    rng=random.Random(9282400)
    for L in (F(2),F(3),F(397,100),F(5),F(6)):
        D=100;span=int(L*D)
        # Include coincident boundaries, zero weights and boundary points.
        pts=[(rng.randrange(span+1),rng.randrange(span+1),rng.randrange(6)) for _ in range(20)]
        pts += [(0,0,0),(50,50,3),(150,50,7),(50,150,11),(150,150,13)]
        result=sweep(L,D,pts)
        T=F(result['interval']['upper'])
        assert 0<T<=F(1,1000)
        for t in (T,T/2,T/10**6):
            assert separate(L,D,pts,t)['minimum_numerator']==result['minimum_numerator']


def test_integer_lattice_boundary_jump_and_zero_measure():
    pts=[(x,y,1) for x in (1,3) for y in (1,3)]
    r=sweep(F(2),2,pts)
    assert r['minimum_numerator']==separate(F(2),2,pts,F(r['interval']['upper']))['minimum_numerator']
    assert sweep(F(2),2,[(0,0,0)])['minimum_numerator']==0


def test_sign_replay_rejects_forged_condition():
    s=Signs(F(1,1000));assert s.sign((0,0,1,-10**12))==1
    assert s.T==F(1,2*10**12);s.replay()
    s.conditions[(0,0,1,-10**12)]=-1
    with pytest.raises(AssertionError):s.replay()
    with pytest.raises(ValueError):sweep(5,100,[(1,1,-1)])


def test_dense_positive_grid_against_numeric_sweep():
    # Sparse configurations often have minimum 0, hiding an incorrect rectangle.
    pts=[(x,y,1+(7*x+3*y)%13) for x in range(13) for y in range(13)]
    L,D=F(3),4
    result=sweep(L,D,pts)
    assert result['minimum_numerator']>0
    T=F(result['interval']['upper'])
    for t in (T,T/2,T/10**7):
        assert separate(L,D,pts,t)['minimum_numerator']==result['minimum_numerator']


def test_capture_rectangle_against_rotation_including_quadratic_terms():
    from certify_near_axis_sweep import capture_rectangle
    for x,y,D in ((7,13,10),(3,0,2),(0,9,3)):
        us,vs=capture_rectangle(x,y,D)
        for t in (F(1,1000),F(1,3),F(1,2)):
            a,b,r=1-t*t,2*t,1+t*t
            evaluate=lambda p:sum(c*t**i for i,c in enumerate(p))
            assert tuple(map(evaluate,us))==tuple(2*(a*x+b*y)+s*D*r for s in (-1,1))
            assert tuple(map(evaluate,vs))==tuple(2*(-b*x+a*y)+s*D*r for s in (-1,1))
            if y:
                buggy=2*y-D-4*x*t+(2*y-D)*t*t
                assert buggy!=evaluate(vs[0])


def test_shifted_sweep_both_sides_and_half_angle_endpoint():
    pts=[(x,y,1+(7*x+3*y)%13) for x in range(13) for y in range(13)]
    for center,direction in ((F(1,4),1),(F(1,4),-1),(F(1,3),1),(F(1,3),-1),(F(1,2),-1)):
        result=sweep(F(3),4,pts,center=center,direction=direction)
        T=F(result['parameter_interval']['upper'])
        assert F(result['interval']['lower'])<F(result['interval']['upper'])
        for delta in (T,T/2,T/10**7):
            assert separate(F(3),4,pts,center+direction*delta)['minimum_numerator']==result['minimum_numerator']
    for center,direction in ((F(0),-1),(F(1,2),1),(F(-1),1),(F(1,4),0)):
        with pytest.raises(ValueError):sweep(F(3),4,pts,center=center,direction=direction)


def test_shifted_rectangle_against_direct_physical_rotation():
    from certify_near_axis_sweep import capture_rectangle
    p,q=81,512
    for direction in (-1,1):
        basis=((q*q-p*p,-2*p*q*direction,-q*q),
               (2*p*q,2*q*q*direction),
               (q*q+p*p,2*p*q*direction,q*q))
        us,vs=capture_rectangle(7,13,10,basis=basis)
        for step in (F(1,1000),F(1,10**12)):
            t=F(p,q)+direction*step
            a,b,r=q*q*(1-t*t),q*q*2*t,q*q*(1+t*t)
            evaluate=lambda poly:sum(c*step**i for i,c in enumerate(poly))
            assert tuple(map(evaluate,us))==tuple(2*(7*a+13*b)+s*10*r for s in (-1,1))
            assert tuple(map(evaluate,vs))==tuple(2*(-7*b+13*a)+s*10*r for s in (-1,1))
