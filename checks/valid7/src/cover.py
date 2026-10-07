"""Independent reader for mixed cover format v1 (written from FORMAT.md only)."""
from fractions import Fraction as F
from collections import defaultdict
import sys


def tokens(path):
    first = True
    for line in open(path):
        line = line.split('#', 1)[0]
        for t in line.split():
            if first:
                assert t == 'mixed', "not a mixed cover"; first = False; continue
            yield int(t)


def load(path):
    it = tokens(path)
    assert next(it) == 1, "mixed version"
    s = F(next(it), next(it))
    D = next(it); W = next(it)
    pts = [(F(next(it), D), F(next(it), D), F(next(it), W)) for _ in range(next(it))]
    segs = []
    for _ in range(next(it)):
        x0, y0, x1, y1, w = (next(it) for _ in range(5))
        segs.append(((F(x0, D), F(y0, D)), (F(x1, D), F(y1, D)), F(w, W)))
    polys = []
    for _ in range(next(it)):
        k = next(it); w = F(next(it), W)
        vs = [(F(next(it), D), F(next(it), D)) for _ in range(k)]
        polys.append((vs, w))
    assert next(it, None) is None, "trailing data"
    return dict(s=s, D=D, W=W, pts=pts, segs=segs, polys=polys)


def area(vs):
    return sum(vs[i][0] * vs[(i + 1) % len(vs)][1] - vs[(i + 1) % len(vs)][0] * vs[i][1]
               for i in range(len(vs))) / 2


def validate(c):
    s = c['s']
    inside = lambda p: 0 <= p[0] <= s and 0 <= p[1] <= s
    for p in c['pts']:
        assert inside(p) and p[2] >= 0
    for a, b, w in c['segs']:
        assert a != b and inside(a) and inside(b) and w >= 0
    for vs, w in c['polys']:
        assert all(inside(v) for v in vs) and w >= 0 and area(vs) > 0
        n = len(vs)
        for i in range(n):  # strict convexity, CCW
            (ax, ay), (bx, by), (cx, cy) = vs[i], vs[(i + 1) % n], vs[(i + 2) % n]
            assert (bx - ax) * (cy - by) - (by - ay) * (cx - bx) > 0


def total(c):
    return sum(p[2] for p in c['pts']) + sum(w for *_, w in c['segs']) + sum(w for _, w in c['polys'])


def edge_density(c, h):
    """Axis-parallel segments -> {elementary edge of the h-grid: linear density}.  Refuses anything else."""
    dens = defaultdict(F)
    for (x0, y0), (x1, y1), w in c['segs']:
        L = abs(x1 - x0) + abs(y1 - y0)
        assert x0 == x1 or y0 == y1, "non-axis segment"
        if y0 == y1:
            a, b = sorted((x0, x1)); assert (a / h).denominator == 1 == (b / h).denominator == (y0 / h).denominator
            for i in range(int(a / h), int(b / h)):
                dens[('h', i, int(y0 / h))] += w / L
        else:
            a, b = sorted((y0, y1)); assert (a / h).denominator == 1 == (b / h).denominator == (x0 / h).denominator
            for i in range(int(a / h), int(b / h)):
                dens[('v', int(x0 / h), i)] += w / L
    return {k: v for k, v in dens.items() if v}


def d4_maps(n):
    """The 8 symmetries acting on elementary edges of an n x n grid (n cells per side)."""
    def pt(g, x, y):
        for _ in range(g & 3):
            x, y = n - y, x          # rotation by 90 degrees
        if g & 4:
            x = n - x                # reflection
        return x, y
    def edge(g, e):
        o, i, j = e
        a, b = ((i, j), (i + 1, j)) if o == 'h' else ((i, j), (i, j + 1))
        a, b = pt(g, *a), pt(g, *b)
        if a[1] == b[1]:
            return ('h', min(a[0], b[0]), a[1])
        return ('v', a[0], min(a[1], b[1]))
    return edge, pt


if __name__ == '__main__':
    c = load(sys.argv[1]); validate(c)
    T = total(c)
    print(f"s={c['s']} points={len(c['pts'])} segments={len(c['segs'])} polygons={len(c['polys'])}")
    print(f"total = {T} = {float(T):.12f}")
    h = F(1, c['D']); n = int(c['s'] / h)
    dens = edge_density(c, h)
    lines = {(o, j if o == 'h' else i) for (o, i, j) in dens}
    print(f"elementary edges carrying mass: {len(dens)} on {len(lines)} grid lines; "
          f"segment lengths: {sorted({abs(b[0]-a[0])+abs(b[1]-a[1]) for a, b, _ in c['segs']})}")
    edge, pt = d4_maps(n)
    ok = True
    for g in range(8):
        img = {edge(g, e): v for e, v in dens.items()}
        polys = sorted((sorted((pt(g, x / h, y / h)) for x, y in vs), w) for vs, w in c['polys'])
        base = sorted((sorted((x / h, y / h) for x, y in vs), w) for vs, w in c['polys'])
        if img != dens or polys != base:
            ok = False; print("NOT invariant under", g)
    print("D4-invariant (segment measure as edge densities; polygons as vertex sets):", ok)
    for vs, w in c['polys']:
        print(f"polygon {[(str(x), str(y)) for x, y in vs]} mass {w} area {area(vs)} density {w/area(vs)}")
    S2 = c['s'] * c['s']
    print(f"s^2 - total = {S2 - T} = {float(S2 - T):.12f}; D = (s^2 - total)/4 = {(S2 - T) / 4}")
