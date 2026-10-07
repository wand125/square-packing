"""Pool strict validation deficits from both models without dropping provenance."""
import argparse,json,math
from fractions import Fraction as F
from pathlib import Path
from mixed_density_check import expand,evaluate
from mixed_net_audit import symmetry


def collect(root,threshold=F(10001,10000)):
    if not F(1)<=threshold<=F(10001,10000):raise ValueError('Invalid repair threshold')
    models={name:expand(json.loads((root/file).read_text())) for name,file in [('fixed_mixed','fixed-candidate.json'),('added_density','mixed-candidate.json')]}
    unique={};counts={}
    for name,model in models.items():
        symmetry(model);folder=root/'validation'/name;records=[]
        for path in sorted(folder.glob('net*/result.json')):
            d=json.loads(path.read_text());records.extend((path.parent.name,w) for w in d['exact_witnesses'])
        records.extend(('fresh',w) for w in json.loads((folder/'fresh.json').read_text())['witnesses'])
        records=[(kind,w) for kind,w in records if F(w['score'])<threshold]
        counts[name]=dict(below_gamma=len(records),below_one=sum(F(w['score'])<1 for _,w in records))
        for kind,w in records:
            x,y,t=map(F,(w['cx'],w['cy'],w['t']));exact=evaluate(model,x,y,t)
            assert all(exact[k]==w[k] for k in exact) and F(exact['score'])<threshold
            if t*t+2*t-1>0:x,y,t=y,x,(1-t)/(1+t)
            key=tuple(map(str,(x,y,t)))
            if key not in unique:
                L,B=model[:2];reach=(L-B*(1+2*t-t*t)/(1+t*t))/2
                unique[key]=dict(cx=str(x),cy=str(y),t=str(t),sources=[],normalized_pose=[float((x-L/2)/reach),float((y-L/2)/reach),2*math.atan(float(t))/(math.pi/4)],evaluations={label:evaluate(m,x,y,t) for label,m in models.items()})
            unique[key]['sources'].append(dict(candidate=name,kind=kind,candidate_digest=model[-1]))
    rows=list(unique.values());summary={}
    for name in models:
        values=[F(w['evaluations'][name]['score']) for w in rows]
        summary[name]=dict(below_one=sum(v<1 for v in values),minimum=float(min(values)),total_deficit=float(sum(max(F(0),1-v) for v in values)))
    result=dict(status='EXACT_REPAIR_POOL_NOT_REFITTED',repair_threshold=str(threshold),source_counts=counts,count=len(rows),summary=summary,witnesses=rows)
    path=root/'next-pool.json';assert not path.exists();path.write_text(json.dumps(result,indent=2));print(json.dumps({k:v for k,v in result.items() if k!='witnesses'}),flush=True)
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('root',type=Path);ap.add_argument('--threshold',type=F,default=F(10001,10000));a=ap.parse_args();collect(a.root,a.threshold)
