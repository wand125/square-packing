"""Whole-centre fixed-angle audit of n45 reflection endpoints."""
from fractions import Fraction as F
from time import perf_counter
import json
from n45_small_motion import ROOT,snapshot
from endpoint_cells import scan


def main():
    start=perf_counter();out=[]
    for endpoint in (F(1),F(19,20)):
        for colour in (0,1):
            for focus in range(7):
                if (colour+focus)%2==0:continue
                pts=snapshot(colour,focus,'leftmost-right',F(1),reflection=endpoint);record=dict(colour=colour,focus=focus,endpoint=str(endpoint),tests=[])
                for t in (F(1,3),F(-1,3),F(2,5),F(-2,5)):
                    result=scan(pts,[F(1)]*len(pts),t,F(1,10**8),k=7);record['tests'].append(result)
                    if 'score' in result:break
                out.append(record);print(json.dumps(dict(colour=colour,focus=focus,endpoint=str(endpoint),empty=any('score' in r for r in record['tests']))),flush=True)
    (ROOT/'centre-audit.json').write_text(json.dumps(dict(records=out,seconds=perf_counter()-start),indent=2))

if __name__=='__main__':main()
