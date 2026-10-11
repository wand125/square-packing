#!/usr/bin/env python3
"""Exact checker for packing certificates (upper bounds), method 1.

Reads a packing file (FORMAT.md) and decides, with exact arithmetic in a real number field
Q(g) = Q[x]/(m), that

  * the container is the claimed polygon (kind and size),
  * every square is a closed unit square lying in the closed container,
  * no two squares have overlapping interiors (touching along edges or at corners is allowed).

Method: containment of a convex square in a convex polygon is checked at the four vertices;
disjointness of interiors by the separating axis theorem (an edge normal of one of the two
squares weakly separates them).

Arithmetic: elements of Q(g) are reduced polynomials in g with Fraction coefficients. The
minimal polynomial is checked to be irreducible, so an element is zero exactly when its
reduced representation is zero. The sign of a nonzero element is found by interval arithmetic
over a rational interval isolating g (checked with a Sturm sequence), refined by bisection.

Standard library only. Usage: python3 check_packing.py FILE.json [--json]
"""

import ast
import json
import sys
from fractions import Fraction

# ---------------------------------------------------------------- rational polynomials
# A polynomial is a list of Fractions, lowest degree first, with no trailing zeros.


def ptrim(p):
    p = list(p)
    while p and p[-1] == 0:
        p.pop()
    return p


def padd(p, q):
    n = max(len(p), len(q))
    return ptrim([(p[i] if i < len(p) else 0) + (q[i] if i < len(q) else 0) for i in range(n)])


def pneg(p):
    return [-c for c in p]


def pmul(p, q):
    if not p or not q:
        return []
    r = [Fraction(0)] * (len(p) + len(q) - 1)
    for i, a in enumerate(p):
        if a:
            for j, b in enumerate(q):
                r[i + j] += a * b
    return ptrim(r)


def pdivmod(p, q):
    p = list(p)
    out = [Fraction(0)] * max(len(p) - len(q) + 1, 1)
    while len(p) >= len(q) and p:
        c = p[-1] / q[-1]
        k = len(p) - len(q)
        out[k] = c
        for i, b in enumerate(q):
            p[i + k] -= c * b
        p = ptrim(p)
    return ptrim(out), p


def pderiv(p):
    return ptrim([i * p[i] for i in range(1, len(p))])


def peval(p, x):
    r = Fraction(0)
    for c in reversed(p):
        r = r * x + c
    return r


def sign(x):
    return (x > 0) - (x < 0)


def sturm_chain(p):
    chain = [p, pderiv(p)]
    while chain[-1]:
        _, r = pdivmod(chain[-2], chain[-1])
        chain.append(pneg(r))
    return chain[:-1]


def sign_changes(signs):
    s = [x for x in signs if x != 0]
    return sum(1 for a, b in zip(s, s[1:]) if a != b)


def roots_in(p, lo, hi):
    """Number of distinct real roots of p in (lo, hi]; hi=None means +infinity."""
    ch = sturm_chain(p)
    at_lo = sign_changes([sign(peval(q, lo)) for q in ch])
    if hi is None:
        at_hi = sign_changes([sign(q[-1]) for q in ch])
    else:
        at_hi = sign_changes([sign(peval(q, hi)) for q in ch])
    return at_lo - at_hi


def has_rational_root(p):
    """Rational root test for a polynomial with rational coefficients."""
    from math import gcd

    den = 1
    for c in p:
        den = den * c.denominator // gcd(den, c.denominator)
    ip = [int(c * den) for c in p]
    if ip[0] == 0:  # root 0
        return True
    a0, an = abs(ip[0]), abs(ip[-1])

    def divisors(m):
        return [d for d in range(1, m + 1) if m % d == 0]

    for u in divisors(a0):
        for v in divisors(an):
            for s in (1, -1):
                if peval(p, Fraction(s * u, v)) == 0:
                    return True
    return False


# ---------------------------------------------------------------- the number field


