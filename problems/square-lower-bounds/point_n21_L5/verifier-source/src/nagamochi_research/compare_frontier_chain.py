"""Compare checker rules on identical representatives of unresolved angle bins."""
from pathlib import Path
from fractions import Fraction as F
import importlib.util,json,hashlib,time,argparse
from collections import defaultdict

def run(config,summary,out):
 assert not out.exists();c=json.loads(config.read_text());data=json.loads(summary.read_text());assert data['candidate_sha256']==c['candidate_sha256'];checker=Path(c['checker']);assert hashlib.sha256(checker.read_bytes()).hexdigest()==c['checker_sha256'];assert hashlib.sha256(Path(c['parent']).read_bytes()).hexdigest()==c['candidate_sha256']
 spec=importlib.util.spec_from_file_location('zm_pinned',checker);mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);m,pts,ws=mod.read_cert(c['parent']);groups=defaultdict(list)
 for row in data['pending']:
  box=tuple(map(F,row['box']));groups[min(7,int(8*(box[4]+box[5])))].append(row)
 records=[]
 for angle_bin,rows in sorted(groups.items()):
  row=rows[len(rows)//2];box=tuple(map(F,row['box']));methods=[]
  for name,chain,depth in [('baseline',False,0),('chain',True,0),('split4',False,4)]:
   chk=mod.Checker(m,pts,ws,max_depth=depth,use_chain=chain,theta_bias=4,chain_from=0);chk.fast='check';start=time.monotonic();stats,unc,leaves=chk.run_box(box)
   methods.append(dict(method=name,stats=stats,seconds=time.monotonic()-start,uncertified=[list(map(str,b)) for b in unc]));print(angle_bin,name,stats['UNCERT'],round(methods[-1]['seconds'],3),flush=True)
  records.append(dict(angle_bin=angle_bin,parent_index=row['parent_index'],box=row['box'],methods=methods))
 out.write_text(json.dumps(dict(candidate_sha256=c['candidate_sha256'],summary_sha256=hashlib.sha256(summary.read_bytes()).hexdigest(),checker_sha256=c['checker_sha256'],selection='middle entry in each of eight half-angle bins',selfcheck=True,records=records,general_coverage_verified=False),indent=2))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('config',type=Path);p.add_argument('summary',type=Path);p.add_argument('out',type=Path);a=p.parse_args();run(a.config,a.summary,a.out)
