"""Write the n = 4 certificate of the form used in this repository.

    python tools/make_cert.py                      # L = v4, prints certificates/n4/n4_cert.json byte for byte
    python tools/make_cert.py --L 9651/5000        # a rational L (no wedges needed below v4)

Points (weights 1/2 each, total 7/2):
    the D2-orbit of the corner (1, L-1):  (1, L-1), (2L-1, L-1), (1, 1), (2L-1, 1)
    the centre (L, L/2)
    (L, L/2 + a), (L, L/2 - a)  with a = 2286/10000
Wedges (pairs: corner point, centre): (0,4), (1,4), (2,4), (3,4).
"""
import argparse, json, os, sys
from fractions import Fraction as F
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "checker"))
from q3 import Q3, ALPHA  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--L", default="alpha", help='"alpha" (= v4) or a rational, or "alpha+p/q"')
ap.add_argument("--no-wedges", action="store_true")
ap.add_argument("--out", default="-")
a = ap.parse_args()
if a.L == "alpha":
    L = ALPHA
elif a.L.startswith("alpha+"):
    L = ALPHA + F(a.L[len("alpha+"):])
else:
    L = Q3(F(a.L))
off, h = F(2286, 10000), F(1, 2)
pts = [(Q3(1), L - 1), (2 * L - 1, L - 1), (Q3(1), Q3(1)), (2 * L - 1, Q3(1)), (L, L / 2), (L, L / 2 + off), (L, L / 2 - off)]
cert = {"L": str(L), "symmetry": "D2", "points": [{"x": str(x), "y": str(y), "w": str(h)} for x, y in pts]}
if not a.no_wedges and not L.is_rational():
    cert["wedges"] = [[0, 4], [1, 4], [2, 4], [3, 4]]
s = json.dumps(cert)
if a.out == "-":
    sys.stdout.write(s)
else:
    open(a.out, "w").write(s)
