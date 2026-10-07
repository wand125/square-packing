from fractions import Fraction as F
from copy import deepcopy
import pytest
from adaptive_angle_cover import run as seed_run
from two_angle_cover import run,verify,patterns
from joint_angle_lp import rotation


def test_shared_capture_and_tampered_floor(tmp_path):
    seed=tmp_path/'seed.json';seed_run(F(4),F(1,100),F(0),seed,True)
    q=run(seed,F(3999,1000),12,tmp_path/'mixed.json',symmetry=True)
    excluded=verify(q)
    assert 1 in excluded and 2 in excluded and 9 not in excluded
    bad=deepcopy(q);bad['cases'][1]['floors'][0]+=1
    with pytest.raises(AssertionError):verify(bad)
    endpoint=run(seed,F(4),12,tmp_path/'endpoint.json',symmetry=True)
    assert 12 not in verify(endpoint)  # Explicit axis-parallel 12-box packing fits.


def test_representative_matches_its_entire_face_pattern():
    points=[(F(x),F(y)) for x,y in ((-1,-1),(-1,0),(0,0),(1,1),(1,0))]
    t=F(1,3);B=F(99,100);d=patterns(points,F(4),t,B,representatives=True);c,s=rotation(t)
    for p,xy in zip(d['patterns'],d['centres']):
        x,y=map(F,xy)
        direct=[i for i,(X,Y) in enumerate(points) if abs(c*(X-x)+s*(Y-y))<B/2 and abs(-s*(X-x)+c*(Y-y))<B/2]
        assert direct==p


def test_axis_type_extends_to_a_two_sided_angle_band():
    from two_angle_cover import axis_band_radius
    from score import square,cross,sub
    B=F(999,1000);h=axis_band_radius(B);inner=square(0,0,B,0)
    for t in (-h,F(0),h):
        outer=square(0,0,1,t)
        assert all(cross(sub(b,a),sub(p,a))>0 for a,b in zip(outer,outer[1:]+outer[:1]) for p in inner)
        c,s=rotation(t);assert abs(c)+abs(s)>=1
