"""Restrict centre intervals by necessary containment of physical unit boxes."""
from fractions import Fraction as F
from correlated_pose_core import correlated_lower_bound


def restrict_centres(L,box):
    x0,x1,y0,y1,a,b=box
    if x0>x1 or y0>y1 or not F(-1,2)<=a<=b<=F(1,2):raise ValueError('Invalid pose interval')
    endpoints=[abs(a),abs(b)]
    if a<=0<=b:endpoints.append(F(0))
    radius=min((1-t*t+2*t)/(2*(1+t*t)) for t in endpoints)
    x0=max(x0,radius);x1=min(x1,L-radius)
    y0=max(y0,radius);y1=min(y1,L-radius)
    if x0>x1 or y0>y1:return None
    return x0,x1,y0,y1,a,b


def physical_lower_bound(model,*box):
    tight=restrict_centres(model[0],box)
    # Empty physical domain: any finite lower bound is vacuously valid.
    # Total measure is also at least every nonempty core score, so it does
    # not weaken min-of-children bounds when used for an impossible child.
    if tight is None:return model[4]
    original=correlated_lower_bound(model,*box)
    if tight==box:return original
    return max(original,correlated_lower_bound(model,*tight))


def adaptive_physical_lower_bound(model,*box):
    """PL30 on both children of each coordinate split; D4 invariant."""
    value=physical_lower_bound(model,*box)
    for axis in range(3):
        mid=(box[2*axis]+box[2*axis+1])/2
        left=list(box);right=list(box)
        left[2*axis+1]=mid;right[2*axis]=mid
        value=max(value,min(physical_lower_bound(model,*left),physical_lower_bound(model,*right)))
    return value


def adaptive2_physical_lower_bound(model,*box):
    """Two levels of complete coordinate splits, retaining each parent bound."""
    from functools import lru_cache
    @lru_cache(None)
    def evaluate(region,depth):
        value=physical_lower_bound(model,*region)
        if depth:
            for axis in range(3):
                mid=(region[2*axis]+region[2*axis+1])/2
                left=list(region);right=list(region)
                left[2*axis+1]=mid;right[2*axis]=mid
                value=max(value,min(evaluate(tuple(left),depth-1),evaluate(tuple(right),depth-1)))
        return value
    return evaluate(tuple(box),2)
