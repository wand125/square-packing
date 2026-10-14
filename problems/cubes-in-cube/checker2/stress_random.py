"""Extra soundness test: random boxes of radius 10^U(-4,-0.7) anywhere in the domain, plus boxes around P0 images;
for each box the checker closes, 40 random poses + 64 corners must contain one of the listed points (1e-12)."""
import json, math, subprocess, itertools, numpy as np, sys
S=2+1/math.sqrt(2); P=np.array([[S-1 if (p>>w)&1 else 1 for w in range(3)] for p in range(8)])
ROOT=np.array([[0,2*math.pi],[0,math.pi],[0,math.pi/2],[0,.5],[0,.5],[0,.5]])
def Rz(a): c,s=math.cos(a),math.sin(a); return np.array([[c,-s,0],[s,c,0],[0,0,1]])
def Ry(b): c,s=math.cos(b),math.sin(b); return np.array([[c,0,s],[0,1,0],[-s,0,c]])
def pose(v):
    R=Rz(v[0])@Ry(v[1])@Rz(v[2]); h=.5*np.abs(R).sum(1); return R,h+np.array(v[3:])*(S-2*h)
rng=np.random.default_rng(int(sys.argv[1]) if len(sys.argv)>1 else 88); boxes=[]
for k in range(int(sys.argv[2]) if len(sys.argv)>2 else 20000):
    ctr=ROOT[:,0]+rng.random(6)*(ROOT[:,1]-ROOT[:,0])
    if k%4==0: ctr[3+rng.integers(3)]=0.0          # wall contact
    rad=10**rng.uniform(-4,-0.7)*(ROOT[:,1]-ROOT[:,0])*rng.random(6)
    lo=np.maximum(ctr-rad,ROOT[:,0]); hi=np.minimum(ctr+rad,ROOT[:,1]); boxes.append(np.stack([lo,hi],1))
inp=''.join(json.dumps({'box':b.tolist()})+'\n' for b in boxes)
out=subprocess.run(['./target/release/m5-check2','--batch'],input=inp,capture_output=True,text=True,check=True).stdout.splitlines()
cnt={}; bad=0; n=0
for b,l in zip(boxes,out):
    r=json.loads(l); cnt[r['rule']]=cnt.get(r['rule'],0)+1
    if not r.get('points'): continue
    vs=[b[:,0]+rng.random(6)*(b[:,1]-b[:,0]) for _ in range(40)]+[np.where(np.array(m),b[:,1],b[:,0]) for m in itertools.product([0,1],repeat=6)]
    for v in vs:
        R,c=pose(v); t=(P-c)@R; ok=(np.abs(t).max(1)<=.5+1e-12)[r['points']].any(); n+=1; bad+= (not ok)
print('boxes',len(boxes),'by rule',dict(sorted(cnt.items())),'poses',n,'failures',bad)
