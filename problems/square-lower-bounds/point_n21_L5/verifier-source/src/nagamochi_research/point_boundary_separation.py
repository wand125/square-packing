"""Finite edge-crossing probe; exact witnesses, never a complete separator."""
import argparse
import hashlib
import json
from fractions import Fraction as F
from pathlib import Path


def boundary_poses(seed, point, L, B, radius=F(3, 100), eps=F(1, 10**7)):
    """Translate along edge normals to both sides of a point tangency."""
    x, y, t = map(F, seed)
    px, py = map(F, point)
    c, s = (1-t*t)/(1+t*t), 2*t/(1+t*t)
    h = (c+abs(s))/2
    for nx, ny in ((c, s), (-s, c)):
        distance = (px-x)*nx+(py-y)*ny
        for sign in (-1, 1):
            delta = distance-sign*B/2
            if abs(delta) > radius:
                continue
            for offset in (-eps, eps):
                shift = delta+offset
                pose = (x+shift*nx, y+shift*ny, t)
                if all(h <= z <= L-h for z in pose[:2]):
                    yield pose


def run(prior, out):
    from repair_lemma_measure import np, expand, evaluate, coefficients, expand_primitives
    out.mkdir(parents=True, exist_ok=False)
    candidate = prior/'candidate.json'
    data = json.loads(candidate.read_text()); model = expand(data)
    L, B = model[:2]
    z = np.load(prior/'state.npz')
    primitives = json.loads(str(z['primitives_json']))
    ex = expand_primitives(primitives, L)
    result = json.loads((prior/'results.json').read_text())
    seeds = [tuple(F(row[k]) for k in ('cx','cy','t'))
             for row in result['local_witnesses']+result['exact_held_checks']]
    points = [tuple(map(F, row['point'])) for row in data['points'] if F(row['mass']) > 0]
    probes = set(seeds)
    for seed in seeds:
        for point in points:
            for eps in (F(1,10**7), F(1,10**5)):
                probes.update(boundary_poses(seed, point, L, B, eps=eps))
    probes = sorted(probes)
    values = coefficients(probes, B, ex, L) @ z['weights']
    checks = []
    for i in np.argsort(values)[:64]:
        row = evaluate(model, *probes[int(i)])
        row['numeric_score'] = float(values[i]); checks.append(row)
    # Selection is numerical; every reported witness is evaluated exactly.
    report = dict(status='FINITE_POINT_BOUNDARY_PROBE',
                  candidate_sha256=hashlib.sha256(candidate.read_bytes()).hexdigest(),
                  seeds=len(seeds), point_atoms=len(points), probes=len(probes),
                  radius='3/100', epsilons=['1/10000000','1/100000'],
                  source_local_minimum=result['local_minimum'],
                  numeric_minimum=float(min(values)),
                  exact_minimum=str(min(F(row['score']) for row in checks)),
                  max_checked_numeric_error=max(abs(float(F(row['score']))-row['numeric_score']) for row in checks),
                  local_witnesses=checks, general_packing_exclusion=False)
    (out/'results.json').write_text(json.dumps(report, indent=2))
    print({k:v for k,v in report.items() if k!='local_witnesses'}, flush=True)


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('prior', type=Path); p.add_argument('out', type=Path)
    a = p.parse_args(); run(a.prior, a.out)