class Field:
    def __init__(self, spec):
        if spec is None:
            self.name = None
            self.m = [Fraction(0), Fraction(1)]  # Q itself, generator 0 (unused)
            self.deg = 1
            self.lo = self.hi = Fraction(0)
            return
        self.name = spec["generator"]
        self.m = ptrim([Fraction(c) for c in spec["minpoly"]])
        self.deg = len(self.m) - 1
        if self.deg < 1:
            raise ValueError("minpoly must have degree >= 1")
        self.lo, self.hi = Fraction(spec["interval"][0]), Fraction(spec["interval"][1])
        if not self.lo < self.hi:
            raise ValueError("empty generator interval")
        # irreducibility: degree 2 or 3 -> no rational root
        if self.deg in (2, 3):
            if has_rational_root(self.m):
                raise ValueError("minpoly has a rational root, so it is not irreducible")
        elif self.deg > 3:
            try:
                import sympy
            except ImportError:
                raise ValueError("degree > 3 needs sympy for the irreducibility check")
            x = sympy.Symbol("x")
            poly = sympy.Poly([sympy.Rational(str(c)) for c in reversed(self.m)], x)
            if not poly.is_irreducible:
                raise ValueError("minpoly is not irreducible")
        # the interval isolates exactly one root, and the root is not an endpoint
        if peval(self.m, self.lo) == 0 or peval(self.m, self.hi) == 0:
            raise ValueError("generator interval endpoint is a root")
        if roots_in(self.m, self.lo, self.hi) != 1:
            raise ValueError("generator interval does not isolate exactly one root")

    def refine(self):
        mid = (self.lo + self.hi) / 2
        if sign(peval(self.m, mid)) == sign(peval(self.m, self.lo)):
            self.lo = mid
        else:
            self.hi = mid

    def reduce(self, p):
        if self.deg == 1:
            return ptrim(p[:1])
        return pdivmod(p, self.m)[1]

    def inv(self, p):
        if not p:
            raise ZeroDivisionError("division by zero in the number field")
        # extended Euclid: find a with a*p = 1 mod m
        r0, r1 = self.m, p
        s0, s1 = [], [Fraction(1)]
        while len(r1) > 1:
            q, r = pdivmod(r0, r1)
            r0, r1 = r1, r
            s0, s1 = s1, padd(s0, pneg(pmul(q, s1)))
        if not r1:
            raise ZeroDivisionError("not invertible (minpoly reducible?)")
        return self.reduce([c / r1[0] for c in s1])

    def interval(self, p):
        """Rational interval containing the value of p at the generator."""
        lo, hi = Fraction(0), Fraction(0)
        for c in reversed(p):
            prods = [lo * self.lo, lo * self.hi, hi * self.lo, hi * self.hi]
            lo, hi = min(prods) + c, max(prods) + c
        return lo, hi

    def sign(self, p):
        if not p:
            return 0
        if len(p) == 1:
            return sign(p[0])
        for _ in range(4000):
            lo, hi = self.interval(p)
            if lo > 0:
                return 1
            if hi < 0:
                return -1
            self.refine()
        raise RuntimeError("sign not decided")

    def approx(self, p):
        if len(p) <= 1:
            return float(p[0]) if p else 0.0
        while True:
            lo, hi = self.interval(p)
            if hi - lo < Fraction(1, 10**15) * (1 + abs(lo)):
                return float((lo + hi) / 2)
            self.refine()


class Num:
    __slots__ = ("F", "p")

    def __init__(self, F, p):
        self.F, self.p = F, p

    def _c(self, o):
        return o if isinstance(o, Num) else Num(self.F, ptrim([Fraction(o)]))

    def __add__(self, o):
        return Num(self.F, padd(self.p, self._c(o).p))

    __radd__ = __add__

    def __neg__(self):
        return Num(self.F, pneg(self.p))

    def __sub__(self, o):
        return self + (-self._c(o))

    def __rsub__(self, o):
        return self._c(o) - self

    def __mul__(self, o):
        return Num(self.F, self.F.reduce(pmul(self.p, self._c(o).p)))

    __rmul__ = __mul__

    def __truediv__(self, o):
        return Num(self.F, self.F.reduce(pmul(self.p, self.F.inv(self._c(o).p))))

    def __rtruediv__(self, o):
        return self._c(o) / self

    def __pow__(self, k):
        if not isinstance(k, int) or k < 0:
            raise ValueError("only nonnegative integer powers")
        r = Num(self.F, [Fraction(1)])
        for _ in range(k):
            r = r * self
        return r

    def sgn(self):
        return self.F.sign(self.p)

    def is_zero(self):
        return not self.p

    def __float__(self):
        return self.F.approx(self.p)

    def __repr__(self):
        return repr(self.p)


# ---------------------------------------------------------------- reading numbers


