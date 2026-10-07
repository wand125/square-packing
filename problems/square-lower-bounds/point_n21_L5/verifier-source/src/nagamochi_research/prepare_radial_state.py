"""Convert a radial research checkpoint to native mixed-search continuation."""
import argparse,hashlib,json
from pathlib import Path
from fractions import Fraction as F
import numpy as np
from unified_measure import RADIAL_SCHEMA,validate

def convert(source,out,n,include_witnesses=False):
    if out.exists():raise FileExistsError(out)
    z=np.load(source,allow_pickle=False);primitives=json.loads(str(z['primitives_json']))
    for kind,x,y,R,q in z['kernels']:
        if kind not in (0,1,2):raise ValueError('unknown radial kind')
        g=(x,y,R,q) if kind==2 else (x,y,R)
        primitives.append(dict(kind=('disk','bump','annulus')[int(kind)],geometry=list(map(lambda a:str(float(a)),g)),family='radial_import'))
    weights=z['weights'];poses=z['poses'];dual=z['dual']
    if weights.shape!=(len(primitives),) or dual.shape!=(len(poses),) or not np.isfinite(dual).all() or np.any(dual<0):raise ValueError('checkpoint dimensions/dual')
    mass=sum((F(str(float(w))) for w in weights),F(0))
    data=dict(schema=RADIAL_SCHEMA,n=n,L=str(float(z['L'])),B=str(float(z['B'])),net=dict(step='83/40000',last=200),
        total_mass=str(mass),primitives=[dict(p,mass=str(float(w))) for p,w in zip(primitives,weights)])
    validate(data)
    added=[];keys={tuple(np.round(p,13)) for p in poses}
    if include_witnesses and 'new_poses' in z:
        for p in z['new_poses']:
            key=tuple(np.round(p,13))
            if key not in keys:keys.add(key);added.append(p)
    if added:poses=np.vstack((poses,added));dual=np.pad(dual,(0,len(added)))
    out.parent.mkdir(parents=True,exist_ok=True)
    with out.open('xb') as f:
        np.savez_compressed(f,poses=poses,weights=weights,dual=dual,primitives_json=json.dumps(primitives),L=z['L'],B=z['B'],rhs=z['rhs'])
    report=dict(source=str(source),source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),rows=len(poses),primitives=len(primitives),added_witnesses=len(added),requires_refit=bool(added),certified=False)
    out.with_suffix('.json').write_text(json.dumps(report,indent=2)+'\n');return report

if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('source',type=Path);ap.add_argument('--out',type=Path,required=True);ap.add_argument('--n',type=int,required=True);ap.add_argument('--include-witnesses',action='store_true');a=ap.parse_args()
    print(json.dumps(convert(a.source,a.out,a.n,a.include_witnesses)))
