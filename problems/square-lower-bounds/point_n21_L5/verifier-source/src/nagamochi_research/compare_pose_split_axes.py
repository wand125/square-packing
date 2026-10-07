"""Exact split-direction diagnostic on specified cells, not a global proof."""
from pathlib import Path
from fractions import Fraction as F
import argparse,hashlib,json,time
from mixed_density_check import expand
from robust_pose_core import best_lower_bound
from pose_symmetry import cached_bound


def bisect(box,axis):
    i=2*axis;middle=(box[i]+box[i+1])/2
    left=list(box);right=list(box);left[i+1]=middle;right[i]=middle
    return tuple(left),tuple(right)


def run(candidate,cover_path,sample_path,out,limit=32):
    model=expand(json.loads(candidate.read_text()));cover=json.loads(cover_path.read_text())
    assert cover['digest']==model[-1]
    sample=json.loads(sample_path.read_text())['samples'][:limit]
    lower,cache=cached_bound(model,best_lower_bound,'D4');start=time.monotonic();rows=[]
    for sample_row in sample:
        path=sample_row['path'];r=cover['leaves'][path];box=tuple(map(F,r['box']))
        old=lower(*box);assert old==F(r['lower'])
        alternatives=[]
        for axis in range(3):
            children=bisect(box,axis);bounds=[lower(*b) for b in children]
            alternatives.append(dict(axis=axis,boxes=[list(map(str,b)) for b in children],
                                     lower=list(map(str,bounds)),parent_bound=str(max(old,min(bounds)))))
        rows.append(dict(path=path,old=str(old),alternatives=alternatives))
    threshold=F(cover['threshold'])
    summary=[]
    for axis in range(3):
        values=[F(r['alternatives'][axis]['parent_bound']) for r in rows]
        summary.append(dict(axis=axis,improved=sum(v>F(r['old']) for v,r in zip(values,rows)),
                            high=sum(v>=threshold for v in values),
                            mean_gain=str(sum((v-F(r['old']) for v,r in zip(values,rows)),F(0))/len(rows))))
    q=dict(candidate_sha256=hashlib.sha256(candidate.read_bytes()).hexdigest(),
           cover_sha256=hashlib.sha256(cover_path.read_bytes()).hexdigest(),rows=rows,summary=summary,
           best_axis_high=sum(max(F(a['parent_bound']) for a in r['alternatives'])>=threshold for r in rows),
           seconds=time.monotonic()-start,unique_evaluations=len(cache),general_packing_exclusion=False)
    out.write_text(json.dumps(q,indent=2));print({k:v for k,v in q.items() if k not in ('rows','candidate_sha256','cover_sha256')},flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser()
    for name in ('candidate','cover','sample','out'):p.add_argument(name,type=Path)
    p.add_argument('--limit',type=int,default=32);a=p.parse_args()
    run(a.candidate,a.cover,a.sample,a.out,a.limit)
