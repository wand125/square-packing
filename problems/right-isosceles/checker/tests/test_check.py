"""Acceptance tests for the right isosceles container T_L = conv{(0,0), (L,0), (0,L)}."""
from fractions import Fraction

from check import CertError, check

ONE_PT = [{"x": "1/2", "y": "1/2", "w": "1"}]
N3 = [{"x": "3/4", "y": "1", "w": "1/2"}, {"x": "1", "y": "3/4", "w": "1/2"},
      {"x": "3/4", "y": "5/4", "w": "1/2"}, {"x": "5/4", "y": "3/4", "w": "1/2"}]


def run(L, pts, sym, depth=30):
    return check({"L": L, "symmetry": sym, "points": pts}, max_depth=depth)


def test_n1_point_in_every_square():
    # L = 2: the only unit square is [0,1]^2 (s(1) = 2), so it contains (1/2, 1/2)
    assert run("2", ONE_PT, "D1")["status"] == "verified"
    assert run("2", ONE_PT, "none")["status"] == "verified"


def test_n1_negative():
    assert run("11/4", ONE_PT, "D1", depth=10)["status"] == "failed"


def test_n3_certificate():
    s = check({"L": "3", "symmetry": "D1", "points": N3}, n=3)
    assert s["status"] == "verified" and s["total_weight_lt_n"]
    assert run("3", N3, "none")["status"] == "verified"


def test_n3_negative():
    assert run("301/100", N3, "D1", depth=16)["status"] == "failed"


def test_not_symmetric_rejected():
    s = run("3", N3[:3], "D1")
    assert s["status"] == "failed" and "D1-invariant" in s["reason"]


# Segments of any nonzero length: rho is the mass of the whole segment, a square captures
# rho * |Q cap pq| / |pq|.
def seg(px, py, qx, qy, rho):
    return {"p": {"x": px, "y": py}, "q": {"x": qx, "y": qy}, "rho": rho}


SHORT_45 = [seg("1/4", "1/4", "1/2", "1/2", "1")]          # length sqrt2/4, on the diagonal (D1-invariant)
SHORT_PAIR = [seg("1/4", "1/2", "1/2", "1/2", "1/2"), seg("1/2", "1/4", "1/2", "1/2", "1/2")]


def run_seg(L, segs, sym, depth=30, n=None):
    return check({"L": L, "symmetry": sym, "points": [], "segments": segs}, max_depth=depth, n=n)


def test_short_segments_n1():
    s = run_seg("2", SHORT_45, "D1", n=2)
    assert s["status"] == "verified" and s["total_weight"] == "1"
    assert run_seg("2", SHORT_45, "none")["status"] == "verified"
    assert run_seg("2", SHORT_PAIR, "D1")["status"] == "verified"


def test_short_segments_negative():
    assert run_seg("11/4", SHORT_45, "D1", depth=10)["status"] == "failed"
    assert run_seg("11/4", SHORT_PAIR, "D1", depth=10)["status"] == "failed"


def test_zero_length_segment_rejected():
    try:
        run_seg("2", [seg("1/2", "1/2", "1/2", "1/2", "1")], "D1")
    except CertError as e:
        assert "length 0" in str(e)
    else:
        raise AssertionError("zero-length segment accepted")


# Hypotenuse frame: the same triangle with the hypotenuse [0, H] on the x-axis, H = L sqrt2.
# The n = 3 certificate moved by s = (y - x + L)/sqrt2, h = (L - x - y)/sqrt2 (L = 3).
N3_HYP = [{"x": "13/8*sqrt2", "y": "5/8*sqrt2", "w": "1/2"}, {"x": "11/8*sqrt2", "y": "5/8*sqrt2", "w": "1/2"},
          {"x": "7/4*sqrt2", "y": "1/2*sqrt2", "w": "1/2"}, {"x": "5/4*sqrt2", "y": "1/2*sqrt2", "w": "1/2"}]


