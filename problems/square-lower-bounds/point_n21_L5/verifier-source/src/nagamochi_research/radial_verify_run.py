"""Pool-compatible resumable exact verification of a frozen native candidate."""
import os
for name in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMBA_NUM_THREADS'):os.environ[name]='1'
import argparse,json,time,hashlib
from pathlib import Path
from fractions import Fraction as F
from unified_measure import verify,validate

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--config',type=Path,required=True);a=ap.parse_args()
    cfg=json.loads(a.config.read_text());base=a.config.resolve().parent
    source=base/cfg['parent'];candidate=json.loads(source.read_text());L,B,n,_,mass,_=validate(candidate)
    if n!=cfg['n'] or L!=F(cfg['L']) or mass!=F(cfg['target']) or not 0<mass<n:raise ValueError('candidate/config mismatch or invalid budget')
    out=base/cfg['out'];out.mkdir(parents=True,exist_ok=True)
    proof=out/'proof.json';progress=out/'progress.json'
    records=json.loads(progress.read_text())['records'] if progress.exists() else [];started=time.monotonic()
    def write(path,data):
        p=path.with_suffix(path.suffix+'.tmp');p.write_text(json.dumps(data,indent=2)+'\n');p.replace(path)
    def emit(**kw):
        kw['elapsed']=time.monotonic()-started;records.append(kw);write(progress,dict(records=records));print(json.dumps(kw),flush=True)
    work=json.loads(proof.read_text()) if proof.exists() else json.loads((base/cfg['proof_parent']).read_text()) if cfg.get('proof_parent') else None
    write(out/'manifest.json',dict(config=cfg,parent_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),source_sha256={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in Path(__file__).parent.glob('*.py')}))
    try:
        while True:
            work=verify(candidate,work,max_boxes=cfg.get('chunk_boxes',16),checkpoint=lambda w:write(proof,w),
                integral_subdivisions=cfg.get('integral_subdivisions',32),max_integral_subdivisions=cfg.get('max_integral_subdivisions',256))
            emit(operation='proof',status=work['status'],boxes=work['boxes'],directions_completed=work['directions_completed'])
            if work['status']=='CERTIFIED':
                write(out/'certificate.json',candidate);emit(operation='finish',status='CERTIFIED',globally_verified=True);return
            if work['status']=='UNCOVERED':
                emit(operation='finish',status='SAVED_EXACT_COUNTEREXAMPLE',witness=work['witness'],globally_verified=False);return
            if work.get('reason')=='INTEGRAL_PRECISION':
                emit(operation='finish',status='SAVED_INTEGRAL_REVIEW',globally_verified=False);return
            if work['boxes']>=cfg.get('review_boxes',20000):
                emit(operation='finish',status='SAVED_EXACT_REVIEW',globally_verified=False);return
    except Exception as e:emit(operation='error',status='ERROR',error=repr(e));raise

if __name__=='__main__':main()
