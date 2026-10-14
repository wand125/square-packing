"""System 2 (independent of check_sympy.py): own exact field Q(sqrt2) on Fractions, no sympy.
Containment: every vertex in [0,s]^3. Interiors disjoint: clip cube A's faces by cube B's six closed half-spaces
(exact Sutherland-Hodgman per face, plus B's faces clipped by A for the cap) and compute the exact volume of
A∩B by the divergence theorem; interiors are disjoint iff the volume is exactly 0 (both are convex bodies)."""
import itertools
from fractions import Fraction as F
from configs import CONFIGS
class Q:
    __slots__ = ('a', 'b')
    def __init__(s, a, b=0): s.a = F(a); s.b = F(b)
    def __add__(s, o): o = o if isinstance(o, Q) else Q(o); return Q(s.a + o.a, s.b + o.b)
    __radd__ = __add__
    def __neg__(s): return Q(-s.a, -s.b)
    def __sub__(s, o): return s + (-(o if isinstance(o, Q) else Q(o)))
    def __rsub__(s, o): return Q(o) - s
    def __mul__(s, o): o = o if isinstance(o, Q) else Q(o); return Q(s.a*o.a + 2*s.b*o.b, s.a*o.b + s.b*o.a)
    __rmul__ = __mul__
    def __truediv__(s, o):
        o = o if isinstance(o, Q) else Q(o); n = o.a*o.a - 2*o.b*o.b; assert n != 0
        return s * Q(o.a / n, -o.b / n)
    def sign(s):
        a, b = s.a, s.b
        if a >= 0 and b >= 0: return 0 if a == 0 and b == 0 else 1
        if a <= 0 and b <= 0: return -1
        d = a*a - 2*b*b                        # a and b of opposite signs
        return (1 if a > 0 else -1) if d > 0 else ((1 if b > 0 else -1) if d < 0 else 0)
    def __eq__(s, o): return (s - o).sign() == 0
def V(t): return Q(t[0], t[1])
def dot(u, w): return u[0]*w[0] + u[1]*w[1] + u[2]*w[2]
def sub(u, w): return [u[i] - w[i] for i in range(3)]
def add(u, w): return [u[i] + w[i] for i in range(3)]
def scl(k, u): return [k*x for x in u]
def cross(u, w): return [u[1]*w[2]-u[2]*w[1], u[2]*w[0]-u[0]*w[2], u[0]*w[1]-u[1]*w[0]]
def cube(c, R):
    C = [V(t) for t in c]; M = [[V(R[i][j]) for j in range(3)] for i in range(3)]
    col = [[M[i][j] for i in range(3)] for j in range(3)]
    for i in range(3):
        for j in range(3): assert dot(col[i], col[j]) == (1 if i == j else 0)
    assert dot(cross(col[0], col[1]), col[2]) == 1
    half = [(n, dot(n, C) + Q(F(1, 2))) for a in col for n in (a, scl(Q(-1), a))]   # n.x <= d
    faces = []
    for k in range(3):
        u, w = col[(k+1) % 3], col[(k+2) % 3]
        for sg in (1, -1):
            fc = add(C, scl(Q(F(sg, 2)), col[k]))
            ring = [add(fc, add(scl(Q(F(a, 2)), u), scl(Q(F(b, 2)), w))) for a, b in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
            faces.append(ring if sg == 1 else ring[::-1])   # counter-clockwise seen from outside
    return C, col, half, faces
def clip(poly, n, d):
    out = []
    for i in range(len(poly)):
        p, q2 = poly[i], poly[(i+1) % len(poly)]
        fp, fq = dot(n, p) - d, dot(n, q2) - d
        if fp.sign() <= 0: out.append(p)
        if fp.sign() * fq.sign() < 0:
            t = fp / (fp - fq); out.append(add(p, scl(t, sub(q2, p))))
    return out
def volume(A, B):
    # boundary of A∩B = (faces of A clipped by B) ∪ (faces of B clipped by A); faces lying on a common plane
    # with the same orientation would be counted twice, so take A's copy only when B's face is not coplanar-same.
    tot = Q(0)
    for X, Y in ((A, B), (B, A)):
        for f in X[3]:
            poly = f
            for n, d in Y[2]:
                poly = clip(poly, n, d)
                if len(poly) < 3: break
            if len(poly) < 3: continue
            if X is B and any(all((dot(n, p) - d).sign() == 0 for p in f) and outward_same(f, X, n) for n, d in A[2]): continue
            for i in range(1, len(poly)-1):
                tot = tot + dot(poly[0], cross(poly[i], poly[i+1]))
    return tot / 6
def outward_same(f, X, n):
    c = scl(Q(F(1, 4)), add(add(f[0], f[1]), add(f[2], f[3]))); out = sub(c, X[0])
    return dot(out, n).sign() > 0
for name, (side, cubes) in CONFIGS.items():
    s = V(side); cs = [cube(c, R) for c, R in cubes]
    for C, col, half, faces in cs:
        for sg in itertools.product((-1, 1), repeat=3):
            p = add(C, add(add(scl(Q(F(sg[0], 2)), col[0]), scl(Q(F(sg[1], 2)), col[1])), scl(Q(F(sg[2], 2)), col[2])))
            assert all(x.sign() >= 0 and (s - x).sign() >= 0 for x in p), (name, 'containment')
    for A, B in itertools.combinations(cs, 2):
        vol = volume(A, B); assert vol.sign() >= 0
        assert vol.sign() == 0, (name, 'overlap volume', vol.a, vol.b)
    print(name, 'side', side, 'cubes', len(cs), 'OK (system 2: exact Q(sqrt2), intersection volume 0)')
# negative controls: the checks must reject overlapping or protruding placements
from configs import S, Z45, q, mid
bad = {'overlap': (S, [([mid, mid, q('1/2')], Z45), ([mid, mid, q('11/10')], Z45)]),
       'protrude': (S, [([mid, mid, q('2/5')], Z45)])}
for name, (side, cubes) in bad.items():
    s = V(side); cs = [cube(c, R) for c, R in cubes]; failed = False
    for C, col, half, faces in cs:
        for sg in itertools.product((-1, 1), repeat=3):
            p = add(C, add(add(scl(Q(F(sg[0], 2)), col[0]), scl(Q(F(sg[1], 2)), col[1])), scl(Q(F(sg[2], 2)), col[2])))
            if not all(x.sign() >= 0 and (s - x).sign() >= 0 for x in p): failed = True
    for A, B in itertools.combinations(cs, 2):
        vol = volume(A, B)
        if vol.sign() != 0: failed = True; print('  control', name, 'overlap volume', float(vol.a) + float(vol.b)*2**.5)
    assert failed, name; print('control', name, 'rejected as expected')
