#!/usr/bin/env python3
"""Write the packing certificates (upper bounds) of this repository.

Each packing is written as exact coordinates in the format of FORMAT.md. The files are data;
this script only records how they were made. Run from the repository root:

    python3 tools/packing_check/make_packings.py          # write all files
    python3 tools/packing_check/make_packings.py --check  # compare with the files on disk
"""

import json
import os
import sys

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))

SQRT2 = {"generator": "sqrt2", "minpoly": ["-2", "0", "1"], "interval": ["1", "2"]}
SQRT3 = {"generator": "sqrt3", "minpoly": ["-3", "0", "1"], "interval": ["1", "2"]}
FRIEDMAN = "Erich Friedman, Packing Center"


def axis_square(x, y):
    return {"axis": [x, y]}


def cert(problem, n, container, squares, field=None, defs=None, source=None, side_claim=None,
         note=None):
    d = {"format": "packing-certificate/1", "problem": problem, "n": n}
    if field:
        d["field"] = field
    if defs:
        d["defs"] = defs
    d["container"] = container
    if side_claim:
        d["side_claim"] = side_claim
    if note:
        d["packing"] = note
    if source:
        d["source"] = source
    d["squares"] = squares
    return d


# ---------------------------------------------------------------- right isosceles triangle


def right_isosceles(n):
    """Leg frame T = conv{(0,0), (L,0), (0,L)}."""
    if n in (3, 6, 10, 15):
        L = {3: 3, 6: 4, 10: 5, 15: 6}[n]
        sq = [axis_square(str(i), str(j)) for j in range(L) for i in range(L) if i + j <= L - 2]
        assert len(sq) == n
        cont = {"kind": "right_isosceles_triangle", "side": str(L),
                "vertices": [["0", "0"], [str(L), "0"], ["0", str(L)]]}
        rows = ", ".join(str(L - 1 - j) for j in range(L - 1))
        return cert(f"squares in a right isosceles triangle, n = {n}", n, cont, sq,
                    note=f"axis-parallel staircase with rows {rows} in the corner of the right angle",
                    source=f"{FRIEDMAN}, \"Squares in Right Isosceles Triangles\"")
    # n = 2, 4: squares standing on the hypotenuse. M = midpoint of the hypotenuse,
    # u = unit vector along it, w = unit inward normal; point (a, b) = M + a u + b w.
    Lx = {2: "2*sqrt2", 4: "5*sqrt2/2"}[n]
    defs = {"L": Lx, "h": "sqrt2/2"}

    def P(a, b):
        return [f"L/2 + ({a})*h - ({b})*h", f"L/2 - ({a})*h - ({b})*h"]

    def stand(a0, b0):  # square with base [a0, a0+1] at height b0, CCW in the leg frame
        return {"vertices": [P(a0, b0), P(a0, b0 + 1), P(f"{a0}+1", b0 + 1), P(f"{a0}+1", b0)]}

    if n == 2:
        sq = [stand("-1", 0), stand("0", 0)]
        note = "the hypotenuse (length 4) as base, two squares side by side on it"
    else:
        sq = [stand("-3/2", 0), stand("-1/2", 0), stand("1/2", 0), stand("-1/2", 1)]
        note = ("the hypotenuse (length 5) as base, three squares side by side on it "
                "and one on the middle one")
    cont = {"kind": "right_isosceles_triangle", "side": "L",
            "vertices": [["0", "0"], ["L", "0"], ["0", "L"]]}
    return cert(f"squares in a right isosceles triangle, n = {n}", n, cont, sq, field=SQRT2,
                defs=defs, note=note,
                source=f"{FRIEDMAN}, \"Squares in Right Isosceles Triangles\"")


# ---------------------------------------------------------------- regular hexagon, n = 3


