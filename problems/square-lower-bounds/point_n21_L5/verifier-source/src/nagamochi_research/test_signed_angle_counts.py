from fractions import Fraction as F
from signed_angle_counts import domains,compositions
from joint_angle_lp import rotation
from two_angle_cover import patterns


def test_reflection_preserves_support_ids_and_negative_angle_capture():
    points=[(F(x,10),F(y,10)) for x,y in [(0,0),(11,3),(-7,12),(9,-6)]]
    t=F(1,100);B=F(99,100);L=F(3999,1000)
    # Independent negative-angle test at representatives of every reflected face.
    d=patterns([(x,-y) for x,y in points],L,t,B,representatives=True)
    c,s=rotation(-t)
    for ids,xy in zip(d['patterns'],d['centres']):
        x,y=F(xy[0]),-F(xy[1])
        actual=[i for i,(X,Y) in enumerate(points)
                if abs(c*(X-x)+s*(Y-y))<B/2 and abs(-s*(X-x)+c*(Y-y))<B/2]
        assert actual==ids
    assert domains(points,L,t,B,F(0))[2]==patterns([(x,-y) for x,y in points],L,t,B)


def test_compositions_cover_every_count_without_saturation():
    got=compositions(12,9)
    assert set(got)=={(a,b,12-a-b) for a in range(13) for b in range(13-a) if a<=9}
    assert len(got)==85 and (0,6,6) in got and (9,1,2) in got


def test_replay_rejects_missing_composition_and_false_capture():
    from copy import deepcopy
    import pytest
    from signed_angle_counts import verify
    from two_angle_cover import axis_band_radius
    q=dict(model='SIGNED_THREE_BAND_SHARED_MEASURE_V1',n=1,k=3,L='2999/1000',
           t='1/100',h='0',B='99/100',axis_h=str(min(axis_band_radius(F(99,100)),F(1,4000))),
           axis_cap=4,points=[['0','0']],cases=[dict(counts=list(counts),numerators=[1],
           floors=[0,0,0],total=1,gap=-1,excluded=False) for counts in compositions(1,4)])
    assert verify(q)['excluded']==0
    bad=deepcopy(q);bad['cases'].pop()
    with pytest.raises(AssertionError):verify(bad)
    bad=deepcopy(q);bad['cases'][0]['floors'][2]=2
    with pytest.raises(AssertionError):verify(bad)
