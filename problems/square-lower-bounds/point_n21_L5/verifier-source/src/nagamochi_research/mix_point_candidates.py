"""Exchange over convex mixtures of fixed point candidates, with exact replay.

The LP only proposes coefficients. Export uses an exact convex combination,
then the fixed-angle separator checks every centre at each requested angle.
No claim about angles between the requested ones is made.
"""
from pathlib import Path
from fractions import Fraction as F
import os
for key in ('OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS', 'MKL_NUM_THREADS'):
    os.environ[key] = '1'
import json, hashlib, argparse
from math import lcm
import numpy as np
from scipy.optimize import linprog
from probe_external_integer_bridge import read
from refit_external_point_weights import exact_hits
from exact_fixed_angle_separator import run as separate


def rational_simplex(values, denominator=10**9):
    nums = [max(0, int(float(v) * denominator)) for v in values]
    total = sum(nums)
    if not total:
        raise ValueError('Empty mixture')
    return [F(n, total) for n in nums]


def mixture_upper_bound(rows, dual_values):
    """Exact finite-pose upper bound for every mixture of these candidates."""
    dual = rational_simplex(dual_values)
    assert len(dual) == len(rows) and rows
    upper = max(sum((q*row[j] for q,row in zip(dual,rows)),F(0))
                for j in range(len(rows[0])))
    return dual, upper


def run(candidates, separation_files, angles, out, rounds=4):
    out.mkdir(exist_ok=False)
    data = [read(p) for p in candidates]
    L, span, _, points = data[0]
    geometry = [(x,y) for x,y,_ in points]
    assert all(l == L and s == span and [(x,y) for x,y,_ in ps] == geometry
               for l,s,w,ps in data)
    weights = [[F(w,W) for x,y,w in ps] for l,s,W,ps in data]
    source_hashes = [hashlib.sha256(p.read_bytes()).hexdigest() for p in candidates]
    poses = set()
    def collect(report):
        assert report['candidate_sha256'] in source_hashes or report['candidate_sha256'] in generated
        for row in report['records']:
            for r in [row] + row.get('extra_witnesses', []):
                poses.add(tuple(F(r['witness'][k]) for k in ('cx','cy','t')))
    generated = []
    for path in separation_files:
        collect(json.loads(path.read_text()))
    rows = {}
    results = []
    for iteration in range(rounds):
        for pose in sorted(poses - rows.keys()):
            hits = np.flatnonzero(exact_hits(points,L,span,pose))
            rows[pose] = [sum((ws[int(i)] for i in hits), F(0)) for ws in weights]
        ordered = sorted(rows)
        A = np.array([[float(v) for v in rows[p]] for p in ordered])
        k = len(candidates)
        sol = linprog(np.r_[np.zeros(k), -1.],
                      A_ub=np.c_[-A, np.ones(len(A))], b_ub=np.zeros(len(A)),
                      A_eq=[np.r_[np.ones(k), 0.]], b_eq=[1.],
                      bounds=[(0,None)]*(k+1), method='highs', options={'threads':1})
        assert sol.success, sol.message
        coefficients = rational_simplex(sol.x[:k])
        dual, upper = mixture_upper_bound([rows[p] for p in ordered], -sol.ineqlin.marginals)
        new = [sum((c*ws[i] for c,ws in zip(coefficients, weights)), F(0))
               for i in range(len(points))]
        W = lcm(*(v.denominator for v in new))
        directory = out / f'round{iteration+1}'
        directory.mkdir()
        candidate = directory / 'candidate.txt'
        candidate.write_text('\n'.join([f'{L.numerator} {L.denominator}', str(int(F(span)/L)),
                                       str(W), str(len(points))] +
                                      [f'{x} {y} {int(w*W)}' for (x,y),w in zip(geometry,new)])+'\n')
        read(candidate)
        sha = hashlib.sha256(candidate.read_bytes()).hexdigest()
        generated.append(sha)
        mass = sum(new, F(0))
        assert mass == sum((c*sum(ws,F(0)) for c,ws in zip(coefficients,weights)),F(0))
        finite_minimum = min(sum((c*v for c,v in zip(coefficients,rows[p])),F(0)) for p in ordered)
        separate(candidate, angles, directory/'fixed-angles.json')
        report = json.loads((directory/'fixed-angles.json').read_text())
        minimum = min(F(row['minimum']) for row in report['records'])
        collect(report)
        result = dict(round=iteration+1, coefficients=list(map(str,coefficients)),
                      candidate_sha256=sha, total_mass=str(mass), finite_rows=len(rows),
                      finite_minimum=str(finite_minimum), fixed_angle_minimum=str(minimum),
                      convex_hull_upper_bound=str(upper),
                      positive_dual_poses=[dict(pose=list(map(str,p)),weight=str(q),
                                               captures=list(map(str,rows[p])))
                                           for p,q in zip(ordered,dual) if q],
                      success_angles=sum(F(r['minimum'])>=1 for r in report['records']),
                      new_poses=len(poses-rows.keys()), general_coverage_verified=False)
        (directory/'result.json').write_text(json.dumps(result,indent=2))
        results.append(result)
        print(result,flush=True)
        if not poses-rows.keys():
            break
    result = dict(sources=[dict(path=str(p),sha256=s) for p,s in zip(candidates,source_hashes)],
                  angles=list(map(str,angles)), rounds=results, general_coverage_verified=False)
    (out/'result.json').write_text(json.dumps(result,indent=2))
    return result


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('config',type=Path)
    p.add_argument('out',type=Path)
    a = p.parse_args(); c = json.loads(a.config.read_text())
    run(list(map(Path,c['candidates'])), list(map(Path,c['separations'])),
        list(map(F,c['angles'])), a.out, c.get('rounds',4))
