#!/usr/bin/env python3
"""Comparison plots for the closed-form bound, one per block k² ≤ N ≤ (k+1)², k = 7..17, from the table CSV.

python3 tools/closed_form_plots.py --csv closed-form-table.csv --out DIR
Writes DIR/block-kNN.svg (static SVG, fixed colours readable on light and dark backgrounds) and DIR/captions.json.
The CSV is the output of tools/closed_form_table.py, so the plots show exactly the values of the table.
The y-axis is s − k, so every block spans 0 (N = k²) to 1 (N = (k+1)²).
"""
import argparse, csv, json, math, os

# series in drawing order (later on top): key, colour, dash, width, en, ja
SERIES = [
    ('sqrt', '#8a8f98', '', 1.0, '√N (area bound)', '√N（面積の下界）'),
    ('ref_nagamochi', '#9a8fb0', '5 4', 1.6, "Nagamochi's formula (reference)", 'Nagamochi の式（参考）'),
    ('karakus', '#3fa7a0', '', 1.8, "Karakuş's formula", 'Karakuş の式'),
    ('known_lb', '#4f86d9', '', 0, 'best known lower bound', '既知の最良の下界'),
    ('a_N', '#e0912f', '', 2.6, 'our bound a(N)', 'この下界 a(N)'),
]
UB = ('known_ub', '#d0566d', 'best known upper bound (hollow: trivial ⌈√N⌉)', '既知の最良の上界（白抜き：自明な ⌈√N⌉）')
AXIS = '#8a8f98'


def num(x):
    return float(x) if x not in ('', None) else None


def plot(rows, k):
    n0, n1 = k * k, (k + 1) ** 2
    W, H, L, R, T, B = 640, 300, 46, 12, 12, 34
    X = lambda n: L + (n - n0) / (n1 - n0) * (W - L - R)
    Y = lambda y: H - B - y * (H - T - B)
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" font-family="system-ui, sans-serif" font-size="11">']
    # axes and grid
    for g in (0, .25, .5, .75, 1):
        out.append(f'<line x1="{L}" y1="{Y(g):.1f}" x2="{W-R}" y2="{Y(g):.1f}" stroke="{AXIS}" stroke-opacity="{0.6 if g in (0, 1) else 0.18}"/>')
        out.append(f'<text x="{L-6}" y="{Y(g)+4:.1f}" text-anchor="end" fill="{AXIS}">{g:g}</text>')
    step = 5 if n1 - n0 <= 40 else 10
    for n in range(n0, n1 + 1):
        if n in (n0, n1) or (n % step == 0 and n - n0 >= 3 and n1 - n >= 3):   # no label crowding the ends
            out.append(f'<line x1="{X(n):.1f}" y1="{H-B}" x2="{X(n):.1f}" y2="{H-B+4}" stroke="{AXIS}"/><text x="{X(n):.1f}" y="{H-B+16}" text-anchor="middle" fill="{AXIS}">{n}</text>')
    out.append(f'<text x="{W-R}" y="{H-3}" text-anchor="end" fill="{AXIS}">N</text>')
    out.append(f'<text x="12" y="{T+4}" fill="{AXIS}" transform="rotate(-90 12 {T+4})" text-anchor="end">s − {k}</text>')
    blk = [r for r in rows if n0 <= int(r['N']) <= n1]
    # upper bound: filled squares for records, hollow for trivial
    for r in blk:
        y = num(r['known_ub'])
        if y is None:
            continue
        x, yy = X(int(r['N'])), Y(y - k)
        if r['known_ub_trivial']:
            out.append(f'<rect x="{x-2.5:.1f}" y="{yy-2.5:.1f}" width="5" height="5" fill="none" stroke="{UB[1]}" stroke-width="1"/>')
        else:
            out.append(f'<rect x="{x-3:.1f}" y="{yy-3:.1f}" width="6" height="6" fill="{UB[1]}"/>')
    for key, col, dash, w, _, _ in SERIES:
        if key == 'sqrt':   # the area bound, computed from N (every N of the block, squares included)
            pts = [(int(r['N']), math.sqrt(int(r['N']))) for r in blk]
        else:
            pts = [(int(r['N']), num(r[key])) for r in blk if num(r[key]) is not None and not r['square']]
        if key == 'known_lb':   # points: published values are per N
            out += [f'<circle cx="{X(n):.1f}" cy="{Y(v-k):.1f}" r="2.6" fill="{col}"/>' for n, v in pts]
            continue
        if pts:
            d = ' '.join(f'{X(n):.1f},{Y(v-k):.1f}' for n, v in pts)
            out.append(f'<polyline points="{d}" fill="none" stroke="{col}" stroke-width="{w}" stroke-linejoin="round"' + (f' stroke-dasharray="{dash}"' if dash else '') + '/>')
    out.append('</svg>')
    # caption facts
    ns = [r for r in blk if not r['square'] and r['a_N']]
    above_lb = sum(1 for r in ns if float(r['a_minus_known_lb']) > 1e-9)
    eq_nag = [int(r['N']) for r in ns if abs(float(r['a_minus_nagamochi'])) <= 1e-9]
    above_kar = sum(1 for r in ns if float(r['a_minus_karakus']) > 1e-9)
    records = sum(1 for r in blk if not r['known_ub_trivial'])
    cap = {'k': k, 'n0': n0, 'n1': n1, 'nonsquare': len(ns), 'above_known_lb': above_lb, 'above_karakus': above_kar,
           'equal_nagamochi': eq_nag, 'ub_records': records}
    return '\n'.join(out), cap


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--csv', required=True); ap.add_argument('--out', required=True)
    ap.add_argument('--kmin', type=int, default=7); ap.add_argument('--kmax', type=int, default=17)
    o = ap.parse_args()
    rows = list(csv.DictReader(open(o.csv)))
    os.makedirs(o.out, exist_ok=True)
    caps = []
    for k in range(o.kmin, o.kmax + 1):
        svg, cap = plot(rows, k)
        open(os.path.join(o.out, f'block-k{k:02d}.svg'), 'w').write(svg)
        caps.append(cap)
    legend = [{'key': UB[0], 'colour': UB[1], 'en': UB[2], 'ja': UB[3], 'mark': 'square'}] + \
             [{'key': s[0], 'colour': s[1], 'dash': s[2], 'en': s[4], 'ja': s[5], 'mark': 'dot' if s[0] == 'known_lb' else 'line'} for s in SERIES]
    json.dump({'legend': legend, 'blocks': caps}, open(os.path.join(o.out, 'captions.json'), 'w'), ensure_ascii=False, indent=1)
    print(len(caps), 'plots')


if __name__ == '__main__':
    main()
