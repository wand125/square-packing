import type {Edge, Point, Projection, Regions} from './types';
import {inCell} from './rect-edges';
export interface Options {
  minPlotHeight?: number;
  zoomText: (value: any) => void;
  ALL: boolean;
  CELL: Point | null;
  COL: string[];
  CSEL: {k: number; key: string} | null;
  K: Edge | null;
  R: Regions;
  at: Point | null;
  base: HTMLCanvasElement | null;
  createCanvas: () => HTMLCanvasElement;
  css: (name: string) => string;
  cv: HTMLCanvasElement;
  dpr: (canvas: HTMLCanvasElement, width: number, height: number) => number;
  figW: () => number;
  geo: Projection | null;
  hov: Point | null;
  kcol: (k: number) => string;
  pc: HTMLCanvasElement;
  sel: {key: string; w: number};
  zc: HTMLCanvasElement;
  zctx: CanvasRenderingContext2D;
  zoomW: () => number;
}
/** Extracted from the original desktop viewer; arithmetic, sample ordering and tolerances are unchanged.
 * Options are explicit per-call dependencies supplied by the view; there is no framework or global page state. */

export function scaleFor(ctx: CanvasRenderingContext2D, options: Options, k: any, w: any): any {
    var pad = 30, ymax = 0, KK = options.R.ks.filter(function (x) { return x.k === k; })[0];
    ymax = KK.ymax || 0;
    KK.pieces.forEach(function (p) { p.pts.forEach(function (q) { ymax = Math.max(ymax, q[0]); }); });
    return { S: (w - pad - 10) / (k + 0.6), ymax: ymax + 0.6, pad: pad };
  }

export function drawAll(ctx: CanvasRenderingContext2D, options: Options): any {
    var w = options.figW(), pad = 30, xmax = options.R.ks[options.R.ks.length - 1].k + 0.6, ymax = Math.max(...options.R.ks.map((k: any) => k.ymax || 0));
    options.R.ks.forEach(function (KK) { KK.pieces.forEach(function (p) { p.pts.forEach(function (q) { ymax = Math.max(ymax, q[0]); }); }); });
    ymax += 0.6;
    var S = (w - pad - 10) / xmax, h = Math.max(options.minPlotHeight || 0, ymax * S + pad + 10), px = options.dpr(options.cv, w, h);
    var X = function (b) { return (pad + b * S) * px; }, Y = function (a) { return (h - pad - a * (options.minPlotHeight ? (h - pad - 10) / ymax : S)) * px; };
    options.geo = { X: X, Y: Y, px: px };
    ctx.clearRect(0, 0, options.cv.width, options.cv.height); ctx.font = (11 * px) + 'px ' + options.css('--mono');
    ctx.strokeStyle = options.css('--line'); ctx.fillStyle = options.css('--fg2'); ctx.lineWidth = px;
    for (var i = 0; i <= xmax; i++) { ctx.beginPath(); ctx.moveTo(X(i), Y(0)); ctx.lineTo(X(i), Y(ymax)); ctx.stroke(); ctx.fillText(String(i), X(i) - 3 * px, Y(0) + 14 * px); }
    for (i = 0; i <= ymax; i++) { ctx.beginPath(); ctx.moveTo(X(0), Y(i)); ctx.lineTo(X(xmax), Y(i)); ctx.stroke(); ctx.fillText(String(i), X(0) - 14 * px, Y(i) + 4 * px); }
    ctx.setLineDash([5 * px, 4 * px]); ctx.strokeStyle = options.css('--fg2'); ctx.beginPath(); ctx.moveTo(X(0), Y(0)); ctx.lineTo(X(ymax), Y(ymax)); ctx.stroke(); ctx.setLineDash([]);
    options.R.ks.forEach(function (KK) {
      if (!KK.pieces.length) return;
      ctx.strokeStyle = options.kcol(KK.k); ctx.lineWidth = 2.2 * px;
      KK.pieces.forEach(function (p, j) {
        var q = KK.pieces[j + 1];
        ctx.beginPath(); p.pts.forEach(function (v, t) { t ? ctx.lineTo(X(v[1]), Y(v[0])) : ctx.moveTo(X(v[1]), Y(v[0])); });
        if (q) ctx.lineTo(X(q.pts[0][1]), Y(q.pts[0][0]));   // close the jumps between pieces
        ctx.stroke();
      });
      var e = KK.pieces[0].pts[0]; ctx.fillStyle = options.kcol(KK.k); ctx.fillText(String(KK.k), X(e[1]) - 4 * px, Y(e[0]) - 6 * px);
    });
    options.base = options.createCanvas(); options.base.width = options.cv.width; options.base.height = options.cv.height; options.base.getContext('2d').drawImage(options.cv, 0, 0);
    if (options.hov) hover(ctx, options, options.hov);
  }

