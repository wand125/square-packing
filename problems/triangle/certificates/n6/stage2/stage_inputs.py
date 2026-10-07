"""Exact inputs for a localization stage of n = 6 (frame of the stored pinwheel).

A case is 'obstacles:partners' (square labels).  Each obstacle square is known to have a pose with
|c - c0|_inf <= D and |theta - theta0| <= DTH (from the previous stage).  We emit
  * witness points p = c0 + R(theta0) w (exact in Q(sqrt3)), w on the boundary of [-H, H]^2 at spacing
    STEP plus w = 0, and prove exactly (rational bounds) that sqrt2*D + DTH*|w|_2 + |w|_inf < 1/2, so p lies in
    the open obstacle square for every such pose; any other square containing p overlaps it;
  * exclusion boxes (symmetry none, u = tan(theta/2) in [0, 1]) for each partner: x, y in c0 +- D exactly,
    u in an inner rational approximation of tan((theta0 +- DTH)/2), split at theta = 0 = pi/2;
  * float files for lp_exact.py (--obstacle-points, --exclude-poses).
Usage: python stage_inputs.py CASE [D_obstacle DTH_obstacle H STEP D_partner DTH_partner]          -> writes n6/stage2/<tag>.inputs.json + float files
       python stage_inputs.py --finalize CASE lp_cert.json out_cert.json
"""
import json, math, sys
from fractions import Fraction as F
sys.path.insert(0, "checker")
from q3 import Q3
S3 = Q3(0, 1); HALF = F(1, 2)
TRIG = {0: (Q3(1), Q3(0)), 30: (S3 / 2, Q3(HALF)), 60: (Q3(HALF), S3 / 2)}


def q3s(z):
    return f"{z.a}" if z.b == 0 else f"{z.a}{'+' if z.b > 0 else '-'}{abs(z.b)}*sqrt3"


def packing():
    d = json.load(open("certificates/n6/n6_packing.json")); out = []
    for s in d["squares"]:
        V = [(Q3.parse(x), Q3.parse(y)) for x, y in s]
        cx = sum((v[0] for v in V), Q3(0)) * F(1, 4); cy = sum((v[1] for v in V), Q3(0)) * F(1, 4)
        deg = round(math.degrees(math.atan2(float(V[1][1] - V[0][1]), float(V[1][0] - V[0][0])))) % 90
        out.append((cx, cy, deg))
    return out


def rat_up(x, den=10**9):
    return F(math.ceil(x * den) + 1, den)


def rat_dn(x, den=10**9):
    return F(math.floor(x * den) - 1, den)


def sqrt_up(q: F):
    r = rat_up(math.sqrt(float(q)))
    assert r * r >= q
    return r


def ubox(lo_deg, hi_deg):
    """inner rational u-interval(s) for theta in [lo, hi] degrees (may wrap below 0 into [90 - ., 90))."""
    out = []
    def inner(a, b):  # theta in [a, b] within [0, 90]
        ua = F(0) if a <= 0 else rat_up(math.tan(math.radians(a) / 2))
        ub = F(1) if b >= 90 else rat_dn(math.tan(math.radians(b) / 2))
        # exact check of the inner property via float with margin (tan monotone; rat_up/dn add 1e-9 margin)
        if ua < ub:
            out.append((ua, ub))
    if lo_deg < 0:
        inner(0, hi_deg); inner(90 + lo_deg, 90)
    else:
        inner(lo_deg, hi_deg)
    return out


def main():
    if sys.argv[1] == "--finalize":
        case, lpc, outp = sys.argv[2:5]
        tag = tagof(case)
        inp = json.load(open(f"certificates/n6/stage2/{tag}.inputs.json"))
        c = json.load(open(lpc))
        assert c.get("symmetry") == "none"
        c["exclusions"] = inp["exclusions"]; c["obstacle_points"] = inp["obstacle_points"]; c["stage"] = inp["stage"]
        json.dump(c, open(outp, "w"), indent=1)
        print("wrote", outp); return
    case = sys.argv[1]
    D = F(sys.argv[2]) if len(sys.argv) > 2 else F(1, 50)
    DTH = F(sys.argv[3]) if len(sys.argv) > 3 else F(1, 50)
    H = F(sys.argv[4]) if len(sys.argv) > 4 else F(9, 20)
    STEP = F(sys.argv[5]) if len(sys.argv) > 5 else F(1, 20)
    DP = F(sys.argv[6]) if len(sys.argv) > 6 else F(1, 50)      # partner (exclusion) box half-width
    DTHP = F(sys.argv[7]) if len(sys.argv) > 7 else DTH          # partner angle half-width
    PK = packing(); tag = tagof(case)
    obs, par = [[int(k) for k in t.split(",")] for t in case.split(":")]
    SQRT2_UP = F(141422, 100000); assert SQRT2_UP ** 2 >= 2
    wits, wf = [], []
    ws = [(F(0), F(0))]
    k = int(2 * H / STEP); assert k * STEP == 2 * H
    for i in range(k + 1):
        s = -H + i * STEP
        ws += [(s, -H), (s, H)] + ([(-H, s), (H, s)] if 0 < i < k else [])
    for w in ws:
        bound = SQRT2_UP * D + DTH * sqrt_up(w[0] ** 2 + w[1] ** 2) + max(abs(w[0]), abs(w[1]))
        assert bound < HALF, (w, bound)
    for o in obs:
        cx, cy, deg = PK[o]; co, si = TRIG[deg]
        for w in ws:
            x = cx + co * w[0] - si * w[1]; y = cy + si * w[0] + co * w[1]
            wits.append({"x": q3s(x), "y": q3s(y)}); wf.append([float(x), float(y)])
    excl, ef = [], []
    for p in par:
        cx, cy, deg = PK[p]
        dd = float(DTHP) * 180 / math.pi
        for ua, ub in ubox(deg - dd, deg + dd):
            excl.append({"x": [q3s(cx - Q3(DP)), q3s(cx + Q3(DP))], "y": [q3s(cy - Q3(DP)), q3s(cy + Q3(DP))],
                         "u": [str(ua), str(ub)]})
        ef.append([float(cx), float(cy), math.radians(deg), float(DP) * 0.999, float(DTHP) * 0.999])
    stage = {"case": case, "obstacles": obs, "partners": par, "D_obstacle": str(D), "D_partner": str(DP), "DTH_partner": str(DTHP), "DTH": str(DTH), "H": str(H),
             "STEP": str(STEP), "witness_rule": "sqrt2*D + DTH*|w|_2 + |w|_inf < 1/2 checked exactly"}
    json.dump({"stage": stage, "exclusions": excl, "obstacle_points": wits}, open(f"certificates/n6/stage2/{tag}.inputs.json", "w"), indent=1)
    json.dump(wf, open(f"certificates/n6/stage2/{tag}.wit.json", "w")); json.dump(ef, open(f"certificates/n6/stage2/{tag}.excl.json", "w"))
    print(tag, len(wits), "witness points,", len(excl), "exclusion boxes")


def tagof(case):
    o, p = case.split(":")
    return "o" + o.replace(",", "") + "_p" + p.replace(",", "")


main()
