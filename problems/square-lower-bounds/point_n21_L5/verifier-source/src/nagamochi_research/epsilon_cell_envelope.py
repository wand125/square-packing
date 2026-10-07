"""One rational relaxation for every real 0 < epsilon <= epsilon_max.

L=k-epsilon. Near-axis boxes have |tan(theta/2)| <= epsilon/10000.
Their epsilon-dependent axis inner side is 1-epsilon/50, larger than
the actual centre-cell width. Occupancy and ordered neighbour separation
are derived BEFORE replacing centres and inner sides by uniform envelopes.
"""
from fractions import Fraction as F
from functools import lru_cache
from itertools import combinations
from pathlib import Path
import json,time,hashlib
from fixed_orientation_cover import angle_envelope
from joint_angle_lp import rotation
from saturated_axis_cells import subtract_open,remove_contained
from saturated_joint_search import assemble_model,search_model,replay_model
from replay_saturated_pairs import static_exclusions,clique_upper


def convex_hull(points):
    points=sorted(set(points))
    if len(points)<=1:return points
    def cross(a,b,c):return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
    lower=[];upper=[]
    for p in points:
        while len(lower)>1 and cross(lower[-2],lower[-1],p)<=0:lower.pop()
        lower.append(p)
    for p in reversed(points):
        while len(upper)>1 and cross(upper[-2],upper[-1],p)<=0:upper.pop()
        upper.append(p)
    return lower[:-1]+upper[:-1]


def coalesce(pieces,t,R):
    """Enlarge unions to convex hulls only if each hull still has capacity one."""
    c,s=rotation(t);pieces=list(pieces)
    while True:
        merged=False
        for i,j in combinations(range(len(pieces)),2):
            vertices=pieces[i]+pieces[j]
            if all(max(a*x+b*y for x,y in vertices)-min(a*x+b*y for x,y in vertices)<R for a,b in ((c,s),(-s,c))):
                hull=convex_hull(vertices)
                pieces=[p for z,p in enumerate(pieces) if z not in (i,j)]+[hull]
                merged=True;break
        if not merged:return pieces


def parameters(k,eps_max=F(1,1000),t=F(1,100),rot_h=F(1,100000)):
    E,span=angle_envelope(t,rot_h)
    return dict(k=k,eps_max=str(eps_max),t=str(t),rot_h=str(rot_h),
                axis_inner=str(1-eps_max/50),rot_inner=str(F(999999,1000000)/E),
                rot_half=str((k-span)/2),axis_h_rule='epsilon/10000',axis_inner_rule='1-epsilon/50')


def check_parameters(q):
    k=q['k'];em=F(q['eps_max']);A=F(q['axis_inner']);R=F(q['rot_inner'])
    assert k in (4,5,6,7,8)
    assert 0<em<=(F(1,1000) if k in (4,5) else F(1,10))
    assert q['axis_h_rule']=='epsilon/10000' and q['axis_inner_rule']=='1-epsilon/50'
    assert A==1-em/50 and 0<A<1
    # For every epsilon>0:
    # 1-(1-e/50)(1+e/5000) = e*(1/50-1/5000)+e^2/250000 > 0.
    # (1-e/50)-(1-e/(k-1)) = e*(1/(k-1)-1/50) > 0.
    assert F(1,50)-F(1,5000)>0 and F(1,k-1)-F(1,50)>0
    E,span=angle_envelope(F(q['t']),F(q['rot_h']))
    assert 0<R<=1 and R*E<1 and F(q['rot_half'])>=(k-span)/2


@lru_cache(maxsize=64)
def domains(encoded,missing):
    q=json.loads(encoded);check_parameters(q)
    k=q['k'];em=F(q['eps_max']);A=F(q['axis_inner']);R=F(q['rot_inner']);H=F(q['rot_half'])
    assert len(set(missing))==len(missing) and all(type(i) is int and 0<=i<(k-1)**2 for i in missing)
    intervals=[]
    for i in range(k-1):
        a=F(i,k-1)-F(1,2);b=F(i+1,k-1)-F(1,2)
        intervals.append((min(a*(k-1),a*(k-1-em)),max(b*(k-1),b*(k-1-em))))
    cells={}
    for i,(x,X) in enumerate(intervals):
        for j,(y,Y) in enumerate(intervals):
            index=i*(k-1)+j
            if index not in missing:cells[index]=[(x,y),(X,y),(X,Y),(x,Y)]
    c,s=rotation(F(q['t']));w=c+s
    pieces=[[(-H,-H),(H,-H),(H,H),(-H,H)]]
    for cell in cells.values():
        inequalities=[]
        for a,b,threshold in ((F(1),F(0),(A+R*w)/2),(F(0),F(1),(A+R*w)/2),
                              (c,s,(R+A*w)/2),(-s,c,(R+A*w)/2)):
            for sign in (-1,1):
                aa,bb=sign*a,sign*b
                inequalities.append((aa,bb,threshold+min(aa*x+bb*y for x,y in cell)))
        new={}
        for p in pieces:
            for z in subtract_open(p,inequalities):new[tuple(sorted(set(z)))]=z
        pieces=list(new.values())
    return cells,coalesce(remove_contained(pieces),F(q['t']),R)


