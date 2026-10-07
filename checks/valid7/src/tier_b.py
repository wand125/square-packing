"""Tier B: exact certificate that min over a centre box of mu(Q(c, t)) >= 1 for every u in an interval (a, b)
not containing 0, by symbolic execution of src/solver.py.

Lemma B1.  Run the solver with u an RF at a sample s.  If no guard polynomial has a root in an open interval
J ∋ s, every branch is taken identically for all u in J, so for u in J the solver's candidate list is the list of
rational functions R_i(u) it returned, and min_c mu = min_i R_i(u) (Lemmas F1, F2 at each u).  If
(N_i - D_i) D_i >= 0 on the closure of J for every i (R_i = N_i/D_i), then min_c mu >= 1 on J.
Lemma B2.  For u != 0 (mod pi/2), m(u) = min over admissible centres in the box of mu is continuous in u
(mu is continuous in the pose there, and the admissible centre set varies continuously).  So if the open
components J_1, J_2, ... cover (a, b) up to finitely many points, m >= 1 on all of (a, b), and on [a, b] when
0 is not in [a, b].
The components' ends are real roots of guard polynomials, kept as exact isolating intervals.
"""
from fractions import Fraction
import time
import rf
from rf import P, Q, Resample
import solver


class Alg:
    """The unique root of the squarefree polynomial p in the open interval (l, r), with p(l) != 0 != p(r)
    (normalised at construction with exact Sturm counts); or a rational (p = None, l = r)."""
    __slots__ = ('p', 'l', 'r', 'seq')

    def __init__(self, p, l, r):
        self.p, self.l, self.r, self.seq = p, Q(l), Q(r), None
        if p is None:
            return
        self.seq = rf.sturm(p)
        if p(self.r) == 0:                 # convention of isolate(): (l, r] holds exactly one root
            if rf.count_roots(self.seq, self.l, self.r) == 1:
                self.p, self.l = None, self.r
                return
        assert rf.count_roots(self.seq, self.l, self.r) - (1 if p(self.r) == 0 else 0) == 1, 'Alg: not isolating'
        # move the ends off roots of p, keeping exactly one root strictly inside
        while p(self.l) == 0 or p(self.r) == 0:
            m = (self.l + self.r) / 2
            if p(m) == 0:
                if self._count(self.l, m) == 0 and self._count(m, self.r) == 0:
                    self.p, self.l, self.r = None, m, m      # m is the root
                    return
            if self._count(self.l, m) == 1:
                self.r = m
            else:
                self.l = m

    def _count(self, a, b):
        """Roots of p in the open interval (a, b)."""
        return rf.count_roots(self.seq, a, b) - (1 if self.p(b) == 0 else 0)

    @staticmethod
    def rat(x):
        return Alg(None, x, x)

    def refine(self):
        if self.p is None:
            return
        m = (self.l + self.r) / 2
        v = self.p(m)
        if v == 0:
            self.p, self.l, self.r = None, m, m
        elif (self.p(self.l) > 0) != (v > 0):      # p(l) != 0 by the invariant: a sign change locates the root
            self.r = m
        else:
            self.l = m

    def width(self):
        return self.r - self.l


def alg_cmp(A, B):
    """-1, 0, 1 exactly."""
    for _ in range(400):
        if A.r < B.l or (A.p is None and B.p is not None and A.r <= B.l) or (A.p is None and B.p is None and A.r < B.l):
            return -1
        if B.r < A.l or (B.p is None and A.p is not None and B.r <= A.l) or (A.p is None and B.p is None and B.r < A.l):
            return 1
        if A.p is None and B.p is None:
            return 0 if A.l == B.l else (-1 if A.l < B.l else 1)
        if A.p is not None and B.p is not None:
            g = A.p.gcd(B.p)
            if g.degree() > 0:
                lo, hi = max(A.l, B.l), min(A.r, B.r)
                if lo < hi and rf.count_roots(rf.sturm(rf.squarefree(g)), lo, hi) - (1 if g(hi) == 0 else 0) > 0:
                    return 0
        if A.p is not None and B.p is None and A.l < B.l < A.r and A.p(B.l) == 0:
            return 0
        if B.p is not None and A.p is None and B.l < A.l < B.r and B.p(A.l) == 0:
            return 0
        if A.width() >= B.width():
            A.refine()
        else:
            B.refine()
    raise RuntimeError('alg_cmp did not separate')


def strip0(p):
    k = 0
    while p[k] == 0:
        k += 1
    return P([p[i] for i in range(k, p.degree() + 1)]) if k else p


def root_free(p, lo, hi):
    """Sufficient test: p has no real root in [lo, hi] (Taylor at lo, coefficient bound)."""
    t = p(P([lo, 1]))
    w = hi - lo
    s = Q(0); wp = Q(1)
    for i in range(1, t.degree() + 1):
        wp *= w
        s += abs(t[i]) * wp
    return abs(t[0]) > s


