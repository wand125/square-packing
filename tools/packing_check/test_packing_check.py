#!/usr/bin/env python3
"""Negative and positive controls for both packing checkers.

Every packing in make_packings.py must be VALID for both checkers; every mutation below must be
INVALID for both. Run from anywhere: python3 tools/packing_check/test_packing_check.py
"""

import copy
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import check_packing  # noqa: E402
import check_packing2  # noqa: E402
import make_packings  # noqa: E402

EPS = "1/1000000000000"


def both(cert):
    return check_packing.check(cert)["result"], check_packing2.run(cert)["result"]


def mutations(T):
    hexa = T["problems/hexagon/n3/packing.json"]
    dom = T["problems/domino/certificates/n4/packing.json"]
    tri4 = T["problems/right-isosceles/certificates/n4/packing.json"]
    g25 = T["problems/square-lower-bounds/point_n21_L5/packing_n25.json"]
    out = {}

    m = copy.deepcopy(dom)  # shrink the rectangle by 10^-12 (container and squares follow v)
    m["defs"]["v"] = f"2*(s+c)*(1+s)/((s+c)**2+s**2) - {EPS}"
    out["domino: v - 1e-12"] = m

    m = copy.deepcopy(dom)  # tilt L and U by a tiny change of beta, same container
    u = f"(t+{EPS})"
    m["defs"] = {"c0": "(1-t**2)/(1+t**2)", "s0": "2*t/(1+t**2)",
                 "v": "2*(s0+c0)*(1+s0)/((s0+c0)**2+s0**2)",
                 "c": f"(1-{u}**2)/(1+{u}**2)", "s": f"2*{u}/(1+{u}**2)", "bx": "2*c"}
    out["domino: beta perturbed, v kept"] = m

    m = copy.deepcopy(dom)  # side claim with a polynomial that the side does not satisfy
    m["side_claim"]["minpoly"] = ["-4", "-32", "8", "6"]
    out["domino: wrong minimal polynomial"] = m

    m = copy.deepcopy(hexa)  # smaller hexagon
    m["defs"]["v"] = f"(1+sqrt3)/2 - {EPS}"
    out["hexagon: v - 1e-12"] = m

    m = copy.deepcopy(hexa)  # container claims side v but is drawn with side v + 1
    m["container"]["side"] = "v+1"
    out["hexagon: wrong side"] = m

    m = copy.deepcopy(hexa)  # only a triangle given as the hexagon
    m["container"]["vertices"] = m["container"]["vertices"][::2]
    out["hexagon: three vertices"] = m

    m = copy.deepcopy(tri4)  # legs 5/sqrt2 - 1e-12
    m["defs"]["L"] = f"5*sqrt2/2 - {EPS}"
    out["right isosceles n4: leg - 1e-12"] = m

    m = copy.deepcopy(tri4)  # top square moved down by 1e-12 into the middle one
    for p in m["squares"][3]["vertices"]:
        p[1] = p[1] + f" - {EPS}"
    out["right isosceles n4: top square sinks 1e-12"] = m

    m = copy.deepcopy(g25)  # one square shifted right by 1e-12
    m["squares"][7] = {"axis": ["2+" + EPS, "1"]}
    out["grid 25: shifted square"] = m

    m = copy.deepcopy(g25)  # two copies of the same square
    m["squares"][24] = m["squares"][23]
    out["grid 25: duplicate square"] = m

    m = copy.deepcopy(g25)  # not a unit square
    m["squares"][0] = {"vertices": [["0", "0"], ["1", "0"], ["1", "1+" + EPS], ["0", "1"]]}
    out["grid 25: non-square"] = m

    m = copy.deepcopy(g25)  # a 45-degree square in the corner overlapping its neighbours
    m["field"] = make_packings.SQRT2
    m["squares"][0] = {"vertices": [["sqrt2/2", "0"], ["sqrt2", "sqrt2/2"],
                                    ["sqrt2/2", "sqrt2"], ["0", "sqrt2/2"]]}
    out["grid 25: tilted square"] = m

    m = copy.deepcopy(g25)  # n larger than the number of squares
    m["n"] = 26
    out["grid 25: n = 26"] = m

    m = copy.deepcopy(g25)  # clockwise container
    m["container"]["vertices"] = m["container"]["vertices"][::-1]
    out["grid 25: clockwise container"] = m
    return out


def main():
    T = make_packings.targets()
    fails = 0
    for name, cert in T.items():
        r = both(cert)
        ok = r == ("VALID", "VALID")
        fails += not ok
        print(("ok    " if ok else "FAIL  ") + f"{r}  {name}")
    for name, cert in mutations(T).items():
        r = both(cert)
        ok = r == ("INVALID", "INVALID")
        fails += not ok
        print(("ok    " if ok else "FAIL  ") + f"{r}  {name}")
    print("all controls passed" if not fails else f"{fails} controls FAILED")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
