import {mountShared} from '../shared/containers';
import {layout, bi} from './layout';
// Phone view of Other containers: the container and n are chosen from a list grouped by container, in a popup opened
// from a round button at the bottom right; the display checkboxes above the figure; the angle and "keep inside" under it.
export function mountPhone(host: HTMLElement) {
 const l = layout();
 const root = host.querySelector('#ct')!;
 const picker = host.querySelector('.ct-pick') as HTMLElement;
 const fig = host.querySelector('.cv-fig')!;
 const canvas = fig.querySelector('canvas')!;
 const shows = fig.querySelector('.bar')!;
 const angle = host.querySelector('#ct-a')!.closest('label')!;
 const keep = host.querySelector('#ct-keep')!.closest('label')!;
 l.move(angle, fig); l.move(keep, fig);
 // the display checkboxes: only in a floating panel opened by the eye button at the top right
 const vb = document.createElement('button'); vb.type = 'button'; vb.className = 'rr-info-btn ct-view-btn'; vb.setAttribute('aria-label', 'display'); vb.setAttribute('aria-expanded', 'false');
 vb.innerHTML = '<svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true"><path d="M2 12s3.6-6.5 10-6.5S22 12 22 12s-3.6 6.5-10 6.5S2 12 2 12z" fill="none" stroke="currentColor" stroke-width="1.8"/><circle cx="12" cy="12" r="3" fill="none" stroke="currentColor" stroke-width="1.8"/></svg>';
 const panel = document.createElement('div'); panel.className = 'ct-view-pop'; panel.hidden = true;
 l.add(vb, document.body); l.add(panel, root); l.move(shows, panel);
 const setOpen = (o: boolean) => { panel.hidden = !o; vb.setAttribute('aria-expanded', String(o)); };
 vb.addEventListener('click', e => { e.stopPropagation(); setOpen(panel.hidden); });
 const outside = (e: Event) => { if (!panel.hidden && !panel.contains(e.target as Node) && e.target !== vb) setOpen(false); };
 document.addEventListener('click', outside);
 const keepHtml = keep.innerHTML;
 keep.innerHTML = keep.innerHTML.replace(/<span data-l="en">[^<]*<\/span><span data-l="ja">[^<]*<\/span>/, bi('Keep inside', '容器に収める'));
 picker.hidden = true;
 const names: Record<string, [string, string]> = {'triangle': ['Equilateral triangle', '正三角形'], 'right-isosceles': ['Right isosceles triangle', '直角二等辺三角形'], 'hexagon': ['Regular hexagon', '正六角形'], 'domino': ['1×2 rectangle', '1×2 の長方形']};
 const keys = Object.keys(names);
 const pick = document.createElement('dialog'); pick.className = 'issue-pop ct-pick-pop'; pick.setAttribute('aria-label', 'container and n');
 l.add(pick, root);
 const nb = document.createElement('button'); nb.type = 'button'; nb.className = 'cert-n-btn'; nb.setAttribute('aria-label', 'container and n'); l.add(nb, document.body);
 const bars = () => Array.from(picker.querySelectorAll('.bar'));
 const build = (claims: Record<string, string>) => {
  pick.innerHTML = bars().map((bar, i) => `<h3>${bi(...names[keys[i]] as [string, string])}</h3><div class="ct-pick-list">` +
   Array.from(bar.querySelectorAll('button')).map((b, j) => `<button type="button" data-ci="${i}" data-bj="${j}" aria-pressed="${b.getAttribute('aria-pressed')}"><span class="num">n = ${b.textContent!.trim()}</span><span class="dim">${claims[keys[i] + '-' + b.textContent!.trim()] || ''}</span></button>`).join('') + '</div>').join('');
 };
 const show = () => {
  const on = picker.querySelector('[aria-pressed="true"]'); const i = bars().findIndex(b => b.contains(on));
  nb.innerHTML = i >= 0 && on ? `${['△', '◺', '⬡', '▭'][i]} ${on.textContent!.trim()}` : 'n';
  pick.querySelectorAll('[data-ci]').forEach(b => b.setAttribute('aria-pressed', String(bars()[+(b as HTMLElement).dataset.ci!]?.querySelectorAll('button')[+(b as HTMLElement).dataset.bj!] === on)));
 };
 let claims: Record<string, string> = {};
 fetch(import.meta.env.BASE_URL.replace(/\/?$/, '/') + 'data/containers.json').then(r => r.json()).then((all: {cont: string; n: number | string; claim: string}[]) => {
  claims = Object.fromEntries(all.map(x => [x.cont + '-' + x.n, x.claim])); build(claims); show();
 }).catch(() => { build({}); show(); });
 nb.addEventListener('click', () => { pick.showModal(); (pick.querySelector('[aria-pressed="true"]') as HTMLElement | null)?.scrollIntoView({block: 'center'}); });
 pick.addEventListener('click', e => {
  const b = (e.target as Element).closest<HTMLElement>('[data-ci]');
  if (b) { (bars()[+b.dataset.ci!].querySelectorAll('button')[+b.dataset.bj!] as HTMLButtonElement).click(); pick.close(); return; }
  if (e.target === pick) pick.close();
 });
 // the picker is filled once the data has loaded: build the list then
 const observer = new MutationObserver(() => { if (pick.querySelectorAll('[data-ci]').length !== picker.querySelectorAll('.bar button').length) build(claims); show(); }); observer.observe(picker, {subtree: true, childList: true, attributes: true, attributeFilter: ['aria-pressed']});
 mountShared(host); build(claims); show();
 return () => { document.removeEventListener('click', outside); observer.disconnect(); pick.close(); picker.hidden = false; keep.innerHTML = keepHtml; l.cleanup(); };
}
