import {mountShared} from '../shared/certificate';
import {layout, bi} from './layout';
export function mountPhone(host: HTMLElement) {
 const l = layout();
 const fig = host.querySelector('.cv-fig')!;
 l.move(host.querySelector('[data-o="m"]')!.closest('dl')!, fig);
 // the direction slider and "keep inside" (short label) right under the figure
 const canvas = fig.querySelector('canvas.m')!;
 const dir = host.querySelector('#cv-r')!.closest('label')!, keep = host.querySelector('#cv-keep')!.closest('label')!;
 const row = keep.parentElement!, scanResult = row.nextElementSibling!;   // keep and the scan button share a row; the result follows
 l.move(scanResult, fig, canvas.nextSibling); l.move(row, fig, canvas.nextSibling); l.move(dir, fig, canvas.nextSibling);
 const keepHtml = keep.innerHTML;
 keep.innerHTML = keep.innerHTML.replace(/<span data-l="en">[^<]*<\/span><span data-l="ja">[^<]*<\/span>/, bi('Keep inside', '容器に収める'));
 const heading = host.querySelector('.cv-main > h2')!;
 const states = document.createElement('details'); states.className = 'phone-section';
 const summary = document.createElement('summary'); summary.innerHTML = heading.innerHTML;
 states.append(summary); l.add(states, heading.parentElement!);
 l.move(heading, states); (heading as HTMLElement).hidden = true;
 l.move(host.querySelector('[data-states]')!, states);
 const scan = document.createElement('details'); scan.className = 'phone-section';
 scan.innerHTML = `<summary>${bi('Scan this direction', 'この角度を走査')}</summary>`;
 const note = host.querySelector('[data-scan-note]')!;
 l.add(scan, host.querySelector('.cv-side')!);
 l.move(host.querySelector('[data-kind="rect"]')!, scan);
 // the strip and the note go in the section
 l.move(note, scan);
 const scanBtn = host.querySelector('#cv-scan') as HTMLElement, scanHtml = scanBtn.innerHTML; scanBtn.innerHTML = bi('Scan this angle', 'この角度を走査');
 // the n list: in a popup opened from a round button at the bottom right (above the tab bar), as a list
 const list = host.querySelector('.cv-list')!;
 const pick = document.createElement('dialog'); pick.className = 'issue-pop cert-pick'; pick.setAttribute('aria-label', 'n');
 l.add(pick, host.querySelector('#cv')!); l.move(list, pick);   // inside #cv, where the controller looks for the list
 const nb = document.createElement('button'); nb.type = 'button'; nb.className = 'cert-n-btn'; nb.setAttribute('aria-label', 'n'); l.add(nb, document.body);
 const showN = () => { const on = list.querySelector('[data-cert][aria-pressed="true"]') as HTMLElement | null; nb.textContent = on ? 'n ' + on.dataset.n : 'n'; };
 nb.addEventListener('click', () => { pick.showModal(); (list.querySelector('[aria-pressed="true"]') as HTMLElement | null)?.scrollIntoView({block: 'center'}); });
 pick.addEventListener('click', e => { if (e.target === pick || (e.target as Element).closest('[data-cert]')) pick.close(); });
 const nObserver = new MutationObserver(showN); nObserver.observe(list, {subtree: true, attributes: true, attributeFilter: ['aria-pressed']});
 mountShared(host);
 showN();
 return () => { nObserver.disconnect(); pick.close(); (heading as HTMLElement).hidden = false; keep.innerHTML = keepHtml; scanBtn.innerHTML = scanHtml; l.cleanup(); };
}
