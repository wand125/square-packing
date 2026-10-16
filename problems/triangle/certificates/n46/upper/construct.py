"""Exact packing of 46 unit squares in the equilateral triangle of side v = 10 + 2/sqrt(3).

The layout is Joshua Wolk's n = 46 packing from Erich Friedman's table "Squares in Triangles" (September 2026):
axis-parallel squares (family A) and two families of squares tilted by +60 and -60 degrees (P and M), each
family aligned with one side of the triangle. We read the positions off the published picture, solved a linear
program for the free offsets, and rounded them to rationals with denominator 1000; the exact values are
listed below and are the whole construction.

Each square is given by its centre (cx, cy) and its axis (cos, sin); the other axis is (-sin, cos).
Values are strings "a+b*sqrt3" with rational a, b. The output uses [p, q] meaning p + q*sqrt(3).
Usage: python construct.py out.json
"""
import json, re, sys
from fractions import Fraction as F

SQUARES = [
    ("P", "10069/2000+1/4*sqrt3", "-1/4+10069/2000*sqrt3", "1/2", "0+1/2*sqrt3"),
    ("P", "8647/2000+1/4*sqrt3", "-1/4+8647/2000*sqrt3", "1/2", "0+1/2*sqrt3"),
    ("P", "2373/500+3/4*sqrt3", "-3/4+2373/500*sqrt3", "1/2", "0+1/2*sqrt3"),
    ("P", "191/50+1/4*sqrt3", "-1/4+191/50*sqrt3", "1/2", "0+1/2*sqrt3"),
    ("P", "1697/400+3/4*sqrt3", "-3/4+1697/400*sqrt3", "1/2", "0+1/2*sqrt3"),
    ("M", "12339/2000+5/12*sqrt3", "-1/4+7661/2000*sqrt3", "0+1/2*sqrt3", "1/2"),
    ("P", "3317/1000+1/4*sqrt3", "-1/4+3317/1000*sqrt3", "1/2", "0+1/2*sqrt3"),
    ("P", "3739/1000+3/4*sqrt3", "-3/4+3739/1000*sqrt3", "1/2", "0+1/2*sqrt3"),
    ("P", "1557/400+5/4*sqrt3", "-5/4+1557/400*sqrt3", "1/2", "0+1/2*sqrt3"),
    ("M", "3433/500+5/12*sqrt3", "-1/4+1567/500*sqrt3", "0+1/2*sqrt3", "1/2"),
    ("P", "5627/2000+1/4*sqrt3", "-1/4+5627/2000*sqrt3", "1/2", "0+1/2*sqrt3"),
    ("P", "6471/2000+3/4*sqrt3", "-3/4+6471/2000*sqrt3", "1/2", "0+1/2*sqrt3"),
    ("P", "3389/1000+5/4*sqrt3", "-5/4+3389/1000*sqrt3", "1/2", "0+1/2*sqrt3"),
    ("M", "3493/500-1/12*sqrt3", "-3/4+1507/500*sqrt3", "0+1/2*sqrt3", "1/2"),
    ("M", "14739/2000+5/12*sqrt3", "-1/4+5261/2000*sqrt3", "0+1/2*sqrt3", "1/2"),
    ("P", "231/100+1/4*sqrt3", "-1/4+231/100*sqrt3", "1/2", "0+1/2*sqrt3"),
    ("P", "1093/400+3/4*sqrt3", "-3/4+1093/400*sqrt3", "1/2", "0+1/2*sqrt3"),
    ("P", "5771/2000+5/4*sqrt3", "-5/4+5771/2000*sqrt3", "1/2", "0+1/2*sqrt3"),
    ("M", "14979/2000-1/12*sqrt3", "-3/4+5021/2000*sqrt3", "0+1/2*sqrt3", "1/2"),
    ("M", "7873/1000+5/12*sqrt3", "-1/4+2127/1000*sqrt3", "0+1/2*sqrt3", "1/2"),
    ("M", "14549/2000-7/12*sqrt3", "-5/4+5451/2000*sqrt3", "0+1/2*sqrt3", "1/2"),
    ("A", "3319/1000+0*sqrt3", "1257/500+0*sqrt3", "1", "0"),
    ("M", "7993/1000-1/12*sqrt3", "-3/4+2007/1000*sqrt3", "0+1/2*sqrt3", "1/2"),
    ("M", "16753/2000+5/12*sqrt3", "-1/4+3247/2000*sqrt3", "0+1/2*sqrt3", "1/2"),
    ("A", "289/125+0*sqrt3", "21/8+0*sqrt3", "1", "0"),
    ("M", "3889/500-7/12*sqrt3", "-5/4+1111/500*sqrt3", "0+1/2*sqrt3", "1/2"),
    ("A", "2163/500+0*sqrt3", "349/125+0*sqrt3", "1", "0"),
    ("A", "5333/1000+0*sqrt3", "1257/500+0*sqrt3", "1", "0"),
    ("M", "222/25+5/12*sqrt3", "-1/4+28/25*sqrt3", "0+1/2*sqrt3", "1/2"),
    ("M", "17183/2000-1/12*sqrt3", "-3/4+2817/2000*sqrt3", "0+1/2*sqrt3", "1/2"),
    ("P", "28/25+1/4*sqrt3", "-1/4+28/25*sqrt3", "1/2", "0+1/2*sqrt3"),
    ("A", "2743/1000+0*sqrt3", "1507/1000+0*sqrt3", "1", "0"),
    ("A", "7257/1000+0*sqrt3", "1507/1000+0*sqrt3", "1", "0"),
    ("A", "1441/250+0*sqrt3", "1507/1000+0*sqrt3", "1", "0"),
    ("A", "4757/1000+0*sqrt3", "1507/1000+0*sqrt3", "1", "0"),
    ("A", "15/4+0*sqrt3", "1507/1000+0*sqrt3", "1", "0"),
    ("A", "5/2+1/3*sqrt3", "1/2+0*sqrt3", "1", "0"),
    ("A", "19/2+1/3*sqrt3", "1/2+0*sqrt3", "1", "0"),
    ("A", "17/2+1/3*sqrt3", "1/2+0*sqrt3", "1", "0"),
    ("A", "15/2+1/3*sqrt3", "1/2+0*sqrt3", "1", "0"),
    ("A", "13/2+1/3*sqrt3", "1/2+0*sqrt3", "1", "0"),
    ("A", "11/2+1/3*sqrt3", "1/2+0*sqrt3", "1", "0"),
    ("A", "9/2+1/3*sqrt3", "1/2+0*sqrt3", "1", "0"),
    ("A", "7/2+1/3*sqrt3", "1/2+0*sqrt3", "1", "0"),
    ("A", "3/2+1/3*sqrt3", "1/2+0*sqrt3", "1", "0"),
    ("A", "1/2+1/3*sqrt3", "1/2+0*sqrt3", "1", "0"),
]

