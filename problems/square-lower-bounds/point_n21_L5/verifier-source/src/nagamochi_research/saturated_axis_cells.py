"""Necessary rotated-centre domain when every axis-centre cell is occupied.

Closed residual polygons retain boundary and degenerate pieces. This is a
conditional relaxation, not a complete mixed-packing solver.
"""
from fractions import Fraction as F
from pathlib import Path
from itertools import combinations
import json,time
from joint_angle_lp import rotation
from score import area


def halfplane(poly,a,b,d):
    """Keep a*x+b*y<=d, retaining point/segment intersections."""
    if not poly:return []
    result=[]
    for p,q in zip(poly,poly[1:]+poly[:1]):
        u=d-a*p[0]-b*p[1];v=d-a*q[0]-b*q[1]
        if u>=0:result.append(p)
        if (u<0<v) or (v<0<u):
            z=u/(u-v);result.append((p[0]+z*(q[0]-p[0]),p[1]+z*(q[1]-p[1])))
    clean=[]
    for p in result:
        if not clean or p!=clean[-1]:clean.append(p)
    if len(clean)>1 and clean[0]==clean[-1]:clean.pop()
    return clean


def subtract_open(poly,inequalities):
    """Complement of an OPEN convex polygon, represented as a closed union."""
    remaining=poly;outside=[]
    for a,b,d in inequalities:
        piece=halfplane(remaining,-a,-b,-d)
        if piece:outside.append(piece)
        remaining=halfplane(remaining,a,b,d)
        if not remaining:break
    return outside


def contained(poly,outer):
    """Exact containment in a closed convex polygon, segment, or point."""
    if len(outer)==1:return all(p==outer[0] for p in poly)
    if area(outer)==0:
        a=min(outer);b=max(outer)
        return all((b[0]-a[0])*(p[1]-a[1])==(b[1]-a[1])*(p[0]-a[0])
                   and a[0]<=p[0]<=b[0] and min(a[1],b[1])<=p[1]<=max(a[1],b[1]) for p in poly)
    return all((b[0]-a[0])*(p[1]-a[1])-(b[1]-a[1])*(p[0]-a[0])>=0
               for a,b in zip(outer,outer[1:]+outer[:1]) for p in poly)


def remove_contained(pieces):
    # Equal regions keep the first representative; lower-dimensional boundary
    # pieces are removed ONLY when already covered by a retained closed piece.
    return [p for i,p in enumerate(pieces) if not any(
        i!=j and contained(p,q) and (j<i or not contained(q,p))
        for j,q in enumerate(pieces))]


def build(L,t,k,axis_inner=F(1),rot_inner=F(1),rot_half=None,missing=()):
    L,t,axis_inner,rot_inner=map(F,(L,t,axis_inner,rot_inner));c,s=rotation(t);w=c+s
    assert 0<=t<=F(2,5) and k-1<L<k and 0<axis_inner<=1
    assert len(set(missing))==len(missing) and all(type(i) is int and 0<=i<(k-1)**2 for i in missing)
    d=(L-1)/(k-1);assert d<axis_inner
    H=(L-w)/2 if rot_half is None else F(rot_half)
    pieces=[[(-H,-H),(H,-H),(H,H),(-H,H)]];forbidden=[]
    for i in range(k-1):
        for j in range(k-1):
            if i*(k-1)+j in missing:continue
            mx=-(L-1)/2+(F(i)+F(1,2))*d;my=-(L-1)/2+(F(j)+F(1,2))*d
            rx=(axis_inner+rot_inner*w-d)/2;ru=(rot_inner+(axis_inner-d)*w)/2
            inequalities=[]
            for a,b,radius in ((F(1),F(0),rx),(F(0),F(1),rx),(c,s,ru),(-s,c,ru)):
                for sign in (-1,1):inequalities.append((sign*a,sign*b,radius+sign*(a*mx+b*my)))
            forbidden.append(inequalities)
            new={}
            for p in pieces:
                for q in subtract_open(p,inequalities):new[tuple(sorted(set(q)))]=q
            pieces=list(new.values())
    return (remove_contained(pieces) if missing else pieces),forbidden


def diagnose(L,t,k,out):
    start=time.monotonic();L,t=F(L),F(t);pieces,forbidden=build(L,t,k);c,s=rotation(t)
    spans=[]
    for poly in pieces:
        spans.append([(min(a*x+b*y for x,y in poly),max(a*x+b*y for x,y in poly)) for a,b in ((c,s),(-s,c))])
    single=[all(hi-lo<1 for lo,hi in p) for p in spans]
    compatible=[set() for _ in spans]
    for i,j in combinations(range(len(spans)),2):
        if any(max(spans[i][v][1]-spans[j][v][0],spans[j][v][1]-spans[i][v][0])>=1 for v in (0,1)):
            compatible[i].add(j);compatible[j].add(i)
    triangle=None
    for i in range(len(spans)):
        for j in compatible[i]:
            if j<=i:continue
            common=[v for v in compatible[i]&compatible[j] if v>j]
            if common:triangle=[i,j,min(common)];break
        if triangle:break
    result=dict(status='EXACT_SATURATED_AXIS_DOMAIN_DIAGNOSTIC',L=str(L),t=str(t),k=k,axis_boxes=(k-1)**2,
                pieces=[[[str(x),str(y)] for x,y in p] for p in pieces],
                residual_area=str(sum(area(p) for p in pieces)),degenerate_pieces=sum(area(p)==0 for p in pieces),
                each_piece_capacity_one=all(single),compatible_triangle=triangle,
                upper_two_proved=all(single) and triangle is None,seconds=time.monotonic()-start,
                limitation='Assumes all axis-centre cells are occupied. Nonempty residuals and compatibility triangles are only relaxations, not feasible packings.')
    out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(result,indent=2))
    print(k,L,t,len(pieces),result['residual_area'],result['degenerate_pieces'],triangle,result['seconds'],flush=True)
    return result
