#!/usr/bin/env python3
"""Independent exact checker of Lemmas R1 (localisation) and R2 (total mass) for all 34 interval families of the
rectangle closed form, with the square case and the certified saving line.

Generalised from the published independent checker problems/rectangle-upper-bounds/indep-checker/rect_r1r2_indep.py
(interval 34 only): its segment algebra (canonical, transform, restrict, periodic) and the construction are reused;
the interval bounds, the input paths, the per-interval report, the saving check against intervals.json, the input
binding (sha256) and the negative-control mode are new. Written from the specifications only (closed-form SPEC
§1.3, §2.1, §3; rectangle SPEC §1-§3); the first-system checkers were not read.

Why finitely many (delta, k, m) suffice (as in rect_r1r2_indep.py): subtracting the seven stored periods verifies
the fixed F/T/V decomposition; reversal and transposition are exact profile identities independent of delta and of
the wall length; corner coordinates and masses are affine in delta with a fixed structure on the interval, and
nonnegativity and containment are checked at both ends; the only varying length is the V rows, with fixed density.
The geometric gaps are affine in the two deltas and grow with each integer side parameter, so the four endpoint
pairs at k = m = 7 bound all larger containers. Larger k or m only add integer wall periods, which preserve the
checked identities and shift the windows by integers; the sizes used exercise both parities of k and m and unequal
sides. Endpoint comparisons alone would not suffice without these structural and geometric checks, and none of this
checks coverage of all unit-square poses (that is the leaf replay of the closed form).

usage: python3 rect_r1r2_all.py FAMILIES_DIR INTERVALS_JSON [--only 1,34] [--report report.json] [--no-sha]
  FAMILIES_DIR holds <asset>/family.json for every interval (asset = the intervals.json field without .tar.gz)
  --no-sha: do not require family_sha256 (only for the negative controls, so that the content checks are shown)
"""
from collections import defaultdict
from fractions import Fraction as Q
from hashlib import sha256
from itertools import product
from pathlib import Path
import json
import sys
import time

ALPHA = Q(9, 5)
RADIUS = Q(3, 4)
ZERO = Q(0)
SIZES = ((7, 7), (7, 9), (9, 7), (8, 11), (12, 7), (7, 13), (8, 8), (10, 14))
STANDARD_U = [[ALPHA, ALPHA], [Q(1000), ALPHA], [Q(1000), Q(1000)], [ALPHA, Q(1000)]]


class Checks:
    def __init__(self, verbose):
        self.items = []
        self.verbose = verbose

    def __call__(self, name, ok, detail=''):
        self.items.append((name, bool(ok), detail))
        if self.verbose or not ok:
            print(('  PASS ' if ok else '  FAIL ') + name + (': ' + detail if detail else ''))


def segment(x, y, X, Y, density):
    if x != X and y != Y:
        raise ValueError('non-axis-parallel segment')
    if x == X and y == Y:
        return None
    return (0, y, min(x, X), max(x, X), density) if y == Y else (1, x, min(y, Y), max(y, Y), density)


def rows_to_segments(rows):
    result = []
    for row in rows:
        if len(row) != 5:
            raise ValueError('F/T row must have five entries')
        x, y, X, Y, m = map(Q, row)
        length = abs(X - x) + abs(Y - y)
        if m < 0 or (not length and m):
            raise ValueError('negative mass or positive point mass')
        if x != X and y != Y:
            raise ValueError('non-axis-parallel input')
        if length and m:
            result.append(segment(x, y, X, Y, m / length))
    return result


def canonical(segments):
    """Sweep each supporting line, add overlaps and merge equal neighbours."""
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
            raise ValueError('unbalanced density sweep')
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
    return transform(segs, lambda u, v: (u + x, v + y))


def negative(segs):
    return [(axis, c, lo, hi, -d) for axis, c, lo, hi, d in segs]


def mass(segs):
    return sum(((hi - lo) * d for _, _, lo, hi, d in segs), ZERO)


def nonnegative(segs):
    return all(s[4] >= 0 for s in canonical(segs))


def inside(segs, width, height):
    return all(0 <= c <= (height if axis == 0 else width) and 0 <= lo < hi <= (width if axis == 0 else height)
               for axis, c, lo, hi, d in canonical(segs) if d)


