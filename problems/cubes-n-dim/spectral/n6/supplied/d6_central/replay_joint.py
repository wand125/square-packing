"""Exact rational checks for JOINT_EXTERIOR_BOUND.md."""
from fractions import Fraction as F
from math import comb
M=F(1,4**8)
c=(M-F(1,5**7))*5**10
assert c==F(1573625,65536)
for m in range(1,6):
    e4=F(comb(m,4),m**8) if m>=4 else F(0)
    e5=F(comb(m,5),m**10) if m>=5 else F(0)
    assert e4+c*e5<=M
D=F(8,5**7)+10*c/F(5**10)
w4=F(3297,1000);w5=F(121,125)
assert (w4*D/8)**8 < F(1,5**49)
assert w5*D <10*c/F(5**9)
print('Joint exterior scalar constant and rational tangent weights verified exactly.')
