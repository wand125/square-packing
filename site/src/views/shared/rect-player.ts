import {rectIndex, rectK} from './rect-data';
import * as player_timeline from '../../engines/player-timeline';
import * as player_draw from '../../engines/player-draw';
import * as audioEngine from '../../engines/audio';
// Rectangles player: for k squares, the box from the square (a = b) down the edge to the 1-wide strip, drawn upright
// (a across, b up), with the packing from the sampled families. Consecutive arrangements are joined continuously;
// where the squares cannot be matched, the two drawings are crossfaded.
const mounted = new WeakSet<HTMLElement>();
export function mountShared(host: HTMLElement) {
  if (mounted.has(host)) return;
  mounted.add(host);
  const createCanvas = () => document.createElement('canvas');
  const player_drawOptions: player_draw.Options = {
    get frameWidth() {return host.classList.contains('phone-view') ? host.clientWidth : undefined;},
    get frameHeight() {return host.classList.contains('phone-view') ? root.querySelector('.rp-col').clientHeight : undefined;},
    get tl() {return tl;},
    report: (p: any) => { o.scrub.value = Math.round(1000 * t / T);
    o.back.href = 'rect-regions.html#' + K.k + '-' + p.key;
    // only when it changes: Safari throws after about 100 history changes in 30 s (this runs every frame)
    var h = allMode ? '#all' : '#' + K.k + '-' + p.key; if (location.hash !== h) { try { history.replaceState(null, '', h); } catch (e) {} } },
    get K() { return K; },
    get T() { return T; },
    get css() { return css; },
    get cv() { return cv; },
    get gg() { return gg; }, set gg(value) { gg = value; },
    get ja() { return ja; },
    get lightTheme() { return document.documentElement.dataset.theme === 'light'; },
    get marks() { return marks; },
    get t() { return t; },
    get viewportHeight() { return window.innerHeight; },
    get pixelRatio() { return window.devicePixelRatio || 1; },
  };
  const audioOptions: audioEngine.Options = {
    get enabled() {return o.mus.checked;},
    title: (text) => {o.musl.title = text;},
    get T() { return T; },
    get audio() { return audio; },
    get blobUrl() { return blobUrl; }, set blobUrl(value) { blobUrl = value; },
    get endTimer() { return endTimer; },
    get loadSeq() { return loadSeq; }, set loadSeq(value) { loadSeq = value; },
    get musicT() { return musicT; },
    get playing() { return playing; },
    get ready() { return ready; }, set ready(value) { ready = value; o.mus.disabled = !value; o.musl.classList.toggle('off', !value); },
    get speed() { return speed; },
    get t() { return t; }
  };

  'use strict';
  var root: any = host.querySelector('#rp'); if (!root) return;
  var cv = root.querySelector('canvas'), ctx = cv.getContext('2d'), o: Record<string, any> = {};
  root.querySelectorAll('[data-o]').forEach(function (el) { o[el.dataset.o] = el; });
  var R = null, K = null, tl = [], T = 0, t = 0, playing = false, last = 0, speed = 1;   // fixed: the music is written for 1×
  // one audio element for the score, reused for every k and choice (two elements could otherwise play at once)
  var musicT = null;   // the length of the timeline each score was written to (data/music/index.json)
  fetch('data/music/index.json', { cache: 'no-store' }).then(function (r) { return r.json(); }).then(function (d) { musicT = d; if (K) loadMusic(K.k); }).catch(function () {});
  var audio = new Audio(), ready = false, actx = null, asrc = null, adest = null, endTimer = null, loadSeq = 0, blobUrl = null;
  audio.preload = 'auto';
  window.SPAudio = function () { return { paused: audio.paused, at: +audio.currentTime.toFixed(2), ready: ready, src: audio.src.split('/').pop() }; };
  function music(): any { return audioEngine.music(audioOptions); }
  function loadMusic(k: any): any { return audioEngine.loadMusic(audioOptions, k); }
  function css(n) { return getComputedStyle(document.documentElement).getPropertyValue(n).trim(); }
  function ja() { return document.documentElement.lang === 'ja'; }

  // the timeline: from the diagonal end down to a = 1, piece by piece (pieces are stored from a = 1 upwards)
  var PER_A = 7, STEP = 0.9, JOIN = 0.7, HOLD = 0.25, WIND = 0.95;   // WIND includes HOLD, a short stop before the shaking   // WIND: the wind-up before a switch that changes the shape a lot   // seconds per unit of a; per jump at constant a; per crossfade
  function framesOf(p: any): any { return player_timeline.framesOf(p); }
  function build(): any { const result = player_timeline.build(K); tl = result.segments; T = result.duration; }
  // two drawings can be joined continuously when every square has a near partner (same count, nearby poses)
  function close(A: any, B: any): any { return player_timeline.close(A, B); }
  function match(A: any, B: any): any { return player_timeline.match(A, B); }
  function lerp(u: any, v: any, s: any): any { return player_timeline.lerp(u, v, s); }
  // a spring that overshoots and settles, for jumps at constant a and for switches between arrangements
  function spring(u: any): any { return player_timeline.spring(u); }
  function angLerp(u: any, v: any, s: any): any { return player_timeline.angLerp(u, v, s); }   // squares: period 90°
  function mixFrames(F: any, G: any, s: any): any { return player_timeline.mixFrames(F, G, s); }
  function at(time: any): any { return player_timeline.at(tl, time); }

  // the whole frame is drawn on the canvas (so a recording carries it): text at the top, the box, the edge graph, the timeline
  var marks = [];
  // during a wind-up the header keeps the piece before it: step and formula change once the wind-up is over
  function shown(st: any): any { return player_timeline.shown(tl, st); }
  function draw(): any { return player_draw.draw(ctx, player_drawOptions); }
  function tiltColor(th: any): any { return player_draw.tiltColor(ctx, player_drawOptions, th); }
  function wrap(text: any, x: any, y: any, w: any, lh: any, maxLines: any): any { return player_draw.wrap(ctx, player_drawOptions, text, x, y, w, lh, maxLines); }
  // the edge of k (b across, a up, as on the Rectangles page) with the current box as a dot; click to jump there
  var gg = null;
  function graph(box: any, x0: any, y0: any, w: any, h: any, d: any): any { return player_draw.graph(ctx, player_drawOptions, box, x0, y0, w, h, d); }
  // clicks on the frame: on the timeline, seek; on the graph, jump to the nearest point of the run
  cv.addEventListener('click', function (ev) {
    if (!gg) return;
    var r = cv.getBoundingClientRect(), d = gg.d, x = (ev.clientX - r.left) * cv.width / r.width, y = (ev.clientY - r.top) * cv.height / r.height;
    if (ev.clientY - r.top > r.height - 30) {   // the timeline is along b: the time whose box has the nearest b
      var bt = -1, bb = 1e18;
      for (var k2 = 0; k2 <= 600; k2++) { var t2 = T * k2 / 600, f2 = at(t2), b2 = (f2.box || f2.layers[0][0].box)[0], dx = Math.abs(gg.X(b2) - x); if (dx < bb) { bb = dx; bt = t2; } }
      t = bt; draw(); return;
    }
    var best = -1, bd = 400 * d * d;
    for (var i = 0; i <= 400; i++) { var tt = T * i / 400, f = at(tt), bx = f.box || f.layers[0][0].box, dd = Math.pow(gg.X(bx[0]) - x, 2) + Math.pow(gg.Y(bx[1]) - y, 2); if (dd < bd) { bd = dd; best = tt; } }
    if (best >= 0) { t = best; draw(); }
  });
  var animation = 0;
  function schedule() { cancelAnimationFrame(animation); animation = requestAnimationFrame(tick); }
  function tick(now) {
    if (!playing) return;
    var dt = last ? (now - last) / 1000 : 0; last = now;
    if (music() && audio.paused && t < T) startMusic();   // the audio stopped by itself (a stall): restart it at the picture's time
    if (music() && !audio.paused) t = Math.min(T, audio.currentTime); else t = Math.min(T, t + dt * speed);
    draw();
    if (t >= T && (allMode || (host.classList.contains('phone-view') && !rec)) && K.k < R.ks[R.ks.length - 1].k) {   // All: hold the last frame a moment, then the next k
      var nk = R.ks[R.ks.findIndex(x => x.k === K.k) + 1].k;
      clearTimeout(endTimer);
      endTimer = setTimeout(async function () { if (!playing) return; if (await choose(nk, true, true)) { startMusic(); schedule(); } }, 900);
      return;
    }
    if (t >= T) { playing = false; o.play.textContent = '▶'; clearTimeout(endTimer); endTimer = setTimeout(function () { if (rec) rec.stop(); if (!playing) stopMusic(); }, 3200); return; }
    schedule();
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
  let selection = 0, loading = false;
  function loadError(error) { root.dataset.error = String(error); o.len.textContent = ja() ? '読み込み失敗：再選択してください' : 'Load failed: select again'; }
  async function choose(k, keepAll = false, resume = false) {
    if (!R) return false;
    const version = ++selection;
    loading = true;
    playing = resume; last = 0;
    o.play.textContent = playing ? '❚❚' : '▶';
    clearTimeout(endTimer); cancelAnimationFrame(animation); stopMusic();
    if (!keepAll) allMode = false;
    let edge;
    try { edge = await rectK(R, k); }
    catch (error) { if (version === selection) { loading = false; playing = false; o.play.textContent = '▶'; loadError(error); } return false; }
    if (version !== selection) return false;
    K = edge; loading = false; build(); t = 0;
    marks = tl.filter(function (s, i) { return i > 0; }).map(function (s) { var f = at(s.t0); return (f.box || f.layers[0][0].box)[0]; });
    root.querySelectorAll('[data-k]').forEach(function (b) { b.setAttribute('aria-pressed', b.dataset.k === 'all' ? allMode : +b.dataset.k === k); });
    o.len.textContent = T.toFixed(0) + ' s'; loadMusic(k); draw();
    if (playing) { startMusic(); schedule(); }
    if (allMode) { const next = R.ks[R.ks.indexOf(K) + 1]; if (next) void rectK(R, next.k).catch(() => {}); }
    return true;
  }
  o.play.addEventListener('click', function () {
    if (loading) { playing = !playing; o.play.textContent = playing ? '❚❚' : '▶'; return; }
    if (!K) return;
    if (playing) { playing = false; cancelAnimationFrame(animation); clearTimeout(endTimer); o.play.textContent = '▶'; stopMusic(); return; }
    if (t >= T) t = 0;
    playing = true; last = 0; o.play.textContent = '❚❚'; startMusic(); schedule();
  });
  // back to the start (stopped), and play from the start; in All both go back to k = 2
  async function toStart() {
    if (!K || loading) return;
    playing = false; o.play.textContent = '▶'; stopMusic(); clearTimeout(endTimer);
    if (allMode && K.k !== R.ks[0].k) { await choose(R.ks[0].k, true); return; }
    t = 0; if (audio) try { audio.currentTime = 0; } catch (e) {}
    draw();
  }
  o.home.addEventListener('click', toStart);
  o.restart.addEventListener('click', async function () { await toStart(); if (loading || !K) return; playing = true; last = 0; o.play.textContent = '❚❚'; startMusic(); schedule(); });
  function startMusic(): any { return audioEngine.startMusic(audioOptions); }
  function stopMusic(): any { return audioEngine.stopMusic(audioOptions); }
  // record: play from the start and save the canvas as a video file when the run ends
  var rec = null;
  o.rec.addEventListener('click', function () {
    if (rec) { rec.stop(); return; }
    if (!K || loading) return;
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
    t = 0; playing = true; last = 0; o.play.textContent = '❚❚'; startMusic(); schedule();
  });
  o.scrub.addEventListener('input', function () { t = T * (+o.scrub.value / 1000); if (music() && playing) audio.currentTime = t; draw(); });
  o.mus.addEventListener('change', function () { if (!music()) stopMusic(); else if (playing) startMusic(); });
  root.querySelectorAll('[data-k]').forEach(function (b) {
    b.addEventListener('click', function () {
      // a new k while playing keeps playing, from the start of that k
      if (b.dataset.k === 'all') { allMode = true; choose(2, true, playing); b.setAttribute('aria-pressed', 'true'); history.replaceState(null, '', '#all'); return; }
      choose(+b.dataset.k, false, playing);
    });
  });
  document.addEventListener('langchange', function () { root.querySelectorAll('option[data-en]').forEach(function (op) { op.textContent = op.getAttribute('data-' + document.documentElement.lang); }); draw(); });
  new MutationObserver(draw).observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme'] });
  window.addEventListener('resize', draw);
  host.addEventListener('playerresize', draw);
  async function restoreHash() {if (!R) return;
    // opened from Rectangles: #k, or #k-piece to start at that piece (e.g. #14-14.13)
    var m = /^#(\d+)(?:-([\d.]+))?$/.exec(location.hash), k = m && R.ks.some(function (x) { return x.k === +m[1]; }) ? +m[1] : 11;   // default k = 11
    if(location.hash === '#all') { allMode = true; await choose(2, true); return; }
    if (!await choose(k)) return;
    if (m && m[2]) {   // start where the piece itself begins (its run or step, after any wind-up and pop)
      var seg = tl.filter(function (x) { return x.p.key === m[2] && (x.kind === 'run' || x.kind === 'step'); })[0] || tl.filter(function (x) { return x.p.key === m[2]; })[0];
      if (seg) { t = seg.t0 + 1e-3; draw(); }   // just inside it, not on the boundary with the segment before
    }
  }
  window.addEventListener('hashchange', restoreHash);
  rectIndex(host.dataset.preview === '1').then(function (d) { R = d; restoreHash(); }).catch(loadError);
}
