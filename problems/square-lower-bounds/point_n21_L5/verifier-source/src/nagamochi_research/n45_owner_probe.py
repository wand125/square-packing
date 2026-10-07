"""Seek a box containing the repaired trajectory but another red anchor.
Exact fixed-angle feasibility only; no exhaustive all-angle assertion.
"""
from fractions import Fraction as F
import json
from n45_small_motion import ROOT,heights
from motion_pilot import rows,strict_contains
from endpoint_cells import clip_linear
from score import square,area


def probe(focus,singleton=False):
    ys,_=heights(focus);red=rows(7,ys,0);blue=rows(7,ys,1);y=ys[focus];target=(F(1),y);ends=[(F(47,100),y),(F(39,40),y)];side=F(100000001,100000000)
    for j in range(-41,42):
        t=F(j,100);c=(1-t*t)/(1+t*t);s=2*t/(1+t*t);h=side/2;r=h*(abs(c)+abs(s));rot=lambda p:(c*p[0]+s*p[1],-s*p[0]+c*p[1]);anchor=rot(target)
        for point in red:
            if point==target:continue
            req=[rot(p) for p in ends+[point]];lo=[max(p[a] for p in req)-h for a in (0,1)];hi=[min(p[a] for p in req)+h for a in (0,1)]
            if any(a>=b for a,b in zip(lo,hi)):continue
            poly=[(lo[0],lo[1]),(hi[0],lo[1]),(hi[0],hi[1]),(lo[0],hi[1])]
            for aa,bb,hh in [(c,-s,r),(-c,s,-(7-r)),(s,c,r),(-s,-c,-(7-r))]:poly=clip_linear(poly,aa,bb,hh) if poly else []
            for aa,bb,hh in [(1,0,anchor[0]+h),(-1,0,-anchor[0]+h),(0,1,anchor[1]+h),(0,-1,-anchor[1]+h)]:
                q=clip_linear(poly,F(aa),F(bb),hh) if poly else []
                if not q or area(q)==0:continue
                pieces=[q]
                if singleton:
                    for bp in blue:
                        if bp==(F(1,2),y):continue
                        bu,bv=rot(bp);remain=[]
                        for piece in pieces:
                            outside=[(1,0,bu+h),(-1,0,-bu+h),(0,1,bv+h),(0,-1,-bv+h)]
                            if any(all(aa*p[0]+bb*p[1]>=hh for p in piece) for aa,bb,hh in outside):remain.append(piece);continue
                            for aa,bb,hh in outside:
                                cut=clip_linear(piece,F(aa),F(bb),hh)
                                if cut and area(cut)>0:remain.append(cut)
                        pieces=remain
                        if not pieces:break
                if not pieces:continue
                q=pieces[0]
                u=sum(p[0] for p in q)/len(q);v=sum(p[1] for p in q)/len(q);x=c*u-s*v;yy=s*u+c*v;box=square(x,yy,side,t)
                if singleton:assert sum(strict_contains(box,p) for p in blue)==1
                assert all(strict_contains(box,p) for p in ends+[point]) and not strict_contains(box,target)
                assert all(0<=a<=7 and 0<=b<=7 for a,b in box)
                return dict(focus=focus,cx=str(x),cy=str(yy),t=str(t),side=str(side),red_captures=[list(map(str,p)) for p in red if strict_contains(box,p)],blue_captures=[list(map(str,p)) for p in blue if strict_contains(box,p)])
    return dict(focus=focus,status='NO_WITNESS_ON_FINITE_ANGLE_SET')

if __name__=='__main__':
    import sys
    singleton='--singleton' in sys.argv
    out=[probe(0,singleton),probe(6,singleton)];(ROOT/('owner-singleton.json' if singleton else 'owner-probe.json')).write_text(json.dumps(out,indent=2));print(json.dumps(out))
