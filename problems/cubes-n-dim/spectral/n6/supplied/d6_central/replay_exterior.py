"""Exact finite constants in EXTERIOR_FOUR_BOUND.md."""
from fractions import Fraction as F
assert F(5,5**8)<F(1,4**8)
assert F(9477,13**8)==F(3**6,13**7)<F(1,4**8)
assert max(a*(6-a) for a in range(1,6))==9
print('Fourth exterior bound finite comparisons verified exactly.')
