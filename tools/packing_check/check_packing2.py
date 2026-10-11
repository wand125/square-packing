#!/usr/bin/env python3
"""Exact checker for packing certificates (upper bounds), method 2.

An independent second check of the same file format (FORMAT.md), sharing no code with
check_packing.py. It decides, exactly:

  * the container has the claimed shape and size, from its vertex-to-vertex distances,
  * every square is a unit square (four sides 1, both diagonals sqrt 2),
  * area(square ∩ container) = 1 for every square, so each closed square lies in the container,
  * area(square_i ∩ square_j) = 0 for every pair, so no two interiors overlap.

The intersections are computed by clipping one convex polygon by the other
(Sutherland–Hodgman) in exact arithmetic; the area is the shoelace formula.

Arithmetic: sympy polynomials over QQ reduced modulo the minimal polynomial (checked
irreducible by sympy). Signs: the generator is isolated by sympy's real root isolation and the
element is evaluated in mpmath interval arithmetic, with the isolating interval shrunk until
the sign is decided. An element is zero exactly when its reduced polynomial is zero.

Requires sympy (which includes mpmath). Usage: python3 check_packing2.py FILE.json [--json]
"""

import ast
import json
import sys

import sympy
from mpmath import iv
from sympy import QQ, Poly, Rational, Symbol

X = Symbol("x")


class K:
    """The field Q(g) = Q[x]/(m)."""

    def __init__(self, spec):
        if spec is None:
            self.name, self.m = None, None
            return
        self.name = spec["generator"]
        coeffs = [Rational(c) for c in spec["minpoly"]]
        self.m = Poly(list(reversed(coeffs)), X, domain=QQ)
        if self.m.degree() < 1 or not self.m.is_irreducible:
            raise ValueError("minpoly must be irreducible of degree >= 1")
        lo, hi = Rational(spec["interval"][0]), Rational(spec["interval"][1])
        roots = [r for r in sympy.real_roots(self.m) if lo < r and r < hi]
        if len(roots) != 1:
            raise ValueError("the interval must contain exactly one root of minpoly")
        self.lo, self.hi = lo, hi
        self.eps = Rational(1, 10**8)
        self.box = None

    def gen(self):
        return Poly(X, X, domain=QQ).rem(self.m) if self.m is not None else None

    def const(self, q):
        return Poly(Rational(q), X, domain=QQ)

    def red(self, p):
        return p.rem(self.m) if self.m is not None else p

    def mul(self, a, b):
        return self.red(a * b)

    def div(self, a, b):
        if b.is_zero:
            raise ZeroDivisionError("division by zero")
        if self.m is None:
            return a * Poly(1 / b.LC(), X, domain=QQ)
        return self.red(a * b.invert(self.m))

    def _isolate(self):
        while True:
            ivs = [(Rational(u), Rational(v)) for (u, v), _ in self.m.intervals(eps=self.eps)]
            mine = [(u, v) for u, v in ivs if self.lo < (u + v) / 2 < self.hi]
            if len(mine) == 1:
                return mine[0]
            self.eps /= 2

    def sign(self, p):
        if p.is_zero:
            return 0
        if p.degree() <= 0:
            return 1 if p.LC() > 0 else -1
        for _ in range(60):
            if self.box is None:
                self.box = self._isolate()
            u, v = self.box
            iv.prec = 60 + 4 * int(sympy.log(1 / self.eps, 2) + 1)
            g = iv.mpf([iv.mpf(sympy.Rational(u).p) / sympy.Rational(u).q,
                        iv.mpf(sympy.Rational(v).p) / sympy.Rational(v).q])
            val = iv.mpf(0)
            for c in p.all_coeffs():
                c = Rational(c)
                val = val * g + iv.mpf(c.p) / c.q
            if val.a > 0:
                return 1
            if val.b < 0:
                return -1
            self.eps = self.eps ** 2
            self.box = None
        raise RuntimeError("sign not decided")

    def approx(self, p):
        if self.m is None:
            return float(p.LC()) if not p.is_zero else 0.0
        ivs = [(Rational(u), Rational(v))
               for (u, v), _ in self.m.intervals(eps=Rational(1, 10**30))]
        u, v = [(u, v) for u, v in ivs if self.lo < (u + v) / 2 < self.hi][0]
        return float(p.as_expr().subs(X, (u + v) / 2))