def geometry(q,missing):
    return domains(json.dumps(q,sort_keys=True),tuple(missing))


def model(q,missing,chosen):
    cells,pieces=geometry(q,missing);k=q['k'];A=F(q['axis_inner']);R=F(q['rot_inner']);t=F(q['t'])
    indices={v:i for i,v in enumerate(cells)};polys=list(cells.values())+[pieces[i] for i in chosen]
    n=len(polys);forced=[]
    for cell,idx in indices.items():
        i,j=divmod(cell,k-1)
        for other,axis,valid in ((cell+k-1,0,i<k-2),(cell+1,1,j<k-2)):
            if valid and other in indices:
                row=[F(0)]*(2*n);row[2*idx+axis]=1;row[2*indices[other]+axis]=-1
                forced.append((row,-A))
    return assemble_model(polys,[F(0)]*len(cells)+[t]*len(chosen),[A]*len(cells)+[R]*len(chosen),forced)


def verify(q):
    config=q['config'];missing=q['missing'];check_parameters(config)
    cells,pieces=geometry(config,missing);N=len(pieces);assert q['regions']==N
    c,s=rotation(F(config['t']));R=F(config['rot_inner'])
    for p in pieces:
        assert all(max(a*x+b*y for x,y in p)-min(a*x+b*y for x,y in p)<R for a,b in ((c,s),(-s,c)))
    excluded=static_exclusions(pieces,F(config['t']),R);seen=set()
    for case in q['cases']:
        chosen=tuple(case['chosen']);assert len(chosen)==2 and 0<=chosen[0]<chosen[1]<N and chosen not in seen
        seen.add(chosen)
        if replay_model(model(config,missing,chosen),case['tree']):excluded.add(chosen)
    assert excluded==set(map(tuple,q['excluded_pairs']))
    upper=clique_upper(N,excluded);assert upper==q['rotated_count_upper']
    return dict(status='EXACT_UNIFORM_EPSILON_PAIR_BOUND',axis_boxes=len(cells),rotated_count_upper=upper,
                epsilon_interval=f"0 < epsilon <= {config['eps_max']}",regions=N)


def run(config,missing,out):
    cells,pieces=geometry(config,missing);N=len(pieces);c,s=rotation(F(config['t']));R=F(config['rot_inner'])
    assert all(max(a*x+b*y for x,y in p)-min(a*x+b*y for x,y in p)<R for p in pieces for a,b in ((c,s),(-s,c)))
    excluded=static_exclusions(pieces,F(config['t']),R);cases=[];start=time.monotonic()
    q=dict(status='RUNNING',config=config,missing=list(missing),regions=N)
    for edge in combinations(range(N),2):
        if edge in excluded:continue
        data=model(config,missing,edge);case=search_model(data,300);case['chosen']=list(edge);cases.append(case)
        if replay_model(data,case['tree']):excluded.add(edge)
        q.update(cases=cases,excluded_pairs=sorted(excluded),seconds=time.monotonic()-start)
        out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(q,indent=2))
    q.update(rotated_count_upper=clique_upper(N,excluded),status='EXACT_UNIFORM_EPSILON_PAIR_BOUND')
    q['replay']=verify(q);out.write_text(json.dumps(q,indent=2));print(out.name,q['replay'],q['seconds'],flush=True)
    return q


def remaining_groups(base,target):
    excluded=set(map(tuple,base['excluded_pairs']))
    return [v for v in combinations(range(base['regions']),target)
            if not any(e in excluded for e in combinations(v,2))]


def verify_completion(base,q):
    verify(base)
    target=q['target'];assert type(target) is int and target>0
    expected=set(remaining_groups(base,target));seen=set();excluded=set()
    for case in q['cases']:
        chosen=tuple(case['chosen']);assert chosen in expected and chosen not in seen
        seen.add(chosen)
        if replay_model(model(base['config'],base['missing'],chosen),case['tree']):excluded.add(chosen)
    return dict(target_rotated_count=target,joint_groups=len(expected),remaining_groups=len(expected-excluded),
                target_excluded=expected==excluded)


