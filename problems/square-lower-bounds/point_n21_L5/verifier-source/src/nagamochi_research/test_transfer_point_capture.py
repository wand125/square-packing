from fractions import Fraction as F
from itertools import product
from transfer_point_capture import bound,classify,bound_alpha_one

def test_closed_boundary_is_not_excluded():
    box=[F(1),F(1),F(1),F(1),F(0),F(0)]
    assert classify((F(3,2),F(1)),box)=='always'
    assert classify((F(3,2)+F(1,100),F(1)),box)=='outside'

def test_transfer_against_all_relaxed_memberships():
    coords=[(F(1),F(1)),(F(3,2),F(1)),(F(8),F(8))];box=[F(9,10),F(11,10),F(9,10),F(11,10),F(0),F(1,10)]
    old=[F(2,5),F(4,5),F(2)];new=[F(1,5),F(11,10),F(0)];q=F(1)
    v=bound(coords,old,new,box,q);types=[classify(p,box) for p in coords];feasible=[]
    for bits in product([0,1],repeat=3):
        if any(k=='always' and not b or k=='outside' and b for k,b in zip(types,bits)):continue
        if sum(w*b for w,b in zip(old,bits))>=q:feasible.append(sum(w*b for w,b in zip(new,bits)))
    assert feasible and F(v['lower'])<=min(feasible)
    assert F(v['lower'])>=sum(w for w,k in zip(new,types) if k=='always')

def test_alpha_one_matches_full_classification_and_relaxed_memberships():
    coords=[(F(1),F(1)),(F(3,2),F(1)),(F(8),F(8)),(F(0),F(0))]
    box=[F(9,10),F(11,10),F(9,10),F(11,10),F(0),F(1,10)]
    old=[F(2,5),F(4,5),F(2),F(1)];new=[F(2,5),F(7,10),F(0),F(1)];q=F(1)
    result=bound_alpha_one(coords,old,new,box,q);kinds=[classify(p,box) for p in coords]
    expected=q+sum((v-w if k=='always' else min(F(0),v-w) if k=='uncertain' else F(0) for w,v,k in zip(old,new,kinds)),F(0))
    assert F(result['lower'])==expected
    assert result['classified_points']==2 and result['skipped_points']==2
    for bits in product([0,1],repeat=len(coords)):
        if any(k=='always' and not b or k=='outside' and b for k,b in zip(kinds,bits)):continue
        if sum(w*b for w,b in zip(old,bits))>=q:assert expected<=sum(w*b for w,b in zip(new,bits))
    assert F(bound(coords,old,new,box,q)['lower'])>=expected
