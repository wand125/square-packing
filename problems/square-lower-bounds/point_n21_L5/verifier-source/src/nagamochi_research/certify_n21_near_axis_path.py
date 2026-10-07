"""Exact open-angle counterexample path for a specified point measure at L=5.

Path: cx=h(t)+261*t^2/1000, cy=7/2-261*t/1000.
Every polynomial sign is certified on 0<t<=T by its leading coefficient.
This rejects only the supplied measure, never all measures or packings.
"""
import argparse
import hashlib
import json
from fractions import Fraction as F
from pathlib import Path
from probe_external_integer_bridge import read
from score import square, contains


def add(a, b):
    return [(a[i] if i < len(a) else F(0)) +
            (b[i] if i < len(b) else F(0)) for i in range(max(len(a), len(b)))]


def scale(a, c):
    return [v*c for v in a]


def mul(a, b):
    out = [F(0)]*(len(a)+len(b)-1)
    for i, x in enumerate(a):
        for j, y in enumerate(b):
            out[i+j] += x*y
    return out


def sign_on_open_interval(poly, T):
    for j, c in enumerate(poly):
        if c:
            remainder = sum(abs(v)*T**(k-j) for k, v in enumerate(poly) if k > j)
            if remainder >= abs(c):
                raise ValueError('Leading coefficient cannot certify this interval')
            return (1 if c > 0 else -1), remainder/abs(c)
    return 0, F(0)


def run(candidate, out, T=F(1, 100000), *, alpha=F(261, 1000),
        beta=F(261, 1000), xlinear=F(0), ybase=F(7, 2)):
    assert not out.exists() and 0 < T <= F(1, 1000)
    L, span, W, pts = read(candidate)
    assert L == 5
    D = F(span)/L
    alpha, beta, xlinear, ybase = map(F, (alpha, beta, xlinear, ybase))
    r, c, s = [F(1), F(0), F(1)], [F(1), F(0), F(-1)], [F(0), F(2)]
    hnum = [F(1), F(2), F(-1)]
    xnum = add(hnum, mul([F(0), 2*xlinear, 2*alpha], r))
    ynum = mul([2*ybase, -2*beta], r)
    # All numerators have positive denominator 2*r; require centre within walls.
    walls = [add(xnum, scale(hnum, -1)),
             add(add(scale(r, 2*L), scale(hnum, -1)), scale(xnum, -1)),
             add(ynum, scale(hnum, -1)),
             add(add(scale(r, 2*L), scale(hnum, -1)), scale(ynum, -1))]
    assert all(sign_on_open_interval(p, T)[0] >= 0 for p in walls)
    rr = mul(r, r)
    mass = 0
    captured = []
    max_ratio = F(0)
    for i, (X, Y, w) in enumerate(pts):
        dx = add(scale(r, 2*F(X)/D), scale(xnum, -1))
        dy = add(scale(r, 2*F(Y)/D), scale(ynum, -1))
        A = add(mul(c, dx), mul(s, dy))
        B = add(scale(mul(s, dx), -1), mul(c, dy))
        signs = []
        for poly in (A, scale(A, -1), B, scale(B, -1)):
            sign, ratio = sign_on_open_interval(add(poly, scale(rr, -1)), T)
            signs.append(sign)
            max_ratio = max(max_ratio, ratio)
        if max(signs) <= 0:
            mass += w
            captured.append(i)
    # Independent exact polygon evaluations check the algebra at two positive t.
    checks = []
    for t in (T, T/10**7):
        h = (1+2*t-t*t)/(2*(1+t*t))
        poly = square(h+xlinear*t+alpha*t*t, ybase-beta*t, F(1), t)
        hits = [i for i, (x, y, w) in enumerate(pts)
                if contains(poly, (F(x)/D, F(y)/D))]
        assert hits == captured
        checks.append(str(t))
    data = dict(status='EXACT_OPEN_ANGLE_PATH_CAPTURE',
                candidate_sha256=hashlib.sha256(candidate.read_bytes()).hexdigest(),
                L='5', interval=dict(lower='0', lower_open=True, upper=str(T)),
                cx=f'(1+2*t-t*t)/(2*(1+t*t)) + ({xlinear})*t + ({alpha})*t*t',
                cy=f'({ybase}) - ({beta})*t', capture=str(F(mass, W)),
                parameters=dict(alpha=str(alpha), beta=str(beta),
                                xlinear=str(xlinear), ybase=str(ybase)),
                captured_indices=captured, all_point_signs_certified=True,
                all_wall_signs_certified=True, maximum_remainder_ratio=str(max_ratio),
                polygon_replay_parameters=checks, rejects_candidate=mass < W,
                general_packing_exclusion=False)
    out.write_text(json.dumps(data, indent=2))
    print({k: v for k, v in data.items() if k != 'captured_indices'})


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('candidate', type=Path)
    p.add_argument('out', type=Path)
    a = p.parse_args()
    run(a.candidate, a.out)
