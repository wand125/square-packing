"""Same-input control vs batch: untouched wall probes and fresh strict checks."""
import json
from pathlib import Path
from fractions import Fraction as F
import numpy as np
from expanded_search_pilot import ROOT
from mixed_wall_batch import score
from mixed_density_check import expand,evaluate
from mixed_axis_verify import verify
from verify_axis_certificate import replay
from mixed_rotated_verify import compile_verifier,run as rotated
from mixed_density_separate import run as separate


def main():
    root=ROOT/'n21';probe=root/'shared-net-refit-2/wall-batch-balanced/probe.npz'
    with np.load(probe) as z:poses=z['poses'];labels=z['labels'];xyz=z['coordinates']
    binary=Path('/tmp/mixed-wall-compare');compile_verifier(binary);summary={}
    for arm in ('control','batch'):
        folder=root/f'shared-net-refit-3-{arm}';out=folder/'validation';out.mkdir(exist_ok=False)
        for name,file in [('fixed_mixed','fixed-candidate.json'),('added_density','mixed-candidate.json')]:
            dest=out/name;dest.mkdir();candidate=folder/file;data=json.loads(candidate.read_text());model=expand(data)
            values=score(data,poses);np.save(dest/'probe-values.npy',values)
            result=dict(mass=float(model[-2]),probe={part:dict(minimum=float(values[labels==part].min()),below_one=int(sum(values[labels==part]<1)),below_gamma=int(sum(values[labels==part]<1.0001))) for part in ('train','held')})
            held=np.flatnonzero(labels=='held');i=int(held[np.argmin(values[held])]);x,y,t=[F(float(v)).limit_denominator(10**10) for v in xyz[i]]
            result['exact_worst_held']=evaluate(model,x,y,t)
            axis=verify(candidate,dest/'axis');result['axis']=axis['status']
            if axis['status']=='AXIS_VERIFIED':replay(dest/'axis')
            r=rotated(candidate,1,dest/'net1',binary,nodes=200000)
            result['net1']={k:r[k] for k in ('status','nodes','seconds','frontier_area_fraction')};result['net1']['below_one']=sum(F(w['score'])<1 for w in r['exact_witnesses'])
            separate(candidate,dest/'fresh.json',seed=926219)
            fresh=json.loads((dest/'fresh.json').read_text());result['fresh']=dict(witnesses=len(fresh['witnesses']),numerical_minimum=fresh['numerical_minimum'])
            summary[f'{arm}/{name}']=result;(root/'wall-batch-comparison.json').write_text(json.dumps(summary,indent=2))
            print(json.dumps(dict(arm=arm,name=name,**{k:v for k,v in result.items() if k!='exact_worst_held'})),flush=True)
if __name__=='__main__':main()
