"""Boundary-anchored template contraction, concentrated near the centre.

Geometry and local weight compensation are initial-solution heuristics only.
The polynomial coordinate map is monotone and exactly D4-compatible.
"""
import os
for name in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMBA_NUM_THREADS'):os.environ[name]='1'
import argparse,json,time,sys,math,hashlib
from pathlib import Path
from fractions import Fraction as F
import numpy as np
from template_initial import load_template

class CentralWarp:
    def __init__(self,L0,L1,wall=0,power=1):
        self.L0=F(str(L0));self.L1=F(str(L1));self.wall=F(str(wall));self.power=power
        self.width=self.L0-2*self.wall;self.delta=self.L0-self.L1
        if type(power)!=int or not 0<=power<=6 or not 0<=self.wall<min(self.L0,self.L1)/2:raise ValueError('invalid resize')
        self.norm=F(math.factorial(2*power+1),math.factorial(power)**2)
        peak=self.norm/F(4)**power
        if 1-self.delta/self.width*peak<=0:raise ValueError('central contraction would fold')
    def cdf(self,s):
        p=self.power
        return self.norm*sum((F((-1)**j*math.comb(p,j),p+j+1)*s**(p+j+1) for j in range(p+1)),F(0))
    def map(self,x):
        x=F(str(x))
        if not 0<=x<=self.L0:raise ValueError('coordinate outside source')
        if x<=self.wall:return x
        if x>=self.L0-self.wall:return x-self.delta
        return x-self.delta*self.cdf((x-self.wall)/self.width)
    def derivative(self,x):
        x=F(str(x))
        if x<=self.wall or x>=self.L0-self.wall:return F(1)
        s=(x-self.wall)/self.width
        return 1-self.delta/self.width*self.norm*(s*(1-s))**self.power


def warp_template(ps,weights,L0,L1,target,wall=0,power=1,mass_power=1):
    warp=CentralWarp(L0,L1,wall,power);out=[];ws=[]
    if not 0<=mass_power<=1 or not np.isfinite(target) or target<=0:raise ValueError('invalid mass settings')
    weights=np.asarray(weights,dtype=float)
    if weights.ndim!=1 or len(ps)!=len(weights) or not np.isfinite(weights).all() or np.any(weights<0):raise ValueError('invalid source weights')
    for p,w in zip(ps,weights):
        if w<=0:continue
        g=list(map(F,p['geometry']));kind=p['kind']
        if kind=='rectangle':
            x,y,X,Y=g;new=list(map(warp.map,g));jac=((new[2]-new[0])*(new[3]-new[1]))/((X-x)*(Y-y))
        elif kind=='segment':
            x,y,X,Y=g;new=list(map(warp.map,g));jac=warp.derivative((x+X)/2)*warp.derivative((y+Y)/2)
        else:
            new=[warp.map(g[0]),warp.map(g[1])]+g[2:];jac=warp.derivative(g[0])*warp.derivative(g[1])
        out.append(dict(kind=kind,geometry=list(map(str,new)),family='central_warp'))
        ws.append(float(w)*float(jac)**mass_power)
    ws=np.asarray(ws,float)
    if not len(ws) or not np.isfinite(ws).all() or ws.sum()<=0:raise ValueError('empty/invalid source')
    raw=float(ws.sum());ws*=target/raw
    return out,ws,dict(raw_mass=raw,renormalization=target/raw,central_scale=float(warp.derivative(warp.L0/2)))


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--config',type=Path,required=True);a=ap.parse_args();cfg=json.loads(a.config.read_text());base=a.config.resolve().parent
    for key in ('code_dir','research_dir'):sys.path.insert(0,str((base/cfg[key]).resolve()))
    from unified_geometry import expand_primitives,matrix
    from mixed_grid_pricing import screening_poses,quality_metrics
    out=base/cfg['out'];out.mkdir(parents=True,exist_ok=False);source=base/cfg['template'];L0,B,ps,w=load_template(source);L=F(cfg['L']);target=float(cfg['target'])
    if not 0<target<cfg['n']:raise ValueError('invalid target')
    q=screening_poses(L,B,count=32768,seed=cfg['seed'],boundary_fraction=.25);records=[]
    for power,wall in cfg['maps']:
        # A coordinate matrix is shared between weight compensation variants.
        started=time.perf_counter();new,_,_=warp_template(ps,w,L0,L,target,wall,power,0)
        ex=expand_primitives(new,L);A=np.vstack([matrix(q[i:i+256],float(B),ex) for i in range(0,len(q),256)])
        shared_matrix_seconds=time.perf_counter()-started
        for eta in cfg.get('mass_powers',[0.,1.]):
            gen=time.perf_counter();new,weights,meta=warp_template(ps,w,L0,L,target,wall,power,eta)
            key=f'p{power}-wall{wall}-mass{eta}';dest=out/key;dest.mkdir();poses=screening_poses(L,B,count=4096,seed=cfg['seed']+1,boundary_fraction=.25)
            np.savez_compressed(dest/'resume-state.npz',primitives_json=json.dumps(new),weights=weights,poses=poses,dual=np.zeros(len(poses)),L=float(L),B=float(B),rhs=1.001)
            generation_seconds=time.perf_counter()-gen
            quality=quality_metrics(A@weights,weights.sum(),target)
            record=dict(key=key,power=power,wall=wall,mass_power=eta,generation_seconds=generation_seconds,shared_matrix_seconds=shared_matrix_seconds,quality=quality,**meta)
            (dest/'result.json').write_text(json.dumps(record,indent=2)+'\n');records.append(record)
            (out/'progress.json').write_text(json.dumps(dict(records=records),indent=2)+'\n');print(json.dumps(record),flush=True)
    (out/'result.json').write_text(json.dumps(dict(config=cfg,source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),records=records,certified=False),indent=2)+'\n')

if __name__=='__main__':main()
