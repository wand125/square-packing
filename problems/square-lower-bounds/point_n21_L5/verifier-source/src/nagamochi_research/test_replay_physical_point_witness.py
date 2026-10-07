from fractions import Fraction as F
import pytest
from replay_physical_point_witness import contains,replay,bernstein_nonpositive


def test_wall_clipping_and_degenerate_axis():
    box=['2/5','3/5','49/100','51/100','0','0']
    assert contains((1,F(1,2)),2,box)
    assert not contains((F(6,5),F(1,2)),2,box)
    assert replay([(F(1),F(1,2))],[F(1)],2,box,[0])==1
    with pytest.raises(ValueError):replay([(F(1),F(1,2))],[F(1,2)],2,box,[0])
    with pytest.raises(ValueError):replay([(F(1),F(1,2))],[F(1)],2,box,[0,0])


def test_interior_rotation_and_positive_polynomial():
    assert contains((1,1),3,['9/10','11/10','9/10','11/10','0','1/2'])
    assert not contains((2,2),3,['9/10','11/10','9/10','11/10','0','1/2'])
    assert bernstein_nonpositive([-1,0,1],0,1)
    assert not bernstein_nonpositive([0,1,-1],0,1)
