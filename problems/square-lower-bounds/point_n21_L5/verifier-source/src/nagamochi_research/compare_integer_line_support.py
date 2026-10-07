"""Exact opposing-edge support census at half-integer axis poses.
Matching counts diagnose branch complexity; they do not prove coverage.
"""
from fractions import Fraction as F
from pathlib import Path
from collections import defaultdict
import json,argparse,hashlib
from probe_external_integer_bridge import read

def inspect(path,K,centres):
 native,span,W,pts=read(path);measure=defaultdict(F)
 for x,y,w in pts:measure[F(x)*K/span,F(y)*K/span]+=F(w,W)
 records=[]
 for cx,cy in centres:
  edges={name:{} for name in ['bottom','top','left','right']}
  for (x,y),w in measure.items():
   if cx-F(1,2)<x<cx+F(1,2):
    if y==cy-F(1,2):edges['bottom'][x]=w
    if y==cy+F(1,2):edges['top'][x]=w
   if cy-F(1,2)<y<cy+F(1,2):
    if x==cx-F(1,2):edges['left'][y]=w
    if x==cx+F(1,2):edges['right'][y]=w
  pairs=[]
  for a,b in [('bottom','top'),('left','right')]:
   one,two=edges[a],edges[b];shared=one.keys()&two.keys();unmatched=one.keys()^two.keys()
   pairs.append(dict(edges=[a,b],counts=[len(one),len(two)],shared_positions=len(shared),union_positions=len(one.keys()|two.keys()),unmatched_positions=len(unmatched),unmatched_mass=str(sum((one.get(x,F(0))+two.get(x,F(0)) for x in unmatched),F(0)))))
  records.append(dict(centre=[str(cx),str(cy)],opposing_pairs=pairs))
 return dict(file=str(path),sha256=hashlib.sha256(path.read_bytes()).hexdigest(),normalized_integer_side=str(K),total_mass=str(sum(measure.values())),points=len(measure),records=records,general_coverage_verified=False)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('root',type=Path);p.add_argument('out',type=Path);a=p.parse_args();assert not a.out.exists();centres=[(F(3,2),F(3,2)),(F(3,2),F(5,2)),(F(5,2),F(5,2))]
 result=[inspect(a.root/'s12/certificates/s21/s21_lower_4.9950.txt',F(5),centres),inspect(a.root/'s12/certificates/s32/s32_closed_cover_6.txt',F(6),centres),inspect(a.root/'s12/certificates/s32/s32_shift_v1.txt',F(6),centres)];a.out.write_text(json.dumps(result,indent=2))
 for r in result:
  print(Path(r['file']).name)
  for row in r['records']:print(row['centre'],[(p['shared_positions'],p['unmatched_positions']) for p in row['opposing_pairs']])
