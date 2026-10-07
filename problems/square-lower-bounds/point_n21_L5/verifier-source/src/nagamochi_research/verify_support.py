"""Independently replay saved support-model duals without invoking a solver."""
import json,sys
from pathlib import Path
from fractions import Fraction as F
from support_pilot import basis,exact_row
from score import square


def verify(path):
    data=json.loads(path.read_text());k=data['k'];cols=basis(k,data['model']!='refined',data['model']=='interior')
    assert data['columns']==len(cols)
    loads=[F(0)]*len(cols);total=F(0)
    for witness in data['dual']['witnesses']:
        pose={key:F(v) for key,v in witness['pose'].items()};y=F(witness['dual_weight'])
        assert y>=0 and 0<pose['delta']<=F(1,100)
        poly=square(pose['cx'],pose['cy'],1+pose['delta'],pose['t'])
        assert all(0<=x<=k and 0<=z<=k for x,z in poly)
        row=exact_row(k,cols,pose)
        loads=[v+y*a for v,a in zip(loads,row)];total+=y
    assert all(v<=col['cost'] for v,col in zip(loads,cols))
    assert total==F(data['dual']['bound'])
    return dict(k=k,model=data['model'],lower_bound=float(total),witnesses=len(data['dual']['witnesses']),status='VERIFIED_FINITE_SUPPORT_DUAL')


if __name__=='__main__':
    for path in sorted(Path(sys.argv[1]).glob('k*-*.json')):
        print(json.dumps(verify(path)),flush=True)
