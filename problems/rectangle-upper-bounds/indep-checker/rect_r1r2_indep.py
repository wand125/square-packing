#!/usr/bin/env python3
"""Independent exact structural checker for the rectangle R1/R2 identities.

Only the statement of the checks, ../closed-form/SPEC.md and the family files inform this implementation.
Segments carry one-dimensional density, never atoms at their endpoints.

Why the finite checks extend: subtracting the seven stored periods verifies the
fixed F/T/V decomposition. Reversal and transposition are exact profile identities,
independent of delta and wall length. Corner coordinates and masses are affine;
nonnegative densities and corner containment are checked at both interval ends.
The only varying length is V, with fixed density. Thus the structural identities
hold throughout the interval, not merely at sampled values. The geometric gaps
are affine in the two deltas and increase with each integer side parameter, so
all four endpoint pairs at k=m=7 bound all larger containers. Adding integer wall
periods preserves the checked identities and shifts the windows by integers
(with two parities). The requested sizes exercise both parities and unequal
sides. Endpoint comparisons alone would NOT suffice without these structural
and geometric checks; they do not verify coverage of all unit square poses.
"""
from collections import defaultdict
from fractions import Fraction as Q
from hashlib import sha256
from itertools import product
from pathlib import Path
import json
import sys
import time

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / 'inputs/cf34/interval_0.99_1'
ALPHA = Q(9, 5)
RADIUS = Q(3, 4)
ZERO = Q(0)
checks = []


def check(name, ok, detail=''):
    checks.append(bool(ok))
    print(('PASS' if ok else 'FAIL') + ' ' + name + (': ' + detail if detail else ''))


def segment(x, y, X, Y, density):
    if x != X and y != Y:
        raise ValueError('Non-axis-parallel segment')
    if x == X and y == Y:
        return None
    return (0, y, min(x, X), max(x, X), density) if y == Y else (1, x, min(y, Y), max(y, Y), density)


def rows_to_segments(rows):
    result = []
    for row in rows:
        if len(row) != 5:
            raise ValueError('F/T row must have five entries')
        x, y, X, Y, mass = map(Q, row)
        length = abs(X-x) + abs(Y-y)
        if mass < 0 or (not length and mass):
            raise ValueError('Negative mass or positive point mass')
        if x != X and y != Y:
            raise ValueError('Non-axis-parallel input')
        if length and mass:
            result.append(segment(x, y, X, Y, mass/length))
    return result


def canonical(segments):
    """Sweep each supporting line, add overlaps and merge equal neighbors."""
    events = defaultdict(lambda: defaultdict(Q))
    for s in segments:
        if s is None:
            continue
        axis, c, lo, hi, density = s
        if lo < hi and density:
            events[axis, c][lo] += density
            events[axis, c][hi] -= density
    result = []
    for (axis, c), changes in sorted(events.items()):
        density = ZERO
        previous = None
        pieces = []
        for pos, change in sorted(changes.items()):
            if previous is not None and previous < pos and density:
                if pieces and pieces[-1][3] == previous and pieces[-1][4] == density:
                    old = pieces.pop()
                    pieces.append((axis, c, old[2], pos, density))
                else:
                    pieces.append((axis, c, previous, pos, density))
            density += change
            previous = pos
        if density:
            raise ValueError('Unbalanced density sweep')
        result.extend(pieces)
    return tuple(result)


def transform(segs, fn):
    result = []
    for axis, c, lo, hi, density in segs:
        p, q = ((lo, c), (hi, c)) if axis == 0 else ((c, lo), (c, hi))
        x, y = fn(*p)
        X, Y = fn(*q)
        result.append(segment(x, y, X, Y, density))
    return result


def shift(segs, x=ZERO, y=ZERO):
    return transform(segs, lambda u, v: (u+x, v+y))


def negative(segs):
    return [(axis, c, lo, hi, -d) for axis, c, lo, hi, d in segs]


def mass(segs):
    return sum(((hi-lo)*d for _, _, lo, hi, d in segs), ZERO)


