"""Independent exact verifier. No producer modules, numpy or numeric eigensolvers."""
import json, sys, time, hashlib
from fractions import Fraction as Q
from itertools import combinations
from math import comb, factorial
from pathlib import Path
START=time.time()
SOURCE=Path(sys.argv[1]) if len(sys.argv)>1 else Path('../d6_spectral/certificate_cap795/certificate.json')
c=json.loads(SOURCE.read_text())
v=[tuple(map(Q,p)) for p in c['vertices']]
assert all(len(p)==6 and sum(p)==1 and Q(13,20)<=p[0]<=Q(159,200) and all(p[i]>=p[i+1]>=0 for i in range(5)) for p in v)

def det(a):
 a=[list(r) for r in a]; out=Q(1)
 for i in range(len(a)):
  j=next((j for j in range(i,len(a)) if a[j][i]),None)
  if j is None:return Q(0)
  if j!=i:a[i],a[j]=a[j],a[i];out=-out
  d=a[i][i];out*=d
  for j in range(i+1,len(a)):
   t=a[j][i]/d
   for k in range(i+1,len(a)):a[j][k]-=t*a[i][k]
 return out

def orientation(s):return det([[v[s[j]][i]-v[s[0]][i] for i in range(5)] for j in range(1,6)])
expected=[]
for k in range(2,7):
 for a in [Q(13,20),Q(159,200)]:expected.append(tuple([a]+[(1-a)/(k-1)]*(k-1)+[Q(0)]*(6-k)))
assert v[:10]==expected
initial=[tuple(s) for s in c['initial']]
assert initial==[tuple(list(range(2*k,10,2))+list(range(1,2*k+2,2))) for k in range(5)]
# Oriented chain boundary cancellation: all exposed faces must lie on frustum boundary.
faces={};volume=Q(0)
for s in initial:
 d=orientation(s);assert d;volume+=abs(d)/factorial(5)
 for j in range(6):
  face=s[:j]+s[j+1:]; inv=sum(face[a]>face[b] for a in range(5) for b in range(a+1,5))
  key=tuple(sorted(face));faces[key]=faces.get(key,0)+(1 if d>0 else -1)*(-1)**(j+inv)
for f,n in faces.items():
 if not n:continue
 assert abs(n)==1
 assert (all(v[i][0]==Q(13,20) for i in f) or all(v[i][0]==Q(159,200) for i in f) or all(v[i][5]==0 for i in f) or any(all(v[i][j]==v[i][j+1] for i in f) for j in range(1,5)))
# Sorted tail cone volume: full tail simplex volume divided by 5!, then integrate p1.
assert volume==((1-Q(13,20))**5-(1-Q(159,200))**5)/(factorial(5)**2)
print('initial frustum chain and exact volume PASS',flush=True)