export function hover(ctx: CanvasRenderingContext2D, options: Options, hp: any): any {
    options.hov = hp; if (!options.base) return;
    ctx.clearRect(0, 0, options.cv.width, options.cv.height); ctx.drawImage(options.base, 0, 0);
    var b0 = hp[0] - 0.5, a0 = hp[1] - 0.5, X = options.geo.X, Y = options.geo.Y;
    ctx.strokeStyle = options.css('--fg'); ctx.lineWidth = 1.5 * options.geo.px; ctx.strokeRect(X(b0), Y(a0 + 1), X(b0 + 1) - X(b0), Y(a0) - Y(a0 + 1));
    drawZoom(options.zctx, options, options.zc, b0, a0, options.zoomW(), null, null);
    options.zoomText('b ∈ [' + b0.toFixed(2) + ', ' + (b0 + 1).toFixed(2) + '], a ∈ [' + a0.toFixed(2) + ', ' + (a0 + 1).toFixed(2) + ']');
  }

export function drawZoom(cx: CanvasRenderingContext2D, options: Options, c: HTMLCanvasElement, b0: any, a0: any, size: any, csel: any, dot: any): any {
    var pad = 34, S = size - 2 * pad, w = size, h = S + 2 * pad, px = options.dpr(c, w, h);
    var X = function (b) { return (pad + (b - b0) * S) * px; }, Y = function (a) { return (h - pad - (a - a0) * S) * px; };
    cx.clearRect(0, 0, c.width, c.height);
    cx.fillStyle = options.css('--bg2'); cx.fillRect(X(b0), Y(a0 + 1), S * px, S * px);
    cx.font = (11 * px) + 'px ' + options.css('--mono'); cx.fillStyle = options.css('--fg2'); cx.strokeStyle = options.css('--line'); cx.lineWidth = px;
    for (var t = 0; t <= 10; t++) {
      var v = t / 10; cx.beginPath(); cx.moveTo(X(b0 + v), Y(a0)); cx.lineTo(X(b0 + v), Y(a0 + 1)); cx.moveTo(X(b0), Y(a0 + v)); cx.lineTo(X(b0 + 1), Y(a0 + v)); cx.stroke();
      if (t % 5 === 0) { cx.fillText((b0 + v).toFixed(2), X(b0 + v) - 12 * px, Y(a0) + 16 * px); cx.fillText((a0 + v).toFixed(2), 0, Y(a0 + v) + 4 * px); }
    }
    cx.save(); cx.beginPath(); cx.rect(X(b0), Y(a0 + 1), S * px, S * px); cx.clip();
    var diag = a0 + 1 > b0;
    if (diag) { cx.setLineDash([5 * px, 4 * px]); cx.strokeStyle = options.css('--fg2'); cx.beginPath(); cx.moveTo(X(b0 - 1), Y(b0 - 1)); cx.lineTo(X(b0 + 2), Y(b0 + 2)); cx.stroke(); }
    [false, true].forEach(function (mirror) {
      if (mirror && !diag) return;
      options.R.ks.forEach(function (KK) {
        cx.strokeStyle = options.kcol(KK.k); cx.lineWidth = (mirror ? 1.6 : 2.6) * px; cx.setLineDash(mirror ? [6 * px, 4 * px] : []);
        var P = function (v) { return mirror ? [X(v[0]), Y(v[1])] : [X(v[1]), Y(v[0])]; };
        KK.pieces.forEach(function (p) {
          var on = csel && csel.k === KK.k && csel.key === p.key, lw = cx.lineWidth;
          cx.beginPath(); p.pts.forEach(function (v, i) { var q = P(v); i ? cx.lineTo(q[0], q[1]) : cx.moveTo(q[0], q[1]); });
          if (on) cx.lineWidth = lw * 1.8;
          cx.globalAlpha = csel && !on ? 0.4 : 1; cx.stroke(); cx.globalAlpha = 1; cx.lineWidth = lw;
        });
      });
    });
    cx.restore(); cx.setLineDash([]);
    cx.strokeStyle = options.css('--fg'); cx.lineWidth = px; cx.strokeRect(X(b0), Y(a0 + 1), S * px, S * px);
    if (dot) { cx.beginPath(); cx.arc(X(dot[0]), Y(dot[1]), 4.5 * px, 0, 7); cx.fillStyle = options.css('--fg'); cx.fill(); }
    return { X: X, Y: Y, px: px };
  }

