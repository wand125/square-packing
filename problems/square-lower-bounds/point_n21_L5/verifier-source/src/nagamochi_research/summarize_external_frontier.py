"""Compare unresolved parameter volume and original roots across refinement."""
from pathlib import Path
from fractions import Fraction as F
from math import prod
from collections import Counter
import json,argparse,hashlib

def volume(box):
 b=list(map(F,box));assert all(b[i]<=b[i+1] for i in (0,2,4));return prod(b[i+1]-b[i] for i in (0,2,4))
def run(config,out):
 assert not out.exists();c=json.loads(config.read_text());front=Path(c['frontier']);assert hashlib.sha256(front.read_bytes()).hexdigest()==c['frontier_sha256'];source=json.loads(front.read_text());rows=[json.loads(l) for l in (Path(c['output'])/'roots.jsonl').read_text().splitlines()];assert len(rows)==len(source['pending']);remaining=[];failed_original=set();tally=Counter()
 for index,(r,parent) in enumerate(zip(rows,source['pending'])):
  assert r['index']==index and r['root']==parent['box'] and r['config_sha256']==hashlib.sha256(config.read_bytes()).hexdigest();tally.update(r['stats']);bounds=list(map(F,parent['box']))
  for b in r['uncertified']:
   v=list(map(F,b));assert all(bounds[i]<=v[i]<=v[i+1]<=bounds[i+1] for i in (0,2,4));remaining.append(dict(parent_index=parent['parent_index'],box=b));failed_original.add(parent['parent_index'])
 old=sum((volume(p['box']) for p in source['pending']),F(0));new=sum((volume(p['box']) for p in remaining),F(0));assert new<=old
 completed_original=len(source['inherited_root_indices'])+len({p['parent_index'] for p in source['pending']}-failed_original)
 result=dict(candidate_sha256=c['candidate_sha256'],config_sha256=hashlib.sha256(config.read_bytes()).hexdigest(),input_leaves=len(rows),completed_input_leaves=sum(not r['uncertified'] for r in rows),remaining_leaves=len(remaining),completed_original_roots=completed_original,remaining_original_roots=len(failed_original),previous_unresolved_parameter_volume=str(old),new_unresolved_parameter_volume=str(new),remaining_parameter_volume_fraction=str(new/old),volume_is_not_physical_configuration_probability=True,leaf_counts={k:v for k,v in tally.items() if k not in ('boxes','maxdepth')},pending=remaining,general_coverage_verified=False)
 out.write_text(json.dumps(result,indent=2));print({k:v for k,v in result.items() if k!='pending'})
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('config',type=Path);p.add_argument('out',type=Path);a=p.parse_args();run(a.config,a.out)
