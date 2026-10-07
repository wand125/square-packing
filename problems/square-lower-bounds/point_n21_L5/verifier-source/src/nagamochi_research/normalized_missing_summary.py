"""Combine all three rotation orbits, retaining the narrower rotor-band scope."""
from pathlib import Path
from fractions import Fraction as F
import json,hashlib
from normalized_certificate_transfer import transfer
from normalized_pair_refinement import verify_completion
from complete_missing_cells import rotation_orbit


def verify_all(envelope_root,result_root,capped=False):
    source=envelope_root/'scaled-exact/k4-m0.json';completion=envelope_root/'scaled-exact/k4-m0-full4.json'
    base=json.loads(source.read_text());part=json.loads(completion.read_text())
    assert part['source_sha256']==hashlib.sha256(source.read_bytes()).hexdigest()
    corner=transfer(base,part);assert corner['axis_boxes']==8 and corner['rotated_boxes']==4 and corner['missing']==[0]
    config=base['config'];paths=[source,completion];results=[dict(missing=[0],replay=corner)];covered=rotation_orbit(4,0)
    for m in (1,4):
        source=envelope_root/f'k4-m{m}.json';pair_path=result_root/f'n12-m{m}-pairs.json'
        completion=result_root/('n12-m1-full4.json' if m==1 else ('n12-m4-capped-full4.json' if capped else 'n12-m4-moving-full4.json'))
        base=json.loads(source.read_text());pairs=json.loads(pair_path.read_text());part=json.loads(completion.read_text())
        if m==4:assert part['rotated_t_halfwidth_rule']==('min(rot_h,epsilon/(2*(k-1)))' if capped else 'epsilon/10000')
        assert base['config']==config and base['missing']==[m] and part['target']==4
        assert pairs['source_sha256']==part['source_sha256']==hashlib.sha256(source.read_bytes()).hexdigest()
        assert part['pair_sha256']==hashlib.sha256(pair_path.read_bytes()).hexdigest()
        replay=verify_completion(base,pairs,part);assert replay['target_excluded']
        orbit=rotation_orbit(4,m);assert not covered&orbit;covered|=orbit
        paths.extend([source,pair_path,completion]);results.append(dict(missing=[m],replay=replay))
    assert covered==set(range(9)) and F(config['eps_max'])/10000<=F(config['rot_h'])
    return dict(status='EXACT_ALL_SINGLE_MISSING_CAPPED_BAND_EXCLUSION' if capped else 'EXACT_ALL_SINGLE_MISSING_MOVING_BAND_EXCLUSION',k=4,axis_boxes=8,rotated_boxes=4,
                epsilon_upper=config['eps_max'],axis_t_halfwidth='epsilon/6',rotated_t=config['t'],
                rotated_t_halfwidth=f"min({config['rot_h']},epsilon/6)" if capped else 'epsilon/10000',covered_cells=sorted(covered),cases=results,
                inputs=[dict(path=str(p),sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in paths])
