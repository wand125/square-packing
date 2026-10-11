"""Visualize top: one card per page, each with a small figure drawn from the data that page shows."""
import json, os
from fractions import Fraction
from lib import HERE, bi
from pages.home import PAGES, thumb, thumbs

W = 220


def _svg(h, body):
    return f'<svg viewBox="0 0 {W} {h:.0f}" width="{W}" height="{h:.0f}" aria-hidden="true">{body}</svg>'


def fig_certificate():
    # the point certificate for s(29) >= 5.57: each atom a dot, its area by weight, in [0, L]^2
    d = json.load(open(os.path.join(HERE, 'data', 'cert-point-n29.json')))
    L = float(Fraction(d['L'])); s = (W - 8) / L; wmax = max(a[2] for a in d['atoms'])
    dots = ''.join(f'<circle cx="{4 + x * s:.1f}" cy="{4 + (L - y) * s:.1f}" r="{0.6 + 3.2 * (w / wmax) ** 0.5:.2f}"/>' for x, y, w in d['atoms'])
    return _svg(W, f'<rect x="4" y="4" width="{L * s:.1f}" height="{L * s:.1f}" class="gf-box"/><g class="gf-dot">{dots}</g>')


def fig_rectangles():
    # a certified packing of 11 squares in its box: the witness with the most tilted squares
    import math
    R = json.load(open(os.path.join(HERE, 'data', 'rect-regions.json')))
    K = [K for K in R['ks'] if K['k'] == 11][0]
    ws = [w for p in K['pieces'] for w in p['witnesses'] if w.get('squares')]
    w = max(ws, key=lambda w: sum(1 for q in w['squares'] if abs(math.sin(2 * q[2])) > 1e-6))
    bx, by = w['box']; s = (W - 8) / bx; h = by * s + 8
    P = lambda x, y: f'{4 + x * s:.1f},{h - 4 - y * s:.1f}'
    sq = []
    for cx, cy, th in w['squares']:
        c, n = math.cos(th) / 2, math.sin(th) / 2
        sq.append('<polygon points="' + ' '.join(P(cx + u * c - v * n, cy + u * n + v * c) for u, v in ((-1, -1), (1, -1), (1, 1), (-1, 1))) + '" class="th-sq"/>')
    return _svg(h, f'<rect x="4" y="4" width="{bx * s:.1f}" height="{by * s:.1f}" class="th-c"/>{"".join(sq)}')


def fig_containers():
    cont = [it for it in json.load(open(os.path.join(HERE, 'data', 'containers.json'))) if it['packing']]
    pick = [it for it in cont if (it['cont'], it['n']) in (('triangle', 6), ('hexagon', 3), ('domino', 4))]
    return '<div class="gf-row">' + ''.join(thumb(it, 68) for it in pick) + '</div>'


FIG = {'certificate.html': fig_certificate, 'rect-regions.html': fig_rectangles, 'containers.html': fig_containers}


def build():
    cards = ''.join(
        f'<a class="gcard" href="{f}"><span class="gc-t">{bi(en, ja)}</span>'
        f'<span class="gc-f">{FIG[f]() if f in FIG else ""}</span><span class="gc-d">{bi(we, wj)}</span></a>'
        for f, en, ja, we, wj, g in PAGES if g == 'exp')
    return f'''<div class="home">
<section><h2>Pages</h2><div class="gcards">{cards}</div></section>
<section><h2>{bi("Optimal packings in other containers", "正方形以外の容器の最適な詰め方")}</h2>{thumbs()}</section>
</div>'''
