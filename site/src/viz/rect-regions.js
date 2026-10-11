// Rectangles: for k = 2 .. 20 squares, the edge in the (b, a) plane (b = long side, drawn as x; a = short side, as y)
// where k squares begin to fit, its pieces, the witness packings, and for k <= 10 the proof status of Friedman's pieces.
(function () {
  'use strict';
  var root = document.getElementById('rr'); if (!root) return;
  var cv = root.querySelector('canvas.reg'), ctx = cv.getContext('2d'), pc = root.querySelector('canvas.pk'), pctx = pc.getContext('2d');
  var tb = root.querySelector('#rr-rows'), o = {};
  root.querySelectorAll('[data-o]').forEach(function (el) { o[el.dataset.o] = el; });
  var COL = ['#286bb2', '#b64c19', '#23805d', '#9660b8', '#a67b05', '#b54179', '#39818b', '#7d7434', '#7463cb', '#5b7f2e', '#a14f4f', '#3f6fa0'];
  var SRC = { friedman: ["Friedman's piece", 'Friedman の片'], grid: ['grid', '格子'], ours: ['our shapes', '当方の型'] };
  var KIND = { proved: ['proved (one checker so far)', '証明済み（検査器 1 つ）'], progress: ['in progress', '進行中'], open: ['not yet', '未'] };
  // one colour per number of squares k = 2 .. 20 (the All view)
  function kcol(k) { return 'hsl(' + Math.round((k - 2) * 360 / (R.ks.length + 1)) + ', 60%, ' + (document.documentElement.dataset.theme === 'light' ? 40 : 62) + '%)'; }
  var ALL = false, CELL = null, CSEL = null, at = null;   // at: [b, a], the point chosen on the selected piece with the slider   // CSEL: the piece chosen in the cell view   // CELL = [i, j]: the grid cell [i, i+1] x [j, j+1] magnified in place of the plot
  var R = null, K = null, sel = { key: null, w: 0 }, geo = null, cur = 5;
  // FIT (<= 1) shrinks the figures so that the pieces table starts within the top two thirds of the window
  var FIT = 1;
  function figW() { return Math.max(200, Math.round(Math.min(root.querySelector('.cv-fig').clientWidth || 600, 680) * FIT)); }
  function sideW() { return Math.max(160, Math.round(Math.min(Math.max(220, (root.querySelector('.pcard').clientWidth || 640) * 0.5), 460) * FIT)); }
  function zoomW() { return Math.min(root.querySelector('.cv-side').clientWidth || 320, 480); }
  function css(n) { return getComputedStyle(document.documentElement).getPropertyValue(n).trim(); }
  function ja() { return SP.L() === 'ja'; }
  function dpr(c, w, h) { var d = window.devicePixelRatio || 1; c.style.width = w + 'px'; c.style.height = h + 'px'; c.width = Math.round(w * d); c.height = Math.round(h * d); return d; }
  function esc(t) { return String(t).replace(/&/g, '&amp;').replace(/</g, '&lt;'); }
  // a parametric piece "a = A(p), b = B(p)" is shown on two lines
  function fml(t) { return esc(t).replace(/,\s*(?=[ab]\s*=)/, '<br>'); }
  function piece(key) { return K.pieces.filter(function (p) { return p.key === key; })[0]; }

  // the plot: x = b from 0 to k + 0.6, y = a from 0 to the top of the edge; height capped at that of k = 5
  function scaleFor(k, w) {
    var pad = 30, ymax = 0, KK = R.ks.filter(function (x) { return x.k === k; })[0];
    KK.pieces.forEach(function (p) { p.pts.forEach(function (q) { ymax = Math.max(ymax, q[0]); }); });
    return { S: (w - pad - 10) / (k + 0.6), ymax: ymax + 0.6, pad: pad };
  }
  function drawAll() {
    var w = figW(), pad = 30, xmax = R.ks[R.ks.length - 1].k + 0.6, ymax = 0;
    R.ks.forEach(function (KK) { KK.pieces.forEach(function (p) { p.pts.forEach(function (q) { ymax = Math.max(ymax, q[0]); }); }); });
    ymax += 0.6;
    var S = (w - pad - 10) / xmax, h = ymax * S + pad + 10, px = dpr(cv, w, h);
    var X = function (b) { return (pad + b * S) * px; }, Y = function (a) { return (h - pad - a * S) * px; };
    geo = { X: X, Y: Y, px: px };
    ctx.clearRect(0, 0, cv.width, cv.height); ctx.font = (11 * px) + 'px ' + css('--mono');
    ctx.strokeStyle = css('--line'); ctx.fillStyle = css('--fg2'); ctx.lineWidth = px;
    for (var i = 0; i <= xmax; i++) { ctx.beginPath(); ctx.moveTo(X(i), Y(0)); ctx.lineTo(X(i), Y(ymax)); ctx.stroke(); ctx.fillText(i, X(i) - 3 * px, Y(0) + 14 * px); }
    for (i = 0; i <= ymax; i++) { ctx.beginPath(); ctx.moveTo(X(0), Y(i)); ctx.lineTo(X(xmax), Y(i)); ctx.stroke(); ctx.fillText(i, X(0) - 14 * px, Y(i) + 4 * px); }
    ctx.setLineDash([5 * px, 4 * px]); ctx.strokeStyle = css('--fg2'); ctx.beginPath(); ctx.moveTo(X(0), Y(0)); ctx.lineTo(X(ymax), Y(ymax)); ctx.stroke(); ctx.setLineDash([]);
    R.ks.forEach(function (KK) {
      ctx.strokeStyle = kcol(KK.k); ctx.lineWidth = 2.2 * px;
      KK.pieces.forEach(function (p, j) {
        var q = KK.pieces[j + 1];
        ctx.beginPath(); p.pts.forEach(function (v, t) { t ? ctx.lineTo(X(v[1]), Y(v[0])) : ctx.moveTo(X(v[1]), Y(v[0])); });
        if (q) ctx.lineTo(X(q.pts[0][1]), Y(q.pts[0][0]));   // close the jumps between pieces
        ctx.stroke();
      });
      var e = KK.pieces[0].pts[0]; ctx.fillStyle = kcol(KK.k); ctx.fillText(KK.k, X(e[1]) - 4 * px, Y(e[0]) - 6 * px);
    });
    base = document.createElement('canvas'); base.width = cv.width; base.height = cv.height; base.getContext('2d').drawImage(cv, 0, 0);
    if (hov) hover(hov);
  }
  // the hover window in All: a 1 x 1 box centred on the pointer (right of the diagonal), magnified in the side column
  var base = null, hov = null, zc = root.querySelector('canvas.zm'), zctx = zc.getContext('2d'), hq = 0;
  function hover(hp) {
    hov = hp; if (!base) return;
    ctx.clearRect(0, 0, cv.width, cv.height); ctx.drawImage(base, 0, 0);
    var b0 = hp[0] - 0.5, a0 = hp[1] - 0.5, X = geo.X, Y = geo.Y;
    ctx.strokeStyle = css('--fg'); ctx.lineWidth = 1.5 * geo.px; ctx.strokeRect(X(b0), Y(a0 + 1), X(b0 + 1) - X(b0), Y(a0) - Y(a0 + 1));
    drawZoom(zc, zctx, b0, a0, zoomW(), null, null);
    o.zt.textContent = 'b ∈ [' + b0.toFixed(2) + ', ' + (b0 + 1).toFixed(2) + '], a ∈ [' + a0.toFixed(2) + ', ' + (a0 + 1).toFixed(2) + ']';
  }
  cv.addEventListener('mousemove', function (ev) {
    if (!ALL || CELL || !geo) return;
    var r = cv.getBoundingClientRect(), x = (ev.clientX - r.left) * geo.px, y = (ev.clientY - r.top) * geo.px;
    var unit = geo.X(1) - geo.X(0), b = (x - geo.X(0)) / unit, a = (geo.Y(0) - y) / unit;
    if (a < 0 || b < 0 || a > b) return;
    if (hq) cancelAnimationFrame(hq);
    hq = requestAnimationFrame(function () { hq = 0; zc.hidden = false; hover([b, a]); });
  });
  function inCell(q, b0, a0) { return q[1] >= b0 && q[1] <= b0 + 1 && q[0] >= a0 && q[0] <= a0 + 1; }
  function throughCell(p, b0, a0) { return p.pts.some(function (q) { return inCell(q, b0, a0) || (b0 === a0 && inCell([q[1], q[0]], b0, a0)); }); }
  // a magnified 1 x 1 window [b0, b0 + 1] x [a0, a0 + 1] of every edge, drawn on canvas c of side about size;
  // where the window reaches the diagonal, the edges mirrored across a = b are dashed
  function drawZoom(c, cx, b0, a0, size, csel, dot) {
    var pad = 34, S = size - 2 * pad, w = size, h = S + 2 * pad, px = dpr(c, w, h);
    var X = function (b) { return (pad + (b - b0) * S) * px; }, Y = function (a) { return (h - pad - (a - a0) * S) * px; };
    cx.clearRect(0, 0, c.width, c.height);
    cx.fillStyle = css('--bg2'); cx.fillRect(X(b0), Y(a0 + 1), S * px, S * px);
    cx.font = (11 * px) + 'px ' + css('--mono'); cx.fillStyle = css('--fg2'); cx.strokeStyle = css('--line'); cx.lineWidth = px;
    for (var t = 0; t <= 10; t++) {
      var v = t / 10; cx.beginPath(); cx.moveTo(X(b0 + v), Y(a0)); cx.lineTo(X(b0 + v), Y(a0 + 1)); cx.moveTo(X(b0), Y(a0 + v)); cx.lineTo(X(b0 + 1), Y(a0 + v)); cx.stroke();
      if (t % 5 === 0) { cx.fillText((b0 + v).toFixed(2), X(b0 + v) - 12 * px, Y(a0) + 16 * px); cx.fillText((a0 + v).toFixed(2), 0, Y(a0 + v) + 4 * px); }
    }
    cx.save(); cx.beginPath(); cx.rect(X(b0), Y(a0 + 1), S * px, S * px); cx.clip();
    var diag = a0 + 1 > b0;
    if (diag) { cx.setLineDash([5 * px, 4 * px]); cx.strokeStyle = css('--fg2'); cx.beginPath(); cx.moveTo(X(b0 - 1), Y(b0 - 1)); cx.lineTo(X(b0 + 2), Y(b0 + 2)); cx.stroke(); }
    [false, true].forEach(function (mirror) {
      if (mirror && !diag) return;
      R.ks.forEach(function (KK) {
        cx.strokeStyle = kcol(KK.k); cx.lineWidth = (mirror ? 1.6 : 2.6) * px; cx.setLineDash(mirror ? [6 * px, 4 * px] : []);
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
    cx.strokeStyle = css('--fg'); cx.lineWidth = px; cx.strokeRect(X(b0), Y(a0 + 1), S * px, S * px);
    if (dot) { cx.beginPath(); cx.arc(X(dot[0]), Y(dot[1]), 4.5 * px, 0, 7); cx.fillStyle = css('--fg'); cx.fill(); }
    return { X: X, Y: Y, px: px };
  }
  // the magnified cell, drawn in the plot's place
  function drawCell() {
    var w = figW();
    geo = drawZoom(cv, ctx, CELL[0], CELL[1], Math.min(w, 560), CSEL, CSEL && at && inCell([at[1], at[0]], CELL[0], CELL[1]) ? at : null);
  }
  function draw() {
    if (CELL) return drawCell();
    if (ALL) return drawAll();
    if (!K) return;
    var w = figW(), s = scaleFor(K.k, w), s5 = scaleFor(5, w);
    var S = Math.min(s.S, s5.S * s5.ymax / s.ymax), pad = s.pad, xmax = K.k + 0.6, ymax = s.ymax, h = ymax * S + pad + 10, px = dpr(cv, w, h);
    var X = function (b) { return (pad + b * S) * px; }, Y = function (a) { return (h - pad - a * S) * px; };
    geo = { X: X, Y: Y, px: px };
    ctx.clearRect(0, 0, cv.width, cv.height); ctx.font = (11 * px) + 'px ' + css('--mono');
    ctx.strokeStyle = css('--line'); ctx.fillStyle = css('--fg2'); ctx.lineWidth = px;
    for (var i = 0; i <= xmax; i++) { ctx.beginPath(); ctx.moveTo(X(i), Y(0)); ctx.lineTo(X(i), Y(ymax)); ctx.stroke(); ctx.fillText(i, X(i) - 3 * px, Y(0) + 14 * px); }
    for (i = 0; i <= ymax; i++) { ctx.beginPath(); ctx.moveTo(X(0), Y(i)); ctx.lineTo(X(xmax), Y(i)); ctx.stroke(); ctx.fillText(i, X(0) - 14 * px, Y(i) + 4 * px); }
    ctx.setLineDash([5 * px, 4 * px]); ctx.strokeStyle = css('--fg2'); ctx.beginPath(); ctx.moveTo(X(0), Y(0)); ctx.lineTo(X(ymax), Y(ymax)); ctx.stroke(); ctx.setLineDash([]);
    ctx.fillText('b', X(xmax) - 10 * px, Y(0) - 4 * px); ctx.fillText('a', X(0) + 4 * px, Y(ymax) + 10 * px);
    // shade: rectangles below the edge (fewer than k squares fit)
    ctx.beginPath(); ctx.moveTo(X(1), Y(1)); ctx.lineTo(X(K.k), Y(1));
    K.pieces.forEach(function (p) { p.pts.forEach(function (q) { ctx.lineTo(X(q[1]), Y(q[0])); }); });
    ctx.closePath(); ctx.fillStyle = css('--bg3'); ctx.fill();
    // where the edge jumps between consecutive pieces (b changes at one a), join the ends with a thin line
    ctx.strokeStyle = css('--fg2'); ctx.lineWidth = px;
    K.pieces.forEach(function (p, j) {
      var q = K.pieces[j + 1]; if (!q) return;
      var e = p.pts[p.pts.length - 1], f = q.pts[0];
      if (Math.abs(e[0] - f[0]) > 1e-9 || Math.abs(e[1] - f[1]) > 1e-9) { ctx.beginPath(); ctx.moveTo(X(e[1]), Y(e[0])); ctx.lineTo(X(f[1]), Y(f[0])); ctx.stroke(); }
    });
    var labels = [];
    K.pieces.forEach(function (p, j) {
      // the selected piece (the one whose certified packing is shown) is drawn thick in full colour; the others fade
      var on = p.key === sel.key, path = function () { ctx.beginPath(); p.pts.forEach(function (q, t) { t ? ctx.lineTo(X(q[1]), Y(q[0])) : ctx.moveTo(X(q[1]), Y(q[0])); }); };
      ctx.setLineDash(p.kind === 'polyline' ? [5 * px, 3 * px] : []);
      ctx.globalAlpha = on ? 1 : 0.4; ctx.strokeStyle = COL[j % COL.length]; ctx.lineWidth = (on ? 4.5 : 2.2) * px; path(); ctx.stroke();
      ctx.globalAlpha = 1; ctx.setLineDash([]);
      var m = p.pts[p.pts.length >> 1], lx = X(m[1]) + 6 * px, ly = Y(m[0]) - 6 * px, lw = ctx.measureText(p.key).width;
      labels.push({ on: on, t: p.key, x: lx, y: ly, w: lw });
    });
    // piece labels: the selected piece's first, then the others that do not overlap one already placed (k >= 17 has many small pieces)
    var placed = [];
    labels.sort(function (u, v) { return v.on - u.on; }).forEach(function (L) {
      if (placed.some(function (Q) { return L.x < Q.x + Q.w + 4 * px && Q.x < L.x + L.w + 4 * px && Math.abs(L.y - Q.y) < 13 * px; })) return;
      placed.push(L); ctx.fillStyle = css('--fg'); ctx.fillText(L.t, L.x, L.y);
    });
    if (at) {   // the slider's point on the selected piece and its rectangle's corner lines
      ctx.strokeStyle = css('--fg'); ctx.lineWidth = px; ctx.setLineDash([3 * px, 3 * px]);
      ctx.beginPath(); ctx.moveTo(X(at[0]), Y(0)); ctx.lineTo(X(at[0]), Y(at[1])); ctx.lineTo(X(0), Y(at[1])); ctx.stroke(); ctx.setLineDash([]);
      ctx.beginPath(); ctx.arc(X(at[0]), Y(at[1]), 4 * px, 0, 7); ctx.fillStyle = css('--fg'); ctx.fill();
    }
    var p = piece(sel.key), wt = p && p.witnesses[sel.w];
    if (wt) { ctx.beginPath(); ctx.arc(X(wt.b), Y(wt.a), 4.5 * px, 0, 7); ctx.fillStyle = css('--acc'); ctx.fill(); }
  }
  // the certified packing in its box; with the slider, the rectangle b x a at the chosen point is drawn over it (dashed)
  function squares(k, w, box) {
    var bw = Math.max(k.box[0], box ? box[0] : 0), bh = Math.max(k.box[1], box ? box[1] : 0);
    var S = Math.min((w - 12) / bw, 150 / bh), h = bh * S + 12, px = dpr(pc, w, h);
    var X = function (x) { return (6 + x * S) * px; }, Y = function (y) { return (h - 6 - y * S) * px; };
    pctx.clearRect(0, 0, pc.width, pc.height);
    pctx.fillStyle = css('--bg2'); pctx.fillRect(X(0), Y(k.box[1]), k.box[0] * S * px, k.box[1] * S * px);
    pctx.strokeStyle = css('--fg'); pctx.lineWidth = px; pctx.strokeRect(X(0), Y(k.box[1]), k.box[0] * S * px, k.box[1] * S * px);
    k.squares.forEach(function (q) {
      var c = Math.cos(q[2]), s = Math.sin(q[2]);
      pctx.beginPath();
      [[-.5, -.5], [.5, -.5], [.5, .5], [-.5, .5]].forEach(function (v, i) { var x = q[0] + v[0] * c - v[1] * s, y = q[1] + v[0] * s + v[1] * c; i ? pctx.lineTo(X(x), Y(y)) : pctx.moveTo(X(x), Y(y)); });
      pctx.closePath(); pctx.globalAlpha = 0.25; pctx.fillStyle = css('--link'); pctx.fill(); pctx.globalAlpha = 1; pctx.strokeStyle = css('--link'); pctx.stroke();
    });
    if (box) { pctx.setLineDash([5 * px, 3 * px]); pctx.strokeStyle = css('--acc'); pctx.lineWidth = 1.5 * px; pctx.strokeRect(X(0), Y(box[1]), box[0] * S * px, box[1] * S * px); pctx.setLineDash([]); }
  }
  // the a and b formulas of a curve without a short closed form, collapsed (c8's "formula_full")
  // the a and b formulas of a curve without a short closed form (c8's "formula_full"): a toggle; the formulas open
  // at full width, in the detail view under the plot and in the tables as a row spanning every column
  function fullHtml(p) {
    var f = p.formula_full;
    var lines = [f.a, f.b].concat(f.constraints || []).filter(Boolean).map(esc).join('<br>');
    return '<div class="num">' + lines + (f.param ? '<br><span class="dim">' + esc(f.param[ja() ? 'ja' : 'en'] || '') + '</span>' : '') + '</div>';
  }
  function full(p, where) {
    if (!p.formula_full) return '';
    return ' <a href="#" class="fft" data-ff="' + where + '" data-key="' + p.key + '">' + (ja() ? 'a, b の式 ▸' : 'a, b formulas ▸') + '</a>';
  }
  var ffOpen = null;   // the piece whose a and b formulas are open, right under its edge formula in the card
  function bindFull(scope, p) {
    scope.querySelectorAll('a.fft').forEach(function (a) {
      a.addEventListener('click', function (e) {
        e.preventDefault();
        if (a.dataset.ff === 'side') { ffOpen = ffOpen === p ? null : p; o.ffw.hidden = !ffOpen; o.ffw.innerHTML = ffOpen ? fullHtml(ffOpen) : ''; return; }
        var tr = a.closest('tr'), nx = tr.nextElementSibling;
        if (nx && nx.classList.contains('ffrow')) { nx.remove(); return; }
        var row = document.createElement('tr'); row.className = 'ffrow';
        row.innerHTML = '<td colspan="5">' + fullHtml(p) + '</td>'; tr.after(row);
      });
    });
  }
  // b on the piece at a given a, read from its points (linear between neighbours); null where a is constant
  // a point on the piece read from its points (linear between neighbours): the other coordinate where coordinate c
  // (0 = a, 1 = b) equals v; null if the piece does not reach v
  function along(p, c, v) {
    var q = p.pts;
    for (var i = 0; i + 1 < q.length; i++) {
      var lo = Math.min(q[i][c], q[i + 1][c]), hi = Math.max(q[i][c], q[i + 1][c]);
      if (v < lo - 1e-12 || v > hi + 1e-12 || hi - lo < 1e-15) continue;
      var t = (v - q[i][c]) / (q[i + 1][c] - q[i][c]);
      return q[i][1 - c] + t * (q[i + 1][1 - c] - q[i][1 - c]);
    }
    return null;
  }
  function span(p, c) { var v = p.pts.map(function (q) { return q[c]; }); return [Math.min.apply(null, v), Math.max.apply(null, v)]; }
  // the point on the selected piece, set by pressing or dragging along the edge on the plot (or by a certificate button);
  // when none is set yet, the piece's first certified packing, or the middle of the piece
  function point(p) {
    if (!at) {
      var w = p.witnesses[Math.min(sel.w, Math.max(0, p.witnesses.length - 1))];
      if (w) at = [w.b, w.a];
      else { var m = p.pts[p.pts.length >> 1]; at = [m[1], m[0]]; }
    }
    o.ab.textContent = '(' + at[0].toFixed(6) + ', ' + at[1].toFixed(6) + ')';
  }
  // the sampled packing of the piece at a (c8's "family"), linear between the two nearest samples
  function familyAt(p, a) {
    var f = p.family; if (!f || f.a.length === 0) return null;
    var i = 0, n = f.a.length, asc = f.a[n - 1] >= f.a[0];
    while (i + 1 < n && (asc ? f.a[i + 1] < a : f.a[i + 1] > a)) i++;
    var j = Math.min(i + 1, n - 1), t = j === i || f.a[j] === f.a[i] ? 0 : Math.min(1, Math.max(0, (a - f.a[i]) / (f.a[j] - f.a[i])));
    var mix = function (u, v) { return u + t * (v - u); };
    return { box: [mix(f.box[i][0], f.box[j][0]), mix(f.box[i][1], f.box[j][1])],
             squares: f.squares[i].map(function (q, m) { var r = f.squares[j][m]; return [mix(q[0], r[0]), mix(q[1], r[1]), mix(q[2], r[2])]; }) };
  }
  var showCert = true;   // the packing panel shows the certificate (after a certificate button) or the family at the slider
  function showPiece(p, k) {
    o.playp.href = 'rect-player.html#' + k + '-' + p.key; o.playp.hidden = false;
    o.key.textContent = p.key + (p.name ? '  (' + p.name + ')' : '');
    o.f.innerHTML = p.formula ? fml(p.formula) + (p.param ? '<br><span class="dim">' + esc(p.param[ja() ? 'ja' : 'en'] || '') + '</span>' : '')
                              : '<span class="dim">' + (p.note ? esc(p.note[ja() ? 'ja' : 'en']) : (ja() ? '閉じた式は載せていない' : 'no closed form shown')) + '</span>' + full(p, 'side'); o.range.textContent = p.a_text;
    bindFull(o.f, p); if (ffOpen && ffOpen !== p) { ffOpen = null; o.ffw.hidden = true; o.ffw.innerHTML = ''; }
    o.src.textContent = SRC[p.source][ja() ? 1 : 0] + (p.friedman ? ' (Friedman ' + p.friedman.join(', ') + ')' : '');
    o.basis.textContent = p.basis[ja() ? 'ja' : 'en'];
    point(p);
    o.st.innerHTML = p.status.length ? p.status.map(function (s) {
      return '<span class="st' + (s.kind === 'proved' ? ' ex' : '') + '">' + KIND[s.kind][ja() ? 1 : 0] + '</span> ' + (p.status.length > 1 ? s.key + ': ' : '') + esc(s[ja() ? 'ja' : 'en']);
    }).join('<br>') : '–';
    // one button per certified packing of the piece; choosing one also moves the a slider to its a
    var wi = Math.min(sel.w, Math.max(0, p.witnesses.length - 1));
    o.wbar.innerHTML = p.witnesses.length > 0 ? p.witnesses.map(function (w, j) {
      return '<button type="button" data-w="' + j + '" aria-pressed="' + (j === wi) + '">a = ' + parseFloat(w.a.toPrecision(10)) + '</button>'; }).join('') : '';
    o.wbar.querySelectorAll('[data-w]').forEach(function (b) {
      b.addEventListener('click', function () {
        sel.w = +b.dataset.w; showCert = true; var w = p.witnesses[sel.w]; at = [w.b, w.a];
        info(); draw();
      });
    });
    var fa = !showCert && at ? familyAt(p, at[1]) : null;
    if (fa) {
      pc.hidden = false; squares(fa, sideW());
      o.pk.textContent = (ja() ? k + ' 個、長方形 ' : k + ' squares in ') + fa.box[0].toFixed(6) + ' × ' + fa.box[1].toFixed(6)
        + (ja() ? ' — 配置の族を補間した図（証明書ではない）' : ' — interpolated from the sampled family (an illustration, not a certificate)');
      o.wbar.querySelectorAll('[data-w]').forEach(function (b) { b.setAttribute('aria-pressed', 'false'); });
      return;
    }
    var wt = p.witnesses[wi];
    if (wt) { pc.hidden = false; squares(wt, sideW(), at);
      o.pk.textContent = (ja() ? k + ' 個、長方形 ' : k + ' squares in ') + wt.box[0].toFixed(6) + ' × ' + wt.box[1].toFixed(6) + ' — ' + wt.check
        + (at && (Math.abs(at[0] - wt.b) > 1e-9 || Math.abs(at[1] - wt.a) > 1e-9) ? (ja() ? '。破線：グラフ上の点の長方形 ' : '. Dashed: the rectangle at the point on the plot ') + at[0].toFixed(6) + ' × ' + at[1].toFixed(6) : ''); }
    else {
      // a step (a constant, b jumps) has no certified packing of its own: show the packing of the neighbouring piece at
      // the same a, the next piece's start (it fits every b on the step) or else the previous piece's end
      var KK = R.ks.filter(function (x) { return x.k === k; })[0], i = KK.pieces.indexOf(p), nb = null, side = '';
      [[KK.pieces[i + 1], 'next'], [KK.pieces[i - 1], 'prev']].some(function (c) {
        var q = c[0]; if (!q) return false;
        var w = q.witnesses.filter(function (w) { return Math.abs(w.a - p.a0) < 1e-6; })[0];
        var f = w || familyAt(q, p.a0); if (!f) return false;
        nb = { q: q, f: f, cert: !!w }; side = c[1]; return true;
      });
      if (nb) {
        pc.hidden = false; squares(nb.f, sideW(), at);
        o.pk.textContent = (ja() ? '段：' + (side === 'next' ? '次' : '前') + 'の片 ' + nb.q.key + ' の a = ' + p.a0.toFixed(6) + ' での配置（長方形 ' : 'Step: the packing of the ' + (side === 'next' ? 'next' : 'previous') + ' piece ' + nb.q.key + ' at a = ' + p.a0.toFixed(6) + ' (')
          + nb.f.box[0].toFixed(6) + ' × ' + nb.f.box[1].toFixed(6) + (nb.cert ? (ja() ? '、証明書）' : ', certified)') : (ja() ? '、配置の族からの図で証明書ではない）' : ', from the sampled family, not a certificate)'));
      } else { pc.hidden = true; o.pk.textContent = ja() ? '（証明書の配置なし）' : '(no certified packing for this piece)'; }
    }
  }
  function info() {
    // All, and a cell with no piece chosen: only the colour legend of k; the piece panel is for a chosen piece
    var none = (ALL && !CELL) || (CELL && !CSEL);
    o.ctl.hidden = ALL || !!CELL;
    o.pside.hidden = none; o.leg.hidden = !(CELL && !CSEL); o.zoom.hidden = !(ALL && !CELL); o.ptab.hidden = ALL && !CELL;
    if (ALL && !CELL) { if (!hov) zc.hidden = true; return; }
    if (none) {
      var ks = CELL ? R.ks.filter(function (KK) { return KK.pieces.some(function (p) { return throughCell(p, CELL[0], CELL[1]); }); }) : R.ks;
      o.leg.innerHTML = ks.map(function (KK) { return '<span style="color:' + kcol(KK.k) + '">■</span> ' + KK.k; }).join('  ') || '–';
      return;
    }
    if (CELL && CSEL) {
      var KK = R.ks.filter(function (x) { return x.k === CSEL.k; })[0], pp = KK.pieces.filter(function (x) { return x.key === CSEL.key; })[0];
      showPiece(pp, KK.k);
      tb.querySelectorAll('tr').forEach(function (tr) { tr.classList.toggle('on', tr.dataset.key === CSEL.key && +tr.dataset.k === CSEL.k); });
      return;
    }
    if (CELL) {
      ['key', 'range', 'f', 'src', 'basis', 'st'].forEach(function (k) { o[k].textContent = '–'; });
      var ks = R.ks.filter(function (KK) { return KK.pieces.some(function (p) { return throughCell(p, CELL[0], CELL[1]); }); });
      pc.hidden = true; o.pk.innerHTML = ks.map(function (KK) { return '<span style="color:' + kcol(KK.k) + '">■</span> ' + KK.k; }).join('  ') || '–';
      return;
    }
    if (ALL) {
      ['key', 'range', 'f', 'src', 'basis', 'st'].forEach(function (k) { o[k].textContent = '–'; });
      pc.hidden = true; o.pk.innerHTML = R.ks.map(function (KK) { return '<span style="color:' + kcol(KK.k) + '">■</span> ' + KK.k; }).join('  ');
      return;
    }
    var p = piece(sel.key); if (!p) return;
    showPiece(p, K.k);
    tb.querySelectorAll('tr').forEach(function (tr) { tr.classList.toggle('on', tr.dataset.key === sel.key); });
  }
  function cellTable() {
    var rows = [];
    R.ks.forEach(function (KK) {
      KK.pieces.forEach(function (p) {
        if (!throughCell(p, CELL[0], CELL[1])) return;
        rows.push('<tr class="r" data-k="' + KK.k + '" data-key="' + p.key + '"><td class="num"><span style="color:' + kcol(KK.k) + '">■</span> ' + p.key + (p.name ? ' (' + esc(p.name) + ')' : '') + '</td><td class="num">' + esc(p.a_text) + '</td><td class="nw">'
          + (p.status.map(function (st) { return '<span class="st' + (st.kind === 'proved' ? ' ex' : '') + '">' + KIND[st.kind][ja() ? 1 : 0] + '</span>'; }).join(' ') || '–') + '</td><td class="num fw">'
          + (p.formula ? fml(p.formula) : '<span class="dim">' + esc(p.note ? p.note[ja() ? 'ja' : 'en'] : '–') + '</span>' + full(p, 'row')) + '</td><td>' + esc(p.basis[ja() ? 'ja' : 'en']) + '</td></tr>');
      });
    });
    tb.innerHTML = rows.join('') || '<tr><td colspan="5" class="dim">' + (ja() ? 'このマスを通る端はない' : 'no edge passes through this cell') + '</td></tr>';
    // a row opens its k with that piece selected, and shows the piece on the plot
    tb.querySelectorAll('tr[data-k]').forEach(function (tr) {
      var KK = R.ks.filter(function (x) { return x.k === +tr.dataset.k; })[0];
      bindFull(tr, KK.pieces.filter(function (x) { return x.key === tr.dataset.key; })[0]);
      tr.addEventListener('click', function (e) {
        if (e.target.closest('a.fft')) return; CSEL = { k: +tr.dataset.k, key: tr.dataset.key }; sel.w = 0; at = null; showCert = true; info(); draw(); });
    });
  }
  function table() {
    tb.innerHTML = '';
    K.pieces.forEach(function (p) {
      var tr = document.createElement('tr'); tr.className = 'r'; tr.dataset.key = p.key;
      var st = p.status.map(function (s) { return '<span class="st' + (s.kind === 'proved' ? ' ex' : '') + '">' + KIND[s.kind][ja() ? 1 : 0] + '</span>'; }).join(' ');
      tr.innerHTML = '<td class="num">' + p.key + '</td><td class="num">' + esc(p.a_text) + '</td><td class="nw">' + (st || '–') + '</td><td class="num fw">' + (p.formula ? fml(p.formula) : '<span class="dim">' + esc(p.note ? p.note[ja() ? 'ja' : 'en'] : '–') + '</span>' + full(p, 'row')) + '</td><td>' + esc(p.basis[ja() ? 'ja' : 'en']) + '</td>';
      tr.addEventListener('click', function (e) { if (e.target.closest('a.fft')) return; sel.key = p.key; sel.w = 0; at = null; showCert = true; info(); draw(); });
      bindFull(tr, p);
      tb.appendChild(tr);
    });
  }
  function choose(k) {
    if (typeof stopRun === 'function') stopRun();
    document.querySelectorAll('[data-sel]').forEach(function (b) { b.setAttribute('aria-pressed', b.dataset.sel === String(k)); });
    CELL = null;
    if (typeof k === 'string' && k.indexOf('cell-') === 0) {
      var m = k.split('-'); CELL = [+m[1], +m[2]]; ALL = false; cur = k; CSEL = null;
      document.querySelectorAll('[data-sel]').forEach(function (b) { b.setAttribute('aria-pressed', b.dataset.sel === 'all'); });
      o.rh.innerHTML = (ja() ? 'マス b ∈ [' : 'Cell b ∈ [') + CELL[0] + ', ' + (CELL[0] + 1) + '], a ∈ [' + CELL[1] + ', ' + (CELL[1] + 1) + ']'
        + ' <a href="#all" data-back class="btn">' + (ja() ? 'すべてに戻る' : 'back to All') + '</a>';
      o.rh.querySelector('[data-back]').addEventListener('click', function (e) { e.preventDefault(); cur = 'all'; settle(); });
      cellTable(); info(); draw();
      try { history.replaceState(null, '', '#' + k); } catch (e) {}
      return;
    }
    ALL = k === 'all'; cur = k;
    if (ALL) {
      o.rh.innerHTML = ja() ? 'すべての k：k 個が入り始める端' : 'All k: where k squares begin to fit'; o.playp.hidden = true;
      tb.innerHTML = ''; info(); draw();
      try { history.replaceState(null, '', '#all'); } catch (e) {}
      return;
    }
    K = R.ks.filter(function (x) { return x.k === k; })[0];
    sel.key = K.pieces[0].key; sel.w = 0;
    o.rh.innerHTML = ja() ? k + ' 個が入り始める端' + (k <= 10 ? '（Friedman の表）' : '（当方の構成' + (K.status ? '、' + K.status.ja : '') + '）') + (k >= 16 ? '（preview）' : '')
                          : 'Where ' + k + ' squares begin to fit' + (k <= 10 ? " (Friedman's table)" : ' (our construction' + (K.status ? '; ' + K.status.en : '') + ')') + (k >= 16 ? ' (preview)' : '');
    table(); info(); draw();
    try { history.replaceState(null, '', '#' + k); } catch (e) {}
  }
  // keep the table in place: the upper block gets the height of its tallest state over every k, piece and witness
  function settle() {
    var g = root.querySelector('.cv-grid'), keep = [cur, sel.key, sel.w], m = 0, tallest = null;
    var keepAt = at;
    g.style.minHeight = ''; FIT = 1; choose(keep[0]);
    var height = function (key) { if (key) { sel.key = key; sel.w = 0; at = null; } info(); draw(); return g.offsetHeight; };
    if (typeof keep[0] === 'number') K.pieces.forEach(function (p) { var hh = height(p.key); if (hh > m) { m = hh; tallest = p.key; } });
    else m = height(null);
    // the pieces heading should start at 2/3 of the window height or above: shrink the figures to fit, down to half size
    var avail = window.innerHeight * 2 / 3 - (g.getBoundingClientRect().top + window.scrollY) - 24;
    for (var it = 0; it < 4 && m > avail && FIT > 0.5; it++) { FIT = Math.max(0.5, FIT * avail / m); m = height(tallest); }
    g.style.minHeight = m + 'px';
    // back to the piece shown before, if it belongs to this k; otherwise the first piece
    if (typeof keep[0] === 'number') { var kp = piece(keep[1]); sel.key = kp ? kp.key : K.pieces[0].key; sel.w = kp ? keep[2] : 0; at = kp ? keepAt : null; }
    info(); draw();
  }
  cv.addEventListener('click', function (ev) {
    var b = cv.getBoundingClientRect(), x = (ev.clientX - b.left) * geo.px, y = (ev.clientY - b.top) * geo.px;
    if (CELL) return;
    if (ALL) {   // move the magnified 1 x 1 window to centre on the click
      var unit = (geo.X(1) - geo.X(0)), xb = (x - geo.X(0)) / unit, ya = (geo.Y(0) - y) / unit;
      // the clicked grid cell [i, i+1] x [j, j+1]; only cells on or right of the diagonal (j <= i) can be chosen
      var i = Math.floor(xb), j = Math.floor(ya);
      if (i < 0 || j < 0 || j > i) return;
      cur = 'cell-' + i + '-' + j; settle();   // the cell replaces the plot, and the table lists its pieces
      return;
    }
  });
  // k view: press on the plot, or drag, to put the point on the nearest place of the edge; its piece becomes the selected
  // one and the packing panel follows the point (a certified packing when the point is on one, else the sampled family)
  function snap(ev) {
    var r = cv.getBoundingClientRect(), x = (ev.clientX - r.left) * geo.px, y = (ev.clientY - r.top) * geo.px, best = null, bd = 1e18;
    // the candidates: the pieces of k, or in a magnified cell the pieces of every k that pass through it
    var cands = [];
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
    if (!best) return;
    if (CELL) { if (!CSEL || CSEL.k !== best.k || CSEL.key !== best.p.key) { CSEL = { k: best.k, key: best.p.key }; sel.w = 0; } }
    else if (best.p.key !== sel.key) { sel.key = best.p.key; sel.w = 0; }
    at = [best.b, best.a];
    // on a certified packing (within a few pixels): show it; elsewhere the family, or the certificate if there is no family
    var wi = -1;
    best.p.witnesses.forEach(function (w, j) { if (Math.hypot(geo.X(w.b) - geo.X(at[0]), geo.Y(w.a) - geo.Y(at[1])) < 6 * geo.px) wi = j; });
    if (wi >= 0) { sel.w = wi; at = [best.p.witnesses[wi].b, best.p.witnesses[wi].a]; showCert = true; } else showCert = !best.p.family;
    info(); draw();
  }
  // the controls under the plot (k view): first / previous / next / last piece, and moving the point along the whole edge;
  // everything runs left to right on the plot, from the square (a = b) to the strip (b = k), the reverse of the piece order
  var run = null;   // { s: arc length so far, last: time of the last frame } while moving
  function order() { return K.pieces.slice().reverse(); }
  function pathOf() {   // the edge as one polyline in plot units, left to right, with the arc length at every point
    var out = [], L = 0;
    order().forEach(function (p) { p.pts.slice().reverse().forEach(function (q) {
      var prev = out[out.length - 1]; if (prev) L += Math.hypot(q[1] - prev.b, q[0] - prev.a);
      out.push({ p: p, a: q[0], b: q[1], s: L }); }); });
    return out;
  }
  function goPiece(i, where) {   // where: 'left' / 'right' end of the piece, or nothing for its first certified packing
    stopRun(); var P = order(), p = P[Math.max(0, Math.min(P.length - 1, i))];
    var q = where === 'left' ? p.pts[p.pts.length - 1] : where === 'right' ? p.pts[0] : null;
    sel.key = p.key; sel.w = 0; at = q ? [q[1], q[0]] : null; showCert = !q || !p.family; info(); draw();
  }
  var MOVE_ICON = null, PAUSE_ICON = '<svg viewBox="0 0 20 20" width="20" height="20" aria-hidden="true"><rect x="5" y="4" width="3.5" height="12"/><rect x="11.5" y="4" width="3.5" height="12"/></svg>';
  function stopRun() { var b = o.ctl.querySelector('[data-c="play"]'); if (!MOVE_ICON) MOVE_ICON = b.innerHTML; if (run) { run = null; b.innerHTML = MOVE_ICON; } }
  function frame(now) {
    if (!run) return;
    var P = run.path, dt = run.last ? (now - run.last) / 1000 : 0; run.last = now;
    run.s += dt * Math.max(0.8, P[P.length - 1].s / 25);   // the whole edge in about 25 s, at least 0.8 units a second
    if (run.s >= P[P.length - 1].s) { var e = P[P.length - 1]; sel.key = e.p.key; at = [e.b, e.a]; showCert = !e.p.family; info(); draw(); stopRun(); return; }
    var i = 0; while (i + 1 < P.length && P[i + 1].s < run.s) i++;
    var u = P[i], v = P[i + 1], f = v.s > u.s ? (run.s - u.s) / (v.s - u.s) : 0, pc = v.p === u.p ? u.p : (f < 0.5 ? u.p : v.p);
    if (pc.key !== sel.key) { sel.key = pc.key; sel.w = 0; }
    at = [u.b + f * (v.b - u.b), u.a + f * (v.a - u.a)]; showCert = !pc.family; info(); draw();
    requestAnimationFrame(frame);
  }
  o.ctl.querySelectorAll('[data-c]').forEach(function (b) {
    b.addEventListener('click', function () {
      if (!K || ALL || CELL) return;
      var i = order().indexOf(piece(sel.key)), c = b.dataset.c;
      if (c === 'first') goPiece(0, 'left'); else if (c === 'prev') goPiece(i - 1); else if (c === 'next') goPiece(i + 1); else if (c === 'last') goPiece(K.pieces.length - 1, 'right');
      else if (run) stopRun();
      else {   // from the current point, or from the start if the point is at the end
        var P = pathOf(), s0 = 0, bd = 1e18;
        if (at) P.forEach(function (q) { var d = Math.hypot(q.b - at[0], q.a - at[1]); if (d < bd) { bd = d; s0 = q.s; } });
        if (s0 >= P[P.length - 1].s - 1e-9) s0 = 0;
        if (!MOVE_ICON) MOVE_ICON = b.innerHTML; run = { path: P, s: s0, last: 0 }; b.innerHTML = PAUSE_ICON; requestAnimationFrame(frame);
      }
    });
  });
  var dragging = false;
  cv.addEventListener('pointerdown', function (ev) { if ((ALL && !CELL) || (!CELL && !K)) return; stopRun(); dragging = true; cv.setPointerCapture(ev.pointerId); snap(ev); ev.preventDefault(); });
  cv.addEventListener('pointermove', function (ev) { if (dragging) snap(ev); });
  ['pointerup', 'pointercancel'].forEach(function (n) { cv.addEventListener(n, function () { dragging = false; }); });
  document.querySelectorAll('[data-sel]').forEach(function (b) { b.addEventListener('click', function () { cur = b.dataset.sel === 'all' ? 'all' : +b.dataset.sel; settle(); }); });
  document.addEventListener('langchange', function () { if (R) settle(); });
  new MutationObserver(function () { if (K) { info(); draw(); } }).observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme'] });
  var rt = null;
  window.addEventListener('resize', function () { if (R) { clearTimeout(rt); rt = setTimeout(settle, 150); } });
  fetch('data/rect-regions.json').then(function (r) { return r.json(); }).then(function (d) {
    R = d; var h = parseInt(location.hash.slice(1), 10);
    var hs = location.hash.slice(1), hp = /^(\d+)-([\d.]+)$/.exec(hs);   // #k-piece: open k with that piece selected
    cur = hs === 'all' || /^cell-\d+-\d+$/.test(hs) ? hs : R.ks.some(function (x) { return x.k === h; }) ? h : 5; settle();
    if (hp && typeof cur === 'number' && K && K.pieces.some(function (x) { return x.key === hp[2]; })) { sel.key = hp[2]; sel.w = 0; at = null; info(); draw(); }
  });
})();