class Reader:
    def __init__(self, cert):
        self.F = Field(cert.get("field"))
        self.names = {}
        if self.F.name:
            self.names[self.F.name] = Num(self.F, [Fraction(0), Fraction(1)])
        for k, e in (cert.get("defs") or {}).items():
            self.names[k] = self.num(e)

    def num(self, e):
        if isinstance(e, list):  # coefficients of 1, g, g^2, ...
            return Num(self.F, self.F.reduce(ptrim([Fraction(str(c)) for c in e])))
        if isinstance(e, int):
            return Num(self.F, ptrim([Fraction(e)]))
        if not isinstance(e, str):
            raise ValueError(f"bad number {e!r}")
        return self._ev(ast.parse(e, mode="eval").body)

    def _ev(self, n):
        if isinstance(n, ast.Constant) and isinstance(n.value, int):
            return Num(self.F, ptrim([Fraction(n.value)]))
        if isinstance(n, ast.Name):
            if n.id not in self.names:
                raise ValueError(f"unknown name {n.id}")
            return self.names[n.id]
        if isinstance(n, ast.UnaryOp) and isinstance(n.op, (ast.USub, ast.UAdd)):
            v = self._ev(n.operand)
            return -v if isinstance(n.op, ast.USub) else v
        if isinstance(n, ast.BinOp):
            if isinstance(n.op, ast.Pow):
                if not (isinstance(n.right, ast.Constant) and isinstance(n.right.value, int)):
                    raise ValueError("exponent must be a nonnegative integer literal")
                return self._ev(n.left) ** n.right.value
            a, b = self._ev(n.left), self._ev(n.right)
            if isinstance(n.op, ast.Add):
                return a + b
            if isinstance(n.op, ast.Sub):
                return a - b
            if isinstance(n.op, ast.Mult):
                return a * b
            if isinstance(n.op, ast.Div):
                return a / b
        raise ValueError(f"unsupported expression: {ast.dump(n)}")

    def pt(self, q):
        return (self.num(q[0]), self.num(q[1]))


# ---------------------------------------------------------------- geometry


def sub(a, b):
    return (a[0] - b[0], a[1] - b[1])


def dot(a, b):
    return a[0] * b[0] + a[1] * b[1]


def cross(a, b):
    return a[0] * b[1] - a[1] * b[0]


def eq(a, b):
    return (a - b).is_zero()


def edges(P):
    return [sub(P[(i + 1) % len(P)], P[i]) for i in range(len(P))]


def check_convex_ccw(P):
    E = edges(P)
    return all(cross(E[i], E[(i + 1) % len(E)]).sgn() > 0 for i in range(len(E)))


def check_container(kind, P, size, errors):
    E = edges(P)
    k = len(P)
    want = {"square": 4, "rectangle": 4, "equilateral_triangle": 3,
            "right_isosceles_triangle": 3, "regular_hexagon": 6}
    if kind not in want:
        errors.append(f"unknown container kind {kind}")
        return
    if k != want[kind]:
        errors.append(f"{kind} needs {want[kind]} vertices, got {k}")
        return
    if not check_convex_ccw(P):
        errors.append("container vertices are not a convex polygon in counter-clockwise order")
    for v in size.values():
        if v.sgn() <= 0:
            errors.append("container size must be positive")
    if kind == "rectangle":
        w, h = size["width"], size["height"]
        ok = (eq(dot(E[0], E[0]), w * w) and eq(dot(E[1], E[1]), h * h)
              and dot(E[0], E[1]).is_zero()
              and all(eq(E[i + 2][j], -E[i][j]) for i in range(2) for j in range(2)))
        if not ok:
            errors.append("container is not the claimed width x height rectangle "
                          "(first edge = width)")
        return
    a = size["side"]
    a2 = a * a
    if kind == "right_isosceles_triangle":
        # right angle at vertex 0; legs P0P1 and P0P2 of length a
        u, v = sub(P[1], P[0]), sub(P[2], P[0])
        if not (eq(dot(u, u), a2) and eq(dot(v, v), a2) and dot(u, v).is_zero()):
            errors.append("container is not the claimed right isosceles triangle "
                          "(right angle at the first vertex, legs = side)")
        return
    if not all(eq(dot(e, e), a2) for e in E):
        errors.append("container sides do not all have the claimed length")
    if kind == "square":
        if not all(dot(E[i], E[(i + 1) % 4]).is_zero() for i in range(4)):
            errors.append("container angles are not right angles")
    if kind == "regular_hexagon":
        if not all(eq(dot(E[i], E[(i + 1) % 6]), a2 / 2) for i in range(6)):
            errors.append("container turning angles are not 60 degrees")
    # equilateral triangle: three equal sides suffice


