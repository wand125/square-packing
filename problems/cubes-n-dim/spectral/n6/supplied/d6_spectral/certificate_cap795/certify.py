"""Exact rational far-region certificate; numerical work only proposes splits/witnesses."""
from fractions import Fraction as F
from itertools import combinations
from math import comb,isqrt
import numpy as np
import json,time
from spectral_bound import spectral_q_lower,sqrt_bounds
BITS=60;SCALE=1<<BITS;CBITS=40;CSCALE=1<<CBITS
N=6;CAP=F(159,200)
PAIR=list(combinations(range(N),2))
SUB={r:list(combinations(range(N),r)) for r in range(2,7)}
M=[F(1,2),F(1,4),F(1,8),F(9,256),F(6,1024)]
with open('../../d6_exterior_audit/facets.json') as f: raw=json.load(f)
FACETS=[tuple(F(x) for x in v['a']) for v in raw['facets'] if any(F(x) for x in v['a'])]
FACNUM=np.array(FACETS,dtype=float)
for aa in FACETS:
 assert all(x>=0 for x in aa)
 assert all(sum(aa[k-1]*F(comb(m,k),m**(2*k)) for k in range(1,m+1))<=1 for m in range(1,6))

def product(xs):
 v=F(1)
 for x in xs:v*=x
 return v

