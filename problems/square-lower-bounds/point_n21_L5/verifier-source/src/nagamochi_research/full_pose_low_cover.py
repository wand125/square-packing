"""PL20: complete signed-angle pose partition with retained low/unknown leaves.

A completed cover is NOT a packing exclusion. Certified high leaves are
removed from the possible-low set; every other leaf remains in that set.
"""
from fractions import Fraction as F
from pathlib import Path
import argparse,json,heapq,time,hashlib
from mixed_density_check import expand,pose_lower_bound
from pose_symmetry import cached_bound


def root_box(L):return (F(1,2),L-F(1,2),F(1,2),L-F(1,2),F(-5,12),F(5,12))


def split(box):
    # Angle has at most twice the spatial support sensitivity.
    widths=[box[1]-box[0],box[3]-box[2],2*(box[5]-box[4])]
    d=max(range(3),key=lambda i:widths[i]);m=(box[2*d]+box[2*d+1])/2
    left=list(box);right=list(box);left[2*d+1]=m;right[2*d]=m
    return tuple(left),tuple(right)


def volume(box):return (box[1]-box[0])*(box[3]-box[2])*(box[5]-box[4])


def outside_container(box,L):
    lo,hi=box[4:];vs=[abs(lo),abs(hi)]
    if lo<=0<=hi:vs.append(F(0))
    spans=[(1-v*v+2*v)/(1+v*v) for v in vs]
    w=min(spans);h=w/2
    return box[1]<h or box[0]>L-h or box[3]<h or box[2]>L-h


def lower_function(name):
    if name=='square':return pose_lower_bound
    if name=='robust':
        from robust_pose_core import best_lower_bound
        return best_lower_bound
    if name=='correlated':
        from correlated_pose_core import correlated_lower_bound
        return correlated_lower_bound
    if name=='correlated-adaptive1':
        from correlated_pose_core import adaptive_lower_bound
        return adaptive_lower_bound
    if name=='physical-correlated':
        from physical_pose_bound import physical_lower_bound
        return physical_lower_bound
    if name=='physical-adaptive1':
        from physical_pose_bound import adaptive_physical_lower_bound
        return adaptive_physical_lower_bound
    if name=='physical-adaptive2':
        from physical_pose_bound import adaptive2_physical_lower_bound
        return adaptive2_physical_lower_bound
    raise ValueError('Unknown bound method')


def verify(candidate,certificate):
    data=json.loads(candidate.read_text());model=expand(data);q=certificate
    assert q['model']=='FULL_SIGNED_POSE_LOW_COVER_V1' and q['digest']==model[-1]
    threshold=F(q['threshold']);assert threshold>0
    bound_cache={}
    def bound_for(name):
        if name not in bound_cache:
            bound_cache[name]=cached_bound(model,lower_function(name),q.get('symmetry'))[0]
        return bound_cache[name]
    leaves=q['leaves'];seen=set()
    # Index all occupied prefixes once. Repeated full scans at every internal
    # node otherwise make topology verification quadratic in the leaf count.
    prefixes=set()
    for path in leaves:
        assert isinstance(path,str) and set(path)<=set('01'),('invalid path',path)
        prefixes.update(path[:i] for i in range(len(path)+1))
    def visit(path,box):
        if path in leaves:
            rec=leaves[path];seen.add(path)
            assert list(map(str,box))==rec['box']
            if rec['kind']=='OUTSIDE':assert outside_container(box,model[0]);return
            assert rec['kind'] in ('HIGH','POSSIBLE_LOW')
            lower=bound_for(rec.get('bound_method',q.get('bound_method','square')))(*box)
            assert lower==F(rec['lower'])
            assert (rec['kind']=='HIGH')==(lower>=threshold)
            return
        # Reject an absent branch immediately, instead of an infinite walk.
        assert path+'0' in prefixes,('missing left',path)
        assert path+'1' in prefixes,('missing right',path)
        a,b=split(box);visit(path+'0',a);visit(path+'1',b)
    visit('',root_box(model[0]));assert seen==set(leaves)
    return dict(status='EXACT_COMPLETE_POSE_COVER_REPLAYED',leaves=len(leaves),
                high=sum(r['kind']=='HIGH' for r in leaves.values()),
                possible_low=sum(r['kind']=='POSSIBLE_LOW' for r in leaves.values()),
                outside=sum(r['kind']=='OUTSIDE' for r in leaves.values()),
                general_packing_exclusion=False)


def run(candidate,out,threshold,max_nodes=511,bound_method='square'):
    lower_bound=lower_function(bound_method)
    if max_nodes<1:raise ValueError('Need at least one node')
    model=expand(json.loads(candidate.read_text()));start=time.monotonic()
    leaves={};queue=[];evaluations=0
    def add(path,box):
        nonlocal evaluations
        evaluations+=1
        if outside_container(box,model[0]):kind='OUTSIDE';lb=None
        else:
            lb=lower_bound(model,*box);kind='HIGH' if lb>=threshold else 'POSSIBLE_LOW'
        leaves[path]=dict(box=list(map(str,box)),kind=kind,lower=None if lb is None else str(lb))
        if kind=='POSSIBLE_LOW':heapq.heappush(queue,(-volume(box),path,box))
    add('',root_box(model[0]))
    while queue and evaluations+2<=max_nodes:
        _,path,box=heapq.heappop(queue);del leaves[path];a,b=split(box)
        add(path+'0',a);add(path+'1',b)
    q=dict(model='FULL_SIGNED_POSE_LOW_COVER_V1',bound_method=bound_method,digest=model[-1],threshold=str(threshold),
           source_sha256=hashlib.sha256(candidate.read_bytes()).hexdigest(),leaves=leaves,
           evaluations=evaluations,seconds=time.monotonic()-start,
           limitation='Complete overcover of all physical poses; possible-low cells include unresolved cells. No capacity or packing exclusion yet.')
    out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(q,indent=2))
    replay=verify(candidate,json.loads(out.read_text()));out.with_suffix('.replay.json').write_text(json.dumps(replay,indent=2))
    print(json.dumps(dict(**replay,evaluations=evaluations,seconds=q['seconds'])),flush=True)
    return q

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('candidate',type=Path);p.add_argument('out',type=Path)
    p.add_argument('--bound',choices=['square','robust'],default='square')
    p.add_argument('--threshold',type=F,default=F(4,5));p.add_argument('--nodes',type=int,default=511)
    a=p.parse_args();run(a.candidate,a.out,a.threshold,a.nodes,a.bound)
