// Preserve the old site's external-link target and icon on every reading page.
function external(a: HTMLAnchorElement) {
 if (!/^https?:/.test(a.getAttribute('href') || '') || a.host === location.host) return;
 a.target = '_blank'; a.rel = 'noopener';
 if (!a.classList.contains('gh')) a.classList.add('ext');
}
document.querySelectorAll<HTMLAnchorElement>('a[href]').forEach(external);
new MutationObserver(mutations => {
 for (const m of mutations) {
  if (m.type === 'attributes') { if (m.target instanceof HTMLAnchorElement) external(m.target); continue; }
  for (const n of m.addedNodes) { if (!(n instanceof Element)) continue; if (n instanceof HTMLAnchorElement) external(n); n.querySelectorAll<HTMLAnchorElement>('a[href]').forEach(external); }
 }
}).observe(document.body,{childList:true,subtree:true,attributes:true,attributeFilter:['href']});
