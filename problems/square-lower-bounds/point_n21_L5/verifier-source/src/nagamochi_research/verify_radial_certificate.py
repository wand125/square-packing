"""Replay a native or legacy mixed certificate with rational integral bounds."""
import argparse,json
from pathlib import Path
from unified_measure import verify

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('candidate',type=Path);ap.add_argument('--out',type=Path,required=True)
    ap.add_argument('--resume',action='store_true');ap.add_argument('--max-boxes',type=int,default=1000)
    ap.add_argument('--subdivisions',type=int,default=32);ap.add_argument('--max-subdivisions',type=int,default=256)
    a=ap.parse_args();data=json.loads(a.candidate.read_text())
    if a.out.resolve()==a.candidate.resolve():ap.error('checkpoint must not overwrite candidate')
    if a.out.exists() and not a.resume:ap.error('existing output requires --resume')
    work=json.loads(a.out.read_text()) if a.resume else None
    a.out.parent.mkdir(parents=True,exist_ok=True)
    def save(result):
        p=a.out.with_suffix(a.out.suffix+'.tmp');p.write_text(json.dumps(result,indent=2)+'\n');p.replace(a.out)
    result=verify(data,work,max_boxes=a.max_boxes,checkpoint=save,integral_subdivisions=a.subdivisions,max_integral_subdivisions=a.max_subdivisions)
    save(result);print(json.dumps({k:v for k,v in result.items() if k!='stack'}))

if __name__=='__main__':main()
