#!/usr/bin/env python3
"""Exact checker (regular hexagon version, adapted from the triangle checker):
a weighted point set is unavoidable for closed unit squares in H_L.

Claim proved when the status is "verified":

    for every closed unit square Q with Q contained in H_L (any position, any angle):
        sum of w_i over the points p_i in Q  >=  1

H_L is the regular hexagon of side L with centre (L, L*sqrt3/2) and vertices (L/2, 0), (3L/2, 0),
(2L, L*sqrt3/2), (3L/2, L*sqrt3), (L/2, L*sqrt3), (0, L*sqrt3/2) (flat bottom, inside [0,2L]x[0,L*sqrt3]).  See README.md for
the lemmas.  Every accepted inequality is decided with exact Q(sqrt3) arithmetic
(module q3) and exact Bernstein coefficients (module poly).  Floats are used only
to decide what to try (candidate points, candidate separating constraints, where
to split); a wrong float guess can only cost time, never soundness.

Usage:
    python check.py cert.json [--n N] [--root R] [--max-depth D] [--jobs J]
                              [--u-breaks "u1,u2,..."] [--U 1/7] [--u-scale 4]
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

from q3 import Q3, ZERO, ONE, SQRT3  # noqa: E402
from poly import (  # noqa: E402
    DEG, padd, psub, pscale, pmul, ptrim, pfloat, feval, to_bern, bsub, badd, bern_nonneg, peval,
)

HALF = Fraction(1, 2)
POLY_DEPTH = 12          # halvings allowed inside one polynomial test
FLOAT_TOL = 1e-9         # float slack used only for guidance
N_SAMPLES = 9            # float sample angles per u-bin (guidance only)
MAX_LISTED_UNCERTIFIED = int(os.environ.get("CHECK_MAX_LISTED", "200"))  # env override for LP feedback


# =========================================================================== certificate
class CertError(ValueError):
    pass


def load_certificate(path_or_obj):
    """Return (raw_bytes_or_None, L, symmetry, merged points [(x, y, w)])."""
    raw = None
    if isinstance(path_or_obj, (str, os.PathLike)):
        with open(path_or_obj, "rb") as f:
            raw = f.read()
        data = json.loads(raw.decode("utf-8"))
    else:
        data = path_or_obj
    L = Q3.parse(str(data["L"]))
    if L.sign() <= 0:
        raise CertError("L must be positive")
    sym = data.get("symmetry", "none")
    if sym not in ("none", "D6"):
        raise CertError(f"unknown symmetry {sym!r}")
    merged: dict = {}
    for pt in data["points"]:
        x = Q3.parse(str(pt["x"]))
        y = Q3.parse(str(pt["y"]))
        w = Fraction(str(pt["w"]))
        if w < 0:
            raise CertError("weights must be >= 0")
        merged[(x, y)] = merged.get((x, y), Fraction(0)) + w
    points = [(x, y, w) for (x, y), w in merged.items() if w > 0]
    raw_pts = [(Q3.parse(str(pt["x"])), Q3.parse(str(pt["y"]))) for pt in data["points"]]
    pairs = []
    for i, j in data.get("pairs", []):
        p, q = raw_pts[i], raw_pts[j]
        dx, dy = q[0] - p[0], q[1] - p[1]
        if not (dx * dx + dy * dy == Q3(1)):
            raise CertError(f"pair ({i}, {j}) is not at distance exactly 1")
        if merged.get(p, 0) <= 0 or merged.get(q, 0) <= 0:
            raise CertError(f"pair ({i}, {j}) uses a point of weight 0")
        pairs.append((p, q))
    features = []
    for ft in data.get("features", []):
        sites = [(Q3.parse(str(q["x"])), Q3.parse(str(q["y"]))) for q in ft["sites"]]
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
    excused = []
    for e in data.get("excused", []):
        x0, x1, y0, y1 = (Fraction(str(v)) for v in e[:4])
        u0, u1 = Q3.parse(str(e[4])), Q3.parse(str(e[5]))
        if not (x0 < x1 and y0 < y1 and u0 < u1):
            raise CertError("bad excused box")
        excused.append((x0, x1, y0, y1, u0, u1))
    return raw, L, sym, points, pairs, features, excused


def d6_images(L: Q3, x: Q3, y: Q3):
    """The generators of the symmetry group D6 of H_L applied to (x, y)."""
    gx = L
    gy = L * SQRT3 * HALF
    dx, dy = x - gx, y - gy
    # rotation by pi / 3: [[1/2, -sqrt3/2], [sqrt3/2, 1/2]]
    rx = gx + dx * HALF - dy * (SQRT3 * HALF)
    ry = gy + dx * (SQRT3 * HALF) + dy * HALF
    # reflection x -> 2L - x
    return [(rx, ry), (L + L - x, y)]


def check_d6_features(L: Q3, features) -> bool:
    """The multiset of features (site set, k, w) is invariant under both generators."""
    def canon(ft):
        sites, k, w = ft
        return (frozenset(sites), k, w)
    base = sorted(map(repr, map(canon, features)))
    for g in range(2):
        imgs = []
        for sites, k, w in features:
            imgs.append(canon((tuple(d6_images(L, x, y)[g] for x, y in sites), k, w)))
        if sorted(map(repr, imgs)) != base:
            return False
    return True


def check_d6_invariant(L: Q3, points) -> bool:
    """Exact check that the weighted multiset is invariant under the D6 generators."""
    wmap = {(x, y): w for x, y, w in points}
    for x, y, w in points:
        for img in d6_images(L, x, y):
            if wmap.get(img) != w:
                return False
    return True


def check_U(U: Fraction) -> bool:
    """Exact proof that theta(U) = 2 arctan U > pi/12 and U <= 1.

    cos theta(U) = (1-U^2)/(1+U^2) = c.  theta in (0, pi/2] is decreasing in cos, and
    cos(pi/12) = (sqrt6 + sqrt2)/4 > 0 with square (2 + sqrt3)/4.  For c >= 0:
    c < cos(pi/12)  <=>  c^2 < (2 + sqrt3)/4 (both sides nonnegative).
    """
    if not (0 < U <= 1):
        return False
    c = (1 - U * U) / (1 + U * U)
    if c < 0:
        return True
    return Q3(c * c) < Q3(Fraction(1, 2), Fraction(1, 4))


# =========================================================================== geometry
class Line:
    """Half-plane n . c <= O(u) / D(u), D = 1 + u^2, n constant (Q3)."""

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
        q = lambda *c: [Q3(v) if not isinstance(v, Q3) else v for v in c]  # noqa: E731
        self.D = q(1, 0, 1)
        self.E1x, self.E1y = q(1, 0, -1), q(0, 2)
        self.E2x, self.E2y = q(0, -2), q(1, 0, -1)
        self.D2half = pscale(pmul(self.D, self.D), HALF)
        self.KE1x, self.KE1y = pmul(self.D, self.E1x), pmul(self.D, self.E1y)
        self.KE2x, self.KE2y = pmul(self.D, self.E2x), pmul(self.D, self.E2y)
        # admissibility: n_k . c <= b_k - n_k . (R_theta sigma), times D
        # outward normals and offsets of the six sides of H_L
        normals = [
            (ZERO, Q3(-1), ZERO),
            (ZERO, Q3(1), SQRT3 * L),
            (SQRT3 * HALF, -Q3(HALF), SQRT3 * L * Fraction(3, 4)),
            (SQRT3 * HALF, Q3(HALF), SQRT3 * L * Fraction(5, 4)),
            (-SQRT3 * HALF, Q3(HALF), SQRT3 * L * Fraction(1, 4)),
            (-SQRT3 * HALF, -Q3(HALF), -SQRT3 * L * Fraction(1, 4)),
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
            p = (Q3.parse(xs), Q3.parse(ys))
            q = (Q3.parse(xs2), Q3.parse(ys2))
            dx, dy = q[0] - p[0], q[1] - p[1]
            M = (padd(pscale(self.E1x, dx), pscale(self.E1y, dy)),      # d . E1
                 padd(pscale(self.E2x, dx), pscale(self.E2y, dy)))      # d . E2
            self.chord_pairs.append((index[p], index[q], M))
        self.excused = [(Fraction(e[0]), Fraction(e[1]), Fraction(e[2]), Fraction(e[3]), Q3.parse(e[4]), Q3.parse(e[5]))
                        for e in opts.get("excused", [])]
        self.features = []
        for sites, k, w in opts.get("features", []):
            idx = [index[(Q3.parse(x), Q3.parse(y))] for x, y in sites]
            self.features.append((idx, k, Fraction(w)))

    # ------------------------------------------------------------------ intervals
    def interval(self, ua: Q3, ub: Q3):
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
def certify_box(ctx: Context, x0, x1, y0, y1, ua: Q3, ub: Q3):
    """Return "EMPTY", "COVER" or None (not certified).  x0..y1 are Fractions."""
    iv = ctx.interval(ua, ub)
    samples, fD = iv["samples"], iv["fD"]
    corners = [(Q3(x0), Q3(y0)), (Q3(x0), Q3(y1)), (Q3(x1), Q3(y0)), (Q3(x1), Q3(y1))]
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
                return "EMPTY"
        if max(fvals) < min(fO) - FLOAT_TOL:
            # candidate: rectangle inside the half-plane for all u  =>  redundant
            mx = max(ln.nx * cx + ln.ny * cy for cx, cy in corners)
            if ctx.prove_nonneg(psub(ln.O, pscale(D, mx)), ua, ub):
                continue
        lines.append((idx, ln))

    # ---- rectangle lines (offset times D, so all lines share the denominator D)
    rect = [
        Line(ONE, ZERO, pscale(D, Q3(x1)), ("rect", "x1")),
        Line(-ONE, ZERO, pscale(D, Q3(-x0)), ("rect", "x0")),
        Line(ZERO, ONE, pscale(D, Q3(y1)), ("rect", "y1")),
        Line(ZERO, -ONE, pscale(D, Q3(-y0)), ("rect", "y0")),
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
        return "EMPTY"

    # ---- COVER: float-screen candidate points, then prove exactly, heaviest first
    fverts = []
    for _, pr in feasible:
        fverts.append([(feval(pr.fX, s) / d, feval(pr.fY, s) / d) for s, d in zip(samples, fD)])
    fE = [((e1x / d, e1y / d), (e2x / d, e2y / d))
          for (e1x, e1y), (e2x, e2y), d in zip(iv["fE1"], iv["fE2"], fD)]
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
    return None


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
        elif _nonneg(pscale(Mk, Q3(-1)), ua, ub, strict=True):
            sg = -1
        else:
            continue
        ok = True
        for _, pr in feasible:
            W = (pr.W1, pr.W2)
            Nk = psub(W[k], T[k])
            Nj = psub(W[j], T[j])
            K = pscale(pmul(D2h, Mk), Q3(sg))                   # D^2 |M_k| / 2
            conds = []
            for pm in (1, -1):
                numer = padd(pscale(pmul(Nj, Mk), Q3(-1)), pmul(padd(Nk, pscale(D2h, Q3(pm))), Mj))
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
    L = Q3.parse(L_s)
    pts = [(Q3.parse(x), Q3.parse(y), Fraction(w)) for x, y, w in pts_s]
    _WORKER_CTX = Context(L, pts, opts)


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


def box_excused(ctx, bx):
    """The whole box (all centres and all u in it) lies inside one excused box (exact comparisons)."""
    x0, x1, y0, y1, ua, ub = bx
    for e in ctx.excused:
        if e[0] <= x0 and x1 <= e[1] and e[2] <= y0 and y1 <= e[3] and not (ua < e[4]) and not (e[5] < ub):
            return True
    return False


def run_root(task):
    """Adaptive subdivision of one root box (depth-first)."""
    ctx = _WORKER_CTX
    box = (Fraction(task[0]), Fraction(task[1]), Fraction(task[2]), Fraction(task[3]),
           Q3.parse(task[4]), Q3.parse(task[5]))
    max_depth = ctx.opts["max_depth"]
    u_scale = ctx.opts["u_scale"]
    st = {"EMPTY": 0, "COVER": 0, "EXCUSED": 0, "uncertified": 0, "nodes": 0, "max_depth": 0, "unc_list": []}
    stack = [(box, 0)]
    while stack:
        bx, d = stack.pop()
        st["nodes"] += 1
        st["max_depth"] = max(st["max_depth"], d)
        res = "EXCUSED" if box_excused(ctx, bx) else certify_box(ctx, *bx)
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
    if sym == "D6":
        lo, hi = Q3(0), Q3(U)
        pts = [lo, hi]
    else:
        lo, hi = Q3(0), Q3(1)
        pts = [lo, Q3(2, -1), SQRT3 / 3, hi]  # theta = 0, pi/6, pi/3, pi/2
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


def rational_upper(v: Q3, den=64) -> Fraction:
    r = Fraction(math.ceil(float(v) * den) + 1, den)
    if not Q3(r) >= v:  # exact check of the float-guided bound
        raise RuntimeError("rational upper bound failed")
    return r


def check(cert, root=4, max_depth=40, jobs=1, u_breaks=(), U=Fraction(1, 7), u_scale=4, n=None):
    """Run the checker.  `cert` is a path or an already-parsed dict.  Returns the summary dict."""
    t0 = time.time()
    raw, L, sym, points, pairs, features, excused = load_certificate(cert)
    if raw is None:
        raw = json.dumps(cert, sort_keys=True).encode()
    summary = {
        "certificate_sha256": hashlib.sha256(raw).hexdigest(),
        "L": str(L),
        "points": len(points),
    }
    total = sum((w for _, _, w in points), Fraction(0))
    total += sum((Fraction(len(sites) // k) * w for sites, k, w in features), Fraction(0))
    summary["total_weight"] = str(total)   # budget: points + sum floor(m/k) w over features
    summary["features"] = len(features)
    summary["symmetry"] = sym
    if n is not None:
        summary["n"] = n
        summary["total_weight_lt_n"] = total < n
    extra = [Q3.parse(s) for s in u_breaks]
    if sym == "D6":
        U = Fraction(U)
        if not check_U(U):
            raise CertError(f"U = {U} does not satisfy U <= 1 and theta(U) > pi/12")
        if not check_d6_invariant(L, points) or not check_d6_features(L, features):
            summary.update(status="failed", reason="point set is not D6-invariant")
            summary["seconds"] = round(time.time() - t0, 3)
            return summary
        summary["U"] = str(U)
    ubr = root_u_breaks(sym, U, extra)
    summary["u_breaks"] = [str(u) for u in ubr]
    Lx = rational_upper(L + L)
    Ly = rational_upper(L * SQRT3)
    tasks = []
    for i in range(root):
        for j in range(root):
            for k in range(len(ubr) - 1):
                tasks.append((str(Lx * i / root), str(Lx * (i + 1) / root),
                              str(Ly * j / root), str(Ly * (j + 1) / root),
                              str(ubr[k]), str(ubr[k + 1])))
    opts = {"max_depth": max_depth, "u_scale": u_scale,
            "excused": [tuple(str(v) for v in e) for e in excused],
            "pairs": [(str(p[0]), str(p[1]), str(q[0]), str(q[1])) for p, q in pairs],
            "features": [([(str(x), str(y)) for x, y in sites], k, str(w)) for sites, k, w in features]}
    summary["pairs"] = len(pairs)
    init_args = (str(L), [(str(x), str(y), str(w)) for x, y, w in points], opts)
    if jobs > 1:
        from multiprocessing import Pool
        with Pool(jobs, initializer=_init_worker, initargs=init_args) as pool:
            results = []
            for r_ in pool.imap_unordered(run_root, tasks):
                results.append(r_)
                # progress on stderr: root boxes done / total, nodes and uncertified so far
                print(f"progress {len(results)}/{len(tasks)} roots, nodes {sum(x['nodes'] for x in results)}, "
                      f"uncertified {sum(x['uncertified'] for x in results)}, t={time.time() - t0:.0f}s",
                      file=sys.stderr, flush=True)
    else:
        _init_worker(*init_args)
        results = [run_root(t) for t in tasks]
    agg = {"EMPTY": 0, "COVER": 0, "EXCUSED": 0, "uncertified": 0, "nodes": 0, "max_depth": 0}
    unc = []
    for r in results:
        for k in ("EMPTY", "COVER", "EXCUSED", "uncertified", "nodes"):
            agg[k] += r[k]
        agg["max_depth"] = max(agg["max_depth"], r["max_depth"])
        unc.extend(r["unc_list"])
    summary.update(
        root_boxes=len(tasks), root_grid=root, empty_leaves=agg["EMPTY"], cover_leaves=agg["COVER"],
        excused_leaves=agg["EXCUSED"], excused_boxes=len(excused),
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
    ap.add_argument("--u-breaks", default="", help="extra u breakpoints, comma separated Q3 strings")
    ap.add_argument("--U", default="1/7", help="u-range end for symmetry D6 (rational)")
    ap.add_argument("--u-scale", type=float, default=4.0, help="weight of the u side when choosing the split")
    a = ap.parse_args(argv)
    breaks = [s for s in a.u_breaks.split(",") if s.strip()]
    s = check(a.cert, root=a.root, max_depth=a.max_depth, jobs=a.jobs, u_breaks=breaks,
              U=Fraction(a.U), u_scale=a.u_scale, n=a.n)
    print(json.dumps(s, indent=2))
    print(f"total weight = {s['total_weight']}", file=sys.stderr)
    if a.n is not None:
        print(f"total weight < n={a.n}: {s['total_weight_lt_n']}", file=sys.stderr)
    return 0 if s["status"] == "verified" else 1


if __name__ == "__main__":
    sys.exit(main())
