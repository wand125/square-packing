from fractions import Fraction as F
import pytest
from realize_predicate_pattern import search

BOX=list(map(F,[0,1,0,1,0,0]))
def test_realizes_strict_outside_with_exact_values():
    # x-1/4>0 and x-3/4<=0.
    p=[[(x-F(1,4),F(0),F(0)) for x,y in [(0,0),(0,1),(1,0),(1,1)]],
       [(x-F(3,4),F(0),F(0)) for x,y in [(0,0),(0,1),(1,0),(1,1)]]]
    r=search(p,[0,1],BOX,steps=1);assert r['best']['pattern_realized']
    x=F(r['best']['pose'][0]);assert F(1,4)<x<=F(3,4)

def test_closed_equality_is_not_a_strict_outside_witness():
    r=search([[(F(0),F(0),F(0))]*4],[0],BOX,steps=1)
    assert not r['best']['pattern_realized'] and not r['exhaustive']

def test_rejects_nonaffine_corner_model():
    p=[[(F(0),F(0),F(0))]*3+[(F(1),F(0),F(0))]]
    with pytest.raises(ValueError):search(p,[0],BOX,steps=1)
