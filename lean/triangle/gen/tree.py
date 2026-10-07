#!/usr/bin/env python3
"""Build a pose-space tree with Farkas-Bernstein leaves (generator; not trusted).

Node kinds (serialised to JSON, then to Lean):
  {"split": "x"|"y"|"u", "at": Q3, "lo": node, "hi": node}
  {"split": "lin", "form": affine form, "pos": node, "neg": node}   branches form >= 0 / -form >= 0
  {"leaf": "empty", "cert": [...]}
  {"leaf": "cover", "points": [i...], "certs": {i: [cert_k for k in 0..3]}}
"""
import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np

from cert import (Q3, ZERO, ONE, S3, HALF, mpq, aff, aneg, admissibility, box_forms, capture_target,
                  solve, check_identity, aeval_f)

MAX_LIN = 4

BREAKS = [Q3(0), Q3(2, -1), Q3(0, mpq(1, 3)), Q3(1)]   # u at theta = 0, pi/6, pi/3, pi/2


def load(path):
    c = json.loads(Path(path).read_text())
    L = Q3.parse(c['L'])
    pts = [((Q3.parse(p['x']), Q3.parse(p['y'])), mpq(p['w'])) for p in c['points']]
    return L, pts


def poly_clip(poly, a, b, c):
    """Clip a float polygon by a x + b y + c >= 0."""
    out = []
    n = len(poly)
    for i in range(n):
        P, Qp = poly[i], poly[(i + 1) % n]
        fp, fq = a * P[0] + b * P[1] + c, a * Qp[0] + b * Qp[1] + c
        if fp >= 0:
            out.append(P)
        if (fp >= 0) != (fq >= 0):
            t = fp / (fp - fq)
            out.append((P[0] + t * (Qp[0] - P[0]), P[1] + t * (Qp[1] - P[1])))
    return out


def samples(forms_f, box, u0, u1, extra=()):
    """Float sample poses: vertices, edge midpoints and centroid of the admissible polygon."""
    x0, x1, y0, y1 = box
    out = []
    for u in np.linspace(u0, u1, 7):
        poly = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
        for f in list(forms_f) + list(extra):
            a, b, c = f(u)
            poly = poly_clip(poly, a, b, c)
            if not poly:
                break
        if not poly:
            continue
        cx = sum(p[0] for p in poly) / len(poly)
        cy = sum(p[1] for p in poly) / len(poly)
        pts = list(poly) + [((poly[i][0] + poly[(i + 1) % len(poly)][0]) / 2,
                             (poly[i][1] + poly[(i + 1) % len(poly)][1]) / 2) for i in range(len(poly))]
        pts += [(cx, cy)] + [((p[0] + cx) / 2, (p[1] + cy) / 2) for p in poly]
        out += [(x, y, u) for x, y in pts]
    return out


def ffun(form):
    return lambda u: (np_eval(form['x'], u), np_eval(form['y'], u), np_eval(form['1'], u))


def np_eval(p, u):
    r = 0.0
    for c in reversed(p):
        r = r * u + float(c)
    return r