def nonnegative(segs):
    return all(s[4] >= 0 for s in canonical(segs))


def inside(segs, width, height):
    return all(0 <= c <= (height if axis == 0 else width)
               and 0 <= lo < hi <= (width if axis == 0 else height)
               for axis, c, lo, hi, d in canonical(segs) if d)


def restrict(segs, box):
    """Closed box: retain lines ON its boundary; discard only zero lengths."""
    x0, x1, y0, y1 = box
    result = []
    for axis, c, lo, hi, d in segs:
        low, high, c0, c1 = (x0, x1, y0, y1) if axis == 0 else (y0, y1, x0, x1)
        lo, hi = max(lo, low), min(hi, high)
        if c0 <= c <= c1 and lo < hi:
            result.append((axis, c, lo, hi, d))
    return canonical(result)


def area_form(rect, box):
    x0, x1, y0, y1 = rect
    X0, X1, Y0, Y1 = box
    clipped = (max(x0, X0), min(x1, X1), max(y0, Y0), min(y1, Y1))
    return clipped if clipped[0] < clipped[1] and clipped[2] < clipped[3] else ()


def periodic(profile, start, count, transpose=False):
    rows = []
    for n in range(count):
        one = shift(profile, start+n)
        rows.extend(transform(one, lambda x, y: (y, x)) if transpose else one)
    return rows


