"""Exact strip projection and sign bands for a future all-centre angle sweep.

These primitives do not themselves certify a measure or a packing bound.
Polynomial coefficients are in ascending degree order.
"""
from fractions import Fraction as F
from certify_n21_near_axis_path import sign_on_open_interval


def sign_band(poly, cap=F(1, 1000)):
    """Return (sign, T), proving the sign on 0 < t <= T <= cap."""
    cap = F(cap)
    if not 0 < cap <= 1:
        raise ValueError('Need 0 < cap <= 1')
    poly = tuple(map(F, poly))
    for k, c in enumerate(poly):
        if c:
            tail = sum(map(abs, poly[k+1:]), F(0))
            T = min(cap, abs(c)/(2*tail)) if tail else cap
            sign = 1 if c > 0 else -1
            assert sign_on_open_interval(poly, T)[0] == sign
            return sign, T
    return 0, cap


def strip_projection(L, D, t, u0, u1):
    """V projection of the closed physical centre polygon in [u0,u1].

    U=2D((1-t²)cx+2t cy), V=2D(-2t cx+(1-t²)cy).
    Return None for an empty intersection, including strips beyond the polygon.
    Unlike an open-cell sweep, this function retains singleton intersections.
    """
    L, D, t, u0, u1 = map(F, (L, D, t, u0, u1))
    if D <= 0 or not 0 < t < 1 or u0 > u1:
        raise ValueError('Need D > 0, 0 < t < 1, and u0 <= u1')
    a, b, r = 1-t*t, 2*t, 1+t*t
    if L <= (a+b)/r:
        raise ValueError('Need a full-dimensional physical centre domain')
    low = D*r*(a+b)
    high = 2*L*D*r*r-low
    v0 = max((a*u0-high)/b, (low-b*u1)/a,
             (a*low-b*high)/(r*r))
    v1 = min((high-b*u0)/a, (a*u1-low)/b,
             (a*high-b*low)/(r*r))
    return None if v0 > v1 else (v0, v1)
