"""Rigorous (outward-rounded interval) version of the plan-B branch and bound for n = 3 in the regular hexagon
of side v = (1 + sqrt3)/2.  It proves, for one excused box E_k of the stage-1 certificate:

    there are no three pairwise disjoint closed unit squares in H_v with the first one's pose in E_k.

Soundness notes (see n3/PROOF.md, section 5):
  * Interval arithmetic: every + - * / sqrt result is rounded outward by one ulp (np.nextafter); every
    libm cos/sin/atan result is widened by TRIG_PAD = 1e-15 (libm is accurate to about 1 ulp).
  * A pose box b = [x0,x1] x [y0,y1] x [t0,t1] (centre and angle).  For every pose in b, every point of the
    square is within d = |half-diagonal of the centre rectangle| + |t - tm| * sqrt(1/2) of the corresponding
    point of the mid-pose square (chord <= arc).
  * "outside": some corner of the mid-pose square is beyond a side of H by more than d.
  * "overlap": the mid-pose squares shrunk to side 1 - 2d (contained in every pose's square, by a
    winding-number argument) overlap with positive depth on all four separating axes.
  * "lemma inequalities" (local lemma, n3/local_lemma/LOCAL_LEMMA.md) for every D6 image of the pinwheel and
    every assignment of the three boxes, applied only when the contact-validity bound holds on the node.
  * "lemma neighbourhood": all three boxes inside the local lemma's neighbourhood (tilt <= 0.08, corner <= 0.05).
  * Images of boxes under D6 elements are enclosed in outward-rounded bounding boxes (supersets).
The run is a proof for E_k iff it ends with leaves = 0 and an empty stack.
Usage: python bb_rig.py --box K [--eps 0.004]
"""
import argparse, json, math, os, sys, time
from fractions import Fraction as F
import numpy as np
import numba as nb

TRIG_PAD = 1e-15
INF = np.inf


@nb.njit(cache=True)
def dn(x):
    return np.nextafter(x, -INF)


@nb.njit(cache=True)
def up(x):
    return np.nextafter(x, INF)


@nb.njit(cache=True)
def iadd(a0, a1, b0, b1):
    return dn(a0 + b0), up(a1 + b1)


@nb.njit(cache=True)
def isub(a0, a1, b0, b1):
    return dn(a0 - b1), up(a1 - b0)


@nb.njit(cache=True)
def imul(a0, a1, b0, b1):
    p1 = a0 * b0; p2 = a0 * b1; p3 = a1 * b0; p4 = a1 * b1
    return dn(min(min(p1, p2), min(p3, p4))), up(max(max(p1, p2), max(p3, p4)))


@nb.njit(cache=True)
def isq(a0, a1):
    if a0 >= 0:
        return dn(a0 * a0), up(a1 * a1)
    if a1 <= 0:
        return dn(a1 * a1), up(a0 * a0)
    return 0.0, up(max(a0 * a0, a1 * a1))


@nb.njit(cache=True)
def isqrt(a0, a1):
    return dn(math.sqrt(max(a0, 0.0))), up(math.sqrt(max(a1, 0.0)))


@nb.njit(cache=True)
def icos(a0, a1, PI0, PI1):
    """enclosure of cos on [a0, a1]: endpoint values padded by TRIG_PAD, plus +1 / -1 whenever an even / odd
    multiple of pi may lie in [a0, a1] (k*pi is enclosed by [k*PI0, k*PI1] for k >= 0, reversed for k < 0)."""
    if a1 - a0 >= 6.0:
        return -1.0, 1.0
    c0 = math.cos(a0); c1 = math.cos(a1)
    lo = min(c0, c1) - TRIG_PAD; hi = max(c0, c1) + TRIG_PAD
    kmin = int(math.floor(a0 / 3.14159)) - 1; kmax = int(math.ceil(a1 / 3.14159)) + 1
    for k in range(kmin, kmax + 1):
        if k >= 0:
            e0 = k * PI0; e1 = k * PI1
        else:
            e0 = k * PI1; e1 = k * PI0
        e0 = dn(e0); e1 = up(e1)
        if e1 >= a0 and e0 <= a1:
            if k % 2 == 0:
                hi = 1.0
            else:
                lo = -1.0
    return max(lo, -1.0), min(hi, 1.0)


