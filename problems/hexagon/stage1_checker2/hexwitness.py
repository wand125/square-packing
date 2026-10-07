#!/usr/bin/env python3
"""Turn the failed boxes of a hexcheck run into explicit, exactly checked poses.

For each failed box, grid poses (rational u, centre in Q(sqrt3)) are tried.  A pose is reported if
it is admissible (all four square corners in the closed hexagon) and its captured weight is < 1,
both decided exactly.  If the pose's representative lies in no excused box, it is a counterexample
to the claim.

    python hexwitness.py cert.json run_summary.json [--per-box 5]
"""
import argparse
import json
import sys

from gmpy2 import mpq

from hexcheck import load, Hex, HALF
from q3 import Q3


def pose_ok(h, cx, cy, u):
    uq = Q3(u)
    D = 1 + uq * uq
    ct, st = (1 - uq * uq) / D, (2 * uq) / D
    for sx in (-HALF, HALF):
        for sy in (-HALF, HALF):
            x = cx + ct * sx - st * sy
            y = cy + st * sx + ct * sy
            for (a, b) in h.sides:
                if (a[0] * x + a[1] * y + b).sign() < 0:
                    return False, ct, st
    return True, ct, st


def weight(h, cx, cy, ct, st):
    w = mpq(0)
    for px, py, pw in h.pts:
        dx, dy = px - cx, py - cy
        a = dx * ct + dy * st
        b = -dx * st + dy * ct
        if (HALF - a).sign() >= 0 and (HALF + a).sign() >= 0 and (HALF - b).sign() >= 0 and (HALF + b).sign() >= 0:
            w += pw
    return w


def excused(h, cx, cy, u):
    for e in h.exc:
        if (Q3(e[0]) - cx).sign() <= 0 and (cx - Q3(e[1])).sign() <= 0 and \
           (Q3(e[2]) - cy).sign() <= 0 and (cy - Q3(e[3])).sign() <= 0 and e[4] <= u <= e[5]:
            return True
    return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('cert')
    ap.add_argument('summary')
    ap.add_argument('--grid', type=int, default=4)
    a = ap.parse_args()
    c, L, pts, exc, sha = load(a.cert)
    h = Hex(L, pts, exc)
    s = json.load(open(a.summary))
    found = []
    for fb in s['failed_boxes']:
        box = [Q3.parse(v) for v in fb]
        x0, x1, y0, y1, u0, u1 = box
        g = a.grid
        hit = None
        for i in range(g + 1):
            for j in range(g + 1):
                for k in range(g + 1):
                    cx = x0 + (x1 - x0) * mpq(i, g)
                    cy = y0 + (y1 - y0) * mpq(j, g)
                    u = u0.a + (u1.a - u0.a) * mpq(k, g)
                    ok, ct, st = pose_ok(h, cx, cy, u)
                    if not ok:
                        continue
                    w = weight(h, cx, cy, ct, st)
                    if w < 1:
                        hit = dict(centre=[str(cx), str(cy)], u=str(u), captured_weight=str(w),
                                   admissible=True, excused=excused(h, cx, cy, u))
                        break
                if hit:
                    break
            if hit:
                break
        if hit:
            found.append(hit)
    print(json.dumps(dict(certificate=a.cert, sha256=sha, failed_boxes_tried=len(s['failed_boxes']),
                          witnesses=len(found), examples=found[:5]), indent=2))
    return 0


if __name__ == '__main__':
    sys.exit(main())
