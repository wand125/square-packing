#!/usr/bin/env python3
"""A static picture of the measure for one container, from a layout exported by export_layout.py
(the segments of the family assembled for given k and δ, and the interior Lebesgue square).

python3 tools/closed_form_layout.py LAYOUT.json OUT.svg
Line width and opacity grow with the line density of each segment; the interior square is shaded.
"""
import json, math, sys
from fractions import Fraction as F

d = json.load(open(sys.argv[1]))
a = float(F(d['side'])); lo, hi = (float(F(x)) for x in d['interior_lebesgue'])
W = 600; M = 14; S = (W - 2 * M) / a
X = lambda x: M + x * S; Y = lambda y: W - M - y * S
dens = [float(F(s['density'])) for s in d['segments']]; dmax = max(dens)
out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {W}" width="{W}" height="{W}">',
       f'<rect x="{X(0):.1f}" y="{Y(a):.1f}" width="{a*S:.1f}" height="{a*S:.1f}" fill="none" stroke="#8a8f98" stroke-width="1.2"/>',
       f'<rect x="{X(lo):.1f}" y="{Y(hi):.1f}" width="{(hi-lo)*S:.1f}" height="{(hi-lo)*S:.1f}" fill="#4f86d9" fill-opacity="0.18" stroke="#4f86d9" stroke-opacity="0.5"/>']
for s, de in sorted(zip(d['segments'], dens), key=lambda x: x[1]):
    t = math.sqrt(de / dmax)
    at, f0, f1 = float(F(s['at'])), float(F(s['from'])), float(F(s['to']))
    x1, y1, x2, y2 = (f0, at, f1, at) if s['dir'] == 'horizontal' else (at, f0, at, f1)
    out.append(f'<line x1="{X(x1):.1f}" y1="{Y(y1):.1f}" x2="{X(x2):.1f}" y2="{Y(y2):.1f}" stroke="#e0912f" stroke-opacity="{0.25 + 0.75 * t:.2f}" stroke-width="{0.6 + 2.6 * t:.2f}"/>')
out.append('</svg>')
open(sys.argv[2], 'w').write('\n'.join(out))
print(len(d['segments']), 'segments')
