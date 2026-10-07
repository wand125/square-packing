"""Upgrade every leaf of a complete saved partition, then replay it."""
import argparse,json,time,hashlib
from pathlib import Path
from fractions import Fraction as F
from mixed_density_check import expand
from robust_pose_core import best_lower_bound
from pose_symmetry import cached_bound
from full_pose_low_cover import verify


def run(candidate,source,out):
    start=time.monotonic();q=json.loads(source.read_text());model=expand(json.loads(candidate.read_text()))
    assert q['digest']==model[-1]
    lower,cache=cached_bound(model,best_lower_bound,'D4');threshold=F(q['threshold']);improved=0
    q['bound_method']='robust';q['symmetry']='D4';q['upgraded_from_sha256']=hashlib.sha256(source.read_bytes()).hexdigest()
    for i,(path,rec) in enumerate(q['leaves'].items()):
        if rec['kind']=='OUTSIDE':continue
        old=F(rec['lower']);lb=lower(*map(F,rec['box']))
        # Refuse an unexpected decrease; it would need an explicit audit.
        assert lb>=old,(path,old,lb)
        improved+=lb>old;rec['lower']=str(lb);rec['kind']='HIGH' if lb>=threshold else 'POSSIBLE_LOW'
        if i%256==0:print('UPGRADE',i,'unique',len(cache),flush=True)
    q['upgrade_seconds']=time.monotonic()-start;q['unique_score_boxes']=len(cache)
    out.write_text(json.dumps(q,indent=2))
    replay=verify(candidate,json.loads(out.read_text()));replay.update(improved=improved,unique_score_boxes=len(cache),upgrade_seconds=q['upgrade_seconds'])
    out.with_suffix('.replay.json').write_text(json.dumps(replay,indent=2));print(json.dumps(replay),flush=True)
    return q

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('candidate',type=Path);p.add_argument('source',type=Path);p.add_argument('out',type=Path)
    a=p.parse_args();run(a.candidate,a.source,a.out)