def unit_square(V):
    """Check V (4 vertices, cyclic order) is a unit square; return it in CCW order or None."""
    if len(V) != 4:
        return None
    E = edges(V)
    e0 = E[0]
    if not eq(dot(e0, e0), Num(e0[0].F, [Fraction(1)])):
        return None
    r_ccw = (-e0[1], e0[0])
    if all(eq(E[1][j], r_ccw[j]) for j in range(2)):
        Vc = V
    elif all(eq(E[1][j], -r_ccw[j]) for j in range(2)):
        Vc = [V[0], V[3], V[2], V[1]]
        E = edges(Vc)
        e0 = E[0]
    else:
        return None
    E = edges(Vc)
    for i in range(4):
        r = (-E[i][1], E[i][0])
        if not all(eq(E[(i + 1) % 4][j], r[j]) for j in range(2)):
            return None
    return Vc


def inside(P, q):
    """q in the closed convex CCW polygon P."""
    return all(cross(e, sub(q, P[i])).sgn() >= 0 for i, e in enumerate(edges(P)))


def interiors_disjoint(A, B):
    """Separating axis test for two convex CCW polygons, weak separation allowed."""
    for P, Q in ((A, B), (B, A)):
        for i, e in enumerate(edges(P)):
            # outward side of edge i of P: cross(e, x - P[i]) <= 0 for all x in Q
            if all(cross(e, sub(q, P[i])).sgn() <= 0 for q in Q):
                return True
    return False


# ---------------------------------------------------------------- driver


def expand_square(R, s):
    if isinstance(s, dict) and "axis" in s:
        x, y = R.pt(s["axis"])
        return [(x, y), (x + 1, y), (x + 1, y + 1), (x, y + 1)]
    V = s["vertices"] if isinstance(s, dict) else s
    return [R.pt(q) for q in V]


def check(cert):
    R = Reader(cert)
    errors = []
    C = cert["container"]
    kind = C["kind"]
    size = {k: R.num(C[k]) for k in ("side", "width", "height") if k in C}
    P = [R.pt(q) for q in C["vertices"]]
    check_container(kind, P, size, errors)

    claim = cert.get("side_claim")
    if claim:
        a = size["side"] if "side" in size else size[claim["of"]]
        mp = ptrim([Fraction(str(c)) for c in claim["minpoly"]])
        val = Num(R.F, [Fraction(0)])
        for c in reversed(mp):
            val = val * a + c
        if not val.is_zero():
            errors.append("side_claim: the side is not a root of the given polynomial")
        if claim.get("largest_real_root"):
            lo = Fraction(str(claim["below"]))
            if not (a - lo).sgn() > 0:
                errors.append("side_claim: side is not above the given bound")
            if roots_in(mp, lo, None) != 1:
                errors.append("side_claim: the polynomial has more than one root above the bound")

    squares = []
    for i, s in enumerate(cert["squares"]):
        V = unit_square(expand_square(R, s))
        if V is None:
            errors.append(f"square {i} is not a unit square")
            continue
        squares.append(V)
        bad = [j for j, q in enumerate(V) if not inside(P, q)]
        if bad:
            errors.append(f"square {i} is not inside the container (vertices {bad})")
    n = cert["n"]
    if len(cert["squares"]) != n:
        errors.append(f"n = {n} but the file has {len(cert['squares'])} squares")

    overlaps = []
    for i in range(len(squares)):
        for j in range(i + 1, len(squares)):
            if not interiors_disjoint(squares[i], squares[j]):
                overlaps.append((i, j))
    for i, j in overlaps:
        errors.append(f"squares {i} and {j} have overlapping interiors")

    sizes = {k: float(v) for k, v in size.items()}
    return {
        "checker": "packing_check/check_packing.py (separating axes)",
        "problem": cert.get("problem"),
        "n": n,
        "container": kind,
        "size": {k: C[k] for k in size},
        "size_approx": sizes,
        "squares": len(cert["squares"]),
        "pairs_checked": len(squares) * (len(squares) - 1) // 2,
        "result": "VALID" if not errors else "INVALID",
        "errors": errors,
    }


def main(argv):
    args = [a for a in argv[1:] if not a.startswith("--")]
    if len(args) != 1:
        print(__doc__)
        return 2
    with open(args[0]) as f:
        cert = json.load(f)
    rep = check(cert)
    if "--json" in argv:
        print(json.dumps(rep, indent=1))
    else:
        print(f"{rep['problem']}: n = {rep['n']}, {rep['container']} {rep['size']} "
              f"(~{rep['size_approx']}), {rep['squares']} squares, "
              f"{rep['pairs_checked']} pairs: {rep['result']}")
        for e in rep["errors"]:
            print("  " + e)
    return 0 if rep["result"] == "VALID" else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
