"""Boundary-local vertical bending with exact, contact-directed hole checks.

A full-row motion is the control. Local variants freeze all nonfocus points at
x >= cut; only the exception-free focus row moves horizontally in later phases.
Neither finite passage nor failure of this family decides n32 packing.
"""
from fractions import Fraction as F
from pathlib import Path
from math import sqrt
from time import perf_counter
from collections import Counter
import json
from motion_pilot import rows,focus_heights,probe,strict_contains
from score import square
from pilot import samples
from support_pilot import holdout


def weights(x,cut):
    return F(1) if cut is None else max(F(0),min(F(1),(cut-x)/(cut-1)))


def snapshot(colour,focus,cut,time,phase):
    base=rows(6,colour=colour);target=focus_heights(6,focus);out=[]
    for x,y in base:
        r=int((y-F(457,500))/F(1043,1250));w=weights(x,cut)
        yy=y+w*(target[r]-y)*(time if phase=='vertical' else 1)
        xx=x
        if r==focus and (r+colour)%2==1:
            if phase=='row-left':xx-=time/10
            elif phase=='leftmost-right' and x==F(1,2):xx+=time/2
        out.append((xx,yy))
    return out


def directed_hole(base,points):
    # A row edge just longer than 1 can hide a narrow rotated empty square.
    # Finite random angles can miss this; align the square to that edge.
    for i in range(len(base)-1):
        if base[i][1]!=base[i+1][1]:continue
        a,b=points[i],points[i+1];dx,dy=b[0]-a[0],b[1]-a[1]
        length_sq=dx*dx+dy*dy
        if length_sq<=1:continue
        t=F(float(dy)/(sqrt(float(length_sq))+float(dx))).limit_denominator(10**10)
        for delta in (F(1,10**8),F(1,10**10),F(1,10**12)):
            cx,cy=(a[0]+b[0])/2,(a[1]+b[1])/2
            poly=square(cx,cy,1+delta,t)
            if not all(0<=x<=6 and 0<=y<=6 for x,y in poly):continue
            if any(strict_contains(poly,p) for p in points):continue
            return dict(status='EXACT_EMPTY_OPEN_SQUARE',pose=dict(cx=cx,cy=cy,delta=delta,t=t),
                        edge=[i,i+1],edge_length_sq=length_sq)
    return None


def analyse(colour,focus,cut,poses):
    base=rows(6,colour=colour);checks=[]
    # Exception on a different row, at its rightmost point, remains fixed.
    frozen_row=(focus+2)%6
    ids=[i for i,p in enumerate(base) if int((p[1]-F(457,500))/F(1043,1250))==frozen_row]
    frozen=max(ids,key=lambda i:base[i][0])
    for phase in ('vertical','row-left','leftmost-right'):
        if phase!='vertical' and (focus+colour)%2==0:continue
        for time in (F(1,2),F(1)):
            pts=snapshot(colour,focus,cut,time,phase)
            if cut is not None:assert pts[frozen]==base[frozen]
            hit=directed_hole(base,pts)
            if hit is None:hit=probe(pts,poses)
            if hit['status']=='EXACT_EMPTY_OPEN_SQUARE':
                # Keep just the rational pose; regenerate points in the checker.
                checks.append(dict(phase=phase,time=time,status=hit['status'],pose=hit['pose'],edge=hit.get('edge')))
                return dict(colour=colour,focus=focus,cut=cut,frozen_index=frozen,checks=checks,status='REJECTED_LOCAL_PATH')
            checks.append(dict(phase=phase,time=time,status='FINITE_PASS',samples=hit['samples']))
    return dict(colour=colour,focus=focus,cut=cut,frozen_index=frozen,checks=checks,status='FINITE_PASS_NOT_PROOF')


def main():
    start=perf_counter();out=Path('runs/bentz_local_motion_20260926');out.mkdir(parents=True,exist_ok=False)
    poses=[p for p,_ in samples(6)]+holdout(6,626190)
    result={'records':[analyse(c,i,cut,poses) for cut in (None,F(2),F(3),F(4)) for c in (0,1) for i in range(6)],
            'scope':'Local-family counterexamples and finite control checks only; no n32 impossibility claim.'}
    result['seconds']=perf_counter()-start
    result['counts']=dict(Counter(('control-' if e['cut'] is None else 'local-')+e['status'] for e in result['records']))
    (out/'results.json').write_text(json.dumps(result,default=str,indent=2))
    print(json.dumps({k:v for k,v in result.items() if k!='records'}))


if __name__=='__main__':main()
