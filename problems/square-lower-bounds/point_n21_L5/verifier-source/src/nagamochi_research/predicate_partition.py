"""Replay PL45 leaf proofs and an exact rectangular partition of their parent."""
from fractions import Fraction as F
from pathlib import Path
import hashlib,json
from compile_box_capture_rows import geometry,validate_partition
from predicate_lp_capture import replay_certificate


def replay_partition(candidate,proofs,parent,labels):
    if hashlib.sha256(candidate.read_bytes()).hexdigest()!=proofs['candidate_sha256']:
        raise ValueError('Candidate hash mismatch')
    if not labels or len(set(labels))!=len(labels):raise ValueError('Invalid leaf labels')
    records=proofs['records'];by_label={r['label']:r for r in records}
    if len(by_label)!=len(records):raise ValueError('Duplicate certificate labels')
    if any(label not in by_label for label in labels):raise ValueError('Missing leaf')
    chosen=[by_label[label] for label in labels]
    validate_partition(parent,[r['box'] for r in chosen])
    _,coords,weights,digest=geometry(candidate);points=[(*p,w) for p,w in zip(coords,weights)]
    replay=[replay_capture_record(points,r) for r in chosen]
    lower=min(F(r['lower']) for r in replay)
    return dict(candidate_sha256=proofs['candidate_sha256'],geometry_sha256=digest,
                parent=list(map(str,parent)),labels=labels,partition_verified=True,
                leaves_replayed=len(replay),lower=str(lower),certified_unit_capture=lower>=1,
                general_coverage_verified=False)


def replay_capture_record(points,record):
    if record.get('proof_type') in ('PHYSICAL_SIGNED_CONFLICTS','PHYSICAL_PREDICATE_TREE'):
        raise ValueError('Physical proof requires independently supplied container context')
    if 'tree' in record:
        from predicate_branch import replay_model,replay_tree,cut_callbacks
        if tuple(map(F,record['box']))!=tuple(map(F,record['base']['box'])):raise ValueError('Changed branch proof box')
        cost,rows,baseline=replay_model(points,record['base'])
        _,verify=cut_callbacks(points,record['base'])
        result=replay_tree(cost,rows,baseline,F(record['target']),record['tree'],cut_verifier=verify)
        # An unresolved tree still has the universal nonnegative capture bound.
        return dict(result,lower=record['target'] if result['certified_unit_capture'] else '0')
    if 'base' in record:
        from predicate_conflict import replay_strengthened
        return replay_strengthened(points,record)
    return replay_certificate(points,record['box'],record)
