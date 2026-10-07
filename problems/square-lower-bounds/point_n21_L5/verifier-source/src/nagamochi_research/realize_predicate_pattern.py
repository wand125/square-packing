"""Propose rational poses realizing an integral signed-predicate assignment.

A fixed rational angle leaves a two-centre-variable LP. Numerical solutions
only propose poses: ``pattern_realized`` is decided by exact arithmetic.
Failure on finitely many angles never proves that a pattern is impossible.
Physical walls and the original capture calculation remain caller obligations.
"""
from fractions import Fraction as F
import numpy as np
from scipy.optimize import linprog


def search(polynomials, pattern, box, *, steps=256, denominator=10**12):
    box=list(map(F,box));pattern=list(pattern)
    if len(box)!=6 or any(box[i]>box[i+1] for i in (0,2,4)) or box[0]==box[1] or box[2]==box[3]:
        raise ValueError('Need nondegenerate centre intervals')
    if type(steps)is not int or steps<1 or type(denominator)is not int or denominator<1:raise ValueError('Invalid search resolution')
    if not polynomials or len(polynomials)!=len(pattern) or any(z not in (0,1) for z in pattern):raise ValueError('Invalid assignment')
    polys=[[[F(v) for v in p] for p in corners] for corners in polynomials]
    if any(len(p)!=4 or any(len(c)!=3 for c in p) for p in polys):raise ValueError('Expected four centre-corner quadratics')
    if any(p[0][j]+p[3][j]!=p[1][j]+p[2][j] for p in polys for j in range(3)):raise ValueError('Predicates must be affine in centre')
    outside=np.array([1-z for z in pattern],dtype=float);sign=np.where(outside>0,1.,-1.);coeff=np.array(polys,dtype=float);best=None;feasible=0
    for step in range(steps+1):
        t=box[4]+(box[5]-box[4])*F(step,steps);tf=float(t)
        values=(coeff[:,:,0]+tf*coeff[:,:,1]+tf*tf*coeff[:,:,2])*sign[:,None]
        scale=np.maximum(np.max(np.abs(values),axis=1),1e-20)
        a=values[:,0]/scale;b=(values[:,2]-values[:,0])/scale;c=(values[:,1]-values[:,0])/scale
        sol=linprog([0,0,-1],A_ub=np.column_stack([-b,-c,outside]),b_ub=a,bounds=[(0,1),(0,1),(None,None)],method='highs',options={'threads':1})
        if not sol.success:continue
        feasible+=1;u=F(float(sol.x[0])).limit_denominator(denominator);v=F(float(sol.x[1])).limit_denominator(denominator)
        exact=[]
        for p in polys:
            corners=[a+b*t+c*t*t for a,b,c in p];exact.append(corners[0]+u*(corners[2]-corners[0])+v*(corners[1]-corners[0]))
        realized=0<=u<=1 and 0<=v<=1 and all(g<=0 if z else g>0 for g,z in zip(exact,pattern))
        record=dict(pose=list(map(str,[box[0]+(box[1]-box[0])*u,box[2]+(box[3]-box[2])*v,t])),pattern_realized=realized,numerical_margin=float(sol.x[2]),predicate_values=list(map(str,exact)))
        if best is None or (realized,record['numerical_margin'])>(best['pattern_realized'],best['numerical_margin']):best=record
    return dict(best=best,angles_tried=steps+1,numerically_feasible_angles=feasible,exhaustive=False,general_coverage_verified=False)
