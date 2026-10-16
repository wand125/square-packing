#!/usr/bin/env python3
"""Independent exact rectangle-family checker; Python standard library only.

Only the statement of the checks and the input files with their documentation informed this code.
Line measures have no atoms at segment endpoints. Window closure matters for
whole perpendicular lines and point masses, but not for longitudinal endpoints
or area boundaries. All geometric and mass arithmetic uses Fraction.
"""
from collections import defaultdict
from fractions import Fraction as F
from pathlib import Path
import hashlib
import re
import sys
import time

ROOT = Path(__file__).resolve().parent.parent
A0 = F(14, 5)
SIZES = [(8,8), (8,9), (9,8), (9,9), (8,10), (10,8), (8,13),
         (13,8), (9,12), (10,11), (11,14), (12,15), (15,8),
         (14,14), (8,20), (20,8), (17,19)]
HASHES = {
    'K4_k008_family.txt': 'a66668d9d414ad1cf78b19826ce592c540c9033a0234a06b207eb776b3e8ff0f',
    'K4_k008_box9.txt': '4151d7c4059d5dcf56130c9373e6b5b60635e1a4250f46562d7ecc4d64a27801',
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def canonical(segments, points, rectangle):
    """Sum overlapping line densities by endpoint sweep, then merge equal pieces.

    Segments are (axis, fixed_coordinate, start, end, density), axis 0 for
    horizontal and 1 for vertical. The sole area component is a rectangle
    (xmin, xmax, ymin, ymax, density); parsers reject other area geometry.
    """
    events = defaultdict(lambda: defaultdict(F))
    for axis, c, lo, hi, density in segments:
        require(lo < hi, 'Degenerate segment')
        events[axis, c][lo] += density
        events[axis, c][hi] -= density
    lines = []
    for (axis, c), ev in sorted(events.items()):
        pieces = []
        density = F(0)
        previous = None
        for x, delta in sorted(ev.items()):
            if previous is not None and previous < x and density:
                if pieces and pieces[-1][1] == previous and pieces[-1][2] == density:
                    pieces[-1] = (pieces[-1][0], x, density)
                else:
                    pieces.append((previous, x, density))
            density += delta
            previous = x
        require(density == 0, 'Unbalanced density sweep')
        if pieces:
            lines.append((axis, c, tuple(pieces)))
    atoms = defaultdict(F)
    for x, y, mass in points:
        atoms[x, y] += mass
    return (tuple(lines), tuple((x, y, m) for (x, y), m in sorted(atoms.items()) if m), rectangle)


def read_family(path):
    content = path.read_text()
    match = re.search(r'^# D = ([\d/]+)', content, re.M)
    require(match is not None, 'Missing family deficit')
    require('R = 3, w = 3' in content and 'a = 14/5' in content,
            'Unsupported family geometry')
    profile, corner = [], []
    for line in content.splitlines():
        row = line.split('#', 1)[0].split()
        if not row:
            continue
        require(len(row) == 5 and row[0] in ('h', 'v', 'H', 'V'),
                'Unknown family record')
        tag = row[0]
        c, lo, hi, mass = map(F, row[1:])
        require(lo < hi, 'Invalid family segment')
        axis = 0 if tag.lower() == 'h' else 1
        if tag.islower():
            require((0 <= lo < hi <= 1 and 0 <= c <= 3) if axis == 0
                    else (0 <= c < 1 and 0 <= lo < hi <= 3),
                    'Profile outside its specified period/band')
        else:
            require(0 <= c <= 3 and 0 <= lo < hi <= 3, 'Corner outside module')
        (profile if tag.islower() else corner).append((axis, c, lo, hi, mass/(hi-lo)))
    require(profile and corner, 'Empty family')
    return profile, corner, F(match[1])


def assemble(width, height, profile, corner):
    """Closed wall restriction [3,L-3] of a period-one profile.

    The area parts mentioned for the corner and profile, together with the
    central area, are exactly one density-one rectangle; never add them twice.
    """
    segments = []
    def add(segment, swap=False, rx=False, ry=False):
        axis, c, lo, hi, density = segment
        if swap:
            axis = 1-axis
        fixed_limit = height if axis == 0 else width
        varying_limit = width if axis == 0 else height
        if (ry if axis == 0 else rx):
            c = fixed_limit-c
        if (rx if axis == 0 else ry):
            lo, hi = varying_limit-hi, varying_limit-lo
        segments.append((axis, c, lo, hi, density))
    for segment in corner:
        for rx in (False, True):
            for ry in (False, True):
                add(segment, rx=rx, ry=ry)
    for length, swap in ((width, False), (height, True)):
        for j in range(3, length-2):
            for axis, c, lo, hi, density in profile:
                if axis == 0:
                    if j == length-3:
                        continue
                    segment = (axis, c, j+lo, j+hi, density)
                else:
                    if j+c > length-3:
                        continue
                    segment = (axis, j+c, lo, hi, density)
                add(segment, swap=swap)
                add(segment, swap=swap, rx=swap, ry=not swap)
    return canonical(segments, [], (A0, width-A0, A0, height-A0, F(1)))


def read_box(path):
    words = iter(' '.join(line.split('#', 1)[0] for line in path.read_text().splitlines()).split())
    def integer():
        return int(next(words))
    require(next(words) == 'mixed' and integer() == 1, 'Unsupported mixed format')
    side = F(integer(), integer())
    require(side == 9, 'Expected box side nine')
    coord_den, mass_den = integer(), integer()
    require(coord_den > 0 and mass_den > 0, 'Invalid denominators')
    def coord():
        value = F(integer(), coord_den)
        require(0 <= value <= side, 'Coordinate outside box')
        return value
    def mass():
        value = F(integer(), mass_den)
        require(value >= 0, 'Negative box mass')
        return value
    points = [(coord(), coord(), mass()) for _ in range(integer())]
    segments = []
    for _ in range(integer()):
        x0, y0, x1, y1, m = coord(), coord(), coord(), coord(), mass()
        require((x0 == x1) != (y0 == y1), 'Non-axis-parallel or degenerate segment')
        axis, c, lo, hi = (0, y0, min(x0,x1), max(x0,x1)) if y0 == y1 else (1, x0, min(y0,y1), max(y0,y1))
        segments.append((axis, c, lo, hi, m/(hi-lo)))
    require(integer() == 1, 'Expected exactly one area rectangle')
    require(integer() == 4, 'Expected quadrilateral')
    m = mass()
    vertices = [(coord(), coord()) for _ in range(4)]
    xs, ys = sorted(set(x for x,y in vertices)), sorted(set(y for x,y in vertices))
    require(len(xs) == len(ys) == 2 and set(vertices) == {(x,y) for x in xs for y in ys},
            'Area component is not a rectangle')
    require(all(vertices[i][0] == vertices[(i+1)%4][0] or vertices[i][1] == vertices[(i+1)%4][1]
                for i in range(4)), 'Crossed rectangle polygon')
    require(next(words, None) is None, 'Trailing mixed data')
    return canonical(segments, points, (xs[0], xs[1], ys[0], ys[1], m/((xs[1]-xs[0])*(ys[1]-ys[0]))))


def restrict_axis(measure, axis, lo, hi, closed, shift=F(0)):
    """Restrict then translate one coordinate; preserve canonical line form."""
    def contains(x):
        return lo <= x and (x < hi or (closed and x == hi))
    lines, points, rect = measure
    out = []
    for orientation, c, pieces in lines:
        if orientation != axis:  # fixed coordinate is the restricted coordinate
            if contains(c):
                out.append((orientation, c+shift, pieces))
        else:
            clipped = tuple((max(a,lo)+shift, min(b,hi)+shift, d)
                            for a,b,d in pieces if a < hi and b > lo)
            if clipped:
                out.append((orientation, c, clipped))
    atoms = tuple((x+(shift if axis == 0 else 0), y+(shift if axis == 1 else 0), m)
                  for x,y,m in points if contains(x if axis == 0 else y))
    if rect:
        r = list(rect)
        i = 2*axis
        r[i], r[i+1] = max(r[i],lo), min(r[i+1],hi)
        if r[i] >= r[i+1]:
            rect = None
        else:
            r[i] += shift
            r[i+1] += shift
            rect = tuple(r)
    return tuple(out), atoms, rect


def total(measure):
    lines, points, rect = measure
    answer = sum(((hi-lo)*d for _,_,pieces in lines for lo,hi,d in pieces), F(0))
    answer += sum((m for _,_,m in points), F(0))
    if rect:
        x0,x1,y0,y1,d = rect
        answer += (x1-x0)*(y1-y0)*d
    return answer


def shift_for(length, start):
    if start <= 3:
        return 0
    if start > length-5:
        return 9-length
    # Middle starts map into (3,4], never onto the corner seam x=3.
    return 4 - ((start.numerator + start.denominator - 1)//start.denominator)


def windows(length):
    return [(F(i,5), i == 5*(length-2), shift_for(length,F(i,5)))
            for i in range(5*(length-2)+1)]


def localisation(measure, box, width, height, cache):
    count = 0
    for x, xc, s in windows(width):
        require(isinstance(s,int) and 0 <= x+s and x+2+s <= 9, 'Bad x shift')
        source_x = restrict_axis(measure, 0, x, x+2, xc, F(s))
        target_x = restrict_axis(box, 0, x+s, x+2+s, xc)
        for y, yc, t in windows(height):
            require(isinstance(t,int) and 0 <= y+t and y+2+t <= 9, 'Bad y shift')
            source = restrict_axis(source_x, 1, y, y+2, yc, F(t))
            key = (x+s,xc,y+t,yc)
            if key not in cache:
                cache[key] = restrict_axis(target_x, 1, y+t, y+2+t, yc)
            require(source == cache[key],
                    f'Window mismatch: {width}x{height}, ({x},{y}), shifts ({s},{t}), closed ({xc},{yc})')
            count += 1
    return count


# Scope: this script tests the window agreement for the listed sizes only. Windows fall into three kinds per
# axis: starts x<=3 (left end), x>L-5 (right end, including the closed last window) and 3<x<=L-5 (middle,
# moved into (3,4] in the 9-box, avoiding both lines 3 and 6 that carry corner mass). At 9x9 every shift is 0;
# the shift rule is exercised by the sizes with a side >= 10. The extension to all A, B >= 8 is the proof of
# Lemma R6 in ../README.md, not a consequence of these tests.
# A square's bounding width <=sqrt(2)<9/5, so rounding its minimum down by <1/5 puts its maximum strictly below
# the open end two units away; capping at L-2 uses the closed last window. Hence equal restrictions to the
# window give equal mass for the closed square, at any angle.


def main():
    started = time.perf_counter()
    outcomes = []
    def report(label, ok, detail):
        outcomes.append(ok)
        print(f'{"PASS" if ok else "FAIL"} {label}: {detail}', flush=True)
    for name, expected in HASHES.items():
        actual = hashlib.sha256((ROOT/'inputs'/name).read_bytes()).hexdigest()
        report('5 input SHA256', actual == expected, f'{name} {actual}')
    print('SHA256 script ' + hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), flush=True)
    profile, corner, deficit = read_family(ROOT/'inputs/K4_k008_family.txt')
    box = read_box(ROOT/'inputs/K4_k008_box9.txt')
    report('1 exact box equality', assemble(9,9,profile,corner) == box,
           'Canonical summed/merged line densities, point masses, and area rectangle')
    report('2 nonnegative family', all(p[-1] >= 0 for p in profile+corner),
           f'{len(profile)} profile pieces, {len(corner)} corner pieces; area density 1')
    p = sum(((hi-lo)*d for _,_,lo,hi,d in profile),F(0))
    c = sum(((hi-lo)*d for _,_,lo,hi,d in corner),F(0))
    endpoint = sum(((hi-lo)*d for axis,pos,lo,hi,d in profile if axis == 1 and pos == 0),F(0))
    # M = 4C + 2(A+B-12)P + 4E + (A-2a)(B-2a).
    # Verify its linear and constant coefficients, so this is an all-size check.
    mass_ok = 2*p == 2*A0 and 4*c-24*p+4*endpoint+4*A0*A0 == -4*deficit and deficit > 1
    report('3 all-size mass identity', mass_ok,
           f'P={p}, C={c}, E={endpoint}, D={deficit}; M=AB-4D < AB-4')
    print('Shift rule: s_L(x)=0 if x<=3; 9-L if x>L-5; 4-ceil(x) otherwise.', flush=True)
    cache = {}
    all_windows = 0
    for width,height in SIZES:
        measure = assemble(width,height,profile,corner)
        m = total(measure)
        report(f'3 mass {width}x{height}', m == width*height-4*deficit and m < width*height-4,
               f'{m}')
        try:
            n = localisation(measure,box,width,height,cache)
            all_windows += n
            report(f'4 localisation {width}x{height}', True, f'{n} window pairs')
        except ValueError as exc:
            report(f'4 localisation {width}x{height}', False, str(exc))
    report('5 script SHA256', True, 'Script digest printed above (self-hash is not embedded)')
    print(f'Checked {all_windows} window pairs; {len(cache)} distinct target restrictions.', flush=True)
    print(f'Runtime: {time.perf_counter()-started:.3f} seconds', flush=True)
    ok = all(outcomes)
    print('PASS ALL CHECKS' if ok else 'FAIL ONE OR MORE CHECKS', flush=True)
    return 0 if ok else 1


if __name__ == '__main__':
    try:
        sys.exit(main())
    except Exception as exc:
        print(f'FAIL fatal: {type(exc).__name__}: {exc}', flush=True)
        sys.exit(1)
