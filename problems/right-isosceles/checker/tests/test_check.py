"""Acceptance tests for the right isosceles container T_L = conv{(0,0), (L,0), (0,L)}."""
from check import check

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
