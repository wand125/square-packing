import type {Edge, Frame, Piece, Segment, Square, Timeline} from './types';
export const PER_A = 7, STEP = 0.9, JOIN = 0.7, HOLD = 0.25, WIND = 0.95;
/** Extracted from the original desktop viewer; arithmetic, sample ordering and tolerances are unchanged.
 * All computation inputs are explicit; there is no framework or global page state. */

export function framesOf(p: Piece): Frame[] | null {
    var f = p.family; if (!f) return null;
    var idx = f.a.map(function (_, i) { return i; }).sort(function (i, j) { return f.a[j] - f.a[i]; });
    return idx.map(function (i) { return { a: f.a[i], box: f.box[i], sq: f.squares[i] }; });
  }

export function build(K: Edge): Timeline {
    var tl: any[] = [], T = 0;
    var prev = null;
    K.pieces.slice().reverse().forEach(function (p) {
      var fr = framesOf(p);
      if (!fr) {   // a step at constant a: b jumps; joined to the next drawn piece
        tl.push({ kind: 'step', p: p, t0: T, t1: T + STEP }); T += STEP; prev = null; return;   // the step itself makes the switch
      }
      if (prev && !close(prev[prev.length - 1].sq, fr[0].sq)) {
        var lastSeg = tl[tl.length - 1];
        if (!(lastSeg && lastSeg.kind === 'wind')) { tl.push({ kind: 'wind', p: p, from: prev[prev.length - 1], t0: T, t1: T + WIND }); T += WIND; }
        tl.push({ kind: 'fade', p: p, from: prev[prev.length - 1], to: fr[0], t0: T, t1: T + JOIN }); T += JOIN;
      }
      // where b stays the same and only the width a shrinks, the box moves quickly, then winds up for what comes next
      var flatB = Math.abs(fr[0].box[0] - fr[fr.length - 1].box[0]) < 1e-6;
      // sloped pieces (a and b both change) run slowly; pieces where only the width shrinks run quickly
      var d = flatB ? Math.max(0.25, (fr[0].a - fr[fr.length - 1].a) * PER_A * 0.2) : Math.max(1.2, (fr[0].a - fr[fr.length - 1].a) * PER_A * 2);
      tl.push({ kind: 'run', p: p, fr: fr, t0: T, t1: T + d, quick: flatB }); T += d; prev = fr;
      if (flatB) { tl.push({ kind: 'wind', p: p, from: fr[fr.length - 1], t0: T, t1: T + WIND, after: true }); T += WIND; }
    });
    // steps take the drawings on both sides; a step whose two sides cannot be joined winds up first
    tl.forEach(function (s, i) {
      if (s.kind !== 'step') return;
      var b = tl.slice(0, i).reverse().filter(function (x) { return x.kind === 'run'; })[0], n = tl.slice(i + 1).filter(function (x) { return x.kind === 'run'; })[0];
      s.from = b ? b.fr[b.fr.length - 1] : (n && n.fr[0]); s.to = n ? n.fr[0] : s.from;
    });
    // a run that begins with a step starts in the square m x m at the diagonal: k squares of the m x m grid there
    var first = tl[0];
    if (first && first.kind === 'step') {
      var end = first.p.pts[first.p.pts.length - 1], m = Math.round(end[0]), sqs = [];
      for (var c = 0; c < m * m && sqs.length < K.k; c++) sqs.push([c % m + 0.5, Math.floor(c / m) + 0.5, 0]);
      first.from = { a: end[0], box: [end[1], end[0]], sq: sqs };
    }
    var out = [], shift = 0;
    tl.forEach(function (s) {
      s.t0 += shift; s.t1 += shift;
      var before = out[out.length - 1];
      if (s.kind === 'step' && !close(s.from.sq, s.to.sq) && !(before && before.kind === 'wind')) { out.push({ kind: 'wind', p: s.p, from: s.from, t0: s.t0, t1: s.t0 + WIND }); s.t0 += WIND; s.t1 += WIND; shift += WIND; }
      out.push(s);
    });
    tl = out; T += shift;
    while (tl.length && tl[tl.length - 1].kind === 'wind') { T -= tl[tl.length - 1].t1 - tl[tl.length - 1].t0; tl.pop(); }   // nothing follows the last wind-up
    return {segments: tl, duration: T};
  }

