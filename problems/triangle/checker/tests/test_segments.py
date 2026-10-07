"""Tests for segment masses (README item 6b)."""
import math
import random
from fractions import Fraction as F

import pytest

import check as C
from q3 import Q3, SQRT3

L2 = "2+2/3*sqrt3"


def seg_json(p, q, rho):
    return {"p": {"x": str(p[0]), "y": str(p[1])}, "q": {"x": str(q[0]), "y": str(q[1])}, "rho": str(rho)}


def d3_orbit_segments(L, p, q, rho):
    """The three rotation images of segment pq (closed under the reflection when pq is)."""
    out = []
    for _ in range(3):
        out.append(seg_json(p, q, rho))
        p, q = C.d3_images(L, *p)[0], C.d3_images(L, *q)[0]
    return out


# ----------------------------------------------------------------- certificate checks
def test_segment_must_have_unit_length():
    base = {"L": L2, "symmetry": "none", "points": []}
    ok = dict(base, segments=[seg_json((Q3(0), Q3(1)), (Q3(F(3, 5)), Q3(F(9, 5))), "1/2")])
    assert len(C.load_certificate(ok)[6]) == 1
    # sqrt3-coordinates with exact unit length: (1/2, sqrt3/2)
    ok2 = dict(base, segments=[seg_json((Q3(1), Q3(0)), (Q3(F(3, 2)), SQRT3 / 2), "1")])
    assert len(C.load_certificate(ok2)[6]) == 1
    bad_pairs = [
        ((Q3(0), Q3(1)), (Q3(F(3, 5)), Q3(F(9, 5)) + F(1, 1000))),   # length slightly off
        ((Q3(0), Q3(0)), (Q3(1), Q3(1))),                            # length sqrt2
        ((Q3(1), Q3(0)), (Q3(F(3, 2)), SQRT3 / 2 + F(1, 10**9))),    # tiny irrational error
        ((Q3(0), Q3(0)), (Q3(0), Q3(0))),                            # degenerate
    ]
    for p, q in bad_pairs:
        with pytest.raises(C.CertError):
            C.load_certificate(dict(base, segments=[seg_json(p, q, "1/2")]))
    neg = dict(base, segments=[seg_json((Q3(0), Q3(1)), (Q3(F(3, 5)), Q3(F(9, 5))), "-1/2")])
    with pytest.raises(C.CertError):
        C.load_certificate(neg)


def test_d3_segment_invariance():
    L = Q3.parse(L2)
    gx = L / 2
    p, q = (gx - F(1, 2), Q3(F(1, 2))), (gx + F(1, 2), Q3(F(1, 2)))      # symmetric under x -> L - x
    segs = C.load_certificate({"L": L2, "points": [], "segments": d3_orbit_segments(L, p, q, "1/3")})[6]
    assert len(segs) == 3 and C.check_d3_segments(L, segs)
    assert not C.check_d3_segments(L, segs[:2])
    p2, q2 = (gx - F(2, 5), Q3(F(1, 2))), (gx + F(3, 5), Q3(F(1, 2)))    # not reflection-symmetric
    segs2 = C.load_certificate({"L": L2, "points": [], "segments": d3_orbit_segments(L, p2, q2, "1/3")})[6]
    assert C.check_d3_segments(L, segs2) is False
    s = C.check({"L": L2, "symmetry": "D3", "points": [], "segments": d3_orbit_segments(L, p2, q2, "1/3")})
    assert s["status"] == "failed" and "D3" in s["reason"]


def test_budget_counts_segments():
    L = Q3.parse(L2)
    gx = L / 2
    cert = {"L": L2, "symmetry": "none",
            "points": [{"x": str(gx), "y": str(L * SQRT3 / 6), "w": "1"}],
            "segments": [seg_json((gx - F(1, 2), Q3(F(1, 2))), (gx + F(1, 2), Q3(F(1, 2))), "1/4")]}
    s = C.check(cert, max_depth=40)
    assert s["total_weight"] == "5/4" and s["segments"] == 1
    assert s["status"] == "verified"           # the centroid alone already verifies


