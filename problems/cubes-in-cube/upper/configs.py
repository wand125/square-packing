"""Exact packings. A cube is (centre, R) with R's columns the cube axes; entries are
(a, b) meaning a + b*sqrt2 with a, b rational given as strings. Side s and the configurations:
  n8_side2  : 2x2x2 grid in side 2 (s3(2..8) <= 2)
  n9_s      : 8 corner cubes + 1 cube rotated 45 deg about z at the centre, side s = 2 + 1/sqrt2
  n10_s     : 8 corner cubes + 2 such cubes at z in [0,1] and [s-1,s]."""
from fractions import Fraction as F
def q(a, b=0): return (F(a), F(b))
I = [[q(1), q(0), q(0)], [q(0), q(1), q(0)], [q(0), q(0), q(1)]]
H = q(0, '1/2')                      # 1/sqrt2 = sqrt2/2
Z45 = [[H, (-H[0], -H[1]), q(0)], [H, H, q(0)], [q(0), q(0), q(1)]]
S = q(2, '1/2')                      # 2 + 1/sqrt2
def corner(side):
    lo, hi = q('1/2'), (side[0] - F(1, 2), side[1])
    return [([x, y, z], I) for x in (lo, hi) for y in (lo, hi) for z in (lo, hi)]
mid = (S[0] / 2, S[1] / 2)
CONFIGS = {
    'n8_side2': (q(2), corner(q(2))),
    'n9_s': (S, corner(S) + [([mid, mid, mid], Z45)]),
    'n10_s': (S, corner(S) + [([mid, mid, q('1/2')], Z45), ([mid, mid, (S[0] - F(1, 2), S[1])], Z45)]),
}
