"""PL39: convert a shrunken-square centre certificate into an angle band."""
from fractions import Fraction as F
from pathlib import Path
import argparse, json, hashlib
from probe_external_integer_bridge import read


def band(t, side):
    t, side = F(t), F(side)
    if not 0 < side <= 1 or not 0 <= t <= F(1, 2):
        raise ValueError('Invalid side or nominal half-angle')
    q = min(F(1, 4), (1-side)/(2*side))
    assert side*(1+2*q) <= 1
    return max(F(0), (t-q)/(1+t*q)), min(F(1, 2), (t+q)/(1-t*q)), q


def merge_bands(intervals):
    merged=[]
    for lo,hi in sorted(intervals):
        assert 0<=lo<=hi<=F(1,2)
        if merged and lo<=merged[-1][1]:
            merged[-1]=(merged[-1][0],max(hi,merged[-1][1]))
        else:
            merged.append((lo,hi))
    gaps=[];end=F(0)
    for lo,hi in merged:
        if lo>end:gaps.append((end,lo))
        end=hi
    if end<F(1,2):gaps.append((end,F(1,2)))
    return merged,gaps


def run(source, directory, out, separation_name='fixed-angle3.json'):
    assert not out.exists()
    digest = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    meta = json.loads((directory/'normalization.json').read_text())
    normalized = directory/'normalized.txt'
    assert digest(source) == meta['source_sha256']
    assert digest(normalized) == meta['normalized_sha256']
    side = F(meta['inner_square_side'])
    L, span, W, pts = read(source)
    M, other_span, other_W, other = read(normalized)
    assert M == L/side and W == other_W and len(pts) == len(other)
    for (x,y,w), (u,v,z) in zip(pts,other):
        assert w == z and F(x)*L/span/side == F(u)*M/other_span
        assert F(y)*L/span/side == F(v)*M/other_span
    separation = directory/separation_name
    result = json.loads(separation.read_text())
    assert result['candidate_sha256'] == digest(normalized)
    bands = []
    for r in result['records']:
        minimum = F(r['minimum_numerator'], W)
        assert minimum == F(r['minimum'])
        if minimum < 1:
            continue
        lo, hi, q = band(F(r['t']), side)
        bands.append(dict(nominal=r['t'], lower=str(lo), upper=str(hi),
                          relative_half_angle_radius=str(q), capture_lower=str(minimum)))
    merged,gaps=merge_bands([(F(b['lower']),F(b['upper'])) for b in bands])
    data = dict(status='CERTIFIED_ALL_CENTRE_ANGLE_BANDS',
                source_sha256=digest(source), separation_sha256=digest(separation),
                physical_L=str(L), inner_square_side=str(side), bands=bands,
                merged_bands=[list(map(str,b)) for b in merged],
                intervals_needing_verification=[list(map(str,b)) for b in gaps],
                covered_half_angle_length=str(sum((hi-lo for lo,hi in merged),F(0))),
                all_half_angles_covered=not gaps,
                independent_separator_replay=False, general_coverage_verified=False)
    out.write_text(json.dumps(data, indent=2))
    print(data)


if __name__ == '__main__':
    p=argparse.ArgumentParser()
    p.add_argument('source',type=Path);p.add_argument('directory',type=Path);p.add_argument('out',type=Path)
    p.add_argument('--separation',default='fixed-angle3.json')
    a=p.parse_args();run(a.source,a.directory,a.out,a.separation)