class Builder:
    def __init__(self, L, pts, max_depth=40, uscale=4.0):
        self.L, self.pts = L, pts
        self.adm = admissibility(L)
        self.adm_f = [ffun(f) for _, f in self.adm]
        self.targets = [[capture_target(p, k) for k in range(4)] for p, _ in pts]
        self.targets_f = [[ffun(t) for t in ts] for ts in self.targets]
        self.max_depth, self.uscale = max_depth, uscale
        self.stats = dict(leaves=0, empty=0, cover=0, failed=0, lps=0)

    def captured_f(self, i, x, y, u, tol=-1e-12):
        return all(a * x + b * y + c >= tol for a, b, c in (f(u) for f in self.targets_f[i]))

    def build(self, box, U0, U1, lin=(), depth=0):
        x0, x1, y0, y1 = box
        forms = self.adm + box_forms(*box) + [(('lin', k), f) for k, f in enumerate(lin)]
        fb = tuple(float(v) for v in box)
        S = samples(self.adm_f, fb, float(U0), float(U1), [ffun(f) for f in lin])
        if not S:
            self.stats['lps'] += 1
            c = solve(aff([Q3(-1)]), forms, U0, U1)
            if c is not None:
                self.stats['leaves'] += 1; self.stats['empty'] += 1
                return {'leaf': 'empty', 'cert': c}
            # A very thin region (e.g. between two nearly coincident split lines, or on a line
            # f = 0) may have no float sample.  Choose candidates from samples taken without the
            # split forms; the split forms stay in the LP as hypotheses.
            if lin:
                S = samples(self.adm_f, fb, float(U0), float(U1))
        if S:
            common = [i for i in range(len(self.pts)) if all(self.captured_f(i, *s) for s in S)]
            common.sort(key=lambda i: -self.pts[i][1])
            if sum(self.pts[i][1] for i in common) >= 1:
                # try the candidates one by one; keep those whose four certificates exist
                chosen, certs, wsum = [], {}, mpq(0)
                for i in common:
                    if wsum >= 1:
                        break
                    cs = []
                    for k in range(4):
                        self.stats['lps'] += 1
                        c = solve(self.targets[i][k], forms, U0, U1)
                        if c is None:
                            break
                        cs.append(c)
                    if len(cs) == 4:
                        chosen.append(i); certs[i] = cs; wsum += self.pts[i][1]
                if wsum >= 1:
                    self.stats['leaves'] += 1; self.stats['cover'] += 1
                    return {'leaf': 'cover', 'points': chosen, 'certs': certs}
        # Union cover: every sample is covered but no common set is.  Split by a capture side.
        if S and len(lin) < MAX_LIN:
            wt = [sum(self.pts[i][1] for i in range(len(self.pts)) if self.captured_f(i, *s)) for s in S]
            if min(wt) >= 1:
                split = self.lin_split(S, lin)
                if split is not None:
                    f = split
                    return {'split': 'lin', 'form': f,
                            'pos': self.build(box, U0, U1, lin + (f,), depth + 1),
                            'neg': self.build(box, U0, U1, lin + (aneg(f),), depth + 1)}
        if depth >= self.max_depth:
            self.stats['failed'] += 1
            return {'leaf': 'FAILED', 'box': [str(v) for v in box], 'u': [str(U0), str(U1)]}
        wx, wy, wu = float(x1 - x0), float(y1 - y0), float(U1 - U0) * self.uscale
        if wu >= max(wx, wy):
            m = (U0 + U1) * HALF
            return {'split': 'u', 'at': m, 'lo': self.build(box, U0, m, lin, depth + 1),
                    'hi': self.build(box, m, U1, lin, depth + 1)}
        if wx >= wy:
            m = (x0 + x1) * HALF
            return {'split': 'x', 'at': m, 'lo': self.build((x0, m, y0, y1), U0, U1, lin, depth + 1),
                    'hi': self.build((m, x1, y0, y1), U0, U1, lin, depth + 1)}
        m = (y0 + y1) * HALF
        return {'split': 'y', 'at': m, 'lo': self.build((x0, x1, y0, m), U0, U1, lin, depth + 1),
                'hi': self.build((x0, x1, m, y1), U0, U1, lin, depth + 1)}


def _cover_ok(self, S):
    common = [i for i in range(len(self.pts)) if all(self.captured_f(i, *s) for s in S)]
    return sum(self.pts[i][1] for i in common) >= 1


def _same_form(f, g):
    return all(f[k] == g[k] for k in ('1', 'x', 'y'))


def _lin_split(self, S, lin=()):
    for i in range(len(self.pts)):
        for k in range(4):
            f = self.targets_f[i][k]
            pos = [s for s in S if (lambda a, b, c: a * s[0] + b * s[1] + c)(*f(s[2])) >= -1e-12]
            neg = [s for s in S if (lambda a, b, c: a * s[0] + b * s[1] + c)(*f(s[2])) <= 1e-12]
            if pos and neg and len(pos) < len(S) and len(neg) < len(S) and _cover_ok(self, pos) and _cover_ok(self, neg):
                return self.targets[i][k]
    return None


Builder.lin_split = _lin_split


def root_box(L):
    # T_L's bounding box, with the top as an exact Q3 value
    return (Q3(0), L, Q3(0), L * S3 * HALF)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('cert')
    ap.add_argument('--max-depth', type=int, default=30)
    ap.add_argument('--out')
    ap.add_argument('--bins', default='0,1,2')
    a = ap.parse_args()
    L, pts = load(a.cert)
    b = Builder(L, pts, a.max_depth)
    t = time.time()
    roots = []
    for bi, (U0, U1) in enumerate(zip(BREAKS, BREAKS[1:])):
        if str(bi) not in a.bins.split(','):
            continue
        roots.append({'u': [str(U0), str(U1)], 'tree': b.build(root_box(L), U0, U1)})
        print(json.dumps(dict(bin=[str(U0), str(U1)], **b.stats, seconds=round(time.time() - t, 1))), flush=True)
    if a.out:
        Path(a.out).write_text(json.dumps(dict(L=str(L), roots=roots), default=str))
    return 0 if b.stats['failed'] == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
