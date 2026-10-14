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

    def bv(ctx, x0, x1, y0, y1, ua, ub, open_side=None):
        iv, f = orig(ctx, x0, x1, y0, y1, ua, ub, open_side)
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
