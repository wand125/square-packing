#!/usr/bin/env python3
"""Second checker for the stage-1 claim of three unit squares in the regular hexagon.

Claim (SPEC_stage1.md): for every admissible pose whose reduced representative
(u = tan(theta/2) in [0, 1/7]) lies in no excused box, the weight of the certificate points in
the closed unit square is >= 1.  The total weight is < 3.

Method (written from the specification only):
* Boxes in (centre x, centre y, u) are split recursively.
* A box contained in one closed excused box is excused.  A box that meets an excused box only
  partly is split, at a face of that excused box when one lies strictly inside.
* A box is empty if one container constraint (a square vertex beyond one hexagon side) is
  violated at every pose of the box.
* A box is covered if points of total weight >= 1 are captured at every pose of the box,
  admissible or not.  For u in [0, 1/7], cos t >= 0 and sin t >= 0, so each of the four capture
  inequalities is affine in the centre with coefficients of fixed sign.  Its worst case over the
  centre rectangle is therefore one fixed corner.  At that corner the inequality, times
  1 + u^2, is a quadratic in u, and its three Bernstein coefficients on the u-interval bound it
  from below.
* A small box that is not settled this way gets an exact local sweep (`local_sweep`): points
  captured on the whole box add a constant, points never captured in the box are dropped, and
  the angular line-arrangement sweep of check2 (`sweep.py`) is run on the remaining points,
  the four box sides and the container constraints that do not hold on the whole box.  This
  handles poses where the captured point switches inside the box.
* All accepted signs are exact in Q(sqrt3); floats only order candidate points.

Closure: an admissible pose that is not excused has a neighbourhood that avoids all (closed)
excused boxes.  Poses with centre in the interior of the admissible region, in the interior of a
box and at a non-critical angle are dense there.  Each of them lies in a covered box, or in an open
cell checked by a local sweep.  The captured weight of a closed square is upper semicontinuous in
the pose, so the bound >= 1 extends to the limit pose.  The admissible region has interior for
every angle (the hexagon's inradius L*sqrt3/2 exceeds sqrt2/2).
"""
import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

from gmpy2 import mpq

from q3 import Q3

HALF = mpq(1, 2)
S3 = Q3(0, 1)
U_MAX = mpq(1, 7)


def load(path):
    raw = Path(path).read_bytes()
    c = json.loads(raw)
    L = Q3.parse(c['L'])
    pts = [(Q3.parse(p['x']), Q3.parse(p['y']), mpq(p['w'])) for p in c['points']]
    exc = [tuple(mpq(v) for v in b) for b in c.get('excused', [])]
    if c.get('pairs') or c.get('features'):
        raise SystemExit('pairs/features are not supported')
    return c, L, pts, exc, hashlib.sha256(raw).hexdigest()


def hexagon_sides(L):
    """Inner half-planes a.q + b >= 0 of H, from its vertices (counter-clockwise)."""
    h = L * S3 * HALF
    V = [(L * HALF, Q3(0)), (L * mpq(3, 2), Q3(0)), (L * 2, h), (L * mpq(3, 2), L * S3),
         (L * HALF, L * S3), (Q3(0), h)]
    sides = []
    for i in range(6):
        (x0, y0), (x1, y1) = V[i], V[(i + 1) % 6]
        a = (-(y1 - y0), x1 - x0)                  # inward normal for a ccw polygon
        b = -(a[0] * x0 + a[1] * y0)
        sides.append((a, b))
    for (a, b) in sides:                           # sanity: the centre is strictly inside
        G = (L, h)
        assert (a[0] * G[0] + a[1] * G[1] + b).sign() > 0
    return V, sides


def d6_invariant(L, pts):
    G = (L, L * S3 * HALF)
    c, s = Q3(HALF), Q3(0, HALF)                   # rotation by pi/3
    bag = {}
    for x, y, w in pts:
        bag[(x, y)] = bag.get((x, y), 0) + w
    def rot(p):
        dx, dy = p[0] - G[0], p[1] - G[1]
        return (G[0] + c * dx - s * dy, G[1] + s * dx + c * dy)
    def ref(p):
        return (L * 2 - p[0], p[1])
    for f in (rot, ref):
        img = {}
        for p, w in bag.items():
            q = f(p)
            img[q] = img.get(q, 0) + w
        if img != bag:
            return False
    return True


