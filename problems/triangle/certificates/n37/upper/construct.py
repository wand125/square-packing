"""Exact packing of 37 unit squares in the equilateral triangle of side v = 9 + 2/sqrt(3).

- Bottom row: 9 axis-parallel squares on the base; at height 1 the width is exactly 9.
- Above it lies an equilateral triangle of side 9 (vertices (1/sqrt3, 1), (v - 1/sqrt3, 1), apex).
  In it, 28 squares in the shape of Friedman's n = 28 packing: axis-parallel rows of 7, 6, 3, 2 pushed against
  the left side, a 3 + 2 block aligned with the right side and a 3 + 2 block aligned with the left side.
Coordinates are written as [p, q] meaning p + q*sqrt(3), with p, q rationals given as strings.
Usage: python construct.py out.json
"""
import json, sys
from fractions import Fraction as F

class Q3:
    def __init__(s, p, q=0): s.p, s.q = F(p), F(q)
    def __add__(s, o): o = o if isinstance(o, Q3) else Q3(o); return Q3(s.p + o.p, s.q + o.q)
    __radd__ = __add__
    def __mul__(s, o): o = o if isinstance(o, Q3) else Q3(o); return Q3(s.p*o.p + 3*s.q*o.q, s.p*o.q + s.q*o.p)
    __rmul__ = __mul__
    def __neg__(s): return Q3(-s.p, -s.q)
    def __sub__(s, o): return s + (-(o if isinstance(o, Q3) else Q3(o)))
    def j(s): return [str(s.p), str(s.q)]

R3 = Q3(0, 1); INV = Q3(0, F(1, 3))          # sqrt3 and 1/sqrt3
V = Q3(9, F(2, 3))                            # 9 + 2/sqrt3
A_, B_, C_, D_ = F(3), F(89, 25), F(53, 10), F(23, 4)   # block offsets along the sides of the side-9 triangle

def pt(x, y): return (x if isinstance(x, Q3) else Q3(x), y if isinstance(y, Q3) else Q3(y))
def sq_axis(x0, y0): return [pt(x0, y0), pt(x0 + 1, y0), pt(x0 + 1, y0 + 1), pt(x0, y0 + 1)]
def sq_frame(o, u, n, s0, t0):
    def P(s, t): return pt(o[0] + s*u[0] + t*n[0], o[1] + s*u[1] + t*n[1])
    return [P(s0, t0), P(s0 + 1, t0), P(s0 + 1, t0 + 1), P(s0, t0 + 1)]

def squares():
    out = []
    for i in range(9):                                            # bottom row
        out.append(sq_axis(INV + i, 0))
    ox, oy = INV, Q3(1)                                           # left corner of the side-9 triangle
    for j, k in enumerate([7, 6, 3, 2]):                          # rows of the n = 28 part
        for i in range(k):
            out.append(sq_axis(ox + (j + 1)*INV + i, oy + j))
    half = Q3(F(1, 2)); h3 = Q3(0, F(1, 2))                       # 1/2 and sqrt3/2
    P1 = (ox + 9, oy); P0 = (ox, oy)
    ur, nr = (-half, h3), (-h3, -half)                             # up the right side, inward normal
    ul, nl = (half, h3), (h3, -half)                               # up the left side, inward normal
    for t0, ss in ((0, [A_, A_ + 1, A_ + 2]), (1, [B_, B_ + 1])):
        out += [sq_frame(P1, ur, nr, s, t0) for s in ss]
    for t0, ss in ((0, [C_, C_ + 1, C_ + 2]), (1, [D_, D_ + 1])):
        out += [sq_frame(P0, ul, nl, s, t0)[::-1] for s in ss]     # this frame is clockwise: reverse
    return out

if __name__ == "__main__":
    sq = squares(); assert len(sq) == 37
    tri = [pt(0, 0), pt(V, 0), pt(V*F(1, 2), V*Q3(0, F(1, 2)))]
    verts = [[c.j() for c in v] for v in tri]
    json.dump({"format": "packing-certificate/1", "problem": "squares in an equilateral triangle, n = 37", "n": 37,
               "field": {"generator": "sqrt3", "minpoly": ["-3", "0", "1"], "interval": ["1", "2"]},
               "number_format": "each number is [p, q] meaning p + q*sqrt(3)",
               "container": {"kind": "equilateral_triangle", "side": V.j(), "vertices": verts},
               "side": V.j(), "triangle": verts,
               "squares": [[[c.j() for c in v] for v in s] for s in sq]}, open(sys.argv[1], "w"), indent=1)
    print("wrote", sys.argv[1])