def guard_roots(guards, lo, hi):
    """All real roots of the guards in the open interval (lo, hi), as Alg, sorted (distinct)."""
    out = []
    for g in guards:
        if lo == 0:
            g = strip0(g)
        if g.degree() <= 0 or root_free(g, lo, hi):
            continue
        sq = rf.squarefree(g)
        for l, r in rf.roots_open(sq, lo, hi):
            a = Alg(sq, l, r)
            if sq(r) == 0:          # cannot happen for roots in the open interval except r == hi; guard anyway
                a = Alg.rat(r)
            out.append(a)
    return out


def nonneg(p, lo, hi):
    """p >= 0 on [lo, hi] exactly; fast path first."""
    if p == 0:
        return True
    if lo == 0:
        q = strip0(p)
        if q[0] > 0 and root_free(q, lo, hi):
            return True
    elif p(lo) > 0 and root_free(p, lo, hi):
        return True
    return rf.nonneg_on(p, lo, hi)


def chain(run, a, b, max_runs=10000):
    """Lemma B1 + B2 for a generic symbolic computation: run(u) (u an RF) returns a list of (value, info) whose
    values must be >= 1.  Components of (a, b) free of guard roots are chained from left to right; on each, every
    value is checked exactly on the open component (algebraic ends)."""
    from tier_b2 import nonneg_open
    a, b = Q(a), Q(b)
    assert a >= 0 or b <= 0
    frontier = Alg.rat(a)
    runs = []
    while not (frontier.p is None and frontier.l == b):
        cap = b
        while True:
            while frontier.p is not None and frontier.r >= cap:
                frontier.refine()
            lo = frontier.r
            s = lo + (cap - lo) / 2
            for _ in range(60):
                try:
                    ctx = rf.Ctx(Fraction(int(s.p), int(s.q)))
                    vals = run(ctx.var())
                    break
                except Resample:
                    s = lo + (s - lo) * Q(2, 3)
            else:
                return {'ok': False, 'why': 'resample', 'at': str(s), 'runs': runs}
            guards = list(ctx.guards.values())
            roots = guard_roots(guards, a, b)
            S = Alg.rat(s)
            L, R = Alg.rat(a), Alg.rat(b)
            for r in roots:
                c = alg_cmp(r, S)
                if c < 0 and alg_cmp(r, L) > 0:
                    L = r
                elif c > 0 and alg_cmp(r, R) < 0:
                    R = r
            if alg_cmp(L, frontier) <= 0:
                break
            while L.p is not None and L.l <= frontier.r:
                L.refine()
                if frontier.p is not None:
                    frontier.refine()
            cap = L.l
            if len(runs) + 1 >= max_runs:
                return {'ok': False, 'why': 'max_runs', 'runs': runs}
        bad = None
        for v, info in vals:
            if not isinstance(v, rf.RF):
                v = rf.RF(P([Q(v)]), P([1]), ctx)
            if not nonneg_open((v.n - v.d) * v.d, L, R):
                bad = (v, info); break
        runs.append({'s': str(s), 'L': (str(L.l), str(L.r)), 'R': (str(R.l), str(R.r)),
                     'guards': len(guards), 'cands': len(vals), 'ok': bad is None})
        if bad is not None:
            return {'ok': False, 'why': 'value', 'at': str(s), 'cand': str(bad[0]), 'info': str(bad[1]),
                    'runs': runs}
        frontier = R
        if len(runs) >= max_runs:
            return {'ok': False, 'why': 'max_runs', 'runs': runs}
    return {'ok': True, 'runs': runs}


def certify(loc, side, box, a, b, log=None, max_runs=10000):
    """B1: the whole box solver (vertices and edge criticals) traced symbolically."""
    x0, x1, y0, y1 = box

    def run(u):
        res = solver.box_min(loc, side, u, x0, x1, y0, y1, keep=True)
        return [] if res is None else [(v, kind) for v, pnt, kind in res[1]]
    return chain(run, a, b, max_runs)


if __name__ == '__main__':
    import sys
    from tier_a import Cover
    cov = Cover(sys.argv[1])
    box = tuple(Fraction(v) for v in sys.argv[2:6])
    a, b = Fraction(sys.argv[6]), Fraction(sys.argv[7])
    loc = solver.Local(cov, *box)
    t = time.time()
    r = certify(loc, cov.s, box, Q(a.numerator, a.denominator), Q(b.numerator, b.denominator))
    print('ok' if r['ok'] else 'FAIL ' + r['why'], 'runs', len(r.get('runs', [])), f'{time.time() - t:.1f}s')
    for x in r.get('runs', [])[:50]:
        print('  ', x)
    if not r['ok']:
        print({k: v for k, v in r.items() if k != 'runs'})
