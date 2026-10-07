from fractions import Fraction as F
from point_boundary_separation import boundary_poses
from score import contains, square


def test_closed_point_edge_crossing_and_physical_containment():
    for t in (F(0), F(1,5), F(-1,5)):
        c,s=(1-t*t)/(1+t*t),2*t/(1+t*t)
        B=F(999999,1000000)
        point=(F(2)+c*B/2,F(2)+s*B/2)
        poses=list(boundary_poses((2,2,t),point,F(4),B))
        assert len(poses)==2
        assert sorted(contains(square(*p[:2], B, p[2]),point) for p in poses)==[False,True]
        assert all(0<=v<=4 for p in poses for corner in square(*p[:2],1,p[2]) for v in corner)


def test_wall_crossing_is_rejected():
    poses=list(boundary_poses((F(1,2),2,0),(0,2),F(4),F(1)))
    assert len(poses)==1
    assert poses[0][0]>F(1,2)
