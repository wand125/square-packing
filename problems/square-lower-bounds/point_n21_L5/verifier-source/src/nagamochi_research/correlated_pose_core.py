"""Rational outer polygon for correlated (cos(theta),sin(theta)) coefficients."""
from fractions import Fraction as F
from endpoint_cells import clip_linear
from mixed_density_check import polygon_score,pose_lower_bound


def rotation(t):return ((1-t*t)/(1+t*t),2*t/(1+t*t))


def coefficient_vertices(t0,t1):
    if not F(-1,2)<=t0<=t1<=F(1,2):raise ValueError('Invalid angle interval')
    u=rotation(t0);v=rotation(t1)
    if t0==t1:return [u]
    c0=min(u[0],v[0]);c1=F(1) if t0<=0<=t1 else max(u[0],v[0])
    s0=u[1];s1=v[1]
    poly=[(c0,s0),(c1,s0),(c1,s1),(c0,s1)]
    # Tangents bound the circle. The chord bounds this minor arc on the other
    # side. Retain the old coefficient rectangle too, guaranteeing dominance.
    for a,b,rhs in [(u[0],u[1],F(1)),(v[0],v[1],F(1))]:
        poly=clip_linear(poly,-a,-b,-rhs)
    poly=clip_linear(poly,u[0]+v[0],u[1]+v[1],1+u[0]*v[0]+u[1]*v[1])
    return poly


def correlated_polygon(model,x0,x1,y0,y1,t0,t1):
    if x0>x1 or y0>y1:raise ValueError('Reversed centre interval')
    L,B=model[:2];poly=[(F(0),F(0)),(L,F(0)),(L,L),(F(0),L)]
    constraints=set()
    for c,s in coefficient_vertices(t0,t1):
        for a,b in ((c,s),(-s,c),(-c,-s),(s,-c)):
            constraints.add((a,b,B/2+min(a*x0,a*x1)+min(b*y0,b*y1)))
    for a,b,rhs in sorted(constraints):
        poly=clip_linear(poly,-a,-b,-rhs)
        if not poly:break
    return poly


def correlated_lower_bound(model,*box):
    d,a=polygon_score(correlated_polygon(model,*box),model[2],model[3])
    return max(d+a,pose_lower_bound(model,*box))


def adaptive_lower_bound(model,*box):
    """Keep both children of each split; maximize three valid parent bounds.

    All three axes are tested, making this bound D4 invariant. A fixed choice
    of x alone would not commute with swapping the centre coordinates.
    """
    answer=correlated_lower_bound(model,*box)
    for axis in range(3):
        i=2*axis;mid=(box[i]+box[i+1])/2
        left=list(box);right=list(box);left[i+1]=mid;right[i]=mid
        answer=max(answer,min(correlated_lower_bound(model,*left),correlated_lower_bound(model,*right)))
    return answer
