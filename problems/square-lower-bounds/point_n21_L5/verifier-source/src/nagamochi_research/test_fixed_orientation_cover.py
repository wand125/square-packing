from fractions import Fraction as F
from copy import deepcopy
import pytest
from fixed_orientation_cover import geometry,run,verify,angle_envelope
from joint_neighbor_family import nonnegative
import sympy as sp


def test_face_pattern_matches_direct_point_membership():
    g=geometry(F(4),F(1,3),F(50,51),4,F(1,200))
    pitch=F(g['pitch']);B=F(g['B'])
    for (i,j),pattern in zip(g['faces'],g['patterns']):
        x,y=(F(i)+F(1,2))*pitch,(F(j)+F(1,2))*pitch
        direct=[n for n,(a,b) in enumerate(g['support_indices'])
                if abs(a*pitch-x)<B/2 and abs(b*pitch-y)<B/2]
        assert direct==pattern


def test_cover_and_missing_face_tamper(tmp_path):
    q=run(F(3999,1000),F(0),F(9999,10000),tmp_path/'proof.json',subdiv=4)
    assert verify(q)['count_upper']==9
    bad=deepcopy(q);bad['geometry']['faces'].pop()
    with pytest.raises(AssertionError):verify(bad)
    bad=deepcopy(q);bad['numerators']=[0]*len(bad['numerators'])
    with pytest.raises(AssertionError):verify(bad)


def test_inner_square_strict_containment_and_sign_rejection():
    with pytest.raises(AssertionError):geometry(4,F(1,3),F(50,51),4,F(1,100))
    t=sp.Symbol('t')
    nonnegative(1-2*t-t*t,t)
    with pytest.raises(AssertionError):nonnegative(-t,t)


def test_exact_angle_envelope_against_polygon_containment():
    from score import square,cross,sub
    from joint_angle_lp import rotation
    t=F(1,3);h=F(1,25);extent,span=angle_envelope(t,h)
    B=F(999999,1000000)/extent;inner=square(0,0,B,t)
    for j in range(21):
        actual=t-h+2*h*F(j,20);outer=square(0,0,1,actual)
        assert sum(rotation(actual))>=span
        assert all(cross(sub(b,a),sub(p,a))>0 for a,b in zip(outer,outer[1:]+outer[:1]) for p in inner)
