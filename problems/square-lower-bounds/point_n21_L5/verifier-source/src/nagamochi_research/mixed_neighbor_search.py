"""Transport failed centres to nearby net angles; exact replay gates every row.

This is a counterexample heuristic, never an angle coverage certificate.
"""
from fractions import Fraction as F
import math
import numpy as np
from scipy.optimize import minimize
from expanded_search_pilot import Geometry, capture
from mixed_density_check import evaluate
from mixed_net_audit import centre_domains, candidate_net


def search(data, model, seeds, max_searches=32):
    L, B = model[:2]
    rects = np.array([[float(F(x)) for x in r['rectangle']] for r in data['rectangles']])
    rw = np.array([float(F(r['mass'])) for r in data['rectangles']])
    points = np.array([[float(F(x)) for x in p['point']] for p in data['points']]).reshape(-1, 2)
    pw = np.array([float(F(p['mass'])) for p in data['points']])
    geo = Geometry(float(L), float(B), rects)
    step,last = candidate_net(data)
    domains = {d['index']: d for d in centre_domains(L, B, step, last)}
    tasks = []; seen = set()
    # Round-robin distances prevent one failed angle consuming the budget.
    for offset in (1, -1, 2, -2, 4, -4, 8, -8):
        for seed in sorted(seeds, key=lambda q: F(q['score'])):
            t = F(seed['t']); x, y = F(seed['cx']), F(seed['cy'])
            j = round(float(t / step))
            if t*t+2*t-1 > 0:
                x, y, t = y, x, (1-t)/(1+t)
            reach = (L-B*(1+2*t-t*t)/(1+t*t))/2
            uv = [(x-L/2)/reach, (y-L/2)/reach]
            target = j+offset
            key = (target, *(round(float(v), 3) for v in uv))
            if target not in domains or key in seen: continue
            seen.add(key); tasks.append((domains[target], uv))
    found = {}; records = []
    for domain, uv in tasks[:max_searches]:
        t = F(domain['t']); high = F(domain['centre_high'])
        if t*t+2*t-1 > 0:
            t = (1-t)/(1+t); uv = uv[::-1]
        reach = (L-B*(1+2*t-t*t)/(1+t*t))/2
        limit = (high-L/2)/reach
        theta = min(1., 2*math.atan(float(t))/(math.pi/4))
        def objective(z):
            pose = np.array([[z[0], z[1], theta]])
            return float((geo.matrix(pose)@rw + capture(pose, float(L), float(B), points, shrink=0)@pw)[0])
        z = np.clip(np.array(uv, dtype=float), 0, float(limit))
        fit = minimize(objective, z, method='Nelder-Mead', bounds=[(0, float(limit))]*2,
                       options={'maxiter': 160, 'xatol': 1e-9, 'fatol': 1e-10})
        accepted = 0
        for point in (z, fit.x):
            u, v = [min(limit, max(F(0), F(float(q)).limit_denominator(10**10))) for q in point]
            w = evaluate(model, L/2+u*reach, L/2+v*reach, t)
            if F(w['score']) < 1:
                w['origin'] = 'neighbor-angle-search:'+str(domain['index'])
                w['normalized_pose'] = [float(u), float(v), theta]
                found[tuple(w[k] for k in ('cx', 'cy', 't'))] = w
                accepted += 1
        records.append(dict(index=domain['index'], numerical_min=float(fit.fun), exact_deficits=accepted))
    return list(found.values()), records
