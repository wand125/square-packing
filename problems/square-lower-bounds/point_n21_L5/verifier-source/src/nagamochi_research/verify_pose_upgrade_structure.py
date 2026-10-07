"""Check full-cover inheritance; numerical local bounds require separate replay."""
from fractions import Fraction as F
import hashlib,json
from pathlib import Path


def check(source,derived,local,source_sha):
    if local['source_sha256']!=source_sha:raise ValueError('Source hash mismatch')
    if source['digest']!=derived['digest']:raise ValueError('Measure mismatch')
    if source.get('symmetry')!=derived.get('symmetry'):raise ValueError('Symmetry changed')
    if set(source['leaves'])!=set(derived['leaves']):raise ValueError('Partition changed')
    values=local['values'];method=local['method'];threshold=F(derived['threshold'])
    if not set(values)<=set(source['leaves']):raise ValueError('Unknown local path')
    for path,old in source['leaves'].items():
        new=derived['leaves'][path]
        if old['box']!=new['box']:raise ValueError('Box changed')
        expected=dict(old)
        if old['kind']=='OUTSIDE':
            if path in values:raise ValueError('Outside leaf upgraded')
        else:
            value=F(values[path]) if path in values else F(old['lower'])
            if value>F(old['lower']):expected.update(lower=str(value),bound_method=method)
            expected['kind']='HIGH' if F(expected['lower'])>=threshold else 'POSSIBLE_LOW'
        if expected!=new:raise ValueError('Unexpected leaf mutation')
    return dict(status='COMPLETE_PARTITION_INHERITANCE_CHECKED',leaves=len(source['leaves']),
                local_values=len(values),requires_local_geometry_replay=True)


def verify(source,derived,local):
    return check(json.loads(source.read_text()),json.loads(derived.read_text()),
                 json.loads(local.read_text()),hashlib.sha256(source.read_bytes()).hexdigest())
