"""Exact mass of an axis-parallel closed unit square [x,x+1]x[y,y+1] (sanity tool, theta = 0 only)."""
from fractions import Fraction as F
from cover import load, edge_density


def make(c):
    h = F(1, c['D']); dens = edge_density(c, h)
    (vs, w), = c['polys']
    lx, ly = min(v[0] for v in vs), min(v[1] for v in vs)
    hx, hy = max(v[0] for v in vs), max(v[1] for v in vs)
    dl = w / ((hx - lx) * (hy - ly))
    ov = lambda a, b, c_, d: max(F(0), min(b, d) - max(a, c_))
    def mass(x, y):
        m = dl * ov(x, x + 1, lx, hx) * ov(y, y + 1, ly, hy)
        for (o, i, j), v in dens.items():
            if o == 'h':
                if y <= j * h <= y + 1: m += v * ov(x, x + 1, i * h, (i + 1) * h)
            else:
                if x <= i * h <= x + 1: m += v * ov(y, y + 1, j * h, (j + 1) * h)
        return m
    return mass


if __name__ == '__main__':
    import sys
    m = make(load(sys.argv[1]))
    for t in [F(0), F(1, 7), F(1, 3), F(1), F(5, 2), F(3)]:
        print('wall', t, m(t, F(0)))
    grid = [F(i, 20) for i in range(0, 121)]
    mn = min((m(x, y), x, y) for x in grid for y in grid)
    print('min over 1/20 grid of lower-left corners:', mn[0], float(mn[0]), mn[1:])
