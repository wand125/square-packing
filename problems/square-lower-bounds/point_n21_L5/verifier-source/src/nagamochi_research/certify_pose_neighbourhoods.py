"""Grow PL42 certificates around repaired poses using exact full-box capture.
A failed finite radius search is not a nonexistence result.
"""
from fractions import Fraction as F
from pathlib import Path
import json,hashlib
from compile_box_capture_rows import geometry,contains_all,compile_rows,replay_rows
from refit_external_point_weights import read,exact_hits


def run(candidate,poses,previous,out,start=F(1,1000),max_halvings=16):
    start=F(start)
    if start<=0 or max_halvings<0:raise ValueError('Invalid radius search')
    out.mkdir(exist_ok=False)
    previous_result=replay_rows(previous,candidate)
    old=json.loads(previous.read_text())
    if previous_result['passed_rows']!=len(old['rows']):raise ValueError('Previous proof not preserved')
    roots=[dict(root_index=r['root_index'],root=r['root'],leaves=[dict(box=v['box'],indices=v['indices']) for v in old['rows'] if v['root_index']==r['root_index']]) for r in old['roots']]
    L,coords,weights,digest=geometry(candidate);_,span,W,pts=read(candidate);attempts=[]
    labels={r['root_index'] for r in roots}
    for i,pose in enumerate(poses):
        cx,cy,t=map(F,pose);hit=exact_hits(pts,L,span,pose);indices=[j for j,h in enumerate(hit) if h]
        radius=min(start,cx/2,(L-cx)/2,cy/2,(L-cy)/2)
        if radius<=0:raise ValueError('No centre interior')
        accepted=None
        for depth in range(max_halvings+1):
            box=[cx-radius,cx+radius,cy-radius,cy+radius,max(F(0),t-radius),min(F(1,2),t+radius)]
            inside=[j for j in indices if contains_all(coords[j],box)]
            mass=sum((weights[j] for j in inside),F(0))
            if mass>=1:
                label='pose-neighbourhood:'+hashlib.sha256(json.dumps(list(map(str,pose))).encode()).hexdigest()[:16]
                if label in labels:raise ValueError('Duplicate neighbourhood label')
                labels.add(label);root=list(map(str,box));roots.append(dict(root_index=label,root=root,leaves=[dict(box=root,indices=inside)]))
                accepted=dict(root_index=label,box=root,halfwidth=str(radius),halvings=depth,capture=str(mass),points=len(inside));break
            radius/=2
        attempts.append(dict(pose=list(map(str,pose)),certificate=accepted,status='CERTIFIED_LOCAL_BOX' if accepted else 'NO_CERTIFICATE_AT_TESTED_SCALES'))
    result=compile_rows(candidate,roots,out/'expanded-proof-rows.json')
    replay=replay_rows(out/'expanded-proof-rows.json',candidate)
    assert replay['passed_rows']==len(result['rows'])
    (out/'replay.json').write_text(json.dumps(replay,indent=2))
    report=dict(candidate_sha256=hashlib.sha256(candidate.read_bytes()).hexdigest(),previous_proof_sha256=hashlib.sha256(previous.read_bytes()).hexdigest(),previous_roots=len(old['roots']),previous_rows=len(old['rows']),new_roots=sum(r['certificate'] is not None for r in attempts),total_roots=len(result['roots']),total_rows=len(result['rows']),attempts=attempts,general_coverage_verified=False,root_labels_are_not_global_grid_indices=True)
    (out/'result.json').write_text(json.dumps(report,indent=2));return report
