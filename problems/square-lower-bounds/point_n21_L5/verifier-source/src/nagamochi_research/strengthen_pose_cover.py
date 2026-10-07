"""Upgrade retained low leaves without changing the complete binary partition."""
from pathlib import Path
from fractions import Fraction as F
import argparse,hashlib,json,time
from mixed_density_check import expand
from full_pose_low_cover import verify,lower_function
from pose_symmetry import cached_bound,images
from refine_saved_pose_cover import atomic_save


def run(candidate,source,out,method='correlated',max_groups=0,wall_only=False):
    model=expand(json.loads(candidate.read_text()));base=json.loads(source.read_text())
    assert base['digest']==model[-1] and base.get('symmetry')=='D4'
    digest=hashlib.sha256(source.read_bytes()).hexdigest();progress=out.with_suffix('.progress.json')
    q=json.loads(progress.read_text()) if progress.exists() else base
    if not progress.exists():q.pop('strengthen_selected_paths',None)
    if progress.exists():
        assert q['strengthen_source_sha256']==digest and q['strengthen_method']==method
        assert q.get('strengthen_max_groups',0)==max_groups
        assert q.get('strengthen_wall_only',False)==wall_only
    q.update(strengthen_source_sha256=digest,strengthen_method=method,strengthen_max_groups=max_groups,strengthen_wall_only=wall_only)
    lower,cache=cached_bound(model,lower_function(method),'D4');start=time.monotonic();last=start
    work=[(p,r) for p,r in q['leaves'].items() if r['kind']=='POSSIBLE_LOW' and r.get('bound_method')!=method]
    if wall_only:
        from physical_pose_bound import restrict_centres
        work=[(p,r) for p,r in work if restrict_centres(model[0],tuple(map(F,r['box'])))!=tuple(map(F,r['box']))]
    if max_groups:
        assert type(max_groups) is int and max_groups>0
        if 'strengthen_selected_paths' not in q:
            groups={}
            for path,r in work:
                key=images(tuple(map(F,r['box'])),model[0])[0]
                groups.setdefault(key,[]).append((path,r))
            keys=sorted(groups,key=lambda key:max(F(r['lower']) for _,r in groups[key]),reverse=True)[:max_groups]
            q['strengthen_selected_paths']=[path for key in keys for path,_ in groups[key]]
        selected=set(q['strengthen_selected_paths']);work=[(p,r) for p,r in work if p in selected]
    for i,(path,r) in enumerate(work):
        value=lower(*map(F,r['box']));assert value>=F(r['lower'])
        r.update(lower=str(value),bound_method=method,kind='HIGH' if value>=F(q['threshold']) else 'POSSIBLE_LOW')
        if time.monotonic()-last>15:
            atomic_save(progress,q);print('STRENGTHEN',i+1,'of',len(work),'unique',len(cache),flush=True);last=time.monotonic()
    q.update(strengthen_seconds=time.monotonic()-start)
    atomic_save(progress,q);atomic_save(out,q)
    result=verify(candidate,json.loads(out.read_text()))
    out.with_suffix('.replay.json').write_text(json.dumps(result,indent=2));print(result,flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser()
    for name in ('candidate','source','out'):p.add_argument(name,type=Path)
    p.add_argument('--method',choices=['correlated','correlated-adaptive1','physical-correlated','physical-adaptive1','physical-adaptive2'],default='correlated')
    p.add_argument('--max-groups',type=int,default=0)
    p.add_argument('--wall-only',action='store_true')
    a=p.parse_args();run(a.candidate,a.source,a.out,a.method,a.max_groups,a.wall_only)
