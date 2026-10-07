"""Check cumulative row retention and exact local 3D pose neighbourhoods."""
import json
from fractions import Fraction as F
import numpy as np
from expanded_search_pilot import ROOT
from mixed_density_check import expand,evaluate,pose_lower_bound


def main():
    root=ROOT/'n21';records=[];last_ids=None;last_matrix=None
    for index in (2,3,4):
        folder=root/f'exact-refit-{index}';d=json.loads((folder/'results.json').read_text());z=np.load(folder/'replay.npz')
        model=expand(json.loads((folder/'mixed-candidate.json').read_text()));ws=json.loads((folder/'cumulative-witnesses.json').read_text())
        if last_ids is not None:
            assert np.array_equal(z['row_ids'][:len(last_ids)],last_ids)
            assert np.array_equal(z['matrix'][:len(last_matrix)],last_matrix)
        last_ids=z['row_ids'];last_matrix=z['matrix']
        for w in ws:assert F(evaluate(model,F(w['cx']),F(w['cy']),F(w['t']))['score'])>=1
        for name,stat in d['records'][-1]['models'].items():
            weight=z['weights_'+name]
            assert min(weight)>=0 and abs(sum(weight)-stat['mass'])<1e-8
            assert np.min(z['matrix'][:,:len(weight)]@weight)>=1.001-1e-8
            assert len(z['coverage_'+name])==61716+len(ws)
            assert min(z['coverage_'+name])>=1.001-1e-8
        fresh=json.loads((folder/'fresh-separation.json').read_text())
        assert fresh['digest']==model[-1]
        for w in fresh['witnesses']:
            assert evaluate(model,F(w['cx']),F(w['cy']),F(w['t']))['score']==w['score'] and F(w['score'])<1
        records.append(dict(round=index,cumulative=len(ws),fresh=len(fresh['witnesses']),budget=str(model[-2]),rows=len(z['matrix'])))
    regions=[]
    for w in ws:
        x,y,t=map(F,(w['cx'],w['cy'],w['t']))
        for power in range(4,11):
            h=F(1,10**power);box=[x-h,x+h,y-h,y+h,t-h/10,t+h/10]
            lower=pose_lower_bound(model,*box)
            if lower>=1:break
        assert lower>=1
        regions.append(dict(pose_box=list(map(str,box)),lower_bound=str(lower),centre_radius=str(h),half_angle_radius=str(h/10)))
    artifact=dict(digest=model[-1],regions=regions,scope='Exact local centre-and-angle boxes, including inadmissible poses as a safe relaxation. Not global coverage.')
    (folder/'pose-regions.json').write_text(json.dumps(artifact,indent=2))
    for region in regions:assert pose_lower_bound(model,*map(F,region['pose_box']))==F(region['lower_bound'])
    result=dict(status='CUMULATIVE_AND_LOCAL_POSE_CHECKS_PASSED',rounds=records,pose_regions=len(regions),radii=sorted({v['centre_radius'] for v in regions}))
    (root/'cumulative-verified.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))
if __name__=='__main__':main()
