import json
import os
import random
import time
from fractions import Fraction as F

import pytest

import check as C
from poly import peval
from q3 import Q3, SQRT3

HERE = os.path.dirname(os.path.abspath(__file__))
EXAMPLE = os.path.join(os.path.dirname(HERE), "examples", "n2_centroid.json")

L2 = "2+2/3*sqrt3"


def centroid_cert(L: str, sym: str, dx="0"):
    Lq = Q3.parse(L)
    gx = Lq * F(1, 2) + Q3.parse(dx)
    gy = Lq * SQRT3 / 6
    return {"L": L, "symmetry": sym, "points": [{"x": str(gx), "y": str(gy), "w": "1"}]}


def run(cert, **kw):
    t = time.time()
    s = C.check(cert, **kw)
    s["_wall"] = time.time() - t
    return s


# ----------------------------------------------------------------- setup checks
def test_example_file_is_centroid():
    with open(EXAMPLE) as f:
        data = json.load(f)
    assert data == centroid_cert(L2, "D3") or (
        Q3.parse(data["points"][0]["x"]) == Q3.parse(centroid_cert(L2, "D3")["points"][0]["x"])
        and Q3.parse(data["points"][0]["y"]) == Q3.parse(centroid_cert(L2, "D3")["points"][0]["y"])
    )


def test_U_bound():
    assert C.check_U(F(1, 7))
    assert C.check_U(F(132, 1000))          # tan(pi/24) = 0.131652...
    assert not C.check_U(F(131, 1000))
    assert not C.check_U(F(1, 8))


def test_d3_invariance():
    L = Q3.parse(L2)
    ok = C.load_certificate(centroid_cert(L2, "D3"))[3]
    assert C.check_d3_invariant(L, ok)
    bad = C.load_certificate(centroid_cert(L2, "D3", dx="1/50"))[3]
    assert not C.check_d3_invariant(L, bad)
    s = C.check(centroid_cert(L2, "D3", dx="1/50"))
    assert s["status"] == "failed"


def test_vertex_formula_matches_background():
    """At theta = 0 the corner V01 of the admissible-centre triangle matches the closed form."""
    L = Q3.parse(L2)
    ctx = C.Context(L, C.load_certificate(centroid_cert(L2, "D3"))[3], {})
    iv = ctx.interval(Q3(0), Q3(F(1, 7)))
    kept = iv["adm_kept"]
    assert len(kept) == 3                    # one sigma per side after exact dominance
    r = L / (2 * SQRT3)
    h0 = Q3(F(1, 2))
    h1 = (SQRT3 / 2 + F(1, 2)) / 2
    a0, a1 = r - h0, r - h1
    G = (L / 2, L * SQRT3 / 6)
    V01 = (G[0] + (2 * a1 + a0) / SQRT3, G[1] - a0)
    found = False
    for i in kept:
        for j in kept:
            li, lj = ctx.adm[i], ctx.adm[j]
            if li.tag[1] == 0 and lj.tag[1] == 1:
                pr = C.Pair(ctx, li, lj)
                X, Y = peval(pr.X, Q3(0)), peval(pr.Y, Q3(0))   # D(0) = 1
                assert (X, Y) == V01
                assert (X - G[0]) == Q3(F(1, 2))                  # tight contact V01 . e1 = 1/2
                found = True
    assert found


# ----------------------------------------------------------------- acceptance
def test_n2_d3_verified():
    s = run(centroid_cert(L2, "D3"))
    assert s["status"] == "verified", s
    assert s["uncertified"] == 0
    print("n2 D3:", s["nodes"], "nodes", round(s["_wall"], 3), "s")


def test_n2_none_verified():
    s = run(centroid_cert(L2, "none"))
    assert s["status"] == "verified", s
    print("n2 none:", s["nodes"], "nodes", round(s["_wall"], 3), "s")


