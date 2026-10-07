"""Revalidate freshly repaired weights; never reuse old passed cells."""
import json,argparse
from pathlib import Path
from fractions import Fraction as F
from mixed_axis_verify import verify
from verify_axis_certificate import replay
from mixed_rotated_verify import compile_verifier,run as rotated
from mixed_density_separate import run as separate
from expanded_search_pilot import ROOT


def run(root=None,seed=926217):
    root=Path(root) if root else ROOT/'n21/shared-net-refit-1';out=root/'validation';out.mkdir(exist_ok=False)
    fit=json.loads((root/'results.json').read_text());assert fit['status']=='FINITE_REPAIRED_NOT_CERTIFIED'
    binary=out/'mixed-verify';compile_verifier(binary);results={}
    for name,file in [('fixed_mixed','fixed-candidate.json'),('added_density','mixed-candidate.json')]:
        candidate=root/file;folder=out/name;folder.mkdir()
        axis=verify(candidate,folder/'axis');print(name,'axis',axis['status'],flush=True)
        if axis['status']=='AXIS_VERIFIED':replay(folder/'axis')
        angles={}
        for index in (1,85,198):
            r=rotated(candidate,index,folder/f'net{index}',binary,nodes=200000)
            angles[str(index)]={k:r[k] for k in ('status','nodes','leaves','seconds','frontier_area_fraction')}
            angles[str(index)]['exact_deficits']=len(r['exact_witnesses'])
            print(name,index,json.dumps(angles[str(index)]),flush=True)
        separate(candidate,folder/'fresh.json',seed=seed)
        fresh=json.loads((folder/'fresh.json').read_text())
        results[name]=dict(axis=axis['status'],angles=angles,fresh_status=fresh['status'],fresh_witnesses=len(fresh['witnesses']))
        (out/'summary.json').write_text(json.dumps(results,indent=2))
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--root');ap.add_argument('--seed',type=int,default=926217);a=ap.parse_args();run(a.root,a.seed)
