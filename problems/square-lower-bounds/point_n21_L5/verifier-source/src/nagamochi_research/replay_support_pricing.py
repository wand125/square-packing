"""Replay all new-column loads against an already checked rational dual."""
import argparse,json,hashlib
from pathlib import Path
from fractions import Fraction as F
from fixed_support_dual_audit import exact_columns


def replay(base,dual_file,pricing_file):
    base_data=json.loads(base.read_text());dual=json.loads(dual_file.read_text());pricing=json.loads(pricing_file.read_text());B=F(999999,1000000)
    record=next(r for r in dual['records'] if F(r['B'])==B);scale=F(record['scale'])
    ws=[F(x)/scale for x in dual['unscaled_weights']];ps=[tuple(map(F,p)) for p in dual['poses']]
    if len(ws)!=len(ps) or min(ws)<0:raise ValueError('Invalid dual')
    rows=[]
    for column in pricing['columns']:
        kind=column['kind'];tiny=dict(L=base_data['L'],rectangles=[],points=[])
        g=tuple(map(F,column['geometry']));L=F(base_data['L'])
        if kind=='point' and (len(g)!=2 or not all(0<=x<=L for x in g)):raise ValueError('Invalid point')
        if kind=='rectangle' and (len(g)!=4 or not(0<=g[0]<g[2]<=L and 0<=g[1]<g[3]<=L)):raise ValueError('Invalid rectangle')
        if kind=='point':tiny['points']=[dict(point=column['geometry'])]
        elif kind=='rectangle':tiny['rectangles']=[dict(rectangle=column['geometry'])]
        else:raise ValueError('Unsupported basis')
        load=sum(w*exact_columns(tiny,p,B)[0] for p,w in zip(ps,ws))
        if load!=F(column['dual_load']) or (load>1)!=column['improves_dual']:raise ValueError('Wrong column load')
        rows.append(dict(kind=kind,geometry=column['geometry'],load=str(load),improves=load>1))
    return dict(status='EXACT_PRICING_LOADS_REPLAYED',source_dual_sha256=hashlib.sha256(dual_file.read_bytes()).hexdigest(),
                pricing_sha256=hashlib.sha256(pricing_file.read_bytes()).hexdigest(),columns=rows,
                improving=sum(r['improves'] for r in rows),requires_verified_source_dual=True,general_packing_exclusion=False)

if __name__=='__main__':
    p=argparse.ArgumentParser()
    for name in ('base','dual','pricing','out'):p.add_argument(name,type=Path)
    a=p.parse_args();result=replay(a.base,a.dual,a.pricing);a.out.write_text(json.dumps(result,indent=2));print(dict(status=result['status'],columns=len(result['columns']),improving=result['improving']))
