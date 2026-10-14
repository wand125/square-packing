#!/usr/bin/env python3
"""Independent binary64 geometry reference. Tolerance is for testing only, never certification."""
import itertools, json, math, pathlib, subprocess, collections, time
import numpy as np
BASE=pathlib.Path(__file__).resolve().parent
EXE=BASE/'target/release/m5-checker'
S=2+1/math.sqrt(2)
V=np.array([[1+((p>>w)&1)/math.sqrt(2) for w in range(3)] for p in range(8)])

def rot(q):
    q=q/np.linalg.norm(q,axis=-1,keepdims=True)
    w,x,y,z=q.T
    return np.stack([1-2*(y*y+z*z),2*(x*y-w*z),2*(x*z+w*y),
                     2*(x*y+w*z),1-2*(x*x+z*z),2*(y*z-w*x),
                     2*(x*z-w*y),2*(y*z+w*x),1-2*(x*x+y*y)],axis=-1).reshape(-1,3,3)

def group():
    g=[]
    for i in range(4):
        for s in [-1,1]:
            a=np.zeros(4);a[i]=s;g.append(a)
    g.extend(np.array(v)/2 for v in itertools.product([-1,1],repeat=4))
    for i,j in itertools.combinations(range(4),2):
        for a,b in itertools.product([-1,1],repeat=2):
            v=np.zeros(4);v[i]=a/math.sqrt(2);v[j]=b/math.sqrt(2);g.append(v)
    return np.array(g)

def multiply(q,g):
    return np.column_stack([q[:,0]*g[0]-q[:,1:]@g[1:],
        q[:,0,None]*g[1:]+g[0]*q[:,1:]+np.cross(q[:,1:],g[1:])])

def reduce(q,c):
    # Enumerate actual right products, not coordinate folding alone.
    gs=group(); dots=q@np.column_stack([gs[:,0],-gs[:,1:]]).T
    idx=np.argmax(dots,axis=1);v=np.empty_like(q)
    for i,g in enumerate(gs):
        mask=idx==i;v[mask]=multiply(q[mask],g)
    x=v[:,1:]/v[:,0,None]
    order=np.argsort(-np.abs(x),axis=1,kind='stable')
    a=np.take_along_axis(x,order,axis=1)
    # H is a proper signed permutation: first two signs positive; determinant +1 fixes third.
    inv=((order[:,0]>order[:,1]).astype(int)+(order[:,0]>order[:,2])+(order[:,1]>order[:,2]))
    parity=np.where(inv%2==0,1.,-1.)
    signs=np.ones_like(a);signs[:,:2]=np.where(a[:,:2]<0,-1,1)
    signs[:,2]=parity*signs[:,0]*signs[:,1]
    x=a*signs
    c=S/2+np.take_along_axis(c-S/2,order,axis=1)*signs
    c=np.where((c[:,0]>S/2)[:,None],S-c,c)
    qr=np.column_stack([np.ones(len(x)),x]);r=rot(qr);h=np.abs(r).sum(axis=2)/2
    u=(c-h)/(S-2*h)
    return x,np.clip(u,0,1),r,c

def run_batch(boxes,domain=False):
    # Files avoid pipe deadlock and retain reproducible inputs only when desired.
    inp=BASE/'validation_input.tmp';out=BASE/'validation_output.tmp'
    with inp.open('w') as f:
        for b in boxes:
            f.write(json.dumps({'box':[{'lo':float(a),'hi':float(z)} for a,z in b], 'domain':domain},separators=(',',':'))+'\n')
    with inp.open() as f,out.open('w') as g:
        subprocess.run([str(EXE),'--batch'],stdin=f,stdout=g,check=True)
    ans=[json.loads(l) for l in out.read_text().splitlines()]
    inp.unlink();out.unlink();assert len(ans)==len(boxes)
    return ans

def membership(r,c):
    return np.max(np.abs(np.einsum('nwi,npw->npi',r,V[None,:,:]-c[:,None,:])),axis=2)<=0.5+1e-12

def main():
    start=time.monotonic();rng=np.random.default_rng(20261014);n=100000
    q=rng.normal(size=(n,4));r=rot(q);h=np.abs(r).sum(axis=2)/2;u=rng.random((n,3))
    # Include 20k feasible wall/edge/corner poses.
    for k in range(3): u[:20000//(k+1),k]=rng.integers(0,2,size=20000//(k+1))
    c=h+u*(S-2*h);before=membership(r,c)
    x,u,r,c=reduce(q,c);after=membership(r,c)
    assert np.array_equal(before.sum(axis=1),after.sum(axis=1))
    assert np.all(x[:,0]>=x[:,1]-1e-14) and np.all(x[:,1]>=np.abs(x[:,2])-1e-14)
    assert np.max(np.abs(x))<=math.sqrt(2)-1+1e-14 and np.max(np.abs(x).sum(axis=1))<=1+1e-14
    assert np.max(u[:,0])<=0.5+1e-14
    params=np.column_stack([x,u]);rad=10**rng.uniform(-6,-1,size=(n,6))
    lo=np.maximum(params-rad,[-1,-1,-1,0,0,0]);hi=np.minimum(params+rad,[1,1,1,1,1,1])
    boxes=np.stack([lo,hi],axis=2);ans=run_batch(boxes,True);counts=collections.Counter()
    for k,a in enumerate(ans):
        counts[a['reason']]+=1
        if a['reason'] in ['point','centre','wall']: assert after[k,a['p']],(k,a)
        if a['reason']=='local_ab': assert after[k,[0,2,4,6]].any(),(k,a)
        if a['reason']=='pair': assert after[k,a['p']] or after[k,a['q']],(k,a)
        assert a['reason']!='outside', (k,a)
    # Explicit full-dimensional neighborhoods enclosing exact degenerate poses.
    cases=[('corner',[0,0,0],[.5,.5,.5]),
           ('one_wall',[math.tan(.15),0,0],[.5,1,1]),
           ('distance_one_pair',[math.sqrt(2)-1,0,0],[1,S/2,S/2]),
           ('tube',[0,0,math.sqrt(2)-1],[S/2,S/2,1])]
    degenerates={}
    for name,x,c in cases:
        r=rot(np.array([[1,*x]]));h=np.abs(r[0]).sum(axis=1)/2;u=(np.array(c)-h)/(S-2*h)
        # Small rounding errors at wall are clamped; exact mathematical pose is included by outward endpoints.
        p=np.r_[x,np.clip(u,0,1)]
        for level in range(2,31):
            eps=2.**-level
            box=np.stack([np.maximum(p-eps,[-1]*3+[0]*3),np.minimum(p+eps,[1]*6)],axis=1)
            a=run_batch([box])[0]
            if a['reason']!='split':break
        assert a['reason']!='split',(name,a)
        # Sample 2,000 poses inside each certified neighborhood.
        ps=rng.uniform(box[:,0],box[:,1],size=(2000,6));rr=rot(np.column_stack([np.ones(2000),ps[:,:3]]))
        hh=np.abs(rr).sum(axis=2)/2;cc=hh+ps[:,3:]*(S-2*hh);inside=membership(rr,cc)
        assert np.all(inside[:,a['p']] | (inside[:,a['q']] if a['reason']=='pair' else False))
        degenerates[name]={'coordinate_radius_power':level,'reason':a['reason'],'p':a['p'],'q':a['q'],'box':box.tolist(),'sampled':2000}
    result={'random_poses':n,'symmetry_poses':n,'closure_counts':dict(counts),'false_closures':0,
            'degenerates':degenerates,'seconds':time.monotonic()-start,'seed':20261014}
    (BASE/'validation.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