@nb.njit(cache=True)
def isin(a0, a1, PI0, PI1):
    # sin x = cos(x - pi/2)
    h0, h1 = PI0 / 2, PI1 / 2
    return icos(dn(a0 - h1), up(a1 - h0), PI0, PI1)


@nb.njit(cache=True)
def box_d_up(b):
    """upper bound of d = hypot(half-widths of the centre rectangle) + sqrt(1/2) * half-width of the angle"""
    hx = up((b[1] - b[0]) / 2); hy = up((b[3] - b[2]) / 2); ht = up((b[5] - b[4]) / 2)
    r = up(math.sqrt(up(up(hx * hx) + up(hy * hy))))
    # + 1e-14 covers the rounding of the midpoint used as the reference pose
    return up(up(r + up(ht * 0.7071067811865477)) + 1e-14)


@nb.njit(cache=True)
def mid_pose(b):
    """the mid pose itself is taken as an exact floating point pose (any pose works as the reference as long as
    d bounds the distance to it): use the rounded midpoints and enlarge d by their rounding (included in box_d_up
    through up())."""
    return (b[0] + b[1]) * 0.5, (b[2] + b[3]) * 0.5, (b[4] + b[5]) * 0.5


@nb.njit(cache=True)
def corners_iv(cx, cy, t, side, PI0, PI1, out):
    """corners of the square (centre cx,cy floats, angle t float) with side 'side' (float), as intervals
    out[k, 0:2] = x interval, out[k, 2:4] = y interval, k = 0..3 (BL, BR, TR, TL)"""
    c0, c1 = icos(t, t, PI0, PI1); s0, s1 = isin(t, t, PI0, PI1)
    sg = ((-0.5, -0.5), (0.5, -0.5), (0.5, 0.5), (-0.5, 0.5))
    for k in range(4):
        a = sg[k][0] * side; b = sg[k][1] * side           # exact (side has few bits? no: treat as interval)
        a0 = dn(a); a1 = up(a); b0 = dn(b); b1 = up(b)
        ac = imul(a0, a1, c0, c1); bs = imul(b0, b1, s0, s1)
        as_ = imul(a0, a1, s0, s1); bc = imul(b0, b1, c0, c1)
        x = isub(ac[0], ac[1], bs[0], bs[1]); y = iadd(as_[0], as_[1], bc[0], bc[1])
        x = iadd(x[0], x[1], cx, cx); y = iadd(y[0], y[1], cy, cy)
        out[k, 0] = x[0]; out[k, 1] = x[1]; out[k, 2] = y[0]; out[k, 3] = y[1]


@nb.njit(cache=True)
def outside_rig(b, H0, H1, NSiv, PI0, PI1, tmp):
    cx, cy, t = mid_pose(b)
    d = box_d_up(b)
    corners_iv(cx, cy, t, 1.0, PI0, PI1, tmp)
    for k in range(4):
        for j in range(6):
            px = imul(NSiv[j, 0], NSiv[j, 1], tmp[k, 0], tmp[k, 1])
            py = imul(NSiv[j, 2], NSiv[j, 3], tmp[k, 2], tmp[k, 3])
            s = iadd(px[0], px[1], py[0], py[1])
            v = isub(s[0], s[1], H0, H1)
            if v[0] > up(d * 1.000000000001):
                return True
    return False


