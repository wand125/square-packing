import type {Edge} from './types';
import {at, shown} from './player-timeline';
export interface Options {
  frameWidth?: number;
  frameHeight?: number;
  tl: any[];
  report: (value: any) => void;
  K: Edge | null;
  T: number;
  css: (name: string) => string;
  cv: HTMLCanvasElement;
  gg: {X: (x: number) => number; Y: (y: number) => number; d: number; b0: number; b1: number} | null;
  ja: () => boolean;
  lightTheme: boolean;
  marks: number[];
  t: number;
  viewportHeight: number;
  pixelRatio: number;
}
/** Extracted from the original desktop viewer; arithmetic, sample ordering and tolerances are unchanged.
 * Options are explicit per-call dependencies supplied by the view; there is no framework or global page state. */

export function draw(ctx: CanvasRenderingContext2D, options: Options): any {
    if (!options.K) return;
    var H = options.frameHeight || (options.frameWidth ? options.frameWidth * 16 / 9 : Math.min(options.viewportHeight * 0.8, 760)), W = options.frameWidth || Math.round(H * 9 / 16), d = options.pixelRatio || 1;
    options.cv.style.width = W + 'px'; options.cv.style.height = H + 'px'; options.cv.width = Math.round(W * d); options.cv.height = Math.round(H * d);
    var fr = at(options.tl, options.t), top = fr.layers[0][0], box = fr.box || top.box, p = shown(options.tl, fr.st), fg = options.css('--fg'), fg2 = options.css('--fg2'), mono = options.css('--mono'), sans = options.css('--sans');
    ctx.fillStyle = options.css('--bg'); ctx.fillRect(0, 0, options.cv.width, options.cv.height);
    // header
    // the number of squares, large, at the top left; the values and the piece beside it; the edge formula below
    ctx.fillStyle = fg; ctx.font = '600 ' + (64 * d) + 'px ' + sans; ctx.textBaseline = 'top';
    ctx.fillText(String(options.K.k), 12 * d, 8 * d);
    var nx = 12 * d + ctx.measureText(String(options.K.k)).width + 12 * d;
    ctx.font = '600 ' + (14 * d) + 'px ' + sans; ctx.fillText(options.ja() ? '個の単位正方形' : 'unit squares', nx, 16 * d);
    ctx.font = (12 * d) + 'px ' + mono; ctx.fillStyle = fg2;
    ctx.fillText('a = ' + box[1].toFixed(5) + '   b = ' + box[0].toFixed(5), nx, 38 * d);
    // the position of the piece in the run, counted from the square: step i / m
    var order = options.K.pieces.slice().reverse(), si = order.indexOf(p) + 1;
    ctx.fillText('step ' + si + '/' + order.length + (p.name ? '  (' + p.name + ')' : '') + (fr.st.kind === 'step' && p === fr.st.p ? (options.ja() ? '  a 一定' : '  a fixed') : ''), nx, 56 * d);
    ctx.textBaseline = 'alphabetic';
    var ftxt = p.formula || (p.note ? p.note[options.ja() ? 'ja' : 'en'] : ''); ctx.font = (10.5 * d) + 'px ' + mono;
    // the formula, right-aligned; a parametric one as two lines, a = … and b = …
    ctx.textAlign = 'right';
    var parts = String(ftxt).split(/,\s*(?=[ab]\s*=)/), fy = 96;
    parts.forEach(function (ln) { fy = wrap(ctx, options, ln, (W - 14) * d, fy * d, (W - 28) * d, 13 * d, 1e9) / d; });   // in full, even if it runs behind the box
    ctx.textAlign = 'left';
    // the box (a across, b up)
    var gh = Math.round(H * 0.2), area = { top: 128, bottom: H - gh - 46 };
    // the height cap for the box: the same up to k = 12; from k = 13 it grows evenly, by two squares in all at k = 15;
    // from k = 16 the starting box keeps the height of k = 15
    var H0 = area.bottom - area.top, kk = Math.min(options.K.k, 15), grow = 2 * Math.max(0, kk - 12) / 3, Hc = H0 + grow * H0 / (kk + 0.2);
    var S = Math.min((W - 28) / Math.max(box[1], Math.sqrt(options.K.k) + 0.4), Hc / (kk + 0.2) * kk / options.K.k);
    var sq = 1 - (fr.squash || 0), sh = (fr.shake || 0) * 2.5;
    var ox = (W - box[1] * S) / 2 + sh, oy = area.bottom;
    var X = function (yy) { return (ox + yy * S) * d; }, Y = function (x) { return (oy - x * S * sq) * d; };
    ctx.fillStyle = options.css('--bg2'); ctx.fillRect(X(0), Y(box[0]), box[1] * S * d, box[0] * S * d);
    ctx.strokeStyle = fg; ctx.lineWidth = 1.2 * d; ctx.strokeRect(X(0), Y(box[0]), box[1] * S * d, box[0] * S * d);
    fr.layers.forEach(function (L) {
      var alpha = L[1], scale = L[2] === undefined ? 1 : L[2]; if (alpha <= 0.001 || scale <= 0.001) return;
      L[0].sq.forEach(function (q) {
        var c = Math.cos(q[2]), s = Math.sin(q[2]), h = 0.5 * scale;
        ctx.beginPath();
        [[-h, -h], [h, -h], [h, h], [-h, h]].forEach(function (v, i) { var x = q[0] + v[0] * c - v[1] * s, yy = q[1] + v[0] * s + v[1] * c; i ? ctx.lineTo(X(yy), Y(x)) : ctx.moveTo(X(yy), Y(x)); });
        var col = tiltColor(ctx, options, q[2]); ctx.closePath(); ctx.fillStyle = col; ctx.globalAlpha = 0.3 * Math.min(1, alpha); ctx.fill(); ctx.globalAlpha = Math.min(1, alpha); ctx.strokeStyle = col; ctx.lineWidth = 1.2 * d; ctx.stroke();
      });
    });
    ctx.globalAlpha = 1;
    // the edge graph and the timeline
    graph(ctx, options, box, 0, (H - gh - 30) * d, W * d, gh * d, d);
    // the timeline runs along b, under the graph: its progress ends right below the graph's point
    var ty = (H - 10) * d, xs = options.gg.X(options.gg.b0), xe = options.gg.X(options.gg.b1);
    ctx.strokeStyle = options.css('--line'); ctx.lineWidth = 4 * d; ctx.lineCap = 'butt'; ctx.beginPath(); ctx.moveTo(xs, ty); ctx.lineTo(xe, ty); ctx.stroke();
    ctx.strokeStyle = options.css('--acc'); ctx.beginPath(); ctx.moveTo(xs, ty); ctx.lineTo(options.gg.X(box[0]), ty); ctx.stroke();
    ctx.fillStyle = fg2; options.marks.forEach(function (m) { ctx.fillRect(options.gg.X(m) - d, ty - 7 * d, 2 * d, 4 * d); });
    options.report(p);   // back to Rectangles at this k and the piece on screen
  }

