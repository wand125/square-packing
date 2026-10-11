import type {Container, Point, Pose} from './types';
const EPS = 1e-9;
/** Extracted from the original desktop viewer; arithmetic, sample ordering and tolerances are unchanged.
 * All computation inputs are explicit; there is no framework or global page state. */

export function bbox(P: Point[]): [number, number, number, number] {
    var xs = P.map(function (p) { return p[0]; }), ys = P.map(function (p) { return p[1]; });
    return [Math.min.apply(null, xs), Math.min.apply(null, ys), Math.max.apply(null, xs), Math.max.apply(null, ys)];
  }

export function corners(x: number, y: number, a: number): Point[] {
    var c = Math.cos(a), s = Math.sin(a);
    return [[-.5, -.5], [.5, -.5], [.5, .5], [-.5, .5]].map<Point>(function (k) { return [x + k[0] * c - k[1] * s, y + k[0] * s + k[1] * c]; });
  }

export function inside(D: Container, p: Point): boolean {
    var P = D.poly;
    for (var i = 0; i < P.length; i++) {
      var a = P[i], b = P[(i + 1) % P.length];
      if ((b[0] - a[0]) * (p[1] - a[1]) - (b[1] - a[1]) * (p[0] - a[0]) < -1e-9) return false;
    }
    return true;
  }

export function captured(D: Container, st: Pose): [number, number, number] {
    var c = Math.cos(st.a), s = Math.sin(st.a), e = [[c, s], [-s, c]], m = 0, k = 0, inn = D.points.map(function (p) {
      var dx = p[0] - st.x, dy = p[1] - st.y;
      return Math.abs(dx * c + dy * s) <= 0.5 + EPS && Math.abs(-dx * s + dy * c) <= 0.5 + EPS;
    });
    D.points.forEach(function (p, i) { if (inn[i]) { m += p[2]; k++; } });
    var lp = 0;
    D.pairs.forEach(function (pr) {
      if (inn[pr[0]] || inn[pr[1]]) return;
      var p = D.points[pr[0]], q = D.points[pr[1]], d = [q[0] - p[0], q[1] - p[1]];
      for (var ax = 0; ax < 2; ax++) {
        var ek = e[ax], ej = e[1 - ax], dk = d[0] * ek[0] + d[1] * ek[1];
        if (Math.abs(dk) < 1e-12) continue;
        var ck = (st.x - p[0]) * ek[0] + (st.y - p[1]) * ek[1], ta = (ck + 0.5) / dk, tb = (ck - 0.5) / dk, ok = true;
        [ta, tb].forEach(function (t) {
          var x = p[0] + t * d[0] - st.x, y = p[1] + t * d[1] - st.y;
          if (Math.abs(x * ej[0] + y * ej[1]) > 0.5 + EPS) ok = false;
        });
        if (ok && Math.max(ta, tb) >= -EPS && Math.min(ta, tb) <= 1 + EPS) { lp += Math.min(p[2], q[2]); inn[pr[0]] = inn[pr[1]] = true; break; }
      }
    });
    return [m + lp, k, lp];
  }

export function fits(D: Container, st: Pose, x: number, y: number): boolean { return corners(x, y, st.a).every(p => inside(D, p)); }

export function centroid(D: Container, st: Pose): Point {
    var c = D.poly.reduce<Point>(function (a, p) { return [a[0] + p[0] / D.poly.length, a[1] + p[1] / D.poly.length]; }, [0, 0]);
    if (fits(D, st, c[0], c[1])) return c;
    var b = bbox(D.poly), best = null, bd = Infinity, n = 80;
    for (var i = 0; i <= n; i++) for (var j = 0; j <= n; j++) {
      var x = b[0] + (b[2] - b[0]) * i / n, y = b[1] + (b[3] - b[1]) * j / n, d = (x - c[0]) * (x - c[0]) + (y - c[1]) * (y - c[1]);
      if (d < bd && fits(D, st, x, y)) { bd = d; best = [x, y]; }
    }
    return best || c;
  }

export function cons(D: Container, st: Pose): [number, number, number][] {
    var P = D.poly, out: [number, number, number][] = [], off = corners(0, 0, st.a);
    for (var i = 0; i < P.length; i++) {
      var A = P[i], B = P[(i + 1) % P.length], ex = B[0] - A[0], ey = B[1] - A[1], l = Math.hypot(ex, ey), n = [-ey / l, ex / l];
      var m = Math.min.apply(null, off.map(function (v) { return n[0] * v[0] + n[1] * v[1]; }));
      out.push([n[0], n[1], n[0] * A[0] + n[1] * A[1] - m]);
    }
    return out;
  }

export function project(D: Container, st: Pose, x: number, y: number): Point | null {
    var C = cons(D, st, ), ok = function (p) { return C.every(function (c) { return c[0] * p[0] + c[1] * p[1] >= c[2] - 1e-9; }); };
    if (ok([x, y])) return [x, y];
    var best: Point | null = null, bd = Infinity;
    function take(p) { var d = (p[0] - x) * (p[0] - x) + (p[1] - y) * (p[1] - y); if (d < bd && ok(p)) { bd = d; best = p; } }
    C.forEach(function (c) { var t = c[0] * x + c[1] * y - c[2]; take([x - t * c[0], y - t * c[1]]); });
    for (var i = 0; i < C.length; i++) for (var j = i + 1; j < C.length; j++) {
      var a = C[i], b = C[j], det = a[0] * b[1] - a[1] * b[0];
      if (Math.abs(det) > 1e-12) take([(a[2] * b[1] - a[1] * b[2]) / det, (a[0] * b[2] - a[2] * b[0]) / det]);
    }
    return best;   // null when no position fits at this angle
  }
