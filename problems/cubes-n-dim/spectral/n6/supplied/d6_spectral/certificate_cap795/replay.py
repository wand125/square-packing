"""Producer-side replay: Python standard library and exact arithmetic only."""
from fractions import Fraction as F
from itertools import combinations
from math import comb
import json,time
from spectral_bound import sqrt_bounds,certify_witness
BITS=60
PAIR=list(combinations(range(6),2))
M=[F(1,2),F(1,4),F(1,8),F(9,256),F(6,1024)]
def product(xs):
 v=F(1)
 for x in xs:v*=x
 return v
def root(x,n):
 assert x>=0
 if not x:return F(0)
 Q=(x.numerator << (n*BITS))//x.denominator
 r=1<<((Q.bit_length()+n-1)//n)
 while True:
  t=((n-1)*r+Q//r**(n-1))//n
  if t>=r:break
  r=t
 while (r+1)**n<=Q:r+=1
 while r**n>Q:r-=1
 z=F(r,1<<BITS)
 assert z**n<=x<(z+F(1,1<<BITS))**n
 return z

def main():
 start=time.time()
 with open('certificate.json') as f:c=json.load(f)
 V=[tuple(map(F,p)) for p in c['vertices']]
 expected=[]
 for k in range(1,6):
  for a in (F(13,20),F(159,200)):expected.append(tuple([a]+[(1-a)/k]*k+[F(0)]*(5-k)))
 assert V[:10]==expected
 initial=[tuple(list(range(2*k,10,2))+list(range(1,2*k+2,2))) for k in range(5)]
 assert [tuple(s) for s in c['initial']]==initial
 assert len(V)==len(c['spectral_witnesses'])
 facets=[tuple(map(F,a)) for a in c['facets']]
 for a in facets:
  assert len(a)==5 and min(a)>=0
  for m in range(1,6):assert sum(a[k-1]*F(comb(m,k),m**(2*k)) for k in range(1,m+1))<=1
 coeff=[]
 for w in c['tangents']:
  a=facets[w['facet']];t=list(map(F,w['t']));b=list(map(F,w['coeff']))
  assert len(t)==len(b)==5 and min(t)>=0 and min(b)>=0
  d=1+sum((2*k-1)*a[k-1]*t[k-1]**(2*k) for k in range(1,6))
  assert all(b[k-1]<=2*k*a[k-1]*t[k-1]**(2*k-1)/d for k in range(1,6))
  coeff.append(b)
 data=[]
 for i,p in enumerate(V):
  assert len(p)==6 and sum(p)==1 and min(p)>=0 and F(13,20)<=p[0]<=F(159,200)
  assert all(p[j]>=p[j+1] for j in range(5))
  roots=[sqrt_bounds(x,BITS) for x in p];target=2*sum(x[1] for x in roots)-2
  q=certify_witness(p,[[F(x) for x in row] for row in c['spectral_witnesses'][i]])
  R=sum(sorted(p[a]*p[b] for a,b in PAIR)[:10])
  E=[sum(product(p[j] for j in I) for I in combinations(range(6),k+1)) for k in range(1,6)]
  H=[root((k+1)*E[k-1]/M[k-1],2*k) for k in range(1,6)]
  pe=sum(product(p[j] for j in I)*(1-sum(p[j] for j in I)) for I in combinations(range(5),4))
  base=[q+R/2,q+(sqrt_bounds(1+18*R,BITS)[0]-1)/9,5*H[4]-target,8*root((p[4]+p[5])*product(p[:4]),8)-target,4*root(F(256,5)*pe,8)-target]
  data.append((roots,target,H,base))
  if i%10000==0:print('vertices',i,flush=True)
 cache={};stack=list(initial);leaves=0;minimum=None;types=[0]*6
 for number,rec in enumerate(c['records']):
  assert stack
  s=stack.pop()
  if rec[0]=='split':
   _,a,b,m=rec
   assert 0<=a<6 and 0<=b<6 and a!=b and 0<=m<len(V)
   assert V[m]==tuple((x+y)/2 for x,y in zip(V[s[a]],V[s[b]]))
   s1=list(s);s2=list(s);s1[a]=m;s2[b]=m;stack.extend([tuple(s1),tuple(s2)])
  else:
   assert rec[0]=='leaf' and rec[1] in range(6)
   typ=rec[1];loss=F(0);width=[]
   for k in range(6):
    i=min(s,key=lambda i:V[i][k]);j=max(s,key=lambda i:V[i][k]);width.append(V[j][k]-V[i][k])
    if V[i][k]!=V[j][k]:
     al,au=data[i][0][k];bl,bu=data[j][0][k];loss+=(bu-al)**2/(2*(bl+al))
   err=sum(width[a]*width[b] for a,b in PAIR)
   if typ<5:
    assert len(rec)==2
    z=min(data[i][3][typ] for i in s)-loss-(err/8 if typ==0 else err/4 if typ==1 else 0)
   else:
    assert len(rec)==3 and 0<=rec[2]<len(coeff)
    w=rec[2]
    for i in s:
     if (i,w) not in cache:cache[i,w]=sum(a*b for a,b in zip(coeff[w],data[i][2]))-data[i][1]
    z=min(cache[i,w] for i in s)-loss
   assert z>0,(number,z)
   minimum=z if minimum is None else min(minimum,z);leaves+=1;types[typ]+=1
  if number%500000==0:print('records',number,flush=True)
 assert not stack
 result={'status':'VERIFIED','vertices':len(V),'nodes':len(c['records']),'leaves':leaves,'types':types,'min_slack':str(minimum),'seconds':time.time()-start}
 with open('replay_result.json','w') as f:json.dump(result,f,indent=2)
 print(json.dumps(result,indent=2),flush=True)
if __name__=='__main__':main()
