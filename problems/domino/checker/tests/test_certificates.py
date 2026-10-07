"""End-to-end: a certificate that must verify and one that must fail."""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
from check import check  # noqa: E402

UB = ("K[-21/37;-11/37;15/37]",)


def test_n3_half():
    cert = {"L": "3/2", "symmetry": "D2",
            "points": [{"x": "1", "y": "3/4", "w": "1"}, {"x": "2", "y": "3/4", "w": "1"}],
            "pairs": [[0, 1]]}
    s = check(cert, max_depth=30, n=3)
    assert s["status"] == "verified" and s["total_weight_lt_n"]


def test_n4_v4_verifies():
    s = check(os.path.join(HERE, "..", "..", "certificates", "n4", "n4_cert.json"),
              max_depth=30, u_breaks=UB, n=4, jobs=2)
    assert s["status"] == "verified" and s["total_weight"] == "7/2" and s["total_weight_lt_n"]


def test_control_above_v4_fails():
    s = check(os.path.join(HERE, "..", "..", "controls", "control_v4_plus_1e-6.json"),
              max_depth=30, u_breaks=UB, n=4, jobs=2)
    assert s["status"] == "failed" and s["uncertified"] > 0