export function close(A: Square[], B: Square[]): boolean {
    if (!A || !B || A.length !== B.length) return false;
    return A.every(function (q) { return B.some(function (r) { return Math.hypot(q[0] - r[0], q[1] - r[1]) < 0.35 && Math.abs(Math.sin(2 * (q[2] - r[2]))) < 0.41   /* tilts within about 12° join continuously */; }); });
  }

export function match(A: Square[], B: Square[]): Square[] {   // B reordered to follow A
    var used = [];
    return A.map(function (q) {
      var bi = -1, bd = 1e9;
      B.forEach(function (r, j) { if (used[j]) return; var d = Math.hypot(q[0] - r[0], q[1] - r[1]) + 0.3 * Math.abs(Math.sin(2 * (q[2] - r[2]))); if (d < bd) { bd = d; bi = j; } });
      used[bi] = 1; return B[bi];
    });
  }

export function lerp(u: number, v: number, s: number): number { return u + (v - u) * s; }

export function spring(u: number): number { if (u >= 1) return 1; return 1 - Math.exp(-6 * u) * Math.cos(9 * u) * (1 - u) ; }

export function angLerp(u: number, v: number, s: number): number { var d = Math.atan2(Math.sin(4 * (v - u)), Math.cos(4 * (v - u))) / 4; return u + d * s; }

export function mixFrames(F: Frame, G: Frame, s: number): Frame {
    var g = match(F.sq, G.sq);
    return { a: lerp(F.a, G.a, s), box: [lerp(F.box[0], G.box[0], s), lerp(F.box[1], G.box[1], s)],
             sq: F.sq.map(function (q, i) { return [lerp(q[0], g[i][0], s), lerp(q[1], g[i][1], s), angLerp(q[2], g[i][2], s)]; }) };
  }

export function at(tl: Segment[], time: number): any {
    var s = tl.filter(function (x) { return time >= x.t0 && time <= x.t1; })[0] || tl[tl.length - 1];
    var u = (time - s.t0) / Math.max(1e-9, s.t1 - s.t0);
    if (s.kind === 'run') {
      var fr = s.fr, x = u * (fr.length - 1), i = Math.min(fr.length - 2, Math.floor(x));
      if (fr.length === 1) return { st: s, layers: [[fr[0], 1]] };
      if (s.quick) { u = 1 - Math.pow(1 - u, 3); x = u * (fr.length - 1); i = Math.min(fr.length - 2, Math.floor(x)); }
      return { st: s, layers: [[mixFrames(fr[i], fr[i + 1], x - i), 1]] };
    }
    if (s.kind === 'wind') {   // a short stop, then the box squeezes and shakes
      var w = Math.max(0, (time - s.t0 - HOLD) / Math.max(1e-9, s.t1 - s.t0 - HOLD));
      return { st: s, layers: [[s.from, 1]], squash: 0.06 * Math.sin(Math.PI * w / 2), shake: w * Math.sin(w * 45) };
    }
    if (s.kind === 'step' && close(s.from.sq, s.to.sq)) return { st: s, layers: [[mixFrames(s.from, s.to, spring(u)), 1]] };
    // no continuous join: the box moves, the two drawings crossfade
    // no continuous join: the box springs to its new size, the old squares shrink away and the new ones pop in
    var e = spring(u), bx = [lerp(s.from.box[0], s.to.box[0], e), lerp(s.from.box[1], s.to.box[1], e)];
    var out = Math.max(0, 1 - u / 0.35), pop = u < 0.3 ? 0 : spring((u - 0.3) / 0.7);
    return { st: s, box: bx, layers: [[s.from, out, out], [s.to, Math.min(1, pop * 1.5), pop]] };
  }

export function shown(tl: Segment[], st: Segment): Piece {
    var i = tl.indexOf(st);
    while (i > 0 && tl[i].kind === 'wind') i--;
    return tl[i].kind === 'wind' ? st.p : tl[i].p;
  }
