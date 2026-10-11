import type {Measure, Point, WeightedRegion} from './types';
/** Extracted from the original desktop viewer; arithmetic, sample ordering and tolerances are unchanged.
 * All computation inputs are explicit; there is no framework or global page state. */

export function frac(s: string | number): number { var p = String(s).split('/'); return p.length > 1 ? +p[0] / +p[1] : +s; }

export function ang(D: Measure, r: number): number { return D.step ? 2 * Math.atan(r * D.step) : r * Math.PI / 18000; }

export function half(th: number): number { return (Math.cos(th) + Math.sin(th)) / 2; }

export function mass(D: Measure, cx: number, cy: number, th: number): number {
    var c = Math.cos(th), s = Math.sin(th), h = D.B / 2, m = 0, i;
    if (D.atoms) {
      for (i = 0; i < D.atoms.length; i++) {
        var a = D.atoms[i], dx = a[0] - cx, dy = a[1] - cy;
        if (Math.abs(dx * c + dy * s) <= h + 1e-9 && Math.abs(-dx * s + dy * c) <= h + 1e-9) m += a[2];
      }
    }
    if (D.segs) for (i = 0; i < D.segs.length; i++) m += D.segs[i][4] * segFrac(D.segs[i], cx, cy, c, s, h);
    if (!D.rects) return m;
    var P: Point[] = [[cx + h * (c - s), cy + h * (s + c)], [cx + h * (-c - s), cy + h * (-s + c)],
             [cx + h * (-c + s), cy + h * (-s - c)], [cx + h * (c + s), cy + h * (s - c)]];
    var e = h * (Math.abs(c) + Math.abs(s));
    for (i = 0; i < D.rects.length; i++) {
      var R = D.rects[i];
      if (R[2] <= cx - e || R[0] >= cx + e || R[3] <= cy - e || R[1] >= cy + e) continue;
      m += R[4] * clipArea(P, R);
    }
    return m;
  }

export function segFrac(g: WeightedRegion, cx: number, cy: number, c: number, s: number, h: number): number {
    var ax = g[0] - cx, ay = g[1] - cy, bx = g[2] - cx, by = g[3] - cy;
    var u0 = ax * c + ay * s, v0 = -ax * s + ay * c, u1 = bx * c + by * s, v1 = -bx * s + by * c, t0 = 0, t1 = 1;
    [[u0, u1], [v0, v1]].forEach(function (q) {
      var p0 = q[0], d = q[1] - q[0];
      if (Math.abs(d) < 1e-15) { if (Math.abs(p0) > h + 1e-9) t1 = -1; return; }
      var a = (-h - 1e-9 - p0) / d, b = (h + 1e-9 - p0) / d;
      if (a > b) { var x = a; a = b; b = x; }
      t0 = Math.max(t0, a); t1 = Math.min(t1, b);
    });
    return t1 > t0 ? t1 - t0 : 0;
  }

export function clipArea(P: Point[], R: WeightedRegion): number {
    var poly = P;
    poly = clip(poly, function (p) { return p[0] - R[0]; });
    poly = clip(poly, function (p) { return R[2] - p[0]; });
    poly = clip(poly, function (p) { return p[1] - R[1]; });
    poly = clip(poly, function (p) { return R[3] - p[1]; });
    var a = 0;
    for (var i = 0; i < poly.length; i++) { var p = poly[i], q = poly[(i + 1) % poly.length]; a += p[0] * q[1] - q[0] * p[1]; }
    return Math.abs(a) / 2;
  }

export function clip(poly: Point[], f: (p: Point) => number): Point[] {
    var o: Point[] = [];
    for (var i = 0; i < poly.length; i++) {
      var p = poly[i], q = poly[(i + 1) % poly.length], fp = f(p), fq = f(q);
      if (fp >= 0) o.push(p);
      if ((fp >= 0) !== (fq >= 0)) { var t = fp / (fp - fq); o.push([p[0] + t * (q[0] - p[0]), p[1] + t * (q[1] - p[1])]); }
    }
    return o;
  }

export function massDec(d: any): string {   // decimal of the exact total (a/b, or a/2^k)
    var t = String(d.total_mass).split('/'), q = t.length > 1 ? (t[1].indexOf('^') > 0 ? Math.pow(2, +t[1].split('^')[1]) : +t[1]) : 1;
    return (+t[0] / q).toFixed(6);
  }

export function expand(d: any, L: number): void {
    function img(q, sw, fx, fy) { var x = q[0], y = q[1]; if (sw) { var t = x; x = y; y = t; } return [fx ? L - x : x, fy ? L - y : y]; }
    [['atoms_d4', 'atoms', 1], ['segs_d4', 'segs', 2], ['rects_d4', 'rects', 2]].forEach(function (k) {
      var src = d[k[0]]; if (!src) return;
      var out = d[k[1]] || (d[k[1]] = []);
      src.forEach(function (q) {
        for (var sw = 0; sw < 2; sw++) for (var fx = 0; fx < 2; fx++) for (var fy = 0; fy < 2; fy++) {
          var a = img(q, sw, fx, fy);
          if (k[2] === 1) { out.push([a[0], a[1], q[2]]); continue; }
          var b = img([q[2], q[3]], sw, fx, fy);
          if (k[1] === 'rects') out.push([Math.min(a[0], b[0]), Math.min(a[1], b[1]), Math.max(a[0], b[0]), Math.max(a[1], b[1]), q[4]]);
          else out.push([a[0], a[1], b[0], b[1], q[4]]);
        }
      });
      delete d[k[0]];
    });
  }
