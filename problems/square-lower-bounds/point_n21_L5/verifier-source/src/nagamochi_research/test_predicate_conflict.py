from fractions import Fraction as F
import pytest
from predicate_conflict import find_conflict,verify_sum,bernstein

BOX=list(map(F,[0,1,0,1,0,1]))
def constant(v):return [(F(v),F(0),F(0))]*4


def test_signed_mix_excludes_only_matching_pattern():
    # g0=.1 and g1=.2: assignment z0=0,z1=1 is impossible; g0-g1<0.
    polys=[constant(F(1,10)),constant(F(1,5))]
    cert=find_conflict(polys,[0,1],BOX);assert cert
    row=verify_sum(polys,[0,1],BOX,cert['multipliers'])
    assert sum(v*[0,1][i] for i,v in row['terms'])<row['rhs']
    assert sum(v*[0,0][i] for i,v in row['terms'])>=row['rhs']


def test_strict_outside_is_needed_on_zero_boundary():
    assert verify_sum([constant(0)],[0],BOX,[1])['rhs']==1
    with pytest.raises(ValueError):verify_sum([constant(0)],[1],BOX,[1])
    with pytest.raises(ValueError):verify_sum([constant(-1)],[0],BOX,[-1])


def test_exact_quadratic_max_rejects_interior_violation():
    poly=[(F(-1,8),F(1),F(-1))]*4
    with pytest.raises(ValueError):verify_sum([poly],[0],BOX,[1])
    assert bernstein((F(1),F(2),F(3)),F(0),F(1))==(F(1),F(2),F(6))


def test_strengthened_saved_certificate_replays_and_rejects_forgery():
    import json
    from predicate_lp_capture import certify
    from predicate_conflict import strengthen,replay_strengthened
    pts=[(F(0),F(0),F(1)),(F(1),F(0),F(1))]
    box=list(map(F,['2/5','3/5','0','0','0','1/100']))
    r=json.loads(json.dumps(strengthen(pts,certify(pts,box),box)))
    assert replay_strengthened(pts,r)['certified_unit_capture']
    r['lower']='2'
    with pytest.raises(ValueError):replay_strengthened(pts,r)


def test_three_way_conflict_without_pairwise_conflict():
    from itertools import product
    corners=list(product((F(0),F(1)),repeat=2))
    polys=[[(x-F(2,5),F(0),F(0)) for x,y in corners],
           [(y-F(2,5),F(0),F(0)) for x,y in corners],
           [(F(7,10)-x-y,F(0),F(0)) for x,y in corners]]
    cert=find_conflict(polys,[0,0,0],BOX)
    assert cert and len(cert['row']['support'])==3
    for i,j in [(0,1),(0,2),(1,2)]:
        assert find_conflict([polys[i],polys[j]],[0,0],BOX) is None
