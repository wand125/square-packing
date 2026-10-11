// Non-square containers: the container, the optimal packing (when the source fixes it) and the certificate's
// weighted points; a movable unit square shows the weight of the points it contains (closed square).
(function () {
  'use strict';
  var root = document.getElementById('ct');
  if (!root) return;
  var cvs = root.querySelector('canvas'), ctx = cvs.getContext('2d'), aIn = root.querySelector('#ct-a'), keep = root.querySelector('#ct-keep');
  var out = {}; root.querySelectorAll('[data-o]').forEach(function (el) { out[el.dataset.o] = el; });
  // tolerance for points on the edge of the closed square (the browser computes in floating point)
  var EPS = 1e-9;
  var ALL = [], D = null, st = { x: 0, y: 0, a: 0 }, show = { pack: true, pts: true, sq: true };
  var px, S, ox, oy, pad = 10;
  function css(n) { return getComputedStyle(document.documentElement).getPropertyValue(n).trim(); }
  function L() { return SP.L(); }

  function bbox(P) {
    var xs = P.map(function (p) { return p[0]; }), ys = P.map(function (p) { return p[1]; });
    return [Math.min.apply(null, xs), Math.min.apply(null, ys), Math.max.apply(null, xs), Math.max.apply(null, ys)];
  }
  function size() {
    var w = Math.min(root.querySelector('.cv-fig').clientWidth, 620), b = bbox(D.poly), dpr = window.devicePixelRatio || 1;
    var sc = (w - 2 * pad) / Math.max(b[2] - b[0], b[3] - b[1]), hgt = (b[3] - b[1]) * sc + 2 * pad;
    cvs.style.width = w + 'px'; cvs.style.height = hgt + 'px'; cvs.width = Math.round(w * dpr); cvs.height = Math.round(hgt * dpr);
    px = dpr; S = sc; ox = pad + ((w - 2 * pad) - (b[2] - b[0]) * sc) / 2 - b[0] * sc; oy = pad + b[3] * sc;
  }
  function X(x) { return (ox + x * S) * px; }
  function Y(y) { return (oy - y * S) * px; }
  function path(P) { ctx.beginPath(); P.forEach(function (p, i) { i ? ctx.lineTo(X(p[0]), Y(p[1])) : ctx.moveTo(X(p[0]), Y(p[1])); }); ctx.closePath(); }
  function corners(x, y, a) {
    var c = Math.cos(a), s = Math.sin(a);
    return [[-.5, -.5], [.5, -.5], [.5, .5], [-.5, .5]].map(function (k) { return [x + k[0] * c - k[1] * s, y + k[0] * s + k[1] * c]; });
  }
  function inside(p) {
    var P = D.poly;
    for (var i = 0; i < P.length; i++) {
      var a = P[i], b = P[(i + 1) % P.length];
      if ((b[0] - a[0]) * (p[1] - a[1]) - (b[1] - a[1]) * (p[0] - a[0]) < -1e-9) return false;
    }
    return true;
  }
  // weight the closed square captures: points inside it, plus Lemma P for a pair at distance 1 whose chord crosses the
  // square between two opposite edges and meets the segment between the points (then the square contains one of them)
  function captured() {
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

  function draw() {
    if (!D) return;
    var acc = css('--acc'), fg2 = css('--fg2'), link = css('--link');
    ctx.clearRect(0, 0, cvs.width, cvs.height);
    path(D.poly); ctx.fillStyle = css('--bg2'); ctx.fill(); ctx.strokeStyle = css('--fg'); ctx.lineWidth = 1.2 * px; ctx.stroke();
    if (show.pack && D.packing) D.packing.forEach(function (q) {
      path(q); ctx.globalAlpha = 0.22; ctx.fillStyle = link; ctx.fill(); ctx.globalAlpha = 1;
      ctx.strokeStyle = link; ctx.lineWidth = px; ctx.stroke();
    });
    if (show.pts) {
      ctx.strokeStyle = fg2; ctx.lineWidth = px; ctx.setLineDash([3 * px, 3 * px]);
      D.pairs.forEach(function (pr) { var a = D.points[pr[0]], b = D.points[pr[1]]; ctx.beginPath(); ctx.moveTo(X(a[0]), Y(a[1])); ctx.lineTo(X(b[0]), Y(b[1])); ctx.stroke(); });
      ctx.setLineDash([]);
      var wmax = D.points.reduce(function (x, p) { return Math.max(x, p[2]); }, 0), rad = Math.min(5, 70 / Math.sqrt(D.points.length));
      ctx.fillStyle = acc;
      D.points.forEach(function (p) { ctx.beginPath(); ctx.arc(X(p[0]), Y(p[1]), Math.max(1, rad * Math.sqrt(p[2] / wmax)) * px, 0, 7); ctx.fill(); });
    }
    if (show.sq) {
      var Q = corners(st.x, st.y, st.a), ok = Q.every(inside), cm = captured();
      path(Q); ctx.strokeStyle = !ok ? fg2 : cm[0] >= 1 - 1e-9 ? css('--ok') : '#d9534f'; ctx.lineWidth = 2 * px;
      if (!ok) ctx.setLineDash([4 * px, 3 * px]); ctx.stroke(); ctx.setLineDash([]);
      out.c.textContent = '(' + st.x.toFixed(4) + ', ' + st.y.toFixed(4) + ')';
      out.a.textContent = (st.a * 180 / Math.PI).toFixed(2) + '°';
      out.m.textContent = cm[0].toFixed(6) + '  (' + cm[1] + (L() === 'ja' ? ' 点' : ' pts') + (cm[2] ? (L() === 'ja' ? '、補題 P で ' : ', Lemma P ') + cm[2] : '') + ')';
      out.fit.textContent = ok ? (L() === 'ja' ? '容器の中' : 'inside the container') : (L() === 'ja' ? '容器からはみ出す' : 'not inside the container');
    }
  }

  function bi(o) { return o ? (L() === 'ja' ? o.ja : o.en) : ''; }
  function select(i) {
    D = ALL[i];
    root.querySelectorAll('[data-i]').forEach(function (b) { b.setAttribute('aria-pressed', +b.dataset.i === i); });
    st.a = 0; aIn.value = 0;
    var c = centroid(); st.x = c[0]; st.y = c[1];
    // show only the notes, explanations and sources that concern this container and certificate
    root.querySelectorAll('[data-cont], [data-when]').forEach(function (el) {
      var on = (!el.dataset.cont || el.dataset.cont === D.cont) && (!el.dataset.n || +el.dataset.n === D.n) &&
        (!el.dataset.when || (el.dataset.when === 'pairs' ? D.pairs.length > 0 : !!D.stage));
      el.hidden = !on;
    });
    info(); size(); draw();
  }
  function info() {
    var f = {
      claim: D.claim, L: D.L.toFixed(9), pts: D.points.length + (D.pairs.length ? (L() === 'ja' ? '（組 ' : ' (') + D.pairs.length + (L() === 'ja' ? '）' : ' pairs)') : ''),
      w: D.weight + ' < ' + D.n, sym: D.symmetry, cert: D.cert + (D.stage ? ' — ' + bi(D.stage) : ''),
      pack: D.packing ? (L() === 'ja' ? '図に描いた（文書の記述で位置が決まる）' : 'drawn (the source fixes every square)') : bi(D.pnote)
    };
    Object.keys(f).forEach(function (k) { var el = root.querySelector('[data-f="' + k + '"]'); if (el) el.textContent = f[k]; });
    var docs = root.querySelector('[data-f="docs"]'); docs.innerHTML = '';
    D.docs.forEach(function (d) { var a = document.createElement('a'); a.href = root.dataset.blob + d; a.textContent = d.split('/').slice(-2).join('/'); docs.appendChild(a); });
  }
  function fits(x, y) { return corners(x, y, st.a).every(inside); }
  // a position where the square at the current angle fits, nearest to the centroid (grid search); the centroid if none
  function centroid() {
    var c = D.poly.reduce(function (a, p) { return [a[0] + p[0] / D.poly.length, a[1] + p[1] / D.poly.length]; }, [0, 0]);
    if (fits(c[0], c[1])) return c;
    var b = bbox(D.poly), best = null, bd = Infinity, n = 80;
    for (var i = 0; i <= n; i++) for (var j = 0; j <= n; j++) {
      var x = b[0] + (b[2] - b[0]) * i / n, y = b[1] + (b[3] - b[1]) * j / n, d = (x - c[0]) * (x - c[0]) + (y - c[1]) * (y - c[1]);
      if (d < bd && fits(x, y)) { bd = d; best = [x, y]; }
    }
    return best || c;
  }
  // centres where the square at the current angle fits: n·c >= k for each edge (inward normal n), a convex polygon
  function cons() {
    var P = D.poly, out = [], off = corners(0, 0, st.a);
    for (var i = 0; i < P.length; i++) {
      var A = P[i], B = P[(i + 1) % P.length], ex = B[0] - A[0], ey = B[1] - A[1], l = Math.hypot(ex, ey), n = [-ey / l, ex / l];
      var m = Math.min.apply(null, off.map(function (v) { return n[0] * v[0] + n[1] * v[1]; }));
      out.push([n[0], n[1], n[0] * A[0] + n[1] * A[1] - m]);
    }
    return out;
  }
  // nearest centre to (x, y) where the square fits: the point itself, a projection on one constraint line, or a corner
  function project(x, y) {
    var C = cons(), ok = function (p) { return C.every(function (c) { return c[0] * p[0] + c[1] * p[1] >= c[2] - 1e-9; }); };
    if (ok([x, y])) return [x, y];
    var best = null, bd = Infinity;
    function take(p) { var d = (p[0] - x) * (p[0] - x) + (p[1] - y) * (p[1] - y); if (d < bd && ok(p)) { bd = d; best = p; } }
    C.forEach(function (c) { var t = c[0] * x + c[1] * y - c[2]; take([x - t * c[0], y - t * c[1]]); });
    for (var i = 0; i < C.length; i++) for (var j = i + 1; j < C.length; j++) {
      var a = C[i], b = C[j], det = a[0] * b[1] - a[1] * b[0];
      if (Math.abs(det) > 1e-12) take([(a[2] * b[1] - a[1] * b[2]) / det, (a[0] * b[2] - a[2] * b[0]) / det]);
    }
    return best;   // null when no position fits at this angle
  }
  function pick(ev) {
    var b = cvs.getBoundingClientRect(), x = ((ev.clientX - b.left) - ox) / S, y = (oy - (ev.clientY - b.top)) / S;
    if (keep.checked) { var q = project(x, y); if (!q) return; x = q[0]; y = q[1]; }
    st.x = x; st.y = y; draw();
  }
  var drag = false;
  cvs.addEventListener('pointerdown', function (ev) { drag = true; cvs.setPointerCapture(ev.pointerId); pick(ev); });
  cvs.addEventListener('pointermove', function (ev) { if (drag) pick(ev); });
  ['pointerup', 'pointercancel', 'lostpointercapture'].forEach(function (t) { cvs.addEventListener(t, function () { drag = false; }); });
  aIn.addEventListener('input', function () {
    // snap to multiples of 15° within 1.5° (the container edges meet at multiples of 15°: 45°, 60°, 120°, 90°)
    var deg = +aIn.value, sn = Math.round(deg / 15) * 15;
    if (Math.abs(deg - sn) <= 1.5) { deg = sn; aIn.value = sn; }
    var a0 = st.a; st.a = deg * Math.PI / 180;
    if (keep.checked) { var q = project(st.x, st.y); if (q) { st.x = q[0]; st.y = q[1]; } else st.a = a0; }
    draw();
  });
  keep.addEventListener('change', function () { if (keep.checked) { var q = project(st.x, st.y); if (q) { st.x = q[0]; st.y = q[1]; draw(); } } });
  root.querySelectorAll('[data-show]').forEach(function (c) { c.addEventListener('change', function () { show[c.dataset.show] = c.checked; draw(); }); });
  document.addEventListener('langchange', function () { if (D) { info(); draw(); } });
  new MutationObserver(draw).observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme'] });
  window.addEventListener('resize', function () { if (D) { size(); draw(); } });
  fetch('data/containers.json').then(function (r) { return r.json(); }).then(function (d) {
    ALL = d;
    var bar = root.querySelector('.ct-pick');
    var NAMES = JSON.parse(root.dataset.names);
    Object.keys(NAMES).forEach(function (cont) {
      var g = document.createElement('div'); g.className = 'bar';
      var lab = document.createElement('span'); lab.className = 'dim ct-lab'; lab.innerHTML = NAMES[cont]; g.appendChild(lab);
      ALL.forEach(function (it, i) {
        if (it.cont !== cont) return;
        var b = document.createElement('button'); b.type = 'button'; b.dataset.i = i; b.textContent = it.n;
        b.addEventListener('click', function () { select(i); }); g.appendChild(b);
      });
      bar.appendChild(g);
    });
    var h = location.hash.slice(1), at = ALL.findIndex(function (it) { return it.cont + '-' + it.n === h; });
    select(at < 0 ? 0 : at);
  });
})();
