"""Broken-copy test for check_d6.py: each mutation of a valid cap or strip certificate must be rejected.
usage: python3 -I mutate_d6.py cap|strip certificate.json
The checker is imported from this directory and run in-process on each mutated certificate."""
import copy, json, os, sys, importlib.util
from fractions import Fraction as Fr

here = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("check_d6", os.path.join(here, "check_d6.py"))
C = importlib.util.module_from_spec(spec); spec.loader.exec_module(C)

kind, path = sys.argv[1], sys.argv[2]
cert = json.load(open(path)); recs = cert["records"]
issplit = (lambda x: x is not None) if kind == "cap" else (lambda x: x[0] == "split")
wkey = "witnesses" if kind == "cap" else "spectral_witnesses"
k = next(i for i, x in enumerate(recs) if issplit(x))

def with_records(change):
    def f(c):
        c["records"] = list(recs); change(c["records"])
    return f

def r_mid(R):
    r = list(R[k]); r[-1] += 1; R[k] = r
def r_leaf(R):
    R[k] = None if kind == "cap" else ["leaf", 0]
def r_drop(R):
    R.pop()
def v_init(c):
    c["vertices"] = list(cert["vertices"]); v = list(c["vertices"][1]); v[0], v[1] = "33/50", "17/50"; c["vertices"][1] = v
def s_init(c):
    c["initial"] = [list(s) for s in cert["initial"]]; c["initial"][0] = [0, 2, 4, 6, 8, 3]
def w_half(c):
    c[wkey] = [[[str(Fr(s) / 2) for s in row] for row in W] for W in cert[wkey]]
def t_up(c):
    c["tangents"] = copy.deepcopy(cert["tangents"]); t = c["tangents"][0]
    t["coeff"] = [str(Fr(x) * Fr(1001, 1000)) for x in t["coeff"]]
def f_up(c):
    c["facets"] = copy.deepcopy(cert["facets"]); c["facets"][0][4] = str(Fr(c["facets"][0][4]) + 1)

tests = [("wrong midpoint index", with_records(r_mid)), ("leaf placed too early", with_records(r_leaf)),
         ("missing last record", with_records(r_drop)), ("wrong initial vertex", v_init),
         ("wrong initial simplex", s_init), ("all spectral witnesses halved", w_half)]
if kind == "strip":
    tests += [("tangent coefficient increased by 0.1%", t_up), ("facet violating a support inequality", f_up)]

import io, contextlib
bad = 0
for name, mut in tests:
    c = dict(cert); mut(c)
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            ch = C.Checker(kind, c); ch.check_geometry(); ch.check_tangents(); ch.replay()
        print(f"{name}: ACCEPTED (bad)"); bad += 1
    except AssertionError as e:
        print(f"{name}: rejected ({str(e)[:80] or 'assertion'})")
print(f"{len(tests) - bad} of {len(tests)} broken copies rejected")
sys.exit(1 if bad else 0)
