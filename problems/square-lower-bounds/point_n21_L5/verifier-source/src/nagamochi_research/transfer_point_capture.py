"""Conditional exact lower-bound transfer between two finite point measures.

The caller must independently verify old_lower on the same physical pose box.
This module verifies only the geometric correction, never the source proof.
"""
from fractions import Fraction as F
from itertools import product
from compile_box_capture_rows import contains_all
from closed_cover_bridge import predicate,quad_max


def classify(point, box):
    x,y=map(F,point);x0,x1,y0,y1,t0,t1=map(F,box)
    if x<x0-F(3,4) or x>x1+F(3,4) or y<y0-F(3,4) or y>y1+F(3,4):return 'outside'
    if contains_all((x,y),box):return 'always'
    corners=list(product((x0,x1),(y0,y1)))
    for kind in range(4):
        # An everywhere strictly positive excess excludes the closed point.
        lower=min(-quad_max(*(-v for v in predicate((x,y),kind,cx,cy,F(1))),t0,t1) for cx,cy in corners)
        if lower>0:return 'outside'
    return 'uncertain'


def bound(coordinates, old_weights, new_weights, box, old_lower):
    box=tuple(map(F,box));old=list(map(F,old_weights));new=list(map(F,new_weights));q=F(old_lower)
    if len(box)!=6 or any(box[i]>box[i+1] for i in (0,2,4)) or not 0<=box[4]<=box[5]<=F(1,2):raise ValueError('Invalid box')
    if len(coordinates)!=len(old) or len(old)!=len(new) or any(w<0 for w in old+new) or q<0:raise ValueError('Invalid measures')
    kinds=[classify(p,box) for p in coordinates]
    always=[i for i,k in enumerate(kinds) if k=='always'];uncertain=[i for i,k in enumerate(kinds) if k=='uncertain']
    old_base=sum((old[i] for i in always),F(0));new_base=sum((new[i] for i in always),F(0))
    alphas={F(0),F(1)}|{new[i]/old[i] for i in uncertain if old[i]>0}
    def lower(a):return a*q+new_base-a*old_base+sum((min(F(0),new[i]-a*old[i]) for i in uncertain),F(0))
    alpha=max(sorted(alphas),key=lower);value=lower(alpha)
    return dict(alpha=str(alpha),lower=str(value),source_lower=str(q),always=len(always),uncertain=len(uncertain),outside=kinds.count('outside'),source_proof_verified=False,conditional_unit_capture=value>=1,general_coverage_verified=False)


def bound_alpha_one(coordinates, old_weights, new_weights, box, old_lower):
    """PL56 at alpha=1: unchanged weights need no geometric classification.

    This is a cheaper, possibly weaker alternative to ``bound``. The caller
    still has to replay the source proof on the same physical domain.
    """
    box=tuple(map(F,box));old=list(map(F,old_weights));new=list(map(F,new_weights));q=F(old_lower)
    if len(box)!=6 or any(box[i]>box[i+1] for i in (0,2,4)) or not 0<=box[4]<=box[5]<=F(1,2):raise ValueError('Invalid box')
    if len(coordinates)!=len(old) or len(old)!=len(new) or any(w<0 for w in old+new) or q<0:raise ValueError('Invalid measures')
    value=q;changed=0
    for point,w,v in zip(coordinates,old,new):
        delta=v-w
        if not delta:continue
        changed+=1;kind=classify(point,box)
        if kind=='always':value+=delta
        elif kind=='uncertain':value+=min(F(0),delta)
    return dict(alpha='1',lower=str(value),source_lower=str(q),classified_points=changed,skipped_points=len(old)-changed,source_proof_verified=False,conditional_unit_capture=value>=1,general_coverage_verified=False)
