"""Targeted soundness check of rule local_ab: boxes of radius 1e-4..1e-2 around random parameters
near P0 = (sqrt2-1, 0, 0, 0, 1/2, 1/2); for every box the checker closes by local_ab, 50 random poses inside the
box must each contain one of the four x = 1 points (closed, tolerance 1e-12)."""
import json, math, subprocess, tempfile, numpy as np, collections, pathlib
EXE=pathlib.Path(__file__).with_name('target')/'release'/'m5-checker'
S=2+1/math.sqrt(2); P=np.array([[S-1 if (p>>w)&1 else 1 for w in range(3)] for p in range(8)])
ROOT=np.array([[0,math.sqrt(2)-1],[0,math.sqrt(2)-1],[-(math.sqrt(2)-1),math.sqrt(2)-1],[0,.5],[0,1],[0,1]])
def pose(v):
    x,y,z=v[:3]; d=1+x*x+y*y+z*z
    R=np.array([[1+x*x-y*y-z*z,2*(x*y-z),2*(x*z+y)],[2*(x*y+z),1+y*y-x*x-z*z,2*(y*z-x)],[2*(x*z-y),2*(y*z+x),1+z*z-x*x-y*y]])/d
    h=0.5*np.abs(R).sum(1); c=h+np.array(v[3:])*(S-2*h); return R,c
rng=np.random.default_rng(1014); P0=np.array([math.sqrt(2)-1,0,0,0,.5,.5]); boxes=[]
for k in range(30000):
    sp=10**rng.uniform(-4,-1.7); centre=P0+rng.uniform(-1,1,6)*np.array([.02,.02,.02,.02,.02,.02]); centre[3]=abs(centre[3])*rng.choice([0,1])
    rad=10**rng.uniform(-4,-2)
    lo=np.maximum(centre-rad,ROOT[:,0]); hi=np.minimum(centre+rad,ROOT[:,1])
    if np.all(lo<hi): boxes.append(np.stack([lo,hi],1))
with tempfile.TemporaryDirectory() as td:
    f=pathlib.Path(td)/'in.jsonl'; f.write_text(''.join(json.dumps({'box':[{'lo':float(a),'hi':float(b)} for a,b in bx],'domain':False})+'\n' for bx in boxes))
    out=subprocess.run([str(EXE),'--batch'],stdin=open(f),capture_output=True,text=True,check=True).stdout.splitlines()
cnt=collections.Counter(); bad=0; tested=0
for bx,l in zip(boxes,out):
    a=json.loads(l); cnt[a['reason']]+=1
    if a['reason']!='local_ab': continue
    for _ in range(50):
        v=bx[:,0]+rng.random(6)*(bx[:,1]-bx[:,0]); R,c=pose(v); t=(P-c)@R
        ok=np.all(np.abs(t)<=0.5+1e-12,axis=1)[[0,2,4,6]].any(); tested+=1
        if not ok: bad+=1
print('boxes',len(boxes),dict(cnt),'local_ab poses tested',tested,'failures',bad)
