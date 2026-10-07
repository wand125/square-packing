"""Use a narrower proof only as a branch-order hint for the fixed-band model."""
from pathlib import Path
from collections import Counter
import argparse,hashlib,json,time
from variable_rotor_angles import model
from normalized_axis_cells import model as nominal_model
from saturated_joint_search import search_model,replay_model
from bounded_farkas import certificate


def reorder(data,order):
    A,b,pairs,polys,angles=data
    assert sorted(order)==list(range(len(pairs))) and all(type(i) is int for i in order)
    return A,b,[pairs[i] for i in order],polys,angles


def verify(q):
    assert q['model']=='GUIDED_SHARED_ROTOR_ANGLE_V1'
    data,gap=model(q['config'],q['missing'],q['chosen'],True)
    return replay_model(reorder(data,q['pair_order']),q['tree'],positive_index=gap)


def run(source,out,limit):
    raw=source.read_bytes();q=json.loads(raw);assert q['model']=='NORMALIZED_CAPPED_BANDS_V4'
    data,gap=model(q['config'],q['missing'],q['chosen'],True)
    nominal=nominal_model(q['config'],q['missing'],q['chosen'],True,True,True,False)
    counts=Counter()
    def visit(t):
        if 'pair' in t:
            p=nominal[2][t['pair']];counts[(p['i'],p['j'])]+=1
        for c in t.get('children',[]):visit(c)
    visit(q['tree']);pairs=data[2]
    order=sorted(range(len(pairs)),key=lambda i:(-counts[(pairs[i]['i'],pairs[i]['j'])],i))
    result=search_model(reorder(data,order),limit,positive_index=gap,branch_rule='ordered',certificate_solver=certificate)
    result.update(model='GUIDED_SHARED_ROTOR_ANGLE_V1',config=q['config'],missing=q['missing'],chosen=q['chosen'],pair_order=order,
                  hint_source=str(source),hint_sha256=hashlib.sha256(raw).hexdigest(),hint_role='Branch order only; no narrow-band exclusions imported.')
    result['verified']=verify(result);out.write_text(json.dumps(result,indent=2));print({k:result[k] for k in ('status','nodes','seconds','verified')},flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('source',type=Path);p.add_argument('out',type=Path);p.add_argument('--nodes',type=int,default=200);a=p.parse_args();run(a.source,a.out,a.nodes)
