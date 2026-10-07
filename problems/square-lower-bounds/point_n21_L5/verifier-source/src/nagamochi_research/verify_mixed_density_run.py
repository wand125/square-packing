"""Replay exact deficits/centre bounds and finite numerical repair results."""
from fractions import Fraction as F
import json
import numpy as np
from expanded_search_pilot import ROOT
from mixed_density_check import expand,evaluate,centre_lower_bound

def main():
    root=ROOT/'n21';out=root/'exact-refit';old=expand(json.loads((root/'mixed-candidate.json').read_text()));new=expand(json.loads((out/'mixed-candidate.json').read_text()))
    counts=[]
    for model,path in [(old,root/'new-separation.json'),(new,out/'fresh-separation.json')]:
        data=json.loads(path.read_text());assert data['digest']==model[-1]
        for w in data['witnesses']:
            r=evaluate(model,F(w['cx']),F(w['cy']),F(w['t']))
            assert r=={k:v for k,v in w.items() if k!='normalized_pose'}
            assert F(r['score'])<1
        counts.append(len(data['witnesses']))
    regions=json.loads((out/'local-regions.json').read_text());assert regions['digest']==new[-1]
    for rec in regions['records']:
        lower=centre_lower_bound(new,*map(F,rec['centre_box']),F(rec['t']))
        assert lower==F(rec['lower_bound']) and lower>=1
    z=np.load(out/'replay.npz');result=json.loads((out/'results.json').read_text());final=result['records'][-1]
    for name,m in final['models'].items():
        w=z['weights_'+name];a=z['matrix'][:,:len(w)]
        assert min(w)>=0 and np.min(a@w)>=1.001-1e-8
        assert abs(sum(w)-m['mass'])<1e-8
        assert len(z['coverage_'+name])==61716+counts[0]
        assert min(z['coverage_'+name])>=1.001-1e-8
    output=dict(exact_deficits_before_after=counts,exact_fixed_angle_regions=len(regions['records']),finite_repair_replayed=True,status='LOCAL_CHECKS_VERIFIED_NOT_GLOBAL_CERTIFICATE')
    (out/'verified.json').write_text(json.dumps(output,indent=2));print(json.dumps(output))
if __name__=='__main__':main()
