import {mountShared} from '../shared/rect-regions';
import {layout, bi, squaresIcon, iconKButtons} from './layout';
// Phone view of Rectangles: no introduction on the page (an "i" button at the top opens it), the k choice in a popup
// opened from the round button at the bottom right (as on the other pages), the packing inside the piece card.
export function mountPhone(host: HTMLElement) {
 const l = layout();
 const rr = host.querySelector('#rr')!;
 const card = host.querySelector('.pcard') as HTMLElement;
 // the packing stays on the page, under the plot; the piece card opens in a popup (info button), and the player in a
 // full-screen popup (Player button)
 const pack = document.createElement('div'); pack.className = 'rr-phone-pack';
 const fig = host.querySelector('#rr .cv-fig')!; l.add(pack, fig.parentElement!); l.move(pack, fig.parentElement!, fig.nextSibling);
 l.move(host.querySelector('canvas.pk')!, pack);
 (globalThis as any).SP_PACK_MAXH = 260;   // more room for the packing on phones
 const row = document.createElement('div'); row.className = 'rr-fab-col';
 const ib2 = document.createElement('button'); ib2.type = 'button'; ib2.className = 'rr-fab'; ib2.setAttribute('aria-label', 'piece'); ib2.innerHTML = '<span class="rr-fab-i">i</span>';
 const playA = card.querySelector('[data-o="playp"]') as HTMLAnchorElement;
 const pl = document.createElement('button'); pl.type = 'button'; pl.className = 'rr-fab'; pl.setAttribute('aria-label', 'player'); pl.innerHTML = '<svg viewBox="0 0 24 24" width="22" height="22" aria-hidden="true"><rect x="3" y="9" width="18" height="11" rx="1.5" fill="none" stroke="currentColor" stroke-width="1.7"/><path d="M3 9l2.5-4.5h15L18 9M8.5 4.5L6 9M14 4.5L11.5 9" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linejoin="round"/><path d="M10 12v5l4.5-2.5z" fill="currentColor"/></svg>';
 pl.classList.add('rr-fab-movie'); row.append(ib2); l.add(row, document.body); l.add(pl, document.body);   // the player: top right, under the page's i
 const cardPop = document.createElement('dialog'); cardPop.className = 'issue-pop rr-card-pop';
 cardPop.innerHTML = '<button type="button" class="issue-pop-x" aria-label="close">✕</button>';
 l.add(cardPop, rr); l.move(card, cardPop);
 playA.hidden = true;
 ib2.addEventListener('click', () => cardPop.showModal());
 cardPop.addEventListener('click', e => { if (e.target === cardPop || (e.target as Element).closest('.issue-pop-x')) cardPop.close(); });
 const playPop = document.createElement('dialog'); playPop.className = 'rr-play-pop';
 playPop.innerHTML = '<button type="button" class="issue-pop-x" aria-label="close">✕</button>';
 l.add(playPop, document.body);
 // a fresh iframe each time: closing removes it, which stops its music
 pl.addEventListener('click', () => { const u = new URL(playA.href); u.search = '?embed=1'; playPop.querySelector('iframe')?.remove(); const f = document.createElement('iframe'); f.title = 'player'; f.src = u.href; playPop.append(f); playPop.showModal(); });
 const closePlay = () => { playPop.querySelectorAll('iframe').forEach(f => { f.src = 'about:blank'; f.remove(); }); playPop.close(); };   // removing the player stops its music
 playPop.addEventListener('close', () => { playPop.querySelector('iframe')?.remove(); });
 playPop.querySelector('.issue-pop-x')!.addEventListener('click', closePlay);
 // in All (no piece) the packing and its buttons go away with the card
 const syncPack = () => { pack.hidden = card.hidden; };
 const packObserver = new MutationObserver(syncPack); packObserver.observe(card, {attributes: true, attributeFilter: ['hidden']}); syncPack();
 // introduction → popup behind an "i" button
 const lede = host.querySelector('.lede') as HTMLElement | null;
 const info = document.createElement('dialog'); info.className = 'issue-pop rr-info';
 info.innerHTML = '<button type="button" class="issue-pop-x" aria-label="close">✕</button>' + (lede?.querySelector('.lede-l')?.innerHTML || '');
 l.add(info, host);
 const ib = document.createElement('button'); ib.type = 'button'; ib.className = 'rr-info-btn'; ib.textContent = 'i'; ib.setAttribute('aria-label', 'about this page'); l.add(ib, document.body);
 if (lede) lede.hidden = true;
 ib.addEventListener('click', () => info.showModal());
 info.addEventListener('click', e => { if (e.target === info || (e.target as Element).closest('.issue-pop-x')) info.close(); });
 // k choice → popup from the bottom right
 const sel = host.querySelector('.rr-sel')!;
 const pick = document.createElement('dialog'); pick.className = 'issue-pop rr-k-pick'; pick.setAttribute('aria-label', 'k');
 l.add(pick, host); l.move(sel, pick);
 const kb = document.createElement('button'); kb.type = 'button'; kb.className = 'rr-fab rr-fab-k'; kb.setAttribute('aria-label', 'k');
 // the k button shows k small squares (a 2 × 2 grid of squares for All)
 const showK = () => { const on = sel.querySelector('[data-sel][aria-pressed="true"]') as HTMLElement | null; kb.innerHTML = on && on.dataset.sel !== 'all' ? squaresIcon(+on.dataset.sel!) + `<small>${on.dataset.sel}</small>` : squaresIcon(4) + '<small>All</small>'; };
 kb.addEventListener('click', () => pick.showModal());
 pick.addEventListener('click', e => { if (e.target === pick || (e.target as Element).closest('[data-sel]')) pick.close(); });
 const observer = new MutationObserver(showK); observer.observe(sel, {subtree: true, attributes: true, attributeFilter: ['aria-pressed']});
 // the pieces: a list in a popup, opened from a round button above the k button (hidden in All, where there are no pieces)
 const ptab = host.querySelector('[data-o="ptab"]') as HTMLElement;
 const pp = document.createElement('dialog'); pp.className = 'issue-pop rr-piece-pick'; pp.setAttribute('aria-label', 'pieces');
 l.add(pp, host.querySelector('#rr')!); l.move(ptab, pp);
 const pb = document.createElement('button'); pb.type = 'button'; pb.className = 'rr-fab'; pb.setAttribute('aria-label', 'pieces'); row.append(pb, kb);
 pb.innerHTML = '<svg viewBox="0 0 24 24" width="22" height="22" aria-hidden="true"><path d="M3 5c4 0 5 5 8 7s6 1 10 1M3 20h18M3 4v16" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round"/></svg>';
 const showP = () => { pb.hidden = ptab.hidden; };
 pb.addEventListener('click', () => { pp.showModal(); (ptab.querySelector('tr.on') as HTMLElement | null)?.scrollIntoView({block: 'center'}); });
 pp.addEventListener('click', e => { if (e.target === pp) { pp.close(); return; } const tr = (e.target as Element).closest('tr'); if (tr && !(e.target as Element).closest('a')) setTimeout(() => pp.close(), 0); });
 const pObserver = new MutationObserver(showP); pObserver.observe(ptab, {subtree: true, childList: true, attributes: true, attributeFilter: ['class', 'hidden']});
 mountShared(host); showK(); showP();
 const undoIcons = iconKButtons(sel, 'data-sel');
 return () => { undoIcons(); packObserver.disconnect(); playA.hidden = false; cardPop.close(); playPop.close(); observer.disconnect(); pObserver.disconnect(); pp.close(); info.close(); pick.close(); if (lede) lede.hidden = false; l.cleanup(); };
}
