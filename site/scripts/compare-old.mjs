/** Compare the long desktop reading content, including expandable details, in both languages.
 * Short phone ledes and duplicated card labels are new UI, excluded explicitly.
 * The shared shell is checked separately. Build with SP_PREVIEW=1 to match the reference.
 * Usage: SP_PREVIEW=1 npx astro build && node scripts/compare-old.mjs
 * --strict also fails on the intentionally unavailable paper links.
 */
import {readFileSync} from 'node:fs';
import {resolve} from 'node:path';
import {parse} from 'parse5';
const files = ['index','guide','outcomes','themes','results','releases','methods','verify','about','certificate','containers','rect-regions','rect-player'];
const oldRoot = resolve(process.env.SP_OLD_SITE || '../site-draft/_site');
const newRoot = resolve('dist');
const attr = (n,k) => n.attrs?.find(a => a.name === k)?.value;
const has = (n,c) => (attr(n,'class') || '').split(/\s+/).includes(c);
function find(n,p) { if (p(n)) return n; for (const c of n.childNodes || []) { const v = find(c,p); if (v) return v; } }
function excluded(n,lang,details) { return ['script','style','svg'].includes(n.tagName) || (attr(n,'data-l') && attr(n,'data-l') !== lang) || has(n,'lede-s') || has(n,'cell-label') || (!details && n.attrs?.some(a => a.name === 'hidden')); }
const blocks = new Set(['p','div','section','h1','h2','h3','tr','td','th','dt','dd','li','ul','ol','pre','label','option','table','thead','tbody']);
function text(n,lang,details = true) {
 if (excluded(n,lang,details)) return '';
 if (n.nodeName === '#text') return n.value;
 const t = (n.childNodes || []).map(c => text(c,lang,details)).join('');
 return blocks.has(n.tagName) ? ' '+t+' ' : t;
}
const norm = s => s.replace(/\s+/gu,' ').trim();
function links(n,lang) {
 if (excluded(n,lang,true)) return [];
 const href = n.tagName === 'a' ? attr(n,'href') : undefined;
 return [...(href === undefined ? [] : [normalizeLink(href)]), ...(n.childNodes || []).flatMap(c => links(c,lang))];
}
function normalizeLink(href) {
 if (/^(?:https?:|mailto:)/.test(href)) return href;
 let s = href.replace(/^\/square-packing\/?/,'').replace(/^\.\//,'');
 if (!s || s === 'index.html') return 'index.html';
 return s;
}
function delta(a,b) { const bag = new Map(); for (const s of a) bag.set(s,(bag.get(s)||0)+1); for (const s of b) bag.set(s,(bag.get(s)||0)-1); return [...bag].filter(([,n]) => n !== 0); }
function mismatch(a,b) { let i=0; while(i<a.length && a[i]===b[i]) i++; return {at:i, old:a.slice(Math.max(0,i-55),i+160), new:b.slice(Math.max(0,i-55),i+160)}; }
const sitemap = readFileSync('src/lib/sitemap.ts','utf8');
const available = new Set([...sitemap.matchAll(/file: '([^']+)'/g)].map(m=>m[1]));
let failures = 0, expected = 0;
for (const file of files) {
 const oldDoc = parse(readFileSync(resolve(oldRoot,file+'.html'),'utf8')), newDoc = parse(readFileSync(resolve(newRoot,file+'.html'),'utf8'));
 const oldMain = find(oldDoc,n=>n.tagName==='main'), newMain = find(newDoc,n=>n.tagName==='main');
 // A release reference excludes only the old site's explicitly preview-only navigation/card.
 if (!find(newDoc,n=>n.tagName==='a' && normalizeLink(attr(n,'href')||'')==='explain.html')) {
  const prune=n=>{n.childNodes=(n.childNodes||[]).filter(c=>!(c.tagName==='a' && normalizeLink(attr(c,'href')||'')==='explain.html')); n.childNodes.forEach(prune);};
  prune(oldDoc);
 }
 if (!find(newMain,n=>attr(n,'data-preview')==='1')) {
  const prune=n=>{ n.childNodes=(n.childNodes||[]).filter(c=>!has(c,'pv')&&!has(c,'pv-l')); n.childNodes.forEach(prune); };
  if (['rect-regions','rect-player'].includes(file)) prune(oldMain);
 }
 const report = {page:file+'.html',text:{},links:{}};
 for (const lang of ['en','ja']) {
  const x = norm(text(oldMain,lang)), y = norm(text(newMain,lang));
  report.text[lang] = x===y ? 'PASS (including expanded details)' : mismatch(x,y);
  if (x!==y) failures++;
  const hiddenX=norm(text(oldMain,lang,false)), hiddenY=norm(text(newMain,lang,false));
  if(hiddenX!==hiddenY) { report.text[lang+'Collapsed'] = mismatch(hiddenX,hiddenY); failures++; }
  const changes = delta(links(oldMain,lang),links(newMain,lang));
  const intended = changes.filter(([href,n]) => n>0 && href.startsWith('paper-') && !available.has(href));
  const unexpected = changes.filter(c => !intended.includes(c));
  report.links[lang] = unexpected.length ? {unexpected,intendedUnavailablePapers:intended} : intended.length ? {status:'PASS with sitemap exceptions',intendedUnavailablePapers:intended} : 'PASS';
  failures += unexpected.length; expected += intended.length;
 }
 console.log(JSON.stringify(report));
 // Full-document nav links are reported rather than silently excluded from comparison.
 const oldHeader=find(oldDoc,n=>n.tagName==='header'), newHeader=find(newDoc,n=>n.tagName==='header');
 const shellDelta=delta(links(oldHeader,'en'),links(newHeader,'en'));
 if(shellDelta.length) { console.log(JSON.stringify({page:file+'.html',sharedHeaderLinkDifferences:shellDelta})); failures+=shellDelta.length; }
 const oldTabs=find(oldDoc,n=>has(n,'tabbar')), newTabs=find(newDoc,n=>has(n,'tabbar'));
 const tabsDelta=delta(links(oldTabs,'en'),links(newTabs,'en'));
 if(tabsDelta.length) { console.log(JSON.stringify({page:file+'.html',tabLinkDifferences:tabsDelta})); failures+=tabsDelta.length; }
 for(const lang of ['en','ja']) for(const [name,x,y] of [['header',oldHeader,newHeader],['tabs',oldTabs,newTabs]]) {
  // Navigation anchors are separate controls even when the HTML omits whitespace between them.
  const shellText=n=>norm((n.childNodes||[]).map(c=>text(c,lang)).join(' ')).replace(/\s+/g,'');
  if(shellText(x)!==shellText(y)) {console.log(JSON.stringify({page:file+'.html',shell:name,lang,difference:mismatch(shellText(x),shellText(y))}));failures++;}
 }
}
console.log(`Comparison: ${files.length} pages; ${failures} unexpected differences; ${expected} explicit sitemap exceptions (counted per page/language).`);
process.exitCode = failures || (process.argv.includes('--strict') && expected) ? 1 : 0;