@nb.njit(cache=True)
def sat_depth_lo(P, Q):
    """lower bound of the SAT overlap depth of two quadrilaterals given by interval corners (not normalised;
    only its sign matters)"""
    best = 1e18
    for which in range(2):
        poly = P if which == 0 else Q
        for k in range(2):
            ex = isub(poly[k + 1, 0], poly[k + 1, 1], poly[k, 0], poly[k, 1])
            ey = isub(poly[k + 1, 2], poly[k + 1, 3], poly[k, 2], poly[k, 3])
            # normal (-ey, ex)
            amin0 = 1e18; amin1 = 1e18; amax0 = -1e18; amax1 = -1e18
            bmin0 = 1e18; bmin1 = 1e18; bmax0 = -1e18; bmax1 = -1e18
            for i in range(4):
                pa = iadd(*imul(-ey[1], -ey[0], P[i, 0], P[i, 1]), *imul(ex[0], ex[1], P[i, 2], P[i, 3]))
                pb = iadd(*imul(-ey[1], -ey[0], Q[i, 0], Q[i, 1]), *imul(ex[0], ex[1], Q[i, 2], Q[i, 3]))
                amin0 = min(amin0, pa[0]); amin1 = min(amin1, pa[1]); amax0 = max(amax0, pa[0]); amax1 = max(amax1, pa[1])
                bmin0 = min(bmin0, pb[0]); bmin1 = min(bmin1, pb[1]); bmax0 = max(bmax0, pb[0]); bmax1 = max(bmax1, pb[1])
            # depth = min(amax, bmax) - max(amin, bmin); lower bound:
            lo = dn(min(amax0, bmax0) - max(amin1, bmin1))
            best = min(best, lo)
    return best


@nb.njit(cache=True)
def overlap_rig(b, c, PI0, PI1, T1, T2):
    d1 = box_d_up(b); d2 = box_d_up(c)
    if d1 >= 0.49 or d2 >= 0.49:
        return False
    x1, y1, t1 = mid_pose(b); x2, y2, t2 = mid_pose(c)
    s1 = dn(1.0 - up(2 * d1)); s2 = dn(1.0 - up(2 * d2))
    corners_iv(x1, y1, t1, s1, PI0, PI1, T1)
    corners_iv(x2, y2, t2, s2, PI0, PI1, T2)
    return sat_depth_lo(T1, T2) > 0.0


# ----------------------------------------------------------------------------------------------- D6 images
@nb.njit(cache=True)
def g_inverse_box_rig(b, k, mirror, PI0, PI1, CA, SA):
    """outward bounding box of the image of pose box b under g^{-1}, g = R(k pi/3) o (mirror ? diag(-1,1) : I).
    CA[k], SA[k] are intervals (2-vectors) of cos(-k pi/3), sin(-k pi/3)."""
    xmin = 1e18; xmax = -1e18; ymin = 1e18; ymax = -1e18
    for x in (b[0], b[1]):
        for y in (b[2], b[3]):
            u = isub(*imul(CA[k, 0], CA[k, 1], x, x), *imul(SA[k, 0], SA[k, 1], y, y))
            w = iadd(*imul(SA[k, 0], SA[k, 1], x, x), *imul(CA[k, 0], CA[k, 1], y, y))
            if mirror:
                u = (-u[1], -u[0])
            xmin = min(xmin, u[0]); xmax = max(xmax, u[1]); ymin = min(ymin, w[0]); ymax = max(ymax, w[1])
    out = np.empty(6)
    out[0] = xmin; out[1] = xmax; out[2] = ymin; out[3] = ymax
    a0 = dn(k * PI0 / 3); a1 = up(k * PI1 / 3)
    if mirror:
        out[4] = dn(a0 - b[5]); out[5] = up(a1 - b[4])
    else:
        out[4] = dn(b[4] - a1); out[5] = up(b[5] - a0)
    return out


