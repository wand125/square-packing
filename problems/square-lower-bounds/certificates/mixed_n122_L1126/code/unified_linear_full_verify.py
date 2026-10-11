"""Full-net proof and regenerated-input replay for linear mixed measures.

Experimental separate verifier. No partial angle set is a global certificate.
Replay uses the same outward-rounded implementation, not a second algorithm.
"""
import argparse,json,hashlib,subprocess,tempfile
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor,as_completed
from fractions import Fraction as F
from unified_measure import validate,net_check
from unified_linear_verify import SOURCE,compile_verifier,export,run
from mixed_net_audit import net_certificate


def worker(args):
    candidate,index,out,binary,nodes=args
    r=run(Path(candidate),index,Path(out),Path(binary),nodes)
    return dict(index=index,status=r['status'],nodes=r['nodes'],seconds=r['seconds'],witnesses=len(r['exact_witnesses']))


def atomic(path,value):
    p=path.with_suffix('.tmp');p.write_text(json.dumps(value,indent=2)+'\n');p.replace(path)


def replay_angle(args):
    candidate,folder,binary=args;candidate=Path(candidate);folder=Path(folder)
    data=json.loads(candidate.read_text());stored=json.loads((folder/'result.json').read_text());m=stored['manifest']
    assert stored['status']=='ANGLE_VERIFIED' and stored['frontier']==[] and not stored['exact_witnesses']
    assert (folder/'verify.cpp').read_bytes()==SOURCE.read_bytes()
    with tempfile.TemporaryDirectory(prefix='linear-replay-') as tmp:
        path=Path(tmp)/'input.txt';manifest=export(data,m['index'],path)
        assert manifest==m and path.read_bytes()==(folder/'input.txt').read_bytes()
        result=json.loads(subprocess.check_output([str(binary),str(path),str(stored['nodes'])],text=True))
    for key in ('status','nodes','leaves','lower','frontier'):assert result[key]==stored[key],key
    return dict(index=m['index'],status='LINEAR_ANGLE_REPLAYED',input_sha256=m['input_sha256'],nodes=result['nodes'])


def verify(candidate,out,workers=2,nodes=3000000):
    if not 1<=workers<=3 or nodes<1:raise ValueError('workers/nodes')
    out=out.resolve();out.mkdir(parents=True,exist_ok=False)
    data=json.loads(candidate.read_text());L,B,n,expanded,mass,digest=validate(data);step,last=net_check(data);count=last+1
    if not 0<mass<n:raise ValueError('invalid budget')
    net=net_certificate(B,step,last);p=out/'candidate.json';p.write_text(json.dumps(data,indent=2)+'\n')
    (out/'verify.cpp').write_bytes(SOURCE.read_bytes());binary=out/'verify';compile_verifier(binary)
    manifest=dict(candidate_digest=digest,n=n,L=str(L),B=str(B),mass=str(mass),net=net,angle_count=count,workers=workers,node_limit=nodes,source_sha256=hashlib.sha256(SOURCE.read_bytes()).hexdigest())
    atomic(out/'manifest.json',manifest);records={}
    def save(status):
        atomic(out/'summary.json',dict(status=status,globally_verified=status=='ALL_LINEAR_ANGLES_VERIFIED_AND_REPLAYED',candidate_digest=digest,complete_angles=len(records),verified_angles=sum(x['status']=='ANGLE_VERIFIED' for x in records.values()),records=records))
    save('RUNNING')
    with ProcessPoolExecutor(max_workers=workers) as pool:
        fs=[pool.submit(worker,(str(p),j,str(out/f'net{j:03}'),str(binary),nodes)) for j in range(count)]
        failed=False
        for f in as_completed(fs):
            if f.cancelled():continue
            r=f.result();records[str(r['index'])]=r;save('PARTIAL_NOT_CERTIFIED');print(json.dumps(dict(done=len(records),**r)),flush=True)
            if r['status']=='ANGLE_BELOW_GAMMA' and not failed:
                failed=True
                for pending in fs:pending.cancel()
    if failed:save('EXACT_DEFICITS_REQUIRE_REPAIR');return
    if len(records)!=count or any(x['status']!='ANGLE_VERIFIED' for x in records.values()):save('INCOMPLETE_NOT_CERTIFIED');return
    save('ALL_ANGLES_VERIFIED_AWAITING_REPLAY');replayed={}
    assert (out/'verify.cpp').read_bytes()==SOURCE.read_bytes()
    binary=out/'replay-verify';compile_verifier(binary)
    with ProcessPoolExecutor(max_workers=workers) as pool:
        fs=[pool.submit(replay_angle,(str(p),str(out/f'net{j:03}'),str(binary))) for j in range(count)]
        for f in as_completed(fs):
            r=f.result();replayed[str(r['index'])]=r;atomic(out/'replay-progress.json',dict(done=len(replayed),total=count))
            if len(replayed)%10==0 or len(replayed)==count:print(json.dumps(dict(replayed=len(replayed),total=count)),flush=True)
    assert set(map(int,replayed))==set(range(count))
    assert validate(json.loads(p.read_text()))[-1]==digest
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()==manifest['source_sha256']
    certificate=dict(status='ALL_LINEAR_ANGLES_VERIFIED_AND_REPLAYED',n=n,L=str(L),B=str(B),total_mass=str(mass),budget_gap=str(n-mass),candidate_digest=digest,net=net,angle_count=count,source_sha256=manifest['source_sha256'],results=replayed,
        theorem='No packing of n closed unit squares in the closed container: strictly interior net cores are disjoint, each has measure at least 1, and total nonnegative measure is below n.',
        replay_scope='All angles including axis use regenerated inputs and the SAME outward-rounded implementation. Not an independent second algorithm or proof-assistant formalization.')
    atomic(out/'certificate.json',certificate);save('ALL_LINEAR_ANGLES_VERIFIED_AND_REPLAYED');print(json.dumps(dict(status=certificate['status'],n=n,L=str(L))),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--candidate',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--workers',type=int,default=2);p.add_argument('--nodes',type=int,default=3000000);a=p.parse_args();verify(a.candidate,a.out,a.workers,a.nodes)
