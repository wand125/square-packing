"""Recheck the entire 201-angle result and emit a theorem-level manifest.
The axis integer-table replay is independent; oblique checks re-run the same
outward-rounded implementation from regenerated rational inputs.
"""
import argparse,json,hashlib
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor,as_completed
from fractions import Fraction as F
from mixed_density_check import expand
from mixed_net_audit import symmetry,net_certificate,centre_domains,candidate_net
from mixed_rotated_verify import compile_verifier,SOURCE
from verify_rotated_result import replay
from verify_axis_certificate import replay as replay_axis


def worker(args):return replay(Path(args[0]),Path(args[1]),Path(args[2]))


def verify(root,workers=3):
    root=root.resolve();summary=json.loads((root/'summary.json').read_text())
    data=json.loads((root/'candidate.json').read_text());m=expand(data);symmetry(m);step,last=candidate_net(data);count=last+1;net=net_certificate(m[1],step,last);domains=centre_domains(m[0],m[1],step,last);manifest=json.loads((root/'manifest.json').read_text())
    assert summary['verified_angles']==count and summary['complete_angles']==count
    assert manifest['net']==net
    assert set(map(int,summary['records']))==set(range(count))
    assert summary['candidate_digest']==manifest['candidate_digest']==m[-1]
    assert (root/'verify.cpp').read_bytes()==SOURCE.read_bytes();assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()==manifest['source_sha256']
    axis=replay_axis(root/'axis',root/'candidate.json');assert axis['digest']==m[-1] and F(axis['gamma'])>=1
    binary=root/'replay-verify';compile_verifier(binary);checked={0:axis}
    futures=[]
    with ProcessPoolExecutor(max_workers=workers) as pool:
        for j in range(1,count):
            p=root/f'net{j:03}';r=json.loads((p/'result.json').read_text());s=r['manifest']
            assert r['status']=='ANGLE_VERIFIED' and r['frontier']==[]
            assert s['candidate_digest']==m[-1] and s['net_index']==j and s['domain']==domains[j] and F(s['gamma'])>=1
            futures.append(pool.submit(worker,(str(p),str(binary),str(root/'candidate.json'))))
        for future in as_completed(futures):
            result=future.result();checked[result['index']]=result
            (root/'replay-progress.json').write_text(json.dumps(dict(done=len(checked),total=count),indent=2))
            if len(checked)%10==0 or len(checked)==count:print(json.dumps(dict(replayed=len(checked),total=count)),flush=True)
    assert set(checked)==set(range(count))
    result=dict(status='ALL_ANGLES_VERIFIED_AND_REPLAYED',n=data['n'],L=data['L'],B=data['B'],total_mass=str(m[-2]),budget_gap=str(F(data['n'])-m[-2]),candidate_digest=m[-1],angle_count=count,net=net,
                theorem='No packing of n closed unit squares in the closed square of side L: choose disjoint interior closed cores at net angles; each has measure >=1 but total measure <n.',
                replay_scope='Independent axis integer-table checker; oblique verification uses regenerated input and the same outward-rounded algorithm. Not a separate independent oblique implementation.',
                point_mass=str(sum((w for p,w in m[3]),F(0))),results=checked)
    (root/'certificate.json').write_text(json.dumps(result,indent=2));print(json.dumps({k:v for k,v in result.items() if k not in ('results','net')}),flush=True)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('root',type=Path);p.add_argument('--workers',type=int,default=3);a=p.parse_args();assert 1<=a.workers<=3;verify(a.root,a.workers)
