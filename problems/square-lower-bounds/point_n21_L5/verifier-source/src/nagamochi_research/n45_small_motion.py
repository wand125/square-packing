"""n45 reduced-shift motion scout; exact witnesses, no all-time proof."""
from fractions import Fraction as F
from pathlib import Path
from time import perf_counter
from collections import Counter
import json
from motion_pilot import rows,probe
from pilot import samples
from support_pilot import holdout

ROOT=Path('runs/n45_small_motion_20260926')

def heights(focus):
    special={i for i in (focus-1,focus) if 0<=i<6};g=F(847,1000) if len(special)==1 else F(427,500)
    other=(7-2*F(457,500)-len(special)*g)/(6-len(special));gaps=[g if i in special else other for i in range(6)]
    assert max(gaps)**2<=F(3,4)
    shift=F(3,100) if len(special)==1 else F(1,50)
    assert (F(1,2)+shift)**2+g*g<=1
    ys=[F(457,500)]
    for gap in gaps:ys.append(ys[-1]+gap)
    assert ys[-1]==7-F(457,500)
    return ys,shift

def snapshot(colour,focus,phase,time,reflection=F(1)):
    target,shift=heights(focus);d=F(457,500);base=[d+i*(7-2*d)/6 for i in range(7)]
    ys=[x+(y-x)*time for x,y in zip(base,target)] if phase=='vertical' else target
    ps=[]
    for x,y in rows(7,ys,colour):
        if y==ys[focus]:
            if phase=='row-left':x-=shift*time
            if phase=='leftmost-right' and x==F(1,2):x+=(reflection-F(1,2))*time
        ps.append((x,y))
    return ps

def main():
    start=perf_counter();ROOT.mkdir(exist_ok=False);poses=[p for p,_ in samples(7)]+holdout(7,945331)+holdout(7,945332);records=[]
    for colour in (0,1):
        for focus in range(7):
            if (colour+focus)%2==0:continue
            r=dict(colour=colour,focus=focus,checks=[],status='FINITE_PASS_NOT_PROOF')
            for phase in ('vertical','row-left','leftmost-right'):
                for time in (F(0),F(1,4),F(1,2),F(3,4),F(1)):
                    pts=snapshot(colour,focus,phase,time);test=probe(pts,poses)
                    w=dict(phase=phase,time=str(time),status=test['status'])
                    if 'pose' in test:w['pose']=test['pose']
                    r['checks'].append(w)
                    if test['status']=='EXACT_EMPTY_OPEN_SQUARE':r['status']='REJECTED';break
                if r['status']=='REJECTED':break
            records.append(r);print(json.dumps(r,default=str),flush=True)
    (ROOT/'results.json').write_text(json.dumps(dict(records=records,poses_per_state=len(poses),seconds=perf_counter()-start,counts=dict(Counter(r['status'] for r in records))),default=str,indent=2))

if __name__=='__main__':main()
