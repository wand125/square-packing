// Rectangles player: for k squares, the box from the square (a = b) down the edge to the 1-wide strip, drawn upright
// (a across, b up), with the packing from the sampled families. Consecutive arrangements are joined continuously;
// where the squares cannot be matched, the two drawings are crossfaded.
(function () {
  'use strict';
  var root = document.getElementById('rp'); if (!root) return;
  var cv = root.querySelector('canvas'), ctx = cv.getContext('2d'), o = {};
  root.querySelectorAll('[data-o]').forEach(function (el) { o[el.dataset.o] = el; });
  var R = null, K = null, tl = [], T = 0, t = 0, playing = false, last = 0, speed = 1;   // fixed: the music is written for 1×
  // one audio element for the score, reused for every k and choice (two elements could otherwise play at once)
  var musicT = null;   // the length of the timeline each score was written to (data/music/index.json)
  fetch('data/music/index.json', { cache: 'no-store' }).then(function (r) { return r.json(); }).then(function (d) { musicT = d; if (K) loadMusic(K.k); }).catch(function () {});
  var audio = new Audio(), ready = false, actx = null, asrc = null, adest = null, endTimer = null, loadSeq = 0, blobUrl = null;
  audio.preload = 'auto';
  window.SPAudio = function () { return { paused: audio.paused, at: +audio.currentTime.toFixed(2), ready: ready, src: audio.src.split('/').pop() }; };
  function music() { return ready && o.mus.checked && speed === 1; }
  function loadMusic(k) {
    // the score: bright style, wind-up D (a break before each pop)
    audio.pause(); ready = false; o.mus.disabled = true; o.musl.classList.add('off');
    var want = ++loadSeq;
    // a score is written to one timeline: if the timeline of k has changed since (new data), the score would drift, so it is not played
    if (!musicT || Math.abs((musicT[k] || -1) - T) > 0.05) { o.musl.title = 'the score does not match this timeline'; return; }
    o.musl.title = '';
    // the score's own timeline length in the address, so a re-scored file is never taken from a cache
    var src = 'data/music/k' + k + '-normal-D.mp3?t=' + musicT[k];
    // loaded whole into memory, so that seeking works on any server (a server without range requests restarts at 0)
    fetch(src, { cache: 'no-store' }).then(function (r) { if (!r.ok) throw new Error(r.status); return r.blob(); }).then(function (b) {
      if (want !== loadSeq) return;   // a newer choice was made meanwhile
      if (blobUrl) URL.revokeObjectURL(blobUrl);
      blobUrl = URL.createObjectURL(b);
      audio.oncanplaythrough = function () { if (want !== loadSeq) return; audio.oncanplaythrough = null; ready = true; o.mus.disabled = false; o.musl.classList.remove('off'); if (playing && music()) startMusic(); };
      audio.src = blobUrl; audio.load();
    }).catch(function () { if (want === loadSeq) { ready = false; o.mus.disabled = true; o.musl.classList.add('off'); } });
  }
  function css(n) { return getComputedStyle(document.documentElement).getPropertyValue(n).trim(); }
  function ja() { return SP.L() === 'ja'; }

  // the timeline: from the diagonal end down to a = 1, piece by piece (pieces are stored from a = 1 upwards)
  var PER_A = 7, STEP = 0.9, JOIN = 0.7, HOLD = 0.25, WIND = 0.95;   // WIND includes HOLD, a short stop before the shaking   // WIND: the wind-up before a switch that changes the shape a lot   // seconds per unit of a; per jump at constant a; per crossfade
  function framesOf(p) {
    var f = p.family; if (!f) return null;
    var idx = f.a.map(function (_, i) { return i; }).sort(function (i, j) { return f.a[j] - f.a[i]; });
    return idx.map(function (i) { return { a: f.a[i], box: f.box[i], sq: f.squares[i] }; });
  }
  function build() {
    tl = []; T = 0;
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
  }
  // two drawings can be joined continuously when every square has a near partner (same count, nearby poses)
  function close(A, B) {
    if (!A || !B || A.length !== B.length) return false;
    return A.every(function (q) { return B.some(function (r) { return Math.hypot(q[0] - r[0], q[1] - r[1]) < 0.35 && Math.abs(Math.sin(2 * (q[2] - r[2]))) < 0.41   /* tilts within about 12° join continuously */; }); });
  }
  function match(A, B) {   // B reordered to follow A
    var used = [];
    return A.map(function (q) {
      var bi = -1, bd = 1e9;
      B.forEach(function (r, j) { if (used[j]) return; var d = Math.hypot(q[0] - r[0], q[1] - r[1]) + 0.3 * Math.abs(Math.sin(2 * (q[2] - r[2]))); if (d < bd) { bd = d; bi = j; } });
      used[bi] = 1; return B[bi];
    });
  }
  function lerp(u, v, s) { return u + (v - u) * s; }
  // a spring that overshoots and settles, for jumps at constant a and for switches between arrangements
  function spring(u) { if (u >= 1) return 1; return 1 - Math.exp(-6 * u) * Math.cos(9 * u) * (1 - u) ; }
  function angLerp(u, v, s) { var d = Math.atan2(Math.sin(4 * (v - u)), Math.cos(4 * (v - u))) / 4; return u + d * s; }   // squares: period 90°
  function mixFrames(F, G, s) {
    var g = match(F.sq, G.sq);
    return { a: lerp(F.a, G.a, s), box: [lerp(F.box[0], G.box[0], s), lerp(F.box[1], G.box[1], s)],
             sq: F.sq.map(function (q, i) { return [lerp(q[0], g[i][0], s), lerp(q[1], g[i][1], s), angLerp(q[2], g[i][2], s)]; }) };
  }
  function at(time) {
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

  // the whole frame is drawn on the canvas (so a recording carries it): text at the top, the box, the edge graph, the timeline
  var marks = [];
  // during a wind-up the header keeps the piece before it: step and formula change once the wind-up is over
  function shown(st) {
    var i = tl.indexOf(st);
    while (i > 0 && tl[i].kind === 'wind') i--;
    return tl[i].kind === 'wind' ? st.p : tl[i].p;
  }
  function draw() {
    if (!K) return;
    var H = Math.min(window.innerHeight * 0.8, 760), W = Math.round(H * 9 / 16), d = window.devicePixelRatio || 1;
    cv.style.width = W + 'px'; cv.style.height = H + 'px'; cv.width = Math.round(W * d); cv.height = Math.round(H * d);
    var fr = at(t), top = fr.layers[0][0], box = fr.box || top.box, p = shown(fr.st), fg = css('--fg'), fg2 = css('--fg2'), mono = css('--mono'), sans = css('--sans');
    ctx.fillStyle = css('--bg'); ctx.fillRect(0, 0, cv.width, cv.height);
    // header
    // the number of squares, large, at the top left; the values and the piece beside it; the edge formula below
    ctx.fillStyle = fg; ctx.font = '600 ' + (64 * d) + 'px ' + sans; ctx.textBaseline = 'top';
    ctx.fillText(K.k, 12 * d, 8 * d);
    var nx = 12 * d + ctx.measureText(String(K.k)).width + 12 * d;
    ctx.font = '600 ' + (14 * d) + 'px ' + sans; ctx.fillText(ja() ? '個の単位正方形' : 'unit squares', nx, 16 * d);
    ctx.font = (12 * d) + 'px ' + mono; ctx.fillStyle = fg2;
    ctx.fillText('a = ' + box[1].toFixed(5) + '   b = ' + box[0].toFixed(5), nx, 38 * d);
    // the position of the piece in the run, counted from the square: step i / m
    var order = K.pieces.slice().reverse(), si = order.indexOf(p) + 1;
    ctx.fillText('step ' + si + '/' + order.length + (p.name ? '  (' + p.name + ')' : '') + (fr.st.kind === 'step' && p === fr.st.p ? (ja() ? '  a 一定' : '  a fixed') : ''), nx, 56 * d);
    ctx.textBaseline = 'alphabetic';
    var ftxt = p.formula || (p.note ? p.note[ja() ? 'ja' : 'en'] : ''); ctx.font = (10.5 * d) + 'px ' + mono;
    // the formula, right-aligned; a parametric one as two lines, a = … and b = …
    ctx.textAlign = 'right';
    var parts = String(ftxt).split(/,\s*(?=[ab]\s*=)/), fy = 96;
    parts.forEach(function (ln) { fy = wrap(ln, (W - 14) * d, fy * d, (W - 28) * d, 13 * d, 1e9) / d; });   // in full, even if it runs behind the box
    ctx.textAlign = 'left';
    // the box (a across, b up)
    var gh = Math.round(H * 0.2), area = { top: 128, bottom: H - gh - 46 };
    // the height cap for the box: the same up to k = 12; from k = 13 it grows evenly, by two squares in all at k = 15;
    // from k = 16 the starting box keeps the height of k = 15
    var H0 = area.bottom - area.top, kk = Math.min(K.k, 15), grow = 2 * Math.max(0, kk - 12) / 3, Hc = H0 + grow * H0 / (kk + 0.2);
    var S = Math.min((W - 28) / Math.max(box[1], Math.sqrt(K.k) + 0.4), Hc / (kk + 0.2) * kk / K.k);
    var sq = 1 - (fr.squash || 0), sh = (fr.shake || 0) * 2.5;
    var ox = (W - box[1] * S) / 2 + sh, oy = area.bottom;
    var X = function (yy) { return (ox + yy * S) * d; }, Y = function (x) { return (oy - x * S * sq) * d; };
    ctx.fillStyle = css('--bg2'); ctx.fillRect(X(0), Y(box[0]), box[1] * S * d, box[0] * S * d);
    ctx.strokeStyle = fg; ctx.lineWidth = 1.2 * d; ctx.strokeRect(X(0), Y(box[0]), box[1] * S * d, box[0] * S * d);
    fr.layers.forEach(function (L) {
      var alpha = L[1], scale = L[2] === undefined ? 1 : L[2]; if (alpha <= 0.001 || scale <= 0.001) return;
      L[0].sq.forEach(function (q) {
        var c = Math.cos(q[2]), s = Math.sin(q[2]), h = 0.5 * scale;
        ctx.beginPath();
        [[-h, -h], [h, -h], [h, h], [-h, h]].forEach(function (v, i) { var x = q[0] + v[0] * c - v[1] * s, yy = q[1] + v[0] * s + v[1] * c; i ? ctx.lineTo(X(yy), Y(x)) : ctx.moveTo(X(yy), Y(x)); });
        var col = tiltColor(q[2]); ctx.closePath(); ctx.fillStyle = col; ctx.globalAlpha = 0.3 * Math.min(1, alpha); ctx.fill(); ctx.globalAlpha = Math.min(1, alpha); ctx.strokeStyle = col; ctx.lineWidth = 1.2 * d; ctx.stroke();
      });
    });
    ctx.globalAlpha = 1;
    // the edge graph and the timeline
    graph(box, 0, (H - gh - 30) * d, W * d, gh * d, d);
    // the timeline runs along b, under the graph: its progress ends right below the graph's point
    var ty = (H - 10) * d, xs = gg.X(gg.b0), xe = gg.X(gg.b1);
    ctx.strokeStyle = css('--line'); ctx.lineWidth = 4 * d; ctx.lineCap = 'butt'; ctx.beginPath(); ctx.moveTo(xs, ty); ctx.lineTo(xe, ty); ctx.stroke();
    ctx.strokeStyle = css('--acc'); ctx.beginPath(); ctx.moveTo(xs, ty); ctx.lineTo(gg.X(box[0]), ty); ctx.stroke();
    ctx.fillStyle = fg2; marks.forEach(function (m) { ctx.fillRect(gg.X(m) - d, ty - 7 * d, 2 * d, 4 * d); });
    o.scrub.value = Math.round(1000 * t / T);
    o.back.href = 'rect-regions.html#' + K.k + '-' + p.key;   // back to Rectangles at this k and the piece on screen
  }
  function tiltColor(th) {
    var deg = Math.abs(((th * 180 / Math.PI) % 90 + 90) % 90), f = Math.min(deg, 90 - deg) / 45;   // 0 axis-parallel .. 1 at 45°
    return 'hsl(' + Math.round(212 + 108 * f) + ', ' + Math.round(55 + 15 * f) + '%, ' + (document.documentElement.dataset.theme === 'light' ? 42 : 62) + '%)';
  }
  function wrap(text, x, y, w, lh, maxLines) {   // draws text in at most maxLines lines; returns the y below it
    var words = String(text).split(' '), line = '', n = 0;
    ctx.fillStyle = css('--fg2');
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
  // the edge of k (b across, a up, as on the Rectangles page) with the current box as a dot; click to jump there
  var gg = null;
  function graph(box, x0, y0, w, h, d) {
    var gx = ctx, bmin = 1e9, bmax = 0, amin = 1e9, amax = 0;
    K.pieces.forEach(function (p) { p.pts.forEach(function (q) { bmin = Math.min(bmin, q[1]); bmax = Math.max(bmax, q[1]); amin = Math.min(amin, q[0]); amax = Math.max(amax, q[0]); }); });
    var m = 5 * d, Sx = (w - 2 * m) / (bmax - bmin), Sy = (h - 2 * m) / Math.max(1e-9, amax - amin);
    var X = function (b) { return x0 + m + (b - bmin) * Sx; }, Y = function (a) { return y0 + h - m - (a - amin) * Sy; };
    gg = { X: X, Y: Y, d: d, b0: bmin, b1: bmax };   // the timeline uses the same b scale
    // no axes, ticks or grid: the edge and the current point only
    gx.strokeStyle = css('--link'); gx.lineWidth = 1.8 * d;
    K.pieces.forEach(function (p) { gx.beginPath(); p.pts.forEach(function (q, j) { j ? gx.lineTo(X(q[1]), Y(q[0])) : gx.moveTo(X(q[1]), Y(q[0])); }); gx.stroke(); });
    gx.beginPath(); gx.arc(X(box[0]), Y(box[1]), 4 * d, 0, 7); gx.fillStyle = css('--acc'); gx.fill();
  }
  // clicks on the frame: on the timeline, seek; on the graph, jump to the nearest point of the run
  cv.addEventListener('click', function (ev) {
    if (!gg) return;
    var r = cv.getBoundingClientRect(), d = gg.d, x = (ev.clientX - r.left) * d, y = (ev.clientY - r.top) * d;
    if (ev.clientY - r.top > r.height - 30) {   // the timeline is along b: the time whose box has the nearest b
      var bt = -1, bb = 1e18;
      for (var k2 = 0; k2 <= 600; k2++) { var t2 = T * k2 / 600, f2 = at(t2), b2 = (f2.box || f2.layers[0][0].box)[0], dx = Math.abs(gg.X(b2) - x); if (dx < bb) { bb = dx; bt = t2; } }
      t = bt; draw(); return;
    }
    var best = -1, bd = 400 * d * d;
    for (var i = 0; i <= 400; i++) { var tt = T * i / 400, f = at(tt), bx = f.box || f.layers[0][0].box, dd = Math.pow(gg.X(bx[0]) - x, 2) + Math.pow(gg.Y(bx[1]) - y, 2); if (dd < bd) { bd = dd; best = tt; } }
    if (best >= 0) { t = best; draw(); }
  });
  function tick(now) {
    if (!playing) return;
    var dt = last ? (now - last) / 1000 : 0; last = now;
    if (music() && audio.paused && t < T) startMusic();   // the audio stopped by itself (a stall): restart it at the picture's time
    if (music() && !audio.paused) t = Math.min(T, audio.currentTime); else t = Math.min(T, t + dt * speed);
    draw();
    if (t >= T && allMode && K.k < R.ks[R.ks.length - 1].k) {   // All: hold the last frame a moment, then the next k
      playing = false; var nk = K.k + 1;
      setTimeout(function () { if (!allMode) return; choose(nk, true); playing = true; last = 0; o.play.textContent = '❚❚'; startMusic(); requestAnimationFrame(tick); }, 900);
      return;
    }
    if (t >= T) { playing = false; o.play.textContent = '▶'; clearTimeout(endTimer); endTimer = setTimeout(function () { if (rec) rec.stop(); if (!playing) stopMusic(); }, 3200); return; }
    requestAnimationFrame(tick);
  }
  // the timeline of the current k, for scoring music to it: every segment with its kind, piece, times and box sizes
  window.SPTimeline = function () {
    return { k: K.k, T: T, hold: HOLD, segments: tl.map(function (s) {
      var f0 = at(s.t0 + 1e-6), f1 = at(Math.max(s.t0, s.t1 - 1e-6));
      return { kind: s.kind + (s.quick ? '-quick' : ''), piece: s.p.key, name: s.p.name || null, t0: +s.t0.toFixed(4), t1: +s.t1.toFixed(4),
               box0: (f0.box || f0.layers[0][0].box).map(function (v) { return +v.toFixed(5); }), box1: (f1.box || f1.layers[0][0].box).map(function (v) { return +v.toFixed(5); }) };
    }) };
  };
  var allMode = false;
  function choose(k, keepAll) {
    if (!keepAll) allMode = false;
    K = R.ks.filter(function (x) { return x.k === k; })[0]; build(); t = 0; playing = false; o.play.textContent = '▶';
    marks = tl.filter(function (s, i) { return i > 0; }).map(function (s) { var f = at(s.t0); return (f.box || f.layers[0][0].box)[0]; });
    root.querySelectorAll('[data-k]').forEach(function (b) { b.setAttribute('aria-pressed', b.dataset.k === 'all' ? allMode : +b.dataset.k === k); });
    o.len.textContent = T.toFixed(0) + ' s'; loadMusic(k); draw();
  }
  o.play.addEventListener('click', function () {
    if (playing) { playing = false; o.play.textContent = '▶'; stopMusic(); return; }
    if (t >= T) t = 0;
    playing = true; last = 0; o.play.textContent = '❚❚'; startMusic(); requestAnimationFrame(tick);
  });
  // back to the start (stopped), and play from the start; in All both go back to k = 2
  function toStart() {
    playing = false; o.play.textContent = '▶'; stopMusic(); clearTimeout(endTimer);
    if (allMode && K.k !== R.ks[0].k) { choose(R.ks[0].k, true); return; }
    t = 0; if (audio) try { audio.currentTime = 0; } catch (e) {}
    draw();
  }
  o.home.addEventListener('click', toStart);
  o.restart.addEventListener('click', function () { toStart(); playing = true; last = 0; o.play.textContent = '❚❚'; startMusic(); requestAnimationFrame(tick); });
  function startMusic() { clearTimeout(endTimer); if (music()) { if (Math.abs(audio.currentTime - t) > 0.05) audio.currentTime = t; audio.play().catch(function () {}); } }
  function stopMusic() { if (audio) audio.pause(); }
  // record: play from the start and save the canvas as a video file when the run ends
  var rec = null;
  o.rec.addEventListener('click', function () {
    if (rec) { rec.stop(); return; }
    if (!window.MediaRecorder || !cv.captureStream) { o.rec.textContent = ja() ? '録画できない' : 'cannot record'; return; }
    var type = ['video/webm;codecs=vp9', 'video/webm', 'video/mp4'].filter(function (m) { return MediaRecorder.isTypeSupported(m); })[0] || '';
    var chunks = [];
    var stream = cv.captureStream(30);
    if (music()) {   // route the music through Web Audio so the recording gets it too
      actx = actx || new AudioContext();
      if (!asrc) { asrc = actx.createMediaElementSource(audio); asrc.connect(actx.destination); }
      if (actx.state === 'suspended') actx.resume();
      adest = adest || actx.createMediaStreamDestination(); asrc.connect(adest);
      adest.stream.getAudioTracks().forEach(function (tr) { stream.addTrack(tr); });
    }
    rec = new MediaRecorder(stream, type ? { mimeType: type, videoBitsPerSecond: 6e6 } : {});
    rec.ondataavailable = function (e) { if (e.data.size) chunks.push(e.data); };
    rec.onstop = function () {
      var blob = new Blob(chunks, { type: rec.mimeType || 'video/webm' }), a = document.createElement('a');
      a.href = URL.createObjectURL(blob); a.download = 'rectangles-k' + K.k + (/mp4/.test(blob.type) ? '.mp4' : '.webm'); a.click();
      rec = null; o.rec.textContent = '● ' + (ja() ? '録画' : 'record');
    };
    rec.start(); o.rec.textContent = '■ ' + (ja() ? '停止' : 'stop');
    t = 0; playing = true; last = 0; o.play.textContent = '❚❚'; startMusic(); requestAnimationFrame(tick);
  });
  o.scrub.addEventListener('input', function () { t = T * (+o.scrub.value / 1000); if (music() && playing) audio.currentTime = t; draw(); });
  o.mus.addEventListener('change', function () { if (!music()) stopMusic(); else if (playing) startMusic(); });
  root.querySelectorAll('[data-k]').forEach(function (b) {
    b.addEventListener('click', function () {
      if (b.dataset.k === 'all') { choose(2); allMode = true; b.setAttribute('aria-pressed', 'true'); return; }
      choose(+b.dataset.k);
    });
  });
  document.addEventListener('langchange', function () { root.querySelectorAll('option[data-en]').forEach(function (op) { op.textContent = op.getAttribute('data-' + SP.L()); }); draw(); });
  new MutationObserver(draw).observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme'] });
  window.addEventListener('resize', draw);
  fetch('data/rect-regions.json', { cache: 'no-store' }).then(function (r) { return r.json(); }).then(function (d) {
    R = d;
    // opened from Rectangles: #k, or #k-piece to start at that piece (e.g. #14-14.13)
    var m = /^#(\d+)(?:-([\d.]+))?$/.exec(location.hash), k = m && R.ks.some(function (x) { return x.k === +m[1]; }) ? +m[1] : 5;
    choose(k);
    if (m && m[2]) {   // start where the piece itself begins (its run or step, after any wind-up and pop)
      var seg = tl.filter(function (x) { return x.p.key === m[2] && (x.kind === 'run' || x.kind === 'step'); })[0] || tl.filter(function (x) { return x.p.key === m[2]; })[0];
      if (seg) { t = seg.t0 + 1e-3; draw(); }   // just inside it, not on the boundary with the segment before
    }
  });
})();
