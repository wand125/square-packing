"""Complete a separate normalized proof; never import original-coordinate LPs."""
from pathlib import Path
import argparse,json,os
from normalized_pair_refinement import run,complete


def main():
    p=argparse.ArgumentParser();p.add_argument('source',type=Path);p.add_argument('out',type=Path);p.add_argument('--target',type=int,required=True);a=p.parse_args()
    a.out.mkdir(exist_ok=True,parents=True)
    print('worker_pid',os.getpid(),flush=True)
    run(a.source,a.out/'pairs.json',target=a.target,strict=True)
    q=complete(a.source,a.out/'pairs.json',a.out/'completion.json',strict=True)
    if q['replay']['target_excluded']:
        base=json.loads(a.source.read_text());k=base['config']['k']
        print('EXACT_NORMALIZED_FIXED_BAND_EXCLUSION',k,'axis halfwidth epsilon/'+str(2*(k-1)),flush=True)


if __name__=='__main__':main()
