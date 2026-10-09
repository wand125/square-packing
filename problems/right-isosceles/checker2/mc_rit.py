"""Float Monte Carlo probe (not a proof): minimum capture over random admissible poses in T_L."""
import json, math, sys
import numpy as np
R2 = math.sqrt(2)
def qf(s):
    if 'sqrt2' not in s: return float(eval(s))
    body = s[:s.index('*sqrt2')]; k = max(body.rfind('+'), body.rfind('-'))
    return (eval(body) * R2) if k <= 0 else eval(body[:k]) + eval(body[k:]) * R2
c = json.load(open(sys.argv[1])); L = qf(c['L'])
P = np.array([[qf(p['x']), qf(p['y'])] for p in c['points']]); W = np.array([eval(p['w']) for p in c['points']], float)
rng = np.random.default_rng(int(sys.argv[2]) if len(sys.argv) > 2 else 1)
best = (9, None)
for _ in range(20):
    m = 200000
    t = rng.uniform(0, math.pi / 2, m); cx = rng.uniform(0, L, m); cy = rng.uniform(0, L, m)
    ct, st = np.cos(t), np.sin(t); ok = np.ones(m, bool)
    for sx, sy in ((.5, .5), (.5, -.5), (-.5, .5), (-.5, -.5)):
        vx = cx + ct * sx - st * sy; vy = cy + st * sx + ct * sy
        ok &= (vx >= 0) & (vy >= 0) & (vx + vy <= L)
    cx, cy, ct, st, t = cx[ok], cy[ok], ct[ok], st[ok], t[ok]
    dx = P[None, :, 0] - cx[:, None]; dy = P[None, :, 1] - cy[:, None]
    a = dx * ct[:, None] + dy * st[:, None]; b = -dx * st[:, None] + dy * ct[:, None]
    cap = ((np.abs(a) <= .5) & (np.abs(b) <= .5)).astype(float) @ W
    i = int(np.argmin(cap))
    if cap[i] < best[0]: best = (float(cap[i]), (float(cx[i]), float(cy[i]), float(t[i])))
print(json.dumps({'cert': sys.argv[1].split('/')[-1], 'min_capture': best[0], 'at': best[1]}))