def test_n2_example_file_cli(capsys):
    assert C.main([EXAMPLE, "--n", "2", "--root", "2"]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["status"] == "verified" and out["total_weight_lt_n"] is True


def test_n2_parallel_jobs():
    s = run(centroid_cert(L2, "none"), jobs=2)
    assert s["status"] == "verified"


def test_smaller_L_verified():
    s = run(centroid_cert("199/100+2/3*sqrt3", "D3"))
    assert s["status"] == "verified"


# ----------------------------------------------------------------- negative
@pytest.mark.parametrize("sym", ["D3", "none"])
def test_larger_L_not_verified(sym):
    s = run(centroid_cert("201/100+2/3*sqrt3", sym), max_depth=12)
    assert s["status"] == "failed"
    assert s["uncertified"] > 0 and s["max_depth"] == 12


def test_larger_L_really_has_avoiding_square():
    """Independent witness that the negative case is genuinely negative."""
    L = Q3.parse("201/100+2/3*sqrt3")
    G = (L / 2, L * SQRT3 / 6)
    c = (Q3(F(431, 400)), Q3(F(1, 2)))       # theta = 0, bottom-left corner square
    assert admissible(L, c, F(1), F(0))
    assert not contains(c, F(1), F(0), G)


def test_shifted_point_not_verified():
    s = run(centroid_cert(L2, "none", dx="1/50"), max_depth=12)
    assert s["status"] == "failed"
    assert s["uncertified"] > 0


# ----------------------------------------------------------------- random soundness
def square_vertices(c, co, si):
    out = []
    for sx in (F(1, 2), F(-1, 2)):
        for sy in (F(1, 2), F(-1, 2)):
            out.append((c[0] + co * sx - si * sy, c[1] + si * sx + co * sy))
    return out


def admissible(L, c, co, si):
    """Independent exact test: all 4 vertices in the closed triangle (via edge cross products)."""
    A, B, T = (Q3(0), Q3(0)), (L, Q3(0)), (L / 2, L * SQRT3 / 2)
    for v in square_vertices(c, co, si):
        for P0, P1 in ((A, B), (B, T), (T, A)):     # counter-clockwise: inside is left
            cross = (P1[0] - P0[0]) * (v[1] - P0[1]) - (P1[1] - P0[1]) * (v[0] - P0[0])
            if cross < 0:
                return False
    return True


def contains(c, co, si, p):
    dx, dy = p[0] - c[0], p[1] - c[1]
    return abs_le(dx * co + dy * si) and abs_le(-dx * si + dy * co)


def abs_le(v):
    return Q3(F(-1, 2)) <= v <= Q3(F(1, 2))


def test_random_poses_capture_verified_certificate():
    cert = centroid_cert(L2, "none")
    assert C.check(cert)["status"] == "verified"
    _, L, _, pts = C.load_certificate(cert)[:4]
    rng = random.Random(12345)
    gx, gy = float(L) / 2, float(L) * 3 ** 0.5 / 6
    hits = 0
    tries = 0
    while hits < 300 and tries < 20000:
        tries += 1
        u = F(rng.randint(0, 2000), 2000)
        co, si = (1 - u * u) / (1 + u * u), 2 * u / (1 + u * u)
        c = (Q3(F(round((gx + rng.uniform(-0.7, 0.7)) * 10**6), 10**6)),
             Q3(F(round((gy + rng.uniform(-0.7, 0.7)) * 10**6), 10**6)))
        if not admissible(L, c, co, si):
            continue
        hits += 1
        weight = sum((w for x, y, w in pts if contains(c, co, si, (x, y))), F(0))
        assert weight >= 1, (c, u)
    assert hits >= 100


# ---------------------------------------------------------------- Lemma P (chord pairs)
EX = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "examples")


def test_pair_distance_must_be_one():
    cert = json.load(open(os.path.join(EX, "n4_cert.json")))
    cert = dict(cert, points=[dict(p) for p in cert["points"]])
    cert["points"][2]["y"] = cert["points"][2]["y"] + "+1/100"
    with pytest.raises(C.CertError):
        C.load_certificate(cert)


def test_n4_endpoint_with_pairs_verifies():
    s = C.check(os.path.join(EX, "n4_cert.json"), max_depth=32, jobs=2, n=4)
    assert s["status"] == "verified" and s["total_weight_lt_n"]


def test_n4_without_pairs_does_not_verify_quickly():
    cert = json.load(open(os.path.join(EX, "n4_cert.json")))
    cert.pop("pairs")
    s = C.check(cert, max_depth=14, jobs=2, n=4)
    assert s["status"] == "failed"


def test_n4_pairs_negative_Lplus():
    s = C.check(os.path.join(EX, "neg_n4_Lplus.json"), max_depth=14, jobs=2, n=4)
    assert s["status"] == "failed"


def test_n3_endpoint_verifies():
    s = C.check(os.path.join(EX, "n3_cert.json"), max_depth=44, jobs=2, n=3)
    assert s["status"] == "verified" and s["total_weight_lt_n"]


def test_n3_negative_Lplus():
    s = C.check(os.path.join(EX, "neg_n3_Lplus.json"), max_depth=12, jobs=2, n=3)
    assert s["status"] == "failed"
