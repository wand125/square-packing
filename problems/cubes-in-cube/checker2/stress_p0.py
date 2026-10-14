"""Extra soundness test: boxes around all Euler representatives of P0 (45 deg about world x, centre (1/2, s/2, s/2)) and of its
images under axis permutations (45 deg about y / z touching y=0 / z=0), radius 10^U(-4,-1.5), random offset."""
import json, math, subprocess, itertools, numpy as np
exec(open('stress_random.py').read().split('rng=')[0])
def euler(R):
    b=math.acos(max(-1,min(1,R[2,2])))
    if abs(math.sin(b))<1e-9: return None
    a=math.atan2(R[1,2],R[0,2])%(2*math.pi); g=math.atan2(R[2,1],-R[2,0])
    return [a,b,g]
G=[np.array(m) for m in set(tuple(map(tuple,np.array(Pm)*np.array(sg)[:,None]*0+np.diag(sg)@np.eye(3)[list(Pm)])) for Pm in itertools.permutations(range(3)) for sg in itertools.product([1,-1],repeat=3))]
G=[g for g in G if np.linalg.det(g)>0]
reps=[]
for ax in range(3):
    t=math.pi/4; c,s_=math.cos(t),math.sin(t); R0=np.eye(3)
    o=[w for w in range(3) if w!=ax]; R0[o[0],o[0]]=c;R0[o[0],o[1]]=-s_;R0[o[1],o[0]]=s_;R0[o[1],o[1]]=c
    u=[.5,.5,.5]; u[ax]=0
    for g in G:
        e=euler(R0@g)
        if e is None: continue
        e[2]%=math.pi/2
        for gg in (e[2], e[2]+math.pi/2 if e[2]<1e-12 else None):
            pass
        reps.append(e+u)
rng=np.random.default_rng(5); boxes=[]
for k in range(6000):
    v=np.array(reps[k%len(reps)]); rad=10**rng.uniform(-4,-1.5)
    ctr=v+rng.uniform(-1,1,6)*rad*0.7
    lo=np.maximum(ctr-rad,ROOT[:,0]); hi=np.minimum(ctr+rad,ROOT[:,1])
    if np.all(lo<hi): boxes.append(np.stack([lo,hi],1))
inp=''.join(json.dumps({'box':b.tolist()})+'\n' for b in boxes)
out=subprocess.run(['./target/release/m5-check2','--batch'],input=inp,capture_output=True,text=True,check=True).stdout.splitlines()
cnt={}; bad=0; n=0
for b,l in zip(boxes,out):
    r=json.loads(l); cnt[r['rule']]=cnt.get(r['rule'],0)+1
    if not r.get('points'): continue
    for v in [b[:,0]+rng.random(6)*(b[:,1]-b[:,0]) for _ in range(40)]+[np.where(np.array(m),b[:,1],b[:,0]) for m in itertools.product([0,1],repeat=6)]:
        R,c=pose(v); t=(P-c)@R; n+=1; bad+=not (np.abs(t).max(1)<=.5+1e-12)[r['points']].any()
print('reps',len(reps),'boxes',len(boxes),'by rule',dict(sorted(cnt.items())),'poses',n,'failures',bad)
