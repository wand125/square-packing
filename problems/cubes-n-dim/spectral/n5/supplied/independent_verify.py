"""Independent exact checker, using Python's standard library only.
Does not import the producer or its spectral evaluator. Certificate floats and
reported margins are neither needed nor trusted. Run: python independent_verify.py [certificate.json]
"""
import json
import sys
import hashlib
from fractions import Fraction as R
from math import isqrt
from pathlib import Path

PRECISION = 128
UNIT = 1 << PRECISION

def enclosure(t):
    if t < 0:
        raise ValueError('Negative square-root argument')
    k = isqrt(t.numerator * UNIT * UNIT // t.denominator)
    low, high = R(k, UNIT), R(k+1, UNIT)
    assert low*low <= t < high*high
    return low, high

def vertex_bound(p, a):
    assert len(p) == 5 and sum(p) == 1
    assert all(0 <= p[i] <= R(3,4) for i in range(5))
    assert all(p[i] >= p[i+1] for i in range(4))
    assert len(a) == 5 and all(len(row) == 5 for row in a)
    assert all(a[i][j] == a[j][i] for i in range(5) for j in range(5))
    error_rows = []
    for i in range(5):
        row_error = R(0)
        for j in range(5):
            cov = (p[i] if i == j else R(0)) - p[i]*p[j]
            square = sum(a[i][k]*a[k][j] for k in range(5))
            row_error += abs(cov-square)
        error_rows.append(row_error)
    residual = max(error_rows)
    trace_lb = max(R(0), sum(a[i][i] for i in range(5))-5*enclosure(residual)[1])
    return enclosure(R(2))[0]*trace_lb - 2*sum(enclosure(t)[1] for t in p)+2

def gap_bound(points):
    bound = R(0)
    for column in zip(*points):
        low, high = min(column), max(column)
        if low == high:
            continue
        a = enclosure(low)[0]
        b = enclosure(high)[1]
        # f(a,b)=(b-a)^2/(2(a+b)) decreases with a and increases with b.
        bound += (b-a)**2/(2*(a+b))
    return bound

def main():
    path = Path(sys.argv[1]) if len(sys.argv)>1 else Path(__file__).with_name('certificate.json')
    raw = path.read_bytes()
    cert = json.loads(raw)
    vertices = [tuple(R(t) for t in p) for p in cert['vertices']]
    matrices = [[[R(t) for t in row] for row in a] for a in cert['witnesses']]
    assert len(vertices) == len(matrices)
    assert len(set(vertices)) == len(vertices)
    bases, cuts = [], []
    for k in range(2,6):
        bases.append((R(1,k),)*k+(R(0),)*(5-k))
        cuts.append((R(3,4),)+(R(1,4*(k-1)),)*(k-1)+(R(0),)*(5-k))
    expected_vertices = [p for pair in zip(bases,cuts) for p in pair]
    assert vertices[:8] == expected_vertices
    # Independently reconstruct pulling triangulation of the truncated simplex.
    roots = [tuple(list(range(2*j,8,2))+list(range(1,2*j+2,2))) for j in range(4)]
    assert [list(s) for s in roots] == cert['initial']
    bounds = [vertex_bound(p,a) for p,a in zip(vertices,matrices)]
    pending = [(s,0) for s in roots]
    leaves = 0
    minimum = None
    depth_seen = 0
    used = set()
    for decision in cert['records']:
        assert pending, 'Extraneous record'
        simplex, depth = pending.pop()
        assert len(set(simplex)) == 5
        used.update(simplex)
        depth_seen = max(depth_seen,depth)
        if decision is None:
            margin = min(bounds[i] for i in simplex)-gap_bound([vertices[i] for i in simplex])
            assert margin > 0, 'Unproved leaf'
            minimum = margin if minimum is None else min(minimum,margin)
            leaves += 1
        else:
            assert len(decision) == 3
            left,right,new = decision
            assert all(type(z) is int for z in decision)
            assert 0 <= left < 5 and 0 <= right < 5 and left != right
            assert 0 <= new < len(vertices)
            midpoint = tuple((a+b)/2 for a,b in zip(vertices[simplex[left]],vertices[simplex[right]]))
            assert vertices[new] == midpoint, 'Incorrect midpoint'
            first,second = list(simplex),list(simplex)
            first[left],second[right] = new,new
            pending.append((tuple(first),depth+1))
            pending.append((tuple(second),depth+1))
    assert not pending, 'Incomplete cover'
    assert len(used) == len(vertices), 'Unused vertices'
    assert len(cert['records']) == 2*leaves-4
    print('INDEPENDENT EXACT VERIFICATION PASSED')
    print('SHA256:',hashlib.sha256(raw).hexdigest())
    print('vertices:',len(vertices),'records:',len(cert['records']),'leaves:',leaves,'maximum depth:',depth_seen)
    print('minimum exact margin:',minimum)
    print('margin exceeds 1/5000000:',minimum > R(1,5000000))

if __name__ == '__main__':
    main()
