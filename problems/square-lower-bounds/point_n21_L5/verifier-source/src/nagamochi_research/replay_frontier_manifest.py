"""Replay a frontier's ordinary campaign proofs and replacement parent proofs.

Missing entries remain missing; a partial audit never certifies the frontier.
Even a closed frontier is only one part of the global coverage chain.
"""
from pathlib import Path
from fractions import Fraction as F
import hashlib,json,gzip
from physical_pose_enclosure import replay_partition
from near_axis_partition_bridge import replay_parent


def replay(candidate,frontier,entries):
    sha=hashlib.sha256(candidate.read_bytes()).hexdigest()
    fsha=hashlib.sha256(frontier.read_bytes()).hexdigest()
    data=json.loads(frontier.read_text())
    if data['candidate_sha256']!=sha:raise ValueError('Frontier candidate mismatch')
    seen=set();results=[]
    for entry in entries:
        index=entry['index']
        if type(index)is not int or not 0<=index<len(data['pending']) or index in seen:
            raise ValueError('Invalid or duplicate frontier index')
        seen.add(index);path=Path(entry['path']);raw=path.read_bytes()
        if hashlib.sha256(raw).hexdigest()!=entry['sha256']:raise ValueError('Artifact hash mismatch')
        proof=json.loads(gzip.decompress(raw) if path.suffix=='.gz' else raw)
        box=data['pending'][index]['box']
        if entry['kind']=='CAMPAIGN':
            context=proof['context']
            if context['candidate_sha256']!=sha or context['frontier_sha256']!=fsha or context['global_leaf_index']!=index:
                raise ValueError('Campaign context mismatch')
            if context['input']!=data['pending'][index]:raise ValueError('Campaign input mismatch')
            checked=replay_partition(candidate,box,proof['proof']['records'],sha)
        elif entry['kind']=='JOINED_PARENT':
            if proof['candidate_sha256']!=sha or tuple(map(F,proof['parent']))!=tuple(map(F,box)):
                raise ValueError('Replacement parent mismatch')
            checked=replay_parent(candidate,box,proof['pieces'],sha)
        else:raise ValueError('Unknown frontier proof kind')
        results.append(dict(index=index,kind=entry['kind'],proof_sha256=entry['sha256'],replay=checked))
    missing=sorted(set(range(len(data['pending'])))-seen)
    unresolved=[r['index'] for r in results if not r['replay']['certified_unit_capture']]
    return dict(candidate_sha256=sha,frontier_sha256=fsha,total=len(data['pending']),
                verified=len(results),certified=len(results)-len(unresolved),
                missing=missing,unresolved=unresolved,records=results,
                frontier_capture_verified=not missing and not unresolved,
                general_coverage_verified=False)
