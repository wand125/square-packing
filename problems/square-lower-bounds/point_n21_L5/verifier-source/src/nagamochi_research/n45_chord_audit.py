"""Exact short-chord witnesses and incompatible single-line guarantees."""
from fractions import Fraction as F
import json
from n45_small_motion import ROOT
from score import square,segment_length
from motion_pilot import strict_contains


def main():
    t=F(2,5);c=F(21,29);s=F(20,29);side=F(1000001,1000000);r=side*(c+s)/2;threshold=r-c*s;cy=F(7,2);out=[]
    assert side/c>1 and side/s>1
    for left in (F(2,5),F(47,100),F(12,25)):
        centres=[r+F(1,1000),left+side/(2*c)-F(1,1000)];boxes=[]
        for cx in centres:
            poly=square(cx,cy,side,t)
            assert all(0<=x<=7 and 0<=y<=7 for x,y in poly)
            assert strict_contains(poly,(left,cy)) and strict_contains(poly,(F(1),cy))
            bounds=[cx-threshold,cx+threshold]
            assert all(segment_length(poly,(x,0),(x,7))==1 for x in bounds)
            boxes.append(dict(cx=str(cx),cy=str(cy),side=str(side),t=str(t),chord_at_old_line=str(segment_length(poly,(F(457,500),0),(F(457,500),7))),lines_with_chord_above_one=list(map(str,bounds))))
        disjoint=F(boxes[0]['lines_with_chord_above_one'][1])<F(boxes[1]['lines_with_chord_above_one'][0])
        assert disjoint==(left>F(2,5))
        out.append(dict(left=str(left),boxes=boxes,no_common_vertical_line=disjoint))
    (ROOT/'chord-audit.json').write_text(json.dumps(out,indent=2));print(json.dumps([dict(left=r['left'],no_common_vertical_line=r['no_common_vertical_line']) for r in out]))

if __name__=='__main__':main()
