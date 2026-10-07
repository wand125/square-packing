"""Replay n45 motion, ownership and chord witnesses, and cubic certificate."""
from fractions import Fraction as F
import json
from n45_small_motion import ROOT,snapshot,heights
from n45_anchor_repair import common_snapshot,certificate
from score import square,segment_length
from motion_pilot import strict_contains,rows


def empty_check(points,w):
    side=F(w['side']) if 'side' in w else 1+F(w['delta'])
    poly=square(w['cx'],w['cy'],side,w['t'])
    assert all(0<=x<=7 and 0<=y<=7 for x,y in poly)
    assert not any(strict_contains(poly,p) for p in points)


def main():
    count=0;d=json.loads((ROOT/'results.json').read_text())
    for r in d['records']:
        for w in r['checks']:
            if 'pose' in w:empty_check(snapshot(r['colour'],r['focus'],w['phase'],F(w['time'])),w['pose']);count+=1
    d=json.loads((ROOT/'centre-audit.json').read_text())
    for r in d['records']:
        for w in r['tests']:
            if 'score' in w:empty_check(snapshot(r['colour'],r['focus'],'leftmost-right',F(1),F(r['endpoint'])),w);count+=1
    d=json.loads((ROOT/'anchor-repair.json').read_text());assert d['certificate']==certificate(F(847,1000),F(39,40))
    for r in d['records']:
        for w in r['checks']:
            if 'score' in w['test']:empty_check(common_snapshot(r['colour'],r['focus'],F(w['time'])),w['test']);count+=1
    chord=json.loads((ROOT/'chord-audit.json').read_text())
    for r in chord:
        for w in r['boxes']:
            p=square(w['cx'],w['cy'],w['side'],w['t']);cy=F(w['cy']);t=F(w['t']);side=F(w['side']);c=(1-t*t)/(1+t*t);s=2*t/(1+t*t);rad=side*(c+s)/2-c*s;cx=F(w['cx'])
            assert strict_contains(p,(F(r['left']),cy)) and strict_contains(p,(F(1),cy))
            assert all(0<=x<=7 and 0<=y<=7 for x,y in p)
            assert list(map(F,w['lines_with_chord_above_one']))==[cx-rad,cx+rad]
            assert all(segment_length(p,(x,0),(x,7))==1 for x in (cx-rad,cx+rad))
            assert segment_length(p,(F(457,500),0),(F(457,500),7))==F(w['chord_at_old_line'])
        assert r['no_common_vertical_line']==(F(r['boxes'][0]['lines_with_chord_above_one'][1])<F(r['boxes'][1]['lines_with_chord_above_one'][0]))
    for file in ('owner-probe.json','owner-singleton.json'):
        for w in json.loads((ROOT/file).read_text()):
            ys,_=heights(w['focus']);y=ys[w['focus']];p=square(w['cx'],w['cy'],w['side'],w['t'])
            assert all(0<=x<=7 and 0<=yy<=7 for x,yy in p)
            assert all(strict_contains(p,(x,y)) for x in (F(47,100),F(39,40))) and not strict_contains(p,(F(1),y))
            for c,key in ((0,'red_captures'),(1,'blue_captures')):
                assert [list(map(str,q)) for q in rows(7,ys,c) if strict_contains(p,q)]==w[key]
            if file=='owner-singleton.json':assert len(w['blue_captures'])==1
    result=dict(status='VERIFIED_LOCAL_WITNESSES_AND_CUBIC_CONDITION',empty_records=count,cubic_leaves=64,chord_pairs=3,owner_witnesses=4,scope='No n45 packing impossibility or full motion proof.')
    (ROOT/'check.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))

if __name__=='__main__':main()
