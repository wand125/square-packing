"""Seek additional exact witnesses for uncovered counts in three saved bands.

Uses a previously independently replayed geometry cache. Failure to obtain a
positive exact gap is unresolved, never a feasible physical packing claim.
"""
from pathlib import Path
from math import ceil
from fractions import Fraction as F
import argparse, gzip, hashlib, json, time
import numpy as np
from scipy.optimize import linprog
from minimal_capture_rows import minimal_indices
from signed_lp_pilot import matrix


def run(folder, out, attempts=12):
    with gzip.open(folder/'geometry.json.gz', 'rt') as f:
        g = json.load(f)
    report = json.loads((folder/'results.json').read_text())
    replay = json.loads((folder/'replay.json').read_text())
    assert replay['status'] == 'FULL_GEOMETRY_AND_INTEGER_WITNESSES_REPLAYED'
    assert report['source_sha256'] == g['source_sha256']
    # This experiment is specifically the n32, L=299/50 three-band family.
    assert replay['L'] == '299/50'
    assert F(replay['axis_halfwidth']) <= (6-F(replay['L']))/10
    ds = g['domains']; N = len(g['points'])
    reduced = [[rows[i] for i in minimal_indices(rows)] for rows in ds]
    A = matrix(reduced, N)
    certs = []
    def add(w):
        assert len(w) == N and all(type(x) is int and x >= 0 for x in w)
        floors = [min(sum(w[i] for i in r) for r in rows) for rows in ds]
        total = sum(w)
        certs.extend([(total, floors), (total, [floors[0], floors[2], floors[1]])])
        return total, floors
    for r in report['records']:
        if 'numerators' in r: add(r['numerators'])
    counts = [(a,b,32-a-b) for a in range(26) for b in range(33-a)]
    tried = set(); records = []; start = time.monotonic()
    def gap(c):
        return max(sum(x*y for x,y in zip(c,fs))/m-1 for m,fs in certs)
    def excluded(c):
        return any(sum(x*y for x,y in zip(c,fs)) > m for m,fs in certs)
    for _ in range(attempts):
        remaining = [c for c in counts if not excluded(c)]
        choices = [c for c in remaining if c not in tried]
        if not choices: break
        # Diagnose worst currently covered composition; mirror is equivalent.
        c = min(choices, key=gap); tried.add(c); tried.add((c[0],c[2],c[1]))
        fit = linprog([0]*N+[-x for x in c], A_ub=A, b_ub=np.zeros(A.shape[0]),
                      A_eq=[[1]*N+[0]*3], b_eq=[1], bounds=(0,None),
                      method='highs-ipm', options={'time_limit':10})
        r = dict(counts=c, status=int(fit.status))
        if fit.x is not None and np.all(np.isfinite(fit.x)):
            w = [max(0,ceil(float(x)*10**10)) for x in fit.x[:N]]
            m,fs = add(w); exact_gap = sum(x*y for x,y in zip(c,fs))-m
            r.update(numerators=w,total=m,floors=fs,gap=exact_gap,exact_exclusion=exact_gap>0)
        records.append(r)
        remaining = [c for c in counts if not excluded(c)]
        q = dict(source_sha256=g['source_sha256'],
                 geometry_sha256=hashlib.sha256((folder/'geometry.json.gz').read_bytes()).hexdigest(),
                 records=records,remaining=remaining,covered=len(counts)-len(remaining),
                 seconds=time.monotonic()-start,general_packing_exclusion=False)
        tmp=out.with_suffix('.tmp');tmp.write_text(json.dumps(q));tmp.replace(out)
        print({k:v for k,v in r.items() if k!='numerators'},'remaining',len(remaining),flush=True)


def verify(folder, out):
    q=json.loads(out.read_text())
    assert q['geometry_sha256']==hashlib.sha256((folder/'geometry.json.gz').read_bytes()).hexdigest()
    with gzip.open(folder/'geometry.json.gz','rt') as f:g=json.load(f)
    assert q['source_sha256']==g['source_sha256']
    original=json.loads((folder/'results.json').read_text())
    ds=g['domains'];pts=[tuple(map(F,p)) for p in g['points']];index={p:i for i,p in enumerate(pts)}
    permutation=[index[(x,-y)] for x,y in pts];certs=[]
    for r in original['records']+q['records']:
        if 'numerators' not in r:continue
        w=r['numerators'];assert len(w)==len(pts) and all(type(v) is int and v>=0 for v in w)
        floors=[min(sum(w[i] for i in row) for row in rows) for rows in ds]
        assert sum(w)==r['total'] and floors==r['floors']
        gap=sum(a*b for a,b in zip(r['counts'],floors))-sum(w)
        assert gap==r['gap'] and r['exact_exclusion']==(gap>0)
        reflected=[w[i] for i in permutation]
        reflected_floors=[min(sum(reflected[i] for i in row) for row in rows) for rows in ds]
        assert reflected_floors==[floors[0],floors[2],floors[1]]
        certs.extend([(sum(w),floors),(sum(w),reflected_floors)])
    counts=[(a,b,32-a-b) for a in range(26) for b in range(33-a)]
    remaining=[list(c) for c in counts if not any(sum(a*b for a,b in zip(c,fs))>m for m,fs in certs)]
    assert remaining==q['remaining'] and len(counts)-len(remaining)==q['covered']
    result=dict(status='ALL_INTEGER_WEIGHTS_AND_REFLECTIONS_REPLAYED',covered=q['covered'],remaining=len(remaining),general_packing_exclusion=False)
    out.with_suffix('.replay.json').write_text(json.dumps(result,indent=2));print(result)


if __name__ == '__main__':
    p=argparse.ArgumentParser();p.add_argument('folder',type=Path);p.add_argument('out',type=Path)
    p.add_argument('--attempts',type=int,default=12);p.add_argument('--replay',action='store_true');a=p.parse_args()
    if a.replay:verify(a.folder,a.out)
    else:run(a.folder,a.out,a.attempts)
