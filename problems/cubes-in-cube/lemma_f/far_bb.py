#!/usr/bin/env python3
"""Exact rational branch-and-bound for the far region.

Claim checked: for every rotation R and column k, either
  (A) max_i R_ik^2 > 1/2   (column within 45 deg of an axis: handled by the local lemma, see PROOF.md), or
  (B) F_k(R) = sum_i |R_ik| (2 - w_i) < 1,  w_i = sum_j |R_ij|.
Rotations are R(q) = N(q)/|q|^2 for quaternions q; S^3/{+-1} is covered by the 4 cube faces q_m = 1, other coords in [-1,1].
All arithmetic is exact (Fraction) interval arithmetic, so the result is a proof once the box list closes.
"""
from fractions import Fraction as Fr
import sys, json, time

def imul(a, b):
    p = (a[0]*b[0], a[0]*b[1], a[1]*b[0], a[1]*b[1]); return (min(p), max(p))
def iadd(a, b): return (a[0]+b[0], a[1]+b[1])
def isub(a, b): return (a[0]-b[1], a[1]-b[0])
def isq(a):
    lo, hi = a
    if lo >= 0: return (lo*lo, hi*hi)
    if hi <= 0: return (hi*hi, lo*lo)
    return (Fr(0), max(lo*lo, hi*hi))
def iabs(a):
    lo, hi = a
    if lo >= 0: return a
    if hi <= 0: return (-hi, -lo)
    return (Fr(0), max(-lo, hi))
def idiv_pos(a, d):  # d > 0
    p = (a[0]/d[0], a[0]/d[1], a[1]/d[0], a[1]/d[1]); return (min(p), max(p))

TWO = (Fr(2), Fr(2))

def numer(w, x, y, z):
    """N(q) with R = N/|q|^2 (standard quaternion rotation matrix times |q|^2)."""
    ww, xx, yy, zz = isq(w), isq(x), isq(y), isq(z)
    xy, xz, yz = imul(x, y), imul(x, z), imul(y, z)
    wx, wy, wz = imul(w, x), imul(w, y), imul(w, z)
    d = lambda a, b, c, e: isub(iadd(a, b), iadd(c, e))
    t = lambda a, b: (2*a[0]+2*b[0], 2*a[1]+2*b[1])
    u = lambda a, b: (2*(a[0]-b[1]), 2*(a[1]-b[0]))
    return [[d(ww, xx, yy, zz), u(xy, wz), t(xz, wy)],
            [t(xy, wz), d(ww, yy, xx, zz), u(yz, wx)],
            [u(xz, wy), t(yz, wx), d(ww, zz, xx, yy)]]

def check_box(face, box, pending_cols):
    """Return the list of columns k not yet closed on this box."""
    coords = list(box); coords.insert(face, (Fr(1), Fr(1)))
    n = (Fr(1), Fr(1))
    for c in box: n = iadd(n, isq(c))
    N = numer(*coords)
    A = [[iabs(idiv_pos(N[i][j], n)) for j in range(3)] for i in range(3)]
    W = [iadd(iadd(A[i][0], A[i][1]), A[i][2]) for i in range(3)]
    left = []
    for k in pending_cols:
        # (A): some i has |R_ik|^2 > 1/2 on the whole box
        if any(A[i][k][0] * A[i][k][0] > Fr(1, 2) for i in range(3)):
            continue
        F = (Fr(0), Fr(0))
        for i in range(3): F = iadd(F, imul(A[i][k], isub(TWO, W[i])))
        if F[1] < 1:
            continue
        left.append(k)
    return left

def run(max_depth=30):
    stack = [(f, ((Fr(-1), Fr(1)),)*3, (0, 1, 2), 0) for f in range(4)]
    stats = {"boxes": 0, "closed": 0, "max_depth": 0}
    while stack:
        f, box, cols, dep = stack.pop()
        stats["boxes"] += 1; stats["max_depth"] = max(stats["max_depth"], dep)
        left = check_box(f, box, cols)
        if not left:
            stats["closed"] += 1; continue
        if dep >= max_depth:
            print("FAIL: depth limit", f, [tuple(map(float, c)) for c in box], left); return False, stats
        # split the widest coordinate
        j = max(range(3), key=lambda t: box[t][1]-box[t][0])
        lo, hi = box[j]; mid = (lo+hi)/2
        for part in ((lo, mid), (mid, hi)):
            nb = list(box); nb[j] = part
            stack.append((f, tuple(nb), tuple(left), dep+1))
    return True, stats

if __name__ == "__main__":
    t0 = time.time(); ok, st = run()
    st["seconds"] = round(time.time()-t0, 1); st["ok"] = ok
    print(json.dumps(st))