def main():
    start_time = time.perf_counter()
    print('Independent exact rectangle R1/R2 checker; Fraction arithmetic')
    for filename in ('family.json', 'family_right.json'):
        print('SHA256', str((DATA/filename).relative_to(ROOT)), sha256((DATA/filename).read_bytes()).hexdigest())
    print('SHA256 indep-checker/rect_r1r2_indep.py', sha256(Path(__file__).read_bytes()).hexdigest())
    family = json.loads((DATA/'family.json').read_bytes())
    d0, d1 = Q(family['d0']), Q(family['d1'])
    check('Input interval and standard quadrant', (d0, d1) == (Q(99,100), Q(1)) and Q(family['UA']) == ALPHA and 'U' not in family)
    F, T = (rows_to_segments(family[key]) for key in ('F', 'T'))
    V = [tuple(map(Q, row)) for row in family['V']]
    check('Input F/T axis alignment and nonnegative masses', True)
    check('Input V nonnegative densities and lengths throughout interval', all(rho >= 0 and xl <= 2+d0 for xl,y,rho in V))
    # The half-open period owns its phase-zero line, never its phase-one line.
    extracted = [s for s in T if (s[0] == 0 and 3 <= s[2] < s[3] <= 4)
                 or (s[0] == 1 and 3 <= s[1] < 4)]
    profile = canonical(shift(extracted, -Q(3)))
    terminal = tuple(s for s in profile if s[0] == 1 and s[1] == 0)
    mv = mass(terminal)
    check('Profile mass = 9/5', mass(profile) == ALPHA)
    check('Profile grid and support', inside(profile, Q(1), ALPHA) and all(
        all((5*z).denominator == 1 for z in (c, lo, hi)) and
        ((axis == 0 and Q(1,5) <= c <= ALPHA) or (axis == 1 and 0 <= c < 1))
        for axis,c,lo,hi,d in profile))
    # Reversing [0,1] moves phase 0 to phase 1. Put that line back at phase 0.
    reversed_profile = transform(profile, lambda x,y: (1-x,y))
    reversed_profile = [(ax, ZERO if ax == 1 and c == 1 else c, lo, hi, d)
                        for ax,c,lo,hi,d in reversed_profile]
    check('Profile reversal h[j,p]=h[j,4-p], v[q,i]=v[-q mod 5,i]', canonical(reversed_profile) == profile)
    bottom7 = periodic(profile, Q(2), 7)
    left7 = periodic(profile, Q(2), 7, True)
    fixed = canonical(F + negative(left7))
    translated = canonical(T + negative(bottom7))
    check('F minus seven transposed periods: nonnegative corner', nonnegative(fixed) and inside(fixed, 2+d0, Q(2)))
    check('T minus seven periods: nonnegative seam at x=2', nonnegative(translated) and all(ax == 1 and c == 2 and 0 <= lo < hi <= 2 for ax,c,lo,hi,d in translated))
    check('F reconstruction includes every stored row and phase', canonical(list(fixed)+left7) == canonical(F))
    check('T reconstruction includes every stored row and phase', canonical(list(translated)+bottom7) == canonical(T))
    for n in range(3,9):
        # Away from the seam, compare directly to each JSON period, not a copy.
        tp = [s for s in T if (s[0] == 0 and n <= s[2] < s[3] <= n+1) or (s[0] == 1 and n <= s[1] < n+1)]
        fp = [s for s in F if (s[0] == 1 and n <= s[2] < s[3] <= n+1) or (s[0] == 0 and n <= s[1] < n+1)]
        check(f'JSON bottom/left periods [{n},{n+1})', canonical(shift(tp,-Q(n))) == profile and canonical(transform(shift(fp,y=-Q(n)),lambda x,y:(y,x))) == profile)
    m_fixed_formula = mass([s for s in F if (s[0] == 1 and s[3] <= 2) or (s[0] == 0 and s[1] <= 2)]) + mass([s for s in T if s[0] == 1 and s[1] == 2]) - 2*mv
    check('SPEC fixed corner mass formula including -2*m_v', m_fixed_formula == mass(fixed)+mass(translated))

    def corner(delta):
        return list(fixed) + shift(translated, delta) + [s for xl,y,rho in V if (s := segment(xl,y,2+delta,y,rho)) is not None]

    def saving(delta):
        return Q(99,25) + ALPHA*delta - mass(corner(delta)) - mv

    def side(delta, integer):
        return corner(delta) + periodic(profile, 2+delta, integer-4) + shift(terminal, integer+delta-2)

    def local(delta, width, height):
        # Include the next period even if a phase-zero line lies on the boundary.
        nx = max(0, int(width-(2+delta))+2)
        ny = max(0, int(height-2)+2)
        return corner(delta) + periodic(profile,2+delta,nx) + periodic(profile,Q(2),ny,True)

    for delta in (d0,d1):
        s = saving(delta)
        print(f'S({delta}) = {s}')
        check(f'S({delta}) > 3/4', s > Q(3,4))
        check(f'S({delta}) >= stored guaranteed saving', s >= Q(family['S_d0' if delta == d0 else 'S_d1']))
        check(f'Corner support and nonnegativity delta={delta}', inside(corner(delta),2+delta,Q(2)) and nonnegative(corner(delta)))
        check(f'Corner affine mass formula delta={delta}', mass(corner(delta)) == m_fixed_formula + sum((rho*(2+delta-xl) for xl,y,rho in V),ZERO))
    check('r > sqrt(2)/2 exactly (r^2 > 1/2)', RADIUS > 0 and RADIUS**2 > Q(1,2))
    for da,db in product((d0,d1), repeat=2):
        for label,L,other in (('a',7+da,db),('b',7+db,da)):
            for bound,offset in (('opposite corner / reversed wall end',2+other),('terminal / opposite wall',Q(2)),('Lebesgue upper edge',ALPHA)):
                gap = L-offset-(L/2+RADIUS)
                check(f'Geometry {label}/2+r < {label}-{offset} ({bound}); k=m=7, da={da}, db={db}', gap > 0, f'gap={gap}; increases by 1/2 per integer increment')
    # Closed restriction regression: entire boundary lines survive, point contacts do not.
    boundary = [(1,Q(1),ZERO,Q(2),Q(3)), (0,Q(1),ZERO,Q(2),Q(4))]
    check('Closed-box restriction retains boundary lines', restrict(boundary,(ZERO,Q(1),ZERO,Q(1))) == canonical([(1,Q(1),ZERO,Q(1),Q(3)),(0,Q(1),ZERO,Q(1),Q(4))]))
    check('Closed-box point intersection has zero segment mass', not restrict([(0,ZERO,Q(1),Q(2),Q(1))],(ZERO,Q(1),ZERO,Q(1))))
    check('Canonical overlap addition and merging', canonical([(0,ZERO,ZERO,Q(2),Q(1)),(0,ZERO,Q(1),Q(3),Q(1))]) == ((0,ZERO,ZERO,Q(1),Q(1)),(0,ZERO,Q(1),Q(2),Q(2)),(0,ZERO,Q(2),Q(3),Q(1))))

    sizes = ((7,7),(7,9),(9,7),(8,11),(12,7),(7,13),(8,8),(10,14))
    print('Wall assignment: SW bottom uses delta_a; SW left is sigma(SE right), reversed then transposed with integer phase at y=2.')
    print('SE pullback bottom uses delta_b; SE pullback left is reversed/transposed SW bottom with integer phase at y=2.')
    for (k,m),(da,db) in product(sizes,product((d0,d1),repeat=2)):
        a,b = k+da,m+db
        tag = f'k={k},m={m},da={da},db={db}'
        tau = lambda x,y: (a-y,x)
        sigma = lambda x,y: (a-x,b-y)
        inverse_tau = lambda x,y: (y,a-x)
        sw,se = side(da,k),transform(side(db,m),tau)
        rect = canonical(sw+se+transform(sw+se,sigma))
        u = (ALPHA,a-ALPHA,ALPHA,b-ALPHA)
        total = mass(rect)+(a-2*ALPHA)*(b-2*ALPHA)
        check('R2 total '+tag,total == a*b-2*saving(da)-2*saving(db))
        check('R2 nonnegative '+tag,nonnegative(rect))
        check('R2 support '+tag,inside(rect,a,b) and 0 <= u[0] < u[1] <= a and 0 <= u[2] < u[3] <= b)
        check('R2 sigma invariance '+tag,canonical(transform(rect,sigma)) == rect and (a-u[1],a-u[0],b-u[3],b-u[2]) == u)
        for name,delta,w,h,global_rows,global_u in (
                ('SW',da,a/2+RADIUS,b/2+RADIUS,rect,u),
                ('SE',db,b/2+RADIUS,a/2+RADIUS,transform(rect,inverse_tau),(ALPHA,b-ALPHA,ALPHA,a-ALPHA))):
            box = (ZERO,w,ZERO,h)
            check('R1 closed local '+name+' '+tag,restrict(global_rows,box) == restrict(local(delta,w,h),box) and area_form(global_u,box) == (ALPHA,w,ALPHA,h))
        # Direct wall-only comparisons include each terminal and the near phase-zero line.
        w,h = a/2+RADIUS,b/2+RADIUS
        left_global = transform(transform(periodic(profile,2+db,m-4)+shift(terminal,b-2),tau),sigma)
        check('R1 SW left profile and phase '+tag,restrict(left_global,(ZERO,w,ZERO,h)) == restrict(periodic(profile,Q(2),int(h)+2,True),(ZERO,w,ZERO,h)))
        left_se = transform(periodic(profile,2+da,k-4)+shift(terminal,a-2),inverse_tau)
        check('R1 SE left profile and phase '+tag,restrict(left_se,(ZERO,h,ZERO,w)) == restrict(periodic(profile,Q(2),int(w)+2,True),(ZERO,h,ZERO,w)))
        if k == m and da == db:
            # Independently arrange four rotations; no sigma or rectangle builder.
            square = []
            rotated = side(da,k)
            for _ in range(4):
                square.extend(rotated)
                rotated = transform(rotated,lambda x,y:(a-y,x))
            check('Square independent rho construction '+tag,canonical(square) == rect and u == (ALPHA,a-ALPHA,ALPHA,a-ALPHA))
    print(f'SUMMARY: {sum(checks)}/{len(checks)} checks passed; {len(checks)-sum(checks)} failed')
    print(f'Runtime: {time.perf_counter()-start_time:.3f} seconds')
    return 0 if all(checks) else 1


if __name__ == '__main__':
    try:
        sys.exit(main())
    except Exception as exc:
        print(f'FAIL fatal error: {type(exc).__name__}: {exc}')
        sys.exit(1)
