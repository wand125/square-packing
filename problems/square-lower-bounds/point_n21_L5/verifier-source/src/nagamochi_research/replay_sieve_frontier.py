"""Solver-free replay of saved sieve partitions and their exact residual list.

This establishes one link in a coverage chain. It does not certify omitted
upstream regions, unresolved downstream boxes, or a general packing bound.
"""
import hashlib
import json
from fractions import Fraction as F
from compile_box_capture_rows import geometry, validate_partition
from physical_pose_enclosure import enclose
from point_box_sieve import replay as replay_points


def replay(candidate, source, records, residual, progress=None):
    paths = dict(candidate=candidate, source=source, records=records, residual=residual)
    hashes = {k: hashlib.sha256(p.read_bytes()).hexdigest() for k,p in paths.items()}
    incoming = json.loads(source.read_text()); outgoing = json.loads(residual.read_text())
    if incoming['candidate_sha256'] != hashes['candidate'] or outgoing['candidate_sha256'] != hashes['candidate']:
        raise ValueError('Frontier candidate mismatch')
    L, coords, weights, _ = geometry(candidate)
    pending, counts = [], dict(parents=0, captured_leaves=0, empty_leaves=0, completed_parents=0)
    with records.open() as stream:
        for index, line in enumerate(stream):
            if index >= len(incoming['pending']):
                raise ValueError('Extra sieve parent')
            row = json.loads(line); parent = incoming['pending'][index]
            if type(row['index']) is not int or row['index'] != index or row['parent_index'] != parent['parent_index']:
                raise ValueError('Sieve parent identity mismatch')
            if tuple(map(F, row['root'])) != tuple(map(F, parent['box'])):
                raise ValueError('Sieve parent box mismatch')
            validate_partition(parent['box'], [leaf['enclosure']['original_box'] for leaf in row['leaves']])
            failed = []
            for leaf in row['leaves']:
                enclosure = leaf['enclosure']; expected = enclose(L, enclosure['original_box'])
                if enclosure != expected:
                    raise ValueError('Sieve physical enclosure mismatch')
                box, proof = expected['enclosing_box'], leaf['proof']
                if box is None:
                    if proof is not None:
                        raise ValueError('Unexpected empty-region proof')
                    counts['empty_leaves'] += 1
                elif proof is not None:
                    replay_points(coords, weights, box, proof)
                    counts['captured_leaves'] += 1
                else:
                    failed.append(dict(parent_index=parent['parent_index'], frontier_index=index,
                                       box=enclosure['original_box']))
            if type(row['completed']) is not bool or row['completed'] != (not failed):
                raise ValueError('Incorrect parent completion flag')
            pending.extend(failed); counts['parents'] += 1; counts['completed_parents'] += not failed
            if progress and counts['parents'] % 100 == 0:
                progress(dict(counts, residual_leaves=len(pending)))
    if counts['parents'] != len(incoming['pending']):
        raise ValueError('Missing sieve parents')
    if pending != outgoing['pending']:
        raise ValueError('Residual list differs: gap, duplicate, order or geometry')
    # Refuse a mixed snapshot if an input was modified during a long replay.
    if hashes != {k: hashlib.sha256(p.read_bytes()).hexdigest() for k,p in paths.items()}:
        raise ValueError('Replay input changed')
    return dict(counts, residual_leaves=len(pending), input_sha256=hashes,
                partitions_verified=True, capture_proofs_replayed=True,
                residual_list_verified=True, upstream_coverage_verified=False,
                general_coverage_verified=False)
