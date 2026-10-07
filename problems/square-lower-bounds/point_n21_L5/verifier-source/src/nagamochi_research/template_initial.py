"""Fast, explicitly warm initialization from a reusable D4 measure template.

Source certification is NOT transferred. Generation and independent numerical
assessment have separate timings; offline template search cost is not hidden.
"""
import os
for name in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMBA_NUM_THREADS'):os.environ[name]='1'
import argparse,json,sys,time,hashlib
from pathlib import Path
from fractions import Fraction as F
from collections import Counter
import numpy as np
from unified_measure import orbit


def load_template(path):
    path=Path(path)
    if path.suffix=='.npz':
        z=np.load(path,allow_pickle=False)
        return F(str(float(z['L']))),F(str(float(z['B']))),json.loads(str(z['primitives_json'])),z['weights']
    d=json.loads(path.read_text());L=F(str(d['L']));B=F(str(d['B']));ps=[];weights=[]
    if 'rectangles' in d:
        if len(d['rectangles'])!=len(d['weights']):raise ValueError('rectangle weight count mismatch')
        for r,w in zip(d['rectangles'],d['weights']):
            if F(str(w)):
                ps.append(dict(kind='rectangle',geometry=list(map(str,r)),family='template'));weights.append(float(F(str(w))))
    elif 'point_cols' in d:
        if d.get('charge_cols') or len(d['weights'])!=len(d['point_cols']):raise ValueError('point-only template required')
        sites=[tuple(map(F,s)) for s in d['sites']]
        for indices,w in zip(d['point_cols'],d['weights']):
            if not F(w):continue
            g=sites[indices[0]]
            if len(set(indices))!=len(indices) or set(orbit('point',g,L))!={sites[i] for i in indices}:raise ValueError('column is not one full D4 orbit')
            if len(set(Counter(sites[i] for i in indices).values()))!=1:raise ValueError('nonuniform orbit multiplicity')
            ps.append(dict(kind='point',geometry=list(map(str,g)),family='template'));weights.append(float(F(w)*len(indices)))
    else:raise ValueError('unsupported template schema')
    weights=np.asarray(weights,float)
    if np.any(weights<0) or not np.isfinite(weights).all():raise ValueError('invalid template weights')
    return L,B,ps,weights


def transfer(ps,weights,L0,L1,target,mode):
    L0=F(str(L0));L1=F(str(L1));ratio=L1/L0
    weights=np.asarray(weights,float)
    if len(weights)!=len(ps) or not np.isfinite(weights).all() or np.any(weights<0):raise ValueError('invalid template weights')
    if mode not in ('scaled','wall') or min(L0,L1)<=2:raise ValueError('invalid transfer')
    def coord(x):
        if mode=='scaled':return x*ratio
        if x<=1:return x
        if x>=L0-1:return L1-(L0-x)
        return 1+(x-1)*(L1-2)/(L0-2)
    result=[];ws=[]
    for p,w in zip(ps,weights):
        if w<=0:continue
        g=list(map(F,p['geometry']));kind=p['kind']
        if kind in ('point','disk','bump','annulus'):
            g[:2]=[coord(x) for x in g[:2]]
            if kind!='point' and mode=='scaled':g[2]*=ratio
        else:g=[coord(x) for x in g]
        result.append(dict(kind=kind,geometry=list(map(str,g)),family=f'template_{mode}'));ws.append(w)
    ws=np.array(ws,float)
    if not len(ws) or not np.isfinite(ws).all() or np.any(ws<0) or target<=0:raise ValueError('invalid mass')
    ws*=float(target)/ws.sum()
    return result,ws


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--config',type=Path,required=True);a=ap.parse_args()
    cfg=json.loads(a.config.read_text());base=a.config.resolve().parent
    sys.path.insert(0,str((base/cfg['code_dir']).resolve()));sys.path.insert(0,str((base/cfg['research_dir']).resolve()))
    from unified_geometry import expand_primitives,matrix
    from mixed_grid_pricing import screening_poses,quality_metrics
    out=base/cfg['out'];out.mkdir(parents=True,exist_ok=False);start=time.perf_counter()
    source=base/cfg['template'];L0,B,ps,weights=load_template(source)
    L=F(cfg['L']);target=F(cfg['target'])
    if not 0<target<cfg['n']:raise ValueError('invalid target')
    ps,weights=transfer(ps,weights,L0,L,float(target),cfg['transfer_mode'])
    metadata={}
    if source.suffix=='.npz':
        original=np.load(source,allow_pickle=False)
        metadata={key:original[key] for key in ('net_json','core_json') if key in original}
    poses=screening_poses(L,B,count=4096,seed=20272000,boundary_fraction=.25)
    np.savez_compressed(out/'resume-state.npz',poses=poses,weights=weights,dual=np.zeros(len(poses)),primitives_json=json.dumps(ps),L=float(L),B=float(B),rhs=1.001,**metadata)
    generation_seconds=time.perf_counter()-start
    if 'core_json' in metadata:
        from trimmed_numeric import matrix as trimmed_matrix
        from trimmed_core import parameters
        core=json.loads(str(metadata['core_json']));net=json.loads(str(metadata['net_json']))
        if core['kind']!='octagon_with_square_radial':raise ValueError('unsupported core')
        h,g=parameters(net['step'],core['margin']);matrix=lambda q,b,e:trimmed_matrix(q,b,e,float(h),float(g))
    expanded=expand_primitives(ps,L);held=screening_poses(L,B,count=65536,seed=20273000,boundary_fraction=.25)
    values=np.concatenate([matrix(held[i:i+256],float(B),expanded)@weights for i in range(0,len(held),256)])
    report=dict(status='SAVED_TRANSFER_INITIAL',config=cfg,source_L=str(L0),generation_seconds=generation_seconds,
        assessment_seconds=time.perf_counter()-start-generation_seconds,source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
        source_code_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),primitives=len(ps),
        quality=quality_metrics(values,weights.sum(),float(target)),certified=False,
        limitation='Warm transfer; offline template preparation excluded and source proof does not transfer.')
    (out/'result.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report),flush=True)


if __name__=='__main__':main()
