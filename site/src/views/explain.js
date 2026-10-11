// Explanation page: the net lemma, the branch and bound over centres, and the band insertion of the k^2 - c lift.
(function () {
  'use strict';
  function css(n) { return getComputedStyle(document.documentElement).getPropertyValue(n).trim(); }
  function L() { return document.documentElement.lang; }
  function canvas(c, w, h) {
    var dpr = window.devicePixelRatio || 1;
    c.style.width = w + 'px'; c.style.height = h + 'px'; c.width = Math.round(w * dpr); c.height = Math.round(h * dpr);
    return dpr;
  }
  function frac(s) { var p = String(s).split('/'); return p.length > 1 ? +p[0] / +p[1] : +p[0]; }
  var redraw = [];
  new MutationObserver(function () { redraw.forEach(function (f) { f(); }); }).observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme'] });
  document.addEventListener('langchange', function () { redraw.forEach(function (f) { f(); }); });

  // ---- A. net lemma: B = 9977/10000, t_r = 83 r / 40000 (lower-bounds.md §3)
  (function () {
    var root = document.getElementById('ex-net'); if (!root) return;
    var B = 9977 / 10000, D = 83 / 40000, cv = root.querySelector('canvas'), ctx = cv.getContext('2d'), inp = root.querySelector('input');
    var o = {}; root.querySelectorAll('[data-o]').forEach(function (el) { o[el.dataset.o] = el; });
    function draw() {
      var w = Math.min(root.querySelector('.cv-fig').clientWidth, 520), px = canvas(cv, w, w * 0.62), W = cv.width, H = cv.height;
      var a = +inp.value * Math.PI / 180, t = Math.tan(a / 2), r = Math.round(t / D), th = 2 * Math.atan(r * D), d = a - th;
      var reach = B / 2 * (Math.cos(d) + Math.abs(Math.sin(d)));
      ctx.clearRect(0, 0, W, H);
      // left: unit square at angle a and the core at angle th, same centre
      var s = H * 0.36, cx = W * 0.27, cy = H / 2;
      function sq(side, ang, col, lw) {
        var c = Math.cos(ang), sn = Math.sin(ang), h = side / 2;
        ctx.beginPath();
        [[1, 1], [-1, 1], [-1, -1], [1, -1]].forEach(function (k, i) {
          var x = cx + 2 * s * h * (k[0] * c - k[1] * sn), y = cy - 2 * s * h * (k[0] * sn + k[1] * c);
          i ? ctx.lineTo(x, y) : ctx.moveTo(x, y);
        });
        ctx.closePath(); ctx.strokeStyle = col; ctx.lineWidth = lw * px; ctx.stroke();
      }
      sq(1, a, css('--fg2'), 1); sq(B, th, css('--ok'), 1.5);
      // right: the corner region in the unit square's own frame, magnified
      var M = 400, bx = W * 0.56, by = H * 0.1, bw = W * 0.4, bh = H * 0.8;
      ctx.save(); ctx.beginPath(); ctx.rect(bx, by, bw, bh); ctx.clip();
      ctx.fillStyle = css('--bg2'); ctx.fillRect(bx, by, bw, bh);
      var fx = bx + bw * 0.75, fy = by + bh * 0.25;      // the corner (1/2, 1/2) of the unit square
      function P(x, y) { return [fx + (x - 0.5) * 2 * s * M, fy - (y - 0.5) * 2 * s * M]; }
      ctx.strokeStyle = css('--fg2'); ctx.lineWidth = 1.5 * px; ctx.beginPath();
      var p0 = P(-1, 0.5), p1 = P(0.5, 0.5), p2 = P(0.5, -1); ctx.moveTo(p0[0], p0[1]); ctx.lineTo(p1[0], p1[1]); ctx.lineTo(p2[0], p2[1]); ctx.stroke();
      var c = Math.cos(-d), sn = Math.sin(-d), h = B / 2;
      ctx.strokeStyle = css('--ok'); ctx.beginPath();
      [[-1, 1], [1, 1], [1, -1]].forEach(function (k, i) {
        var q = P(h * (k[0] * c - k[1] * sn), h * (k[0] * sn + k[1] * c)); i ? ctx.lineTo(q[0], q[1]) : ctx.moveTo(q[0], q[1]);
      });
      ctx.stroke(); ctx.restore();
      ctx.strokeStyle = css('--line'); ctx.lineWidth = px; ctx.strokeRect(bx, by, bw, bh);
      ctx.fillStyle = css('--fg2'); ctx.font = (11 * px) + 'px ' + css('--mono');
      ctx.fillText('×' + M, bx + 6 * px, by + bh - 6 * px);
      o.r.textContent = r; o.th.textContent = (th * 180 / Math.PI).toFixed(5) + '°';
      o.d.textContent = (d * 180 / Math.PI).toFixed(5) + '°  (tan |d| = ' + Math.abs(Math.tan(d)).toFixed(6) + ' ≤ ' + D + ')';
      o.reach.textContent = reach.toFixed(7) + ' < 0.5';
    }
    inp.addEventListener('input', draw); window.addEventListener('resize', draw); redraw.push(draw); draw();
  })();

  // ---- B. branch and bound over centres for one net direction (lower-bounds.md §4), on cert_n29_L557
  (function () {
    var root = document.getElementById('ex-bb'); if (!root) return;
    var cv = root.querySelector('canvas'), ctx = cv.getContext('2d'), rIn = root.querySelector('input'), run = root.querySelector('button');
    var o = {}; root.querySelectorAll('[data-o]').forEach(function (el) { o[el.dataset.o] = el; });
    var C = null, grid = null, G = 0.5, boxes = [], job = null, stats = null, finished = false, px, S, pad = 8;
    fetch('data/cert-point-n29.json').then(function (r) { return r.json(); }).then(function (d) {
      C = d; C.L = frac(d.L); C.B = frac(d.B); C.D = frac(d.step);
      var n = Math.ceil(C.L / G); grid = []; for (var i = 0; i < n * n; i++) grid.push([]);
      d.atoms.forEach(function (a) { grid[Math.min(n - 1, a[0] / G | 0) * n + Math.min(n - 1, a[1] / G | 0)].push(a); });
      grid.n = n; start();
    });
    function near(x0, y0, x1, y1) {
      var n = grid.n, out = [], i0 = Math.max(0, x0 / G | 0), i1 = Math.min(n - 1, x1 / G | 0), j0 = Math.max(0, y0 / G | 0), j1 = Math.min(n - 1, y1 / G | 0);
      for (var i = i0; i <= i1; i++) for (var j = j0; j <= j1; j++) out.push.apply(out, grid[i * n + j]);
      return out;
    }
    // atoms covered by the core for every centre in the box: test the four corners (the conditions are linear in the centre)
    function covered(b, c, s) {
      var h = C.B / 2, e = h * (c + s), m = 0;
      var cand = near(b[2] - e, b[3] - e, b[0] + e, b[1] + e);
      for (var k = 0; k < cand.length; k++) {
        var a = cand[k], ok = true;
        for (var q = 0; q < 4 && ok; q++) {
          var x = q & 1 ? b[2] : b[0], y = q & 2 ? b[3] : b[1], dx = a[0] - x, dy = a[1] - y;
          if (Math.abs(dx * c + dy * s) > h || Math.abs(-dx * s + dy * c) > h) ok = false;
        }
        if (ok) m += a[2];
      }
      return m;
    }
    function start() {
      if (!C) return;
      var r = +rIn.value, th = 2 * Math.atan(r * C.D), c = Math.cos(th), s = Math.sin(th), h = (c + s) / 2;
      var stack = [[h, h, C.L - h, C.L - h, 0]];
      finished = false; boxes = []; stats = { seen: 0, done: 0, fail: 0, depth: 0, min: Infinity };
      var me = job = {};
      (function step() {
        if (job !== me) return;
        var k = 0;   // a few hundred boxes per frame, so the subdivision can be watched
        while (stack.length && k++ < 300) {
          var b = stack.pop(); stats.seen++;
          var m = covered(b, c, s);
          if (m >= 1 + 1e-9) { boxes.push(b); stats.done++; stats.depth = Math.max(stats.depth, b[4]); stats.min = Math.min(stats.min, Math.max(b[2] - b[0], b[3] - b[1])); continue; }
          if (Math.max(b[2] - b[0], b[3] - b[1]) < 1e-7) { stats.fail++; boxes.push(b.concat([1])); continue; }
          if (b[2] - b[0] >= b[3] - b[1]) { var xm = (b[0] + b[2]) / 2; stack.push([b[0], b[1], xm, b[3], b[4] + 1], [xm, b[1], b[2], b[3], b[4] + 1]); }
          else { var ym = (b[1] + b[3]) / 2; stack.push([b[0], b[1], b[2], ym, b[4] + 1], [b[0], ym, b[2], b[3], b[4] + 1]); }
        }
        draw(stack.length === 0);
        if (stack.length && job === me) requestAnimationFrame(step);
      })();
    }
    function draw(fin = finished) {
      finished = fin;
      if (!C) return;
      var w = Math.min(root.querySelector('.cv-fig').clientWidth, 560); px = canvas(cv, w, w); S = (w - 2 * pad) / C.L;
      ctx.clearRect(0, 0, cv.width, cv.height);
      var X = function (x) { return (pad + x * S) * px; }, Y = function (y) { return (pad + (C.L - y) * S) * px; };
      ctx.fillStyle = css('--bg2'); ctx.fillRect(X(0), Y(C.L), C.L * S * px, C.L * S * px);
      var ok = css('--ok'), dmax = Math.max(1, stats.depth);
      boxes.forEach(function (b) {
        ctx.fillStyle = b[5] ? '#d9534f' : ok; ctx.globalAlpha = b[5] ? 0.9 : 0.12 + 0.6 * b[4] / dmax;
        ctx.fillRect(X(b[0]), Y(b[3]), Math.max(px * 0.5, (b[2] - b[0]) * S * px), Math.max(px * 0.5, (b[3] - b[1]) * S * px));
      });
      ctx.globalAlpha = 1; ctx.fillStyle = css('--acc');
      C.atoms.forEach(function (a) { ctx.beginPath(); ctx.arc(X(a[0]), Y(a[1]), 1.1 * px, 0, 7); ctx.fill(); });
      ctx.strokeStyle = css('--line'); ctx.lineWidth = px; ctx.strokeRect(X(0), Y(C.L), C.L * S * px, C.L * S * px);
      var r = +rIn.value;
      o.r.textContent = r + ' / 200  (θ = ' + (2 * Math.atan(r * C.D) * 180 / Math.PI).toFixed(4) + '°)';
      o.seen.textContent = stats.seen.toLocaleString('en');
      o.done.textContent = stats.done.toLocaleString('en');
      o.fail.textContent = stats.fail;
      o.depth.textContent = stats.depth + (isFinite(stats.min) ? '  (' + stats.min.toExponential(2) + ')' : '');
      o.state.textContent = fin ? (L() === 'ja' ? '完了' : 'finished') : (L() === 'ja' ? '実行中' : 'running');
    }
    rIn.addEventListener('input', function () { o.r.textContent = rIn.value; });
    run.addEventListener('click', start); window.addEventListener('resize', function () { if (stats) draw(); }); redraw.push(function () { if (stats) draw(); });
  })();

  // ---- C. the k^2 - c lift: s(77) cover with the inserted cross-shaped band
  (function () {
    var root = document.getElementById('ex-lift'); if (!root) return;
    var cv = root.querySelector('canvas'), ctx = cv.getContext('2d'), band = root.querySelector('input'), C = null;
    fetch('data/cert-lift-n77.json').then(function (r) { return r.json(); }).then(function (d) { C = d; C.L = frac(d.L); draw(); });
    function draw() {
      if (!C) return;
      var w = Math.min(root.querySelector('.cv-fig').clientWidth, 560), px = canvas(cv, w, w), pad = 8, S = (w - 2 * pad) / C.L;
      var X = function (x) { return (pad + x * S) * px; }, Y = function (y) { return (pad + (C.L - y) * S) * px; };
      ctx.clearRect(0, 0, cv.width, cv.height);
      ctx.fillStyle = css('--bg2'); ctx.fillRect(X(0), Y(C.L), C.L * S * px, C.L * S * px);
      if (band.checked) {
        ctx.fillStyle = css('--link'); ctx.globalAlpha = 0.16;
        ctx.fillRect(X(4), Y(9), S * px, 9 * S * px); ctx.fillRect(X(0), Y(5), 9 * S * px, S * px); ctx.globalAlpha = 1;
      }
      ctx.strokeStyle = css('--link'); ctx.lineWidth = px;
      C.segs.forEach(function (g) { ctx.beginPath(); ctx.moveTo(X(g[0]), Y(g[1])); ctx.lineTo(X(g[2]), Y(g[3])); ctx.stroke(); });
      var wmax = C.atoms.reduce(function (x, a) { return Math.max(x, a[2]); }, 0);
      ctx.fillStyle = css('--acc');
      C.atoms.forEach(function (a) { ctx.beginPath(); ctx.arc(X(a[0]), Y(a[1]), Math.max(0.5, 2.2 * Math.sqrt(a[2] / wmax)) * px, 0, 7); ctx.fill(); });
      ctx.strokeStyle = css('--line'); ctx.strokeRect(X(0), Y(C.L), C.L * S * px, C.L * S * px);
    }
    band.addEventListener('change', draw); window.addEventListener('resize', draw); redraw.push(draw);
  })();
})();
