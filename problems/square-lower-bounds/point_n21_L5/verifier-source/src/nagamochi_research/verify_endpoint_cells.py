"""Replay point-score deficits and certify an affine delta family exactly."""
from fractions import Fraction as F
from pathlib import Path
import json
from score import square,contains

ROOT=Path('runs/endpoint_cells_20260926')

def main():
    d=json.loads((ROOT/'results.json').read_text());source=json.loads(Path('runs/endpoint_route_20260926/results.json').read_text())
    pts=[tuple(map(F,p['point'])) for p in source['point_weights']];ws=[F(p['weight']) for p in source['point_weights']]
    witnesses=[w for w in d['records'] if 'score' in w]
    for w in witnesses:
        poly=square(w['cx'],w['cy'],w['side'],w['t'])
        assert all(0<=x<=6 and 0<=y<=6 for x,y in poly)
        assert sum(v for p,v in zip(pts,ws) if contains(poly,p))==F(w['score'])<1
    a,b=[w for w in witnesses if F(w['t'])==F(1,3)];da,db=F(a['delta']),F(b['delta'])
    slopes={key:(F(a[key])-F(b[key]))/(da-db) for key in ('cx','cy')}
    intercepts={key:F(a[key])-slopes[key]*da for key in slopes};upper=max(da,db)
    t=F(1,3);c=F(4,5);s=F(3,5)
    def margins(p,delta):
        x=intercepts['cx']+slopes['cx']*delta;y=intercepts['cy']+slopes['cy']*delta
        u=c*(p[0]-x)+s*(p[1]-y);v=-s*(p[0]-x)+c*(p[1]-y);h=(1+delta)/2
        return [h-u,h+u,h-v,h+v]
    captured=[];excluded=[]
    for i,p in enumerate(pts):
        m0,m1=margins(p,F(0)),margins(p,upper)
        if all(v>=0 for v in m0+m1):captured.append(i)
        else:
            sides=[j for j in range(4) if m0[j]<=0 and m1[j]<0]
            assert sides,'No uniform affine exclusion';excluded.append(dict(point=i,facet=sides[0],margin_at_zero=str(m0[sides[0]]),margin_at_upper=str(m1[sides[0]])))
    for delta in (F(0),upper):
        poly=square(intercepts['cx']+slopes['cx']*delta,intercepts['cy']+slopes['cy']*delta,1+delta,t)
        assert all(0<=x<=6 and 0<=y<=6 for x,y in poly)
    value=sum(ws[i] for i in captured);assert value==F(3,4)
    out=dict(status='VERIFIED_DEFICIT_FOR_ALL_POSITIVE_DELTA_UP_TO_BOUND',witnesses=len(witnesses),upper=str(upper),t=str(t),centres={k:dict(intercept=str(intercepts[k]),slope=str(slopes[k])) for k in slopes},score=str(value),captured=captured,excluded=excluded,scope='Counterexample to this fixed point score for every 0<delta<=upper; no packing counterexample.')
    (ROOT/'family-check.json').write_text(json.dumps(out,indent=2));print(json.dumps({k:v for k,v in out.items() if k not in ('captured','excluded')}))

if __name__=='__main__':main()