export function drawCell(ctx: CanvasRenderingContext2D, options: Options): any {
    var w = options.figW();
    options.geo = drawZoom(ctx, options, options.cv, options.CELL[0], options.CELL[1], Math.min(w, 560), options.CSEL, options.CSEL && options.at && inCell([options.at[1], options.at[0]], options.CELL[0], options.CELL[1]) ? options.at : null);
  }

export function draw(ctx: CanvasRenderingContext2D, options: Options): any {
    if (options.CELL) return drawCell(ctx, options);
    if (options.ALL) return drawAll(ctx, options);
    if (!options.K) return;
    var w = options.figW(), s = scaleFor(ctx, options, options.K.k, w), s5 = scaleFor(ctx, options, 5, w);
    var S = Math.min(s.S, s5.S * s5.ymax / s.ymax), pad = s.pad, xmax = options.K.k + 0.6, ymax = s.ymax, h = Math.max(options.minPlotHeight || 0, ymax * S + pad + 10), px = options.dpr(options.cv, w, h);
    var X = function (b) { return (pad + b * S) * px; }, Y = function (a) { return (h - pad - a * (options.minPlotHeight ? (h - pad - 10) / ymax : S)) * px; };
    options.geo = { X: X, Y: Y, px: px };
    ctx.clearRect(0, 0, options.cv.width, options.cv.height); ctx.font = (11 * px) + 'px ' + options.css('--mono');
    ctx.strokeStyle = options.css('--line'); ctx.fillStyle = options.css('--fg2'); ctx.lineWidth = px;
    for (var i = 0; i <= xmax; i++) { ctx.beginPath(); ctx.moveTo(X(i), Y(0)); ctx.lineTo(X(i), Y(ymax)); ctx.stroke(); ctx.fillText(String(i), X(i) - 3 * px, Y(0) + 14 * px); }
    for (i = 0; i <= ymax; i++) { ctx.beginPath(); ctx.moveTo(X(0), Y(i)); ctx.lineTo(X(xmax), Y(i)); ctx.stroke(); ctx.fillText(String(i), X(0) - 14 * px, Y(i) + 4 * px); }
    ctx.setLineDash([5 * px, 4 * px]); ctx.strokeStyle = options.css('--fg2'); ctx.beginPath(); ctx.moveTo(X(0), Y(0)); ctx.lineTo(X(ymax), Y(ymax)); ctx.stroke(); ctx.setLineDash([]);
    ctx.fillText('b', X(xmax) - 10 * px, Y(0) - 4 * px); ctx.fillText('a', X(0) + 4 * px, Y(ymax) + 10 * px);
    // shade: rectangles below the edge (fewer than k squares fit)
    ctx.beginPath(); ctx.moveTo(X(1), Y(1)); ctx.lineTo(X(options.K.k), Y(1));
    options.K.pieces.forEach(function (p) { p.pts.forEach(function (q) { ctx.lineTo(X(q[1]), Y(q[0])); }); });
    ctx.closePath(); ctx.fillStyle = options.css('--bg3'); ctx.fill();
    // where the edge jumps between consecutive pieces (b changes at one a), join the ends with a thin line
    ctx.strokeStyle = options.css('--fg2'); ctx.lineWidth = px;
    options.K.pieces.forEach(function (p, j) {
      var q = options.K.pieces[j + 1]; if (!q) return;
      var e = p.pts[p.pts.length - 1], f = q.pts[0];
      if (Math.abs(e[0] - f[0]) > 1e-9 || Math.abs(e[1] - f[1]) > 1e-9) { ctx.beginPath(); ctx.moveTo(X(e[1]), Y(e[0])); ctx.lineTo(X(f[1]), Y(f[0])); ctx.stroke(); }
    });
    var labels = [];
    options.K.pieces.forEach(function (p, j) {
      // the selected piece (the one whose certified packing is shown) is drawn thick in full colour; the others fade
      var on = p.key === options.sel.key, path = function () { ctx.beginPath(); p.pts.forEach(function (q, t) { t ? ctx.lineTo(X(q[1]), Y(q[0])) : ctx.moveTo(X(q[1]), Y(q[0])); }); };
      ctx.setLineDash(p.kind === 'polyline' ? [5 * px, 3 * px] : []);
      ctx.globalAlpha = on ? 1 : 0.4; ctx.strokeStyle = options.COL[j % options.COL.length]; ctx.lineWidth = (on ? 4.5 : 2.2) * px; path(); ctx.stroke();
      ctx.globalAlpha = 1; ctx.setLineDash([]);
      var m = p.pts[p.pts.length >> 1], lx = X(m[1]) + 6 * px, ly = Y(m[0]) - 6 * px, lw = ctx.measureText(p.key).width;
      labels.push({ on: on, t: p.key, x: lx, y: ly, w: lw });
    });
    // piece labels: the selected piece's first, then the others that do not overlap one already placed (k >= 17 has many small pieces)
    var placed = [];
    labels.sort(function (u, v) { return v.on - u.on; }).forEach(function (L) {
      if (placed.some(function (Q) { return L.x < Q.x + Q.w + 4 * px && Q.x < L.x + L.w + 4 * px && Math.abs(L.y - Q.y) < 13 * px; })) return;
      placed.push(L); ctx.fillStyle = options.css('--fg'); ctx.fillText(L.t, L.x, L.y);
    });
    if (options.at) {   // the slider's point on the selected piece and its rectangle's corner lines
      ctx.strokeStyle = options.css('--fg'); ctx.lineWidth = px; ctx.setLineDash([3 * px, 3 * px]);
      ctx.beginPath(); ctx.moveTo(X(options.at[0]), Y(0)); ctx.lineTo(X(options.at[0]), Y(options.at[1])); ctx.lineTo(X(0), Y(options.at[1])); ctx.stroke(); ctx.setLineDash([]);
      ctx.beginPath(); ctx.arc(X(options.at[0]), Y(options.at[1]), 4 * px, 0, 7); ctx.fillStyle = options.css('--fg'); ctx.fill();
    }
    var p = options.K.pieces.find(p => p.key === options.sel.key), wt = p && p.witnesses[options.sel.w];
    if (wt) { ctx.beginPath(); ctx.arc(X(wt.b), Y(wt.a), 4.5 * px, 0, 7); ctx.fillStyle = options.css('--acc'); ctx.fill(); }
  }

