"""Replay finite-model dual certificates with Fraction geometry only; no LP solver."""
from fractions import Fraction as F
from pathlib import Path
import argparse,json
from score import square,features,template


def verify(path):
    d=json.loads(path.read_text());k=d['k'];costs=template(k)[3]
    loads=[F(0)]*4;bound=F(0)
    for w in d['dual_witnesses']:
        p=w['pose'];delta=F(p['delta']);t=F(p['t']);x=F(p['cx']);y=F(p['cy'])
        assert p['k']==k and 0<delta<=F(1,100)
        poly=square(x,y,1+delta,t)
        assert all(0<=v<=k for point in poly for v in point)
        row=features(k,poly);assert row==list(map(F,w['features']))
        weight=F(w['dual_weight']);assert weight>=0
        bound+=weight
        loads=[v+weight*a for v,a in zip(loads,row)]
    assert loads==list(map(F,d['exact_dual_loads']))
    assert all(v<=c for v,c in zip(loads,costs))
    assert bound==F(d['exact_finite_model_lower_bound'])
    return dict(k=k,lower_bound=str(bound),lower_bound_float=float(bound),witnesses=len(d['dual_witnesses']),status='VERIFIED_FINITE_MODEL_DUAL')


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('directory',type=Path);a=ap.parse_args()
    result=[verify(p) for p in sorted(a.directory.glob('k*.json'))]
    print(json.dumps(result,indent=2))
