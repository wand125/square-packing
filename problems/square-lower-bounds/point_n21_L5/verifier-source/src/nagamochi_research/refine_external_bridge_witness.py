"""Exact rational local descent; witnessed failures, never coverage claims."""
from fractions import Fraction as F
from math import lcm
from itertools import product
from pathlib import Path
import json,argparse,hashlib
from probe_external_integer_bridge import read
from score import square,contains

def run(certificate,prior,index,target=None):
 native,span,W,pts=read(certificate);data=json.loads(prior.read_text());assert data['sha256']==hashlib.sha256(certificate.read_bytes()).hexdigest();row=data['records'][index];L=F(row['L']);w=row['minimum'];pose=tuple(F(w[k]) for k in ['cx','cy','t']);count=0
 def evaluate(pose):
  nonlocal count
  cx,cy,t=pose
  if not 0<=t<=F(1,2):return None
  p,q=t.numerator,t.denominator;a=q*q-p*p;b=2*p*q;r=q*q+p*p;h=F(a+b,2*r)
  if not h<=cx<=L-h or not h<=cy<=L-h:return None
  H=lcm(L.denominator,cx.denominator,cy.denominator);A=int(L*H);X0=int(span*cx*H);Y0=int(span*cy*H);limit=r*span*H;count+=1
  return sum(m for x,y,m in pts if 2*abs(a*(x*A-X0)+b*(y*A-Y0))<=limit and 2*abs(a*(y*A-Y0)-b*(x*A-X0))<=limit)
 if target is not None:
  old_L=L;L=F(target);cx,cy,t=pose;h=(1-t*t+2*t)/(2*(1+t*t));pose=(h+(cx-h)*(L-2*h)/(old_L-2*h),h+(cy-h)*(L-2*h)/(old_L-2*h),t)
 best=evaluate(pose);initial_score=F(best,W);history=[]
 for step in map(F,['1/100','1/1000','1/10000','1/100000','1/1000000','1/10000000']):
  for iteration in range(8):
   chosen=pose;value=best
   for delta in product((-1,0,1),repeat=3):
    if delta==(0,0,0):continue
    trial=tuple(a+step*b for a,b in zip(pose,delta));mass=evaluate(trial)
    if mass is not None and mass<value:value=mass;chosen=trial
   if chosen==pose:break
   pose,best=chosen,value;history.append(dict(step=str(step),pose=list(map(str,pose)),score=str(F(best,W))))
 poly=square(*pose[:2],F(1),pose[2]);assert all(0<=x<=L and 0<=y<=L for x,y in poly)
 exact=sum((F(m,W) for x,y,m in pts if contains(poly,(F(x)*L/span,F(y)*L/span))),F(0));assert exact==F(best,W)
 mass=F(sum(m for x,y,m in pts),best)
 return dict(source_sha256=data['sha256'],L=str(L),source_witness=w,initial_score=str(initial_score),minimum=dict(cx=str(pose[0]),cy=str(pose[1]),t=str(pose[2]),score=str(exact)),evaluations=count,history=history,uniform_rescale_mass=str(mass),above_21=mass>21,minimum_polygon_replayed=True,general_coverage_verified=False)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('certificate',type=Path);p.add_argument('prior',type=Path);p.add_argument('out',type=Path);p.add_argument('--index',type=int,default=1);a=p.parse_args();assert not a.out.exists();r=run(a.certificate,a.prior,a.index);a.out.write_text(json.dumps(r,indent=2));print(r['minimum'],r['evaluations'],float(F(r['uniform_rescale_mass'])))
