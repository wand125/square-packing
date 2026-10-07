"""Independent numerical holdout for a saved native mixed initial state."""
import os
for name in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMBA_NUM_THREADS'):os.environ[name]='1'
import argparse,json,sys,hashlib,time
from pathlib import Path
from fractions import Fraction as F
import numpy as np


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--state',type=Path,required=True)
    ap.add_argument('--code-dir',type=Path,required=True);ap.add_argument('--target',type=float,required=True)
    ap.add_argument('--seed',type=int,default=20265000);ap.add_argument('--count',type=int,default=65536)
    ap.add_argument('--boundary-fraction',type=float,default=.25);ap.add_argument('--out',type=Path,required=True)
    ap.add_argument('--pose-state',type=Path);ap.add_argument('--normalized-poses',action='store_true')
    a=ap.parse_args();sys.path.insert(0,str(a.code_dir.resolve()))
    from unified_geometry import expand_primitives,matrix
    from mixed_grid_pricing import screening_poses,quality_metrics
    start=time.perf_counter();z=np.load(a.state,allow_pickle=False)
    ps=json.loads(str(z['primitives_json']));weights=z['weights'];L=float(z['L']);B=float(z['B'])
    if len(ps)!=len(weights) or not np.all(np.isfinite(weights)) or np.any(weights<0):raise ValueError('invalid saved weights')
    if 'core_json' in z:
        from trimmed_numeric import matrix as trimmed_matrix
        from trimmed_core import parameters
        core=json.loads(str(z['core_json']));net=json.loads(str(z['net_json']))
        if core['kind']!='octagon_with_square_radial':raise ValueError('unsupported core')
        h,g=parameters(net['step'],core['margin']);matrix=lambda q,b,e:trimmed_matrix(q,b,e,float(h),float(g))
    ids=np.flatnonzero(weights>0);expanded=expand_primitives([ps[i] for i in ids],F(str(L)))
    if a.normalized_poses and a.pose_state is None:raise ValueError('normalized poses require a pose state')
    if a.pose_state is not None:
        poses=np.load(a.pose_state,allow_pickle=False)['poses']
        if a.normalized_poses:
            from radial_pricing import physical_poses
            poses=physical_poses(poses,L,B)
    else:poses=screening_poses(L,B,count=a.count,seed=a.seed,boundary_fraction=a.boundary_fraction)
    values=np.concatenate([matrix(poses[i:i+256],B,expanded)@weights[ids] for i in range(0,len(poses),256)])
    result=quality_metrics(values,float(weights.sum()),a.target)
    result.update(seed=a.seed,boundary_fraction=a.boundary_fraction,seconds=time.perf_counter()-start,
        state_sha256=hashlib.sha256(a.state.read_bytes()).hexdigest(),active_primitives=len(ids),
        source_sha256={name:hashlib.sha256(Path(sys.modules[name].__file__).read_bytes()).hexdigest() for name in ('unified_geometry','mixed_grid_pricing','trimmed_core','trimmed_numeric') if name in sys.modules})
    result['source_sha256']['evaluate_initial']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    if a.pose_state is not None:
        result.update(seed=None,boundary_fraction=None,pose_state_sha256=hashlib.sha256(a.pose_state.read_bytes()).hexdigest(),
            pose_geometry='normalized legacy poses reevaluated at candidate L/B' if a.normalized_poses else 'saved physical poses')
    with a.out.open('x') as f:json.dump(result,f,indent=2);f.write('\n')
    print(json.dumps(result),flush=True)


if __name__=='__main__':main()
