import {mountShared} from '../shared/rect-player';
import {layout, bi} from './layout';
export function mountPhone(host: HTMLElement) {
 const l = layout(), abort = new AbortController(), options = {signal: abort.signal};
 const root = host.querySelector<HTMLElement>('#rp')!;
 const frame = host.querySelector<HTMLElement>('.rp-col')!;
 const canvas = frame.querySelector('canvas')!;
 const get = <T extends HTMLElement>(key: string) => host.querySelector<T>(`[data-o="${key}"]`)!;
 const sheet = document.createElement('dialog'); sheet.className = 'phone-k-sheet'; sheet.setAttribute('aria-label', 'k');
 const close = document.createElement('button'); close.innerHTML = bi('Done', '閉じる');
 sheet.append(close); l.add(sheet, root);
 l.move(host.querySelector('.rr-sel')!, sheet);
 const help = document.createElement('p'); help.innerHTML = bi('Swipe up or down to change k. Tap to play or pause. Drag the bottom bar to seek. The sampled packings are illustrations, not certificates. Colour shows tilt, from axis-parallel blue to red-violet at 45°. Music, where a score exists, follows the timeline at 1×; record saves the frame as video.', '上下にスワイプして k を切り替え。タップで再生・一時停止。下のバーをドラッグして時刻を移動。配置の標本は作図であって証明書ではない。色は傾き（軸に平行で青、45° で赤紫）を示す。音楽は曲がある k で、1× の時刻表に沿って再生。録画は枠全体を動画として保存する。'); sheet.append(help);
 const k = document.createElement('button'); k.className = 'phone-k'; k.textContent = 'k'; k.setAttribute('aria-label','k'); k.setAttribute('aria-haspopup','dialog');
 l.add(k, frame);
 k.addEventListener('click', () => sheet.showModal(), options);
 close.addEventListener('click', () => sheet.close(), options);
 sheet.addEventListener('click', e => { if ((e.target as Element).closest('[data-k]')) sheet.close(); }, options);
 const rail = document.createElement('div'); rail.className = 'phone-rail'; l.add(rail, frame);
 const music = document.createElement('button'); music.className = 'phone-music';
 music.innerHTML = `♫<small>${bi('music','音楽')}</small>`; rail.append(music);
 music.addEventListener('click', () => { const m = get<HTMLInputElement>('mus'); m.checked = !m.checked; m.dispatchEvent(new Event('change')); sync(); }, options);
 l.move(get('back'), rail); l.move(get('restart'), rail); l.move(get('rec'), rail);
 get('back').classList.add('phone-rectangles');
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
  const top = document.querySelector('.topbar')!.getBoundingClientRect().bottom;
  const bottom = document.querySelector('.tabbar')!.getBoundingClientRect().top;
  host.style.setProperty('--player-top',`${top}px`);
  host.style.setProperty('--player-height',`${Math.max(180,bottom-top)}px`);
  host.dispatchEvent(new Event('playerresize'));
 };
 window.addEventListener('resize',fit,options); window.visualViewport?.addEventListener('resize',fit,options); fit();
 if (!('MediaRecorder' in window) || !canvas.captureStream) get('rec').hidden=true;
 mountShared(host);
 return () => { abort.abort(); observer.disconnect(); clearTimeout(timer); sheet.close(); get('back').classList.remove('phone-rectangles'); get('rec').hidden=false; l.cleanup(); };
}
