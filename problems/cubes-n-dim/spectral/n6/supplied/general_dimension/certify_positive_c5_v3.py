from pathlib import Path
"""Exact positive C5 certificate using fixed rational pair allocations.
Floating point proposes allocations only. Acceptance is rational at all vertices.
"""
from fractions import Fraction as F
from math import isqrt,sqrt,hypot
import json,time,gzip
BITS=48;SCALE=1<<BITS

def sqrtup(x):
 k=isqrt((x.numerator*SCALE*SCALE)//x.denominator);lo=F(k,SCALE)
 return lo if lo*lo==x else F(k+1,SCALE)

def proposal(v):
 n=5;S=sum(v);N=sqrt(sum(x*x for x in v));t=S-N
 candidates=[]
 # Constant-demand rows, normalized pairwise; valid only if exact check passes.
 r=[t/(S-x) for x in v]
 C=[[0.]*n for _ in range(n)]
 for i in range(n):
  for j in range(i):
   den=hypot(r[i],r[j]);C[i][j]=r[i]/den;C[j][i]=r[j]/den
 candidates.append(C)
 # One-parameter positive allocations, all with exact pair capacity in real arithmetic.
 s=sqrt(sum(x*x for x in v[1:]))
 for l in (s,.5*s,2*s):
  C=[[0.]*n for _ in range(n)]
  for i in range(n):
   for j in range(i):
    den=hypot(v[i]+l,v[j]+l);C[i][j]=(v[i]+l)/den;C[j][i]=(v[j]+l)/den
  candidates.append(C)
 for h in (2,3,4):
  R=sum(v[h:]);H=sum(v[:h]);A=[max(0,(t-(H-v[i])/sqrt(2))/R) for i in range(h)]
  if max(A)>1:continue
  C=[[0. if i==j else 1/sqrt(2) for j in range(n)] for i in range(n)]
  for i in range(h):
   for j in range(h,n):C[i][j]=A[i];C[j][i]=sqrt(1-A[i]*A[i])
  candidates.append(C)
 best=max(candidates,key=lambda C:min(sum(v[j]*C[i][j] for j in range(n))-t for i in range(n)))
 C=[[F(0)]*n for _ in range(n)]
 for i in range(n):
  for j in range(i):
   # Rational unit-circle parametrization; both entries nonnegative.
   q=F(max(0,min(1000000,round(1000000*best[j][i]/(1+best[i][j])))),1000000)
   C[i][j]=(1-q*q)/(1+q*q);C[j][i]=2*q/(1+q*q)
 return C

def certify(V):
 if sum(max(p[i] for p in V)**2 for i in range(4))<=F(1,100):return 'near_axis'
 W=[(F(1),)+p for p in V];m=[sum(p[i] for p in W)/5 for i in range(5)];M=sqrtup(sum(x*x for x in m))
 C=proposal([float(x) for x in m]);d=[x/M for x in m]
 for i in range(5):
  coeff=[d[j]+C[i][j]-1 for j in range(5)]
  if any(sum(coeff[j]*p[j] for j in range(5))<0 for p in W):return None
 return 'fixed_rational_flow'

def run(limit=10000000):
 V=tuple(tuple(F(int(i<j)) for i in range(4)) for j in range(5));stack=[(V,0)];counts={};splits=0;depth=0;start=time.time();records=[]
 while stack:
  V,d=stack.pop();kind=certify(V)
  if kind:
   counts[kind]=counts.get(kind,0)+1;depth=max(depth,d)
   if kind=='near_axis':records.append(['a'])
   else:
    W=[(F(1),)+p for p in V];m=[sum(p[i] for p in W)/5 for i in range(5)];C=proposal([float(x) for x in m])
    records.append(['f',[str(C[j][i]/(1+C[i][j])) for i in range(5) for j in range(i)]])
   continue
  if splits>=limit:print('INCOMPLETE',splits,len(stack),counts,flush=True);return
  _,i,j=max((sum((V[i][k]-V[j][k])**2 for k in range(4)),i,j) for i in range(5) for j in range(i))
  records.append(["s",i,j])
  mid=tuple((V[i][k]+V[j][k])/2 for k in range(4));A=list(V);B=list(V);A[i]=mid;B[j]=mid
  stack.append((tuple(A),d+1));stack.append((tuple(B),d+1));splits+=1
  if splits%10000==0:print('progress',splits,len(stack),counts,round(time.time()-start,1),flush=True)
 out={'verified':True,'splits':splits,'leaves':counts,'maximum_depth':depth,'sqrt_bits':BITS,'seconds':time.time()-start}
 with gzip.open(Path(__file__).with_name('positive_c5_exact_tree.json.gz'),'wt') as f:json.dump(records,f,separators=(',',':'))
 print(json.dumps(out),flush=True)
 with open(Path(__file__).with_name('positive_c5_certificate_v3_result.json'),'w') as f:json.dump(out,f,indent=2)
if __name__=='__main__':run()