def quad_min_ok(a, b, c, u0, u1, strict=False):
    """a + b u + c u^2 >= 0 (or > 0) on [u0, u1], via its degree-2 Bernstein coefficients."""
    B0 = a + b * u0 + c * u0 * u0
    B1 = a + b * ((u0 + u1) * HALF) + c * (u0 * u1)
    B2 = a + b * u1 + c * u1 * u1
    if strict:
        return all(v.sign() > 0 for v in (B0, B1, B2))
    return all(v.sign() >= 0 for v in (B0, B1, B2))


def quad_max_neg(a, b, c, u0, u1):
    """a + b u + c u^2 < 0 on [u0, u1]."""
    return quad_min_ok(-a, -b, -c, u0, u1, strict=True)


# Times D = 1 + u^2:  D cos = 1 - u^2,  D sin = 2u.  Polynomials as (const, u, u^2).
DC = (1, 0, -1)
DS = (0, 2, 0)
DD = (1, 0, 1)


def pmul_scalar(p, k):
    return tuple(k * v for v in p)


def padd(*ps):
    return tuple(sum(v[i] for v in ps) for i in range(3))


class Hex:
    def __init__(self, L, pts, exc):
        self.L, self.pts, self.exc = L, pts, exc
        self.V, self.sides = hexagon_sides(L)
        self.fpts = [(float(x), float(y), float(w)) for x, y, w in pts]

    # ------------------------------------------------------------- empty boxes
    def empty(self, box):
        """Some side a.q + b >= 0 and some square vertex v = c + R(sx, sy) violate it on the
        whole box: D*(a.(c + R s) + b) < 0.  Affine in c: the max is at the corner chosen by
        the signs of a."""
        x0, x1, y0, y1, u0, u1 = box
        for (a, b) in self.sides:
            cx = x1 if a[0].sign() > 0 else x0
            cy = y1 if a[1].sign() > 0 else y0
            base = a[0] * cx + a[1] * cy + b
            for sx in (-HALF, HALF):
                for sy in (-HALF, HALF):
                    # D*(a.(R s)) = a0*(sx*DC - sy*DS) + a1*(sx*DS + sy*DC)
                    p = padd(pmul_scalar(DD, base),
                             pmul_scalar(DC, a[0] * sx + a[1] * sy),
                             pmul_scalar(DS, a[1] * sx - a[0] * sy))
                    if quad_max_neg(p[0], p[1], p[2], u0, u1):
                        return True
        return False

    # ------------------------------------------------------------- capture
    def captured(self, i, box):
        """p_i lies in Q(c, t) for every (c, u) in the box (admissible or not).
        Conditions |e1.(p - c)| <= 1/2, |e2.(p - c)| <= 1/2, e1 = (cos, sin), e2 = (-sin, cos).
        Times D: D/2 -+ (DC*(px - cx) + DS*(py - cy)) >= 0  and  D/2 -+ (-DS*(px - cx) + DC*(py - cy)) >= 0.
        With DC, DS >= 0 on [0, 1/7], each is monotone in cx and cy, so the worst corner is fixed."""
        x0, x1, y0, y1, u0, u1 = box
        px, py, _ = self.pts[i]
        half_D = pmul_scalar(DD, HALF)
        # e1.(p - c) <= 1/2 : worst at smallest c (cx0, cy0)
        tests = [
            padd(half_D, pmul_scalar(DC, -(px - x0)), pmul_scalar(DS, -(py - y0))),
            # -e1.(p - c) <= 1/2 : worst at largest c
            padd(half_D, pmul_scalar(DC, px - x1), pmul_scalar(DS, py - y1)),
            # e2.(p - c) = -DS (px - cx) + DC (py - cy) <= D/2 : worst at cx max, cy min
            padd(half_D, pmul_scalar(DS, px - x1), pmul_scalar(DC, -(py - y0))),
            # -e2.(p - c) <= D/2 : worst at cx min, cy max
            padd(half_D, pmul_scalar(DS, -(px - x0)), pmul_scalar(DC, py - y1)),
        ]
        return all(quad_min_ok(t[0], t[1], t[2], u0, u1) for t in tests)

    def float_margin(self, i, box):
        import math
        x0, x1, y0, y1, u0, u1 = (float(v) for v in box)
        px, py, _ = self.fpts[i]
        worst = 1e9
        for u in (u0, u1, (u0 + u1) / 2):
            t = 2 * math.atan(u)
            c, s = math.cos(t), math.sin(t)
            for cx in (x0, x1):
                for cy in (y0, y1):
                    a = c * (px - cx) + s * (py - cy)
                    b = -s * (px - cx) + c * (py - cy)
                    worst = min(worst, 0.5 - abs(a), 0.5 - abs(b))
        return worst

    def cover(self, box):
        cand = sorted(range(len(self.pts)), key=lambda i: -self.float_margin(i, box))
        w = mpq(0)
        used = 0
        for i in cand:
            if self.float_margin(i, box) < -0.05:
                break
            if self.captured(i, box):
                w += self.pts[i][2]
                used += 1
                if w >= 1:
                    return True, used
        return False, used

    # ------------------------------------------------------------- local sweep
    def never_captured(self, i, box):
        """Some capture inequality fails on the whole box (strictly), at its most favourable corner."""
        x0, x1, y0, y1, u0, u1 = box
        px, py, _ = self.pts[i]
        half_D = pmul_scalar(DD, HALF)
        tests = [
            padd(half_D, pmul_scalar(DC, -(px - x1)), pmul_scalar(DS, -(py - y1))),
            padd(half_D, pmul_scalar(DC, px - x0), pmul_scalar(DS, py - y0)),
            padd(half_D, pmul_scalar(DS, px - x0), pmul_scalar(DC, -(py - y1))),
            padd(half_D, pmul_scalar(DS, -(px - x1)), pmul_scalar(DC, py - y0)),
        ]
        return any(quad_max_neg(q[0], q[1], q[2], u0, u1) for q in tests)

    def inside_container(self, box):
        """Every pose of the box is admissible: each side/vertex constraint holds at the worst corner."""
        x0, x1, y0, y1, u0, u1 = box
        for (a, b) in self.sides:
            cx = x0 if a[0].sign() > 0 else x1
            cy = y0 if a[1].sign() > 0 else y1
            base = a[0] * cx + a[1] * cy + b
            for sx in (-HALF, HALF):
                for sy in (-HALF, HALF):
                    q = padd(pmul_scalar(DD, base),
                             pmul_scalar(DC, a[0] * sx + a[1] * sy),
                             pmul_scalar(DS, a[1] * sx - a[0] * sy))
                    if not quad_min_ok(q[0], q[1], q[2], u0, u1):
                        return False
        return True

    def line_holds_on_box(self, line, box):
        """A x + B y <= C (polynomials in u, with constant A and B up to the factor D) holds on the
        whole box: check C - A x - B y >= 0 at the worst corner, as a polynomial in u."""
        import sweep as S
        A, B, C, _ = line
        x0, x1, y0, y1, u0, u1 = box
        # A and B are D times a constant normal component: the sign of the constant decides the corner
        a = A[-1] if A else Q3(0)
        b = B[-1] if B else Q3(0)
        cx = x1 if a.sign() > 0 else x0
        cy = y1 if b.sign() > 0 else y0
        g = S.psub(S.psub(C, S.pscale(A, cx)), S.pscale(B, cy))
        g = list(g) + [Q3(0)] * (3 - len(g))
        if len(g) > 3:
            return False
        return quad_min_ok(g[0], g[1], g[2], u0, u1)

    def local_sweep(self, box):
        """Exact minimum of the captured weight over the box (all of whose poses are admissible),
        by the angular arrangement sweep of check2 restricted to the box: points captured on the
        whole box add a constant, points never captured are dropped (dropping can only lower the
        count), and the remaining points enter the arrangement with the four box sides.
        Returns (ok, details)."""
        import sweep as S
        from fractions import Fraction
        x0, x1, y0, y1, u0, u1 = box
        W0 = mpq(0)
        und = []
        for i in range(len(self.pts)):
            if self.captured(i, box):
                W0 += self.pts[i][2]
            elif not self.never_captured(i, box):
                und.append(i)
        if W0 >= 1:
            return True, 'constant'
        one = Q3(1)
        lines = [((Q3(-1),), (), (-x0,), ('box', 'x0')), ((one,), (), (x1,), ('box', 'x1')),
                 ((), (Q3(-1),), (-y0,), ('box', 'y0')), ((), (one,), (y1,), ('box', 'y1'))]
        allines, nadm24 = S.build_lines(self.L, [self.pts[i] for i in und], 'hex')
        # keep the container constraints that are not satisfied on the whole box
        for k in range(nadm24):
            if not self.line_holds_on_box(allines[k], box):
                lines.append(allines[k])
        nreg = len(lines)
        lines += allines[nadm24:]
        polys = S.event_polys(lines)
        lo = Fraction(int(u0.a.numerator), int(u0.a.denominator))
        hi = Fraction(int(u1.a.numerator), int(u1.a.denominator))
        ivs, _, _ = S.critical_intervals(polys, lo, hi)
        samples = S.sample_points(ivs, lo, hi)
        need = 1 - W0
        worst = None
        for u in samples:
            m, _, _ = S.check_at(lines, nreg, [self.pts[i][2] for i in und], u)
            if m is None:
                # no open cell of the box meets the admissible region at this u: nothing to check
                # (boundary poses are covered by the closure argument)
                continue
            worst = m if worst is None or m < worst else worst
            if m < need:
                return False, f'weight {W0 + m} at u = {u}'
        return True, dict(undecided=len(und), lines=len(lines), region_lines=nreg, samples=len(samples),
                          min_weight=None if worst is None else str(W0 + worst))

    # ------------------------------------------------------------- excused boxes
    def excuse_state(self, box):
        """('in', None) if box is inside one closed excused box, ('split', (dim, value)) to cut at a
        face of a partly overlapping one, ('free', None) if no excused box meets the interior."""
        x0, x1, y0, y1, u0, u1 = box
        lo = (x0, y0, u0)
        hi = (x1, y1, u1)
        for e in self.exc:
            elo = (e[0], e[2], e[4])
            ehi = (e[1], e[3], e[5])
            if all((Q3(elo[k]) - lo[k]).sign() <= 0 and (hi[k] - Q3(ehi[k])).sign() <= 0 for k in range(3)):
                return 'in', None
        for e in self.exc:
            elo = (e[0], e[2], e[4])
            ehi = (e[1], e[3], e[5])
            # interiors meet?
            if all((Q3(elo[k]) - hi[k]).sign() < 0 and (lo[k] - Q3(ehi[k])).sign() < 0 for k in range(3)):
                for k in range(3):
                    for v in (elo[k], ehi[k]):
                        if (lo[k] - Q3(v)).sign() < 0 and (Q3(v) - hi[k]).sign() < 0:
                            return 'split', (k, Q3(v))
        return 'free', None


