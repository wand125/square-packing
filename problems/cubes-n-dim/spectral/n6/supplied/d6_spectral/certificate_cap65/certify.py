"""Exact rational simplex certificate for the capped d=6 corrected covariance inequality.
Floating arithmetic is used only to choose subdivision edges and propose the
spectral witness; all acceptance decisions are verified using Fractions.
"""
from fractions import Fraction as F
from math import isqrt
import time,json
import numpy as np
from spectral_bound import spectral_q_lower
BITS=48
D=1<<BITS

def sqrt_bounds(x):
    assert x>=0
    k=isqrt((x.numerator<<(2*BITS))//x.denominator)
    a=F(k,D)
    return (a,a) if a*a==x else (a,F(k+1,D))

v=[]
for k in range(2,7):
    v.append(tuple([F(1,k)]*k+[F(0)]*(6-k)))
    v.append(tuple([F(13,20)]+[F(7,20*(k-1))]*(k-1)+[F(0)]*(6-k)))
initial=[tuple(list(range(2*k,10,2))+list(range(1,2*k+2,2))) for k in range(5)]
lookup={p:i for i,p in enumerate(v)}
q={}; roots={}; numeric={}; witnesses={}
sqrt2lo=sqrt_bounds(F(2))[0]
def ensure(i):
    if i not in q:
        p=v[i]
        roots[i]=[sqrt_bounds(z) for z in p]
        numeric[i]=np.sqrt(np.array(p,dtype=float))
        q[i], witness=spectral_q_lower(p, return_witness=True)
        witnesses[i]=witness["A"]
        q[i]+=sum(sorted(p[a]*p[b] for a in range(6) for b in range(a+1,6))[:10])/2

def loss(simplex):
    total=F(0)
    for k in range(6):
        i=min(simplex,key=lambda i:v[i][k]);j=max(simplex,key=lambda i:v[i][k])
        if v[j][k]==v[i][k]:continue
        al,au=roots[i][k];bl,bu=roots[j][k]
        total+=(bu-al)**2/(2*(bl+al))
    widths=[max(v[i][k] for i in simplex)-min(v[i][k] for i in simplex) for k in range(6)]
    total+=sum(widths[a]*widths[b] for a in range(6) for b in range(a+1,6))/8
    return total

def main():
    start=time.time();stack=[(s,0) for s in initial]
    checked=leaves=maxdepth=0;minslack=None;records=[]
    while stack:
        simplex,depth=stack.pop();checked+=1;maxdepth=max(maxdepth,depth)
        for i in simplex:ensure(i)
        slack=min(q[i] for i in simplex)-loss(simplex)
        if slack>0:
            records.append(None)
            leaves+=1;minslack=slack if minslack is None else min(minslack,slack)
            continue
        arr=np.array([numeric[i] for i in simplex]);dist=np.sum((arr[:,None,:]-arr[None,:,:])**2,axis=2)
        a,b=np.unravel_index(dist.argmax(),dist.shape);i,j=simplex[a],simplex[b]
        mid=tuple((x+y)/2 for x,y in zip(v[i],v[j]))
        m=lookup.get(mid)
        if m is None:m=len(v);v.append(mid);lookup[mid]=m
        records.append([int(a),int(b),int(m)])
        s1=list(simplex);s2=list(simplex);s1[a]=m;s2[b]=m
        stack.extend([(tuple(s1),depth+1),(tuple(s2),depth+1)])
        if checked%10000==0:print('progress',checked,len(v),leaves,flush=True)
        assert depth<100,'Unexpected certificate depth'
    result={'status':'VERIFIED','arithmetic':'exact rational acceptance','simplices_checked':checked,'leaves':leaves,'vertices':len(v),'max_depth':maxdepth,'min_vertex_q_lower':float(min(q.values())),'min_leaf_slack_lower':float(minslack),'elapsed_seconds':time.time()-start}
    print(json.dumps(result,indent=2),flush=True)
    result['min_leaf_slack_exact']=str(minslack)
    with open('result.json','w') as f:json.dump(result,f,indent=2)
    artifact={'initial':initial,'vertices':[[str(x) for x in p] for p in v],'witnesses':[[[str(x) for x in row] for row in witnesses[i]] for i in range(len(v))],'records':records}
    with open('certificate.json','w') as f:json.dump(artifact,f,separators=(',',':'))
if __name__=='__main__':main()
