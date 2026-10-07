"""Cached full geometry; compare equivalent dominance-pruned LPs, bounded runs."""
from fractions import Fraction as F
from pathlib import Path
import argparse,json,gzip,time,hashlib
from math import ceil
import numpy as np
from scipy.optimize import linprog
from scipy.sparse import csr_matrix
from two_angle_cover import patterns
from minimal_capture_rows import minimal_indices


def matrix(ds,N):
    rr=[];cc=[];vv=[];row=0
    for j,ps in enumerate(ds):
        for p in ps:
            rr.extend([row]*(len(p)+1));cc.extend(p+[N+j]);vv.extend([-1]*len(p)+[1]);row+=1
    return csr_matrix((vv,(rr,cc)),shape=(row,N+3))


def run(parent,out):
    out.mkdir(exist_ok=True);source=json.loads(parent.read_text());sha=hashlib.sha256(parent.read_bytes()).hexdigest();cache=out/'geometry.json.gz'
    if cache.exists():
        with gzip.open(cache,'rt') as f:q=json.load(f)
        assert q['source_sha256']==sha
    else:
        pts={tuple(map(F,p)) for p in source['points']};pts=sorted(pts|{(x,-y) for x,y in pts})
        L,t,B,h=map(F,(source['L'],source['t'],source['B'],source['h']))
        print('BUILD_AXIS',len(pts),flush=True);axis=patterns(pts,L,F(0),B)['patterns']
        print('BUILD_POSITIVE',len(axis),flush=True);positive=patterns(pts,L,t,B,h)['patterns']
        idx={p:i for i,p in enumerate(pts)};reflection=[idx[(x,-y)] for x,y in pts]
        negative=sorted({tuple(sorted(reflection[i] for i in row)) for row in positive})
        q=dict(source_sha256=sha,points=[list(map(str,p)) for p in pts],domains=[axis,positive,[list(r) for r in negative]])
        with gzip.open(cache,'wt') as f:json.dump(q,f)
    ds=q['domains'];N=len(q['points']);start=time.monotonic()
    reduced=[[rows[i] for i in minimal_indices(rows)] for rows in ds]
    print('PRUNED',list(map(len,ds)),'to',list(map(len,reduced)),time.monotonic()-start,flush=True)
    records=[]
    for counts in ([0,1,31],[25,3,4]):
        for label,rows,method in [('full-ds',ds,'highs-ds'),('minimal-ds',reduced,'highs-ds'),('minimal-ipm',reduced,'highs-ipm')]:
            A=matrix(rows,N);start=time.monotonic()
            fit=linprog([0]*N+[-x for x in counts],A_ub=A,b_ub=np.zeros(A.shape[0]),A_eq=[[1]*N+[0]*3],b_eq=[1],bounds=(0,None),method=method,options={'time_limit':10})
            rec=dict(counts=counts,label=label,status=int(fit.status),success=bool(fit.success),seconds=time.monotonic()-start,iterations=int(fit.nit),message=fit.message)
            if fit.x is not None and np.all(np.isfinite(fit.x)):
                w=[max(0,ceil(float(x)*10**10)) for x in fit.x[:N]];total=sum(w)
                floors=[min(sum(w[i] for i in row) for row in domain) for domain in ds]
                rec.update(numerators=w,total=total,floors=floors,gap=sum(a*b for a,b in zip(counts,floors))-total)
                rec['exact_exclusion']=rec['gap']>0
            records.append(rec);(out/'results.json').write_text(json.dumps(dict(source_sha256=sha,full_rows=list(map(len,ds)),minimal_rows=list(map(len,reduced)),records=records,scope='Two specified compositions in three bands only. Not a global packing proof.'),indent=2))
            print({k:v for k,v in rec.items() if k not in ('numerators','message')},flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('parent',type=Path);p.add_argument('out',type=Path);a=p.parse_args();run(a.parent,a.out)
