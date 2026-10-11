/** Reading-table interactions, ported from site.js. No framework or network requests. */
function init() {
 type Control = HTMLInputElement | HTMLSelectElement;
 const lang = () => document.documentElement.lang === 'ja' ? 'ja' : 'en';
 function labels() {
  document.querySelectorAll<HTMLOptionElement>('option[data-en]').forEach(o => { o.textContent = o.getAttribute('data-' + lang()); });
  document.querySelectorAll<HTMLInputElement>('[data-ph-en]').forEach(el => { el.placeholder = el.getAttribute('data-ph-' + lang()) || ''; });
 }
 document.addEventListener('langchange', labels);
 labels();
 document.querySelectorAll<HTMLElement>('[data-filterbar]').forEach(bar => {
  const tb = document.getElementById(bar.dataset.filterbar!);
  if (!tb) return;
  const count = bar.querySelector('.count'), controls = [...bar.querySelectorAll<Control>('[data-key]')];
  const heads = [...tb.closest('table')!.querySelectorAll<HTMLElement>('th.sort')];
  const original = [...tb.querySelectorAll<HTMLTableRowElement>('tr.r')];
  const pairs = original.map(tr => ({tr, detail: tr.nextElementSibling?.classList.contains('x') ? tr.nextElementSibling as HTMLElement : null}));
  // Card labels duplicate headers, so exclude them from the original row search text.
  const searchText = new Map(original.map(tr => { const clone = tr.cloneNode(true) as HTMLElement; clone.querySelectorAll('.cell-label').forEach(el => el.remove()); return [tr,(clone.textContent || '').toLowerCase()]; }));
  let sortKey = '', direction = 'a';
  const value = (c: Control) => c instanceof HTMLInputElement && c.type === 'checkbox' ? (c.checked ? '1' : '') : c.value.trim();
  function apply() {
   let n = 0;
   pairs.forEach(({tr,detail}) => {
    const ok = controls.every(c => { const k = c.dataset.key!, v = value(c); if (!v) return true;
     if (k === 'q') return searchText.get(tr)!.includes(v.toLowerCase());
     if (k === 'nmin') return Number(tr.dataset.n) >= +v;
     if (k === 'nmax') return Number(tr.dataset.n) <= +v;
     return (tr.dataset[k] || '') === v;
    });
    if (ok) n++;
    tr.hidden = !ok;
    if (detail) detail.hidden = !ok || !tr.classList.contains('open');
   });
   if (count) count.textContent = `${n} / ${original.length}`;
  }
  function sort() {
   const sorted = [...pairs];
   if (sortKey) sorted.sort((a,b) => { const p = a.tr.dataset[sortKey], q = b.tr.dataset[sortKey]; const c = ['n','v'].includes(sortKey) ? Number(p)-Number(q) : String(p).localeCompare(String(q)); return direction === 'a' ? c : -c; });
   for (const {tr,detail} of sorted) { tb!.appendChild(tr); if (detail) tb!.appendChild(detail); }
   heads.forEach(th => th.setAttribute('aria-sort', th.dataset.sort === sortKey ? direction === 'a' ? 'ascending' : 'descending' : 'none'));
  }
  function save() {
   const u = new URL(location.href);
   controls.forEach(c => { const checkbox = c instanceof HTMLInputElement && c.type === 'checkbox'; const v = checkbox ? c.checked ? '1' : '0' : c.value.trim(); const def = checkbox ? c.defaultChecked ? '1' : '0' : ''; if (v === def) u.searchParams.delete(c.dataset.key!); else u.searchParams.set(c.dataset.key!,v); });
   if (sortKey) { u.searchParams.set('sort',sortKey); u.searchParams.set('dir',direction); } else { u.searchParams.delete('sort'); u.searchParams.delete('dir'); }
   if (u.href !== location.href) history.pushState(null,'',u);
  }
  function restore() {
   const p = new URL(location.href).searchParams;
   controls.forEach(c => { const k = c.dataset.key!; if (c instanceof HTMLInputElement && c.type === 'checkbox') c.checked = p.has(k) ? p.get(k) !== '0' : c.defaultChecked; else { c.value = p.get(k) || ''; if (c instanceof HTMLSelectElement && c.selectedIndex < 0) c.value = ''; } });
   sortKey = heads.some(th => th.dataset.sort === p.get('sort')) ? p.get('sort')! : '';
   direction = p.get('dir') === 'd' ? 'd' : 'a'; sort(); apply();
  }
  const changed = () => { apply(); save(); };
  bar.addEventListener('input',changed); bar.addEventListener('change',changed);
  heads.forEach(th => {
   th.tabIndex = 0;
   const run = () => { direction = sortKey === th.dataset.sort && direction === 'a' ? 'd' : 'a'; sortKey = th.dataset.sort!; sort(); save(); };
   th.addEventListener('click',run);
   th.addEventListener('keydown',e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); run(); } });
  });
  window.addEventListener('popstate',restore); restore();
 });
 document.querySelectorAll<HTMLTableRowElement>('tr.r').forEach((tr,i) => {
  const detail = tr.nextElementSibling as HTMLElement | null;
  if (!detail?.classList.contains('x')) return;
  tr.tabIndex = 0; tr.setAttribute('aria-expanded','false');
  detail.id ||= `row-detail-${i}`; tr.setAttribute('aria-controls',detail.id);
  const toggle = (e: Event) => { if ((e.target as Element).closest('a,button,input,select')) return; tr.classList.toggle('open'); detail.hidden = !tr.classList.contains('open'); tr.setAttribute('aria-expanded',String(!detail.hidden)); };
  tr.addEventListener('click',toggle);
  tr.addEventListener('keydown',e => { if (e.target === tr && (e.key === 'Enter' || e.key === ' ')) { e.preventDefault(); toggle(e); } });
 });
}
if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded',init,{once:true}); else init();
