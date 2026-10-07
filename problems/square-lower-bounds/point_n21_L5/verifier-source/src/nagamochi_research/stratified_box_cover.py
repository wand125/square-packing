"""Exact axis-aligned cover check including lower-dimensional boundaries."""
from fractions import Fraction as F
from itertools import product


def verify(root,closed,open_lower_t):
    root=tuple(map(F,root));closed=[tuple(map(F,b)) for b in closed];opened=[tuple(map(F,b)) for b in open_lower_t]
    if len(root)!=6 or any(root[i]>root[i+1] for i in (0,2,4)):raise ValueError('Invalid root')
    for box in closed+opened:
        if len(box)!=6 or any(not root[i]<=box[i]<=box[i+1]<=root[i+1] for i in (0,2,4)):
            raise ValueError('Cover box outside root')
    samples=[]
    for axis in (0,2,4):
        knots=sorted({root[axis],root[axis+1]}|{b[k] for b in closed+opened for k in (axis,axis+1)})
        samples.append(sorted(knots+[(a+b)/2 for a,b in zip(knots,knots[1:])]))
    count=0
    for point in product(*samples):
        count+=1
        def inside(b):return all(b[2*k]<=point[k]<=b[2*k+1] for k in range(3))
        if not any(inside(b) for b in closed) and not any(inside(b) and point[2]>b[4] for b in opened):
            raise ValueError('Uncovered stratum: '+str(point))
    return dict(strata_checked=count,boundaries_checked=True)