# ----------------------------------------------------------------------------------------------- lemma tests
@nb.njit(cache=True)
def frame_ranges_rig(b, Pc0, Pc1, theta0f, i, V, R3iv, PI0, PI1):
    """tilt interval [a, c] of square (box b) relative to theta0 (relabelled by a multiple of pi/2), and
    bounds pmin, pmax on |p_i| (lower-left corner minus the vertex V, in frame i)."""
    # theta0 = 2 pi i / 3 as an interval
    th0 = dn(2 * i * PI0 / 3); th1 = up(2 * i * PI1 / 3)
    lo = b[4] - theta0f; hi = b[5] - theta0f
    m = math.floor((lo + hi) / 2 / (math.pi / 2) + 0.5)
    sh0 = dn(m * PI0 / 2) if m >= 0 else dn(m * PI1 / 2)
    sh1 = up(m * PI1 / 2) if m >= 0 else up(m * PI0 / 2)
    # tilt = theta - theta0 - sh
    a0 = dn(dn(b[4] - th1) - sh1); c1 = up(up(b[5] - th0) - sh0)
    # q = c_mid - R(t_mid - sh)(1/2,1/2), rotated by -2 pi i/3, minus V
    cx, cy, t = mid_pose(b)
    tm0 = dn(t - sh1); tm1 = up(t - sh0)
    c0, c1_ = icos(tm0, tm1, PI0, PI1); s0, s1 = isin(tm0, tm1, PI0, PI1)
    hx = isub(*imul(0.5, 0.5, c0, c1_), *imul(0.5, 0.5, s0, s1))
    hy = iadd(*imul(0.5, 0.5, s0, s1), *imul(0.5, 0.5, c0, c1_))
    qx = isub(cx, cx, hx[0], hx[1]); qy = isub(cy, cy, hy[0], hy[1])
    # rotation by -2 pi i / 3 : i = 0 identity; i = 1: cos = -1/2, sin = -sqrt3/2; i = 2: cos = -1/2, sin = +sqrt3/2
    if i == 0:
        fx = qx; fy = qy
    else:
        sgn = -1.0 if i == 1 else 1.0
        sx = (sgn * R3iv[0] / 2, sgn * R3iv[1] / 2) if sgn > 0 else (sgn * R3iv[1] / 2, sgn * R3iv[0] / 2)
        fx = isub(*imul(-0.5, -0.5, qx[0], qx[1]), *imul(sx[0], sx[1], qy[0], qy[1]))
        fy = iadd(*imul(sx[0], sx[1], qx[0], qx[1]), *imul(-0.5, -0.5, qy[0], qy[1]))
    fx = isub(fx[0], fx[1], V[0], V[1]); fy = isub(fy[0], fy[1], V[2], V[3])
    d2 = iadd(*isq(fx[0], fx[1]), *isq(fy[0], fy[1]))
    dd = isqrt(d2[0], d2[1])
    r = box_d_up(b)
    return a0, c1, max(0.0, dn(dd[0] - r)), up(dd[1] + r)


@nb.njit(cache=True)
def analytic_rig(tb, order, Pw, V, R3iv, VV, PI0, PI1):
    """lemma inequalities (i), (ii) on the node (boxes tb[order[0..2]] assigned to pinwheel squares 0, 1, 2)"""
    kap = R3iv[0] / 2                      # lower bound of sqrt3/2
    a = np.empty(3); c = np.empty(3); pmin = np.empty(3); pmax = np.empty(3)
    for i in range(3):
        a[i], c[i], pmin[i], pmax[i] = frame_ranges_rig(tb[order[i]], Pw[i, 0], Pw[i, 1], Pw[i, 2], i, V, R3iv, PI0, PI1)
        if a[i] < -0.5 or c[i] > 0.5:
            return False
    Phi = 0.0
    for i in range(3):
        Phi = max(Phi, abs(a[i]), abs(c[i]))
    if up(2 * Phi) >= kap:
        return False
    mlo = dn((R3iv[0] - 1.0) / 2)          # lower bound of the pinwheel margin (sqrt3-1)/2
    s2 = 1.4142135623730954                # > sqrt2
    for i in range(3):
        j = (i + 1) % 3
        phii = max(abs(a[i]), abs(c[i])); phij = max(abs(a[j]), abs(c[j]))
        base = up(up(pmax[i] + pmax[j]) + up(s2 * phii))
        ch = up(base + up(up(1.065 + base) * phij))
        if ch >= mlo:
            return False
    sumF = 0.0
    v0, v1 = VV[0], VV[1]
    for i in range(3):
        j = (i + 1) % 3
        cj = icos(a[j], c[j], PI0, PI1)
        d0 = dn(a[i] - c[j]); d1 = up(c[i] - a[j])
        cd = icos(d0, d1, PI0, PI1); sd = isin(d0, d1, PI0, PI1)
        t1 = imul(up(1.0 + v1) if False else dn(1.0 + v0), up(1.0 + v1), *isub(cj[0], cj[1], 1.0, 1.0))
        t2 = imul(v0, v1, *isub(cd[0], cd[1], 1.0, 1.0))
        t3 = imul(dn(v0 - 1.0), up(v1 - 1.0), sd[0], sd[1])
        Fhi = up(up(t1[1] - t2[0]) + t3[1])
        sumF = up(sumF + Fhi)
        if up(Fhi + up(Phi * up(pmax[i] + pmax[j]))) <= 0.0:
            return True
    ps = dn(dn(pmin[0] + pmin[1]) + pmin[2])
    if up(sumF - dn(dn(kap - up(2 * Phi)) * ps)) <= 0.0:
        return True
    return False


