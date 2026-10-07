from fractions import Fraction as F
from bridge_lp import transform,hits_exact,row_from_hits
from bridge_dominance import mandatory


def test_d4_membership_including_reflected_angle():
    pts=[(F(1),F(1)),(F(3,2),F(1)),(F(7,5),F(7,5))]
    pose=(F(5,4),F(6,5),F(1,4))
    h=hits_exact(pose,pts)
    for g in range(8):
        # Reflection parity determines orientation sign; quarter turns do not
        # change a square's capture set.
        reflected=((g>=4)+bool(g%4&1)+bool(g%4&2))%2
        x,y=transform(pose[:2],g)
        assert hits_exact((x,y,-pose[2] if reflected else pose[2]),[transform(p,g) for p in pts])==h


def test_rule_and_threshold_are_distinct_charges():
    rules=[[[0,1,2],[0,3,4],[1,3,5],[2,4,5]]]
    assert row_from_hits([1,1,1,0,0,0],rules,[],[[0]])==[1,1,1]
    assert row_from_hits([1,1,0,1,0,0],rules,[],[[0]])==[1,1,0]
    assert row_from_hits([1]*6,rules,[],[[0]])==[1,2,1]


def test_fixed_angle_mandatory_point_and_infeasible_bag():
    pts=[(F(0),F(0)),(F(1),F(1)),(F(1,2),F(1,2)),(F(2),F(2))]
    assert mandatory([0,1],pts,F(0))=={0,1,2}
    assert mandatory([0,3],pts,F(0)) is None
