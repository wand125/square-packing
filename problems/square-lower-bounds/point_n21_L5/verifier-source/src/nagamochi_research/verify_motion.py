"""Replay exact empty-square witnesses and conditional centre certificates."""
import json
from pathlib import Path
from fractions import Fraction as F
from motion_pilot import rows,strict_contains
from score import square
from motion_centres import setup,replay


def main():
    root=Path('runs/bentz_motion_20260926');data=json.loads((root/'motion-results.json').read_text())
    count=0
    for entry in data['baseline']:
        if entry['check']['status']!='EXACT_EMPTY_OPEN_SQUARE':continue
        p={key:F(value) for key,value in entry['check']['pose'].items()};k=entry['k']
        assert 0<p['delta']<=F(1,100)
        poly=square(p['cx'],p['cy'],1+p['delta'],p['t'])
        assert all(0<=x<=k and 0<=y<=k for x,y in poly)
        points=rows(k,colour=entry['colour'])
        assert points==[tuple(map(F,pt)) for pt in entry['check']['points']]
        assert not any(strict_contains(poly,pt) for pt in points)
        count+=1
    assert count==6
    for kind in ('middle','edge'):
        leaves=replay(json.loads((root/f'centre-{kind}.json').read_text()),*setup(kind))
        print(json.dumps(dict(kind=kind,leaves=leaves,status='VERIFIED_CONDITIONAL_CENTRE_LEMMA')))
    print(json.dumps(dict(empty_squares=count,status='VERIFIED_EXACT_ROW_COUNTEREXAMPLES')))


if __name__=='__main__':main()