def restrict(segs, box):
    """Closed box: keep lines on its boundary; discard only zero lengths."""
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
        one = shift(profile, start + n)
        rows.extend(transform(one, lambda x, y: (y, x)) if transpose else one)
    return rows


def check_family(family, entry, check):
    d0, d1 = Q(family['d0']), Q(family['d1'])
    check('interval bounds equal intervals.json', (d0, d1) == (Q(entry['d0']), Q(entry['d1'])) and d0 < d1,
          f'[{d0}, {d1}]')
    U = family.get('U')
    check('alpha = 9/5 and the standard Lebesgue quadrant',
          Q(family['UA']) == ALPHA and (U is None or [[Q(x), Q(y)] for x, y in U] == STANDARD_U))
    F, T = (rows_to_segments(family[key]) for key in ('F', 'T'))
    V = [tuple(map(Q, row)) for row in family['V']]
    check('V nonnegative densities, xl <= 2 + d0', all(rho >= 0 and xl <= 2 + d0 for xl, y, rho in V))
    # the half-open period owns its phase-0 line, never its phase-1 line
    extracted = [s for s in T if (s[0] == 0 and 3 <= s[2] < s[3] <= 4) or (s[0] == 1 and 3 <= s[1] < 4)]
    profile = canonical(shift(extracted, -Q(3)))
    terminal = tuple(s for s in profile if s[0] == 1 and s[1] == 0)
    mv = mass(terminal)
    check('profile mass = 9/5', mass(profile) == ALPHA, str(mass(profile)))
    check('profile on the 1/5 grid and support', inside(profile, Q(1), ALPHA) and all(
        all((5 * z).denominator == 1 for z in (c, lo, hi)) and
        ((axis == 0 and Q(1, 5) <= c <= ALPHA) or (axis == 1 and 0 <= c < 1)) for axis, c, lo, hi, d in profile))
    reversed_profile = transform(profile, lambda x, y: (1 - x, y))
    reversed_profile = [(ax, ZERO if ax == 1 and c == 1 else c, lo, hi, d) for ax, c, lo, hi, d in reversed_profile]
    check('profile reversal h[j,p] = h[j,4-p], v[q,i] = v[-q mod 5,i]', canonical(reversed_profile) == profile)
    bottom7 = periodic(profile, Q(2), 7)
    left7 = periodic(profile, Q(2), 7, True)
    fixed = canonical(F + negative(left7))
    translated = canonical(T + negative(bottom7))
    check('F minus seven transposed periods: nonnegative corner', nonnegative(fixed) and inside(fixed, 2 + d0, Q(2)))
    check('T minus seven periods: nonnegative seam at x = 2', nonnegative(translated) and all(
        ax == 1 and c == 2 and 0 <= lo < hi <= 2 for ax, c, lo, hi, d in translated))
    check('F reconstruction', canonical(list(fixed) + left7) == canonical(F))
    check('T reconstruction', canonical(list(translated) + bottom7) == canonical(T))
    for n in range(3, 9):
        tp = [s for s in T if (s[0] == 0 and n <= s[2] < s[3] <= n + 1) or (s[0] == 1 and n <= s[1] < n + 1)]
        fp = [s for s in F if (s[0] == 1 and n <= s[2] < s[3] <= n + 1) or (s[0] == 0 and n <= s[1] < n + 1)]
        check(f'walls: stored bottom/left period [{n},{n + 1}) = profile',
              canonical(shift(tp, -Q(n))) == profile and
              canonical(transform(shift(fp, y=-Q(n)), lambda x, y: (y, x))) == profile)
    m_fixed_formula = (mass([s for s in F if (s[0] == 1 and s[3] <= 2) or (s[0] == 0 and s[1] <= 2)])
                       + mass([s for s in T if s[0] == 1 and s[1] == 2]) - 2 * mv)
    check('fixed corner mass formula with -2 m_v', m_fixed_formula == mass(fixed) + mass(translated))

    def corner(delta):
        return list(fixed) + shift(translated, delta) + [s for xl, y, rho in V if (s := segment(xl, y, 2 + delta, y, rho)) is not None]

    def saving(delta):
        return Q(99, 25) + ALPHA * delta - mass(corner(delta)) - mv

    def side(delta, integer):
        return corner(delta) + periodic(profile, 2 + delta, integer - 4) + shift(terminal, integer + delta - 2)

    def local(delta, width, height):
        nx = max(0, int(width - (2 + delta)) + 2)
        ny = max(0, int(height - 2) + 2)
        return corner(delta) + periodic(profile, 2 + delta, nx) + periodic(profile, Q(2), ny, True)

    la, lb = Q(entry['certified_line']['alpha']), Q(entry['certified_line']['beta'])
    savings = {}
    for delta in (d0, d1):
        s = saving(delta)
        savings[str(delta)] = str(s)
        check(f'saving: S({delta}) >= certified line alpha_J d + beta_J', s >= la * delta + lb,
              f'S - line = {float(s - la * delta - lb):.3e}')
        check(f'corner support and nonnegativity, delta = {delta}', inside(corner(delta), 2 + delta, Q(2)) and nonnegative(corner(delta)))
        check(f'corner mass affine formula, delta = {delta}',
              mass(corner(delta)) == m_fixed_formula + sum((rho * (2 + delta - xl) for xl, y, rho in V), ZERO))
    check('r > sqrt(2)/2 exactly (r^2 > 1/2)', RADIUS > 0 and RADIUS ** 2 > Q(1, 2))
    for da, db in product((d0, d1), repeat=2):
        for label, Lside, other in (('a', 7 + da, db), ('b', 7 + db, da)):
            for bound, offset in (('opposite corner / reversed wall end', 2 + other), ('terminal / opposite wall', Q(2)),
                                  ('Lebesgue upper edge', ALPHA)):
                gap = Lside - offset - (Lside / 2 + RADIUS)
                check(f'geometry {label}/2 + r < {label} - {offset} ({bound}), k = m = 7, da = {da}, db = {db}', gap > 0)
    for (k, m), (da, db) in product(SIZES, product((d0, d1), repeat=2)):
        a, b = k + da, m + db
        tag = f'k={k},m={m},da={da},db={db}'
        tau = lambda x, y: (a - y, x)
        sigma = lambda x, y: (a - x, b - y)
        inverse_tau = lambda x, y: (y, a - x)
        sw, se = side(da, k), transform(side(db, m), tau)
        rect = canonical(sw + se + transform(sw + se, sigma))
        u = (ALPHA, a - ALPHA, ALPHA, b - ALPHA)
        total = mass(rect) + (a - 2 * ALPHA) * (b - 2 * ALPHA)
        check('R2 total = ab - 2S(da) - 2S(db) ' + tag, total == a * b - 2 * saving(da) - 2 * saving(db))
        check('R2 nonnegative ' + tag, nonnegative(rect))
        check('R2 support ' + tag, inside(rect, a, b) and 0 <= u[0] < u[1] <= a and 0 <= u[2] < u[3] <= b)
        check('R2 sigma invariance ' + tag, canonical(transform(rect, sigma)) == rect and (a - u[1], a - u[0], b - u[3], b - u[2]) == u)
        for name, delta, w, h, global_rows, global_u in (
                ('SW', da, a / 2 + RADIUS, b / 2 + RADIUS, rect, u),
                ('SE', db, b / 2 + RADIUS, a / 2 + RADIUS, transform(rect, inverse_tau), (ALPHA, b - ALPHA, ALPHA, a - ALPHA))):
            box = (ZERO, w, ZERO, h)
            check('R1 closed local ' + name + ' ' + tag,
                  restrict(global_rows, box) == restrict(local(delta, w, h), box) and area_form(global_u, box) == (ALPHA, w, ALPHA, h))
        w, h = a / 2 + RADIUS, b / 2 + RADIUS
        left_global = transform(transform(periodic(profile, 2 + db, m - 4) + shift(terminal, b - 2), tau), sigma)
        check('walls: SW left profile and phase ' + tag,
              restrict(left_global, (ZERO, w, ZERO, h)) == restrict(periodic(profile, Q(2), int(h) + 2, True), (ZERO, w, ZERO, h)))
        left_se = transform(periodic(profile, 2 + da, k - 4) + shift(terminal, a - 2), inverse_tau)
        check('walls: SE left profile and phase ' + tag,
              restrict(left_se, (ZERO, h, ZERO, w)) == restrict(periodic(profile, Q(2), int(w) + 2, True), (ZERO, h, ZERO, w)))
        # terminal lines have phase 0: the bottom wall's terminal line sits at x = a - 2 (an integer shift of phase 0)
        check('walls: terminal line at phase 0 ' + tag, all(ax == 1 for ax, *_ in terminal) and
              canonical(shift(terminal, k + da - 2)) == canonical([s for s in side(da, k) if s and s[0] == 1 and s[1] == a - 2]))
        if k == m and da == db:
            square = []
            rotated = side(da, k)
            for _ in range(4):
                square.extend(rotated)
                rotated = transform(rotated, lambda x, y: (a - y, x))
            check('square case: four rotations = rectangle ' + tag, canonical(square) == rect and u == (ALPHA, a - ALPHA, ALPHA, a - ALPHA))
    return savings, mv


