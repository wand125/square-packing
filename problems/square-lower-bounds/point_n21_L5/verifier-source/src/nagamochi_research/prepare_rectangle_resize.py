"""Prepare, but never enqueue, a resized legacy rectangle-ladder checkpoint.

Retains every normalized pose and one output rectangle per source column.
Rebuild LP coefficients/weights at target L in the existing runner. Old duals,
weights and proof progress are deliberately not carried into the new model.
"""
import argparse,json,hashlib,time
from pathlib import Path
from fractions import Fraction as F
import numpy as np
from central_warp import CentralWarp


def resize_rectangles(rectangles,L0,L1,method='central',wall=1,power=2):
    L0,L1=F(str(L0)),F(str(L1));rectangles=np.asarray(rectangles,float)
    if rectangles.ndim!=2 or rectangles.shape[1]!=4 or not np.isfinite(rectangles).all():raise ValueError('invalid rectangle array')
    if not 0<L1 or not 0<L0 or np.any(rectangles<0) or np.any(rectangles>float(L0)) or np.any(rectangles[:,2:]<=rectangles[:,:2]):raise ValueError('invalid rectangle geometry')
    if method not in ('uniform','wall','central','endpoint'):raise ValueError('unknown method')
    if method=='endpoint':
        def coord(x):
            if L1<=L0:return min(x,L1/2) if x<=L0/2 else max(L1/2,x-(L0-L1))
            return x if x<L0/2 else x+L1-L0 if x>L0/2 else L1/2
    else:
        warp=CentralWarp(L0,L1,0 if method=='uniform' else wall,power if method=='central' else 0)
        coord=warp.map
    out=[];fallback=[]
    for i,row in enumerate(rectangles):
        g=list(map(lambda x:F(str(x)),row));new=list(map(coord,g))
        if new[0]>=new[2] or new[1]>=new[3]:
            # Do not lose a saved column when endpoint trimming collapses it.
            new=[x*L1/L0 for x in g];fallback.append(i)
        out.append(list(map(float,new)))
    return np.asarray(out),fallback


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--source',type=Path,required=True);ap.add_argument('--L',required=True)
    ap.add_argument('--source-L');ap.add_argument('--source-B');ap.add_argument('--source-rhs')
    ap.add_argument('--method',choices=['uniform','wall','central','endpoint'],default='central')
    ap.add_argument('--wall',default='1');ap.add_argument('--power',type=int,default=2)
    ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();start=time.perf_counter()
    z=np.load(a.source,allow_pickle=False)
    if 'primitives_json' in z:raise ValueError('native mixed states require resize_initial.py')
    def value(key,override):
        if key in z:
            v=F(str(float(z[key])))
            if override is not None and v!=F(override):raise ValueError(f'{key} conflicts with saved value')
            return v
        if override is None:raise ValueError(f'missing {key}: provide explicit --source-{key}')
        return F(override)
    L0=value('L',a.source_L);B=value('B',a.source_B);rhs=value('rhs',a.source_rhs)
    if B!=F('.9977') or rhs!=F('1.001'):raise ValueError('legacy runner requires B=.9977 and rhs=1.001')
    poses=z['poses']
    if poses.ndim!=2 or poses.shape[1]!=3 or not np.isfinite(poses).all() or np.any(abs(poses[:,:2])>1+1e-12) or np.any(poses[:,2]<0) or np.any(poses[:,2]>1):raise ValueError('expected legacy normalized poses')
    rects,fallback=resize_rectangles(z['rectangles'],L0,a.L,a.method,F(a.wall),a.power)
    a.out.mkdir(parents=True,exist_ok=False)
    np.savez_compressed(a.out/'resume-state.npz',rectangles=rects,poses=poses,dual=np.zeros(len(poses)),L=float(F(a.L)),B=float(B),rhs=float(rhs))
    report=dict(status='PREPARED_NOT_ENQUEUED',certified=False,source=str(a.source),source_sha256=hashlib.sha256(a.source.read_bytes()).hexdigest(),
        source_L=str(L0),L=str(F(a.L)),method=a.method,wall=a.wall,power=a.power,rows=len(poses),columns=len(rects),
        collapsed_fallback_columns=fallback,seconds=time.perf_counter()-start,
        continuation='Use output checkpoint at target L; do not apply source_L scaling again; rebuild LP and independently certify.',
        code_sha256={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [Path(__file__),Path(__file__).with_name('central_warp.py')]})
    (a.out/'result.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report),flush=True)


if __name__=='__main__':main()