class Ev:
    def __init__(self, k, cert):
        self.k = k
        self.env = {}
        if k.name:
            self.env[k.name] = k.gen()
        for name, e in (cert.get("defs") or {}).items():
            self.env[name] = self(e)

    def __call__(self, e):
        if isinstance(e, list):
            p = Poly(list(reversed([Rational(str(c)) for c in e])) or [0], X, domain=QQ)
            return self.k.red(p)
        if isinstance(e, int):
            return self.k.const(e)
        return self.walk(ast.parse(e, mode="eval").body)

    def walk(self, n):
        k = self.k
        if isinstance(n, ast.Constant) and type(n.value) is int:
            return k.const(n.value)
        if isinstance(n, ast.Name):
            return self.env[n.id]
        if isinstance(n, ast.UnaryOp):
            if isinstance(n.op, ast.USub):
                return -self.walk(n.operand)
            if isinstance(n.op, ast.UAdd):
                return self.walk(n.operand)
        if isinstance(n, ast.BinOp):
            if isinstance(n.op, ast.Pow):
                assert isinstance(n.right, ast.Constant) and type(n.right.value) is int
                assert n.right.value >= 0
                r = k.const(1)
                b = self.walk(n.left)
                for _ in range(n.right.value):
                    r = k.mul(r, b)
                return r
            a, b = self.walk(n.left), self.walk(n.right)
            op = type(n.op)
            if op is ast.Add:
                return a + b
            if op is ast.Sub:
                return a - b
            if op is ast.Mult:
                return k.mul(a, b)
            if op is ast.Div:
                return k.div(a, b)
        raise ValueError("unsupported expression")