# ----------------------------------------------------------------- the box routine vs. sampling
def fl_capture_length(px, py, dx, dy, cx, cy, th):
    """Independent float clip of p + t d (t in [0, 1]) against the square Q(c, theta)."""
    lo, hi = 0.0, 1.0
    for ax, ay in ((math.cos(th), math.sin(th)), (-math.sin(th), math.cos(th))):
        m = dx * ax + dy * ay
        n = (px - cx) * ax + (py - cy) * ay           # (p - c) . e
        # need |n + t m| <= 1/2
        if abs(m) < 1e-15:
            if abs(n) > 0.5:
                return 0.0
            continue
        t1, t2 = (-0.5 - n) / m, (0.5 - n) / m
        lo, hi = max(lo, min(t1, t2)), min(hi, max(t1, t2))
    return max(0.0, hi - lo) * math.hypot(dx, dy)


def fl_admissible(L, cx, cy, th):
    h = math.sqrt(3) / 2
    for sx in (0.5, -0.5):
        for sy in (0.5, -0.5):
            vx = cx + math.cos(th) * sx - math.sin(th) * sy
            vy = cy + math.sin(th) * sx + math.cos(th) * sy
            if vy < 0 or h * vx + 0.5 * vy > h * L or -h * vx + 0.5 * vy > 0:
                return False
    return True


def rational_unit(s):
    s = F(s)
    return Q3((1 - s * s) / (1 + s * s)), Q3(2 * s / (1 + s * s))


