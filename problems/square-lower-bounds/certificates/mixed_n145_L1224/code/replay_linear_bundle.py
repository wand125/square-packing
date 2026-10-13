"""Replay-only check of an existing unified_linear (points/segments/rectangles) certificate directory.

Uses the same per-angle replay as unified_linear_full_verify (regenerate each input from the candidate,
compare byte-for-byte, rerun the outward-rounded verifier with the stored node budget, compare the result),
then checks the stored certificate's per-angle records. Same implementation, not a second algorithm.
"""
import argparse,json,hashlib,sys
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor,as_completed
from unified_measure import validate,net_check
from unified_linear_verify import SOURCE,compile_verifier
from unified_linear_full_verify import replay_angle
from mixed_net_audit import net_certificate


def main():
    ap=argparse.ArgumentParser();ap.add_argument('root',type=Path);ap.add_argument('--workers',type=int,default=3);ap.add_argument('--smoke',type=int,default=0,help='debug only: replay just the first K angles (never a certificate check)');a=ap.parse_args()
    root=a.root.resolve();cand=root/'candidate.json';cert=json.loads((root/'certificate.json').read_text());man=json.loads((root/'manifest.json').read_text())
    data=json.loads(cand.read_text());L,B,n,expanded,mass,digest=validate(data);step,last=net_check(data);count=last+1
    assert cert['status']=='ALL_LINEAR_ANGLES_VERIFIED_AND_REPLAYED' and cert['candidate_digest']==digest==man['candidate_digest']
    assert 0<mass<n and str(mass)==cert['total_mass'] and cert['net']==man['net']==net_certificate(B,step,last) and cert['angle_count']==count
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()==man['source_sha256']==cert['source_sha256'],'verifier source differs from the certificate'
    binary=root.parent/(root.name+'-replay-verify');compile_verifier(binary);out={}
    with ProcessPoolExecutor(max_workers=a.workers) as pool:
        fs=[pool.submit(replay_angle,(str(cand),str(root/f'net{j:03}'),str(binary))) for j in (range(a.smoke) if a.smoke else range(count))]
        for f in as_completed(fs):
            r=f.result();out[str(r['index'])]=r
            if len(out)%20==0 or len(out)==count:print(json.dumps(dict(replayed=len(out),total=count)),flush=True)
    if a.smoke:
        assert all(out[k]==cert['results'][k] for k in out);print(json.dumps(dict(status='SMOKE_ONLY_NOT_A_CHECK',replayed=sorted(map(int,out)))));return
    assert set(out)==set(map(str,range(count))) and all(out[k]==cert['results'][k] for k in out),'replay differs from the stored certificate'
    print(json.dumps(dict(status='ALL_LINEAR_ANGLES_REPLAYED_MATCHING_CERTIFICATE',n=n,L=str(L),total_mass=str(mass),candidate_digest=digest)),flush=True)


if __name__=='__main__':main()
