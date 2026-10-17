"""Exact exhaustive projected root Gram determinant audit; no numerical dependencies."""
from itertools import combinations
from fractions import Fraction as F
from collections import Counter
from pathlib import Path
import json
# Independent determinant via the permutation formula, rather than audit.py elimination.
def det4(M):
 from itertools import permutations
 out=0
 for p in permutations(range(4)):
  inversions=sum(p[i]>p[j] for i in range(4) for j in range(i+1,4));v=(-1)**inversions
  for i in range(4):v*=M[i][p[i]]
  out+=v
 return out
edges=list(combinations(range(6),2));hist=[]
for deleted in range(6):
 counts=Counter()
 for chosen in combinations(edges,4):
  E=[[int(i==a)-int(i==b) for a,b in chosen] for i in range(6) if i!=deleted]
  G=[[sum(E[k][i]*E[k][j] for k in range(5)) for j in range(4)] for i in range(4)]
  counts[det4(G)]+=1
 assert max(counts)==5 and sum(counts.values())==1365
 hist.append({str(k):v for k,v in sorted(counts.items())})
assert all(h==hist[0] for h in hist)
# Verify exact projected e4 identity and smallest-deletion ordering on a rational test.
p=[F(7,20),F(1,4),F(3,20),F(1,10),F(1,10),F(1,20)]
def prod(v):
 z=F(1)
 for x in v:z*=x
 return z
def e4project(j):
 R=[i for i in range(6) if i!=j]
 return sum(prod([p[i] for i in I])*(1-sum(p[i] for i in I)) for I in combinations(R,4))
for j in range(6):
 q=[p[i] for i in range(6) if i!=j]
 assert e4project(j)==5*prod(q)+p[j]*sum(prod([q[i] for i in J]) for J in combinations(range(5),4))
for i,j in combinations(range(6),2):
 assert e4project(i)-e4project(j)==4*(p[j]-p[i])*prod([p[k] for k in range(6) if k not in (i,j)])
out={'deleted_rows_checked':6,'subsets_per_deleted_row':1365,'total_cases':8190,'unscaled_gram_histograms':hist,'maximum_normalized_squared_volume':'5/256','rational_projected_identity_check':True}
Path(__file__).with_name('projected_result.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