def root(x,n,bits):
 assert x>=0
 scaled=(x.numerator<<(n*bits))//x.denominator
 lo=0;hi=1<<((scaled.bit_length()+n-1)//n)
 while hi-lo>1:
  m=(lo+hi)//2
  if m**n<=scaled:lo=m
  else:hi=m
 if hi**n<=scaled:lo=hi
 l=Q(lo,1<<bits);u=l if l**n==x else Q(lo+1,1<<bits)
 assert l**n<=x<=u**n
 return l,u

def prod(xs):
 z=Q(1)
 for x in xs:z*=x
 return z
facets=[tuple(map(Q,a)) for a in c['facets']]
for a in facets:
 assert len(a)==5 and all(x>=0 for x in a)
 for m in range(1,6):assert sum(a[k-1]*Q(comb(m,k),m**(2*k)) for k in range(1,m+1))<=1
weights=[]
for w in c['tangents']:
 a=facets[w['facet']];t=list(map(Q,w['t']));b=list(map(Q,w['coeff']))
 assert len(t)==len(b)==5 and all(x>=0 for x in t+b)
 D=1+sum((2*k-1)*a[k-1]*t[k-1]**(2*k) for k in range(1,6))
 for k in range(1,6):
  exact=2*k*a[k-1]*t[k-1]**(2*k-1)/D
  assert b[k-1]==Q((exact.numerator*(1<<40))//exact.denominator,1<<40)
 weights.append(b)
print('facets and rational Young coefficients PASS',flush=True)
PAIRS=list(combinations(range(6),2));data=[]
# Maximal forest squared volumes, separately derived by balanced component sizes.
M=[]
for k in range(1,6):
 nc=6-k; small,rem=divmod(6,nc);M.append(Q(small**(nc-rem)*(small+1)**rem,4**k))
assert len(c['spectral_witnesses'])==len(v)
for idx,p in enumerate(v):
 A=[list(map(Q,row)) for row in c['spectral_witnesses'][idx]]
 assert len(A)==6 and all(len(row)==6 for row in A) and all(A[i][j]==A[j][i] for i in range(6) for j in range(6))
 residual=max(sum(abs((p[i] if i==j else 0)-p[i]*p[j]-sum(A[i][k]*A[k][j] for k in range(6))) for j in range(6)) for i in range(6))
 trace=max(Q(0),sum(A[i][i] for i in range(6))-6*root(residual,2,100)[1])
 q=root(Q(2),2,100)[0]*trace-2*sum(root(x,2,100)[1] for x in p)+2
 roots=[root(x,2,60) for x in p];target=2*sum(u for l,u in roots)-2
 R=sum(sorted(p[i]*p[j] for i,j in PAIRS)[:10])
 H=[]
 for k in range(1,6):
  e=sum(prod(p[j] for j in inds) for inds in combinations(range(6),k+1))
  H.append(root((k+1)*e/M[k-1],2*k,60)[0])
 proj=sum(prod(p[j] for j in inds)*(1-sum(p[j] for j in inds)) for inds in combinations(range(5),4))
 values=[q+R/2,q+(root(1+18*R,2,60)[0]-1)/9,5*H[4]-target,8*root((p[4]+p[5])*prod(p[:4]),8,60)[0]-target,4*root(Q(256,5)*proj,8,60)[0]-target]
 data.append((roots,values,H,target))
 if idx%1000==0:print('vertices',idx,'seconds',round(time.time()-START,2),flush=True)
stack=list(initial);counts=[0]*6;minimum=None;used=set(range(10));wc={}
for node,rec in enumerate(c['records']):
 assert stack,'extra record'
 s=stack.pop();assert len(set(s))==6
 if rec[0]=='split':
  assert len(rec)==4
  _,a,b,m=rec;assert 0<=a<6 and 0<=b<6 and a!=b and 0<=m<len(v)
  assert v[m]==tuple((v[s[a]][i]+v[s[b]][i])/2 for i in range(6))
  used.add(m);sa=list(s);sb=list(s);sa[a]=m;sb[b]=m;stack.extend([tuple(sa),tuple(sb)])
 else:
  assert rec[0]=='leaf';typ=rec[1];assert 0<=typ<=5
  loss=Q(0);width=[]
  for k in range(6):
   low=min(s,key=lambda i:v[i][k]);high=max(s,key=lambda i:v[i][k]);width.append(v[high][k]-v[low][k])
   if low==high or v[low][k]==v[high][k]:continue
   al,au=data[low][0][k];bl,bu=data[high][0][k]
   loss+=(bu-al)**2/(2*(bl+al))
  if typ<5:
   assert len(rec)==2;slack=min(data[i][1][typ] for i in s)-loss
   if typ<2:slack-=sum(width[i]*width[j] for i,j in PAIRS)/(8 if typ==0 else 4)
  else:
   assert len(rec)==3;wid=rec[2];w=weights[wid]
   for i in s:
    if (i,wid) not in wc:wc[i,wid]=sum(w[k]*data[i][2][k] for k in range(5))-data[i][3]
   slack=min(wc[i,wid] for i in s)-loss
  assert slack>0,(node,rec,slack)
  minimum=slack if minimum is None else min(minimum,slack);counts[typ]+=1
 if node%20000==0:print('nodes',node,'remaining',len(stack),'seconds',round(time.time()-START,2),flush=True)
assert not stack,'unexhausted subtrees'
assert used==set(range(len(v))), 'unused vertices'
result={'certificate_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),'status':'PASS','vertices':len(v),'nodes':len(c['records']),'leaf_types':counts,'leaves':sum(counts),'min_slack':str(minimum),'seconds':time.time()-START}
print(json.dumps(result,indent=2),flush=True)
Path('result.json').write_text(json.dumps(result,indent=2))