export function squares(pctx: CanvasRenderingContext2D, options: Options, k: any, w: any, box: any): any {
    var bw = Math.max(k.box[0], box ? box[0] : 0), bh = Math.max(k.box[1], box ? box[1] : 0);
    // the phone view allows a taller packing (SP_PACK_MAXH)
    var S = Math.min((w - 12) / bw, ((globalThis as any).SP_PACK_MAXH || 150) / bh), h = bh * S + 12, px = options.dpr(options.pc, w, Math.ceil(h / 16) * 16);   // height in steps of 16 px: fewer reallocations while playing
    var X = function (x) { return (6 + x * S) * px; }, Y = function (y) { return (h - 6 - y * S) * px; };
    pctx.clearRect(0, 0, options.pc.width, options.pc.height);
    pctx.fillStyle = options.css('--bg2'); pctx.fillRect(X(0), Y(k.box[1]), k.box[0] * S * px, k.box[1] * S * px);
    pctx.strokeStyle = options.css('--fg'); pctx.lineWidth = px; pctx.strokeRect(X(0), Y(k.box[1]), k.box[0] * S * px, k.box[1] * S * px);
    k.squares.forEach(function (q) {
      var c = Math.cos(q[2]), s = Math.sin(q[2]);
      pctx.beginPath();
      [[-.5, -.5], [.5, -.5], [.5, .5], [-.5, .5]].forEach(function (v, i) { var x = q[0] + v[0] * c - v[1] * s, y = q[1] + v[0] * s + v[1] * c; i ? pctx.lineTo(X(x), Y(y)) : pctx.moveTo(X(x), Y(y)); });
      pctx.closePath(); pctx.globalAlpha = 0.25; pctx.fillStyle = options.css('--link'); pctx.fill(); pctx.globalAlpha = 1; pctx.strokeStyle = options.css('--link'); pctx.stroke();
    });
    if (box) { pctx.setLineDash([5 * px, 3 * px]); pctx.strokeStyle = options.css('--acc'); pctx.lineWidth = 1.5 * px; pctx.strokeRect(X(0), Y(box[1]), box[0] * S * px, box[1] * S * px); pctx.setLineDash([]); }
  }
