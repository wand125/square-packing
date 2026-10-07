"""Exact finite stress test of homothetically moved external point covers.
Every accepted witness is a physical unit square; no global coverage claim.
"""
from fractions import Fraction as F
from math import lcm
from pathlib import Path
import argparse,json,hashlib
from collections import Counter

def read(path):
    v=list(map(int,path.read_text().split()));sn,sd,D,W,m=v[:5];assert len(v)==5+3*m and min(sn,sd,D,W,m)>0
    L=F(sn,sd);span=L*D;assert span.denominator==1;span=int(span)
    pts=[tuple(v[i:i+3]) for i in range(5,len(v),3)];assert all(0<=x<=span and 0<=y<=span and w>=0 for x,y,w in pts)
    counts=Counter()
    for x,y,w in pts:counts[x,y]+=w
    for swap in (0,1):
        for sx,sy in ((1,1),(1,-1),(-1,1),(-1,-1)):
            transformed=Counter()
            for (x,y),w in counts.items():
                if swap:x,y=y,x
                transformed[x if sx==1 else span-x,y if sy==1 else span-y]+=w
            assert transformed==counts
    return L,span,W,pts

def run(path,targets):
    native,span,W,pts=read(path);records=[]
    for L in targets:
        minimum=None;violations=[];count=0
        for t in map(F,['0','1/100000','1/10000','1/1000','1/100','1/10','1/3','2/5']):
            p,q=t.numerator,t.denominator;a=q*q-p*p;b=2*p*q;r=q*q+p*p;h=F(a+b,2*r)
            centres={h,L-h,L/2}
            for j in range(int(L)):
                for delta in map(F,['0','-1/10000','1/10000']):
                    x=F(2*j+1,2)+delta
                    if h<=x<=L-h:centres.add(x)
            for cx in sorted(centres):
                for cy in sorted(centres):
                    H=lcm(L.denominator,cx.denominator,cy.denominator);A=int(L*H);X0=int(span*cx*H);Y0=int(span*cy*H);limit=r*span*H
                    mass=sum(w for x,y,w in pts if 2*abs(a*(x*A-X0)+b*(y*A-Y0))<=limit and 2*abs(a*(y*A-Y0)-b*(x*A-X0))<=limit)
                    rec=dict(cx=str(cx),cy=str(cy),t=str(t),score=str(F(mass,W)));count+=1
                    if minimum is None or mass<minimum[0]:minimum=(mass,rec)
                    if mass<W:violations.append(rec)
        records.append(dict(L=str(L),poses=count,minimum=minimum[1],violations=violations));print(path.name,str(L),count,minimum[1],len(violations),flush=True)
    return dict(file=str(path),sha256=hashlib.sha256(path.read_bytes()).hexdigest(),native_L=str(native),points=len(pts),total_mass=str(F(sum(w for x,y,w in pts),W)),D4_exact=True,records=records,general_coverage_verified=False)

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('certificate',type=Path);p.add_argument('out',type=Path);p.add_argument('targets',nargs='+');a=p.parse_args();assert not a.out.exists();a.out.write_text(json.dumps(run(a.certificate,list(map(F,a.targets))),indent=2))
