"""PL37: exact minimum point capture over every centre at one rational angle.
A sweep over open arrangement cells handles closed capture by nonnegativity.
"""
from fractions import Fraction as F
from bisect import bisect_left,bisect_right
from pathlib import Path
import argparse,json,hashlib,time
from probe_external_integer_bridge import read
from score import square,contains

class RangeMin:
 def __init__(self,n):
  assert n>0;self.n=n;self.value=[0]*(4*n);self.lazy=[0]*(4*n);self.arg=[0]*(4*n);self._build(1,0,n-1)
 def _build(self,k,l,r):
  self.arg[k]=l
  if l<r:
   m=(l+r)//2;self._build(2*k,l,m);self._build(2*k+1,m+1,r)
 def add(self,l,r,w):
  assert 0<=l<=r<self.n;self._add(1,0,self.n-1,l,r,w)
 def _add(self,k,l,r,a,b,w):
  if a<=l and r<=b:self.value[k]+=w;self.lazy[k]+=w;return
  m=(l+r)//2
  if a<=m:self._add(2*k,l,m,a,b,w)
  if b>m:self._add(2*k+1,m+1,r,a,b,w)
  child=min((2*k,2*k+1),key=lambda j:(self.value[j],self.arg[j]));self.value[k]=self.lazy[k]+self.value[child];self.arg[k]=self.arg[child]
 def query(self,l,r):
  assert 0<=l<=r<self.n;return self._query(1,0,self.n-1,l,r,0)
 def _query(self,k,l,r,a,b,carry):
  if a<=l and r<=b:return self.value[k]+carry,self.arg[k]
  carry+=self.lazy[k];m=(l+r)//2;values=[]
  if a<=m:values.append(self._query(2*k,l,m,a,b,carry))
  if b>m:values.append(self._query(2*k+1,m+1,r,a,b,carry))
  return min(values)

def projection(poly,u0,u1):
 values=[v for u,v in poly if u0<=u<=u1]
 for (a,b),(c,d) in zip(poly,poly[1:]+poly[:1]):
  if a==c:continue
  for edge in (u0,u1):
   if min(a,c)<=edge<=max(a,c):values.append(b+(d-b)*(edge-a)/(c-a))
 if not values:return None
 return min(values),max(values)

