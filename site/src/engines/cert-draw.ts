import type {Measure} from './types';
import {ang, mass, half} from './cert-geometry';
export interface Options {
  boundText: (value: any) => void;
  report: (value: any) => void;
  D: Measure | null;
  S: number;
  X: (x: number) => number;
  Y: (y: number) => number;
  createCanvas: () => HTMLCanvasElement;
  css: (name: string) => string;
  cvs: HTMLCanvasElement;
  key: () => string;
  layer: {cv: HTMLCanvasElement; key: string} | null;
  px: number;
  st: {r: number; cx: number; cy: number; scan: {n: number; d: number; x0: number; v: number[]} | null; scanR: number};
  strip: HTMLCanvasElement;
}
/** Extracted from the original desktop viewer; arithmetic, sample ordering and tolerances are unchanged.
 * Options are explicit per-call dependencies supplied by the view; there is no framework or global page state. */

export function paintLayer(ctx: CanvasRenderingContext2D, options: Options): any {
    var oc = options.createCanvas(); oc.width = options.cvs.width; oc.height = options.cvs.height;
    var ctx = oc.getContext('2d'), acc = options.css('--acc');
    if (options.D.rects) {
      var lmax = Math.log(options.D.dmax), lmin = Math.log(options.D.dmin);
      ctx.fillStyle = acc;
      options.D.rects.forEach(function (R) {
        ctx.globalAlpha = 0.06 + 0.5 * (Math.log(R[4]) - lmin) / (lmax - lmin || 1);
        ctx.fillRect(options.X(R[0]), options.Y(R[3]), (R[2] - R[0]) * options.S * options.px, (R[3] - R[1]) * options.S * options.px);
      });
      ctx.globalAlpha = 1;
    }
    if (options.D.segs) {
      ctx.strokeStyle = options.css('--link'); ctx.lineWidth = 1.2 * options.px;
      options.D.segs.forEach(function (g) { ctx.beginPath(); ctx.moveTo(options.X(g[0]), options.Y(g[1])); ctx.lineTo(options.X(g[2]), options.Y(g[3])); ctx.stroke(); });
    }
    if (options.D.atoms) {
      ctx.fillStyle = acc;
      options.D.atoms.forEach(function (a) {
        ctx.beginPath(); ctx.arc(options.X(a[0]), options.Y(a[1]), Math.max(0.6, options.D.rad * Math.sqrt(a[2] / options.D.wmax)) * options.px, 0, 7); ctx.fill();
      });
    }
    options.layer = { cv: oc, key: options.key() };
  }

export function draw(ctx: CanvasRenderingContext2D, options: Options): any {
    if (!options.D) return;
    var W = options.cvs.width, acc = options.css('--acc'), fg = options.css('--fg'), line = options.css('--line'), bg = options.css('--bg2');
    ctx.clearRect(0, 0, W, W);
    ctx.fillStyle = bg; ctx.fillRect(options.X(0), options.Y(options.D.L), options.D.L * options.S * options.px, options.D.L * options.S * options.px);
    var th = ang(options.D, options.st.r);
    if (options.st.scan && options.st.scanR === options.st.r) drawScan(ctx, options);
    if (!options.layer || options.layer.key !== options.key()) paintLayer(ctx, options);
    ctx.drawImage(options.layer.cv, 0, 0);
    ctx.strokeStyle = line; ctx.lineWidth = options.px; ctx.strokeRect(options.X(0), options.Y(options.D.L), options.D.L * options.S * options.px, options.D.L * options.S * options.px);
    // centres where a unit square at this angle fits
    var h = half(th);
    ctx.setLineDash([4 * options.px, 4 * options.px]); ctx.strokeStyle = options.css('--fg2');
    ctx.strokeRect(options.X(h), options.Y(options.D.L - h), (options.D.L - 2 * h) * options.S * options.px, (options.D.L - 2 * h) * options.S * options.px); ctx.setLineDash([]);
    // unit square (outline) and core square at the chosen centre
    sq(ctx, options, options.st.cx, options.st.cy, th, 1, options.css('--fg2'), 1);
    var m = mass(options.D, options.st.cx, options.st.cy, th);
    sq(ctx, options, options.st.cx, options.st.cy, th, options.D.B, m >= 1 - 1e-9 ? options.css('--ok') : '#d9534f', 2);
    options.report({th, m});
    drawStrip(options.strip.getContext('2d')!, options);
  }

export function sq(ctx: CanvasRenderingContext2D, options: Options, cx: any, cy: any, th: any, side: any, col: any, lw: any): any {
    var c = Math.cos(th), s = Math.sin(th), h = side / 2;
    ctx.beginPath();
    [[1, 1], [-1, 1], [-1, -1], [1, -1]].forEach(function (k, i) {
      var x = cx + h * (k[0] * c - k[1] * s), y = cy + h * (k[0] * s + k[1] * c);
      i ? ctx.lineTo(options.X(x), options.Y(y)) : ctx.moveTo(options.X(x), options.Y(y));
    });
    ctx.closePath(); ctx.strokeStyle = col; ctx.lineWidth = lw * options.px; ctx.stroke();
  }

export function drawScan(ctx: CanvasRenderingContext2D, options: Options): any {
    var g = options.st.scan, n = g.n, ok = options.css('--ok');
    for (var i = 0; i < n; i++) for (var j = 0; j < n; j++) {
      var v = g.v[i * n + j]; if (v === undefined) continue;
      ctx.fillStyle = v >= 1 - 1e-9 ? ok : '#d9534f';
      ctx.globalAlpha = v >= 1 - 1e-9 ? Math.min(0.55, 0.12 + (v - 1) * 0.6) : 0.85;
      var x = g.x0 + (i - 0.5) * g.d, y = g.x0 + (j + 0.5) * g.d;
      ctx.fillRect(options.X(x), options.Y(y), g.d * options.S * options.px + 1, g.d * options.S * options.px + 1);
    }
    ctx.globalAlpha = 1;
  }

export function drawStrip(sctx: CanvasRenderingContext2D, options: Options): any {
    var W = options.strip.width, H = options.strip.height;
    sctx.clearRect(0, 0, W, H);
    var a = options.D.angle_lower_bound;
    if (!a) { options.strip.hidden = true; return; }
    options.strip.hidden = false;
    var lo = 1, hi = Math.max.apply(null, a), n = a.length;
    sctx.fillStyle = options.css('--fg2');
    a.forEach(function (v, i) {
      var h = (H - 4 * options.px) * Math.min(1, (v - lo) / (hi - lo) * 1) ;
      sctx.fillRect(i * W / n, H - Math.max(options.px, h), Math.max(options.px, W / n - 0.3 * options.px), Math.max(options.px, h));
    });
    sctx.fillStyle = options.css('--acc'); sctx.fillRect(options.st.r * W / n, 0, Math.max(2 * options.px, W / n), H);
    options.boundText(a[options.st.r].toFixed(6));
  }
