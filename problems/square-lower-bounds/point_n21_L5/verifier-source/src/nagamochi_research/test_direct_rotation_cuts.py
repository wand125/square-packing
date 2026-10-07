from fractions import Fraction as F
from direct_rotation_cuts import extend


def test_quarter_turn_closure_includes_adjacent_pairs_only():
    cells={0:[(-1,-1),(1,-1),(1,1),(-1,1)]}
    box=[(F(-1,10),F(-1,10)),(F(1,10),F(-1,10)),
         (F(1,10),F(1,10)),(F(-1,10),F(1,10))]
    pieces=[[(F(2)+x,y) for x,y in box]]
    for _ in range(3):pieces.append([(-y,x) for x,y in pieces[-1]])
    cuts,proof=extend(cells,pieces,0,1,[(0,1)])
    assert set(cuts)=={(0,1),(1,2),(2,3),(0,3)}
    assert len(proof['derivations'])==3
