import pytest
from assignment_pilot import points,groups,compatible,focus_range,match,case_data,cases,motion_links
from assignment_conflicts import hull,intersects,solve,replay


def test_convexity_forces_intermediate_point_owner():
    # Red endpoints at x=1 and 2 capture the blue midpoint x=1.5.
    rp,bp=points(0),points(1)
    assert compatible((0,1),(1,),rp,bp)
    assert not compatible((0,1),(2,),rp,bp)


def test_hall_certificate_and_bounded_conflict_search():
    matching,witness=match({0:[3],1:[3]},[0,1])
    assert matching is None and witness=={'left':[0,1],'neighbors':[3]}
    ds={0:[2,3],1:[2,3]}
    conflict=lambda a,b:True
    result=solve(ds,conflict)
    assert result['status']=='UNSAT';replay(result['proof_tree'],ds,conflict)
    assert solve(ds,conflict,limit=0)['status']=='UNKNOWN'
    with pytest.raises(AssertionError):replay({'row':0,'children':[]},ds,conflict)


def test_distinct_boxes_cannot_have_crossing_or_touching_hulls():
    assert intersects(hull([(0,0),(2,2)]),hull([(0,2),(2,0)]))
    assert intersects(hull([(0,0),(1,0)]),hull([(1,0),(2,0)]))
    assert not intersects(hull([(0,0),(1,0)]),hull([(2,0),(3,0)]))


def test_freeze_and_known_n33_links():
    # Fixing every row forbids shrinking a base gap 0.8344 to 0.8.
    assert focus_range(set(range(6)),2) is None
    assert all(focus_range(set(),i) is not None for i in range(6))
    rp,bp=points(0),points(1);rg,bg=groups(rp),groups(bp)
    rd=case_data(cases(rg,33)[0],rg,rp);bd=case_data(cases(bg,33)[0],bg,bp)
    links,segments,missing,blocked=motion_links(rd,bd,rg,bg,rp,bp)
    assert len(links)==12 and [len(set(s)) for s in segments]==[6,6]
    assert not missing and not blocked
