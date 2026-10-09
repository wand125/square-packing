#!/usr/bin/env python3
"""Exact checker: a weighted point set is unavoidable for closed unit squares in T_L (right isosceles).

Claim proved when the status is "verified":

    for every closed unit square Q with Q contained in T_L (any position, any angle):
        sum of w_i over the points p_i in Q  (+ sum of rho * |Q cap pq| over segments)  >=  1

T_L is the right isosceles triangle with vertices (0,0), (L,0), (0,L) (legs of length L).
Adapted from ../triangle/checker (equilateral container): only the container, the
number field (Q(sqrt2) instead of Q(sqrt3)) and the symmetry (D1: the reflection
(x, y) -> (y, x)) differ.  See README.md for the lemmas.  Every accepted inequality is decided with exact Q(sqrt2) arithmetic
(module q2) and exact Bernstein coefficients (module poly).  Floats are used only
to decide what to try (candidate points, candidate separating constraints, where
to split); a wrong float guess can only cost time, never soundness.

Usage:
    python3 check.py cert.json [--n N] [--root R] [--max-depth D] [--jobs J]
                              [--u-breaks "u1,u2,..."] [--u-scale 4]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import sys
import time
from fractions import Fraction

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from q2 import Q2, ZERO, ONE, SQRT2  # noqa: E402
from poly import (  # noqa: E402
    DEG, padd, psub, pscale, pmul, ptrim, pfloat, feval, to_bern, bsub, badd, bern_nonneg, peval,
)

HALF = Fraction(1, 2)
POLY_DEPTH = 12          # halvings allowed inside one polynomial test
FLOAT_TOL = 1e-9         # float slack used only for guidance
N_SAMPLES = 9            # float sample angles per u-bin (guidance only)
MAX_LISTED_UNCERTIFIED = 5000


# =========================================================================== certificate
class CertError(ValueError):
    pass


def load_certificate(path_or_obj):
    """Return (raw, L, symmetry, points [(x, y, w)], pairs, features, segments).

    raw is the file bytes or None; segments are [((px, py), (qx, qy), rho)] with
    |q - p| = 1 exactly and rho > 0 (segments of density 0 are dropped).
    """
    raw = None
    if isinstance(path_or_obj, (str, os.PathLike)):
        with open(path_or_obj, "rb") as f:
            raw = f.read()
        data = json.loads(raw.decode("utf-8"))
    else:
        data = path_or_obj
    L = Q2.parse(str(data["L"]))
    if L.sign() <= 0:
        raise CertError("L must be positive")
    sym = data.get("symmetry", "none")
    if sym not in ("none", "D1"):
        raise CertError(f"unknown symmetry {sym!r}")
    merged: dict = {}
    for pt in data.get("points", []):
        x = Q2.parse(str(pt["x"]))
        y = Q2.parse(str(pt["y"]))
        w = Fraction(str(pt["w"]))
        if w < 0:
            raise CertError("weights must be >= 0")
        merged[(x, y)] = merged.get((x, y), Fraction(0)) + w
    points = [(x, y, w) for (x, y), w in merged.items() if w > 0]
    raw_pts = [(Q2.parse(str(pt["x"])), Q2.parse(str(pt["y"]))) for pt in data.get("points", [])]
    pairs = []
    for i, j in data.get("pairs", []):
        p, q = raw_pts[i], raw_pts[j]
        dx, dy = q[0] - p[0], q[1] - p[1]
        if not (dx * dx + dy * dy == Q2(1)):
            raise CertError(f"pair ({i}, {j}) is not at distance exactly 1")
        if merged.get(p, 0) <= 0 or merged.get(q, 0) <= 0:
            raise CertError(f"pair ({i}, {j}) uses a point of weight 0")
        pairs.append((p, q))
    features = []
    for ft in data.get("features", []):
        sites = [(Q2.parse(str(q["x"])), Q2.parse(str(q["y"]))) for q in ft["sites"]]
        k = int(ft["k"])
        w = Fraction(str(ft["w"]))
        if len(set(sites)) != len(sites) or not (1 <= k <= len(sites)) or w < 0:
            raise CertError("bad feature (sites must be distinct, 1 <= k <= m, w >= 0)")
        features.append((tuple(sites), k, w))
    # sites that carry no point weight still need capture proofs: add them with weight 0
    have = {(x, y) for x, y, _ in points}
    for sites, _, _ in features:
        for q in sites:
            if q not in have:
                points.append((q[0], q[1], Fraction(0)))
                have.add(q)
    segments = []
    for sg in data.get("segments", []):
        p = (Q2.parse(str(sg["p"]["x"])), Q2.parse(str(sg["p"]["y"])))
        q = (Q2.parse(str(sg["q"]["x"])), Q2.parse(str(sg["q"]["y"])))
        rho = Fraction(str(sg["rho"]))
        if rho < 0:
            raise CertError("segment density rho must be >= 0")
        dx, dy = q[0] - p[0], q[1] - p[1]
        if not (dx * dx + dy * dy == Q2(1)):
            raise CertError(f"segment {p}-{q} does not have length exactly 1")
        if rho > 0:
            segments.append((p, q, rho))
    return raw, L, sym, points, pairs, features, segments


def d3_images(L: Q2, x: Q2, y: Q2):
    """The generator of the symmetry group of T_L (the reflection (x, y) -> (y, x)) applied to (x, y).

    The name is kept from the equilateral checker; the group here is D1 (order 2).
    """
    return [(y, x)]


def check_d3_features(L: Q2, features) -> bool:
    """The multiset of features (site set, k, w) is invariant under the reflection."""
    def canon(ft):
        sites, k, w = ft
        return (frozenset(sites), k, w)
    base = sorted(map(repr, map(canon, features)))
    imgs = []
    for sites, k, w in features:
        imgs.append(canon((tuple(d3_images(L, x, y)[0] for x, y in sites), k, w)))
    return sorted(map(repr, imgs)) == base


def check_d3_segments(L: Q2, segments) -> bool:
    """The multiset of segments (unordered endpoint pair, rho) is invariant under the reflection."""
    def canon(p, q, rho):
        return repr((sorted([repr(p), repr(q)]), rho))
    base = sorted(canon(p, q, rho) for p, q, rho in segments)
    imgs = sorted(canon(d3_images(L, *p)[0], d3_images(L, *q)[0], rho) for p, q, rho in segments)
    return imgs == base


def check_d3_invariant(L: Q2, points) -> bool:
    """Exact check that the weighted multiset is invariant under the reflection."""
    wmap = {(x, y): w for x, y, w in points}
    for x, y, w in points:
        for img in d3_images(L, x, y):
            if wmap.get(img) != w:
                return False
    return True


# With symmetry D1 the u-range is [0, U_D1], U_D1 = tan(pi/8) = sqrt2 - 1 exactly (theta in [0, pi/4]).
# Reason: the reflection (x, y) -> (y, x) maps a square of angle theta to one of angle pi/2 - theta,
# which is the angle -theta modulo the period pi/2 of the square.
U_D1 = Q2(-1, 1)


# =========================================================================== geometry
class Line:
    """Half-plane n . c <= O(u) / D(u), D = 1 + u^2, n constant (Q2)."""

    __slots__ = ("nx", "ny", "O", "fnx", "fny", "fO", "tag")

    def __init__(self, nx, ny, O, tag):
        self.nx, self.ny, self.O, self.tag = nx, ny, O, tag
        self.fnx, self.fny, self.fO = float(nx), float(ny), pfloat(O)


class Context:
    """Everything that depends only on the certificate (shared by all boxes)."""

    def __init__(self, L, points, opts):
        self.L = L
        self.points = sorted(points, key=lambda t: -t[2])
        self.fpoints = [(float(x), float(y)) for x, y, _ in self.points]
        self.opts = opts
        q = lambda *c: [Q2(v) if not isinstance(v, Q2) else v for v in c]  # noqa: E731
        self.D = q(1, 0, 1)
        self.E1x, self.E1y = q(1, 0, -1), q(0, 2)
        self.E2x, self.E2y = q(0, -2), q(1, 0, -1)
        self.D2half = pscale(pmul(self.D, self.D), HALF)
        self.KE1x, self.KE1y = pmul(self.D, self.E1x), pmul(self.D, self.E1y)
        self.KE2x, self.KE2y = pmul(self.D, self.E2x), pmul(self.D, self.E2y)
        # admissibility: n_k . c <= b_k - n_k . (R_theta sigma), times D
        # sides y >= 0, x >= 0, x + y <= L (normals need not be unit vectors)
        normals = [
            (ZERO, Q2(-1), ZERO),
            (Q2(-1), ZERO, ZERO),
            (ONE, ONE, L),
        ]
        self.adm = []
        for k, (nx, ny, b) in enumerate(normals):
            for sx in (HALF, -HALF):
                for sy in (HALF, -HALF):
                    # D * R_theta sigma = sx * E1 + sy * E2
                    RDx = padd(pscale(self.E1x, sx), pscale(self.E2x, sy))
                    RDy = padd(pscale(self.E1y, sx), pscale(self.E2y, sy))
                    O = psub(pscale(self.D, b), padd(pscale(RDx, nx), pscale(RDy, ny)))
                    self.adm.append(Line(nx, ny, ptrim(O), ("adm", k, sx, sy)))
        # point terms T1 = p . (D E1), T2 = p . (D E2)
        self.pterms = []
        for x, y, _ in self.points:
            T1 = padd(pscale(self.KE1x, x), pscale(self.KE1y, y))
            T2 = padd(pscale(self.KE2x, x), pscale(self.KE2y, y))
            self.pterms.append((T1, T2))
        self.pair_cache: dict = {}
        self.iv_cache: dict = {}
        # chord pairs (Lemma P in README): points p, q with |q - p| = 1
        index = {(x, y): i for i, (x, y, _) in enumerate(self.points)}
        self.chord_pairs = []
        for xs, ys, xs2, ys2 in opts.get("pairs", []):
            p = (Q2.parse(xs), Q2.parse(ys))
            q = (Q2.parse(xs2), Q2.parse(ys2))
            dx, dy = q[0] - p[0], q[1] - p[1]
            M = (padd(pscale(self.E1x, dx), pscale(self.E1y, dy)),      # d . E1
                 padd(pscale(self.E2x, dx), pscale(self.E2y, dy)))      # d . E2
            self.chord_pairs.append((index[p], index[q], M))
        self.features = []
        for sites, k, w in opts.get("features", []):
            idx = [index[(Q2.parse(x), Q2.parse(y))] for x, y in sites]
            self.features.append((idx, k, Fraction(w)))
        # segment masses (README item 6b): unit segments p + t d, t in [0, 1], density rho
        self.segments = []
        self.seg_sign_cache: dict = {}
        for (pxs, pys), (qxs, qys), rho in opts.get("segments", []):
            p = (Q2.parse(pxs), Q2.parse(pys))
            q = (Q2.parse(qxs), Q2.parse(qys))
            self.segments.append(Segment(self, p, q, Fraction(rho)))

    # ------------------------------------------------------------------ intervals
    def interval(self, ua: Q2, ub: Q2):
        key = (ua.a, ua.b, ub.a, ub.b)
        iv = self.iv_cache.get(key)
        if iv is not None:
            return iv
        if len(self.iv_cache) > 4000:
            self.iv_cache.clear()
        fa, fb = float(ua), float(ub)
        samples = [fa + (fb - fa) * i / (N_SAMPLES - 1) for i in range(N_SAMPLES)]
        iv = {
            "ua": ua, "ub": ub, "samples": samples,
            "fD": [1 + s * s for s in samples],
            "fE1": [(1 - s * s, 2 * s) for s in samples],
            "fE2": [(-2 * s, 1 - s * s) for s in samples],
            "B_D2half": to_bern(self.D2half, ua, ub),
            "pbern": {}, "pairbern": {},
        }
        iv["adm_kept"] = self._reduce_parallel(self.adm, ua, ub, samples)
        self.iv_cache[key] = iv
        return iv

    def _reduce_parallel(self, lines, ua, ub, samples):
        """Drop lines dominated by a parallel line with the same normal.

        Line j is dropped only after an exact proof that O_j - O_i >= 0 on [ua, ub]
        for a kept line i with identical normal: then {n.c <= O_i/D} is contained in
        {n.c <= O_j/D} for every angle of the bin, so j does not change P_theta.
        """
        groups: dict = {}
        for idx, ln in enumerate(lines):
            groups.setdefault((ln.nx, ln.ny), []).append(idx)
        kept = []
        mid = samples[len(samples) // 2]
        for idxs in groups.values():
            idxs = sorted(idxs, key=lambda i: feval(lines[i].fO, mid))
            keep = idxs[0]
            kept.append(keep)
            for j in idxs[1:]:
                diff = psub(lines[j].O, lines[keep].O)
                if not self.prove_nonneg(diff, ua, ub):
                    kept.append(j)
        return sorted(kept)

    # ------------------------------------------------------------------ exact tests
    @staticmethod
    def prove_nonneg(p, ua, ub, strict=False):
        return bern_nonneg(to_bern(p, ua, ub), POLY_DEPTH, strict)

    def point_bern(self, iv, pi):
        pb = iv["pbern"].get(pi)
        if pb is None:
            T1, T2 = self.pterms[pi]
            pb = (to_bern(T1, iv["ua"], iv["ub"]), to_bern(T2, iv["ua"], iv["ub"]))
            iv["pbern"][pi] = pb
        return pb


class Segment:
    """A unit segment p + t d (t in [0, 1], |d| = 1) with density rho.

    T = (p . (D E1), p . (D E2))  (degree <= 4), M = (d . E1, d . E2)  (degree <= 2),
    DM = (D M1, D M2) (degree <= 4).  With N_k = W_k - T_k for a vertex V = (X, Y)/D, the slab of
    square axis k is  -D^2/2 <= N_k - t D M_k <= D^2/2  (everything multiplied by D^2 > 0).
    """

    __slots__ = ("p", "q", "rho", "T", "M", "DM", "fp", "fd")

    def __init__(self, ctx, p, q, rho):
        self.p, self.q, self.rho = p, q, rho
        dx, dy = q[0] - p[0], q[1] - p[1]
        self.T = (padd(pscale(ctx.KE1x, p[0]), pscale(ctx.KE1y, p[1])),
                  padd(pscale(ctx.KE2x, p[0]), pscale(ctx.KE2y, p[1])))
        self.M = (padd(pscale(ctx.E1x, dx), pscale(ctx.E1y, dy)),
                  padd(pscale(ctx.E2x, dx), pscale(ctx.E2y, dy)))
        self.DM = (pmul(ctx.D, self.M[0]), pmul(ctx.D, self.M[1]))
        self.fp = (float(p[0]), float(p[1]))
        self.fd = (float(dx), float(dy))


class Pair:
    """Intersection V(u) = (X(u), Y(u)) / D(u) of two non-parallel lines."""

    __slots__ = ("X", "Y", "W1", "W2", "fX", "fY")

    def __init__(self, ctx: Context, li: Line, lj: Line):
        det = li.nx * lj.ny - li.ny * lj.nx
        inv = det.inverse()
        self.X = pscale(psub(pscale(li.O, lj.ny), pscale(lj.O, li.ny)), inv)
        self.Y = pscale(psub(pscale(lj.O, li.nx), pscale(li.O, lj.nx)), inv)
        self.W1 = padd(pmul(self.X, ctx.E1x), pmul(self.Y, ctx.E1y))
        self.W2 = padd(pmul(self.X, ctx.E2x), pmul(self.Y, ctx.E2y))
        self.fX, self.fY = pfloat(self.X), pfloat(self.Y)


def parallel(li: Line, lj: Line) -> bool:
    return (li.nx * lj.ny - li.ny * lj.nx).is_zero()


# =========================================================================== one box
def box_vertices(ctx: Context, x0, x1, y0, y1, ua: Q2, ub: Q2):
    """Return (iv, feasible) where feasible is the list of (key, Pair) vertex candidates of
    P_theta that are not proved infeasible on the box, or (iv, None) if the box is proved EMPTY.
    Every extreme point of P_theta, for every u in [ua, ub], is V(u) for some Pair in the list."""
    iv = ctx.interval(ua, ub)
    samples, fD = iv["samples"], iv["fD"]
    corners = [(Q2(x0), Q2(y0)), (Q2(x0), Q2(y1)), (Q2(x1), Q2(y0)), (Q2(x1), Q2(y1))]
    fcorners = [(float(cx), float(cy)) for cx, cy in corners]
    D = ctx.D

    # ---- admissibility lines: single-line emptiness and redundancy
    lines = []
    for idx in iv["adm_kept"]:
        ln = ctx.adm[idx]
        fvals = [ln.fnx * cx + ln.fny * cy for cx, cy in fcorners]
        fO = [feval(ln.fO, s) / d for s, d in zip(samples, fD)]
        if min(fvals) > max(fO) + FLOAT_TOL:
            # candidate: every corner strictly violates for all u  =>  box empty
            mn = min(ln.nx * cx + ln.ny * cy for cx, cy in corners)
            if ctx.prove_nonneg(psub(pscale(D, mn), ln.O), ua, ub, strict=True):
                return iv, None
        if max(fvals) < min(fO) - FLOAT_TOL:
            # candidate: rectangle inside the half-plane for all u  =>  redundant
            mx = max(ln.nx * cx + ln.ny * cy for cx, cy in corners)
            if ctx.prove_nonneg(psub(ln.O, pscale(D, mx)), ua, ub):
                continue
        lines.append((idx, ln))

    # ---- rectangle lines (offset times D, so all lines share the denominator D)
    rect = [
        Line(ONE, ZERO, pscale(D, Q2(x1)), ("rect", "x1")),
        Line(-ONE, ZERO, pscale(D, Q2(-x0)), ("rect", "x0")),
        Line(ZERO, ONE, pscale(D, Q2(y1)), ("rect", "y1")),
        Line(ZERO, -ONE, pscale(D, Q2(-y0)), ("rect", "y0")),
    ]
    mid = samples[len(samples) // 2]
    drop_adm = set()
    rect_kept = []
    for r in rect:
        dropped = False
        for idx, ln in lines:
            if idx in drop_adm or not (ln.nx == r.nx and ln.ny == r.ny):
                continue
            if feval(ln.fO, mid) <= feval(r.fO, mid):
                if ctx.prove_nonneg(psub(r.O, ln.O), ua, ub):
                    dropped = True        # adm line tighter: rect side redundant
                    break
            elif ctx.prove_nonneg(psub(ln.O, r.O), ua, ub):
                drop_adm.add(idx)         # rect side tighter: adm line redundant
        if not dropped:
            rect_kept.append((None, r))
    all_lines = [(i, ln) for i, ln in lines if i not in drop_adm] + rect_kept

    # ---- vertex candidates: non-parallel pairs, minus provably infeasible ones
    feasible = []
    n = len(all_lines)
    for a in range(n):
        ia, la = all_lines[a]
        for b in range(a + 1, n):
            ib, lb = all_lines[b]
            if parallel(la, lb):
                continue
            if ia is not None and ib is not None:
                key = (ia, ib)
                pr = ctx.pair_cache.get(key)
                if pr is None:
                    pr = ctx.pair_cache[key] = Pair(ctx, la, lb)
            else:
                pr = Pair(ctx, la, lb)
            if not pair_infeasible(ctx, iv, pr, all_lines, a, b):
                pkey = (ia, ib) if ia is not None and ib is not None else None
                feasible.append((pkey, pr))
    if not feasible:
        return iv, None
    return iv, feasible


def float_vertices(iv, feasible):
    """Float guidance: vertex positions at the sample angles, and the unit axes there."""
    samples, fD = iv["samples"], iv["fD"]
    fverts = []
    for _, pr in feasible:
        fverts.append([(feval(pr.fX, s) / d, feval(pr.fY, s) / d) for s, d in zip(samples, fD)])
    fE = [((e1x / d, e1y / d), (e2x / d, e2y / d))
          for (e1x, e1y), (e2x, e2y), d in zip(iv["fE1"], iv["fE2"], fD)]
    return fverts, fE


def certify_box(ctx: Context, x0, x1, y0, y1, ua: Q2, ub: Q2):
    """Return "EMPTY", "COVER" or None (not certified).  x0..y1 are Fractions."""
    iv, feasible = box_vertices(ctx, x0, x1, y0, y1, ua, ub)
    if feasible is None:
        return "EMPTY"

    # ---- COVER: float-screen candidate points, then prove exactly, heaviest first
    fverts, fE = float_vertices(iv, feasible)
    cands = []
    total = 0.0
    lim = 0.5 + FLOAT_TOL
    for pi, (px, py) in enumerate(ctx.fpoints):
        ok = True
        for fv in fverts:
            for (vx, vy), ((a1, b1), (a2, b2)) in zip(fv, fE):
                dx, dy = px - vx, py - vy
                if abs(dx * a1 + dy * b1) > lim or abs(dx * a2 + dy * b2) > lim:
                    ok = False
                    break
            if not ok:
                break
        if ok:
            cands.append(pi)
            total += float(ctx.points[pi][2])
    def segment_order():
        # float estimate of the segment credits, largest first (guidance only)
        out = []
        for si, sg in enumerate(ctx.segments):
            fl = seg_float_min(sg, fverts, fE)
            if fl > 1e-9:
                out.append((float(sg.rho) * fl, si))
        return sorted(out, reverse=True)

    seg_order = None
    if total < 1 - 1e-12 and ctx.segments:
        seg_order = segment_order()
        # float estimate: the better of the sum of per-segment minima and the joint estimate
        # (min over vertices of the sum, README 6b)
        total += max(sum(v for v, _ in seg_order),
                     _joint_float_estimate(ctx, [si for _, si in seg_order], fverts, fE))
    if total < 1 - 1e-12 and not ctx.chord_pairs and not ctx.features:
        return None
    B_D2half = iv["B_D2half"]
    pairbern = []
    for pkey, pr in feasible:
        pb = iv["pairbern"].get(pkey) if pkey is not None else None
        if pb is None:
            pb = (to_bern(pr.W1, ua, ub), to_bern(pr.W2, ua, ub))
            if pkey is not None:
                iv["pairbern"][pkey] = pb
        pairbern.append(pb)
    acc = Fraction(0)
    used = set()
    proven = set()
    for pi in cands:
        BT1, BT2 = ctx.point_bern(iv, pi)
        if all(captured(B_D2half, BT1, BT2, BW1, BW2) for BW1, BW2 in pairbern):
            proven.add(pi)
            acc += ctx.points[pi][2]
            used.add(pi)
            if acc >= 1:
                return "COVER"
    # threshold features: fires on every pose of the box if >= k of its sites are proven captured.
    # (Budget side: disjoint closed squares share no site, so a feature fires in <= floor(m/k) of them.)
    for idx, k, w in ctx.features:
        if sum(1 for i in idx if i in proven) >= k:
            acc += w
            if acc >= 1:
                return "COVER"
    # Lemma P: for a chord pair (p, q) with |q - p| = 1, every pose of the box contains p or q.
    # Each point is counted at most once overall, so the bound min(w_p, w_q) is sound.
    for i, j, M in ctx.chord_pairs:
        if i in used or j in used:
            continue
        if chord_pair_holds(ctx, iv, i, M, feasible):
            acc += min(ctx.points[i][2], ctx.points[j][2])
            used.update((i, j))
            if acc >= 1:
                return "COVER"
    # Segment masses (README 6b): separate mass, so they add to every term above.
    if seg_order is None and ctx.segments:
        seg_order = segment_order()       # exact point proofs fell short of the float screen
    if not seg_order:
        return None
    base = acc                            # points + features + pairs (exact)
    old = {}
    for _, si in seg_order:
        sg = ctx.segments[si]
        lm = segment_credit(ctx, iv, sg, feasible, fverts, fE)
        old[si] = lm
        if lm > 0:
            acc += sg.rho * lm
            if acc >= 1:
                return "COVER"
    # Joint credit (README 6b): min over vertices of the sum, instead of the sum of minima.
    # Only when the float joint estimate clears the deficit and beats the per-segment credits.
    seg_ids = [si for _, si in seg_order]
    need = 1 - float(base)
    j_est = _joint_float_estimate(ctx, seg_ids, fverts, fE)
    if j_est >= need - 1e-12 and j_est > float(acc - base) + 1e-12:
        J = joint_segment_credit(ctx, iv, feasible, fverts, fE, seg_ids, old, need)
        if base + max(J, acc - base) >= 1:
            return "COVER"
    return None


# --------------------------------------------------------------------------- segments
SEG_POLY_DEPTH = 8       # halvings allowed in one segment test
SEG_SAFETY = 1e-6        # float safety subtracted before rounding lmin down
SEG_DEN = 2 ** 20        # lmin is a dyadic rational with this denominator
SEG_U_SPLITS = 3         # halvings of the u-interval allowed in one vertex proof
SEG_LADDER = (1e-6, 1e-5, 1e-4, 1e-3, 1e-2)   # safeties tried below the float minimum


def seg_float_eval(sg, vx, vy, e1, e2):
    """Float guidance: (length, lo, hi) of Q(v, theta) cap segment, where lo / hi is the active
    candidate for the lower / upper end: -1 for t = 0 / t = 1, else (k, sign of d.e_k)."""
    px, py = sg.fp
    dx, dy = sg.fd
    lo, lo_v = -1, 0.0
    hi, hi_v = -1, 1.0
    for k, (ax, ay) in enumerate((e1, e2)):
        m = dx * ax + dy * ay
        nk = (vx - px) * ax + (vy - py) * ay      # (c - p) . e_k
        if abs(m) < 1e-12:
            if abs(nk) > 0.5:
                return 0.0, None, None
            continue
        sgn = 1 if m > 0 else -1
        a = (nk - 0.5 * sgn) / m
        b = (nk + 0.5 * sgn) / m
        if a > lo_v:
            lo, lo_v = (k, sgn), a
        if b < hi_v:
            hi, hi_v = (k, sgn), b
    return max(0.0, hi_v - lo_v), lo, hi


def seg_float_min(sg, fverts, fE) -> float:
    """Float minimum of the intersection length over all vertex candidates and samples."""
    mn = 1.0
    for fv in fverts:
        for (vx, vy), (e1, e2) in zip(fv, fE):
            ln, _, _ = seg_float_eval(sg, vx, vy, e1, e2)
            if ln < mn:
                mn = ln
                if mn <= 0:
                    return 0.0
    return mn


def _seg_sign_ok(ctx, sg, k, sgn, ua, ub) -> bool:
    """Exact (cached): sgn * d.E_k > 0 on the whole interval [ua, ub]."""
    cache = ctx.seg_sign_cache
    key = (id(sg), k, sgn, ua.a, ua.b, ub.a, ub.b)
    r = cache.get(key)
    if r is None:
        if len(cache) > 20000:
            cache.clear()
        r = cache[key] = _nonneg(pscale(sg.M[k], Q2(sgn)), ua, ub, strict=True)
    return r


def _seg_vertex_exact(ctx, sg, pr, ua, ub, lo, hi, d0: Fraction, d1: Fraction, lmin: Fraction) -> bool:
    """Exact proof that, for every u in [ua, ub], at the vertex V(u) of this Pair the interval
    t in [t0(u), t1(u)] lies in [0, 1] and in both slabs of Q(V(u), theta), and t1 - t0 >= lmin.

    t0 = a0/b0 is d0 (lo = -1) or (lower slab end of axis k) + d0 = (s N_k - D^2/2)/(s D M_k) + d0;
    t1 = a1/b1 is 1 - d1 (hi = -1) or (upper slab end of axis k) - d1 = (s N_k + D^2/2)/(s D M_k) - d1;
    s = sign of M_k, proved strictly first, so b0, b1 > 0.  d0, d1 >= 0 are rational slacks.
    The slab conditions are linear in t, so checking them at t0 and t1 covers [t0, t1]; they are
    multiplied by b > 0.  Every condition is a polynomial in u that must be >= 0.
    """
    D2h = pscale(pmul(ctx.D, ctx.D), HALF)
    N = (psub(pr.W1, sg.T[0]), psub(pr.W2, sg.T[1]))

    def end(choice, lower, slack):
        if choice == -1:
            return ([Q2(slack)] if lower else [Q2(1 - slack)]), [ONE]
        k, sgn = choice
        if not _seg_sign_ok(ctx, sg, k, sgn, ua, ub):
            return None
        sN = pscale(N[k], Q2(sgn))
        b = pscale(sg.DM[k], Q2(sgn))
        if lower:
            return padd(psub(sN, D2h), pscale(b, Q2(slack))), b
        return psub(padd(sN, D2h), pscale(b, Q2(slack))), b

    e0 = end(lo, True, d0)
    e1 = end(hi, False, d1)
    if e0 is None or e1 is None:
        return False
    (a0, b0), (a1, b1) = e0, e1
    # length: t1 - t0 >= lmin  <=>  a1 b0 - a0 b1 - lmin b0 b1 >= 0
    conds = [psub(psub(pmul(a1, b0), pmul(a0, b1)), pscale(pmul(b0, b1), Q2(lmin))),
             a0,                    # t0 >= 0
             psub(b1, a1)]          # t1 <= 1
    for a, b in ((a0, b0), (a1, b1)):
        for k in (0, 1):
            # -D^2/2 <= N_k - t D M_k <= D^2/2 at t = a/b, times b > 0
            conds.append(padd(pmul(b, psub(D2h, N[k])), pmul(a, sg.DM[k])))
            conds.append(psub(pmul(b, padd(D2h, N[k])), pmul(a, sg.DM[k])))
    for c in conds:
        c = ptrim(c)
        if c and not bern_nonneg(to_bern(c, ua, ub, max(DEG, len(c) - 1)), SEG_POLY_DEPTH):
            return False
    return True


def _seg_float_candidates(sg, pr, ua, ub, n=N_SAMPLES):
    """Float guidance on [ua, ub]: per sample angle, the lower and upper candidates
    {choice: t} at the vertex V(u) (choice -1 is t = 0 / t = 1), or None if some sample has
    an axis with d.e_k ~ 0 and the vertex outside that slab (no intersection)."""
    fa, fb = float(ua), float(ub)
    px, py = sg.fp
    dx, dy = sg.fd
    out = []
    for i in range(n):
        u = fa + (fb - fa) * i / (n - 1)
        D = 1 + u * u
        vx, vy = feval(pr.fX, u) / D, feval(pr.fY, u) / D
        lows, highs = {-1: 0.0}, {-1: 1.0}
        for k, (ax, ay) in enumerate((((1 - u * u) / D, 2 * u / D), (-2 * u / D, (1 - u * u) / D))):
            m = dx * ax + dy * ay
            nk = (vx - px) * ax + (vy - py) * ay
            if abs(m) < 1e-12:
                if abs(nk) > 0.5:
                    return None
                continue
            sgn = 1 if m > 0 else -1
            lows[(k, sgn)] = (nk - 0.5 * sgn) / m
            highs[(k, sgn)] = (nk + 0.5 * sgn) / m
        out.append((lows, highs))
    return out


def _dyadic_up(x: float) -> Fraction:
    return Fraction(math.ceil(x * SEG_DEN), SEG_DEN) if x > 0 else Fraction(0)


def _seg_vertex_prove(ctx, sg, pr, ua, ub, lmin: Fraction, depth=SEG_U_SPLITS) -> bool:
    """Prove the vertex bound of README 6b on [ua, ub], with the active candidates chosen by
    floats.  If no choice works, split [ua, ub] (each half gets its own choice; the claim is
    for all u, so proving it on both halves suffices)."""
    cands = _seg_float_candidates(sg, pr, ua, ub)
    if cands is None:
        return False
    lo_opts, hi_opts = [], []
    for lows, highs in cands:
        lo = max(lows, key=lows.get)
        hi = min(highs, key=highs.get)
        if lo not in lo_opts:
            lo_opts.append(lo)
        if hi not in hi_opts:
            hi_opts.append(hi)
    fl = float(lmin) - 1e-9          # float tolerance: exact (margin-zero) lmin must not be skipped
    zero = Fraction(0)
    for lo in lo_opts:
        for hi in hi_opts:
            if any(lo not in lw or hi not in hg for lw, hg in cands):
                continue
            span = min(hg[hi] - lw[lo] for lw, hg in cands)
            # slack-free attempt first (needed when lmin is exact and the margin is zero)
            if span >= fl and _seg_vertex_exact(ctx, sg, pr, ua, ub, lo, hi, zero, zero, lmin):
                return True
            g0 = max(max(lw.values()) - lw[lo] for lw, _ in cands)
            g1 = max(hg[hi] - min(hg.values()) for _, hg in cands)
            d0 = _dyadic_up(1.25 * g0 + 1e-7) if g0 > 0 else zero
            d1 = _dyadic_up(1.25 * g1 + 1e-7) if g1 > 0 else zero
            if d0 == 0 and d1 == 0:
                continue                  # already tried above
            if span - float(d0 + d1) < fl:
                continue
            if _seg_vertex_exact(ctx, sg, pr, ua, ub, lo, hi, d0, d1, lmin):
                return True
    if depth <= 0:
        return False
    um = (ua + ub) * HALF
    return (_seg_vertex_prove(ctx, sg, pr, ua, um, lmin, depth - 1)
            and _seg_vertex_prove(ctx, sg, pr, um, ub, lmin, depth - 1))


def segment_credit(ctx, iv, sg, feasible, fverts=None, fE=None) -> Fraction:
    """First lmin proved exactly with |Q cap segment| >= lmin for every pose of the box, among:
    1 (if the float minimum is 1 up to 1e-9), the float minimum snapped to a fraction with
    denominator <= 1000 (if within 1e-9), then l = float minimum - 1e-6 rounded down to 2^-20,
    and l/2; else 0.  Floats only choose the candidates; every accepted value is proved.  Soundness: README item 6b (concavity, vertices suffice)."""
    if fverts is None:
        fverts, fE = float_vertices(iv, feasible)
    fmin = seg_float_min(sg, fverts, fE)
    ua, ub = iv["ua"], iv["ub"]
    for target in seg_targets(fmin):
        if all(_seg_vertex_prove(ctx, sg, pr, ua, ub, target) for _, pr in feasible):
            return target
    return Fraction(0)


def seg_targets(fmin: float, floor: Fraction = Fraction(0)):
    """Candidate lower bounds for a length whose float minimum is fmin, best first, all > floor:
    1. snapped exact values (margin-zero certificates): 1 if fmin > 1 - 1e-9, and
       Fraction(fmin).limit_denominator(1000) if within 1e-9 of fmin;
    2. the ladder fmin - 1e-6, -1e-5, -1e-4, -1e-3, -1e-2, each rounded down to 2^-20;
    3. half of the first ladder value.
    Floats only propose; the caller proves each candidate exactly."""
    out = []
    if fmin > 1 - 1e-9:
        out.append(Fraction(1))
    snap = Fraction(fmin).limit_denominator(1000)
    if snap > 0 and abs(float(snap) - fmin) < 1e-9:
        out.append(snap)
    first = None
    for eps in SEG_LADDER:
        fl = fmin - eps
        if fl > 0:
            v = Fraction(math.floor(fl * SEG_DEN), SEG_DEN)
            if v > 0:
                out.append(v)
                if first is None:
                    first = v
    if first is not None:
        out.append(first / 2)
    res = []
    for v in out:
        if v > floor and v not in res:
            res.append(v)
    return res


def _joint_float_estimate(ctx, seg_ids, fverts, fE) -> float:
    """Float guidance: min over vertex candidates of sum_i rho_i * (min over samples of len_i)."""
    if not seg_ids:
        return 0.0
    return min(sum(float(ctx.segments[si].rho) * _seg_vertex_floatmin(ctx.segments[si], fv, fE)
                   for si in seg_ids) for fv in fverts)


def _seg_vertex_floatmin(sg, fv, fE) -> float:
    """Float minimum length at one vertex candidate over the sample angles."""
    mn = 1.0
    for (vx, vy), (e1, e2) in zip(fv, fE):
        ln, _, _ = seg_float_eval(sg, vx, vy, e1, e2)
        mn = min(mn, ln)
    return mn


def joint_segment_credit(ctx, iv, feasible, fverts, fE, seg_ids, old, need):
    """Joint credit of README 6b (concavity of the sum).

    For each segment i in seg_ids and each vertex candidate v, prove a lower bound c[i][v] on
    the length at V_v(u) for all u in the bin (at least the per-segment credit old[i], which is
    already proved at every vertex).  Segments with c[i][v] > 0 at every candidate form the set
    P; the credit is  min_v sum_{i in P} rho_i c[i][v]  +  sum_{i not in P} rho_i old[i].
    Returns the credit (a Fraction).  Returns 0 early (always a sound lower bound) once the
    proved sum at some vertex is below the float target `need`, since the joint credit is at
    most that sum; this only saves time."""
    ua, ub = iv["ua"], iv["ub"]
    segs = [(si, ctx.segments[si]) for si in seg_ids]
    cols = []
    for (_, pr), fv in zip(feasible, fverts):
        col = {}
        tot = Fraction(0)
        for si, sg in segs:
            fl = _seg_vertex_floatmin(sg, fv, fE)
            c = old.get(si, Fraction(0))
            for t in seg_targets(fl, c):
                if _seg_vertex_prove(ctx, sg, pr, ua, ub, t):
                    c = t
                    break
            col[si] = c
            tot += sg.rho * c
        if float(tot) < need - 1e-12:
            return Fraction(0)          # the minimum over vertices cannot reach the target
        cols.append(col)
    P = [si for si, _ in segs if all(col[si] > 0 for col in cols)]
    J = min(sum((ctx.segments[si].rho * col[si] for si in P), Fraction(0)) for col in cols)
    others = sum((ctx.segments[si].rho * old.get(si, Fraction(0)) for si, _ in segs if si not in P),
                 Fraction(0))
    return J + others




def _nonneg(p, ua, ub, strict=False):
    p = ptrim(p)
    return bern_nonneg(to_bern(p, ua, ub, max(DEG, len(p) - 1)), POLY_DEPTH, strict)


def chord_pair_holds(ctx, iv, i, M, feasible) -> bool:
    """Exact proof of Lemma P on the box: for every u in the bin and every vertex c of P_theta,
    the line p + t d crosses the two edges of Q(c, theta) normal to e_k inside those edges, and the
    chord [t_-, t_+] (length 1/|d.e_k| >= 1) meets [0, 1]; hence p or q = p + d lies in Q.
    All conditions are linear in c for fixed u, so vertices suffice (P_theta is convex).
    With D = 1 + u^2, N_k = D^2 (c - p).e_k, M_k = D d.e_k (all polynomials in u):
      t_+- = (N_k +- D^2/2) / (D M_k).
    """
    ua, ub = iv["ua"], iv["ub"]
    D = ctx.D
    D2 = pmul(D, D)
    D2h = pscale(D2, HALF)
    T = ctx.pterms[i]
    for k in (0, 1):
        j = 1 - k
        Mk, Mj = M[k], M[j]
        if _nonneg(Mk, ua, ub, strict=True):
            sg = 1
        elif _nonneg(pscale(Mk, Q2(-1)), ua, ub, strict=True):
            sg = -1
        else:
            continue
        ok = True
        for _, pr in feasible:
            W = (pr.W1, pr.W2)
            Nk = psub(W[k], T[k])
            Nj = psub(W[j], T[j])
            K = pscale(pmul(D2h, Mk), Q2(sg))                   # D^2 |M_k| / 2
            conds = []
            for pm in (1, -1):
                numer = padd(pscale(pmul(Nj, Mk), Q2(-1)), pmul(padd(Nk, pscale(D2h, Q2(pm))), Mj))
                conds.append(psub(K, numer))
                conds.append(padd(K, numer))
            if sg > 0:
                conds.append(padd(psub(pmul(D, Mk), Nk), D2h))  # t_- <= 1
                conds.append(padd(Nk, D2h))                      # t_+ >= 0
            else:
                conds.append(psub(padd(Nk, D2h), pmul(D, Mk)))  # t_+ <= 1
                conds.append(psub(D2h, Nk))                      # t_- >= 0
            if not all(_nonneg(c, ua, ub) for c in conds):
                ok = False
                break
        if ok:
            return True
    return False


def captured(B_D2half, BT1, BT2, BW1, BW2) -> bool:
    """Exact: |(p - V(u)) . e_k(u)| <= 1/2 for k = 1, 2 and all u in the bin.

    Times D^2 > 0 this is D^2/2 -+ (T_k - W_k) >= 0, whose Bernstein vectors are
    obtained by linearity from the cached vectors.
    """
    for BT, BW in ((BT1, BW1), (BT2, BW2)):
        S = bsub(BT, BW)
        if not bern_nonneg(bsub(B_D2half, S), POLY_DEPTH):
            return False
        if not bern_nonneg(badd(B_D2half, S), POLY_DEPTH):
            return False
    return True


def pair_infeasible(ctx, iv, pr: Pair, all_lines, a, b) -> bool:
    """Exact proof that V_ab(u) strictly violates some third constraint for all u."""
    samples, fD = iv["samples"], iv["fD"]
    fx = [feval(pr.fX, s) for s in samples]
    fy = [feval(pr.fY, s) for s in samples]
    scored = []
    for m, (_, lm) in enumerate(all_lines):
        if m == a or m == b:
            continue
        mn = min((lm.fnx * x + lm.fny * y - feval(lm.fO, s)) / d
                 for x, y, s, d in zip(fx, fy, samples, fD))
        if mn > 1e-13:
            scored.append((mn, m))
    scored.sort(reverse=True)
    for _, m in scored[:3]:
        lm = all_lines[m][1]
        Q = psub(padd(pscale(pr.X, lm.nx), pscale(pr.Y, lm.ny)), lm.O)
        if ctx.prove_nonneg(Q, iv["ua"], iv["ub"], strict=True):
            return True
    return False


# =========================================================================== driver
_WORKER_CTX = None


def _init_worker(L_s, pts_s, opts):
    global _WORKER_CTX
    L = Q2.parse(L_s)
    pts = [(Q2.parse(x), Q2.parse(y), Fraction(w)) for x, y, w in pts_s]
    _WORKER_CTX = Context(L, pts, opts)
    _WORKER_CTX.opts["exclusions_parsed"] = [tuple(Q2.parse(v) for v in ex) for ex in opts.get("exclusions", [])]


def _split(box, u_scale):
    x0, x1, y0, y1, ua, ub = box
    wx = float(x1 - x0)
    wy = float(y1 - y0)
    wu = float(ub - ua) * u_scale
    if wu >= wx and wu >= wy:
        um = (ua + ub) * HALF
        return [(x0, x1, y0, y1, ua, um), (x0, x1, y0, y1, um, ub)]
    if wx >= wy:
        xm = (x0 + x1) / 2
        return [(x0, xm, y0, y1, ua, ub), (xm, x1, y0, y1, ua, ub)]
    ym = (y0 + y1) / 2
    return [(x0, x1, y0, ym, ua, ub), (x0, x1, ym, y1, ua, ub)]


def box_str(box):
    x0, x1, y0, y1, ua, ub = box
    return {"x": [str(x0), str(x1)], "y": [str(y0), str(y1)], "u": [str(ua), str(ub)]}


def run_root(task):
    """Adaptive subdivision of one root box (depth-first)."""
    ctx = _WORKER_CTX
    box = (Fraction(task[0]), Fraction(task[1]), Fraction(task[2]), Fraction(task[3]),
           Q2.parse(task[4]), Q2.parse(task[5]))
    max_depth = ctx.opts["max_depth"]
    u_scale = ctx.opts["u_scale"]
    st = {"EMPTY": 0, "COVER": 0, "EXCLUDED": 0, "uncertified": 0, "nodes": 0, "max_depth": 0, "unc_list": []}
    excl = ctx.opts.get("exclusions_parsed") or []
    def inside_exclusion(bx):
        x0, x1, y0, y1, ua, ub = bx
        for ex in excl:
            if (ex[0] <= Q2(x0)) and (Q2(x1) <= ex[1]) and (ex[2] <= Q2(y0)) and (Q2(y1) <= ex[3]) and (ex[4] <= ua) and (ub <= ex[5]):
                return True
        return False
    stack = [(box, 0)]
    while stack:
        bx, d = stack.pop()
        st["nodes"] += 1
        st["max_depth"] = max(st["max_depth"], d)
        if excl and inside_exclusion(bx):
            st["EXCLUDED"] += 1
            continue
        res = certify_box(ctx, *bx)
        if res is not None:
            st[res] += 1
        elif d >= max_depth:
            st["uncertified"] += 1
            if len(st["unc_list"]) < MAX_LISTED_UNCERTIFIED:
                st["unc_list"].append(box_str(bx))
        else:
            for child in reversed(_split(bx, u_scale)):
                stack.append((child, d + 1))
    return st


def root_u_breaks(sym, U, extra):
    """Root partition of the u-range (exact, sorted, deduplicated)."""
    if sym == "D1":
        lo, hi = Q2(0), U_D1
        pts = [lo, hi]
    else:
        lo, hi = Q2(0), Q2(1)
        pts = [lo, U_D1, hi]  # theta = 0, pi/4, pi/2
    for e in extra:
        if lo < e < hi:
            pts.append(e)
    uniq = []
    for p in pts:
        if not any(p == q for q in uniq):
            uniq.append(p)
    # exact insertion sort (few elements)
    out = []
    for p in uniq:
        i = 0
        while i < len(out) and out[i] < p:
            i += 1
        out.insert(i, p)
    return out


def rational_upper(v: Q2, den=64) -> Fraction:
    r = Fraction(math.ceil(float(v) * den) + 1, den)
    if not Q2(r) >= v:  # exact check of the float-guided bound
        raise RuntimeError("rational upper bound failed")
    return r


def check(cert, root=4, max_depth=40, jobs=1, u_breaks=(), U=None, u_scale=4, n=None, bbox=None):
    """Run the checker.  `cert` is a path or an already-parsed dict.  Returns the summary dict."""
    t0 = time.time()
    raw, L, sym, points, pairs, features, segments = load_certificate(cert)
    if raw is None:
        raw = json.dumps(cert, sort_keys=True).encode()
    summary = {
        "certificate_sha256": hashlib.sha256(raw).hexdigest(),
        "L": str(L),
        "points": len(points),
    }
    total = sum((w for _, _, w in points), Fraction(0))
    total += sum((Fraction(len(sites) // k) * w for sites, k, w in features), Fraction(0))
    total += sum((rho for _, _, rho in segments), Fraction(0))   # unit segments: rho * 1
    summary["total_weight"] = str(total)   # budget: points + sum floor(m/k) w + sum rho |pq|
    summary["features"] = len(features)
    summary["segments"] = len(segments)
    summary["symmetry"] = sym
    if n is not None:
        summary["n"] = n
        summary["total_weight_lt_n"] = total < n
    extra = [Q2.parse(s) for s in u_breaks]
    if sym == "D1":
        U = U_D1
        if (not check_d3_invariant(L, points) or not check_d3_features(L, features)
                or not check_d3_segments(L, segments)):
            summary.update(status="failed", reason="certificate (points, features or segments) is not D1-invariant")
            summary["seconds"] = round(time.time() - t0, 3)
            return summary
        summary["U"] = str(U)
    ubr = root_u_breaks(sym, U, extra)
    summary["u_breaks"] = [str(u) for u in ubr]
    # root grid over [0, B]^2: B is rational_upper(L) or a given rational bbox >= L (exactly checked);
    # a bbox like 6 for L = 5 puts the root-box faces on lines such as x = 3/2
    if bbox is not None:
        B = Fraction(bbox)
        if not Q2(B) >= L:
            raise CertError(f"bbox {B} is smaller than L")
    else:
        B = rational_upper(L)
    summary["bbox"] = str(B)
    Lx = Ly = B
    tasks = []
    for i in range(root):
        for j in range(root):
            for k in range(len(ubr) - 1):
                tasks.append((str(Lx * i / root), str(Lx * (i + 1) / root),
                              str(Ly * j / root), str(Ly * (j + 1) / root),
                              str(ubr[k]), str(ubr[k + 1])))
    opts = {"max_depth": max_depth, "u_scale": u_scale,
            "pairs": [(str(p[0]), str(p[1]), str(q[0]), str(q[1])) for p, q in pairs],
            "features": [([(str(x), str(y)) for x, y in sites], k, str(w)) for sites, k, w in features],
            "segments": [((str(p[0]), str(p[1])), (str(q[0]), str(q[1])), str(rho))
                         for p, q, rho in segments]}
    summary["pairs"] = len(pairs)
    data_ex = json.loads(raw.decode("utf-8")) if raw else (cert if isinstance(cert, dict) else {})
    exclusions = data_ex.get("exclusions", [])
    opts["exclusions"] = [(e["x"][0], e["x"][1], e["y"][0], e["y"][1], e["u"][0], e["u"][1]) for e in exclusions]
    summary["exclusions"] = len(exclusions)
    if exclusions:
        summary["claim"] = ("every admissible closed unit square captures >= 1, except poses whose image in the "
                            "fundamental domain (symmetry " + sym + ") lies in one of the listed exclusion boxes")
    # Obstacle points (README 6d): exact points strictly inside a core K that lies inside a square fixed by an
    # earlier stage.  A pose whose closed square contains one of them overlaps int K, so it is not a pose of
    # another square of the packing.  They get weight 1 for the box test and are not part of the budget.
    obstacle_points = data_ex.get("obstacle_points", [])
    if obstacle_points:
        if sym != "none":
            raise CertError("obstacle_points need symmetry 'none'")
        obs = [(Q2.parse(str(q["x"])), Q2.parse(str(q["y"]))) for q in obstacle_points]
        points = list(points) + [(x, y, Fraction(1)) for x, y in obs]
        summary["obstacle_points"] = len(obs)
        summary["claim"] = (summary.get("claim", "every admissible closed unit square captures >= 1")
                            + "; poses whose square contains an obstacle point are exempt (budget excludes them)")
    init_args = (str(L), [(str(x), str(y), str(w)) for x, y, w in points], opts)
    if jobs > 1:
        from multiprocessing import Pool
        with Pool(jobs, initializer=_init_worker, initargs=init_args) as pool:
            results = list(pool.imap_unordered(run_root, tasks))
    else:
        _init_worker(*init_args)
        results = [run_root(t) for t in tasks]
    agg = {"EMPTY": 0, "COVER": 0, "EXCLUDED": 0, "uncertified": 0, "nodes": 0, "max_depth": 0}
    unc = []
    for r in results:
        for k in ("EMPTY", "COVER", "EXCLUDED", "uncertified", "nodes"):
            agg[k] += r[k]
        agg["max_depth"] = max(agg["max_depth"], r["max_depth"])
        unc.extend(r["unc_list"])
    summary.update(
        root_boxes=len(tasks), root_grid=root, empty_leaves=agg["EMPTY"], cover_leaves=agg["COVER"], excluded_leaves=agg["EXCLUDED"],
        uncertified=agg["uncertified"], uncertified_boxes=unc[:MAX_LISTED_UNCERTIFIED],
        nodes=agg["nodes"], max_depth=agg["max_depth"], max_depth_limit=max_depth,
        seconds=round(time.time() - t0, 3),
        status="verified" if agg["uncertified"] == 0 else "failed",
    )
    return summary


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cert")
    ap.add_argument("--n", type=int, default=None, help="report whether the total weight is < n")
    ap.add_argument("--root", type=int, default=4, help="root grid is R x R over the bounding box")
    ap.add_argument("--max-depth", type=int, default=40)
    ap.add_argument("--jobs", type=int, default=1)
    ap.add_argument("--u-breaks", default="", help="extra u breakpoints, comma separated Q2 strings")
    ap.add_argument("--bbox", default=None, help="rational side of the root bounding box [0, B]^2 (B >= L)")
    ap.add_argument("--u-scale", type=float, default=4.0, help="weight of the u side when choosing the split")
    a = ap.parse_args(argv)
    breaks = [s for s in a.u_breaks.split(",") if s.strip()]
    s = check(a.cert, root=a.root, max_depth=a.max_depth, jobs=a.jobs, u_breaks=breaks,
              u_scale=a.u_scale, n=a.n, bbox=a.bbox)
    print(json.dumps(s, indent=2))
    print(f"total weight = {s['total_weight']}", file=sys.stderr)
    if a.n is not None:
        print(f"total weight < n={a.n}: {s['total_weight_lt_n']}", file=sys.stderr)
    return 0 if s["status"] == "verified" else 1


if __name__ == "__main__":
    sys.exit(main())