def test_hyp_frame():
    c = {"L": "3", "frame": "hyp", "symmetry": "D1", "points": N3_HYP}
    s = check(c, n=3)
    assert s["status"] == "verified" and s["frame"] == "hyp"
    assert check({**c, "symmetry": "none"})["status"] == "verified"
    assert check({**c, "symmetry": "none", "L": "301/100"}, max_depth=16)["status"] == "failed"
    # the reflection is (s, h) -> (H - s, h): dropping one point breaks the invariance
    s = check({**c, "points": N3_HYP[:3]})
    assert s["status"] == "failed" and "D1-invariant" in s["reason"]


def test_endpoint_slices():
    # L = 2: the only admissible square is [0,1]^2 at theta = 0, and (1, 1/2) lies on its edge.  The boxes
    # touching u = 0 have admissible poses only at u = 0; --slices certifies them (emptiness on (0, u1] by a
    # Farkas combination, plus the exact slice at u = 0).  Without slices they stay uncertified.
    pts = [{"x": "1", "y": "1/2", "w": "1"}]
    c = {"L": "2", "symmetry": "none", "points": pts}
    s = check(c, max_depth=14, slices=True, bbox="4")
    assert s["status"] == "verified" and s["slice_leaves"] > 0
    assert check(c, max_depth=14, bbox="4")["status"] == "failed"
    assert check({**c, "L": "3"}, max_depth=14, slices=True, bbox="4")["status"] == "failed"


N4_L = "5/2*sqrt2"


def n4_pair(eps):
    a, b = "5/8*sqrt2", "9/8*sqrt2"
    return [{"x": f"{eps}+{a}", "y": f"{-eps}+{b}", "w": "1"}, {"x": f"{-eps}+{b}", "y": f"{eps}+{a}", "w": "1"},
            {"x": "1/2*sqrt2", "y": "1/2*sqrt2", "w": "1"}]


def test_short_chord_pairs():
    # the n = 4 points with the chord pair shortened to 1 - 2 sqrt2 / 10^6, in T_L with L = 5/sqrt2 - 1/100:
    # verified with the pair (Lemma P for |pq| <= 1), failed without it
    cert = {"L": "-1/100+" + N4_L, "symmetry": "D1", "points": n4_pair(Fraction(1, 10**6))}
    assert check({**cert, "pairs": [[0, 1]]}, max_depth=30)["status"] == "verified"
    assert check(cert, max_depth=12)["status"] == "failed"


def test_long_or_zero_chord_pair_rejected():
    for pts in (n4_pair(Fraction(-1, 10**12)),
                [{"x": "1", "y": "1", "w": "1"}, {"x": "1", "y": "1", "w": "1"}]):
        try:
            check({"L": N4_L, "symmetry": "none", "points": pts, "pairs": [[0, 1]]}, max_depth=4)
        except CertError:
            continue
        raise AssertionError("pair accepted")


# Open end of the u-range (10/12, SPEC "Wedged squares at an end of the u-range"): the square [0, 1] x [1, 2] of
# T_3 is wedged at theta = 0 between the side x = 0 and the hypotenuse, so three constraint lines meet at its centre
# at u = 0 and the vertex (side, box face) stays a candidate on every closed u-interval; (3/4, 1) lies on its
# bottom edge.  The root box with that pose at a corner is closed by the open-side cover plus the slice at u = 0.
def _corner_run(pts, depth=30, sym="D1", root=None):
    import hashlib, json, os, tempfile
    cert = {"L": "3", "symmetry": sym, "points": pts}
    h = hashlib.sha256(json.dumps(cert, sort_keys=True).encode()).hexdigest()
    root = root or {"x": ["1/2", "3/4"], "y": ["5/4", "3/2"], "u": ["0", "-1+1*sqrt2"]}
    f = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False)
    json.dump({"certificate_sha256": h, "uncertified": 1, "uncertified_boxes": [root]}, f)
    f.close()
    try:
        return check(cert, max_depth=depth, slices=True, roots_from=f.name)
    finally:
        os.unlink(f.name)


