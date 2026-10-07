"""Compare exact lower bounds on unchanged diagnostic parent regions."""
import json,hashlib,argparse,time
from pathlib import Path
from fractions import Fraction as F
from mixed_density_check import expand,pose_lower_bound
from translated_core_bound import translated_lower_bound,translated_correlated_lower_bound
from correlated_pose_core import correlated_lower_bound
from physical_pose_bound import restrict_centres

def run(candidate,pilot,out):
    if out.exists():raise FileExistsError(out)
    sha=hashlib.sha256(candidate.read_bytes()).hexdigest();data=json.loads(pilot.read_text())
    assert data['candidate_sha256']==sha
    model=expand(json.loads(candidate.read_text()));density=(model[0],model[1],model[2],[],*model[4:]);records=[]
    for row in data['records']:
        box=tuple(map(F,row['box']));tight=restrict_centres(model[0],box);bounds={};timings={}
        for name,func in [('common',pose_lower_bound),('translated',translated_lower_bound),('correlated',correlated_lower_bound),('translated_correlated',translated_correlated_lower_bound)]:
            start=time.monotonic();bounds[name]=str(func(density,*box));timings[name]=time.monotonic()-start
        if tight is not None:
            start=time.monotonic();bounds['physical_translated_correlated']=str(translated_correlated_lower_bound(density,*tight));timings['physical_translated_correlated']=time.monotonic()-start
        else:raise ValueError('Unexpected empty pilot domain')
        # The old PL36 point contribution remains valid after physical restriction.
        point_lower=F(row['chain_lower'])-F(row['density_lower'])
        combined=max(map(F,bounds.values()))+point_lower
        result=dict(box=row['box'],physical_box=list(map(str,tight)),density_bounds=bounds,seconds=timings,point_lower=str(point_lower),old_lower=row['chain_lower'],combined_lower=str(combined),physical_domain_certified=combined>=1)
        records.append(result);print(float(F(row['chain_lower'])),'->',float(combined),{k:round(float(F(v)),8) for k,v in bounds.items()},flush=True)
    out.write_text(json.dumps(dict(candidate_sha256=sha,records=records,general_packing_exclusion=False),indent=2))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('candidate',type=Path);p.add_argument('pilot',type=Path);p.add_argument('out',type=Path);a=p.parse_args();run(a.candidate,a.pilot,a.out)
