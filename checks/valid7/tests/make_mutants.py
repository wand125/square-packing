"""Write mutant covers next to this file.  Each lowers the mass of a known tight configuration by a relative 1e-4,
so a sound checker must refuse it (a counterexample or a failed Tier B value check).
  M1: segments inside [5/2, 7/2] x [0, 1]  (wall family, (m - 1)/u ~ 0.40 on the original)
  M2: the Lebesgue square                  (every square inside it has mass exactly 1 on the original)
  M3: segments inside [1, 2]^2             (corner family, (m - 1)/u ~ 0.48 on the original)
"""
import os, sys
from fractions import Fraction as F

here = os.path.dirname(os.path.abspath(__file__))
src = sys.argv[1] if len(sys.argv) > 1 else os.path.join(here, '..', 'cover', 'L4_k02_box7.txt')
lines = open(src).read().rstrip('\n').split('\n')
D = 5


def seg_mutant(name, inside):
    out, k = [], 0
    for l in lines:
        t = l.split('#')[0].split()
        if len(t) == 5:
            x0, y0, x1, y1, w = map(int, t)
            if inside(*(F(v, D) for v in (x0, y0, x1, y1))):
                w = w * 9999 // 10000; k += 1
                l = f'{x0} {y0} {x1} {y1} {w}'
        out.append(l)
    out.insert(1, f'# mutant {name}: {k} segments x (1 - 1e-4)')
    open(os.path.join(here, name + '.txt'), 'w').write('\n'.join(out) + '\n')


seg_mutant('M1_wall_1e-4', lambda x0, y0, x1, y1: all(F(5, 2) <= x <= F(7, 2) for x in (x0, x1))
           and all(0 <= y <= 1 for y in (y0, y1)))
seg_mutant('M3_corner_1e-4', lambda *v: all(1 <= x <= 2 for x in v))
out = list(lines)
t = out[-1].split()
assert t[0] == '4'
t[1] = str(int(t[1]) * 9999 // 10000)
out[-1] = ' '.join(t)
out.insert(1, '# mutant M2: Lebesgue square mass x (1 - 1e-4)')
open(os.path.join(here, 'M2_leb_1e-4.txt'), 'w').write('\n'.join(out) + '\n')
