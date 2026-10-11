// Certificate viewer: draws a published measure on [0, L]^2 and the mass captured by a core square of side B
// at a net direction. Floating point, for viewing; the certificate's own checker decides validity.
(function () {
  'use strict';
  var root = document.getElementById('cv');
  if (!root) return;
  var cvs = root.querySelector('canvas.m'), ctx = cvs.getContext('2d');
  var strip = root.querySelector('canvas.strip'), sctx = strip.getContext('2d');
  var rIn = root.querySelector('#cv-r'), keep = root.querySelector('#cv-keep'), out = {};
  root.querySelectorAll('[data-o]').forEach(function (el) { out[el.dataset.o] = el; });
  var VERS = JSON.parse(root.dataset.versions), verSel = root.querySelector('#cv-ver');
  var KINDN = { point: 'points', lift: 'points + segments', rect: 'rectangles', mixed: 'mixed' };
  var D = null, st = { r: 0, cx: 0, cy: 0, scan: null, scanR: -1 }, cache = {};

  function frac(s) { s = String(s); var p = s.split('/'); return p.length > 1 ? +p[0] / +p[1] : +s; }
  function css(n) { return getComputedStyle(document.documentElement).getPropertyValue(n).trim(); }
  // net certificates: theta_r = 2 atan(r * step); certificates for every angle: r in hundredths of a degree
  function ang(r) { return D.step ? 2 * Math.atan(r * D.step) : r * Math.PI / 18000; }
  function half(th) { return (Math.cos(th) + Math.sin(th)) / 2; }   // half-width of a unit square at angle th

  // mass of the measure inside the closed core square (centre cx, cy; side B; angle th)
  function mass(cx, cy, th) {
    var c = Math.cos(th), s = Math.sin(th), h = D.B / 2, m = 0, i;
    if (D.atoms) {
      for (i = 0; i < D.atoms.length; i++) {
        var a = D.atoms[i], dx = a[0] - cx, dy = a[1] - cy;
        if (Math.abs(dx * c + dy * s) <= h + 1e-9 && Math.abs(-dx * s + dy * c) <= h + 1e-9) m += a[2];
      }
    }
    if (D.segs) for (i = 0; i < D.segs.length; i++) m += D.segs[i][4] * segFrac(D.segs[i], cx, cy, c, s, h);
    if (!D.rects) return m;
    var P = [[cx + h * (c - s), cy + h * (s + c)], [cx + h * (-c - s), cy + h * (-s + c)],
             [cx + h * (-c + s), cy + h * (-s - c)], [cx + h * (c + s), cy + h * (s - c)]];
    var e = h * (Math.abs(c) + Math.abs(s));
    for (i = 0; i < D.rects.length; i++) {
      var R = D.rects[i];
      if (R[2] <= cx - e || R[0] >= cx + e || R[3] <= cy - e || R[1] >= cy + e) continue;
      m += R[4] * clipArea(P, R);
    }
    return m;
  }
  // fraction of a segment's length inside the closed square (uniform mass along the segment)
  function segFrac(g, cx, cy, c, s, h) {
    var ax = g[0] - cx, ay = g[1] - cy, bx = g[2] - cx, by = g[3] - cy;
    var u0 = ax * c + ay * s, v0 = -ax * s + ay * c, u1 = bx * c + by * s, v1 = -bx * s + by * c, t0 = 0, t1 = 1;
    [[u0, u1], [v0, v1]].forEach(function (q) {
      var p0 = q[0], d = q[1] - q[0];
      if (Math.abs(d) < 1e-15) { if (Math.abs(p0) > h + 1e-9) t1 = -1; return; }
      var a = (-h - 1e-9 - p0) / d, b = (h + 1e-9 - p0) / d;
      if (a > b) { var x = a; a = b; b = x; }
      t0 = Math.max(t0, a); t1 = Math.min(t1, b);
    });
    return t1 > t0 ? t1 - t0 : 0;
  }
  function clipArea(P, R) {
    var poly = P;
    poly = clip(poly, function (p) { return p[0] - R[0]; });
    poly = clip(poly, function (p) { return R[2] - p[0]; });
    poly = clip(poly, function (p) { return p[1] - R[1]; });
    poly = clip(poly, function (p) { return R[3] - p[1]; });
    var a = 0;
    for (var i = 0; i < poly.length; i++) { var p = poly[i], q = poly[(i + 1) % poly.length]; a += p[0] * q[1] - q[0] * p[1]; }
    return Math.abs(a) / 2;
  }
  function clip(poly, f) {
    var o = [];
    for (var i = 0; i < poly.length; i++) {
      var p = poly[i], q = poly[(i + 1) % poly.length], fp = f(p), fq = f(q);
      if (fp >= 0) o.push(p);
      if ((fp >= 0) !== (fq >= 0)) { var t = fp / (fp - fq); o.push([p[0] + t * (q[0] - p[0]), p[1] + t * (q[1] - p[1])]); }
    }
    return o;
  }

  var px, S, pad = 8;
  function size() {
    var w = Math.min(root.querySelector('.cv-fig').clientWidth, 620);
    var dpr = window.devicePixelRatio || 1;
    cvs.style.width = cvs.style.height = w + 'px'; cvs.width = cvs.height = Math.round(w * dpr);
    px = dpr; S = (w - 2 * pad) / D.L;
    var sw = Math.min(root.querySelector('.cv-side').clientWidth || 300, 360);
    strip.style.width = sw + 'px'; strip.style.height = '48px'; strip.width = Math.round(sw * dpr); strip.height = Math.round(48 * dpr);
  }
  function X(x) { return (pad + x * S) * px; }
  function Y(y) { return (pad + (D.L - y) * S) * px; }

  // the measure is drawn once into an offscreen canvas per certificate, size and theme
  var layer = null;
  function key() { return [D.id, cvs.width, document.documentElement.dataset.theme].join('|'); }
  function paintLayer() {
    var oc = document.createElement('canvas'); oc.width = cvs.width; oc.height = cvs.height;
    var ctx = oc.getContext('2d'), acc = css('--acc');
    if (D.rects) {
      var lmax = Math.log(D.dmax), lmin = Math.log(D.dmin);
      ctx.fillStyle = acc;
      D.rects.forEach(function (R) {
        ctx.globalAlpha = 0.06 + 0.5 * (Math.log(R[4]) - lmin) / (lmax - lmin || 1);
        ctx.fillRect(X(R[0]), Y(R[3]), (R[2] - R[0]) * S * px, (R[3] - R[1]) * S * px);
      });
      ctx.globalAlpha = 1;
    }
    if (D.segs) {
      ctx.strokeStyle = css('--link'); ctx.lineWidth = 1.2 * px;
      D.segs.forEach(function (g) { ctx.beginPath(); ctx.moveTo(X(g[0]), Y(g[1])); ctx.lineTo(X(g[2]), Y(g[3])); ctx.stroke(); });
    }
    if (D.atoms) {
      ctx.fillStyle = acc;
      D.atoms.forEach(function (a) {
        ctx.beginPath(); ctx.arc(X(a[0]), Y(a[1]), Math.max(0.6, D.rad * Math.sqrt(a[2] / D.wmax)) * px, 0, 7); ctx.fill();
      });
    }
    layer = { cv: oc, key: key() };
  }

  function draw() {
    if (!D) return;
    var W = cvs.width, acc = css('--acc'), fg = css('--fg'), line = css('--line'), bg = css('--bg2');
    ctx.clearRect(0, 0, W, W);
    ctx.fillStyle = bg; ctx.fillRect(X(0), Y(D.L), D.L * S * px, D.L * S * px);
    var th = ang(st.r);
    if (st.scan && st.scanR === st.r) drawScan();
    if (!layer || layer.key !== key()) paintLayer();
    ctx.drawImage(layer.cv, 0, 0);
    ctx.strokeStyle = line; ctx.lineWidth = px; ctx.strokeRect(X(0), Y(D.L), D.L * S * px, D.L * S * px);
    // centres where a unit square at this angle fits
    var h = half(th);
    ctx.setLineDash([4 * px, 4 * px]); ctx.strokeStyle = css('--fg2');
    ctx.strokeRect(X(h), Y(D.L - h), (D.L - 2 * h) * S * px, (D.L - 2 * h) * S * px); ctx.setLineDash([]);
    // unit square (outline) and core square at the chosen centre
    sq(st.cx, st.cy, th, 1, css('--fg2'), 1);
    var m = mass(st.cx, st.cy, th);
    sq(st.cx, st.cy, th, D.B, m >= 1 - 1e-9 ? css('--ok') : '#d9534f', 2);
    out.theta.textContent = (th * 180 / Math.PI).toFixed(4) + '°';
    out.t.textContent = D.step ? st.r + ' / ' + D.last : '–';
    out.c.textContent = '(' + st.cx.toFixed(4) + ', ' + st.cy.toFixed(4) + ')';
    out.m.textContent = m.toFixed(6);
    out.m.style.color = m >= 1 - 1e-9 ? css('--ok') : '#d9534f';
    drawStrip();
  }
  function sq(cx, cy, th, side, col, lw) {
    var c = Math.cos(th), s = Math.sin(th), h = side / 2;
    ctx.beginPath();
    [[1, 1], [-1, 1], [-1, -1], [1, -1]].forEach(function (k, i) {
      var x = cx + h * (k[0] * c - k[1] * s), y = cy + h * (k[0] * s + k[1] * c);
      i ? ctx.lineTo(X(x), Y(y)) : ctx.moveTo(X(x), Y(y));
    });
    ctx.closePath(); ctx.strokeStyle = col; ctx.lineWidth = lw * px; ctx.stroke();
  }
  function drawScan() {
    var g = st.scan, n = g.n, ok = css('--ok');
    for (var i = 0; i < n; i++) for (var j = 0; j < n; j++) {
      var v = g.v[i * n + j]; if (v === undefined) continue;
      ctx.fillStyle = v >= 1 - 1e-9 ? ok : '#d9534f';
      ctx.globalAlpha = v >= 1 - 1e-9 ? Math.min(0.55, 0.12 + (v - 1) * 0.6) : 0.85;
      var x = g.x0 + (i - 0.5) * g.d, y = g.x0 + (j + 0.5) * g.d;
      ctx.fillRect(X(x), Y(y), g.d * S * px + 1, g.d * S * px + 1);
    }
    ctx.globalAlpha = 1;
  }
  function drawStrip() {
    var W = strip.width, H = strip.height;
    sctx.clearRect(0, 0, W, H);
    var a = D.angle_lower_bound;
    if (!a) { strip.hidden = true; return; }
    strip.hidden = false;
    var lo = 1, hi = Math.max.apply(null, a), n = a.length;
    sctx.fillStyle = css('--fg2');
    a.forEach(function (v, i) {
      var h = (H - 4 * px) * Math.min(1, (v - lo) / (hi - lo) * 1) ;
      sctx.fillRect(i * W / n, H - Math.max(px, h), Math.max(px, W / n - 0.3 * px), Math.max(px, h));
    });
    sctx.fillStyle = css('--acc'); sctx.fillRect(st.r * W / n, 0, Math.max(2 * px, W / n), H);
    out.lb.textContent = a[st.r].toFixed(6);
  }

  function scan() {
    var th = ang(st.r), h = half(th), n = 64, d = (D.L - 2 * h) / n, x0 = h + d / 2;
    var g = { n: n, d: d, x0: x0, v: new Array(n * n) }, k = 0, min = Infinity, at = null;
    st.scan = g; st.scanR = st.r;
    out.scan.textContent = '…';
    (function step() {
      var t0 = performance.now();
      while (k < n * n && performance.now() - t0 < 30) {
        var i = k % n, j = (k / n) | 0, x = x0 + i * d, y = x0 + j * d, v = mass(x, y, th);
        g.v[k] = v; if (v < min) { min = v; at = [x, y]; } k++;
      }
      draw();
      if (k < n * n && st.scan === g) requestAnimationFrame(step);
      else if (st.scan === g) {
        out.scan.textContent = min.toFixed(6) + ' @ (' + at[0].toFixed(3) + ', ' + at[1].toFixed(3) + ')';
        out.scan.style.color = min >= 1 - 1e-9 ? css('--ok') : '#d9534f';
      }
    })();
  }

  function load(name) {
    st.scan = null; out.scan.textContent = '–'; out.scan.style.color = '';
    // the sidebar marks the n; the selector lists every certificate of that n, the largest side first
    var nOf = null;
    Object.keys(VERS).forEach(function (n) { VERS[n].forEach(function (v) { if (v[0] === name) nOf = n; }); });
    root.querySelectorAll('.cv-items [data-cert]').forEach(function (b) { b.setAttribute('aria-pressed', b.dataset.n === nOf); });
    verSel.innerHTML = '';
    (VERS[nOf] || []).forEach(function (v) {
      var o = document.createElement('option'); o.value = v[0];
      o.textContent = v[1] + '  ' + KINDN[v[2]] + (v[3] ? '  (best)' : '') + '  — ' + v[0].replace('certs/', '');
      if (v[0] === name) o.selected = true; verSel.appendChild(o);
    });
    try { history.replaceState(null, '', '#' + name.replace('certs/', '')); } catch (e) {}
    (cache[name] ? Promise.resolve(cache[name]) : fetch('data/' + name + '.json').then(function (r) { return r.json(); }))
      .then(function (d) {
        cache[name] = d; D = d;
        if (D.L_text === undefined) expand(D, frac(d.L));
        if (D.L_text === undefined) {   // a cached certificate was already converted on its first load
          D.L_text = d.L; D.B_text = d.B; D.step_text = d.step;
          D.L = frac(d.L); D.B = d.B ? frac(d.B) : 1; D.step = d.step ? frac(d.step) : 0;
        }
        if (d.atoms) { D.wmax = d.atoms.reduce(function (x, a) { return Math.max(x, a[2]); }, 0); D.rad = Math.min(4.2, 90 / Math.sqrt(d.atoms.length)); }
        if (d.rects) { var ds = d.rects.map(function (r) { return r[4]; }); D.dmax = Math.max.apply(null, ds); D.dmin = Math.min.apply(null, ds); }
        var last = d.step ? d.last : 4500;
        rIn.max = last; st.r = Math.min(+rIn.value, last); rIn.value = st.r;
        st.cx = st.cy = D.L / 2 - 0.37;
        root.querySelectorAll('[data-info]').forEach(function (el) {
          var k = el.dataset.info;
          el.textContent = k === 'items' ? [d.atoms && d.atoms.length + ' pts', d.segs && d.segs.length + ' seg', d.rects && d.rects.length + ' rect'].filter(Boolean).join(' + ')
            : k === 'net' ? (d.step ? 't = r · ' + d.step + ', r = 0 … ' + d.last : (SP.L() === 'ja' ? 'すべての角度' : 'every angle'))
            : k === 'B' ? (d.B || (SP.L() === 'ja' ? '1（単位正方形そのもの）' : '1 (the unit square itself)')) : d[k];
        });
        root.querySelectorAll('[data-kind]').forEach(function (el) { el.hidden = el.dataset.kind !== d.kind; });
        root.querySelectorAll('[data-net]').forEach(function (el) { el.hidden = (el.dataset.net === '1') !== !!d.step; });
        var a = root.querySelector('a[data-rel]'); a.href = d.release; a.textContent = d.asset;
        var nt = root.querySelector('[data-note]'); nt.textContent = d.note || ''; nt.hidden = !d.note;
        var dd = root.querySelector('[data-docs]'); dd.innerHTML = '';
        (d.docs || []).forEach(function (p) { var l = document.createElement('a'); l.href = dd.dataset.blob + p; l.textContent = p.split('/').slice(-2).join('/'); dd.appendChild(l); });
        size(); draw(); states(D);
      });
  }

  // "What the certificate states", written for the certificate on screen
  function massDec(d) {   // decimal of the exact total (a/b, or a/2^k)
    var t = String(d.total_mass).split('/'), q = t.length > 1 ? (t[1].indexOf('^') > 0 ? Math.pow(2, +t[1].split('^')[1]) : +t[1]) : 1;
    return (+t[0] / q).toFixed(6);
  }
  function fmtInt(k) { return k.toLocaleString('en'); }
  function states(d) {
    var el = root.querySelector('[data-states]'), ja = SP.L() === 'ja', n = d.n, L = d.L_text, B = d.B_text;
    var parts = [];
    if (d.atoms) parts.push(fmtInt(d.atoms.length) + (ja ? ' 点' : ' points'));
    if (d.segs) parts.push(fmtInt(d.segs.length) + (ja ? ' 本の線分（質量は長さに沿って均等）' : ' segments (mass spread evenly along each)'));
    if (d.rects) parts.push(fmtInt(d.rects.length) + (ja ? ' 個の長方形（各長方形の上で一定の密度）' : ' rectangles (constant density on each)'));
    var meas = ja ? '[0, ' + L + ']² 上の測度。正方形の 8 つの対称で変わらない（ここでは 8 つの像に展開して描いている）。' + parts.join('、') + '。総質量 ' + d.total_mass + '（≈ ' + massDec(d) + '）< ' + n + '。'
                  : 'A measure on [0, ' + L + ']², unchanged by the 8 symmetries of the square (drawn here with all 8 images). ' + parts.join(', ') + '. Total mass ' + d.total_mass + ' (≈ ' + massDec(d) + ') < ' + n + '.';
    var cond, why;
    if (d.step) {
      var bd = (frac(d.B) * (1 + d.step)).toFixed(9);
      cond = ja ? '辺 B = ' + B + ' の閉じた正方形（芯）を、単位正方形が入るどの中心に置いても、網の ' + (d.last + 1) + ' 個の角度 θ_r = 2 arctan(r · ' + d.step_text + ')（r = 0 … ' + d.last + '）のどれに向けても、拾う質量は 1 以上。'
                : 'Every closed square of side B = ' + B + ' (the core), at any centre and turned to any of the ' + (d.last + 1) + ' net directions θ_r = 2 arctan(r · ' + d.step_text + '), r = 0 … ' + d.last + ', captures mass at least 1.';
      why = ja ? 'B(1 + step) = ' + bd + ' < 1 なので、各単位正方形の内部に、同じ中心で近くの網の角度に向けた芯が入る。' + n + ' 個の単位正方形が辺 ' + L + ' の正方形に入るなら、芯は互いに重ならず、それぞれ 1 以上を拾うので合計は ' + n + ' 以上になり、総質量を超える。'
               : 'B(1 + step) = ' + bd + ' < 1, so each unit square contains in its interior the core with the same centre turned to a nearby net direction. If ' + n + ' unit squares fit in the square of side ' + L + ', their cores are disjoint and each captures at least 1, so the total would be at least ' + n + ', more than the total mass.';
    } else {
      cond = ja ? '[0, ' + L + ']² の中の閉じた単位正方形は、どの位置・どの角度でも質量 1 以上を拾う。'
                : 'Every closed unit square in [0, ' + L + ']², at every position and angle, captures mass at least 1.';
      why = ja ? n + ' 個の単位正方形が辺 ' + L + ' 未満の正方形に入るとすると、詰め方を辺 ' + L + ' まで拡大する。拡大した各正方形は閉じた単位正方形を含み、それらは互いに重ならないので合計 ' + n + ' 以上を拾い、総質量を超える。'
               : 'If ' + n + ' unit squares fit in a square of side less than ' + L + ', scale the packing up to side ' + L + '; each enlarged square contains a closed unit square, these are disjoint, and together they would capture at least ' + n + ', more than the total mass.';
    }
    var links = (d.docs || []).map(function (p) { return '<a href="' + el.dataset.blob + p + '">' + p.split('/').slice(-2).join('/') + '</a>'; });
    if (d.step) links.push('<a href="' + el.dataset.lb + '">lower-bounds.md §2</a>');
    var esc = function (t) { return String(t).replace(/&/g, '&amp;').replace(/</g, '&lt;'); };
    var row = function (en, jt, v, html) { return '<dt>' + (ja ? jt : en) + '</dt><dd>' + (html ? v : esc(v)) + '</dd>'; };
    el.innerHTML = row('Claim', '主張', d.claim) + row('Measure', '測度', meas) + row('Condition checked', '検査する条件', cond)
      + row('Why ' + n + ' squares do not fit', n + ' 個が入らない理由', why) + row('Sources', '記述の元', '<span class="links-inline">' + links.join(' · ') + '</span>', true);
  }

  // orbit representatives (*_d4, each with 1/8 of its orbit's mass) become their eight images under the symmetries of [0, L]^2
  function expand(d, L) {
    function img(q, sw, fx, fy) { var x = q[0], y = q[1]; if (sw) { var t = x; x = y; y = t; } return [fx ? L - x : x, fy ? L - y : y]; }
    [['atoms_d4', 'atoms', 1], ['segs_d4', 'segs', 2], ['rects_d4', 'rects', 2]].forEach(function (k) {
      var src = d[k[0]]; if (!src) return;
      var out = d[k[1]] || (d[k[1]] = []);
      src.forEach(function (q) {
        for (var sw = 0; sw < 2; sw++) for (var fx = 0; fx < 2; fx++) for (var fy = 0; fy < 2; fy++) {
          var a = img(q, sw, fx, fy);
          if (k[2] === 1) { out.push([a[0], a[1], q[2]]); continue; }
          var b = img([q[2], q[3]], sw, fx, fy);
          if (k[1] === 'rects') out.push([Math.min(a[0], b[0]), Math.min(a[1], b[1]), Math.max(a[0], b[0]), Math.max(a[1], b[1]), q[4]]);
          else out.push([a[0], a[1], b[0], b[1], q[4]]);
        }
      });
      delete d[k[0]];
    });
  }

  function pick(ev) {
    var b = cvs.getBoundingClientRect(), th = ang(st.r), h = half(th);
    var x = ((ev.clientX - b.left) - pad) / S, y = D.L - ((ev.clientY - b.top) - pad) / S;
    var lo = keep.checked ? h : 0;   // keep the unit square inside the container (default) or let the centre go anywhere in K
    st.cx = Math.max(lo, Math.min(D.L - lo, x)); st.cy = Math.max(lo, Math.min(D.L - lo, y)); draw();
  }
  var drag = false;
  cvs.addEventListener('pointerdown', function (ev) { drag = true; cvs.setPointerCapture(ev.pointerId); pick(ev); });
  cvs.addEventListener('pointermove', function (ev) { if (drag) pick(ev); });
  ['pointerup', 'pointercancel', 'lostpointercapture'].forEach(function (t) { cvs.addEventListener(t, function () { drag = false; }); });
  rIn.addEventListener('input', function () {
    st.r = +rIn.value; var h = half(ang(st.r));
    if (keep.checked) { st.cx = Math.max(h, Math.min(D.L - h, st.cx)); st.cy = Math.max(h, Math.min(D.L - h, st.cy)); }
    draw();
  });
  strip.addEventListener('click', function (ev) {
    var b = strip.getBoundingClientRect(); rIn.value = Math.floor((ev.clientX - b.left) / b.width * (D.last + 1));
    rIn.dispatchEvent(new Event('input'));
  });
  root.querySelector('#cv-scan').addEventListener('click', scan);
  keep.addEventListener('change', function () { if (keep.checked) rIn.dispatchEvent(new Event('input')); });
  root.querySelectorAll('.cv-items [data-cert]').forEach(function (b) { b.addEventListener('click', function () { load(b.dataset.cert); }); });
  verSel.addEventListener('change', function () { load(verSel.value); });
  new MutationObserver(draw).observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme'] });
  window.addEventListener('resize', function () { if (D) { size(); draw(); } });
  // the list on the left: filter by kind, keep the chosen certificate in view
  document.addEventListener('langchange', function () { if (D) states(D); });
  var h = location.hash.slice(1), known = Object.keys(VERS).some(function (n) { return VERS[n].some(function (v) { return v[0] === 'certs/' + h; }); });
  var first = known ? 'certs/' + h : root.dataset.first;
  load(first);
  var fb = root.querySelector('.cv-items [aria-pressed="true"]'); if (fb) fb.scrollIntoView({ block: 'nearest' });
})();
