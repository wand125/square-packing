"""PL38 at a fixed centre around a nonzero rational half-angle.

All point and wall signs are proved on each side of the nominal angle.
This certifies one centre only, never every admissible centre.
"""
from pathlib import Path
from fractions import Fraction as F
import hashlib,json
from probe_external_integer_bridge import read
from score import square,contains
from certify_n21_near_axis_path import add,scale,mul,sign_on_open_interval


def polynomials(cx,cy,t0,direction,L,points):
    t=[t0,F(direction)];tt=mul(t,t)
    r=add([F(1)],tt);c=add([F(1)],scale(tt,-1));s=scale(t,2)
    hnum=add(c,s)
    walls=[add(scale(r,2*z),scale(hnum,-1)) for z in (cx,cy,L-cx,L-cy)]
    conditions=[]
    for x,y in points:
        dx,dy=x-cx,y-cy
        A=add(scale(c,2*dx),scale(s,2*dy))
        B=add(scale(c,2*dy),scale(s,-2*dx))
        conditions.append([add(p,scale(r,-1)) for p in (A,scale(A,-1),B,scale(B,-1))])
    return walls,conditions


def run(candidate,out,cx,cy,t0,T=F(1,1000000),max_halvings=20):
    assert not out.exists()
    cx,cy,t0,T=map(F,(cx,cy,t0,T))
    assert 0<T and 0<=t0-T<t0+T<=F(1,2)
    L,span,W,pts=read(candidate)
    positions=[(F(x)*L/span,F(y)*L/span) for x,y,w in pts]
    systems={d:polynomials(cx,cy,t0,d,L,positions) for d in (-1,1)}
    for attempt in range(max_halvings+1):
        try:
            branches=[]
            for direction,(walls,conditions) in systems.items():
                assert all(sign_on_open_interval(p,T)[0]>=0 for p in walls)
                captured=[];ratio=F(0)
                for i,polys in enumerate(conditions):
                    signs=[sign_on_open_interval(p,T) for p in polys]
                    ratio=max([ratio]+[r for s,r in signs])
                    if all(s<=0 for s,r in signs):captured.append(i)
                for u in (T,T/10**7):
                    poly=square(cx,cy,F(1),t0+direction*u)
                    assert all(0<=x<=L and 0<=y<=L for x,y in poly)
                    assert captured==[i for i,p in enumerate(positions) if contains(poly,p)]
                branches.append(dict(direction=direction,capture=str(F(sum(pts[i][2] for i in captured),W)),
                                     captured_indices=captured,maximum_remainder_ratio=str(ratio)))
            break
        except ValueError:
            if attempt==max_halvings:raise
            T/=2
    poly=square(cx,cy,F(1),t0)
    assert all(0<=x<=L and 0<=y<=L for x,y in poly)
    nominal=F(sum(w for p,(x,y,w) in zip(positions,pts) if contains(poly,p)),W)
    minimum=min([nominal]+[F(b['capture']) for b in branches])
    result=dict(candidate_sha256=hashlib.sha256(candidate.read_bytes()).hexdigest(),
                L=str(L),centre=list(map(str,(cx,cy))),nominal_half_angle=str(t0),
                radius=str(T),closed_interval=[str(t0-T),str(t0+T)],
                nominal_capture=str(nominal),minimum_capture=str(minimum),branches=branches,
                all_point_signs_certified=True,all_wall_signs_certified=True,
                independent_polygon_replays_per_branch=2,all_centres_verified=False,
                general_coverage_verified=False)
    out.write_text(json.dumps(result,indent=2))
    print({k:v for k,v in result.items() if k!='branches'},flush=True)
    return result
