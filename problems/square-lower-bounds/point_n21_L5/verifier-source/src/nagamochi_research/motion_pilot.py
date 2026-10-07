"""Bentz-inspired rational row motions, finite checks and exact defect diagnostics.
No all-position/all-time unavoidability or new packing theorem is asserted.
"""
import os
for name in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','VECLIB_MAXIMUM_THREADS'):
    os.environ[name]='1'
from fractions import Fraction as F
from itertools import combinations
from math import isqrt
from pathlib import Path
import json
from time import perf_counter
import numpy as np
from score import square,cross,sub
from pilot import samples
from support_pilot import holdout


def sqrt_interval(n,den=10**12):
    a=isqrt(n*den*den)
    return F(a,den),F(a+1,den)


def rows(k,ys=None,colour=0):
    if ys is None:
        wall=F(9,10) if k==5 else F(457,500)
        ys=[wall+i*(k-2*wall)/(k-1) for i in range(k)]
    out=[]
    for i,y in enumerate(ys):
        xs=[F(j) for j in range(1,k)] if (i+colour)%2==0 else [F(2*j+1,2) for j in range(k)]
        out.extend((x,y) for x in xs)
    return out


def focus_heights(k,index):
    wall=F(9,10) if k==5 else F(457,500)
    special={j for j in (index-1,index) if 0<=j<k-1}
    other=(F(k)-2*wall-F(4,5)*len(special))/(k-1-len(special))
    gaps=[F(4,5) if j in special else other for j in range(k-1)]
    assert min(gaps)>0 and max(gaps)**2<=F(3,4)
    ys=[wall]
    for g in gaps: ys.append(ys[-1]+g)
    return ys


def paths(k):
    base_wall=F(9,10) if k==5 else F(457,500)
    base_ys=[base_wall+i*(k-2*base_wall)/(k-1) for i in range(k)]
    for colour in (0,1):
        for focus in range(k):
            end=focus_heights(k,focus)
            # Vertical interpolation of entire rows; original lemmas' gap bounds
            # hold for every interpolation time since these inequalities are affine.
            for time in (F(0),F(1,2),F(1)):
                ys=[(1-time)*a+time*b for a,b in zip(base_ys,end)]
                yield dict(k=k,colour=colour,focus=focus,phase='vertical',time=time),rows(k,ys,colour)
            if (focus+colour)%2==0: continue
            for phase in ('row-left','leftmost-right'):
                for time in (F(0),F(1,2),F(1)):
                    points=rows(k,end,colour);moved=[]
                    for x,y in points:
                        if y==end[focus]:
                            if phase=='row-left': x-=time/10
                            elif x==F(1,2): x+=time/2
                        moved.append((x,y))
                    yield dict(k=k,colour=colour,focus=focus,phase=phase,time=time),moved


def strict_contains(poly,p):
    return all(cross(sub(b,a),sub(p,a))>0 for a,b in zip(poly,poly[1:]+poly[:1]))


def probe(points,poses):
    data=np.array([[float(p[key]) for key in ('cx','cy','delta','t')] for p in poses]);cx,cy,d,t=data.T
    c=(1-t*t)/(1+t*t);s=2*t/(1+t*t);h=(1+d)/2
    p=np.array(points,dtype=float);dx=p[None,:,0]-cx[:,None];dy=p[None,:,1]-cy[:,None]
    distances=np.maximum(np.abs(c[:,None]*dx+s[:,None]*dy),np.abs(-s[:,None]*dx+c[:,None]*dy))
    margins=h-distances.min(axis=1);order=np.argsort(margins)
    for i in order:
        if margins[i]>1e-11: break
        pose=poses[int(i)];poly=square(pose['cx'],pose['cy'],1+pose['delta'],pose['t'])
        if not any(strict_contains(poly,pt) for pt in points):
            return dict(status='EXACT_EMPTY_OPEN_SQUARE',pose=pose,vertices=poly,points=points,float_margin=float(margins[i]))
    return dict(status='FINITE_PASS',samples=len(poses),minimum_float_margin=float(margins.min()))


def defect_cases(points,slack):
    # Diameter is a necessary condition only. Enumerating a superset is safe for
    # universal combinatorial checks; it does not certify simultaneous packability.
    ids=range(len(points));lim=2*F(101,100)**2
    def close(a,b):return sum((points[a][j]-points[b][j])**2 for j in (0,1))<lim
    pairs=[p for p in combinations(ids,2) if close(*p)]
    if slack==0: yield (),();return
    if slack==1:
        for i in ids:yield (i,),()
        for pair in pairs:yield (), (pair,)
        return
    if slack!=2:raise ValueError('only surplus 0,1,2 supported')
    for empty in combinations(ids,2):yield empty,()
    for pair in pairs:
        for i in ids:
            if i not in pair:yield (i,),(pair,)
    for a,b in combinations(pairs,2):
        if not set(a)&set(b):yield (),(a,b)
    for triple in combinations(ids,3):
        if all(close(*p) for p in combinations(triple,2)):yield (),(triple,)