@nb.njit(cache=True)
def in_lemma_rig(b, i, Pw, V, R3iv, PI0, PI1, rho, rhop):
    a0, c1, pmin, pmax = frame_ranges_rig(b, Pw[i, 0], Pw[i, 1], Pw[i, 2], i, V, R3iv, PI0, PI1)
    return a0 >= -rho and c1 <= rho and pmax <= rhop


@nb.njit(cache=True)
def symmetric_rig(bx, Pw, V, R3iv, VV, PI0, PI1, CA, SA, rho, rhop):
    perms = ((0, 1, 2), (0, 2, 1), (1, 0, 2), (1, 2, 0), (2, 0, 1), (2, 1, 0))
    tb = np.empty((3, 6))
    for gi in range(12):
        k = gi // 2; mirror = (gi % 2) == 1
        for i in range(3):
            tb[i] = g_inverse_box_rig(bx[i], k, mirror, PI0, PI1, CA, SA)
        for pi_ in range(6):
            pm = perms[pi_]
            ok = True
            for s in range(3):
                b = tb[pm[s]]
                if abs((b[0] + b[1]) / 2 - Pw[s, 0]) > 0.25 or abs((b[2] + b[3]) / 2 - Pw[s, 1]) > 0.25:
                    ok = False
                    break
            if not ok:
                continue
            order = np.array([pm[0], pm[1], pm[2]])
            if analytic_rig(tb, order, Pw, V, R3iv, VV, PI0, PI1):
                return True
            inside = True
            for s in range(3):
                if not in_lemma_rig(tb[pm[s]], s, Pw, V, R3iv, PI0, PI1, rho, rhop):
                    inside = False
                    break
            if inside:
                return True
    return False


@nb.njit(cache=True)
def run_rig(B1, full, H0, H1, NSiv, Pw, V, R3iv, VV, PI0, PI1, CA, SA, eps, max_nodes, rho, rhop):
    stack = np.empty((8192, 3, 6))
    stack[0, 0, :] = B1; stack[0, 1, :] = full; stack[0, 2, :] = full; sp = 1
    nodes = 0; n_out = 0; n_ov = 0; n_L = 0; leaves = 0
    tmp = np.empty((4, 4)); T1 = np.empty((4, 4)); T2 = np.empty((4, 4))
    while sp > 0:
        sp -= 1
        bx = stack[sp].copy()
        nodes += 1
        if nodes > max_nodes:
            break
        if outside_rig(bx[0], H0, H1, NSiv, PI0, PI1, tmp) or outside_rig(bx[1], H0, H1, NSiv, PI0, PI1, tmp) \
                or outside_rig(bx[2], H0, H1, NSiv, PI0, PI1, tmp):
            n_out += 1; continue
        if overlap_rig(bx[0], bx[1], PI0, PI1, T1, T2) or overlap_rig(bx[0], bx[2], PI0, PI1, T1, T2) \
                or overlap_rig(bx[1], bx[2], PI0, PI1, T1, T2):
            n_ov += 1; continue
        if symmetric_rig(bx, Pw, V, R3iv, VV, PI0, PI1, CA, SA, rho, rhop):
            n_L += 1; continue
        dmax = -1.0; k = 0
        for i in range(3):
            d = box_d_up(bx[i])
            if d > dmax:
                dmax = d; k = i
        if dmax < eps:
            leaves += 1; continue
        b = bx[k]
        w0 = b[1] - b[0]; w1 = b[3] - b[2]; w2 = (b[5] - b[4]) * 0.7
        ax = 0
        if w1 > w0 and w1 >= w2:
            ax = 1
        elif w2 > w0 and w2 > w1:
            ax = 2
        lo = b[2 * ax]; hi = b[2 * ax + 1]; mid = (lo + hi) / 2      # any split point is fine (cover)
        for half in range(2):
            nbx = bx.copy()
            if half == 0:
                nbx[k, 2 * ax + 1] = mid
            else:
                nbx[k, 2 * ax] = mid
            stack[sp] = nbx
            sp += 1
    return nodes, n_out, n_ov, n_L, leaves, sp


