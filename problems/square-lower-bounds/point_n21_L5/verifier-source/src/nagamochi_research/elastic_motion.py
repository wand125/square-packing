"""Freeze one exceptional point on a long row; bend/contract that row only.
All other rows follow the previously tested full-row motion. Finite scout only.
"""
from fractions import Fraction as F
from pathlib import Path
from collections import Counter
from time import perf_counter
import json
from motion_pilot import rows,focus_heights,probe
from local_motion import directed_hole
from pilot import samples
from support_pilot import holdout


def frozen_row_for(colour,focus):
    ys=focus_heights(6,focus)
    choices=[r for r in range(6) if (r+colour)%2==1 and r!=focus]
    return max(choices,key=lambda r:abs(ys[r]-(F(457,500)+F(1043,1250)*r)))


def snapshot(colour,focus,compression,time,phase,frozen_row=None):
    base=rows(6,colour=colour);target=focus_heights(6,focus)
    if frozen_row is None:frozen_row=frozen_row_for(colour,focus)
    fixed_x=F(11,2);out=[]
    for x,y in base:
        r=int((y-F(457,500))/F(1043,1250));u=time if phase=='vertical' else F(1)
        if r==frozen_row:
            w=min(F(1),(fixed_x-x)/(fixed_x-1))
            xx=x+u*compression*(fixed_x-x);yy=y+u*w*(target[r]-y)
        else:xx=x;yy=y+u*(target[r]-y)
        if r==focus and (r+colour)%2==1:
            if phase=='row-left':xx-=time/10
            elif phase=='leftmost-right' and x==F(1,2):xx+=time/2
        out.append((xx,yy))
    return out


def analyse(colour,focus,compression,poses):
    base=rows(6,colour=colour);fr=frozen_row_for(colour,focus)
    fi=base.index((F(11,2),F(457,500)+F(1043,1250)*fr));checks=[]
    for phase in ('vertical','row-left','leftmost-right'):
        if phase!='vertical' and (focus+colour)%2==0:continue
        for time in (F(1,2),F(1)):
            ps=snapshot(colour,focus,compression,time,phase)
            assert ps[fi]==base[fi]
            hit=directed_hole(base,ps) or probe(ps,poses)
            entry=dict(phase=phase,time=time,status=hit['status'])
            if hit['status']=='EXACT_EMPTY_OPEN_SQUARE':
                entry.update(pose=hit['pose'],edge=hit.get('edge'));checks.append(entry)
                return dict(colour=colour,focus=focus,compression=compression,frozen_row=fr,frozen_index=fi,checks=checks,status='REJECTED_PATH')
            entry['samples']=hit['samples'];checks.append(entry)
    return dict(colour=colour,focus=focus,compression=compression,frozen_row=fr,frozen_index=fi,checks=checks,status='FINITE_PASS_NOT_PROOF')


def main():
    start=perf_counter();out=Path('runs/bentz_local_motion_20260926')
    poses=[p for p,_ in samples(6)]+holdout(6,982163)
    data={'records':[analyse(c,i,comp,poses) for comp in (F(0),F(1,10000),F(1,1000),F(1,200),F(1,100)) for c in (0,1) for i in range(6)]}
    data['seconds']=perf_counter()-start
    data['counts']=dict(Counter(str(r['compression'])+':'+r['status'] for r in data['records']))
    (out/'elastic-results.json').write_text(json.dumps(data,default=str,indent=2))
    print(json.dumps({k:v for k,v in data.items() if k!='records'}))


if __name__=='__main__':main()
