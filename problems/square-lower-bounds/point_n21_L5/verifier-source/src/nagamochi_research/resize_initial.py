"""Resize a reusable template to a nearby L, retaining core/net metadata.

Writes a fresh native state for further search. No source proof is inherited.
"""
import argparse,json,hashlib,time
from pathlib import Path
from fractions import Fraction as F
import numpy as np
from template_initial import load_template
from central_warp import warp_template
from outer_trim import resize_template,endpoint_resize_template
from mixed_grid_pricing import screening_poses
from unified_measure import net_check


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--source',type=Path,required=True)
    ap.add_argument('--L',required=True);ap.add_argument('--target',type=float,required=True)
    ap.add_argument('--method',choices=['uniform','wall','central','endpoint','restriction'],required=True)
    ap.add_argument('--wall',default='1');ap.add_argument('--power',type=int,default=2)
    ap.add_argument('--mass-power',type=float,default=1.)
    ap.add_argument('--out',type=Path,required=True)
    a=ap.parse_args();started=time.perf_counter();L=F(a.L)
    L0,B,ps,w=load_template(a.source)
    if a.method in ('endpoint','restriction'):
        f=endpoint_resize_template if a.method=='endpoint' else resize_template
        ps,w,meta=f(ps,w,L0,L,a.target)
    else:
        power=a.power if a.method=='central' else 0
        wall=0 if a.method=='uniform' else F(a.wall)
        ps,w,meta=warp_template(ps,w,L0,L,a.target,wall,power,a.mass_power)
    metadata={}
    if a.source.suffix=='.npz':
        z=np.load(a.source,allow_pickle=False)
        metadata={key:z[key] for key in ('net_json','core_json') if key in z}
        poses=z['poses'].copy();t=poses[:,2];extent=(1-t*t+2*t)/(1+t*t)
        old=float(L0)-float(B)*extent;new=float(L)-float(B)*extent
        if np.any(old<=0) or np.any(new<=0):raise ValueError('empty centre domain')
        poses[:,:2]=float(L)/2+(poses[:,:2]-float(L0)/2)*(new/old)[:,None]
    else:poses=screening_poses(L,B,count=8192,seed=20300001,boundary_fraction=.25)
    if 'net_json' not in metadata:metadata['net_json']=json.dumps(dict(step='83/40000',last=200))
    net_check(dict(B=str(B),net=json.loads(str(metadata['net_json']))))
    if ps[0]['kind']!='rectangle' or list(map(F,ps[0]['geometry']))!=[0,0,L,L]:
        ps=[dict(kind='rectangle',geometry=['0','0',str(L),str(L)],family='uniform')]+ps;w=np.r_[0.,w]
    a.out.mkdir(parents=True,exist_ok=False)
    np.savez_compressed(a.out/'resume-state.npz',primitives_json=json.dumps(ps),weights=w,poses=poses,dual=np.zeros(len(poses)),L=float(L),B=float(B),rhs=1.001,**metadata)
    report=dict(source=str(a.source),source_sha256=hashlib.sha256(a.source.read_bytes()).hexdigest(),L0=str(L0),L=str(L),B=str(B),
        method=a.method,target=a.target,wall=a.wall,power=a.power,mass_power=a.mass_power,
        generation_seconds=time.perf_counter()-started,certified=False,**meta)
    report['code_sha256']={name:hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest() for name in ('resize_initial.py','central_warp.py','outer_trim.py','template_initial.py')}
    (a.out/'result.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report),flush=True)


if __name__=='__main__':main()
