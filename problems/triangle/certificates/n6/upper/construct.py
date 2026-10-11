"""Exact pinwheel packing of 6 unit squares in the equilateral triangle of side v = 2 + 4/sqrt(3).

Two axis-parallel squares stand on the base with bottom-left corners (1/sqrt3, 0) and (1 + 1/sqrt3, 0); the other
four are their images under the rotations by 120 and 240 degrees about the centroid of the triangle. This is the
packing listed in Erich Friedman's table "Squares in Triangles" for n = 5 and n = 6 (Friedman, 1997).
Each number is written as [p, q], meaning p + q*sqrt(3) with rational p, q.
Usage: python construct.py packing.json
"""
import json, sys
from fractions import Fraction as F

class Q3:
    def __init__(s, p, q=0): s.p, s.q = F(p), F(q)
    def __add__(s, o): o = o if isinstance(o, Q3) else Q3(o); return Q3(s.p + o.p, s.q + o.q)
    __radd__ = __add__
    def __mul__(s, o): o = o if isinstance(o, Q3) else Q3(o); return Q3(s.p*o.p + 3*s.q*o.q, s.p*o.q + s.q*o.p)
    __rmul__ = __mul__
    def __sub__(s, o): o = o if isinstance(o, Q3) else Q3(o); return Q3(s.p - o.p, s.q - o.q)
    def j(s): return [str(s.p), str(s.q)]

V = Q3(2, F(4, 3))                                   # 2 + 4/sqrt3
INV = Q3(0, F(1, 3))                                 # 1/sqrt3
G = (V*F(1, 2), V*Q3(0, F(1, 6)))                    # centroid (v/2, v/(2 sqrt3))
C, S = Q3(F(-1, 2)), Q3(0, F(1, 2))                  # cos 120, sin 120

def rot(p):
    x, y = p[0] - G[0], p[1] - G[1]
    return (G[0] + C*x - S*y, G[1] + S*x + C*y)

def squares():
    base = []
    for i in range(2):
        x0 = INV + i
        base.append([(x0, Q3(0)), (x0 + 1, Q3(0)), (x0 + 1, Q3(1)), (x0, Q3(1))])
    out = list(base)
    for _ in range(2):
        base = [[rot(p) for p in s] for s in base]
        out += base
    return out

if __name__ == "__main__":
    sq = squares()
    tri = [(Q3(0), Q3(0)), (V, Q3(0)), (V*F(1, 2), V*Q3(0, F(1, 2)))]
    verts = [[c.j() for c in v] for v in tri]
    json.dump({"format": "packing-certificate/1", "problem": "squares in an equilateral triangle, n = 6", "n": 6,
               "field": {"generator": "sqrt3", "minpoly": ["-3", "0", "1"], "interval": ["1", "2"]},
               "number_format": "each number is [p, q] meaning p + q*sqrt(3)",
               "container": {"kind": "equilateral_triangle", "side": V.j(), "vertices": verts},
               "squares": [[[c.j() for c in v] for v in s] for s in sq]}, open(sys.argv[1], "w"), indent=1)
    print("wrote", sys.argv[1])