def test_wedged_corner_open_end():
    s = _corner_run(N3)
    assert s["status"] == "verified" and s["open_leaves"] >= 1


def test_wedged_corner_negative():
    # (3/4, 5/4) and its image at weight 1/4: the wedged square captures 3/4 < 1 and must not close
    pts = [dict(p) for p in N3]
    pts[2]["w"] = pts[3]["w"] = "1/4"
    assert _corner_run(pts, depth=16)["status"] == "failed"


def test_wedged_corner_open_end_hi():
    # the upper end of the u-range: symmetry "none" (u in [0, 1]), the D1 image of the wedge, [1, 2] x [0, 1] between
    # the floor and the hypotenuse; near u = 1 the square turns the other way, so the wedge shows at the upper end
    root = {"x": ["5/4", "3/2"], "y": ["1/2", "3/4"], "u": ["3/4", "1"]}
    s = _corner_run(N3, sym="none", root=root)
    assert s["status"] == "verified" and s["open_leaves"] >= 1


def test_open_end_keeps_real_vertices():
    # three lines meet exactly at u = 0 only for the box face y = 3/2: there the open-side test drops the false
    # vertex candidates; with the face moved down by 10^-3 or 10^-7 the candidate (side, face) is a real vertex for
    # small u > 0 and must stay
    import check as C
    rec = []
    orig = C.box_vertices

    def bv(ctx, x0, x1, y0, y1, ua, ub, open_side=None, cone=None):
        iv, f = orig(ctx, x0, x1, y0, y1, ua, ub, open_side, cone)
        if open_side is None:
            rec.append((len(f or []), len(orig(ctx, x0, x1, y0, y1, ua, ub, "lo")[1] or [])))
        return iv, f
    C.box_vertices = bv
    try:
        got = {}
        for y1 in ("3/2", "1499/1000", "14999999/10000000"):
            rec.clear()
            _corner_run(N3, depth=0, root={"x": ["1/2", "3/4"], "y": ["5/4", y1], "u": ["0", "1/1000"]})
            got[y1] = rec[0]
    finally:
        C.box_vertices = orig
    closed, opened = got["3/2"]
    assert opened < closed
    for y1 in ("1499/1000", "14999999/10000000"):
        assert got[y1][0] == got[y1][1]


# Cone leaves (SPEC "Cone leaves"): the wedged hypotenuse crossing of n21_frs3 at (7/8, 41/8), theta = 0.
import os as _os
_N21 = _os.path.join(_os.path.dirname(__file__), "data", "n21_frs3.json")
_CONE_BOX = (Fraction(7, 8), Fraction(15, 16), Fraction(81, 16), Fraction(41, 8))


def _n21_ctx(scale=None):
    import check as C
    from q2 import Q2
    raw, L, sym, pts, pairs, feats, segs = C.load_certificate(_N21)
    if scale is not None:
        pts = [(x, y, w * scale) for x, y, w in pts]
    opts = {"max_depth": 30, "u_scale": 4, "frame_H": None, "u_lo": "0", "u_hi": None, "cone": "1/16",
            "pairs": [(str(p[0]), str(p[1]), str(q[0]), str(q[1])) for p, q in pairs], "features": [], "segments": []}
    C._init_worker(str(L), [(str(x), str(y), str(w)) for x, y, w in pts], opts)
    return C, C._WORKER_CTX, Q2


