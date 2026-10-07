"""Recheck interior patches, prior wall guarantees, axis, and new exploration."""
from fractions import Fraction as F
from pathlib import Path
import json,argparse
import numpy as np
from expanded_search_pilot import ROOT
from mixed_wall_batch import score
from mixed_wall_region import verify as region
from mixed_axis_verify import verify as axis
from verify_axis_certificate import replay
from mixed_rotated_verify import compile_verifier,run as rotated
from mixed_density_separate import run as separate
from mixed_density_check import expand,evaluate


def main(root=None,seed=926220,angles=(1,),gamma=F(10001,10000)):
    root=Path(root) if root else ROOT/'n21/shared-net-refit-4-interior';out=root/'validation';out.mkdir(exist_ok=False)
    with np.load(ROOT/'n21/shared-net-refit-3-batch/interior-batch/probe.npz') as z:poses=z['poses'];labels=z['labels'];xyz=z['coordinates']
    binary=out/'verify';compile_verifier(binary);summary={}
    for name,file in [('fixed_mixed','fixed-candidate.json'),('added_density','mixed-candidate.json')]:
        candidate=root/file;data=json.loads(candidate.read_text());model=expand(data);dest=out/name;dest.mkdir();values=score(data,poses)
        r=dict(mass=float(model[-2]),probes={part:dict(minimum=float(values[labels==part].min()),below_one=int(sum(values[labels==part]<1)),below_gamma=int(sum(values[labels==part]<1.0001))) for part in ('train','held')},regions={})
        np.save(dest/'probe-values.npy',values)
        held=np.flatnonzero(labels=='held');i=held[np.argmin(values[held])];r['exact_worst_held']=evaluate(model,*[F(float(v)).limit_denominator(10**10) for v in xyz[i]])
        a=axis(candidate,dest/'axis');r['axis']=a['status']
        if a['status']=='AXIS_VERIFIED':replay(dest/'axis')
        for j in (1,2,3):
            for kind,box in [('wall',None),('interior',(F(1,2),F(1,2),F(1,64),F(1,64)))]:
                q=region(candidate,j,dest/f'{kind}{j}',binary,box=box)
                r['regions'][f'{kind}{j}']={k:q[k] for k in ('status','nodes','lower','seconds')};print(name,kind,j,r['regions'][f'{kind}{j}'],flush=True)
                if kind=='interior' and q['status']!='REGION_VERIFIED':
                    q=region(candidate,j,dest/f'inner{j}',binary,box=(F(1,2),F(1,2),F(1,512),F(1,512)))
                    r['regions'][f'inner{j}']={k:q[k] for k in ('status','nodes','lower','seconds')};print(name,'inner',j,r['regions'][f'inner{j}'],flush=True)
        for index in angles:
            q=rotated(candidate,index,dest/f'net{index}',binary,nodes=200000,gamma=gamma);r[f'net{index}']={k:q[k] for k in ('status','nodes','seconds')};r[f'net{index}']['below_one']=sum(F(w['score'])<1 for w in q['exact_witnesses'])
            if q['status']=='ANGLE_VERIFIED':
                from verify_rotated_result import replay as replay_angle
                replay_angle(dest/f'net{index}',binary)
            print(name,index,r[f'net{index}'],flush=True)
        separate(candidate,dest/'fresh.json',seed=seed);fresh=json.loads((dest/'fresh.json').read_text());r['fresh']=dict(witnesses=len(fresh['witnesses']),numerical_minimum=fresh['numerical_minimum'])
        summary[name]=r;(out/'summary.json').write_text(json.dumps(summary,indent=2));print(json.dumps(dict(candidate=name,**{k:v for k,v in r.items() if k!='exact_worst_held'})),flush=True)
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--root');ap.add_argument('--seed',type=int,default=926220);ap.add_argument('--angles',type=int,nargs='+',default=[1]);ap.add_argument('--gamma',type=F,default=F(10001,10000));a=ap.parse_args();main(a.root,a.seed,a.angles,a.gamma)
