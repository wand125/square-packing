import {rectIndex, rectK} from './rect-data';
import * as rect_edges from '../../engines/rect-edges';
import * as rect_draw from '../../engines/rect-draw';
// Rectangles: for k = 2 .. 20 squares, the edge in the (b, a) plane (b = long side, drawn as x; a = short side, as y)
// where k squares begin to fit, its pieces, the witness packings, and for k <= 10 the proof status of Friedman's pieces.
const mounted = new WeakSet<HTMLElement>();
export function mountShared(host: HTMLElement) {
  if (mounted.has(host)) return;
  mounted.add(host);
  const createCanvas = () => document.createElement('canvas');
  const rect_drawOptions: rect_draw.Options = {
    get minPlotHeight() { return host.classList.contains('phone-view') ? 200 : 0; },
    zoomText: (value: any) => { o.zt.textContent = value; },
    get ALL() { return ALL; },
    get CELL() { return CELL; },
    get COL() { return COL; },
    get CSEL() { return CSEL; },
    get K() { return K; },
    get R() { return R; },
    get at() { return at; },
    get base() { return base; }, set base(value) { base = value; },
    get createCanvas() { return createCanvas; },
    get css() { return css; },
    get cv() { return cv; },
    get dpr() { return dpr; },
    get figW() { return figW; },
    get geo() { return geo; }, set geo(value) { geo = value; },
    get hov() { return hov; }, set hov(value) { hov = value; },
    get kcol() { return kcol; },
    get pc() { return pc; },
    get sel() { return sel; },
    get zc() { return zc; },
    get zctx() { return zctx; },
    get zoomW() { return zoomW; }
  };

  'use strict';
  var root: any = host.querySelector('#rr'); if (!root) return;
  var cv = root.querySelector('canvas.reg'), ctx = cv.getContext('2d'), pc = root.querySelector('canvas.pk'), pctx = pc.getContext('2d');
  var tb = root.querySelector('#rr-rows'), o: Record<string, any> = {};
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
  function figW() { if (host.classList.contains('phone-view')) return root.querySelector('.cv-fig').clientWidth; return Math.max(200, Math.round(Math.min(root.querySelector('.cv-fig').clientWidth || 600, 680) * (host.classList.contains('phone-view') ? 1 : FIT))); }
  function sideW() { if (host.classList.contains('phone-view')) return Math.max(160,root.querySelector('.pcard').clientWidth); return Math.max(160, Math.round(Math.min(Math.max(220, (root.querySelector('.pcard').clientWidth || 640) * 0.5), 460) * FIT)); }
  function zoomW() { return Math.min(root.querySelector('.cv-side').clientWidth || 320, 480); }
  function css(n) { return getComputedStyle(document.documentElement).getPropertyValue(n).trim(); }
  function ja() { return document.documentElement.lang === 'ja'; }
  function dpr(c, w, h) { var d = window.devicePixelRatio || 1; c.style.width = w + 'px'; c.style.height = h + 'px'; c.width = Math.round(w * d); c.height = Math.round(h * d); return d; }
  function esc(t) { return String(t).replace(/&/g, '&amp;').replace(/</g, '&lt;'); }
  // a parametric piece "a = A(p), b = B(p)" is shown on two lines
  function fml(t) { return esc(t).replace(/,\s*(?=[ab]\s*=)/, '<br>'); }
  function piece(key) { return K.pieces.filter(function (p) { return p.key === key; })[0]; }

  // the plot: x = b from 0 to k + 0.6, y = a from 0 to the top of the edge; height capped at that of k = 5
  function scaleFor(k: any, w: any): any { return rect_draw.scaleFor(ctx, rect_drawOptions, k, w); }
  function drawAll(): any { return rect_draw.drawAll(ctx, rect_drawOptions); }
  // the hover window in All: a 1 x 1 box centred on the pointer (right of the diagonal), magnified in the side column
  var base = null, hov = null, zc = root.querySelector('canvas.zm'), zctx = zc.getContext('2d'), hq = 0;
  function hover(hp: any): any { return rect_draw.hover(ctx, rect_drawOptions, hp); }
  cv.addEventListener('mousemove', function (ev) {
    if (host.classList.contains('phone-view') || !ALL || CELL || !geo) return;
    var r = cv.getBoundingClientRect(), x = (ev.clientX - r.left) * geo.px, y = (ev.clientY - r.top) * geo.px;
    var unit = geo.X(1) - geo.X(0), b = (x - geo.X(0)) / unit, a = (geo.Y(0) - y) / (geo.Y(0) - geo.Y(1));
    if (a < 0 || b < 0 || a > b) return;
    if (hq) cancelAnimationFrame(hq);
    hq = requestAnimationFrame(function () { hq = 0; zc.hidden = false; hover([b, a]); });
  });
  function inCell(q: any, b0: any, a0: any): any { return rect_edges.inCell(q, b0, a0); }
  function throughCell(p: any, b0: any, a0: any): any { return rect_edges.throughCell(p, b0, a0); }
  // a magnified 1 x 1 window [b0, b0 + 1] x [a0, a0 + 1] of every edge, drawn on canvas c of side about size;
  // where the window reaches the diagonal, the edges mirrored across a = b are dashed
  function drawZoom(c: any, cx: any, b0: any, a0: any, size: any, csel: any, dot: any): any { return rect_draw.drawZoom(cx, rect_drawOptions, c, b0, a0, size, csel, dot); }
  // the magnified cell, drawn in the plot's place
  function drawCell(): any { return rect_draw.drawCell(ctx, rect_drawOptions); }
  function draw(): any { return rect_draw.draw(ctx, rect_drawOptions); }
  // the certified packing in its box; with the slider, the rectangle b x a at the chosen point is drawn over it (dashed)
  function squares(k: any, w: any, box: any): any { return rect_draw.squares(pctx, rect_drawOptions, k, w, box); }
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
  function along(p: any, c: any, v: any): any { return rect_edges.along(p, c, v); }
  function span(p: any, c: any): any { return rect_edges.span(p, c); }
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
  function familyAt(p: any, a: any): any { return rect_edges.familyAt(p, a); }
  var showCert = true;   // the packing panel shows the certificate (after a certificate button) or the family at the slider
  function showPiece(p, k) {
    if (!CELL) history.replaceState(null, '', '#' + k + '-' + p.key);
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
    if (!K) return;
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
    host.querySelectorAll<any>('[data-sel]').forEach(function (b) { b.setAttribute('aria-pressed', b.dataset.sel === String(k)); });
    CELL = null;
    if (typeof k === 'string' && k.indexOf('cell-') === 0) {
      var m = k.split('-'); CELL = [+m[1], +m[2]]; ALL = false; cur = k; CSEL = null;
      host.querySelectorAll<any>('[data-sel]').forEach(function (b) { b.setAttribute('aria-pressed', b.dataset.sel === 'all'); });
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
  let selection = 0;
  let progressing = false;
  function loadError(error) { root.dataset.error = String(error); o.rh.textContent = ja() ? '読み込みに失敗しました。もう一度選択してください。' : 'Could not load data. Select again to retry.'; }
  async function progressive() {
    if (progressing) return;
    progressing = true;
    try {
      for (const edge of R.ks) {
        if (typeof cur === 'number') break;
        if (edge.loaded) continue;
        await rectK(R, edge.k);
        if (typeof cur !== 'number') { if (CELL) cellTable(); info(); draw(); }
        await new Promise(resolve => requestAnimationFrame(resolve));
      }
    } catch (error) { loadError(error); }
    finally { progressing = false; }
  }
  async function settle() {
    if (!R) return;
    const version = ++selection;
    const requested = cur;
    if (typeof requested === 'number' && !R.ks.find(x => x.k === requested)?.loaded) {
      stopRun(); K = null; geo = null;
      try { await rectK(R, requested); } catch (error) { if (version === selection) loadError(error); return; }
      if (version !== selection) return;
    }

    var g = root.querySelector('.cv-grid'), keep = [cur, sel.key, sel.w], m = 0, tallest = null;
    var keepAt = at;
    g.style.minHeight = ''; FIT = 1; choose(keep[0]);
    var height = function (key) { if (key) { sel.key = key; sel.w = 0; at = null; } info(); draw(); return g.offsetHeight; };
    if (typeof keep[0] === 'number') K.pieces.forEach(function (p) { var hh = height(p.key); if (hh > m) { m = hh; tallest = p.key; } });
    else m = height(null);
    // the pieces heading should start at 2/3 of the window height or above: shrink the figures to fit, down to half size
    var avail = window.innerHeight * 2 / 3 - (g.getBoundingClientRect().top + window.scrollY) - 24;
    for (var it = 0; !host.classList.contains('phone-view') && it < 4 && m > avail && FIT > 0.5; it++) { FIT = Math.max(0.5, FIT * avail / m); m = height(tallest); }
    // on a narrow screen the columns stack, so a fixed height would only leave a gap
    g.style.minHeight = window.innerWidth > 760 ? m + 'px' : '';
    // back to the piece shown before, if it belongs to this k; otherwise the first piece
    if (typeof keep[0] === 'number') { var kp = piece(keep[1]); sel.key = kp ? kp.key : K.pieces[0].key; sel.w = kp ? keep[2] : 0; at = kp ? keepAt : null; }
    info(); draw();
    if (typeof cur !== 'number') void progressive();
  }
  cv.addEventListener('click', function (ev) {
    if (!geo) return;
    var b = cv.getBoundingClientRect(), x = (ev.clientX - b.left) * geo.px, y = (ev.clientY - b.top) * geo.px;
    if (CELL) return;
    if (ALL) {   // move the magnified 1 x 1 window to centre on the click
      var unit = (geo.X(1) - geo.X(0)), xb = (x - geo.X(0)) / unit, ya = (geo.Y(0) - y) / (geo.Y(0) - geo.Y(1));
      // the clicked grid cell [i, i+1] x [j, j+1]; only cells on or right of the diagonal (j <= i) can be chosen
      var i = Math.floor(xb), j = Math.floor(ya);
      if (i < 0 || j < 0 || j > i) return;
      cur = 'cell-' + i + '-' + j; settle();   // the cell replaces the plot, and the table lists its pieces
      return;
    }
  });
  // k view: press on the plot, or drag, to put the point on the nearest place of the edge; its piece becomes the selected
  // one and the packing panel follows the point (a certified packing when the point is on one, else the sampled family)
  function nearestEdge(x: any, y: any): any { return rect_edges.nearestEdge(CELL, K, R, geo, x, y); }
  function snap(ev) {
    var r = cv.getBoundingClientRect(), x = (ev.clientX - r.left) * geo.px, y = (ev.clientY - r.top) * geo.px, best = null, bd = 1e18;
    best = nearestEdge(x, y);
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
  function pathOf(): any { return rect_edges.pathOf(K); }
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
  host.querySelectorAll<any>('[data-sel]').forEach(function (b) { b.addEventListener('click', function () { cur = b.dataset.sel === 'all' ? 'all' : +b.dataset.sel; settle(); }); });
  document.addEventListener('langchange', function () { if (R) settle(); });
  new MutationObserver(function () { if (K) { info(); draw(); } }).observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme'] });
  var rt = null;
  window.addEventListener('resize', function () { if (R) { clearTimeout(rt); rt = setTimeout(settle, 150); } });
  async function restoreHash() { if (!R) return;
    var h = parseInt(location.hash.slice(1), 10), hs = location.hash.slice(1), hp = /^(\d+)-([\d.]+)$/.exec(hs);   // #k-piece: open k with that piece selected
    cur = hs === 'all' || /^cell-\d+-\d+$/.test(hs) ? hs : R.ks.some(function (x) { return x.k === h; }) ? h : 5; await settle();
    if (cur !== h && hp) return;
    if (hp && typeof cur === 'number' && K && K.pieces.some(function (x) { return x.key === hp[2]; })) { sel.key = hp[2]; sel.w = 0; at = null; info(); draw(); }
  }
  window.addEventListener('hashchange', restoreHash);
  rectIndex(host.dataset.preview === '1').then(function (d) { R = d; restoreHash(); }).catch(loadError);
}
