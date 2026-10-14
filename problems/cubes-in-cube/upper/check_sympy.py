"""System 1: sympy exact arithmetic. Containment: all 8 vertices in [0,s]^3. Interiors pairwise disjoint:
separating-axis theorem over the 15 axes (3+3 face normals, 9 edge cross products); touching allowed."""
import itertools, sympy as sp
from configs import CONFIGS
r2 = sp.sqrt(2)
def v(x): return sp.Rational(x[0].numerator, x[0].denominator) + sp.Rational(x[1].numerator, x[1].denominator) * r2
def cube(c, R):
    C = sp.Matrix([v(t) for t in c]); M = sp.Matrix(3, 3, lambda i, j: v(R[i][j]))
    assert sp.simplify(M.T * M - sp.eye(3)) == sp.zeros(3) and sp.simplify(M.det() - 1) == 0
    return C, M
def nonneg(e): e = sp.nsimplify(sp.expand(e)); return bool(e >= 0)
def verts(C, M): return [C + M * sp.Matrix([sx, sy, sz]) / 2 for sx, sy, sz in itertools.product((-1, 1), repeat=3)]
def interval(C, M, a):
    hw = sum(abs(sp.expand(a.dot(M[:, j]))) for j in range(3)) / 2; m = a.dot(C); return sp.expand(m - hw), sp.expand(m + hw)
for name, (side, cubes) in CONFIGS.items():
    s = v(side); cs = [cube(c, R) for c, R in cubes]
    for C, M in cs:
        for p in verts(C, M):
            assert all(nonneg(p[i]) and nonneg(s - p[i]) for i in range(3)), (name, 'containment')
    for (C1, M1), (C2, M2) in itertools.combinations(cs, 2):
        axes = [M1[:, i] for i in range(3)] + [M2[:, i] for i in range(3)] + [M1[:, i].cross(M2[:, j]) for i in range(3) for j in range(3)]
        ok = False
        for a in axes:
            a = sp.simplify(a)
            if a == sp.zeros(3, 1): continue
            l1, h1 = interval(C1, M1, a); l2, h2 = interval(C2, M2, a)
            if nonneg(l2 - h1) or nonneg(l1 - h2): ok = True; break
        assert ok, (name, 'overlap')
    print(name, 'side', s, 'cubes', len(cs), 'OK (contained, interiors pairwise disjoint)')
# negative control: overlapping stacked 45-degree cubes must be rejected
from configs import S, Z45, q, mid
cs = [cube(c, R) for c, R in [([mid, mid, q('1/2')], Z45), ([mid, mid, q('11/10')], Z45)]]
(C1, M1), (C2, M2) = cs
axes = [M1[:, i] for i in range(3)] + [M2[:, i] for i in range(3)] + [M1[:, i].cross(M2[:, j]) for i in range(3) for j in range(3)]
sep = any(sp.simplify(a) != sp.zeros(3, 1) and (nonneg(interval(C2, M2, a)[0] - interval(C1, M1, a)[1]) or nonneg(interval(C1, M1, a)[0] - interval(C2, M2, a)[1])) for a in axes)
assert not sep; print('control overlap rejected as expected')
