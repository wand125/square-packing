"""Exact dual bound for free nonnegative weights on a fixed D4 point support.

Recompute all positive-dual rows by rational polygon geometry. The bound is
support-specific and does not exclude general square packings.
"""
import os
for key in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS'):
    os.environ[key] = '1'
import argparse
import hashlib
import json
from fractions import Fraction as F
from math import floor, ceil
from pathlib import Path
import numpy as np
from scipy.optimize import linprog
from scipy.sparse import csr_matrix
from probe_external_integer_bridge import read
from score import square, contains


def run(directory, out):
    assert not out.exists()
    candidate = directory / 'candidate.txt'
    report = json.loads((directory / 'result.json').read_text())
    if report.get('proof_rows'):
        raise ValueError('This audit does not yet include PL42 region rows; use a proof-aware audit')
    assert hashlib.sha256(candidate.read_bytes()).hexdigest() == report['sha256']
    L, span, W, pts = read(candidate)
    groups = {}
    for i, (x, y, w) in enumerate(pts):
        groups.setdefault(tuple(sorted((min(x, span-x), min(y, span-y)))), []).append(i)
    orbits = list(groups.values())
    sizes = np.array([len(o) for o in orbits])
    ids = np.empty(len(pts), dtype=int)
    for j, orbit in enumerate(orbits):
        ids[orbit] = j
    state = np.load(directory / 'incidence.npz')
    counts = state['counts']
    assert np.array_equal(ids, state['orbit_ids'])
    assert np.array_equal(sizes, state['sizes'])
    poses = json.loads((directory / 'poses.json').read_text())
    assert counts.shape == (len(poses), len(orbits))
    assert np.all(counts >= 0) and np.all(counts <= sizes)
    sol = linprog(np.ones(len(orbits)), A_ub=-csr_matrix(counts/sizes),
                  b_ub=-np.ones(len(poses)), bounds=(0, None),
                  method='highs', options={'threads': 1})
    assert sol.success, sol.message
    denominator = 10**12
    nums = [ceil(max(0, float(z))*denominator/int(k))
            for z, k in zip(sol.x, sizes)]
    def finite_minimum(weights):
        return min(sum(int(c)*w for c, w in zip(row, weights)) for row in counts)
    minimum = finite_minimum(nums)
    assert minimum > 0
    if minimum < denominator:
        nums = [(w*denominator+minimum-1)//minimum for w in nums]
    minimum = finite_minimum(nums)
    assert minimum >= denominator
    upper = F(sum(w*int(k) for w, k in zip(nums, sizes)), denominator)
    dual = [F(floor(max(0, -float(v))*10**9), 10**9)
            for v in sol.ineqlin.marginals]
    active = [(i, y) for i, y in enumerate(dual) if y]
    loads = [F(0) for o in orbits]
    exact_rows = []
    for i, y in active:
        cx, cy, t = map(F, poses[i])
        poly = square(cx, cy, F(1), t)
        assert all(0 <= x <= L and 0 <= z <= L for x, z in poly)
        hits = [contains(poly, (F(x)*L/span, F(z)*L/span)) for x, z, w in pts]
        row = [sum(hits[k] for k in orbit) for orbit in orbits]
        assert row == list(map(int, counts[i]))
        exact_rows.append(dict(pose=poses[i], multiplier=str(y), counts=row))
        for j, n in enumerate(row):
            loads[j] += y*F(n, int(sizes[j]))
    scale = max([F(1)] + loads)
    lower = sum(dual, F(0))/scale
    data = dict(status='EXACT_FREE_WEIGHT_FIXED_SUPPORT_DUAL',
                candidate_sha256=report['sha256'], L=str(L),
                numerical_minimum_mass=float(sol.fun),
                lower_at_capture_one=str(lower),
                lower_at_training_target=str(lower*F(report['capture_target'])),
                finite_upper_at_capture_one=str(upper),
                finite_upper_at_training_target=str(upper*F(report['capture_target'])),
                primal_per_point_weights=[str(F(w, denominator)) for w in nums],
                primal_finite_minimum=str(F(minimum, denominator)),
                primal_geometry_all_rows_independently_replayed=False,
                scale=str(scale), maximum_scaled_load=str(max(loads)/scale),
                orbits=len(orbits), training_rows=len(poses),
                positive_dual_rows=len(active), rows=exact_rows,
                all_positive_dual_geometry_replayed=True,
                general_packing_exclusion=False,
                scope='Nonnegative weights may increase or decrease on this fixed D4 support.')
    out.write_text(json.dumps(data, indent=2))
    print({k: v for k, v in data.items() if k not in ('rows', 'primal_per_point_weights')}, flush=True)


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('directory', type=Path)
    p.add_argument('out', type=Path)
    a = p.parse_args()
    run(a.directory, a.out)
