"""Reproduce seven known net deficits and benchmark bounded nonzero-angle checks."""
from fractions import Fraction as F
from pathlib import Path
import json
from mixed_density_check import expand,evaluate
from mixed_rotated_verify import compile_verifier,export,query,run


def main():
    root=Path('runs/expanded_n12_n21_20260926/n21/exact-refit-5/targeted-pricing-polished')
    out=Path('runs/mixed_rotated_full_20260926');out.mkdir(exist_ok=True)
    binary=Path('/tmp/mixed_rotated_verify');compile_verifier(binary)
    records=json.loads(Path('runs/mixed_strict_design_20260926/net-witnesses.json').read_text());checks=[]
    for rec,file in zip(records,('fixed-candidate.json','mixed-candidate.json')):
        candidate=root/file;model=expand(json.loads(candidate.read_text()))
        for i,w in enumerate(rec['records']):
            index=w['net_index'];t=F(w['net_t']);cw=w['canonical_witness'];x,y=F(cw['cx']),F(cw['cy'])
            if t*t+2*t-1>0:x,y=y,x
            p=out/f"{rec['candidate']}-witness-{i}.txt";meta=export(model,index,p)
            low,high=F(meta['domain']['centre_low']),F(meta['domain']['centre_high'])
            assert low<=x<=high and low<=y<=high
            exact=evaluate(model,x,y,t);assert exact['score']==w['net_score']
            lower=query(binary,p,[(x,y,F(0),F(0))])[0]
            assert lower<=F(exact['score'])<1
            checks.append(dict(candidate=rec['candidate'],index=index,exact=exact,interval_lower=str(lower),
                               lower_gap=float(F(exact['score'])-lower),in_required_domain=True))
    (out/'known-deficits.json').write_text(json.dumps(checks,indent=2)+'\n')
    print(json.dumps([dict(candidate=w['candidate'],index=w['index'],score=float(F(w['exact']['score'])),gap=w['lower_gap']) for w in checks]),flush=True)
    for name,file,index in [('added-net1','mixed-candidate.json',1),('fixed-net198','fixed-candidate.json',198),('added-net85','mixed-candidate.json',85)]:
        r=run(root/file,index,out/name,binary,nodes=2000)
        print(json.dumps(dict(name=name,status=r['status'],nodes=r['nodes'],leaves=r['leaves'],seconds=r['seconds'],frontier=len(r['frontier']),exact_witnesses=len(r['exact_witnesses']))),flush=True)
if __name__=='__main__':main()
