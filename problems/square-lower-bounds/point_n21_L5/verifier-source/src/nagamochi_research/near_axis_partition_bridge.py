"""Join a recomputed PL44 closed near-axis band to a physical box partition.

Saved success flags are not trusted. The symbolic sweep and axis anchor are
recomputed from the candidate before using the band as a coverage leaf.
"""
from fractions import Fraction as F
import hashlib
import json
from certify_near_axis_sweep import sweep
from exact_fixed_angle_separator import separate
from probe_external_integer_bridge import read
from compile_box_capture_rows import validate_partition
from physical_pose_enclosure import replay_partition


def replay_band(candidate, record):
    sha = hashlib.sha256(candidate.read_bytes()).hexdigest()
    if record['candidate_sha256'] != sha:
        raise ValueError('Band candidate mismatch')
    L, span, W, points = read(candidate)
    if F(record['L']) != L or F(record['expansion_center']) != 0 or record['direction'] != 1:
        raise ValueError('Need the same container and forward axis band')
    fresh = sweep(L, int(F(span)/L), points)
    for key in ('interval', 'minimum_numerator', 'conditions_sha256'):
        if fresh[key] != record[key]:
            raise ValueError('Band replay mismatch: '+key)
    anchor = separate(L, int(F(span)/L), points, F(0))
    q = min(F(fresh['minimum_numerator'], W), F(anchor['minimum_numerator'], W))
    if F(record['minimum']) != F(fresh['minimum_numerator'], W) or F(record['anchor_minimum']) != F(anchor['minimum_numerator'], W):
        raise ValueError('Band mass mismatch')
    interval = fresh['interval']
    if F(interval['lower']) != 0 or interval['upper_open'] or q < 1:
        raise ValueError('Unproved closed near-axis capture')
    return dict(candidate_sha256=sha, upper=interval['upper'], lower=str(q))


def split_at_band(parent, upper):
    parent = list(map(F, parent)); upper = F(upper)
    if len(parent) != 6 or not 0 <= parent[4] < upper < parent[5] <= F(1,2):
        raise ValueError('Band must split the parent angle interval')
    low, high = parent.copy(), parent.copy()
    low[5] = upper; high[4] = upper
    validate_partition(parent, [low, high])
    return list(map(str, low)), list(map(str, high))


def replay_connection(candidate, parent, band_record, high_records):
    band = replay_band(candidate, band_record)
    return _replay_connection_checked(candidate, parent, band, high_records)


def _replay_connection_checked(candidate, parent, band, high_records):
    low, high = split_at_band(parent, band['upper'])
    checked = replay_partition(candidate, high, high_records, band['candidate_sha256'])
    q = F(band['lower'])
    if checked['lower'] is not None:
        q = min(q, F(checked['lower']))
    return dict(candidate_sha256=band['candidate_sha256'], parent=list(map(str,parent)),
                band_box=low, high_box=high, lower=str(q),
                partition_verified=True, band_recomputed=True,
                certified_unit_capture=q >= 1, high_replay=checked,
                scope='physically admissible poses in original parent',
                general_coverage_verified=False)


def replay_parent(candidate, parent, pieces, candidate_sha256):
    """Replay a complete parent with ordinary and PL50-connected pieces.

The per-call cache contains only bands recomputed here, never supplied flags.
"""
    if hashlib.sha256(candidate.read_bytes()).hexdigest() != candidate_sha256:
        raise ValueError('Parent candidate mismatch')
    validate_partition(parent, [p['box'] for p in pieces])
    results, bands = [], {}
    for piece in pieces:
        if piece['kind'] == 'PHYSICAL_PARTITION':
            checked = replay_partition(candidate, piece['box'], piece['records'], candidate_sha256)
        elif piece['kind'] == 'NEAR_AXIS_CONNECTION':
            proof = piece['proof']
            if list(map(F, proof['parent'])) != list(map(F, piece['box'])):
                raise ValueError('Connection parent mismatch')
            key = json.dumps(proof['band'], sort_keys=True, separators=(',', ':'))
            if key not in bands:
                bands[key] = replay_band(candidate, proof['band'])
            checked = _replay_connection_checked(candidate, piece['box'], bands[key], proof['high_records'])
        else:
            raise ValueError('Unknown parent piece kind')
        results.append(checked)
    bounds = [F(r['lower']) for r in results if r['lower'] is not None]
    return dict(candidate_sha256=candidate_sha256, parent=list(map(str,parent)),
                partition_verified=True, pieces=len(pieces), bands_recomputed=len(bands),
                lower=str(min(bounds)) if bounds else None,
                certified_unit_capture=all(r['certified_unit_capture'] for r in results),
                scope='physically admissible poses in original parent',
                general_coverage_verified=False)
