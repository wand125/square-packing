"""Full 201-node mixed certificate verification, exact budget scaling, <=3 CPUs.
No success on partial coverage. Freeze source, candidate and per-angle inputs.
"""
import argparse,json,shutil,hashlib
from pathlib import Path
from fractions import Fraction as F
from concurrent.futures import ProcessPoolExecutor,as_completed
from mixed_density_check import expand
from mixed_net_audit import symmetry,net_certificate,candidate_net
from mixed_axis_verify import verify as axis
from verify_axis_certificate import replay as axis_replay
from mixed_rotated_verify import run,compile_verifier,SOURCE


def scale(data,budget):
    m=expand(data);symmetry(m);net_certificate(m[1],*candidate_net(data));budget=F(budget)
    if not m[-2]<=budget<data['n']:raise ValueError('Scaling requires old mass <= budget < n')
    factor=budget/m[-2];out=json.loads(json.dumps(data))
    for key in ('rectangles','points'):
        for record in out[key]:record['mass']=str(F(record['mass'])*factor)
    out['total_mass']=str(budget);out['scaling_source_digest']=m[-1];out['scaling_factor']=str(factor)
    checked=expand(out);assert checked[-2]==budget;symmetry(checked);return out


def worker(args):
    candidate,index,folder,binary,nodes=args
    r=run(Path(candidate),index,Path(folder),Path(binary),nodes=nodes,gamma=F(1))
    return dict(index=index,status=r['status'],nodes=r['nodes'],seconds=r['seconds'],witnesses=len(r['exact_witnesses']))


def priority_angles(base,last=200):
    """Recent exact failures and neighbours first; still require all 201 to pass."""
    paths=sorted(base.glob('round*/summary.json'),key=lambda p:int(p.parent.name[5:]),reverse=True)
    seeds=[]
    for path in paths[:3]:
        old=json.loads(path.read_text())
        seeds.extend(int(j) for j,r in old['records'].items() if r['status']=='ANGLE_BELOW_GAMMA')
    order=[]
    for j in seeds:
        for d in (0,-1,1,-2,2):
            q=j+d
            if 1<=q<=last and q not in order:order.append(q)
    return order


def main(candidate,out,budget=F(20999,1000),workers=3,nodes=1000000):
    assert 1<=workers<=3
    out=Path(out).resolve();out.mkdir(parents=True,exist_ok=False)
    data=scale(json.loads(Path(candidate).read_text()),budget);step,last=candidate_net(data);count=last+1;p=out/'candidate.json';p.write_text(json.dumps(data,indent=2));model=expand(data)
    shutil.copyfile(SOURCE,out/'verify.cpp');binary=out/'verify';compile_verifier(binary)
    manifest=dict(candidate_digest=model[-1],source_candidate=str(Path(candidate).resolve()),budget=str(budget),n=data['n'],L=data['L'],B=data['B'],net=net_certificate(model[1],step,last),source_sha256=hashlib.sha256(SOURCE.read_bytes()).hexdigest(),workers=workers,node_limit=nodes)
    priority=priority_angles(out.parent,last);manifest['priority_angles']=priority;manifest['stop_on_exact_deficit']=True
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2))
    a=axis(p,out/'axis',gamma=F(1));records={0:dict(index=0,status=a['status'])}
    if a['status']=='AXIS_VERIFIED':axis_replay(out/'axis')
    def save(status=None):
        good=sum(v['status'] in ('AXIS_VERIFIED','ANGLE_VERIFIED') for v in records.values())
        summary=dict(candidate_digest=model[-1],complete_angles=len(records),verified_angles=good,status=status or ('ALL_ANGLES_VERIFIED_AWAITING_REPLAY' if good==count else 'PARTIAL_NOT_CERTIFIED'),records=records)
        tmp=out/'summary.tmp';tmp.write_text(json.dumps(summary,indent=2));tmp.replace(out/'summary.json')
        return good
    save()
    if a['status']=='AXIS_BELOW_GAMMA':
        save('DEFICITS_REQUIRE_REPAIR')
        print(json.dumps(dict(status='DEFICITS_REQUIRE_REPAIR',out=str(out),index=0)),flush=True)
        return
    def accept(r):
        records[r['index']]=r;good=save()
        print(json.dumps(dict(done=len(records),verified=good,**r)),flush=True)
    with ProcessPoolExecutor(max_workers=workers) as pool:
        for offset in range(0,len(priority),workers):
            batch=priority[offset:offset+workers]
            results=list(pool.map(worker,[(str(p),j,str(out/f'net{j:03}'),str(binary),nodes) for j in batch]))
            for r in results:accept(r)
            if any(r['status']=='ANGLE_BELOW_GAMMA' for r in results):
                save('PRIORITY_DEFICITS_REQUIRE_REPAIR')
                print(json.dumps(dict(status='PRIORITY_DEFICITS_REQUIRE_REPAIR',out=str(out))),flush=True)
                return
        remaining=[j for j in range(1,count) if j not in records]
        futures=[pool.submit(worker,(str(p),j,str(out/f'net{j:03}'),str(binary),nodes)) for j in remaining]
        failed=False
        for future in as_completed(futures):
            if future.cancelled():continue
            r=future.result();accept(r)
            if r['status']=='ANGLE_BELOW_GAMMA' and not failed:
                failed=True
                for pending in futures:pending.cancel()
        if failed:
            save('DEFICITS_REQUIRE_REPAIR')
            print(json.dumps(dict(status='DEFICITS_REQUIRE_REPAIR',out=str(out))),flush=True)
            return
    print(json.dumps(dict(status='FULL_PASS_AWAITING_REPLAY' if save()==count else 'REPAIR_OR_REFINEMENT_REQUIRED',out=str(out))),flush=True)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--candidate',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--budget',type=F,default=F(20999,1000));p.add_argument('--workers',type=int,default=3);p.add_argument('--nodes',type=int,default=1000000);a=p.parse_args();main(a.candidate,a.out,a.budget,a.workers,a.nodes)