class Q3:
    def __init__(s, p, q=0): s.p, s.q = F(p), F(q)
    def __add__(s, o): o = o if isinstance(o, Q3) else Q3(o); return Q3(s.p + o.p, s.q + o.q)
    __radd__ = __add__
    def __mul__(s, o): o = o if isinstance(o, Q3) else Q3(o); return Q3(s.p*o.p + 3*s.q*o.q, s.p*o.q + s.q*o.p)
    __rmul__ = __mul__
    def __neg__(s): return Q3(-s.p, -s.q)
    def __sub__(s, o): return s + (-(o if isinstance(o, Q3) else Q3(o)))
    def j(s): return [str(s.p), str(s.q)]

def parse(t):
    m = re.fullmatch(r"([+-]?[0-9/]+)(?:([+-][0-9/]+)\*sqrt3)?", t.replace(" ", ""))
    assert m, t
    return Q3(F(m.group(1)), F(m.group(2)) if m.group(2) else 0)

V = Q3(10, F(2, 3))                           # 10 + 2/sqrt3
HALF = F(1, 2)

def square(cx, cy, c, s):
    cx, cy, c, s = map(parse, (cx, cy, c, s))
    u, w = (c, s), (-s, c)                    # the two axes
    def P(a, b): return (cx + a*u[0] + b*w[0], cy + a*u[1] + b*w[1])
    return [P(-HALF, -HALF), P(HALF, -HALF), P(HALF, HALF), P(-HALF, HALF)]   # counter-clockwise

if __name__ == "__main__":
    sq = [square(*row[1:]) for row in SQUARES]; assert len(sq) == 46
    tri = [(Q3(0), Q3(0)), (V, Q3(0)), (V*HALF, V*Q3(0, HALF))]
    verts = [[c.j() for c in v] for v in tri]
    json.dump({"format": "packing-certificate/1", "problem": "squares in an equilateral triangle, n = 46", "n": 46,
               "field": {"generator": "sqrt3", "minpoly": ["-3", "0", "1"], "interval": ["1", "2"]},
               "number_format": "each number is [p, q] meaning p + q*sqrt(3)",
               "container": {"kind": "equilateral_triangle", "side": V.j(), "vertices": verts},
               "side": V.j(), "triangle": verts,
               "squares": [[[c.j() for c in v] for v in s] for s in sq]}, open(sys.argv[1], "w"), indent=1)
    print("wrote", sys.argv[1])
