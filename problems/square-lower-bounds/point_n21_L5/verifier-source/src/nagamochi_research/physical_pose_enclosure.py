"""Rational rectangular outer enclosure of physically admissible unit-square poses.

The returned box contains every admissible pose of the input box, but may contain
inadmissible poses. A bound on it certifies only admissible poses of the input.
"""
from fractions import Fraction as F


def enclose(L,box):
    L=F(L);b=list(map(F,box))
    if L<=0 or len(b)!=6 or any(b[i]>b[i+1] for i in (0,2,4)) or not 0<=b[4]<=b[5]<=F(1,2):
        raise ValueError('Invalid container or pose box')
    # h'(t)=(1-2t-t^2)/(1+t^2)^2 changes + to - at most once.
    # Therefore h has no interior minimum on this interval.
    h=min((1+2*t-t*t)/(2*(1+t*t)) for t in b[4:])
    clipped=[max(b[0],h),min(b[1],L-h),max(b[2],h),min(b[3],L-h),b[4],b[5]]
    return dict(L=str(L),original_box=list(map(str,b)),minimum_halfwidth=str(h),
                enclosing_box=None if clipped[0]>clipped[1] or clipped[2]>clipped[3] else list(map(str,clipped)),
                scope='physically admissible poses in original box')


def replay_partition(candidate,parent,records,candidate_sha256):
    import hashlib
    from compile_box_capture_rows import geometry,validate_partition
    from predicate_partition import replay_capture_record
    if hashlib.sha256(candidate.read_bytes()).hexdigest()!=candidate_sha256:raise ValueError('Candidate hash mismatch')
    L,coords,weights,_=geometry(candidate);points=[(*p,w) for p,w in zip(coords,weights)]
    validate_partition(parent,[r['enclosure']['original_box'] for r in records])
    bounds=[];empty=0
    for record in records:
        enclosure=record['enclosure'];expected=enclose(L,enclosure['original_box'])
        if expected!=enclosure:raise ValueError('Invalid physical enclosure')
        box=expected['enclosing_box'];proof=record['proof']
        if box is None:
            if proof is not None:raise ValueError('Unexpected proof for empty enclosure')
            empty+=1;continue
        if proof is None or list(map(F,proof['box']))!=list(map(F,box)):raise ValueError('Wrong proof box')
        if proof.get('proof_type')=='PHYSICAL_SIGNED_CONFLICTS':
            from physical_predicate_conflict import replay
            result=replay(points,proof,L)
        elif proof.get('proof_type')=='PHYSICAL_PREDICATE_TREE':
            from physical_predicate_branch import replay
            result=replay(points,proof,L)
        else:
            result=replay_capture_record(points,proof)
        bounds.append(F(result['lower']))
    return dict(candidate_sha256=candidate_sha256,parent=list(map(str,parent)),partition_verified=True,
                empty_leaves=empty,nonempty_leaves=len(bounds),lower=str(min(bounds)) if bounds else None,
                certified_unit_capture=all(b>=1 for b in bounds),vacuous=not bounds,
                scope='physically admissible poses in original parent',general_coverage_verified=False)
