from fractions import Fraction as F
import pytest
from verify_angle_clip import verify


def test_exact_wall_equality_retains_axis():
    r=verify(5,['0','1/2','1','2','0','1/4'],0)
    assert r['clipped'] and r['lower_open'] and r['width_at_cut']=='1'
    assert not verify(5,['0','1/2','1','2','0','1/4'],F(1,4))['clipped']


def test_unsafe_clips_rejected():
    with pytest.raises(ValueError):verify(5,['1/2','3/5','1','2','0','1/4'],0)
    with pytest.raises(ValueError):verify(5,['0','1/2','1','2','0','1/2'],F(1,4))
    with pytest.raises(ValueError):verify(5,['0','1/2','1','2','1/8','1/4'],0)