def root_bounds(x,n,bits=BITS):
 if x==0:return F(0),F(0)
 Q=(x.numerator << (n*bits))//x.denominator
 r=1<<((Q.bit_length()+n-1)//n)
 while True:
  t=((n-1)*r+Q//(r**(n-1)))//n
  if t>=r:break
  r=t
 while (r+1)**n<=Q:r+=1
 while r**n>Q:r-=1
 lo=F(r,1<<bits)
 return lo,lo if lo**n==x else F(r+1,1<<bits)

V=[]
for k in range(2,7):
 V.append(tuple([F(13,20)]+[F(7,20*(k-1))]*(k-1)+[F(0)]*(6-k)))
 V.append(tuple([CAP]+[(1-CAP)/(k-1)]*(k-1)+[F(0)]*(6-k)))
INITIAL=[tuple(list(range(2*k,10,2))+list(range(1,2*k+2,2))) for k in range(5)]
lookup={p:i for i,p in enumerate(V)};data={};A={};W=[];wlookup={};wcaches=[]

def ensure(i):
 if i in data:return
 p=V[i];roots=[sqrt_bounds(x,BITS) for x in p];target=2*sum(x[1] for x in roots)-2
 q,w=spectral_q_lower(p,return_witness=True);A[i]=w['A']
 R=sum(sorted(p[a]*p[b] for a,b in PAIR)[:10]);edge1=q+R/2;edge2=q+(sqrt_bounds(1+18*R,BITS)[0]-1)/9
 E=[sum(product(p[j] for j in I) for I in SUB[k+1]) for k in range(1,6)]
 H=[root_bounds(F(k+1)*E[k-1]/M[k-1],2*k)[0] for k in range(1,6)]
 group=8*root_bounds((p[4]+p[5])*product(p[:4]),8)[0]-target
 det=5*H[4]-target
 projE=sum(product(p[j] for j in I)*(1-sum(p[j] for j in I)) for I in combinations(range(5),4))
 proj=4*root_bounds(F(256,5)*projE,8)[0]-target
 data[i]={'roots':roots,'target':target,'H':H,'base':(edge1,edge2,det,group,proj),'num':np.sqrt(np.array(p,dtype=float))}

def witness(simplex):
 p=np.mean(np.array([V[i] for i in simplex],dtype=float),axis=0)
 L=2*np.sqrt(p).sum()-2
 E=[sum(np.prod(p[list(I)]) for I in SUB[k+1]) for k in range(1,6)]
 H=np.array([(float(k+1)*E[k-1]/float(M[k-1]))**(1/(2*k)) for k in range(1,6)])
 tt=H/max(L,1e-9)
 score=FACNUM@(tt**np.arange(2,11,2));aid=int(score.argmax())
 if score[aid]<.99:return None
 # Coarse reusable exact tangent proposals. Rounding is not used for acceptance.
 t=tuple(F(max(0,int(round(x*64))),64) for x in tt)
 key=(aid,t)
 if key in wlookup:return wlookup[key]
 aa=FACETS[aid];den=1+sum((2*k-1)*aa[k-1]*t[k-1]**(2*k) for k in range(1,6))
 coeff=[]
 for k in range(1,6):
  c=2*k*aa[k-1]*t[k-1]**(2*k-1)/den
  coeff.append(F((c.numerator*CSCALE)//c.denominator,CSCALE))
 wid=len(W);W.append({'facet':aid,'t':t,'coeff':tuple(coeff)});wlookup[key]=wid;wcaches.append({})
 return wid

def wvalue(i,wid):
 cache=wcaches[wid]
 if i not in cache:cache[i]=sum(x*y for x,y in zip(W[wid]['coeff'],data[i]['H']))-data[i]['target']
 return cache[i]

def losses(s):
 loss=F(0);width=[]
 for k in range(6):
  i=min(s,key=lambda i:V[i][k]);j=max(s,key=lambda i:V[i][k]);width.append(V[j][k]-V[i][k])
  if V[j][k]==V[i][k]:continue
  al,au=data[i]['roots'][k];bl,bu=data[j]['roots'][k]
  loss+=(bu-al)**2/(2*(bl+al))
 err=sum(width[a]*width[b] for a,b in PAIR)
 return loss,err

def main():
 start=time.time();stack=[(s,0,None) for s in INITIAL];records=[];leaves=checked=maxdepth=0;slackmin=None;types=[0]*6
 while stack:
  s,depth,inherited=stack.pop();checked+=1;maxdepth=max(maxdepth,depth)
  for i in s:ensure(i)
  loss,err=losses(s);accepted=None;slack=None
  for typ,extra in [(0,err/8),(1,err/4),(2,F(0)),(3,F(0)),(4,F(0))]:
   z=min(data[i]['base'][typ] for i in s)-loss-extra
   if z>0:accepted=['leaf',typ];slack=z;break
  wid=inherited
  if accepted is None and wid is not None:
   z=min(wvalue(i,wid) for i in s)-loss
   if z>0:accepted=['leaf',5,wid];slack=z
  if accepted is None:
   candidate=witness(s)
   if candidate is not None:
    wid=candidate;z=min(wvalue(i,wid) for i in s)-loss
    if z>0:accepted=['leaf',5,wid];slack=z
  if accepted is not None:
   leaves+=1;types[accepted[1]]+=1;records.append(accepted);slackmin=slack if slackmin is None else min(slackmin,slack)
  else:
   arr=np.array([data[i]['num'] for i in s]);dist=np.sum((arr[:,None,:]-arr[None,:,:])**2,axis=2);a,b=map(int,np.unravel_index(dist.argmax(),dist.shape));i,j=s[a],s[b]
   mid=tuple((x+y)/2 for x,y in zip(V[i],V[j]));m=lookup.get(mid)
   if m is None:m=len(V);V.append(mid);lookup[mid]=m
   records.append(['split',a,b,m]);s1=list(s);s2=list(s);s1[a]=m;s2[b]=m;stack.extend([(tuple(s1),depth+1,wid),(tuple(s2),depth+1,wid)])
   assert depth<100,('depth',depth,[list(map(float,V[i])) for i in s])
  if checked%10000==0:print('progress',checked,'vertices',len(V),'leaves',leaves,'stack',len(stack),'witnesses',len(W),'types',types,'sec',time.time()-start,flush=True)
 result={'status':'VERIFIED','nodes':checked,'leaves':leaves,'vertices':len(V),'depth':maxdepth,'min_slack':str(slackmin),'min_slack_float':float(slackmin),'types':types,'tangents':len(W),'seconds':time.time()-start}
 print(json.dumps(result,indent=2),flush=True)
 with open('result.json','w') as f:json.dump(result,f,indent=2)
 cert={'initial':INITIAL,'vertices':[[str(x) for x in p] for p in V],'spectral_witnesses':[[[str(x) for x in row] for row in A[i]] for i in range(len(V))],'facets':[[str(x) for x in a] for a in FACETS],'tangents':[{'facet':w['facet'],'t':[str(x) for x in w['t']],'coeff':[str(x) for x in w['coeff']]} for w in W],'records':records}
 with open('certificate.json','w') as f:json.dump(cert,f,separators=(',',':'))
if __name__=='__main__':main()
