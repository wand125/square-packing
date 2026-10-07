"""Rebuild fixed-orbit monotone-repair dual loads using rational polygons."""
from pathlib import Path
from fractions import Fraction as F
from collections import defaultdict
import json,hashlib,argparse
from probe_external_integer_bridge import read
from score import square,contains

def run(source,witnesses,dualfile,out):
 assert not out.exists();d=json.loads(witnesses.read_text());assert hashlib.sha256(source.read_bytes()).hexdigest()==d['source_sha256'];L,span,W,pts=read(source);audit=json.loads(dualfile.read_text());multipliers=list(map(F,audit['multipliers']));assert len(multipliers)==len(d['witnesses']) and all(v>=0 for v in multipliers);groups=defaultdict(list)
 for i,(x,y,w) in enumerate(pts):groups[tuple(sorted((min(x,span-x),min(y,span-y))))].append(i)
 loads=[F(0)]*len(pts);lower=F(0);lower_one=F(0)
 for multiplier,row in zip(multipliers,d['witnesses']):
  if not multiplier:continue
  x,y,t=map(F,row['pose']);poly=square(x,y,F(1),t);assert all(0<=x<=L and 0<=y<=L for x,y in poly);score=F(0)
  for i,(x,y,w) in enumerate(pts):
   if contains(poly,(F(x)*L/span,F(y)*L/span)):loads[i]+=multiplier;score+=F(w,W)
  assert score==F(row['before']);lower+=multiplier*max(F(0),F(d['target'])-score);lower_one+=multiplier*max(F(0),F(1)-score)
 maximum=max(sum((loads[i] for i in group),F(0))/len(group) for group in groups.values());assert maximum<=1 and maximum==F(audit['max_column_load']);assert lower==F(audit['increment_lower']) and lower_one==F(audit['increment_lower_at_capture_one']);increase=F(d['total_mass'])-F(d['original_mass']);assert increase>=lower
 result=dict(status='EXACT_INCREMENT_DUAL_REPLAYED',source_sha256=d['source_sha256'],dual_sha256=hashlib.sha256(dualfile.read_bytes()).hexdigest(),all_columns=len(groups),max_column_load=str(maximum),increment_lower=str(lower),increment_lower_at_capture_one=str(lower_one),greedy_increment=str(increase),greedy_optimal_for_finite_monotone_problem=increase==lower,general_packing_exclusion=False)
 out.write_text(json.dumps(result,indent=2));print(result)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('source',type=Path);p.add_argument('witnesses',type=Path);p.add_argument('dual',type=Path);p.add_argument('out',type=Path);a=p.parse_args();run(a.source,a.witnesses,a.dual,a.out)
