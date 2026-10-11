import type {Edge, Packing, Piece, Point, Projection, Regions} from './types';
/** Extracted from the original desktop viewer; arithmetic, sample ordering and tolerances are unchanged.
 * All computation inputs are explicit; there is no framework or global page state. */

export function along(p: Piece, c: 0 | 1, v: number): number | null {
    var q = p.pts;
    for (var i = 0; i + 1 < q.length; i++) {
      var lo = Math.min(q[i][c], q[i + 1][c]), hi = Math.max(q[i][c], q[i + 1][c]);
      if (v < lo - 1e-12 || v > hi + 1e-12 || hi - lo < 1e-15) continue;
      var t = (v - q[i][c]) / (q[i + 1][c] - q[i][c]);
      return q[i][1 - c] + t * (q[i + 1][1 - c] - q[i][1 - c]);
    }
    return null;
  }

export function span(p: Piece, c: 0 | 1): Point { var v = p.pts.map(function (q) { return q[c]; }); return [Math.min.apply(null, v), Math.max.apply(null, v)]; }

export function familyAt(p: Piece, a: number): Packing | null {
    var f = p.family; if (!f || f.a.length === 0) return null;
    var i = 0, n = f.a.length, asc = f.a[n - 1] >= f.a[0];
    while (i + 1 < n && (asc ? f.a[i + 1] < a : f.a[i + 1] > a)) i++;
    var j = Math.min(i + 1, n - 1), t = j === i || f.a[j] === f.a[i] ? 0 : Math.min(1, Math.max(0, (a - f.a[i]) / (f.a[j] - f.a[i])));
    var mix = function (u, v) { return u + t * (v - u); };
    return { box: [mix(f.box[i][0], f.box[j][0]), mix(f.box[i][1], f.box[j][1])],
             squares: f.squares[i].map(function (q, m) { var r = f.squares[j][m]; return [mix(q[0], r[0]), mix(q[1], r[1]), mix(q[2], r[2])]; }) };
  }

export function inCell(q: Point, b0: number, a0: number): boolean { return q[1] >= b0 && q[1] <= b0 + 1 && q[0] >= a0 && q[0] <= a0 + 1; }

export function throughCell(p: Piece, b0: number, a0: number): boolean { return p.pts.some(function (q) { return inCell(q, b0, a0) || (b0 === a0 && inCell([q[1], q[0]], b0, a0)); }); }

export function nearestEdge(CELL: Point | null, K: Edge, R: Regions, geo: Projection, x: number, y: number): any {
    var best: {k: number; p: Piece; a: number; b: number} | null = null, bd = 1e18;
    // the candidates: the pieces of k, or in a magnified cell the pieces of every k that pass through it
    var cands: [number, Piece][] = [];
    if (CELL) R.ks.forEach(function (KK) { KK.pieces.forEach(function (p) { if (throughCell(p, CELL[0], CELL[1])) cands.push([KK.k, p]); }); });
    else K.pieces.forEach(function (p) { cands.push([K.k, p]); });
    cands.forEach(function (c) {
      var p = c[1];
      for (var i = 0; i < p.pts.length; i++) {
        var u = p.pts[i], v = p.pts[Math.min(i + 1, p.pts.length - 1)];
        var ux = geo.X(u[1]), uy = geo.Y(u[0]), dx = geo.X(v[1]) - ux, dy = geo.Y(v[0]) - uy, L = dx * dx + dy * dy;
        var t = L > 0 ? Math.max(0, Math.min(1, ((x - ux) * dx + (y - uy) * dy) / L)) : 0;
        var d = Math.pow(ux + t * dx - x, 2) + Math.pow(uy + t * dy - y, 2);
        if (d < bd) { bd = d; best = { k: c[0], p: p, a: u[0] + t * (v[0] - u[0]), b: u[1] + t * (v[1] - u[1]) }; }
      }
    });
    return best;
  }

export function pathOf(K: Edge): any {   // the edge as one polyline in plot units, left to right, with the arc length at every point
    var out = [], L = 0;
    K.pieces.slice().reverse().forEach(function (p) { p.pts.slice().reverse().forEach(function (q) {
      var prev = out[out.length - 1]; if (prev) L += Math.hypot(q[1] - prev.b, q[0] - prev.a);
      out.push({ p: p, a: q[0], b: q[1], s: L }); }); });
    return out;
  }
