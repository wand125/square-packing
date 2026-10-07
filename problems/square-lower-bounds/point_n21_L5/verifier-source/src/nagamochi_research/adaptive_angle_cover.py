"""All-centre angle-class covers with support phases adapted to the domain.

Use translates by B of centre-polygon vertex coordinates +/- B/2. This
resolves thin near-axis boundary regions without a uniformly tiny lattice.
"""
from fractions import Fraction as F
from math import floor,ceil
from pathlib import Path
import json,time
import numpy as np
from scipy.optimize import linprog
from scipy.sparse import csr_matrix
from joint_angle_lp import rotation
from fixed_orientation_cover import angle_envelope
from score import clip,area


def geometry(L,t,B,h,midphases=False):
    L,t,B,h=map(F,(L,t,B,h));extent,span=angle_envelope(t,h)
    assert 0<B<1 and B*extent<1
    c,s=rotation(t);H=(L-span)/2;assert H>0
    poly=[(c*x+s*y,-s*x+c*y) for x,y in ((-H,-H),(H,-H),(H,H),(-H,H))]
    bound=H*(c+s);limit=bound+B/2
    phases={F(0),B/2}|{(p[0]+B/2)%B for p in poly}
    if midphases:
        order=sorted(phases);phases|={(a+b)/2 for a,b in zip(order,order[1:]+[order[0]+B])}
    coordinates=sorted({phase+j*B for phase in phases
                        for j in range(floor((-limit-phase)/B),ceil((limit-phase)/B)+1)
                        if -limit<=phase+j*B<=limit})
    breaks=sorted({-bound,bound}|{p+shift for p in coordinates for shift in (-B/2,B/2)
                                if -bound<p+shift<bound})
    captured=[]
    for lo,hi in zip(breaks,breaks[1:]):
        mid=(lo+hi)/2;captured.append([j for j,p in enumerate(coordinates) if abs(p-mid)<B/2])
    faces=[];patterns=[];m=len(coordinates)
    for i,(lo,hi) in enumerate(zip(breaks,breaks[1:])):
        strip=clip(clip(poly,0,lo,True),0,hi,False)
        if not strip or area(strip)==0:continue
        for j,(low,high) in enumerate(zip(breaks,breaks[1:])):
            cell=clip(clip(strip,1,low,True),1,high,False)
            if cell and area(cell)>0:
                faces.append([i,j]);patterns.append([a*m+b for a in captured[i] for b in captured[j]])
    return dict(L=str(L),t=str(t),B=str(B),h=str(h),midphases=midphases,
                coordinates=list(map(str,coordinates)),breaks=list(map(str,breaks)),faces=faces,patterns=patterns)


def run(L,t,h,out,midphases=False,inner_slack=F(1,1000000)):
    start=time.monotonic();L,t,h,inner_slack=map(F,(L,t,h,inner_slack))
    assert 0<inner_slack<1
    B=(1-inner_slack)/angle_envelope(t,h)[0]
    g=geometry(L,t,B,h,midphases);rows=[];cols=[];m=len(g['coordinates'])
    for i,p in enumerate(g['patterns']):rows.extend([i]*len(p));cols.extend(p)
    A=csr_matrix((np.ones(len(rows)),(rows,cols)),shape=(len(g['patterns']),m*m))
    r=linprog(np.ones(m*m),A_ub=-A,b_ub=-np.ones(A.shape[0]),bounds=(0,None),method='highs')
    assert r.success,r.message
    nums=[max(0,ceil(float(x)*10**9)) for x in r.x]
    den=min(sum(nums[i] for i in row) for row in g['patterns']);assert den>0
    mass=F(sum(nums),den)
    result=dict(status='EXACT_ADAPTIVE_ANGLE_CLASS_COVER',geometry=g,numerators=nums,denominator=den,
                mass=str(mass),mass_float=float(mass),seconds=time.monotonic()-start)
    out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(result,indent=2))
    print(L,t,h,midphases,m,len(g['faces']),float(mass),result['seconds'],flush=True)
    return result


def verify(q):
    g=q['geometry'];rebuilt=geometry(g['L'],g['t'],g['B'],g['h'],g['midphases']);assert rebuilt==g
    nums=q['numerators'];den=q['denominator']
    assert type(den) is int and den>0 and len(nums)==len(g['coordinates'])**2
    assert all(type(v) is int and v>=0 for v in nums)
    assert min(sum(nums[i] for i in row) for row in g['patterns'])>=den
    mass=F(sum(nums),den);assert mass==F(q['mass'])
    return dict(status='EXACT_ADAPTIVE_CLASS_REPLAYED',mass=str(mass),upper=mass.numerator//mass.denominator,
                faces=len(g['faces']),positive_supports=sum(v>0 for v in nums))
