"""Continue shared-angle proofs without recomputing verified subtrees."""
from pathlib import Path
from datetime import datetime,timezone
import argparse,hashlib,json,os,time
from variable_rotor_angles import model,verify
from bounded_farkas import certificate
from resume_disjunctive import resume_model


def main():
    p=argparse.ArgumentParser();p.add_argument('source',type=Path);p.add_argument('out',type=Path);p.add_argument('--nodes',type=int,default=1000);a=p.parse_args()
    raw=a.source.read_bytes();q=json.loads(raw);assert q['model']=='SHARED_ROTOR_ANGLE_MCCORMICK_V2'
    data,gap=model(q['config'],q['missing'],q['chosen'],True)
    r=dict(model=q['model'],config=q['config'],missing=q['missing'],chosen=q['chosen'],gap_index=gap,
           source=str(a.source),source_sha256=hashlib.sha256(raw).hexdigest(),worker_pid=os.getpid(),
           started=datetime.now(timezone.utc).isoformat(),status='RUNNING',additional_node_limit=a.nodes)
    a.out.write_text(json.dumps(r,indent=2));print('worker_pid',os.getpid(),flush=True);start=time.monotonic()
    result=resume_model(data,q['tree'],a.nodes,positive_index=gap,certificate_solver=certificate)
    r.update(result,seconds=time.monotonic()-start)
    assert r['verified']==verify(r)
    tmp=a.out.with_suffix('.tmp');tmp.write_text(json.dumps(r,indent=2));tmp.replace(a.out)
    print({k:r[k] for k in ('status','nodes','reused_subtrees','seconds','verified')},flush=True)


if __name__=='__main__':main()