def sampled_min(ctx_L, sg, box, rng, n=1500):
    x0, x1, y0, y1, ua, ub = [float(v) for v in box]
    px, py = sg.fp
    dx, dy = sg.fd
    mn, hits = float("inf"), 0
    corners = [(x0, y0), (x0, y1), (x1, y0), (x1, y1)]
    for i in range(n + 4 * 9):
        if i < 36:   # include box corners at a grid of angles (where minima tend to sit)
            cx, cy = corners[i % 4]
            u = ua + (ub - ua) * (i // 4) / 8
        else:
            cx, cy = rng.uniform(x0, x1), rng.uniform(y0, y1)
            u = rng.uniform(ua, ub)
        th = 2 * math.atan(u)
        if not fl_admissible(ctx_L, cx, cy, th):
            continue
        hits += 1
        mn = min(mn, fl_capture_length(px, py, dx, dy, cx, cy, th))
    return mn, hits


def test_segment_credit_is_below_sampled_minimum():
    L = Q3.parse(L2)
    Lf = float(L)
    rng = random.Random(2024)
    positive = 0
    checked = 0
    tries = 0
    while checked < 14 and tries < 400:
        tries += 1
        u0 = F(rng.randint(0, 60), 64)
        ua, ub = Q3(u0), Q3(u0 + F(1, 64))
        cx = F(rng.randint(60, int(Lf * 64) - 60), 64)
        cy = F(rng.randint(30, 60), 64)
        h = F(1, 128)
        th = 2 * math.atan(float(u0) + 1 / 128)
        if not fl_admissible(Lf, float(cx), float(cy), th):
            continue
        dvec = rational_unit(F(rng.randint(-12, 12), 12))
        off = (F(rng.randint(-20, 20), 100), F(rng.randint(-20, 20), 100))
        p = (Q3(cx + off[0]) - dvec[0] / 2, Q3(cy + off[1]) - dvec[1] / 2)
        q = (p[0] + dvec[0], p[1] + dvec[1])
        opts = {"segments": [((str(p[0]), str(p[1])), (str(q[0]), str(q[1])), "1")]}
        ctx = C.Context(L, [], opts)
        sg = ctx.segments[0]
        box = (cx - h, cx + h, cy - h, cy + h, ua, ub)
        iv, feasible = C.box_vertices(ctx, *box)
        if feasible is None:
            continue
        lm = C.segment_credit(ctx, iv, sg, feasible)
        smin, hits = sampled_min(Lf, sg, box, rng)
        if hits < 20:
            continue
        checked += 1
        assert lm >= 0
        assert float(lm) <= smin + 1e-12, (box, p, q, lm, smin)
        if lm > 0:
            positive += 1
            assert float(lm) >= smin / 2 - 1e-3   # the routine is not vacuous: within the l/2 fallback
    assert checked >= 10
    assert positive >= 5, positive


def test_segment_credit_zero_when_avoidable():
    """A box of bottom-left squares near theta = 0; the segment lies near the top vertex."""
    L = Q3.parse(L2)
    top = (L / 2, L * SQRT3 / 2 - 1)
    p, q = (top[0] - F(1, 2), top[1]), (top[0] + F(1, 2), top[1])
    ctx = C.Context(L, [], {"segments": [((str(p[0]), str(p[1])), (str(q[0]), str(q[1])), "1")]})
    box = (F(1), F(9, 8), F(1, 2), F(5, 8), Q3(0), Q3(F(1, 32)))
    iv, feasible = C.box_vertices(ctx, *box)
    assert feasible is not None
    assert C.segment_credit(ctx, iv, ctx.segments[0], feasible) == 0
    # a box that is half admissible and half not, with a segment crossing only part of it
    p2 = (Q3(F(1)), Q3(F(9, 16)))
    q2 = (Q3(F(2)), Q3(F(9, 16)))
    ctx2 = C.Context(L, [], {"segments": [((str(p2[0]), str(p2[1])), (str(q2[0]), str(q2[1])), "1")]})
    box2 = (F(1), F(3, 2), F(1, 2), F(1), Q3(0), Q3(F(1, 8)))
    iv2, feas2 = C.box_vertices(ctx2, *box2)
    assert feas2 is not None
    smin, hits = sampled_min(float(L), ctx2.segments[0], box2, random.Random(5))
    lm = C.segment_credit(ctx2, iv2, ctx2.segments[0], feas2)
    assert hits > 0 and float(lm) <= smin + 1e-12


# ----------------------------------------------------------------- end to end
def bottom_segment_cert(rho, eps="1/20", sym="D3"):
    """L just above the n = 1 threshold 1 + 2/sqrt3: every admissible square is close to the
    axis-parallel square on one side's midpoint, so the three mid-height unit segments of the
    D3 orbit give each square nearly unit length of one of them."""
    L = Q3.parse(f"1+{eps}+2/3*sqrt3")
    p = (L / 2 - F(1, 2), Q3(F(1, 2)))
    q = (L / 2 + F(1, 2), Q3(F(1, 2)))
    return {"L": str(L), "symmetry": sym, "points": [], "segments": d3_orbit_segments(L, p, q, rho)}


def test_segments_only_certificate_verifies():
    s = C.check(bottom_segment_cert("2"), max_depth=30)
    assert s["status"] == "verified", s
    assert s["total_weight"] == "6" and s["segments"] == 3


def test_segments_only_tight_densities():
    """The float minimum capture per unit density is ~2.6571 (seg_probe).  A density 2% above
    1/2.6571 verifies; 3% below must not."""
    import seg_probe
    r = seg_probe.probe(bottom_segment_cert("1"), samples=40000, refine=10)
    assert 2.64 < r["min_capture"] < 2.67, r
    s = C.check(bottom_segment_cert("81/211"), max_depth=30)        # 81/211 * 2.6571 = 1.020
    assert s["status"] == "verified", s
    s = C.check(bottom_segment_cert("349/956"), max_depth=8)        # 349/956 * 2.6571 = 0.970
    assert s["status"] == "failed" and s["uncertified"] > 0


def test_seg_probe_n2_centroid():
    import seg_probe
    L = Q3.parse(L2)
    cert = {"L": L2, "symmetry": "none",
            "points": [{"x": str(L / 2), "y": str(L * SQRT3 / 6), "w": "1"}]}
    r = seg_probe.probe(cert, samples=20000, refine=5)
    assert r["min_capture"] == 1.0


# ----------------------------------------------------------------- snapped (exact) credit
def test_snapped_credit_margin_zero():
    """At L = 1 + 2/sqrt3 the only admissible pose with theta = 0 is the square [L/2 - 1/2,
    L/2 + 1/2] x [0, 1] standing on the base.  The unit segment is its bottom edge, so the
    intersection length is exactly 1 with margin zero.  The snapped candidate must prove credit
    exactly 1; the old safe path (float min - 1e-6, dyadic) gives strictly less."""
    L = Q3.parse("1+2/3*sqrt3")
    p, q = (L / 2 - F(1, 2), Q3(0)), (L / 2 + F(1, 2), Q3(0))
    ctx = C.Context(L, [], {"segments": [((str(p[0]), str(p[1])), (str(q[0]), str(q[1])), "1")]})
    cx = float(L) / 2
    e = F(1, 1024)
    x0 = F(math.floor(cx * 1024), 1024)
    box = (x0 - e, x0 + 2 * e, F(1, 2) - e, F(1, 2) + e, Q3(0), Q3(0))   # single angle u = 0
    iv, feasible = C.box_vertices(ctx, *box)
    assert feasible is not None
    assert C.segment_credit(ctx, iv, ctx.segments[0], feasible) == 1
    # the safe dyadic value alone would be < 1
    fverts, fE = C.float_vertices(iv, feasible)
    fmin = C.seg_float_min(ctx.segments[0], fverts, fE)
    assert F(math.floor((fmin - C.SEG_SAFETY) * C.SEG_DEN), C.SEG_DEN) < 1


def test_snapped_credit_tilted_segment():
    """A unit segment at 45 degrees through the square centre lies inside every square of a small
    box of poses (positive-width u-bin), so the proved credit is exactly 1 via the snap."""
    L = Q3.parse(L2)
    c = (F(8, 5), F(7, 10))
    d = rational_unit(F(2, 5))            # (21/29, 20/29), close to 45 degrees
    p = (Q3(c[0]) - d[0] / 2, Q3(c[1]) - d[1] / 2)
    q = (p[0] + d[0], p[1] + d[1])
    ctx = C.Context(L, [], {"segments": [((str(p[0]), str(p[1])), (str(q[0]), str(q[1])), "1")]})
    e = F(1, 256)
    box = (c[0] - e, c[0] + e, c[1] - e, c[1] + e, Q3(0), Q3(F(1, 64)))
    iv, feasible = C.box_vertices(ctx, *box)
    assert feasible is not None
    assert C.segment_credit(ctx, iv, ctx.segments[0], feasible) == 1


# ----------------------------------------------------------------- joint credit (concave sum)
def _collinear_pair_ctx(rho):
    """Two unit segments A = [3/5, 8/5] x {7/10} and B = [8/5, 13/5] x {7/10}: a square centred near
    (8/5, 7/10) moved sideways loses length on one and gains it on the other; the chord of the
    whole line through the square has length 1/cos(theta) >= 1."""
    L = Q3.parse(L2)
    y = "7/10"
    segs = [(("3/5", y), ("8/5", y), rho), (("8/5", y), ("13/5", y), rho)]
    return C.Context(L, [], {"segments": segs})


JOINT_BOX = (F(8, 5) - F(1, 32), F(8, 5) + F(1, 32), F(7, 10) - F(1, 64), F(7, 10) + F(1, 64),
             Q3(0), Q3(F(1, 64)))


def test_joint_credit_needed():
    ctx = _collinear_pair_ctx("21/20")
    iv, feasible = C.box_vertices(ctx, *JOINT_BOX)
    assert feasible is not None
    # per-segment credits: each about 1/2 - 1/32, so the sum of minima is below 1
    old = [C.segment_credit(ctx, iv, sg, feasible) for sg in ctx.segments]
    assert all(o > 0 for o in old)
    assert sum(sg.rho * o for sg, o in zip(ctx.segments, old)) < 1
    # the joint bound proves min over vertices of the sum, which is ~ 21/20 * 1
    fverts, fE = C.float_vertices(iv, feasible)
    J = C.joint_segment_credit(ctx, iv, feasible, fverts, fE, [0, 1], dict(enumerate(old)), 0.0)
    assert J >= 1
    assert C.certify_box(ctx, *JOINT_BOX) == "COVER"
    # soundness against sampling: J / rho is at most the sampled minimum of the total length
    rng = random.Random(7)
    x0, x1, y0, y1, ua, ub = [float(v) for v in JOINT_BOX]
    mn = float("inf")
    for _ in range(3000):
        cx, cy, th = rng.uniform(x0, x1), rng.uniform(y0, y1), 2 * math.atan(rng.uniform(ua, ub))
        if fl_admissible(float(ctx.L), cx, cy, th):
            mn = min(mn, sum(fl_capture_length(*sg.fp, *sg.fd, cx, cy, th) for sg in ctx.segments))
    assert float(J) / 1.05 <= mn + 1e-12


def test_joint_credit_insufficient_density():
    """With rho = 19/20 each, the total capture is ~0.95 < 1: no COVER."""
    ctx = _collinear_pair_ctx("19/20")
    assert C.certify_box(ctx, *JOINT_BOX) is None


def test_seg_targets_ladder():
    t = C.seg_targets(0.99981)
    assert t[0] < F(99981, 100000)        # no snap: no fraction with denominator <= 1000 is within 1e-9
    assert F(1) not in t
    vals = [float(v) for v in t]
    for eps in (1e-6, 1e-5, 1e-4, 1e-3, 1e-2):
        assert any(abs(v - (0.99981 - eps)) < 2 ** -19 for v in vals)
    assert abs(vals[-1] - (0.99981 - 1e-6) / 2) < 2 ** -19
    assert C.seg_targets(1.0)[0] == 1
    assert C.seg_targets(0.5, F(1, 2)) == []
