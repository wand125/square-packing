"""Checker 2 (independent of checker 1): exact arithmetic in Q(sqrt3) with its own number class, no sympy.
- Each polygon has four sides of length 1 and area 1 (shoelace), so it is a unit square.
- Each square lies in the closed triangle: clipping the square by the triangle leaves area 1.
- Every two squares meet in area 0: the square A clipped by the square B (Sutherland-Hodgman) has area 0.
For convex polygons, intersection area 0 is the same as disjoint interiors.
Usage: python check_clip.py packing.json"""
import json, sys, itertools
from fractions import Fraction as F

class K:
    """p + q*sqrt3, exact; sign by comparing squares."""
    __slots__ = ("p", "q")
    def __init__(s, p, q=F(0)): s.p, s.q = F(p), F(q)
    def __add__(s, o): return K(s.p + o.p, s.q + o.q)
    def __sub__(s, o): return K(s.p - o.p, s.q - o.q)
    def __mul__(s, o): return K(s.p*o.p + 3*s.q*o.q, s.p*o.q + s.q*o.p)
    def inv(s):
        den = s.p*s.p - 3*s.q*s.q
        return K(s.p/den, -s.q/den)
    def __truediv__(s, o): return s*o.inv()
    def sign(s):
        a, b = s.p, s.q                      # sign of a + b*sqrt3
        if a >= 0 and b >= 0: return 0 if (a == 0 and b == 0) else 1
        if a <= 0 and b <= 0: return -1
        t = a*a - 3*b*b                      # opposite signs
        if t == 0: return 0
        return (1 if a > 0 else -1) if t > 0 else (1 if b > 0 else -1)

def rd(c): return K(F(c[0]), F(c[1]))
def cross(o, a, b): return (a[0]-o[0])*(b[1]-o[1]) - (a[1]-o[1])*(b[0]-o[0])
def area2(P):
    s = K(0)
    for i in range(len(P)):
        a, b = P[i], P[(i+1) % len(P)]
        s = s + (a[0]*b[1] - a[1]*b[0])
    return s
def clip(subject, clipper):
    """Sutherland-Hodgman; clipper counter-clockwise and convex."""
    out = subject
    for i in range(len(clipper)):
        a, b = clipper[i], clipper[(i+1) % len(clipper)]
        inp, out = out, []
        if not inp: break
        for j in range(len(inp)):
            p, q = inp[j], inp[(j+1) % len(inp)]
            sp_, sq_ = cross(a, b, p).sign(), cross(a, b, q).sign()
            if sp_ >= 0: out.append(p)
            if sp_ * sq_ < 0:
                cp, cq = cross(a, b, p), cross(a, b, q)
                t = cp / (cp - cq)
                out.append((p[0] + (q[0]-p[0])*t, p[1] + (q[1]-p[1])*t))
    return out

d = json.load(open(sys.argv[1]))
T = [(rd(v[0]), rd(v[1])) for v in d["triangle"]]
S = [[(rd(v[0]), rd(v[1])) for v in s] for s in d["squares"]]
TWO = K(2)
for s in S:
    for i in range(4):
        a, b = s[i], s[(i+1) % 4]
        assert ((a[0]-b[0])*(a[0]-b[0]) + (a[1]-b[1])*(a[1]-b[1]) - K(1)).sign() == 0, "side != 1"
    assert (area2(s) - TWO).sign() == 0, "area != 1 or not counter-clockwise"
assert area2(T).sign() > 0
for s in S:
    c = clip(s, T)
    assert (area2(c) - TWO).sign() == 0, "square not inside the triangle"
bad = []
for i, j in itertools.combinations(range(len(S)), 2):
    c = clip(S[i], S[j])
    if len(c) >= 3 and area2(c).sign() != 0:
        bad.append((i, j))
print(f"checker 2 (Q(sqrt3) clipping): n={len(S)}, unit squares ok, containment ok, pairs with positive overlap area: {bad}")
print("VALID" if not bad else "INVALID")
