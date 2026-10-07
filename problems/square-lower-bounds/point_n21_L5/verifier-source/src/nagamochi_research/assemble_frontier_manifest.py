"""Bind distributed artifacts to one frontier; numerical replay is separate."""
import gzip
import hashlib
import json
from fractions import Fraction as F
from pathlib import Path


def validate_allocation(allocation, total):
    if type(total) is not int or total < 0 or allocation['total'] != total:
        raise ValueError('Wrong frontier size')
    def indices(values):
        if any(type(i) is not int or not 0 <= i < total for i in values):
            raise ValueError('Invalid allocation index')
        if len(values) != len(set(values)):
            raise ValueError('Duplicate allocation index')
        return set(values)
    saved = indices([e['index'] for e in allocation['saved']])
    remaining = indices(allocation['remaining'])
    assigned = []
    for values in allocation['groups'].values():
        indices(values)
        assigned.extend(values)
    if indices(assigned) != remaining or saved & remaining or saved | remaining != set(range(total)):
        raise ValueError('Allocation gap or overlap')


def assemble(candidate, frontier, allocation, campaign_entries, replacements):
    sha = hashlib.sha256(Path(candidate).read_bytes()).hexdigest()
    raw = Path(frontier).read_bytes()
    fsha = hashlib.sha256(raw).hexdigest()
    data = json.loads(raw)
    if data['candidate_sha256'] != sha or allocation['candidate_sha256'] != sha or allocation['frontier_sha256'] != fsha:
        raise ValueError('Allocation input mismatch')
    total = len(data['pending'])
    validate_allocation(allocation, total)
    selected = {}
    unavailable = []
    superseded = []
    # Replacement precedence is explicit; no last-write-wins within a class.
    for kind, entries in [('CAMPAIGN', campaign_entries), ('JOINED_PARENT', replacements)]:
        seen = set()
        for e in entries:
            i = e['index']
            if type(i) is not int or not 0 <= i < total or i in seen or e['kind'] != kind:
                raise ValueError('Invalid or duplicate artifact index')
            seen.add(i)
            path = Path(e['path']) if e.get('path') else None
            if path is None or not path.is_file():
                unavailable.append(dict(index=i, kind=kind, path=e.get('path'), remote_job=e.get('remote_job')))
                continue
            raw = path.read_bytes()
            if hashlib.sha256(raw).hexdigest() != e['sha256']:
                raise ValueError('Artifact hash mismatch')
            proof = json.loads(gzip.decompress(raw) if path.suffix == '.gz' else raw)
            if kind == 'CAMPAIGN':
                c = proof['context']
                if (c['candidate_sha256'], c['frontier_sha256'], c['global_leaf_index'], c['input']) != (sha, fsha, i, data['pending'][i]):
                    raise ValueError('Campaign binding mismatch')
                if e.get('config_sha256') and c['config_sha256'] != e['config_sha256']:
                    raise ValueError('Campaign configuration mismatch')
            elif proof['candidate_sha256'] != sha or tuple(map(F, proof['parent'])) != tuple(map(F, data['pending'][i]['box'])):
                raise ValueError('Replacement binding mismatch')
            if i in selected:
                superseded.append(selected[i])
            selected[i] = dict(index=i, kind=kind, path=str(path), sha256=e['sha256'])
    return dict(candidate_sha256=sha, frontier_sha256=fsha, total=total,
                entries=[selected[i] for i in sorted(selected)], superseded=superseded,
                unavailable=unavailable, missing=sorted(set(range(total))-selected.keys()),
                artifact_bindings_verified=True, numerical_replay_performed=False,
                frontier_capture_verified=False, general_coverage_verified=False)