def q3_interval(sv, R3lo, R3hi):
    sv = sv.replace(" ", "")
    if "sqrt3" not in sv:
        q = F(sv); return float_down(q), float_up(q)
    b = sv.replace("*sqrt3", "")
    i = max(b.rfind("+"), b.rfind("-"))
    a, bb = (F(b[:i]), F(b[i:])) if i > 0 else (F(0), F(b))
    lo = float_down(a) + min(float_down(bb) * R3lo, float_down(bb) * R3hi, float_up(bb) * R3lo, float_up(bb) * R3hi)
    hi = float_up(a) + max(float_down(bb) * R3lo, float_down(bb) * R3hi, float_up(bb) * R3lo, float_up(bb) * R3hi)
    return np.nextafter(lo, -np.inf), np.nextafter(hi, np.inf)


def float_down(q):
    f = float(q)
    return f if F(f) <= q else np.nextafter(f, -np.inf)


def float_up(q):
    f = float(q)
    return f if F(f) >= q else np.nextafter(f, np.inf)


def setup():
    R3lo, R3hi = np.nextafter(math.sqrt(3), -np.inf), np.nextafter(math.sqrt(3), np.inf)
    assert F(R3lo) ** 2 < 3 < F(R3hi) ** 2
    PI0, PI1 = np.nextafter(math.pi, -np.inf), np.nextafter(math.pi, np.inf)   # math.pi < pi < next
    v0, v1 = np.nextafter((1 + R3lo) / 2, -np.inf), np.nextafter((1 + R3hi) / 2, np.inf)
    H0, H1 = np.nextafter(v0 * R3lo / 2, -np.inf), np.nextafter(v1 * R3hi / 2, np.inf)
    # outward normals of the sides: (cos(pi/2 + k pi/3), sin(...)) = combinations of 0, +-1, +-1/2, +-sqrt3/2
    exact = {0: (0.0, 1.0), 1: (-0.5, 0.5), 2: (-0.5, -0.5), 3: (0.0, -1.0), 4: (0.5, -0.5), 5: (0.5, 0.5)}
    NSiv = np.zeros((6, 4))
    for k in range(6):
        ang = math.pi / 2 + k * math.pi / 3
        cx, cy = math.cos(ang), math.sin(ang)
        # x components are 0 or +-sqrt3/2, y components are +-1 or +-1/2
        if abs(cx) < 1e-12:
            NSiv[k, 0:2] = 0.0
        else:
            s = 1 if cx > 0 else -1
            NSiv[k, 0:2] = sorted((s * R3lo / 2, s * R3hi / 2))
        NSiv[k, 2:4] = (round(cy * 2) / 2, round(cy * 2) / 2)
    # vertex V = (-v/2, -h), pinwheel poses (floats are fine: they only position the lemma frames; the lemma
    # neighbourhood and inequalities are evaluated relative to these exact centres -- see the note below)
    V = np.array([dn_f(-v1 / 2), up_f(-v0 / 2), dn_f(-H1), up_f(-H0)])
    S = (1 + math.sqrt(3)) / 2; H = S * math.sqrt(3) / 2
    Pw = np.zeros((3, 3))
    for i in range(3):
        an = 2 * math.pi * i / 3
        Pw[i, 0] = math.cos(an) * (-S / 2 + .5) - math.sin(an) * (-H + .5)
        Pw[i, 1] = math.sin(an) * (-S / 2 + .5) + math.cos(an) * (-H + .5)
        Pw[i, 2] = an
    CA = np.zeros((6, 2)); SA = np.zeros((6, 2))
    half = {0: (1.0, 0.0), 1: (0.5, -1), 2: (-0.5, -1), 3: (-1.0, 0.0), 4: (-0.5, 1), 5: (0.5, 1)}
    for k in range(6):
        c = math.cos(-k * math.pi / 3); s = math.sin(-k * math.pi / 3)
        CA[k] = (round(c * 2) / 2, round(c * 2) / 2)
        if abs(s) < 1e-12:
            SA[k] = (0.0, 0.0)
        else:
            sg = 1 if s > 0 else -1
            SA[k] = sorted((sg * R3lo / 2, sg * R3hi / 2))
    return dict(R3iv=np.array([R3lo, R3hi]), PI0=PI0, PI1=PI1, VV=np.array([v0, v1]), H0=H0, H1=H1, NSiv=NSiv,
                V=V, Pw=Pw, CA=CA, SA=SA, S=S, H=H)