def test_cone_leaf_wedged_crossing():
    # the box that the plain checker never closes is one cone leaf; the corner is found by crossing_corners
    C, ctx, Q2 = _n21_ctx()
    ub = Q2.parse("-1/4+1/4*sqrt2") * Fraction(1, 16)
    bx = _CONE_BOX + (Q2(0), ub)
    assert (Fraction(7, 8), Fraction(41, 8)) in C.crossing_corners(ctx, *bx[:4])
    assert C.certify_box(ctx, *bx) is None and C.certify_box(ctx, *bx, open_side="lo") is None
    rec = []
    assert C.cone_leaf(ctx, bx, (Fraction(7, 8), Fraction(41, 8)), 4, record=rec) > 0
    # the certified pieces cover the box for u > 0: exact sample poses, each in some piece
    import random
    rnd = random.Random(1)
    for _ in range(300):
        u = Fraction(rnd.randint(1, 10**6), 10**6) * Fraction(1, 400)
        x = Fraction(7, 8) + Fraction(rnd.randint(0, 10**6), 10**6) / 16
        y = Fraction(41, 8) - Fraction(rnd.randint(0, 10**6), 10**6) / 16
        g = u / (1 + u * u)
        a, b = (x - Fraction(7, 8)) / g, (Fraction(41, 8) - y) / g
        assert any(alo <= a and (ahi is None or a <= ahi) and blo <= b and (bhi is None or b <= bhi)
                   and Q2(u) >= pa and Q2(u) <= pb for alo, ahi, blo, bhi, pa, pb in rec)


def test_cone_leaf_negative():
    # weights x 97/100: the exact capture near the corner drops below 1 (1.0211 x 0.97 < 1), the leaf must fail
    C, ctx, Q2 = _n21_ctx(Fraction(97, 100))
    ub = Q2.parse("-1/4+1/4*sqrt2") * Fraction(1, 16)
    bx = _CONE_BOX + (Q2(0), ub)
    old = C.CONE_BUDGET
    C.CONE_BUDGET = 300          # the positive case needs 18 pieces; failing is decided by the budget
    try:
        assert C.cone_leaf(ctx, bx, (Fraction(7, 8), Fraction(41, 8)), 4) == 0
    finally:
        C.CONE_BUDGET = old


# Two-point lemma on ordinary boxes at u = 0 (SPEC "Two-point lemma", 10/18): the square [33/8, 41/8] x [0, 1] of
# n21_frs3 flush with the leg y = 0; R = (41/8, 1/2) or C = (33/8, 1) is inside, with a multiplier 1 - alpha u.
_FLUSH = (Fraction(37, 8), Fraction(1, 2))


def _flush_box(Q2, w, ue):
    X, Y = _FLUSH
    return (X - w, X, Y, Y + w, Q2(0), Q2(ue))


def test_bern_times_u_and_elevate():
    import check as C
    from poly import to_bern, P
    from q2 import Q2
    ua, ub = Q2.parse("1/7"), Q2.parse("-1/4+1/4*sqrt2")
    p = P(Q2(3), Q2(-2), Q2.parse("1/2+sqrt2"), Q2(0), Q2(5))
    up = [Q2(0)] + list(p)
    assert C._bern_times_u(to_bern(p, ua, ub), ua, ub) == to_bern(up, ua, ub, 5)
    assert C._bern_elevate(to_bern(p, ua, ub)) == to_bern(p, ua, ub, 5)


def test_two_point_flush_corner():
    C, ctx, Q2 = _n21_ctx()
    w = Fraction(1, 256)
    for ue in (w, w / 4):
        bx = _flush_box(Q2, w, ue)
        assert C.certify_box(ctx, *bx) == "COVER"
        assert C.certify_box(ctx, *bx, open_side="lo") == "COVER"
    orig = C.two_point_credit
    C.two_point_credit = lambda ctx, fv, fE, pb, B, used, acc, ua, ub: acc
    try:
        assert C.certify_box(ctx, *_flush_box(Q2, w, w)) is None     # Lemma P alone: 0.995
    finally:
        C.two_point_credit = orig


def test_two_point_flush_corner_negative():
    # weights x 98/100: 1.0100 x 0.98 < 1, the box must not be certified
    C, ctx, Q2 = _n21_ctx(Fraction(98, 100))
    w = Fraction(1, 256)
    assert C.certify_box(ctx, *_flush_box(Q2, w, w)) is None
    assert C.certify_box(ctx, *_flush_box(Q2, w, w), open_side="lo") is None