def run(cert):
    k = K(cert.get("field"))
    ev = Ev(k, cert)
    mul = k.mul
    errs = []

    def P(q):
        return (ev(q[0]), ev(q[1]))

    def d2(a, b):
        dx, dy = a[0] - b[0], a[1] - b[1]
        return mul(dx, dx) + mul(dy, dy)

    def area2(poly):  # twice the signed area
        s = k.const(0)
        for i in range(len(poly)):
            (x0, y0), (x1, y1) = poly[i], poly[(i + 1) % len(poly)]
            s = s + mul(x0, y1) - mul(x1, y0)
        return s

    def clip(subject, clipper):
        out = list(subject)
        m = len(clipper)
        for i in range(m):
            if not out:
                break
            a, b = clipper[i], clipper[(i + 1) % m]
            ex, ey = b[0] - a[0], b[1] - a[1]

            def f(p):
                return mul(ex, p[1] - a[1]) - mul(ey, p[0] - a[0])

            vals = [f(p) for p in out]
            sg = [k.sign(v) for v in vals]
            new = []
            for j in range(len(out)):
                p, q = out[j], out[(j + 1) % len(out)]
                fp, fq = vals[j], vals[(j + 1) % len(out)]
                if sg[j] >= 0:
                    new.append(p)
                if sg[j] * sg[(j + 1) % len(out)] < 0:
                    t = k.div(fp, fp - fq)
                    new.append((p[0] + mul(t, q[0] - p[0]), p[1] + mul(t, q[1] - p[1])))
            out = new
        return out

    def eq(a, b):
        return (a - b).is_zero

    # ---- container
    C = cert["container"]
    kind = C["kind"]
    V = [P(q) for q in C["vertices"]]
    nv = len(V)
    if k.sign(area2(V)) <= 0:
        errs.append("container is not counter-clockwise")

    def dist(i, j):
        return d2(V[i % nv], V[j % nv])

    if kind == "rectangle":
        w, h = ev(C["width"]), ev(C["height"])
        good = (nv == 4 and k.sign(w) > 0 and k.sign(h) > 0
                and eq(dist(0, 1), mul(w, w)) and eq(dist(2, 3), mul(w, w))
                and eq(dist(1, 2), mul(h, h)) and eq(dist(3, 0), mul(h, h))
                and eq(dist(0, 2), mul(w, w) + mul(h, h)) and eq(dist(1, 3), mul(w, w) + mul(h, h)))
    else:
        a = ev(C["side"])
        a2 = mul(a, a)
        good = k.sign(a) > 0
        if kind == "square":
            good = good and nv == 4 and all(eq(dist(i, i + 1), a2) for i in range(4)) \
                and all(eq(dist(i, i + 2), 2 * a2) for i in range(2))
        elif kind == "equilateral_triangle":
            good = good and nv == 3 and all(eq(dist(i, i + 1), a2) for i in range(3))
        elif kind == "right_isosceles_triangle":
            good = good and nv == 3 and eq(dist(0, 1), a2) and eq(dist(0, 2), a2) \
                and eq(dist(1, 2), 2 * a2)
        elif kind == "regular_hexagon":
            good = good and nv == 6 and all(eq(dist(i, i + 1), a2) for i in range(6)) \
                and all(eq(dist(i, i + 2), 3 * a2) for i in range(6)) \
                and all(eq(dist(i, i + 3), 4 * a2) for i in range(3))
        else:
            good = False
    if not good:
        errs.append(f"container is not the claimed {kind}")

    # ---- side claim: the side is the largest real root of the given polynomial
    sc = cert.get("side_claim")
    if sc:
        a = ev(C[sc.get("of", "side")])
        cs = [Rational(str(c)) for c in sc["minpoly"]]
        val = k.const(0)
        for c in reversed(cs):
            val = mul(val, a) + k.const(c)
        if not val.is_zero:
            errs.append("side_claim: not a root")
        if sc.get("largest_real_root"):
            # disjoint isolating intervals of all real roots, in increasing order; a rational q
            # between the second largest and the largest root separates them
            ivs = sorted((Rational(u), Rational(v))
                         for (u, v), _ in Poly(list(reversed(cs)), X, domain=QQ).intervals())
            if len(ivs) >= 2:
                q = ivs[-1][0]
                if not (ivs[-2][1] <= q and k.sign(a - k.const(q)) > 0):
                    errs.append("side_claim: not the largest real root")

    # ---- squares
    sqs = []
    one = k.const(1)
    for i, s in enumerate(cert["squares"]):
        if isinstance(s, dict) and "axis" in s:
            x, y = P(s["axis"])
            Q = [(x, y), (x + one, y), (x + one, y + one), (x, y + one)]
        else:
            Q = [P(q) for q in (s["vertices"] if isinstance(s, dict) else s)]
        ok = (len(Q) == 4 and all(eq(d2(Q[j], Q[(j + 1) % 4]), one) for j in range(4))
              and eq(d2(Q[0], Q[2]), 2 * one) and eq(d2(Q[1], Q[3]), 2 * one))
        if not ok:
            errs.append(f"square {i}: not a unit square")
            continue
        A = area2(Q)
        if k.sign(A) < 0:
            Q = Q[::-1]
        sqs.append((i, Q))
        if not eq(area2(clip(Q, V)), 2 * one):
            errs.append(f"square {i}: not contained in the container")
    if len(cert["squares"]) != cert["n"]:
        errs.append("number of squares differs from n")

    for x in range(len(sqs)):
        for y in range(x + 1, len(sqs)):
            (i, A), (j, B) = sqs[x], sqs[y]
            I = clip(A, B)
            if len(I) >= 3 and not area2(I).is_zero:
                errs.append(f"squares {i} and {j}: interiors overlap")

    size = {key: C[key] for key in ("side", "width", "height") if key in C}
    return {
        "checker": "packing_check/check_packing2.py (exact clipping areas)",
        "problem": cert.get("problem"),
        "n": cert["n"],
        "container": kind,
        "size": size,
        "size_approx": {key: k.approx(ev(v)) for key, v in size.items()},
        "squares": len(cert["squares"]),
        "pairs_checked": len(sqs) * (len(sqs) - 1) // 2,
        "result": "VALID" if not errs else "INVALID",
        "errors": errs,
    }


def main(argv):
    files = [a for a in argv[1:] if not a.startswith("--")]
    if len(files) != 1:
        print(__doc__)
        return 2
    with open(files[0]) as fh:
        rep = run(json.load(fh))
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
