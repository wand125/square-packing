"""Exact data checks only: does not verify all-pose capture."""
from fractions import Fraction as F
from pathlib import Path
import argparse
import hashlib
import json

HASHES = {
    'n21-original.txt': '84a7dae793f05ff72de52ddcd3058e8518c1f84c461f94d11305adefe6137679',
    'n21-capture-one.txt': '9f631fbae420e0376ea636a232b7680e937deebe205dc035cfb9c43a3d74b456',
    'upstream-s21-lower-4.9950.txt': 'c8e8f878205f2da9c213e4a87c06f17c5a759dce7e695e676dd5c50e0994f2ef',
}


def read(path, expected):
    data = path.read_bytes()
    if hashlib.sha256(data).hexdigest() != expected:
        raise ValueError(f'SHA mismatch: {path}')
    a, b, d, w, n, *values = map(int, data.split())
    if min(a, b, d, w) <= 0 or n < 0 or len(values) != 3*n:
        raise ValueError('invalid header or record count')
    points = [(F(x,d), F(y,d), F(v,w)) for x,y,v in zip(values[::3],values[1::3],values[2::3])]
    side = F(a,b)
    if any(not (0 <= x <= side and 0 <= y <= side and v >= 0) for x,y,v in points):
        raise ValueError('invalid point or negative mass')
    return side, points


def inspect(directory):
    if not __debug__:
        raise RuntimeError('Python -O disables required assertions')
    records = {name: read(Path(directory)/name, digest) for name,digest in HASHES.items()}
    side, original = records['n21-original.txt']
    normalized_side, normalized = records['n21-capture-one.txt']
    upstream_side, upstream = records['upstream-s21-lower-4.9950.txt']
    q = F(249987,250000)
    assert side == normalized_side == 5 and upstream_side == F(5000,1001)
    assert len(original) == len(normalized) == len(upstream) == 4604
    assert normalized == [(x,y,v/q) for x,y,v in original]
    assert [(x,y) for x,y,v in original] == [(x*F(1001,1000),y*F(1001,1000)) for x,y,v in upstream]
    weights = {(x,y): v for x,y,v in original}
    assert len(weights) == 4604
    assert all(weights.get(p) == v for (x,y),v in weights.items() for p in [(5-x,y),(x,5-y),(y,x)])
    mass = sum(weights.values(),F())
    assert mass == F(2624862500021,125000000000)
    gap = 21*q-mass
    assert gap == F(999979,125000000000) > 0
    return dict(status='EXACT_CERTIFICATE_DATA_CHECKED', entries=4604,
                positive_entries=sum(v>0 for v in weights.values()),
                threshold=str(q), mass=str(mass), normalized_mass=str(mass/q),
                strict_gap=str(gap), d4_invariant=True,
                ordered_upstream_support_scale='1001/1000', hashes=HASHES,
                all_pose_capture_verified_by_this_script=False)


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--certificates', type=Path, default=Path(__file__).resolve().parent/'certificates')
    print(json.dumps(inspect(ap.parse_args().certificates), indent=2))
