import * as cert_geometry from '../../engines/cert-geometry';
import * as cert_draw from '../../engines/cert-draw';
// Certificate viewer: draws a published measure on [0, L]^2 and the mass captured by a core square of side B
// at a net direction. Floating point, for viewing; the certificate's own checker decides validity.
const mounted = new WeakSet<HTMLElement>();
export function mountShared(host: HTMLElement) {
  if (mounted.has(host)) return;
  mounted.add(host);
  const createCanvas = () => document.createElement('canvas');
  const cert_drawOptions: cert_draw.Options = {
    boundText: (value: any) => { out.lb.textContent = value; },
    report: ({th, m}: any) => { out.theta.textContent = (th * 180 / Math.PI).toFixed(4) + '°';
    out.t.textContent = D.step ? st.r + ' / ' + D.last : '–';
    out.c.textContent = '(' + st.cx.toFixed(4) + ', ' + st.cy.toFixed(4) + ')';
    out.m.textContent = m.toFixed(6);
    out.m.style.color = m >= 1 - 1e-9 ? css('--ok') : '#d9534f'; },
    get D() { return D; },
    get S() { return S; },
    get X() { return X; },
    get Y() { return Y; },
    get createCanvas() { return createCanvas; },
    get css() { return css; },
    get cvs() { return cvs; },
    get key() { return key; },
    get layer() { return layer; }, set layer(value) { layer = value; },
    get px() { return px; },
    get st() { return st; },
    get strip() { return strip; }
  };

  'use strict';
  var root: any = host.querySelector('#cv');
  if (!root) return;
  var cvs = root.querySelector('canvas.m'), ctx = cvs.getContext('2d');
  var strip = root.querySelector('canvas.strip'), sctx = strip.getContext('2d');
  var rIn = root.querySelector('#cv-r'), keep = root.querySelector('#cv-keep'), out: Record<string, any> = {};
  root.querySelectorAll('[data-o]').forEach(function (el) { out[el.dataset.o] = el; });
  var VERS = JSON.parse(root.dataset.versions), verSel = root.querySelector('#cv-ver');
  var KINDN = { point: 'points', lift: 'points + segments', rect: 'rectangles', mixed: 'mixed' };
  var D = null, st = { r: 0, cx: 0, cy: 0, scan: null, scanR: -1 }, cache = {};

  function frac(s: any): any { return cert_geometry.frac(s); }
  function css(n) { return getComputedStyle(document.documentElement).getPropertyValue(n).trim(); }
  // net certificates: theta_r = 2 atan(r * step); certificates for every angle: r in hundredths of a degree
  function ang(r: any): any { return cert_geometry.ang(D, r); }
  function half(th: any): any { return cert_geometry.half(th); }   // half-width of a unit square at angle th

  // mass of the measure inside the closed core square (centre cx, cy; side B; angle th)
  function mass(cx: any, cy: any, th: any): any { return cert_geometry.mass(D, cx, cy, th); }
  // fraction of a segment's length inside the closed square (uniform mass along the segment)
  function segFrac(g: any, cx: any, cy: any, c: any, s: any, h: any): any { return cert_geometry.segFrac(g, cx, cy, c, s, h); }
  function clipArea(P: any, R: any): any { return cert_geometry.clipArea(P, R); }
  function clip(poly: any, f: any): any { return cert_geometry.clip(poly, f); }

  var px, S, pad = 8;
  function size() {
    var w = (host.classList.contains('phone-view') ? root.querySelector('.cv-fig').clientWidth : Math.min(root.querySelector('.cv-fig').clientWidth, 620));
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
  function paintLayer(): any { return cert_draw.paintLayer(ctx, cert_drawOptions); }

  function draw(): any { return cert_draw.draw(ctx, cert_drawOptions); }
  function sq(cx: any, cy: any, th: any, side: any, col: any, lw: any): any { return cert_draw.sq(ctx, cert_drawOptions, cx, cy, th, side, col, lw); }
  function drawScan(): any { return cert_draw.drawScan(ctx, cert_drawOptions); }
  function drawStrip(): any { return cert_draw.drawStrip(sctx, cert_drawOptions); }

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
            : k === 'net' ? (d.step ? 't = r · ' + d.step + ', r = 0 … ' + d.last : (document.documentElement.lang === 'ja' ? 'すべての角度' : 'every angle'))
            : k === 'B' ? (d.B || (document.documentElement.lang === 'ja' ? '1（単位正方形そのもの）' : '1 (the unit square itself)')) : d[k];
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
  function massDec(d: any): any { return cert_geometry.massDec(d); }
  function fmtInt(k) { return k.toLocaleString('en'); }
  function states(d) {
    var el = root.querySelector('[data-states]'), ja = document.documentElement.lang === 'ja', n = d.n, L = d.L_text, B = d.B_text;
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
  function expand(d: any, L: any): any { return cert_geometry.expand(d, L); }

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
}
