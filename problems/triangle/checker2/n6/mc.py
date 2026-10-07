"""Float Monte Carlo sanity probe (not a proof): minimum capture over random admissible, non-exempt poses."""
import json
import math
import sys

import numpy as np

S3 = math.sqrt(3)


def qf(s):
    s = s.replace(' ', '')
    if 'sqrt3' not in s:
        return float(eval(s.replace('/', '/')))
    body = s[:s.index('*sqrt3')]
    k = max(body.rfind('+'), body.rfind('-'))
    if k <= 0:
        return eval(body) * S3
    return eval(body[:k]) + eval(body[k:]) * S3


def main(path, n=2_000_000, seed=1):
    c = json.load(open(path))
    L = qf(c['L'])
    P = np.array([[qf(p['x']), qf(p['y'])] for p in c['points']])
    W = np.array([eval(p['w']) for p in c['points']], dtype=float)
    O = np.array([[qf(p['x']), qf(p['y'])] for p in c.get('obstacle_points', [])]).reshape(-1, 2)
    E = [([qf(v) for v in e['x']], [qf(v) for v in e['y']], [eval(v) for v in e['u']]) for e in c.get('exclusions', [])]
    rng = np.random.default_rng(seed)
    hi = 1 / 7 if c.get('symmetry') == 'D3' else 1.0
    worst = (9, None)
    for _ in range(n // 200_000):
        m = 200_000
        u = rng.uniform(0, hi, m)
        t = 2 * np.arctan(u)
        cx = rng.uniform(0, L, m)
        cy = rng.uniform(0, L * S3 / 2, m)
        ct, st = np.cos(t), np.sin(t)
        ok = np.ones(m, bool)
        for sx, sy in ((.5, .5), (.5, -.5), (-.5, .5), (-.5, -.5)):
            vx = cx + ct * sx - st * sy
            vy = cy + st * sx + ct * sy
            ok &= (vy >= 0) & (S3 * vx - vy >= 0) & (S3 * (L - vx) - vy >= 0)
        cx, cy, ct, st, u = cx[ok], cy[ok], ct[ok], st[ok], u[ok]
        ex = np.zeros(len(cx), bool)
        for (x0, x1), (y0, y1), (u0, u1) in E:
            ex |= (cx >= x0) & (cx <= x1) & (cy >= y0) & (cy <= y1) & (u >= u0) & (u <= u1)

        def inside(Q):
            dx = Q[None, :, 0] - cx[:, None]
            dy = Q[None, :, 1] - cy[:, None]
            a = dx * ct[:, None] + dy * st[:, None]
            b = -dx * st[:, None] + dy * ct[:, None]
            return (np.abs(a) <= .5) & (np.abs(b) <= .5)
        if len(O):
            for k in range(0, len(O), 100):
                ex |= inside(O[k:k + 100]).any(1)
        cap = inside(P).astype(float) @ W
        cap[ex] = 9
        i = int(np.argmin(cap)) if len(cap) else None
        if i is not None and cap[i] < worst[0]:
            worst = (float(cap[i]), [float(cx[i]), float(cy[i]), float(u[i])])
    print(json.dumps({'cert': path, 'samples': n, 'min_capture_nonexempt': worst[0], 'at': worst[1]}))


if __name__ == '__main__':
    main(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 2_000_000)
