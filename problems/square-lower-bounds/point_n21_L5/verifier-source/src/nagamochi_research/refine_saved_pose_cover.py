"""Refine all retained low cells and recertify scores; keep full coverage.

Progress checkpoints are themselves complete partitions: a parent is
replaced only after ALL descendants have been classified.
"""
from pathlib import Path
from fractions import Fraction as F
import argparse,json,hashlib,time
from mixed_density_check import expand
from full_pose_low_cover import verify,split,outside_container
from robust_pose_core import best_lower_bound
from pose_symmetry import cached_bound


def atomic_save(path,data):
    temporary=path.with_suffix(path.suffix+'.tmp');temporary.write_text(json.dumps(data));temporary.replace(path)


def run(candidate,source,out,depth=2):
    assert type(depth) is int and 1<=depth<=4
    model=expand(json.loads(candidate.read_text()));original=json.loads(source.read_text())
    assert original['digest']==model[-1] and original.get('bound_method')=='robust' and original.get('symmetry')=='D4'
    digest=hashlib.sha256(source.read_bytes()).hexdigest();progress=out.with_suffix('.progress.json')
    q=json.loads(progress.read_text()) if progress.exists() else json.loads(json.dumps(original))
    if progress.exists():assert q['refinement_source_sha256']==digest and q['refinement_depth']==depth
    q.update(refinement_source_sha256=digest,refinement_depth=depth,refinement_status='RUNNING')
    lower,cache=cached_bound(model,best_lower_bound,'D4');threshold=F(q['threshold']);start=time.monotonic();last=start;count=0
    work=[(key,rec) for key,rec in original['leaves'].items() if rec['kind']=='POSSIBLE_LOW' and key in q['leaves']]
    for key,rec in work:
        children=[(key,tuple(map(F,rec['box'])))]
        for _ in range(depth):children=[(p+str(i),child) for p,box in children for i,child in enumerate(split(box))]
        replacements={}
        for p,box in children:
            if outside_container(box,model[0]):kind='OUTSIDE';lb=None
            else:
                lb=lower(*box);kind='HIGH' if lb>=threshold else 'POSSIBLE_LOW'
            replacements[p]=dict(box=list(map(str,box)),kind=kind,lower=None if lb is None else str(lb))
        del q['leaves'][key];q['leaves'].update(replacements);count+=1
        if time.monotonic()-last>=15:
            atomic_save(progress,q);print('REFINE',count,'of',len(work),'unique',len(cache),flush=True);last=time.monotonic()
    q.update(refinement_status='FINISHED_REPLAY_PENDING',refinement_seconds=time.monotonic()-start,refinement_unique_boxes=len(cache))
    atomic_save(out,q);atomic_save(progress,q)
    result=verify(candidate,json.loads(out.read_text()))
    root_volume=(model[0]-1)**2*F(5,6)
    def vol(r):
        b=list(map(F,r['box']));return (b[1]-b[0])*(b[3]-b[2])*(b[5]-b[4])
    result.update(low_parameter_volume_fraction=str(sum((vol(r) for r in q['leaves'].values() if r['kind']=='POSSIBLE_LOW'),F(0))/root_volume),refinement_seconds=q['refinement_seconds'])
    out.with_suffix('.replay.json').write_text(json.dumps(result,indent=2));print(json.dumps(result),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser()
    for key in ('candidate','source','out'):p.add_argument(key,type=Path)
    p.add_argument('--depth',type=int,default=2);a=p.parse_args();run(a.candidate,a.source,a.out,a.depth)
