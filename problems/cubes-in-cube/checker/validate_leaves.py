"""Soundness sample on the actual local_ab leaves of a full run kept with --keep-leaves.
For each local_ab leaf, 200 random poses (plus the 64 box corners) must each have one of the four x = 1 points
inside the closed cube (tolerance 1e-12)."""
import json, math, sys, numpy as np, itertools
S=2+1/math.sqrt(2); P=np.array([[S-1 if (p>>w)&1 else 1 for w in range(3)] for p in range(8)])
A=math.sqrt(2)-1; ROOT=np.array([[0,A],[0,A],[-A,A],[0,.5],[0,1],[0,1]])
def pose(v):
    x,y,z=v[:3]; d=1+x*x+y*y+z*z
    R=np.array([[1+x*x-y*y-z*z,2*(x*y-z),2*(x*z+y)],[2*(x*y+z),1+y*y-x*x-z*z,2*(y*z-x)],[2*(x*z-y),2*(y*z+x),1+z*z-x*x-y*y]])/d
    h=0.5*np.abs(R).sum(1); c=h+np.array(v[3:])*(S-2*h); return R,c
rng=np.random.default_rng(14); n=bad=0; worst=-1
for l in open(sys.argv[1]):
    if 'local_ab' not in l: continue
    nd=json.loads(l)['node']; g=np.array(nd['grid'],float); L=2.0**-np.array(nd['levels'],float)
    lo=ROOT[:,0]+(ROOT[:,1]-ROOT[:,0])*g*L; hi=ROOT[:,0]+(ROOT[:,1]-ROOT[:,0])*(g+1)*L
    vs=[lo+rng.random(6)*(hi-lo) for _ in range(200)]+[np.where(np.array(m),hi,lo) for m in itertools.product([0,1],repeat=6)]
    for v in vs:
        R,c=pose(v); t=(P-c)@R; ex=(np.abs(t).max(1)-0.5)[[0,2,4,6]].min(); worst=max(worst,ex); n+=1
        if ex>1e-12: bad+=1
print('poses',n,'failures',bad,'worst excess',worst)
