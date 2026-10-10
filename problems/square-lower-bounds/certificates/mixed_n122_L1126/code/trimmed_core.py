"""Rational octagonal inner core for every angle between net nodes.

For half-angle node spacing D, relative half-angle is <=D/2. Set
q=cos(2 atan(D/2))+sin(2 atan(D/2)), h=(1-margin)/2.
The convex hull of (h,0), (h/q,h/q) and their D4 images is strictly
inside every corresponding unit square. At axis-tip vertices the projection
is <=h; at diagonal vertices it is <=h*q/q. Convexity handles all points.
The monotonicity used here holds for 0<=D/2<=1/4<tan(pi/8).

This proves the core inclusion, not the coverage of a weighted measure.
"""
from fractions import Fraction as F
from score import area


def parameters(step,margin=F(1,10**8)):
    D=F(step);margin=F(margin)
    if not 0<D<=F(1,2) or not 0<margin<1:raise ValueError('invalid trimmed core')
    u=D/2;c=(1-u*u)/(1+u*u);s=2*u/(1+u*u)
    return (1-margin)/2,c+s-1


def vertices(step,margin=F(1,10**8)):
    h,g=parameters(step,margin);a=h/(1+g)
    return [(h,F(0)),(a,a),(F(0),h),(-a,a),(-h,F(0)),(-a,-a),(F(0),-h),(a,-a)]


def planes(t,box,step,margin=F(1,10**8)):
    """Common octagon of all centres in box: inequalities A*x+B*y<=C."""
    t=F(t);x0,x1,y0,y1=map(F,box);h,g=parameters(step,margin)
    if x0>x1 or y0>y1:raise ValueError('invalid box')
    c=(1-t*t)/(1+t*t);s=2*t/(1+t*t);out=[]
    for a,b in [(sx*aa,sy*bb) for aa,bb in [(F(1),g),(g,F(1))] for sx in (-1,1) for sy in (-1,1)]:
        A=a*c-b*s;B=a*s+b*c
        C=h+min(A*x for x in (x0,x1))+min(B*y for y in (y0,y1));out.append((A,B,C))
    return out


def coefficient(kind,g,inequalities):
    g=tuple(map(F,g))
    if kind=='point':return F(all(a*g[0]+b*g[1]<=c for a,b,c in inequalities))
    if kind=='segment':
        x,y,X,Y=g;lo=F(0);hi=F(1)
        for a,b,c in inequalities:
            v=c-a*x-b*y;slope=a*(X-x)+b*(Y-y)
            if not slope:
                if v<0:return F(0)
            elif slope>0:hi=min(hi,v/slope)
            else:lo=max(lo,v/slope)
        return max(F(0),hi-lo)
    if kind!='rectangle':raise ValueError('point/segment/rectangle required')
    x,y,X,Y=g;poly=[(x,y),(X,y),(X,Y),(x,Y)]
    for a,b,c in inequalities:
        clipped=[]
        for P,Q in zip(poly,poly[1:]+poly[:1]):
            v=c-a*P[0]-b*P[1];w=c-a*Q[0]-b*Q[1]
            if v>=0:clipped.append(P)
            if v*w<0:
                f=v/(v-w);clipped.append(tuple(P[i]+f*(Q[i]-P[i]) for i in (0,1)))
        poly=clipped
    return area(poly)/((X-x)*(Y-y))