_H = None


def _init(cert_path):
    global _H
    c, L, pts, exc, sha = load(cert_path)
    _H = Hex(L, pts, exc)


def _work(args):
    box, max_depth, uscale, limit_boxes, sweep_size = args
    tag = [round(float(v), 4) for v in box]
    return check_boxes(_H, [(box, 0)], max_depth, uscale, limit_boxes, sweep_size, trace=tag)


def run(cert_path, max_depth, uscale, limit_boxes=None, sweep_size=1 / 256, jobs=1, grid=4):
    c, L, pts, exc, sha = load(cert_path)
    total = sum(w for _, _, w in pts)
    h = Hex(L, pts, exc)
    inv = d6_invariant(L, pts)
    t0 = time.time()
    # the root box, cut into grid x grid x grid pieces (exact rational or Q(sqrt3) endpoints)
    X, Y, Uu = L * 2, L * S3, Q3(U_MAX)
    roots = []
    for i in range(grid):
        for j in range(grid):
            for k in range(grid):
                roots.append((X * mpq(i, grid), X * mpq(i + 1, grid), Y * mpq(j, grid), Y * mpq(j + 1, grid),
                              Uu * mpq(k, grid), Uu * mpq(k + 1, grid)))
    if jobs > 1:
        from multiprocessing import Pool
        parts = []
        with Pool(jobs, initializer=_init, initargs=(cert_path,)) as pool:
            for k, part in enumerate(pool.imap_unordered(
                    _work, [(r, max_depth, uscale, limit_boxes, sweep_size) for r in roots], chunksize=1)):
                parts.append(part)
                st = part[0]
                print(json.dumps(dict(done=k + 1, of=len(roots), seconds=round(time.time() - t0),
                                      boxes=st['boxes'], swept=st['swept'], failed=st['failed'])),
                      file=sys.stderr, flush=True)
    else:
        parts = [check_boxes(h, [(r, 0)], max_depth, uscale, limit_boxes, sweep_size) for r in roots]
    stats = dict(boxes=0, excused=0, empty=0, cover=0, swept=0, failed=0, max_depth=0)
    failed = []
    truncated = False
    for st, fl, tr in parts:
        for k in stats:
            stats[k] = max(stats[k], st[k]) if k == 'max_depth' else stats[k] + st[k]
        failed += fl
        truncated = truncated or tr
    return dict(certificate=Path(cert_path).name, sha256=sha, L=str(L), points=len(pts),
                excused_boxes=len(exc), total_weight=str(total), total_below_3=total < 3,
                d6_invariant=inv, root_pieces=len(roots), **stats, failed_boxes=failed[:50],
                seconds=round(time.time() - t0, 1),
                status='verified' if stats['failed'] == 0 and inv and total < 3 and not truncated
                else 'failed')


