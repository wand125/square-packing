#!/usr/bin/env python3
"""Independent floating sampling of every scalar in the amended rule paths."""
import json, time
import numpy as np
from validate import Checker, box, pose

def quantities(v,y):
    r,c=pose(v); t=r.T@(y-c); out=list(t)
    for w in range(3):
        z=y.copy();z[w]+=1;out.extend(r.T@(z-c))
        for k in range(3):
            out.extend([r[w,k],abs(r[w,k])])
            for j in range(3):
                if j!=k:out.append(r[w,k]*t[j]-r[w,j]*t[k])
        h=np.abs(r[w]).sum()/2;span=3-2*h
        out.extend([1-y[w]+v[w+3]*span,y[w]-2+(1-v[w+3])*span])
        out.extend(abs(r[w,j])+abs(t[j]) for j in range(3))
    return np.array(out)

def run():
    start=time.monotonic();rng=np.random.default_rng(11001);check=Checker(6);count=0;failures=[]
    # 1,000 boxes, ten samples each. Include Clarke crossings, walls, point boxes,
    # endpoint samples and cells with exactly representable centres.
    for i in range(1000):
        v=np.r_[rng.uniform(-.4,.4,3),rng.uniform(0,1,3)]
        if i%4==0:v[:3]=0
        if i%4==1:v[3:]=rng.choice([0.,1.],3)
        b=box(v,0 if i%10==0 else 10**rng.uniform(-6,-.5))
        lo=np.array([q['lo'] for q in b]);hi=np.array([q['hi'] for q in b])
        y=rng.uniform(0,3,3);width=rng.uniform(0,.2,3)
        cy=box(y,width); enc=check.query(b,enclosures=cy)['quantities']
        elo=np.array([q['lo'] for q in enc]);ehi=np.array([q['hi'] for q in enc])
        for j in range(10):
            p=lo if j==0 else hi if j==1 else np.clip(lo+(hi-lo)*rng.random(6),lo,hi)
            yl=np.array([q['lo'] for q in cy]);yh=np.array([q['hi'] for q in cy])
            yy=yl if j==0 else yh if j==1 else np.clip(yl+(yh-yl)*rng.random(3),yl,yh)
            q=quantities(p,yy)
            # No tolerance: sampled floating evaluation must be contained.
            if np.any(q<elo) or np.any(q>ehi):failures.append(dict(box=i,sample=j,indices=np.flatnonzero((q<elo)|(q>ehi)).tolist()))
            count+=1
    check.close()
    report=dict(samples_per_quantity=count,quantities=len(enc),random_boxes=1000,failures=failures,seconds=time.monotonic()-start)
    open('validation/a1.json','w').write(json.dumps(report,indent=2)+'\n');print(json.dumps(report));assert not failures
if __name__=='__main__':run()
