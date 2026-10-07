"""Exact axis probes separating core shrinkage from endpoint support defects.

No finite probe proves coverage. A deficient enlarged closed square does,
however, certify deficiency for every smaller concentric square.
"""
import argparse
import copy
import json
from fractions import Fraction as F
from pathlib import Path
from mixed_density_check import expand


def dilate(data, target):
    out = copy.deepcopy(data); ratio = F(target)/F(data['L'])
    out['L'] = str(target)
    for r in out['rectangles']:
        r['rectangle'] = [str(F(x)*ratio) for x in r['rectangle']]
    for p in out['points']:
        p['point'] = [str(F(x)*ratio) for x in p['point']]
    expand(out)
    return out


def axis_score(model, x, y, side):
    L, _, rects, points, _, _ = model
    h = side/2; a,b,c,d = x-h,y-h,x+h,y+h
    if not (0 <= a < c <= L and 0 <= b < d <= L):
        raise ValueError('Square outside container')
    density = sum((rho*max(F(0),min(c,x1)-max(a,x0))*max(F(0),min(d,y1)-max(b,y0))
                   for x0,y0,x1,y1,rho in rects), F(0))
    closed = sum((w for (u,v),w in points if a <= u <= c and b <= v <= d), F(0))
    interior = sum((w for (u,v),w in points if a < u < c and b < v < d), F(0))
    return dict(cx=str(x), cy=str(y), side=str(side), density=str(density),
                closed_atoms=str(closed), interior_atoms=str(interior),
                closed_score=str(density+closed), interior_score=str(density+interior))


def probe(data,k=5,targets=None):
    results = []
    if type(k) is not int or k<2:raise ValueError('Invalid integer endpoint')
    for target in map(F, targets or ('4.985','4.9875','4.99','5')):
        model = expand(dilate(data,target)); pitch=(target-1)/(k-1)
        centres=[(F(1,2)+i*pitch,F(1,2)+j*pitch) for i in range(k) for j in range(k)]
        core=[axis_score(model,x,y,model[1]) for x,y in centres]
        unit=[axis_score(model,x,y,F(1)) for x,y in centres]
        results.append(dict(L=str(target),candidate_digest=model[-1],
            core_min=min(core,key=lambda q:F(q['closed_score'])),
            closed_unit_min=min(unit,key=lambda q:F(q['closed_score'])),
            core_deficits=sum(F(q['closed_score'])<1 for q in core),
            closed_unit_deficits=sum(F(q['closed_score'])<1 for q in unit),
            core=core,unit=unit))
    model=expand(dilate(data,F(k)));delta=F(1,10**6);side=1+delta;pitch=(k-side)/(k-1)
    enlarged=[axis_score(model,side/2+i*pitch,side/2+j*pitch,side) for i in range(k) for j in range(k)]
    witness=min(enlarged,key=lambda q:F(q['closed_score']))
    family=None
    if F(witness['closed_score'])<1:
        family=dict(delta_interval=['0',str(delta)],left_open=True,right_closed=True,
                    fixed_centre=[witness['cx'],witness['cy']],score_upper=witness['closed_score'],
                    reason='Every concentric square of side 1+delta is contained in the checked closed square. The measure is nonnegative.')
    return dict(status='FINITE_ENDPOINT_PROBE_NOT_CERTIFIED',parent_digest=expand(data)[-1],
                support_transform='Uniform dilation, weights unchanged; no reoptimization',
                targets=results,enlarged_min=witness,deficient_delta_family=family,
                limitations='Axis probes only. Unit closed atom scores do not have a disjoint-packing budget without a boundary argument. A failed fixed measure does not exclude other supports or joint constraints.')


def core_width_probe(data):
    records=[]
    for L in (F('4.9875'),F('4.99')):
        model=expand(dilate(data,L));pitch=(L-1)/4
        centres=[(F(1,2)+i*pitch,F(1,2)+j*pitch) for i in range(5) for j in range(5)]
        def okay(B):return all(F(axis_score(model,x,y,B)['closed_score'])>=1 for x,y in centres)
        lo=model[1];hi=F(1)
        if not okay(hi):
            records.append(dict(L=str(L),status='UNIT_AXIS_DEFICIT'));continue
        for _ in range(20):
            mid=(lo+hi)/2
            if okay(mid):hi=mid
            else:lo=mid
        B=F((hi*10**6).__ceil__(),10**6)
        if B>=1:
            records.append(dict(L=str(L),status='NO_STRICT_CORE_AT_MICRO_RESOLUTION'));continue
        D=(1/B-1)*F(99,100);last=1
        while (1+last*D)**2<2:last+=1
        scores=[F(axis_score(model,x,y,B)['closed_score']) for x,y in centres]
        assert min(scores)>=1 and B*(1+D)<1
        records.append(dict(L=str(L),trial_B=str(B),trial_step=str(D),trial_angle_count=last+1,
                            all_25_min=str(min(scores)),strict_containment_bound=str(B*(1+D)),
                            axis_threshold_bracket=list(map(str,(lo,hi))),scope='Finite axis probes, not global coverage'))
    return records


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--candidate',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--core-width',action='store_true');a=p.parse_args()
    data=json.loads(a.candidate.read_text());result=core_width_probe(data) if a.core_width else probe(data);a.out.parent.mkdir(parents=True,exist_ok=True)
    with a.out.open('x') as f:json.dump(result,f,indent=2)
    if a.core_width:
        for r in result:print(r['L'],r.get('trial_B'),r.get('trial_angle_count'),r.get('status'))
    else:
        for r in result['targets']:print(r['L'],r['core_deficits'],r['closed_unit_deficits'],float(F(r['closed_unit_min']['closed_score'])))
        print('delta_family',result['deficient_delta_family'])
