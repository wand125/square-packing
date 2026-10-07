"""Exact shared-witness comparison and local pose checks after density pricing."""
import json
from fractions import Fraction as F
import numpy as np
from expanded_search_pilot import ROOT
from mixed_density_check import expand,evaluate,pose_lower_bound
from mixed_density_separate import run as separate

def main():
    source=ROOT/'n21/exact-refit-5';root=source/'targeted-pricing-polished';data=json.loads((root/'results.json').read_text());z=np.load(root/'replay.npz')
    models={name:expand(json.loads((root/file).read_text())) for name,file in [('fixed_mixed','fixed-candidate.json'),('added_density','mixed-candidate.json')]}
    initial=json.loads((source/'cumulative-witnesses.json').read_text())+json.loads((source/'fresh-separation.json').read_text())['witnesses']
    final=data['records'][-1]['models']
    for name,model in models.items():
        w=z['weights_'+name]
        assert min(w)>=0 and abs(sum(w)-final[name]['mass'])<1e-8
        assert min(z['matrix'][:,:len(w)]@w)>=1.001-1e-8
        assert len(z['coverage_'+name])==61716+len(initial)
        assert min(z['coverage_'+name])>=1.001-1e-8
        for witness in initial:assert F(evaluate(model,F(witness['cx']),F(witness['cy']),F(witness['t']))['score'])>=1
    assert all(0<x0<x1<F('4.98') and 0<y0<y1<F('4.98') for x0,y0,x1,y1 in z['selected_rectangles'])
    pool=[]
    for name,file in [('fixed_mixed','fixed-candidate.json'),('added_density','mixed-candidate.json')]:
        output=root/(name+'-fresh.json')
        if not output.exists():separate(root/file,output,926216)
        s=json.loads(output.read_text());assert s['digest']==models[name][-1]
        for witness in s['witnesses']:
            checked=evaluate(models[name],F(witness['cx']),F(witness['cy']),F(witness['t']))
            assert checked['score']==witness['score'] and F(checked['score'])<1
        pool+=s['witnesses']
    comparison={}
    for name,model in models.items():
        values=[F(evaluate(model,F(w['cx']),F(w['cy']),F(w['t']))['score']) for w in pool]
        comparison[name]=dict(common_witness_minimum=str(min(values)) if values else None,below_one=sum(v<1 for v in values),deficit_sum=str(sum(max(F(0),1-v) for v in values)))
    regions=[];model=models['added_density']
    for witness in initial:
        x,y,t=map(F,(witness['cx'],witness['cy'],witness['t']))
        for power in range(4,11):
            h=F(1,10**power);box=[x-h,x+h,y-h,y+h,t-h/10,t+h/10];lower=pose_lower_bound(model,*box)
            if lower>=1:break
        assert lower>=1
        regions.append(dict(box=list(map(str,box)),lower=str(lower)))
    (root/'pose-regions.json').write_text(json.dumps(dict(digest=model[-1],regions=regions),indent=2))
    result=dict(status='FINITE_AND_LOCAL_CHECKS_PASSED_NOT_GLOBAL_PROOF',exact_repaired_witnesses=len(initial),local_pose_regions=len(regions),new_witness_comparison=comparison,common_pool_count=len(pool),note='Pool combines both new searches; duplicates retained. Does not certify global coverage.')
    (root/'verified.json').write_text(json.dumps(result,indent=2));print(json.dumps(dict(status=result['status'],repaired=len(initial),regions=len(regions),pool=len(pool),comparison={name:{'minimum':float(F(v['common_witness_minimum'])) if v['common_witness_minimum'] else None,'below_one':v['below_one'],'deficit_sum':float(F(v['deficit_sum']))} for name,v in comparison.items()})))
if __name__=='__main__':main()
