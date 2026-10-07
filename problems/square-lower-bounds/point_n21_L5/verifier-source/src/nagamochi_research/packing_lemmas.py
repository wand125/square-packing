"""Exact reusable packing bounds; proofs: docs/method/packing-lemmas.md.

These functions establish local necessary conditions, never global exclusion.
Only integers, rational strings and Fraction inputs are accepted (no floats).
"""
from fractions import Fraction


def rational(value):
    if isinstance(value, bool) or not isinstance(value, (int, str, Fraction)):
        raise TypeError('Use an integer, rational string or Fraction')
    return Fraction(value)


def rotation(t):
    """PL01: rational cos(theta), sin(theta), t=tan(theta/2)."""
    t = rational(t)
    return (1-t*t)/(1+t*t), 2*t/(1+t*t)


def angle_envelope(t, h):
    """PL01: relative support upper bound and physical span lower bound."""
    t, h = rational(t), rational(h)
    lo, hi = t-h, t+h
    if not 0 <= lo <= hi <= 1:
        raise ValueError('Require 0 <= t-h <= t+h <= 1')
    q = max(abs((v-t)/(1+v*t)) for v in (lo, hi))
    if q > Fraction(2, 5):
        raise ValueError('Relative half-angle tangent exceeds 2/5')
    return (1-q*q+2*q)/(1+q*q), min(sum(rotation(v)) for v in (lo, hi))


def normalized_axis_bounds(k, epsilon):
    """PL03: near-axis capacity and strict fixed-epsilon core (PL04)."""
    if type(k) is not int or k < 3:
        raise ValueError('Require integer k >= 3')
    e = rational(epsilon)
    m = k-1
    if not 0 < e < m:
        raise ValueError('Require 0 < epsilon < k-1; endpoint is excluded')
    sigma = 1-e/m
    h = e/(2*m)
    return dict(sigma=sigma, halfwidth=h, centre_halfwidth=Fraction(m, 2),
                capacity=m*m, axis_side=1/(sigma*(1+2*h)))


def fixed_core_sides(k, epsilon, t, h, safety=Fraction(999999, 1000000)):
    """PL04: sides of strict cores at ONE positive epsilon."""
    bounds = normalized_axis_bounds(k, epsilon)
    safety = rational(safety)
    if not 0 < safety < 1:
        raise ValueError('Require 0 < safety < 1 for strict rotor containment')
    extent, _ = angle_envelope(t, h)
    return bounds['axis_side'], safety/(bounds['sigma']*extent)


def region_capacity_one(vertices, t, side):
    """PL05: sufficient test for same-orientation strict cores in conv(vertices).

False means not established. Caller must prove region coverage and strict
physical containment; this function cannot validate either precondition.
"""
    side = rational(side)
    if side <= 0:
        raise ValueError('Require positive core side')
    points = [(rational(x), rational(y)) for x, y in vertices]
    if not points:
        raise ValueError('Require nonempty polygon or finite hull')
    c, s = rotation(t)
    for a, b in ((c, s), (-s, c)):
        projections = [a*x+b*y for x, y in points]
        if max(projections)-min(projections) > side:
            return False
    return True


def axis_core_halfwidth(side):
    """PL15: two-sided near-axis band strictly containing a core of side B.

Uses the strict inequality of PL03 even when B*(1+2*h) == 1.
"""
    side = rational(side)
    if not Fraction(1,3) < side < 1:
        raise ValueError('Require 1/3 < side < 1')
    return (1-side)/(2*side)


def regions_force_core_intersection(first, second, t_first, t_second, side_first, side_second):
    """PL18 sufficient conflict for every pair of centres in finite convex hulls.

Closed-core intersection is forbidden only when strict containment (PL02)
was established externally. False means no certificate, not compatibility.
"""
    P=[(rational(x),rational(y)) for x,y in first]
    Q=[(rational(x),rational(y)) for x,y in second]
    a,b=rational(side_first),rational(side_second)
    if not P or not Q or min(a,b)<=0:
        raise ValueError('Require nonempty hulls and positive sides')
    c,s=rotation(t_first);C,S=rotation(t_second)
    U=((c,s),(-s,c));V=((C,S),(-S,C))
    def dot(x,y):return x[0]*y[0]+x[1]*y[1]
    for d in U+V:
        p=[dot(d,x) for x in P];q=[dot(d,x) for x in Q]
        farthest=max(abs(max(q)-min(p)),abs(max(p)-min(q)))
        support=(a*sum(abs(dot(d,u)) for u in U)+b*sum(abs(dot(d,v)) for v in V))/2
        if farthest>support:return False
    return True


def low_capture_bound(counts, floors, thresholds, capacities):
    """PL17 arithmetic only: caller must prove all low-capture capacities."""
    if len(counts)!=len(floors) or len(thresholds)!=len(capacities):
        raise ValueError('Length mismatch')
    if any(type(x) is not int or x<0 for x in counts):raise ValueError('Invalid counts')
    n=sum(counts);previous=Fraction(0)
    total=sum(a*rational(c) for a,c in zip(counts,floors))
    for delta,q in zip(thresholds,capacities):
        delta=rational(delta)
        if delta<=previous or type(q) is not int or not 0<=q<=n:raise ValueError('Invalid threshold/capacity')
        total+=(delta-previous)*(n-q);previous=delta
    return total
