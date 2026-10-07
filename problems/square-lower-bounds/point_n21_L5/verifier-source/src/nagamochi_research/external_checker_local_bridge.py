"""Small actual upstream-checker runs; records exact scope, never global proof."""
from pathlib import Path
from fractions import Fraction as F
import importlib.util,json,hashlib,argparse,time

def run(root,out):
 assert not out.exists();checker=root/'s12/search/zeromargin.py';spec=importlib.util.spec_from_file_location('upstream_zm',checker);mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
 witness=json.loads((root/'n21-L4999-refined-witness.json').read_text())['minimum'];cx,cy,t=(F(witness[k]) for k in ('cx','cy','t'));e=F(1,1000000)
 tasks=[('n21-repaired-witness',root/'n21-monotone-repair/candidate.txt',(cx-e,cx+e,cy-e,cy+e,t-e,t+e)),('n32-interior-germ',root/'s12/certificates/s32/s32_shift_v1.txt',(F(1499,1000),F(1501,1000),F(1499,1000),F(1501,1000),F(0),F(1,10000)))]
 records=[]
 for name,cert,box in tasks:
  start=time.monotonic();m,pts,ws=mod.read_cert(str(cert));chk=mod.Checker(m,pts,ws,max_depth=8,use_chain=True,chain_from=0);chk.fast='check';result=chk.run_box(box);stats,unc,leaves=result
  records.append(dict(name=name,certificate_sha256=hashlib.sha256(cert.read_bytes()).hexdigest(),box=list(map(str,box)),stats=stats,uncertified=[list(map(str,b)) for b in unc],seconds=time.monotonic()-start,selfcheck=True))
  print(name,stats,'seconds',records[-1]['seconds'],flush=True)
 out.write_text(json.dumps(dict(checker_sha256=hashlib.sha256(checker.read_bytes()).hexdigest(),records=records,general_coverage_verified=False),indent=2))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('root',type=Path);p.add_argument('out',type=Path);a=p.parse_args();run(a.root,a.out)
