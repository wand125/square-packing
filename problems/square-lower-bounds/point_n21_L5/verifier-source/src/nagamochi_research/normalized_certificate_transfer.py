"""Reuse pure envelope certificates in normalized centre coordinates.

Correlated-epsilon certificates are deliberately NOT accepted: their region
labels refer to unscaled centres. Pure envelope certificates exclude abstract
core packings and therefore can also be used after a verified normalization.
"""
from fractions import Fraction as F
from pathlib import Path
import json,hashlib
from epsilon_cell_envelope import verify_completion,geometry as envelope_geometry
from normalized_axis_cells import geometry as normalized_geometry
from saturated_axis_cells import contained
from fixed_orientation_cover import angle_envelope


def check_embedding(base):
    q=base['config'];k=q['k'];m=k-1;em=F(q['eps_max']);A=F(q['axis_inner']);R=F(q['rot_inner'])
    assert 0<em<m and 0<A<=1
    cells,_=normalized_geometry(q,base['missing']);old,_=envelope_geometry(q,base['missing'])
    assert set(cells)==set(old) and all(contained(p,old[i]) for i,p in cells.items())
    E,span=angle_envelope(F(q['t']),F(q['rot_h']))
    assert R*E<1 and span>=1 and F(q['rot_half'])>=(k-span)/2
    # h=e/(2m), sigma=1-e/m. sigma*(1+2h)=1-e^2/m^2<1.
    assert F(1,m*m)>0
    return cells


def transfer(base,completion):
    assert all('model' not in c or c['model']=='ENVELOPE' for c in completion['cases'])
    result=verify_completion(base,completion);assert result['target_excluded']
    cells=check_embedding(base);q=base['config'];k=q['k'];m=k-1;em=F(q['eps_max'])
    # Normalized adjacent near-axis centres separate by >1 >= A.
    return dict(status='EXACT_NORMALIZED_WIDE_ANGLE_TRANSFER',k=k,
                epsilon_upper=str(em),near_axis_t_halfwidth=f'epsilon/{2*m}',
                rotated_t=q['t'],rotated_t_halfwidth=q['rot_h'],
                axis_boxes=len(cells),rotated_boxes=completion['target'],missing=base['missing'],
                strict_containment_gap_polynomial=dict(epsilon_squared=str(F(1,m*m))),
                source_replay=result,
                limitation='Only the specified two groups. Missing-cell scope is preserved. This is not an unrestricted integer endpoint proof.')


def run(source,completion_path,out):
    raw=source.read_bytes();base=json.loads(raw);completion=json.loads(completion_path.read_text())
    assert completion['source']==source.name and completion['source_sha256']==hashlib.sha256(raw).hexdigest()
    q=transfer(base,completion)
    q['inputs']=[dict(path=str(p),sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in (source,completion_path)]
    out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(q,indent=2));print(out.name,q['near_axis_t_halfwidth'],q['axis_boxes'],q['rotated_boxes'],flush=True)
    return q


if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('root',type=Path);p.add_argument('out',type=Path);a=p.parse_args()
    for label,target in (('None',3),('0',4)):
        run(a.root/f'k4-m{label}.json',a.root/f'k4-m{label}-full{target}.json',a.out/f'n12-m{label}-wide.json')
