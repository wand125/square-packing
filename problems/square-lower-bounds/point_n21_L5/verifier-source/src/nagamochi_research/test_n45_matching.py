from n45_matching import model, orientation_impossible
from assignment_conflicts import solve, replay


def test_orientation_filter_rejects_triangle_but_keeps_rotated_square():
    # All pair distances pass the diameter cut, but this triangle cannot fit.
    assert orientation_impossible([(0,0),(1400,0),(700,1200)])
    # A rotated 1000-side square; its axis-aligned widths are 1400.
    assert not orientation_impossible([(0,0),(600,800),(-200,1400),(-800,600)])


def test_case_enumeration_and_hull_boundary_contact():
    rp,bp,bg,cases,shapes,conflict=model()
    assert len(cases)==157 and len(shapes)==609
    assert all(len(c['groups'])==45 for c in cases)
    assert sum(bool(c['empty']) for c in cases)==46
    assert all(len(set(i for b in c['groups'] for i in bg[b]))==46-len(c['empty']) for c in cases)
    # Interior-captured point hulls touching is already incompatible.
    for a,b in shapes:
        other=next((e for e in shapes if e[0]==a and e!=(a,b)),None)
        if other is not None:
            assert conflict((a,b),other)
            break


def test_conflict_search_proof_and_limit():
    ds={0:[0,1],1:[0,1]}
    conflict=lambda a,b: True
    r=solve(ds,conflict,20)
    assert r['status']=='UNSAT'
    replay(r['proof_tree'],ds,conflict)
    assert solve(ds,conflict,1)['status']=='UNKNOWN'
