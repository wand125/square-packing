import {mountShared} from '../shared/rect-player';
import {layout, bi, iconKButtons} from './layout';
export function mountPhone(host: HTMLElement) {
 const l = layout(), abort = new AbortController(), options = {signal: abort.signal};
 const root = host.querySelector<HTMLElement>('#rp')!;
 const frame = host.querySelector<HTMLElement>('.rp-col')!;
 const canvas = frame.querySelector('canvas')!;
 const get = <T extends HTMLElement>(key: string) => host.querySelector<T>(`[data-o="${key}"]`)!;
 const sheet = document.createElement('dialog'); sheet.className = 'phone-k-sheet'; sheet.setAttribute('aria-label', 'k');
 l.add(sheet, root);   // no Done button: choosing a k or tapping outside closes it
 l.move(host.querySelector('.rr-sel')!, sheet);
 const undoIcons = iconKButtons(sheet, 'data-k');
 const k = document.createElement('button'); k.className = 'phone-k'; k.textContent = 'k'; k.setAttribute('aria-label','k'); k.setAttribute('aria-haspopup','dialog');
 k.addEventListener('click', () => sheet.showModal(), options);
 sheet.addEventListener('click', e => { if (e.target === sheet || (e.target as Element).closest('[data-k]')) sheet.close(); }, options);
 const rail = document.createElement('div'); rail.className = 'phone-rail'; l.add(rail, frame);
 const music = document.createElement('button'); music.className = 'phone-music';
 music.innerHTML = '♫'; music.setAttribute('aria-label', 'music'); rail.append(music);
 music.addEventListener('click', () => { const m = get<HTMLInputElement>('mus'); m.checked = !m.checked; m.dispatchEvent(new Event('change')); sync(); }, options);
 l.move(get('restart'), rail);
 // icons only on phones: ↻ for "from the start", and the current k as the k button, below it
 const restartHtml = get('restart').innerHTML; get('restart').innerHTML = '↻'; get('restart').setAttribute('aria-label', 'from the start');
 rail.append(k);
 // the k button: a 2 × 2 grid of numbered squares (choosing the number of squares)
 k.innerHTML = '<svg viewBox="0 0 24 24" width="26" height="26" aria-hidden="true">' + [[2,2,'1'],[13,2,'2'],[2,13,'3'],[13,13,'4']].map(([x,y,n]) => `<rect x="${x}" y="${y}" width="9" height="9" rx="1" fill="none" stroke="currentColor" stroke-width="1.5"/><text x="${+x+4.5}" y="${+y+7}" text-anchor="middle" font-size="7" font-family="sans-serif" fill="currentColor">${n}</text>`).join('') + '</svg>';
 const kObserver = { disconnect() {} };
 // on phones the player has no Rectangles link and no recording
 const backWasHidden = get('back').hidden, recWasHidden = get('rec').hidden; get('back').hidden = true; get('rec').hidden = true;
 l.move(get('scrub'), frame);
 const overlay = document.createElement('output'); overlay.className = 'phone-play-overlay'; overlay.setAttribute('aria-live','polite'); l.add(overlay, frame);
 let timer: ReturnType<typeof setTimeout>;
 const sync = () => { music.setAttribute('aria-pressed', String(get<HTMLInputElement>('mus').checked)); music.disabled = get<HTMLInputElement>('mus').disabled; };
 const observer = new MutationObserver(sync); observer.observe(get('mus'),{attributes:true}); sync();
 let start: {x:number,y:number} | null = null;
 canvas.addEventListener('pointerdown', e => { start = {x:e.clientX,y:e.clientY}; canvas.setPointerCapture(e.pointerId); }, options);
 canvas.addEventListener('pointercancel', () => { start = null; }, options);
 canvas.addEventListener('pointerup', e => {
  if (!start) return;
  const dy = e.clientY-start.y, dx=e.clientX-start.x; start=null;
  if (Math.abs(dy)>45 && Math.abs(dy)>Math.abs(dx)) {
   const chips = Array.from(host.querySelectorAll<HTMLButtonElement>('[data-k]:not([data-k="all"])'));
   const index = chips.findIndex(b => b.getAttribute('aria-pressed')==='true');
   const next = chips[index + (dy<0 ? 1 : -1)];
   if (next) { next.click(); get('play').click(); if (!matchMedia('(prefers-reduced-motion: reduce)').matches) canvas.animate([{transform:`translateY(${dy<0?24:-24}px)`,opacity:.4},{transform:'translateY(0)',opacity:1}],{duration:180}); }
  } else if (Math.hypot(dx,dy)<15) {
   get('play').click(); overlay.textContent=get('play').textContent; overlay.classList.add('show');
   clearTimeout(timer); timer=setTimeout(() => overlay.classList.remove('show'),650);
  }
 }, options);
 // A tap belongs to playback, not the desktop graph-seeking interaction.
 canvas.addEventListener('click', e => { e.stopImmediatePropagation(); e.preventDefault(); }, {...options,capture:true});
 const fit = () => {
  // the frame fills the space between the bars; a bar that is not shown (embedded player) gives the screen edge
  const tb = document.querySelector('.topbar') as HTMLElement, bb = document.querySelector('.tabbar') as HTMLElement;
  const top = tb.offsetParent ? tb.getBoundingClientRect().bottom : 0;
  const bottom = bb.offsetParent ? bb.getBoundingClientRect().top : window.innerHeight;
  host.style.setProperty('--player-top',`${top}px`);
  host.style.setProperty('--player-height',`${Math.max(180,bottom-top)}px`);
  host.dispatchEvent(new Event('playerresize'));
 };
 window.addEventListener('resize',fit,options); window.visualViewport?.addEventListener('resize',fit,options); fit();
 if (!('MediaRecorder' in window) || !canvas.captureStream) get('rec').hidden=true;
 mountShared(host);
 return () => { undoIcons(); abort.abort(); observer.disconnect(); kObserver.disconnect(); get('restart').innerHTML = restartHtml; clearTimeout(timer); sheet.close(); get('back').hidden = backWasHidden; get('rec').hidden = recWasHidden; l.cleanup(); };
}
