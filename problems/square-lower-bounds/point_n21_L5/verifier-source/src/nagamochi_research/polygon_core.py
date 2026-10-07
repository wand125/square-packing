"""Rational inner polygons of the continuous-angle square intersection.

Research geometry only: this module does not add a production certificate schema.
"""
from fractions import Fraction as F
from trimmed_core import parameters
from score import cross, sub, area


def hull(points):
    points = sorted(set(points))
    def half(seq):
        out = []
        for p in seq:
            while len(out) >= 2 and cross(sub(out[-1], out[-2]), sub(p, out[-1])) <= 0:
                out.pop()
            out.append(p)
        return out
    return half(points)[:-1] + half(reversed(points))[:-1]


def inside_all_angles(point, step, margin=F(1, 10**8)):
    """Exact continuous-angle condition, not an angular sampling test.

    Fold into x>=y>=0. The worst projection is sqrt(x*x+y*y)
    if atan(y/x)<=alpha, and x*cos(alpha)+y*sin(alpha) otherwise.
    alpha=2 atan(step/2); all comparisons below are rational.
    """
    h, _ = parameters(step, margin)
    x, y = sorted(map(abs, map(F, point)), reverse=True)
    u = F(step)/2
    c, s = (1-u*u)/(1+u*u), 2*u/(1+u*u)
    return x*x+y*y <= h*h if y*c <= x*s else x*c+y*s <= h


def vertices(step, arc_intervals=1, margin=F(1, 10**8)):
    """16, 24, 40, ... vertices for arc_intervals=1,2,4,... .

    Join rational points on the radius-h arc to the diagonal corner.
    Every vertex satisfies the exact continuous inclusion condition;
    convexity proves inclusion of every edge and the whole polygon.
    """
    if type(arc_intervals) is not int or arc_intervals < 1:
        raise ValueError('positive integer arc_intervals required')
    h, g = parameters(step, margin)
    seed = [(h/(1+g), h/(1+g))]
    for j in range(arc_intervals+1):
        u = F(step)*j/(2*arc_intervals)
        seed.append((h*(1-u*u)/(1+u*u), h*2*u/(1+u*u)))
    points = [(sx*a, sy*b) for x,y in seed for a,b in ((x,y),(y,x))
              for sx in (-1,1) for sy in (-1,1)]
    poly = hull(points)
    if not all(inside_all_angles(p, step, margin) for p in poly):
        raise AssertionError('core inclusion failed')
    return poly


def outer_area_bound(step, margin=F(1, 10**8)):
    """Intersection at angles 0,+alpha,-alpha bounds the maximal core above.

    This OUTER polygon must never be used as a certified inner core.
    """
    h, _ = parameters(step, margin)
    u = F(step)/2
    c,s = (1-u*u)/(1+u*u),2*u/(1+u*u)
    poly = [(-h,-h),(h,-h),(h,h),(-h,h)]
    for a,b in [(sx*A,sy*B) for A,B in ((c,s),(s,c)) for sx in (-1,1) for sy in (-1,1)]:
        out=[]
        for P,Q in zip(poly,poly[1:]+poly[:1]):
            v=h-a*P[0]-b*P[1];w=h-a*Q[0]-b*Q[1]
            if v>=0:out.append(P)
            if v*w<0:
                t=v/(v-w);out.append(tuple(P[i]+t*(Q[i]-P[i]) for i in (0,1)))
        poly=out
    return area(poly)
