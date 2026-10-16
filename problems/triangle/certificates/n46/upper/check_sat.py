"""Checker 1 (sympy, exact): every polygon is a unit square, lies in the closed triangle, and every two squares
have disjoint interiors (separating axis theorem: some edge normal of one of them separates, touching allowed).
Usage: python check_sat.py packing.json"""
import json, sys, itertools
import sympy as sp
r3 = sp.sqrt(3)
def num(c): return sp.Rational(c[0]) + sp.Rational(c[1])*r3
def sign(e):
    e = sp.nsimplify(sp.expand(e)) if False else sp.expand(e)
    if e == 0: return 0
    return 1 if e.is_positive else -1 if e.is_negative else (_ for _ in ()).throw(ValueError(e))
d = json.load(open(sys.argv[1]))
T = [tuple(map(num, v)) for v in d["triangle"]]
S = [[tuple(map(num, v)) for v in s] for s in d["squares"]]
n = d["n"]; assert len(S) == n
def sub(a, b): return (a[0]-b[0], a[1]-b[1])
def dot(a, b): return a[0]*b[0] + a[1]*b[1]
def cross(a, b): return a[0]*b[1] - a[1]*b[0]
# unit squares, counter-clockwise
for s in S:
    for i in range(4):
        e, f = sub(s[(i+1) % 4], s[i]), sub(s[(i+2) % 4], s[(i+1) % 4])
        assert sign(dot(e, e) - 1) == 0 and sign(dot(e, f)) == 0 and sign(cross(e, f) - 1) == 0, "not a unit square"
# containment: all corners in the closed triangle (counter-clockwise)
assert sign(cross(sub(T[1], T[0]), sub(T[2], T[0]))) > 0
for s in S:
    for p in s:
        for i in range(3):
            assert sign(cross(sub(T[(i+1) % 3], T[i]), sub(p, T[i]))) >= 0, "corner outside"
def separated(a, b):
    for poly in (a, b):
        for i in range(4):
            e = sub(poly[(i+1) % 4], poly[i]); nrm = (e[1], -e[0])
            pa = [sp.expand(dot(nrm, p)) for p in a]; pb = [sp.expand(dot(nrm, p)) for p in b]
            if all(sign(x - y) <= 0 for x in pa for y in pb) or all(sign(y - x) <= 0 for x in pa for y in pb):
                return True
    return False
bad = [(i, j) for i, j in itertools.combinations(range(n), 2) if not separated(S[i], S[j])]
side = num(d["side"])
print(f"checker 1 (sympy SAT): n={n}, side={d['side']}, unit squares ok, containment ok, overlapping pairs: {bad}")
print("VALID" if not bad else "INVALID")