def main(argv):
    if len(argv) < 3:
        print(__doc__.strip().splitlines()[-4])
        return 2
    fam_dir, ipath = Path(argv[1]), Path(argv[2])
    opt = lambda k: argv[argv.index(k) + 1] if k in argv else None
    only = {int(x) for x in opt('--only').split(',')} if opt('--only') else None
    no_sha = '--no-sha' in argv
    t0 = time.perf_counter()
    data = json.loads(ipath.read_bytes())
    intervals = data['intervals'] if isinstance(data, dict) else data
    print('Independent exact rectangle R1/R2 checker, all intervals; Fraction arithmetic')
    print('SHA256 rect_r1r2_all.py', sha256(Path(__file__).read_bytes()).hexdigest())
    print('SHA256 intervals.json', sha256(ipath.read_bytes()).hexdigest())
    if len(intervals) != 34 or sorted(e['index'] for e in intervals) != list(range(1, 35)):
        print('FAIL intervals.json does not list the 34 intervals 1..34')
        return 1
    report = {'checker_sha256': sha256(Path(__file__).read_bytes()).hexdigest(),
              'intervals_sha256': sha256(ipath.read_bytes()).hexdigest(), 'no_sha': no_sha, 'intervals': []}
    nfail = 0
    for e in sorted(intervals, key=lambda e: e['index']):
        if only and e['index'] not in only:
            continue
        asset = e['asset'][:-len('.tar.gz')] if e['asset'].endswith('.tar.gz') else e['asset']
        rel = f'{asset}/family.json'
        t1 = time.perf_counter()
        check = Checks(verbose=False)
        raw = (fam_dir / rel).read_bytes()
        fsha = sha256(raw).hexdigest()
        check('input binding: family sha256 = intervals.json family_sha256', no_sha or fsha == e['family_sha256'], fsha[:16])
        try:
            savings, mv = check_family(json.loads(raw), e, check)
        except Exception as exc:
            check('fatal', False, f'{type(exc).__name__}: {exc}')
            savings, mv = {}, None
        ok = all(c[1] for c in check.items)
        nfail += not ok
        dt = time.perf_counter() - t1
        groups = {}
        for name, okc, _ in check.items:
            g = name.split(' ')[0].rstrip(':')
            groups.setdefault(g, [0, 0])
            groups[g][0] += okc
            groups[g][1] += 1
        print(f'interval {e["index"]:2d} [{e["d0"]}, {e["d1"]}] {rel}: {"PASS" if ok else "FAIL"} '
              f'({sum(c[1] for c in check.items)}/{len(check.items)} checks, {dt:.1f} s)')
        report['intervals'].append({'index': e['index'], 'd0': e['d0'], 'd1': e['d1'], 'family': rel, 'family_sha256': fsha,
                                    'ok': ok, 'checks': len(check.items), 'passed': sum(c[1] for c in check.items),
                                    'groups': groups, 'savings': savings, 'm_v': str(mv),
                                    'failed': [[n, d] for n, okc, d in check.items if not okc][:20], 'seconds': round(dt, 2)})
    n = len(report['intervals'])
    report['seconds'] = round(time.perf_counter() - t0, 1)
    print(f'SUMMARY: {n - nfail}/{n} intervals PASS, {nfail} FAIL; runtime {report["seconds"]} s')
    if opt('--report'):
        Path(opt('--report')).write_text(json.dumps(report, indent=1))
    return 0 if nfail == 0 else 1


if __name__ == '__main__':
    sys.exit(main(sys.argv))
