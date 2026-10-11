import * as containers_geometry from '../../engines/containers-geometry';
import * as containers_draw from '../../engines/containers-draw';
// Non-square containers: the container, the optimal packing (when the source fixes it) and the certificate's
// weighted points; a movable unit square shows the weight of the points it contains (closed square).
const mounted = new WeakSet<HTMLElement>();
export function mountShared(host: HTMLElement) {
  if (mounted.has(host)) return;
  mounted.add(host);
  const createCanvas = () => document.createElement('canvas');
  const containers_drawOptions: containers_draw.Options = {
    report: ({cm, ok}: any) => { out.c.textContent = '(' + st.x.toFixed(4) + ', ' + st.y.toFixed(4) + ')';
      out.a.textContent = (st.a * 180 / Math.PI).toFixed(2) + '°';
      out.m.textContent = cm[0].toFixed(6) + '  (' + cm[1] + (L() === 'ja' ? ' 点' : ' pts') + (cm[2] ? (L() === 'ja' ? '、補題 P で ' : ', Lemma P ') + cm[2] : '') + ')';
      out.fit.textContent = ok ? (L() === 'ja' ? '容器の中' : 'inside the container') : (L() === 'ja' ? '容器からはみ出す' : 'not inside the container'); },
    get D() { return D; },
    get X() { return X; },
    get Y() { return Y; },
    get css() { return css; },
    get cvs() { return cvs; },
    get px() { return px; },
    get show() { return show; },
    get st() { return st; }
  };

  'use strict';
  var root: any = host.querySelector('#ct');
  if (!root) return;
  var cvs = root.querySelector('canvas'), ctx = cvs.getContext('2d'), aIn = root.querySelector('#ct-a'), keep = root.querySelector('#ct-keep');
  var out: Record<string, any> = {}; root.querySelectorAll('[data-o]').forEach(function (el) { out[el.dataset.o] = el; });
  // tolerance for points on the edge of the closed square (the browser computes in floating point)
  var EPS = 1e-9;
  var ALL = [], D = null, st = { x: 0, y: 0, a: 0 }, show = { pack: true, pts: true, sq: true };
  var px, S, ox, oy, pad = 10;
  function css(n) { return getComputedStyle(document.documentElement).getPropertyValue(n).trim(); }
  function L() { return document.documentElement.lang; }

  function bbox(P: any): any { return containers_geometry.bbox(P); }
  function size() {
    var w = (host.classList.contains('phone-view') ? root.querySelector('.cv-fig').clientWidth : Math.min(root.querySelector('.cv-fig').clientWidth, 620)), b = bbox(D.poly), dpr = window.devicePixelRatio || 1;
    var sc = (w - 2 * pad) / Math.max(b[2] - b[0], b[3] - b[1]), hgt = (b[3] - b[1]) * sc + 2 * pad;
    cvs.style.width = w + 'px'; cvs.style.height = hgt + 'px'; cvs.width = Math.round(w * dpr); cvs.height = Math.round(hgt * dpr);
    px = dpr; S = sc; ox = pad + ((w - 2 * pad) - (b[2] - b[0]) * sc) / 2 - b[0] * sc; oy = pad + b[3] * sc;
  }
  function X(x) { return (ox + x * S) * px; }
  function Y(y) { return (oy - y * S) * px; }
  function path(P: any): any { return containers_draw.path(ctx, containers_drawOptions, P); }
  function corners(x: any, y: any, a: any): any { return containers_geometry.corners(x, y, a); }
  function inside(p: any): any { return containers_geometry.inside(D, p); }
  // weight the closed square captures: points inside it, plus Lemma P for a pair at distance 1 whose chord crosses the
  // square between two opposite edges and meets the segment between the points (then the square contains one of them)
  function captured(): any { return containers_geometry.captured(D, st); }

  function draw(): any { return containers_draw.draw(ctx, containers_drawOptions); }

  function bi(o) { return o ? (L() === 'ja' ? o.ja : o.en) : ''; }
  function select(i) {
    D = ALL[i];
    history.replaceState(null, '', '#' + D.cont + '-' + D.n);
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
  function fits(x: any, y: any): any { return containers_geometry.fits(D, st, x, y); }
  // a position where the square at the current angle fits, nearest to the centroid (grid search); the centroid if none
  function centroid(): any { return containers_geometry.centroid(D, st); }
  // centres where the square at the current angle fits: n·c >= k for each edge (inward normal n), a convex polygon
  function cons(): any { return containers_geometry.cons(D, st); }
  // nearest centre to (x, y) where the square fits: the point itself, a projection on one constraint line, or a corner
  function project(x: any, y: any): any { return containers_geometry.project(D, st, x, y); }
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
  window.addEventListener('hashchange', () => { if (!ALL) return; const i = ALL.findIndex(it => it.cont + '-' + it.n === location.hash.slice(1)); if (i >= 0) select(i); });
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
}