def complete(source,target,out):
    raw=source.read_bytes();base=json.loads(raw);verify(base)
    q=dict(source=source.name,source_sha256=hashlib.sha256(raw).hexdigest(),target=target,cases=[])
    for chosen in remaining_groups(base,target):
        data=model(base['config'],base['missing'],chosen);case=search_model(data,3000);case['chosen']=list(chosen)
        q['cases'].append(case);out.write_text(json.dumps(q,indent=2))
        print(out.name,chosen,case['status'],case['nodes'],flush=True)
    q['replay']=verify_completion(base,q);out.write_text(json.dumps(q,indent=2));print(q['replay'],flush=True)
    return q


def verify_hyper_completion(base,q):
    verify(base);target=q['target'];assert type(target) is int and target>0
    groups=set(remaining_groups(base,target));seen=set()
    for case in q['cases']:
        chosen=tuple(case['chosen'])
        assert 2<=len(chosen)<=target and tuple(sorted(set(chosen)))==chosen
        assert all(0<=i<base['regions'] for i in chosen) and chosen not in seen
        seen.add(chosen)
        if replay_model(model(base['config'],base['missing'],chosen),case['tree']):
            groups={v for v in groups if not set(chosen)<=set(v)}
    return dict(target_rotated_count=target,remaining_groups=len(groups),target_excluded=not groups)


def hyper_complete(source,target,out,attempt_limit=30):
    """Price small forbidden subsets by how many target groups they remove."""
    from collections import Counter
    raw=source.read_bytes();base=json.loads(raw);verify(base)
    q=dict(source=source.name,source_sha256=hashlib.sha256(raw).hexdigest(),target=target,cases=[])
    remaining=set(remaining_groups(base,target));tried=set()
    for _ in range(attempt_limit):
        if not remaining:break
        counts=Counter(s for group in sorted(remaining) for s in combinations(group,min(3,target)) if s not in tried)
        if counts:
            chosen=min(counts,key=lambda s:(-counts[s],s))
        else:
            available=remaining-tried
            if not available:break
            chosen=min(available)
        tried.add(chosen);data=model(base['config'],base['missing'],chosen)
        case=search_model(data,1000);case['chosen']=list(chosen);q['cases'].append(case)
        if replay_model(data,case['tree']):remaining={v for v in remaining if not set(chosen)<=set(v)}
        q['remaining_groups']=len(remaining);out.write_text(json.dumps(q,indent=2))
        print(out.name,chosen,case['status'],case['nodes'],'remaining',len(remaining),flush=True)
    q['replay']=verify_hyper_completion(base,q);out.write_text(json.dumps(q,indent=2));print(q['replay'],flush=True)
    return q


def direct_remaining(source,target,seeds,out):
    """Reuse verified small cuts, then search target-size groups directly."""
    import os
    from datetime import datetime,timezone
    raw=source.read_bytes();base=json.loads(raw);verify(base);digest=hashlib.sha256(raw).hexdigest()
    q=dict(source=source.name,source_sha256=digest,target=target,cases=[],status='RUNNING',
           worker_pid=os.getpid(),started=datetime.now(timezone.utc).isoformat())
    remaining=set(remaining_groups(base,target));seen=set();start=time.monotonic()
    for seed in seeds:
        payload=json.loads(seed.read_text());assert payload['source_sha256']==digest and payload['target']==target
        for case in payload['cases']:
            chosen=tuple(case['chosen'])
            if chosen in seen:continue
            if replay_model(model(base['config'],base['missing'],chosen),case['tree']):
                q['cases'].append(case);seen.add(chosen);remaining={v for v in remaining if not set(chosen)<=set(v)}
    def save():
        q.update(remaining_groups=len(remaining),seconds=time.monotonic()-start)
        temp=out.with_suffix('.tmp');temp.write_text(json.dumps(q,indent=2));temp.replace(out)
    save()
    for chosen in sorted(remaining):
        data=model(base['config'],base['missing'],chosen);case=search_model(data,3000);case['chosen']=list(chosen)
        q['cases'].append(case)
        if replay_model(data,case['tree']):remaining.remove(chosen)
        save();print(out.name,chosen,case['status'],case['nodes'],'remaining',len(remaining),flush=True)
    q['replay']=verify_hyper_completion(base,q)
    q['status']='EXACT_CONDITIONAL_UNIFORM_EPSILON_EXCLUSION' if q['replay']['target_excluded'] else 'STOPPED_LOCAL_PROOF_REVIEW'
    save();print(q['replay'],flush=True)
    return q


if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('root',type=Path);a=p.parse_args()
    for k,representatives in ((4,[None,0,1,4]),(5,[None,0,1,2,5])):
        for m in representatives:
            run(parameters(k),[] if m is None else [m],a.root/f'k{k}-m{m}.json')
