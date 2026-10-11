import type {Container, Pose} from './types';
import {corners, captured, inside} from './containers-geometry';
export interface Options {
  report: (value: any) => void;
  D: Container | null;
  X: (x: number) => number;
  Y: (y: number) => number;
  css: (name: string) => string;
  cvs: HTMLCanvasElement;
  px: number;
  show: {pack: boolean; pts: boolean; sq: boolean};
  st: Pose;
}
/** Extracted from the original desktop viewer; arithmetic, sample ordering and tolerances are unchanged.
 * Options are explicit per-call dependencies supplied by the view; there is no framework or global page state. */

export function path(ctx: CanvasRenderingContext2D, options: Options, P: any): any { ctx.beginPath(); P.forEach(function (p, i) { i ? ctx.lineTo(options.X(p[0]), options.Y(p[1])) : ctx.moveTo(options.X(p[0]), options.Y(p[1])); }); ctx.closePath(); }

export function draw(ctx: CanvasRenderingContext2D, options: Options): any {
    if (!options.D) return;
    var acc = options.css('--acc'), fg2 = options.css('--fg2'), link = options.css('--link');
    ctx.clearRect(0, 0, options.cvs.width, options.cvs.height);
    path(ctx, options, options.D.poly); ctx.fillStyle = options.css('--bg2'); ctx.fill(); ctx.strokeStyle = options.css('--fg'); ctx.lineWidth = 1.2 * options.px; ctx.stroke();
    if (options.show.pack && options.D.packing) options.D.packing.forEach(function (q) {
      path(ctx, options, q); ctx.globalAlpha = 0.22; ctx.fillStyle = link; ctx.fill(); ctx.globalAlpha = 1;
      ctx.strokeStyle = link; ctx.lineWidth = options.px; ctx.stroke();
    });
    if (options.show.pts) {
      ctx.strokeStyle = fg2; ctx.lineWidth = options.px; ctx.setLineDash([3 * options.px, 3 * options.px]);
      options.D.pairs.forEach(function (pr) { var a = options.D.points[pr[0]], b = options.D.points[pr[1]]; ctx.beginPath(); ctx.moveTo(options.X(a[0]), options.Y(a[1])); ctx.lineTo(options.X(b[0]), options.Y(b[1])); ctx.stroke(); });
      ctx.setLineDash([]);
      var wmax = options.D.points.reduce(function (x, p) { return Math.max(x, p[2]); }, 0), rad = Math.min(5, 70 / Math.sqrt(options.D.points.length));
      ctx.fillStyle = acc;
      options.D.points.forEach(function (p) { ctx.beginPath(); ctx.arc(options.X(p[0]), options.Y(p[1]), Math.max(1, rad * Math.sqrt(p[2] / wmax)) * options.px, 0, 7); ctx.fill(); });
    }
    if (options.show.sq) {
      var Q = corners(options.st.x, options.st.y, options.st.a), ok = Q.every(p => inside(options.D, p)), cm = captured(options.D, options.st);
      path(ctx, options, Q); ctx.strokeStyle = !ok ? fg2 : cm[0] >= 1 - 1e-9 ? options.css('--ok') : '#d9534f'; ctx.lineWidth = 2 * options.px;
      if (!ok) ctx.setLineDash([4 * options.px, 3 * options.px]); ctx.stroke(); ctx.setLineDash([]);
    options.report({cm, ok});
    }
  }
