"""Pool saved net deficits, keep source provenance, and cross-score both models."""
from fractions import Fraction as F
from pathlib import Path
import json,math
from mixed_density_check import expand,evaluate


def main():
    root=Path('runs/expanded_n12_n21_20260926/n21/exact-refit-5/targeted-pricing-polished')
    out=Path('runs/mixed_rotated_full_20260926')
    models={name:expand(json.loads((root/file).read_text())) for name,file in [('fixed_mixed','fixed-candidate.json'),('added_density','mixed-candidate.json')]}
    records=[]
    for item in json.loads((out/'known-deficits.json').read_text()):
        records.append(dict(source=item['candidate'],kind='previous_net',witness=item['exact']))
    for name,directory in [('fixed_mixed','fixed-net1-gamma1'),('added_density','added-net1-gamma1')]:
        result=json.loads((out/directory/'result.json').read_text())
        for w in result['exact_witnesses']:records.append(dict(source=name,kind='new_near_axis',witness=w))
    unique={}
    for item in records:
        w=item['witness'];x,y,t=map(F,(w['cx'],w['cy'],w['t']));model=models[item['source']]
        assert evaluate(model,x,y,t)==w and F(w['score'])<1
        # Numeric geometry expects theta <= pi/4. Preserve exact geometry by D4.
        if t*t+2*t-1>0:x,y,t=y,x,(1-t)/(1+t)
        key=tuple(map(str,(x,y,t)))
        if key not in unique:
            L,B=model[:2];reach=(L-B*(1+2*t-t*t)/(1+t*t))/2
            unique[key]=dict(cx=str(x),cy=str(y),t=str(t),sources=[],
                normalized_pose=[float((x-L/2)/reach),float((y-L/2)/reach),2*math.atan(float(t))/(math.pi/4)],
                evaluations={name:evaluate(m,x,y,t) for name,m in models.items()})
        unique[key]['sources'].append(dict(candidate=item['source'],kind=item['kind'],candidate_digest=w['candidate_digest']))
    rows=list(unique.values());summary={}
    for name,m in models.items():
        vals=[F(w['evaluations'][name]['score']) for w in rows]
        summary[name]=dict(minimum=float(min(vals)),below_one=sum(v<1 for v in vals),total_deficit=float(sum(max(F(0),1-v) for v in vals)))
    data=dict(status='REPAIR_QUEUE_NOT_REFITTED',count=len(rows),source_counts={name:sum(w['source']==name for w in records) for name in models},summary=summary,witnesses=rows)
    (out/'shared-repair-pool.json').write_text(json.dumps(data,indent=2)+'\n');print(json.dumps(dict(count=len(rows),summary=summary),indent=2))
if __name__=='__main__':main()