def dn_f(x): return np.nextafter(x, -np.inf)
def up_f(x): return np.nextafter(x, np.inf)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--box", type=int, default=86)
    ap.add_argument("--eps", type=float, default=0.004)
    ap.add_argument("--max-nodes", type=float, default=5e9)
    a = ap.parse_args()
    C = setup()
    here = os.path.dirname(os.path.abspath(__file__))
    cert = json.load(open(os.path.join(here, "..", "n3", "stage1_cert.json")))
    e = cert["excused"][a.box]
    R3lo, R3hi = C["R3iv"]
    L0, L1 = q3_interval(cert["L"], R3lo, R3hi)
    h0, h1 = C["H0"], C["H1"]
    # excused box in the checker frame -> centre-0 frame (subtract (L, L sqrt3/2)), angle = 2 atan(u)
    x0 = dn_f(float_down(F(e[0])) - L1); x1 = up_f(float_up(F(e[1])) - L0)
    y0 = dn_f(float_down(F(e[2])) - h1); y1 = up_f(float_up(F(e[3])) - h0)
    t0 = dn_f(2 * math.atan(float_down(F(e[4]))) - 2 * TRIG_PAD); t1 = up_f(2 * math.atan(float_up(F(e[5]))) + 2 * TRIG_PAD)
    B1 = np.array([x0, x1, y0, y1, t0, t1])
    S = C["S"]; H = C["H"]
    full = np.array([dn_f(-S - 1e-9), up_f(S + 1e-9), dn_f(-H - 1e-9), up_f(H + 1e-9), 0.0, up_f(math.pi / 2 + 1e-12)])
    args = (full, C["H0"], C["H1"], C["NSiv"], C["Pw"], C["V"], C["R3iv"], C["VV"], C["PI0"], C["PI1"], C["CA"], C["SA"])
    tc = time.time()
    run_rig(B1, *args, 0.5, 10, 0.08, 0.05)
    tc = time.time() - tc
    t_ = time.time()
    nodes, n_out, n_ov, n_L, leaves, left = run_rig(B1, *args, a.eps, int(a.max_nodes), 0.08, 0.05)
    dt = time.time() - t_
    ok = leaves == 0 and left == 0 and nodes <= a.max_nodes
    print(f"box {a.box} eps {a.eps}: nodes {nodes} out {n_out} overlap {n_ov} lemma {n_L} leaves {leaves} left {left} "
          f"{dt:.1f}s ({nodes/max(dt,1e-9)/1e6:.2f} M/s) compile {tc:.1f}s -> {'PROVED' if ok else 'not proved'}", flush=True)


if __name__ == "__main__":
    main()