export function tiltColor(ctx: CanvasRenderingContext2D, options: Options, th: any): any {
    var deg = Math.abs(((th * 180 / Math.PI) % 90 + 90) % 90), f = Math.min(deg, 90 - deg) / 45;   // 0 axis-parallel .. 1 at 45°
    return 'hsl(' + Math.round(212 + 108 * f) + ', ' + Math.round(55 + 15 * f) + '%, ' + (options.lightTheme ? 42 : 62) + '%)';
  }

export function wrap(ctx: CanvasRenderingContext2D, options: Options, text: any, x: any, y: any, w: any, lh: any, maxLines: any): any {   // draws text in at most maxLines lines; returns the y below it
    var words = String(text).split(' '), line = '', n = 0;
    ctx.fillStyle = options.css('--fg2');
    for (var i = 0; i < words.length; i++) {
      var tst = line ? line + ' ' + words[i] : words[i];
      if (ctx.measureText(tst).width > w && line) {
        if (n === maxLines - 1) { ctx.fillText(line + ' …', x, y); return y + lh; }
        ctx.fillText(line, x, y); y += lh; n++; line = words[i];
      } else line = tst;
    }
    if (line) { ctx.fillText(line, x, y); y += lh; }
    return y;
  }

export function graph(ctx: CanvasRenderingContext2D, options: Options, box: any, x0: any, y0: any, w: any, h: any, d: any): any {
    var gx = ctx, bmin = 1e9, bmax = 0, amin = 1e9, amax = 0;
    options.K.pieces.forEach(function (p) { p.pts.forEach(function (q) { bmin = Math.min(bmin, q[1]); bmax = Math.max(bmax, q[1]); amin = Math.min(amin, q[0]); amax = Math.max(amax, q[0]); }); });
    var m = 5 * d, Sx = (w - 2 * m) / (bmax - bmin), Sy = (h - 2 * m) / Math.max(1e-9, amax - amin);
    var X = function (b) { return x0 + m + (b - bmin) * Sx; }, Y = function (a) { return y0 + h - m - (a - amin) * Sy; };
    options.gg = { X: X, Y: Y, d: d, b0: bmin, b1: bmax };   // the timeline uses the same b scale
    // no axes, ticks or grid: the edge and the current point only
    gx.strokeStyle = options.css('--link'); gx.lineWidth = 1.8 * d;
    options.K.pieces.forEach(function (p) { gx.beginPath(); p.pts.forEach(function (q, j) { j ? gx.lineTo(X(q[1]), Y(q[0])) : gx.moveTo(X(q[1]), Y(q[0])); }); gx.stroke(); });
    gx.beginPath(); gx.arc(X(box[0]), Y(box[1]), 4 * d, 0, 7); gx.fillStyle = options.css('--acc'); gx.fill();
  }
