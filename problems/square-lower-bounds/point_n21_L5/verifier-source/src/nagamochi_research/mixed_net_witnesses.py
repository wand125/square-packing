"""Recheck exploratory arbitrary-angle deficits at nearest proof-net angles."""
from fractions import Fraction as F
from pathlib import Path
import json,math
from mixed_density_check import expand,evaluate
from mixed_net_audit import symmetry,net_certificate


def map_witness(model,w):
    x,y,t=map(F,(w['cx'],w['cy'],w['t']));step=F(83,40000)
    if not 0<=t<=F(83,200):raise ValueError('Outside positive canonical net range')
    j=min(200,max(0,int(t/step+F(1,2))));tj=j*step
    direct=evaluate(model,x,y,tj)
    if tj*tj+2*tj-1>0:
        # Reflect in x=y to put the >45-degree endpoint back in the
        # numerical geometry API range. Exact D4 invariance is required.
        symmetry(model);cx,cy,ct=y,x,(1-tj)/(1+tj)
    else:cx,cy,ct=x,y,tj
    reflected=evaluate(model,cx,cy,ct);assert direct['score']==reflected['score']
    L,B=model[:2];c=(1-ct*ct)/(1+ct*ct);s=2*ct/(1+ct*ct);reach=(L-B*(c+s))/2
    return dict(net_index=j,net_t=str(tj),source_score=w['score'],net_score=direct['score'],net_below_one=F(direct['score'])<1,
                canonical_witness=reflected,normalized_pose=[float((cx-L/2)/reach),float((cy-L/2)/reach),2*math.atan(float(ct))/(math.pi/4)])


def main():
    root=Path('runs/expanded_n12_n21_20260926/n21/exact-refit-5/targeted-pricing-polished');output=[]
    for name,file in [('fixed_mixed','fixed-candidate.json'),('added_density','mixed-candidate.json')]:
        model=expand(json.loads((root/file).read_text()));symmetry(model);net_certificate(model[1])
        ws=json.loads((root/(name+'-fresh.json')).read_text())['witnesses'];records=[map_witness(model,w) for w in ws]
        output.append(dict(candidate=name,digest=model[-1],records=records))
    p=Path('runs/mixed_strict_design_20260926');p.mkdir(exist_ok=True);(p/'net-witnesses.json').write_text(json.dumps(output,indent=2))
    print(json.dumps([dict(candidate=d['candidate'],source_count=len(d['records']),net_deficits=sum(r['net_below_one'] for r in d['records']),net_minimum=float(min(F(r['net_score']) for r in d['records']))) for d in output]))
if __name__=='__main__':main()
