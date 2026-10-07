"""Replay rational empty-square witnesses and continuous edge conditions."""
from pathlib import Path
from fractions import Fraction as F
import json
from local_motion import snapshot as local
from elastic_motion import snapshot as elastic
from elastic_audit import triangle_edges
from motion_pilot import rows,strict_contains
from score import square


def empty(ps,pose):
    p={k:F(v) for k,v in pose.items()};assert 0<p['delta']<=F(1,100)
    poly=square(p['cx'],p['cy'],1+p['delta'],p['t'])
    assert all(0<=x<=6 and 0<=y<=6 for x,y in poly)
    assert not any(strict_contains(poly,pt) for pt in ps)


def verify():
    root=Path('runs/bentz_local_motion_20260926');holes=certs=0
    for name in ('results.json','elastic-results.json','elastic-audit.json','elastic-sweep.json'):
        data=json.loads((root/name).read_text())
        for r in data['records']:
            c,i=r['colour'],r['focus'];base=rows(6,colour=c)
            entries=r.get('checks',r.get('snapshots',[]))
            for entry in entries:
                t=F(entry['time']);phase=entry['phase']
                if name=='results.json':ps=local(c,i,None if r['cut'] is None else F(r['cut']),t,phase)
                else:ps=elastic(c,i,F(r['compression']),t,phase,r.get('frozen_row'))
                if 'frozen_index' in r and not (name=='results.json' and r['cut'] is None):assert ps[r['frozen_index']]==base[r['frozen_index']]
                pose=entry.get('empty_pose',entry.get('pose'))
                if pose is not None:empty(ps,pose);holes+=1
            if name=='elastic-sweep.json':
                for certificate in r['edge_certificates']:
                    maxima=[]
                    for t in (F(0),F(1)):
                        ps=elastic(c,i,F(r['compression']),t,certificate['phase'],r['frozen_row'])
                        maxima.append(max(sum((ps[a][j]-ps[b][j])**2 for j in (0,1)) for a,b in triangle_edges(c)))
                    assert maxima==list(map(F,certificate['endpoint_max_sq']))
                    assert certificate['all_time_unit_edges']==all(v<=1 for v in maxima)
                    if certificate['all_time_unit_edges']:certs+=1
    return dict(exact_empty_witness_records=holes,affine_phase_unit_edge_certificates=certs,
                scope='Repeated witnesses count separately. Edge certificates omit wall cells and full unavoidability.')


if __name__=='__main__':print(json.dumps(verify()))
