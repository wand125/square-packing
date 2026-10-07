"""Fast proposal, exact verification of constant captured point sets on a box."""
from fractions import Fraction as F
import numpy as np
from compile_box_capture_rows import contains_all


def prepare(coords,weights):
    order=sorted((i for i,w in enumerate(weights) if w>0),key=lambda i:weights[i],reverse=True)
    return order,np.array([float(coords[i][0]) for i in order]),np.array([float(coords[i][1]) for i in order]),np.array([float(weights[i]) for i in order])


def witness(coords,weights,box,prepared):
    order,px,py,w=prepared;x0,x1,y0,y1,t0,t1=map(float,map(F,box))
    dx0,dx1,dy0,dy1=px-x0,px-x1,py-y0,py-y1
    polys=[(2*dx0-1,4*dy0,-2*dx0-1),(-2*dx1-1,-4*dy1,2*dx1-1),
           (2*dy0-1,-4*dx1,-2*dy0-1),(-2*dy1-1,4*dx0,2*dy1-1)]
    mask=np.ones(len(order),dtype=bool)
    for a,b,c in polys:
        upper=np.maximum(a+b*t0+c*t0*t0,a+b*t1+c*t1*t1)
        active=c<0;vertex=np.zeros_like(c);np.divide(-b,2*c,out=vertex,where=active)
        active &= (vertex>t0)&(vertex<t1)
        upper=np.where(active,np.maximum(upper,a+b*vertex+c*vertex*vertex),upper)
        mask &= upper<=1e-10
    # This floating rejection may miss a proof; it can never certify a box.
    if float(w[mask].sum())<1-1e-8:return None
    indices=[];mass=F(0)
    for position in np.flatnonzero(mask):
        i=order[int(position)]
        if contains_all(coords[i],box):
            indices.append(i);mass+=weights[i]
            if mass>=1:return dict(indices=indices,lower=str(mass))
    return None


def replay(coords,weights,box,record):
    ids=record['indices']
    if not ids or len(set(ids))!=len(ids) or any(type(i) is not int or not 0<=i<len(coords) for i in ids):raise ValueError('Invalid indices')
    if not all(contains_all(coords[i],box) for i in ids):raise ValueError('Unproved point containment')
    mass=sum((weights[i] for i in ids),F(0))
    if str(mass)!=record['lower'] or mass<1:raise ValueError('Unproved capture')
    return mass