def separate(L,D,points,t,extra_bins=0,violation_threshold=None,levels_per_bin=1):
 if levels_per_bin<1:raise ValueError("Need positive levels per bin")
 if extra_bins<0 or (extra_bins and violation_threshold is None):raise ValueError("Extra bins require a threshold")
 L,t=F(L),F(t)
 if not 0<=t<=F(1,2):raise ValueError('Use 0 <= half-angle <= 1/2')
 if any(w<0 for x,y,w in points):raise ValueError('Negative point mass')
 p,q=t.numerator,t.denominator;a=q*q-p*p;b=2*p*q;r=q*q+p*p;h=F(a+b,2*r)
 if L<=2*h:raise ValueError('Needs a full-dimensional admissible centre domain')
 assert (L*D).denominator==1;span=int(L*D);H=D*r
 poly=[(2*D*(a*x+b*y),2*D*(-b*x+a*y)) for x,y in [(h,h),(L-h,h),(L-h,L-h),(h,L-h)]]
 transformed=[(2*(a*x+b*y),2*(-b*x+a*y),w) for x,y,w in points if w]
 Umin,Umax=min(u for u,v in poly),max(u for u,v in poly);Vmin,Vmax=min(v for u,v in poly),max(v for u,v in poly)
 us=sorted({Umin,Umax}|{F(u+s*H) for u,v,w in transformed for s in (-1,1)});vs=sorted({Vmin,Vmax}|{F(v+s*H) for u,v,w in transformed for s in (-1,1)})
 events={}
 for u,v,w in transformed:
  lo=bisect_left(vs,v-H);hi=bisect_left(vs,v+H)-1
  events.setdefault(u-H,[]).append((lo,hi,w));events.setdefault(u+H,[]).append((lo,hi,-w))
 tree=RangeMin(len(vs)-1);best=None;strips=0;bin_best={}
 for u0,u1 in zip(us,us[1:]):
  for lo,hi,w in events.get(u0,[]):tree.add(lo,hi,w)
  if u1<=Umin or u0>=Umax:continue
  v0,v1=projection(poly,u0,u1)
  if v0>=v1:continue
  lo=bisect_right(vs,v0)-1;hi=bisect_left(vs,v1)-1;assert 0<=lo<=hi<len(vs)-1;mass,index=tree.query(lo,hi);strips+=1
  cell=(mass,u0,u1,max(vs[index],v0),min(vs[index+1],v1))
  if best is None or mass<best[0]:best=cell
  if extra_bins and mass<violation_threshold:
   bucket=min(extra_bins-1,int(((u0+u1)/2-Umin)*extra_bins/(Umax-Umin)))
   levels=bin_best.setdefault(bucket,{})
   levels.setdefault(mass,cell)
   if len(levels)>levels_per_bin:del levels[max(levels)]
 assert best is not None
 def recover(cell):
  mass,u0,u1,v0,v1=cell;v=(v0+v1)/2;low=D*r*(a+b);high=2*span*r*r-low
  left=max(u0,(low+b*v)/a);right=min(u1,(high+b*v)/a)
  if b:
   left=max(left,(low-a*v)/b);right=min(right,(high-a*v)/b)
  else:assert low<a*v<high
  assert left<right;u=(left+right)/2;cx=(a*u-b*v)/(2*D*r*r);cy=(b*u+a*v)/(2*D*r*r)
  assert h<cx<L-h and h<cy<L-h
  witness_poly=square(cx,cy,F(1),t);hits=tuple(i for i,(x,y,w) in enumerate(points) if contains(witness_poly,(F(x,D),F(y,D))))
  assert sum(points[i][2] for i in hits)==mass
  return dict(cx=str(cx),cy=str(cy),t=str(t)),hits
 witness,hits=recover(best)
 result=dict(t=str(t),minimum_numerator=best[0],witness=witness,u_strips=strips,u_boundaries=len(us),v_boundaries=len(vs),witness_polygon_replayed=True)
 if extra_bins:
  seen={hits};extras=[]
  for bucket,levels in sorted(bin_best.items()):
   for mass,cell in sorted(levels.items()):
    pose,captured=recover(cell)
    if captured in seen:continue
    seen.add(captured);extras.append(dict(bucket=bucket,minimum_numerator=mass,witness=pose,witness_polygon_replayed=True))
  result.update(extra_bins=extra_bins,levels_per_bin=levels_per_bin,extra_witnesses=extras)
 return result

def run(candidate,angles,out,extra_bins=0,levels_per_bin=1):
 assert not out.exists();L,span,W,pts=read(candidate);D=int(F(span)/L);records=[]
 for t in angles:
  start=time.monotonic();r=separate(L,D,pts,t,extra_bins=extra_bins,violation_threshold=W,levels_per_bin=levels_per_bin);r.update(minimum=str(F(r['minimum_numerator'],W)),seconds=time.monotonic()-start);records.append(r);print('angle',t,'global fixed-angle min',r['minimum'],'strips',r['u_strips'],'seconds',r['seconds'],flush=True)
 out.write_text(json.dumps(dict(status='EXACT_FIXED_ANGLE_CENTRE_MINIMA',candidate_sha256=hashlib.sha256(candidate.read_bytes()).hexdigest(),L=str(L),records=records,all_angles_verified=False),indent=2))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('candidate',type=Path);p.add_argument('out',type=Path);p.add_argument('angles',nargs='+');a=p.parse_args();run(a.candidate,list(map(F,a.angles)),a.out)