def check_boxes(h, stack, max_depth, uscale, limit_boxes, sweep_size, trace=None):
    stats = dict(boxes=0, excused=0, empty=0, cover=0, swept=0, failed=0, max_depth=0)
    failed = []
    while stack:
        box, depth = stack.pop()
        stats['boxes'] += 1
        stats['max_depth'] = max(stats['max_depth'], depth)
        if trace and stats['boxes'] % 200 == 0:
            print(json.dumps(dict(trace=trace, boxes=stats['boxes'], depth=depth, stack=len(stack),
                                  swept=stats['swept'], failed=stats['failed'],
                                  box=[round(float(v), 6) for v in box])), file=sys.stderr, flush=True)
        if limit_boxes and stats['boxes'] > limit_boxes:
            break
        # A box is first tried as a whole (empty or covered), whatever its relation to the excused
        # boxes: that proves more than needed.  Only if that fails is it excused or split.
        if h.empty(box):
            stats['empty'] += 1
            continue
        ok, _ = h.cover(box)
        if ok:
            stats['cover'] += 1
            continue
        state, cut = h.excuse_state(box)
        if state == 'in':
            stats['excused'] += 1
            continue
        x0, x1, y0, y1, u0, u1 = box
        if max(float(x1 - x0), float(y1 - y0)) <= sweep_size and float(u1 - u0) <= sweep_size / 4:
            ok, info = h.local_sweep(box)
            if ok:
                stats['swept'] += 1
                continue
        if depth >= max_depth:
            stats['failed'] += 1
            failed.append([str(v) for v in box])
            continue
        x0, x1, y0, y1, u0, u1 = box
        central = False
        if cut is not None:
            k, v = cut
            lo_k, hi_k = box[2 * k], box[2 * k + 1]
            frac = float(v - lo_k) / float(hi_k - lo_k)
            central = 0.25 <= frac <= 0.75
        if not central:
            wx, wy, wu = float(x1 - x0), float(y1 - y0), float(u1 - u0) * uscale
            if wu >= max(wx, wy):
                k, v = 2, (u0 + u1) * HALF
            elif wx >= wy:
                k, v = 0, (x0 + x1) * HALF
            else:
                k, v = 1, (y0 + y1) * HALF
        lo = list(box); hi = list(box)
        lo[2 * k + 1] = v
        hi[2 * k] = v
        stack.append((tuple(lo), depth + 1))
        stack.append((tuple(hi), depth + 1))
    truncated = bool(limit_boxes and stats['boxes'] > limit_boxes)
    return stats, failed[:50], truncated


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('cert')
    ap.add_argument('--max-depth', type=int, default=40)
    ap.add_argument('--uscale', type=float, default=16.0)
    ap.add_argument('--limit-boxes', type=int)
    ap.add_argument('--out')
    ap.add_argument('--jobs', type=int, default=1)
    ap.add_argument('--grid', type=int, default=4, help='the root box is cut into grid^3 pieces')
    ap.add_argument('--sweep-size', type=float, default=1 / 256,
                    help='boxes at most this wide (u: a quarter of it) get the exact local sweep')
    a = ap.parse_args()
    s = run(a.cert, a.max_depth, a.uscale, a.limit_boxes, a.sweep_size, a.jobs, a.grid)
    text = json.dumps(s, indent=2)
    print(text)
    if a.out:
        Path(a.out).write_text(text + '\n')
    return 0 if s['status'] == 'verified' else 1


if __name__ == '__main__':
    sys.exit(main())
