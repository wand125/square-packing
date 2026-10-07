"""Check the sufficient Gamma=1 condition, without weakening interval rounding.
The rational model already enforces total mass < n, and the net audit proves
closed cores strictly inside disjoint unit-square interiors. Therefore mass
>=1 per core suffices; 1.0001 is an optional surplus, not a theorem hypothesis.
"""
import json
from fractions import Fraction as F
from pathlib import Path
from expanded_search_pilot import ROOT
from mixed_rotated_verify import run
from verify_rotated_result import replay
from mixed_density_check import expand
from mixed_net_audit import symmetry,net_certificate


def main():
    root=ROOT/'n21/shared-net-refit-5-net23';binary=(root/'validation/verify').resolve();summary={}
    for name,file,indices in [('fixed_mixed','fixed-candidate.json',(1,3)),('added_density','mixed-candidate.json',(2,3))]:
        candidate=root/file;data=json.loads(candidate.read_text());model=expand(data);symmetry(model);net_certificate(model[1]);assert model[-2]<data['n']
        for index in indices:
            dest=root/'validation'/name/f'net{index}-gamma1';r=run(candidate,index,dest,binary,nodes=200000,gamma=F(1))
            summary[f'{name}/{index}']={k:r[k] for k in ('status','nodes','lower','seconds')}
            summary[f'{name}/{index}']['below_one']=len(r['exact_witnesses'])
            if r['status']=='ANGLE_VERIFIED':replay(dest,binary)
            print(name,index,summary[f'{name}/{index}'],flush=True)
    (root/'validation/required-threshold.json').write_text(json.dumps(summary,indent=2))
if __name__=='__main__':main()