def analyse_defects(k,n,colour):
    points=rows(k,colour=colour);slack=len(points)-n
    if slack not in (0,1,2):return dict(points=len(points),slack=slack,status='NOT_ENUMERATED')
    count=unsafe=0;max_bad_rows=0;example=None
    for empty,groups in defect_cases(points,slack):
        count+=1;bad=set(empty)|{i for group in groups for i in group}
        safe=[side for side in (0,1) if all((points[i][0] if side==0 else k-points[i][0])>=2 for i in bad)]
        if not safe:
            unsafe+=1
            if example is None: example=dict(empty=[points[i] for i in empty],groups=[[points[i] for i in g] for g in groups])
        active={p[1] for p in points if p[0]==F(1,2)}
        max_bad_rows=max(max_bad_rows,len({points[i][1] for i in bad}&active))
    return dict(points=len(points),slack=slack,cases=count,no_safe_vertical_side=unsafe,
                max_exceptional_long_rows=max_bad_rows,example=example,
                scope='Surplus patterns plus pair-distance necessary condition; not full packings.')


def capacity(k):
    lo2,hi2=sqrt_interval(2);lo3,hi3=sqrt_interval(3)
    wall=(lo2-F(1,2),hi2-F(1,2));gap=(lo3/2,hi3/2)
    height=(2*wall[0]+(k-1)*gap[0],2*wall[1]+(k-1)*gap[1])
    # To shift a half-integer row by 0.1, both adjacent gaps <=0.8 suffice.
    inner=(2*wall[0]+(k-3)*gap[0]+F(8,5),2*wall[1]+(k-3)*gap[1]+F(8,5))
    edge=(2*wall[0]+(k-2)*gap[0]+F(4,5),2*wall[1]+(k-2)*gap[1]+F(4,5))
    r=k
    while 2*wall[0]+(r-1)*gap[0]<k:r+=1
    return dict(k=k,height_cap_interval=height,interior_focus_height_cap_interval=inner,edge_focus_height_cap_interval=edge,
                base_gap_conditions_possible=height[0]>=k,interior_focus_conditions_possible=inner[0]>=k,
                edge_focus_conditions_possible=edge[0]>=k,rows_sufficient_by_gap_budget=r,
                point_counts_with_these_rows=[sum(k-1 if (i+c)%2==0 else k for i in range(r)) for c in (0,1)])


def main():
    started=perf_counter();out=Path('runs/bentz_motion_20260926');out.mkdir(exist_ok=True,parents=True)
    result={'capacity':[capacity(k) for k in range(4,11)],'motion':[],'baseline':[],'defects':[]}
    for k,n in zip(range(4,11),[12,21,32,45,61,78,97]):
        poses=[p for p,_ in samples(k)]+holdout(k,61703)
        for colour in (0,1):
            result['baseline'].append(dict(k=k,n=n,colour=colour,points=len(rows(k,colour=colour)),check=probe(rows(k,colour=colour),poses)))
            result['defects'].append(dict(k=k,n=n,colour=colour,**analyse_defects(k,n,colour)))
        if k in (5,6):
            for meta,points in paths(k):result['motion'].append(dict(**meta,check=probe(points,poses)))
    # Known n22 control: blue has one surplus point, red has none.
    result['n22_control']=[analyse_defects(5,22,c) for c in (0,1)]
    # Two neighboring horizontal trajectories fit strictly in ONE enlarged square.
    segment_points=[(F(x),F(y)) for x in ('0.4','1') for y in ('0.9','1.7')]
    poly=square(F(7,10),F(13,10),F(101,100),F(0))
    assert all(strict_contains(poly,p) for p in segment_points)
    assert all(0<=x<=5 and 0<=y<=5 for x,y in poly)
    result['shared_box_witness']=dict(vertices=poly,segment_endpoints=segment_points,
                                      scope='Local compatibility only, not a packing of 21 boxes.')
    result['seconds']=perf_counter()-started
    (out/'motion-results.json').write_text(json.dumps(result,default=str,indent=2))
    print(json.dumps(dict(seconds=result['seconds'],motion_snapshots=len(result['motion']),
                         motion_failures=sum(r['check']['status']!='FINITE_PASS' for r in result['motion']),
                         baseline=[(r['k'],r['colour'],r['check']['status']) for r in result['baseline']],
                         control=result['n22_control']),default=str),flush=True)


if __name__=='__main__':main()