def hexagon3():
    defs = {"v": "(1+sqrt3)/2", "h": "v*sqrt3/2"}
    cont = {"kind": "regular_hexagon", "side": "v",
            "vertices": [["-v/2", "-h"], ["v/2", "-h"], ["v", "0"], ["v/2", "h"],
                         ["-v/2", "h"], ["-v", "0"]]}
    B = [("-v/2", "-h"), ("-v/2+1", "-h"), ("-v/2+1", "-h+1"), ("-v/2", "-h+1")]

    def rot(p, k):  # rotation by 2*pi*k/3 about the centre
        x, y = p
        for _ in range(k):
            x, y = f"(-1/2)*({x}) - (sqrt3/2)*({y})", f"(sqrt3/2)*({x}) + (-1/2)*({y})"
        return [x, y]

    sq = [{"vertices": [rot(p, k) for p in B]} for k in range(3)]
    return cert("squares in a regular hexagon, n = 3", 3, cont, sq, field=SQRT3, defs=defs,
                note=("pinwheel: B = [-v/2, -v/2+1] x [-h, -h+1] on the bottom side with its "
                      "lower-left corner at a vertex, and its rotations by 2pi/3 and 4pi/3; "
                      "hexagon centred at 0 with a flat bottom, h = apothem"),
                source=f"{FRIEDMAN}, \"Squares in Hexagons\" (Morandi)")


# ---------------------------------------------------------------- 1 x 2 rectangle, n = 4


def domino4():
    field = {"generator": "t", "minpoly": ["1", "-1", "-5", "1"], "interval": ["0", "1"]}
    defs = {"c": "(1-t**2)/(1+t**2)", "s": "2*t/(1+t**2)",
            "v": "2*(s+c)*(1+s)/((s+c)**2+s**2)", "bx": "2*c"}
    cont = {"kind": "rectangle", "width": "2*v", "height": "v",
            "vertices": [["0", "0"], ["2*v", "0"], ["2*v", "v"], ["0", "v"]]}
    Lsq = [["bx", "0"], ["bx+s", "c"], ["bx+s-c", "s+c"], ["bx-c", "s"]]
    Usq = [[f"2*v-({x})", f"v-({y})"] for x, y in Lsq]
    sq = [axis_square("0", "v-1"), axis_square("2*v-1", "0"),
          {"vertices": Lsq}, {"vertices": Usq}]
    return cert("squares in a 1 x 2 rectangle, n = 4", 4, cont, sq, field=field, defs=defs,
                side_claim={"of": "height", "minpoly": ["-4", "-32", "8", "5"],
                            "largest_real_root": True, "below": "193/100"},
                note=("t = tan(beta/2) is the root of t^3 - 5t^2 - t + 1 in (0, 1), c = cos beta, "
                      "s = sin beta; A = [0,1] x [v-1,v], B = [2v-1,2v] x [0,1], L has vertices "
                      "b, b+(s,c), b+(s-c,s+c), b+(-c,s) with b = (2c,0), U = L reflected "
                      "through the centre (v, v/2)"),
                source=f"{FRIEDMAN}, \"Squares in Dominoes\" (Evert Stenlund, 2010)")


# ---------------------------------------------------------------- the square, k x k grid


def grid(n, k):
    sq = [axis_square(str(i), str(j)) for j in range(k) for i in range(k)][:n]
    cont = {"kind": "square", "side": str(k),
            "vertices": [["0", "0"], [str(k), "0"], [str(k), str(k)], ["0", str(k)]]}
    return cert(f"squares in a square, n = {n}", n, cont, sq,
                note=f"the first {n} cells of the {k} x {k} unit grid, row by row",
                source="the trivial grid packing")


def targets():
    out = {}
    for n in (2, 3, 4, 6, 10, 15):
        out[f"problems/right-isosceles/certificates/n{n}/packing.json"] = right_isosceles(n)
    out["problems/hexagon/n3/packing.json"] = hexagon3()
    out["problems/domino/certificates/n4/packing.json"] = domino4()
    sl = "problems/square-lower-bounds"
    for n in (22, 23, 24, 25):
        out[f"{sl}/point_n21_L5/packing_n{n}.json"] = grid(n, 5)
    out[f"{sl}/point_n45_L7/packing_n45.json"] = grid(45, 7)
    out[f"{sl}/point_n61_L8/packing_n61.json"] = grid(61, 8)
    out[f"{sl}/certificates/k2m4_n77_L9/packing_n77.json"] = grid(77, 9)
    out[f"{sl}/certificates/k2m4_n77_L9/packing_n78.json"] = grid(78, 9)
    return out


def dump(d):
    return json.dumps(d, indent=1) + "\n"


def main(argv):
    bad = 0
    for rel, d in targets().items():
        path = os.path.join(ROOT, rel)
        if "--check" in argv:
            with open(path) as f:
                same = f.read() == dump(d)
            print(("same     " if same else "DIFFERS  ") + rel)
            bad += not same
        else:
            with open(path, "w") as f:
                f.write(dump(d))
            print("wrote " + rel)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
