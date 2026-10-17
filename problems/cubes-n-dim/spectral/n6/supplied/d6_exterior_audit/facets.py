"""Enumerate exact facets of conv(v_1,...,v_5)-R_+^5 through its polar."""
from fractions import Fraction as Q
from math import comb
from itertools import combinations
from pathlib import Path
import json
n=5
V=[[Q(comb(m,k),m**(2*k)) if k<=m else Q(0) for k in range(1,n+1)] for m in range(1,n+1)]
def solve(A,b):
 B=[list(r)+[s] for r,s in zip(A,b)]
 for j in range(n):
  k=next((k for k in range(j,n) if B[k][j]),None)
  if k is None:return None
  B[j],B[k]=B[k],B[j];q=B[j][j];B[j]=[x/q for x in B[j]]
  for k in range(n):
   if k!=j:
    q=B[k][j];B[k]=[x-q*y for x,y in zip(B[k],B[j])]
 return tuple(r[-1] for r in B)
cons=[([Q(int(i==j)) for i in range(n)],Q(0)) for j in range(n)]+[(v,Q(1)) for v in V]
vertices={};singular=0
for indices in combinations(range(10),5):
 z=solve([cons[i][0] for i in indices],[cons[i][1] for i in indices])
 if z is None:singular+=1;continue
 if min(z)<0 or any(sum(x*y for x,y in zip(v,z))>1 for v in V):continue
 vertices[z]=True
facets=sorted(z for z in vertices if any(z))
data={'dimension':5,'support_vectors':[[str(x) for x in v] for v in V],'active_constraint_subsets_checked':comb(10,5),'singular_subsets':singular,'polar_vertex_count_including_zero':len(vertices),'facet_count':len(facets),'facets':[{'a':[str(x) for x in z],'rhs':'1','active_support_sizes':[m+1 for m,v in enumerate(V) if sum(x*y for x,y in zip(v,z))==1]} for z in facets]}
Path(__file__).with_name('facets.json').write_text(json.dumps(data,indent=2));print(json.dumps(data,indent=2))
