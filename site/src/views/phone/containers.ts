import {mountShared} from '../shared/containers';
import {layout, bi} from './layout';
// Phone view of Other containers: one row with the container selector and the n chips; the display checkboxes
// above the figure; the angle right under it, then "keep inside" (short label).
export function mountPhone(host: HTMLElement) {
 const l = layout();
 const picker = host.querySelector('.ct-pick')!;
 const fig = host.querySelector('.cv-fig')!;
 const canvas = fig.querySelector('canvas')!;
 const shows = fig.querySelector('.bar')!;
 const angle = host.querySelector('#ct-a')!.closest('label')!;
 const keep = host.querySelector('#ct-keep')!.closest('label')!;
 const names = [['triangle','Equilateral triangle','正三角形'],['right-isosceles','Right isosceles triangle','直角二等辺三角形'],['hexagon','Regular hexagon','正六角形'],['domino','1×2 rectangle','1×2 の長方形']];
 const ja = () => document.documentElement.lang === 'ja';
 const row = document.createElement('div'); row.className = 'phone-ct-row';
 const sel = document.createElement('select'); sel.className = 'phone-ct-select'; sel.setAttribute('aria-label', 'container');
 const label = () => { sel.innerHTML = names.map(([key, en, j]) => `<option value="${key}">${ja() ? j : en}</option>`).join(''); };
 label();
 row.append(sel);
 l.add(row, picker.parentElement!); l.move(row, picker.parentElement!, picker); l.move(picker, row);
 l.move(shows, fig, canvas);                       // checkboxes above the figure
 l.move(angle, fig);                               // the angle right under the figure
 l.move(keep, fig);                                // then "keep inside"
 const longText = keep.innerHTML;
 keep.innerHTML = keep.innerHTML.replace(/<span data-l="en">[^<]*<\/span><span data-l="ja">[^<]*<\/span>/, bi('Keep inside', '容器に収める'));
 // the controller's own listeners are on the input, which is kept
 const sync = () => {
  const selected = picker.querySelector('[aria-pressed="true"]');
  const bar = selected?.closest('.bar');
  picker.querySelectorAll('.bar').forEach(el => el.classList.toggle('phone-container-active', el === bar));
  const index = Array.from(picker.querySelectorAll('.bar')).indexOf(bar!);
  if (index >= 0) sel.value = names[index][0];
 };
 sel.addEventListener('change', () => {
  const index = names.findIndex(n => n[0] === sel.value);
  picker.querySelectorAll('.bar')[index]?.querySelector<HTMLButtonElement>('button')?.click();
 });
 const onLang = () => { const v = sel.value; label(); sel.value = v; };
 document.addEventListener('langchange', onLang);
 const observer = new MutationObserver(sync); observer.observe(picker,{subtree:true,childList:true,attributes:true,attributeFilter:['aria-pressed']});
 mountShared(host); sync();
 return () => { observer.disconnect(); document.removeEventListener('langchange', onLang); keep.innerHTML = longText; picker.querySelectorAll('.bar').forEach(el => el.classList.remove('phone-container-active')); l.cleanup(); };
}
