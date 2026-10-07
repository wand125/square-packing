from fractions import Fraction as F
from epsilon_cell_envelope import parameters
from direct_fixed_epsilon import sides,TAG
from direct_normalized_search import reconstruct
from score import square,cross,sub
import pytest


def test_larger_cores_are_strictly_inside_scaled_squares():
    for k,e in [(6,F(1,25)),(7,F(7,200)),(8,F(3,100))]:
        cfg=parameters(k,eps_max=e);A,R=sides(cfg,e);sigma=1-e/(k-1)
        h=e/(2*(k-1));t=F(cfg['t']);rh=F(cfg['rot_h'])
        for nominal,side,halfwidth in [(F(0),A,h),(t,R,rh)]:
            for tau in [nominal-halfwidth,nominal,nominal+halfwidth]:
                inner=square(0,0,side,nominal);outer=square(0,0,1/sigma,tau)
                assert all(cross(sub(b,a),sub(p,a))>0 for a,b in zip(outer,outer[1:]+outer[:1]) for p in inner)
    with pytest.raises(AssertionError):
        reconstruct(dict(model=TAG))
