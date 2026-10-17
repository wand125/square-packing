"""Independent exact checks for the d6 four-column exterior bound."""
from itertools import combinations
from fractions import Fraction as F
from collections import Counter
import json
from pathlib import Path

def det(M):
 M=[[F(x) for x in r] for r in M];ans=F(1);n=len(M)
 for j in range(n):
  k=next((k for k in range(j,n) if M[k][j]),None)
  if k is None:return F(0)
  if k!=j:M[j],M[k]=M[k],M[j];ans=-ans
  q=M[j][j];ans*=q
  for k in range(j+1,n):
   t=M[k][j]/q
   for l in range(j+1,n):M[k][l]-=t*M[j][l]
   M[k][j]=0
 return ans
edges=list(combinations(range(6),2));counts=Counter()
for chosen in combinations(edges,4):
 E=[[int(i==a)-int(i==b) for a,b in chosen] for i in range(6)]
 G=[[sum(E[k][i]*E[k][j] for k in range(6)) for j in range(4)] for i in range(4)]
 counts[det(G)]+=1
assert max(counts)==9 and sum(counts.values())==1365
boundary=F(1,4**8);equal5=F(1,5**7);one_vs_four_stationary=F(3**6,13**7)
assert equal5<boundary and one_vs_four_stationary<boundary
# Exact coefficient identity for the 2:3 stationary equation:
# (4r+12r^3)(2r+3)-16(2r²+3r⁴)=12r(1-r)(2r²-r+1).
def mul(a,b):
 c=[0]*(len(a)+len(b)-1)
 for i,x in enumerate(a):
  for j,y in enumerate(b):c[i+j]+=x*y
 return c
def sub(a,b):
 n=max(len(a),len(b));return [(a[i] if i<len(a) else 0)-(b[i] if i<len(b) else 0) for i in range(n)]
lhs=sub(mul([0,4,0,12],[3,2]),[0,0,32,0,48])
rhs=mul([0,12],mul([1,-1],[1,-1,2]))
assert lhs==rhs
# The 1:4 stationary numerator is -8(3r²-4r+1).
assert sub(mul([0,8],[4,1]),[8,0,32])==[-8,32,-24]
result={'four_edge_subsets':1365,'unscaled_gram_determinant_counts':{str(k):v for k,v in sorted(counts.items())},'normalized_max_determinant':str(F(9,256)),'scalar_boundary':str(boundary),'scalar_equal5':str(equal5),'scalar_one_vs_four_r_one_third':str(one_vs_four_stationary),'strict_comparisons_verified':True}
print(json.dumps(result,indent=2));Path(__file__).with_name('result.json').write_text(json.dumps(result,indent=2))
