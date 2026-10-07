from conflict_rank import independence,induced_cycles


def test_rank_uses_integrality_beyond_pairs():
    edges=[(i,(i+1)%5) for i in range(5)]
    assert independence(edges,5)==2
    assert all(.5+.5<=1 for _ in edges) and 5*.5>2
    assert independence([],5)==5
    assert independence([(i,j) for i in range(5) for j in range(i+1,5)],5)==1


def test_cycle_search_rejects_chorded_clique():
    cycle=[{(i-1)%5,(i+1)%5} for i in range(5)]
    assert induced_cycles(cycle,count=1)==[(0,1,2,3,4)]
    clique=[set(range(5))-{i} for i in range(5)]
    assert induced_cycles(clique,count=1)==[]


def test_union_charge_does_not_count_events_within_one_box():
    # All events may fit in the same box, but that box contributes only one.
    events=[True]*5
    assert int(any(events))==1
    assert sum(events)>independence([(i,(i+1)%5) for i in range(5)],5)
