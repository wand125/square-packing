"""Audit saved priced-exchange witnesses against one unchanged candidate."""
import argparse,json,hashlib
from pathlib import Path
from fractions import Fraction as F
from repair_lemma_measure import np,expand,expand_primitives,coefficients,poses,evaluate
from resume_priced_exchange import informative_local


def run(root,latest,out):
    if out.exists():raise FileExistsError(out)
    candidate=latest/'candidate.json';data=json.loads(candidate.read_text());model=expand(data);L,B=model[:2]
    z=np.load(latest/'state.npz');ex=expand_primitives(json.loads(str(z['primitives_json'])),L)
    current=json.loads((latest/'results.json').read_text());gamma=current['records'][-1]['training_minimum']
    saved_poses=json.loads((latest/'poses.json').read_text())
    trained={tuple(map(F,p)) for p in saved_poses['train']}
    last=current['records'][-1]
    pending={tuple(map(F,p)) for p in saved_poses['held']}
    pending.update(tuple(F(row[k]) for k in ('cx','cy','t')) for row in current['local_witnesses']+last['local_witnesses'])
    scan=poses(L,last.get('scan_count',2048),last['scan_seed']);values=coefficients(scan,B,ex,L)@z['weights']
    pending.update(scan[int(i)] for i in np.argsort(values)[:128] if values[i]<gamma-1e-8)
    pool=set();sources=[]
    for f in sorted(root.glob('priced-*/results.json')):
        c=f.parent/'candidate.json'
        if not c.exists():continue
        d=json.loads(c.read_text());report=json.loads(f.read_text())
        if not isinstance(report,dict) or not report.get('records'):continue
        if d.get('n')!=data.get('n') or F(d['L'])!=L or F(d['B'])!=B:continue
        rows=list(report.get('local_witnesses',[]))+list(report.get('exact_held_checks',[]))
        for rec in report['records']:rows.extend(rec.get('local_witnesses',[]))
        for row in rows:pool.add(tuple(F(row[k]) for k in ('cx','cy','t')))
        last=report['records'][-1]
        pool.update(poses(L,last.get('scan_count',2048),last['scan_seed']))
        sources.append(dict(path=str(f),sha256=hashlib.sha256(f.read_bytes()).hexdigest(),candidate_sha256=hashlib.sha256(c.read_bytes()).hexdigest()))
    missing=sorted(pool-trained)
    for x,y,t in missing:
        u=abs(t);h=(1-u*u+2*u)/(2*(1+u*u))
        if u>1 or not(h<=x<=L-h and h<=y<=L-h):raise ValueError('Nonphysical archive pose')
    checks=[];numeric_below_one=0;selected_count=0
    for offset in range(0,len(missing),2048):
        batch=missing[offset:offset+2048];values=coefficients(batch,B,ex,L)@z['weights']
        numeric_below_one+=int(sum(values<1))
        for i,value in enumerate(values):
            if value<1 or value<gamma-1e-8:
                selected_count+=1;row=evaluate(model,*batch[i])
                if informative_local(row,gamma):checks.append(row)
    report=dict(status='FINITE_ARCHIVED_WITNESS_AUDIT',candidate_sha256=hashlib.sha256(candidate.read_bytes()).hexdigest(),
                scope='priced-*/results.json matching n,L,B; all recorded local witnesses and each final deterministic scan',
                sources=sources,archived_unique=len(pool),already_trained=len(pool&trained),not_trained=len(missing),
                numeric_below_one=numeric_below_one,exact_checked=selected_count,selected=len(checks),
                exact_below_one=sum(F(row['score'])<1 for row in checks),
                beyond_next_resume=sum(tuple(F(row[k]) for k in ('cx','cy','t')) not in pending for row in checks),
                subunit_beyond_next_resume=sum(F(row['score'])<1 and tuple(F(row[k]) for k in ('cx','cy','t')) not in pending for row in checks),
                exact_minimum=str(min(F(row['score']) for row in checks)) if checks else None,
                local_witnesses=checks,general_packing_exclusion=False)
    out.write_text(json.dumps(report,indent=2));print({k:v for k,v in report.items() if k not in ('local_witnesses','sources')},flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser()
    for name in ('root','latest','out'):p.add_argument(name,type=Path)
    a=p.parse_args();run(a.root,a.latest,a.out)
