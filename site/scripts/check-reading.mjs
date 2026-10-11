/** Offline Chromium smoke checks. CDP travels over pipes, all page requests are fulfilled
 * from dist or blocked; no HTTP server, network downloads, or extra npm packages. */
import {spawn} from 'node:child_process';
import {readFileSync, mkdtempSync, rmSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {resolve, extname, join} from 'node:path';
import assert from 'node:assert/strict';
const profile = mkdtempSync(join(tmpdir(),'sp-reading-'));
const browser = spawn(process.env.CHROME_BIN || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', [
 '--headless=new','--remote-debugging-pipe','--no-first-run','--no-default-browser-check','--disable-background-networking','--disable-component-update','--disable-sync','--disable-default-apps','--disable-domain-reliability','--disable-extensions','--metrics-recording-only','--no-pings','--host-resolver-rules=MAP * ~NOTFOUND',`--user-data-dir=${profile}`,'about:blank'
], {stdio:['ignore','ignore','pipe','pipe','pipe']});
let sequence=0, buffer='', diagnostics='';
browser.stdio[3].on('error',()=>{});
const pending=new Map(), listeners=new Set();
browser.stderr.on('data',b=>diagnostics+=b);
browser.on('error',e=>{for(const p of pending.values()) p.reject(e);});
browser.on('exit',()=>{for(const p of pending.values()) p.reject(new Error('Chromium exited: '+diagnostics.slice(-1000)));});
browser.stdio[4].on('data',b=>{
 buffer+=b.toString(); let i;
 while((i=buffer.indexOf('\0'))>=0) {
  const msg=JSON.parse(buffer.slice(0,i)); buffer=buffer.slice(i+1);
  if(msg.id) {const p=pending.get(msg.id); pending.delete(msg.id); if(p) msg.error ? p.reject(new Error(JSON.stringify(msg.error))) : p.resolve(msg.result);}
  else for(const fn of listeners) fn(msg);
 }
});
function call(method,params={},sessionId) {
 if(browser.exitCode!==null || browser.signalCode) return Promise.reject(new Error('Chromium exited: '+diagnostics.slice(-1500)));
 const id=++sequence;
 return new Promise((resolve,reject)=>{pending.set(id,{resolve,reject}); browser.stdio[3].write(JSON.stringify({id,method,params,...(sessionId?{sessionId}:{})})+'\0');});
}
let session;
const cmd=(m,p={})=>call(m,p,session);
const errors=[];
listeners.add(msg=>{
 if(msg.method==='Runtime.exceptionThrown') errors.push(msg.params.exceptionDetails.text+': '+JSON.stringify(msg.params.exceptionDetails.exception));
 if(msg.method==='Fetch.requestPaused') {
  const {requestId,request}=msg.params;
  const u=new URL(request.url), rel=decodeURIComponent(u.pathname.replace(/^\/square-packing\/?/,'')) || 'index.html';
  let body='',status=204,type='text/plain';
  if(u.hostname==='reading.invalid' && !rel.includes('..')) {
   try {body=readFileSync(resolve('dist',rel)).toString('base64'); status=200; type=({'.html':'text/html','.js':'text/javascript','.css':'text/css','.json':'application/json','.svg':'image/svg+xml','.woff2':'font/woff2'})[extname(rel)]||'application/octet-stream';} catch {status=404;}
  }
  call('Fetch.fulfillRequest',{requestId,responseCode:status,responseHeaders:[{name:'Content-Type',value:type}],body},msg.sessionId).catch(e=>errors.push(e.message));
 }
});
async function evaluate(expression) {
 const r=await cmd('Runtime.evaluate',{expression,returnByValue:true,awaitPromise:true});
 if(r.exceptionDetails) throw new Error(JSON.stringify(r.exceptionDetails));
 return r.result.value;
}
async function navigate(file,query='') {
 const loaded=new Promise(resolve=>{const f=m=>{if(m.sessionId===session && m.method==='Page.loadEventFired'){listeners.delete(f);resolve();}};listeners.add(f);});
 await cmd('Page.navigate',{url:`https://reading.invalid/square-packing/${file}${query}`}); await loaded;
}
try {
 await call('Browser.getVersion');
 const {targetId}=await call('Target.createTarget',{url:'about:blank'});
 ({sessionId:session}=await call('Target.attachToTarget',{targetId,flatten:true}));
 await cmd('Fetch.enable',{patterns:[{urlPattern:'*'}]});
 await cmd('Page.enable'); await cmd('Runtime.enable');
 await cmd('Emulation.setDeviceMetricsOverride',{width:1280,height:900,deviceScaleFactor:1,mobile:false});
 await navigate('results.html');
 assert.equal(await evaluate(`document.querySelector('.count').textContent`),await evaluate(`document.querySelectorAll('#res tr.r[data-best="1"]').length+' / '+document.querySelectorAll('#res tr.r').length`));
 assert.equal(await evaluate(`getComputedStyle(document.querySelector('.lede-l')).display`),'block');
 const count = await evaluate(`document.querySelectorAll('#res tr.r:not([hidden])').length`);
 assert(count>0);
 await evaluate(`document.getElementById('f-cont').value='hexagon';document.getElementById('f-cont').dispatchEvent(new Event('change',{bubbles:true}))`);
 assert.equal(await evaluate(`document.querySelectorAll('#res tr.r:not([hidden])').length`),1);
 assert.equal(await evaluate(`new URL(location.href).searchParams.get('cont')`),'hexagon');
 await evaluate(`document.querySelector('#res tr.r:not([hidden])').click()`);
 assert.equal(await evaluate(`document.querySelector('#res tr.r:not([hidden])').getAttribute('aria-expanded')`),'true');
 assert.equal(await evaluate(`document.querySelector('#res tr.r:not([hidden])').nextElementSibling.hidden`),false);
 await evaluate(`document.querySelector('th[data-sort="n"]').click();document.querySelector('th[data-sort="n"]').click()`);
 assert.equal(await evaluate(`new URL(location.href).searchParams.get('dir')`),'d');
 await navigate('results.html','?cont=triangle&best=0&sort=n&dir=d');
 assert.equal(await evaluate(`document.getElementById('f-cont').value`),'triangle');
 assert.equal(await evaluate(`document.getElementById('f-best').checked`),false);
 assert.equal(await evaluate(`document.querySelector('th[data-sort="n"]').getAttribute('aria-sort')`),'descending');
 assert.equal(await evaluate(`Array.from(document.querySelectorAll('#res tr.r:not([hidden])')).every(r=>r.dataset.cont==='triangle')`),true);
 await evaluate(`document.getElementById('f-cont').value='hexagon';document.getElementById('f-cont').dispatchEvent(new Event('change',{bubbles:true}));history.back()`);
 await evaluate(`new Promise(resolve=>{if(document.getElementById('f-cont').value==='triangle')resolve();else addEventListener('popstate',()=>resolve(),{once:true});})`);
 assert.equal(await evaluate(`document.getElementById('f-cont').value`),'triangle');
 await evaluate(`document.getElementById('lang').click()`);
 assert.equal(await evaluate(`document.querySelector('option[value="triangle"]').textContent`),'正三角形');
 assert.equal(await evaluate(`document.getElementById('f-q').placeholder`),'文字で絞り込み');
 await evaluate(`document.getElementById('lang').click()`);
 await cmd('Emulation.setTouchEmulationEnabled',{enabled:true});
 await cmd('Emulation.setDeviceMetricsOverride',{width:390,height:844,deviceScaleFactor:1,mobile:true});
 await navigate('results.html');
 assert.equal(await evaluate(`getComputedStyle(document.querySelector('.lede-l')).display`),'none');
 assert.equal(await evaluate(`getComputedStyle(document.querySelector('#res tr.r')).display`),'block');
 assert.equal(await evaluate(`getComputedStyle(document.querySelector('#res .cell-label')).display`),'none');
 assert.equal(await evaluate(`getComputedStyle(document.querySelector('#res .result-phone')).display`),'block');
 assert(await evaluate(`document.querySelector('#res tr.r:not([hidden])').getBoundingClientRect().height<=80`),'compact result card');
 const card=await evaluate(`(()=>{const e=document.querySelector('#res tr.r:not([hidden])');e.scrollIntoView({block:'center'});const r=e.getBoundingClientRect();return {x:r.x+30,y:r.y+r.height/2,id:1}})()`);
 await cmd('Input.dispatchTouchEvent',{type:'touchStart',touchPoints:[card]});
 await cmd('Input.dispatchTouchEvent',{type:'touchEnd',touchPoints:[]});
 assert.equal(await evaluate(`document.querySelector('#res tr.r:not([hidden])').nextElementSibling.hidden`),false);
 await evaluate(`document.getElementById('lang').click()`);
 assert(await evaluate(`document.querySelector('#res .result-phone [data-l=ja]').getBoundingClientRect().width>0`));
 await evaluate(`document.getElementById('lang').click()`);
 assert.equal(await evaluate(`getComputedStyle(document.querySelector('.bar')).flexWrap`),'nowrap');
 await evaluate(`document.querySelector('.more').click()`);
 assert.equal(await evaluate(`getComputedStyle(document.querySelector('.lede-l')).display`),'block');
 const pages=['index.html','guide.html','outcomes.html','themes.html','results.html','releases.html','methods.html','verify.html','about.html'];
 for(const page of pages) {
  await navigate(page);
  assert.equal(await evaluate(`document.documentElement.scrollWidth<=innerWidth`),true,page+' overflows phone viewport');
  assert.equal(await evaluate(`Array.from(document.querySelectorAll('button,select,th.sort,a')).every(e=>!e.getClientRects().length||e.getBoundingClientRect().height>=40)`),true,page+' has a short control');
  if(['themes.html','releases.html'].includes(page)) {
   await evaluate(`document.querySelector('tr.r').dispatchEvent(new KeyboardEvent('keydown',{key:'Enter',bubbles:true}))`);
   assert.equal(await evaluate(`document.querySelector('tr.r').nextElementSibling.hidden`),false);
  }
  if(page==='methods.html') {
   await evaluate(`document.getElementById('m-q').value='not-a-real-method-987';document.getElementById('m-q').dispatchEvent(new Event('input',{bubbles:true}))`);
   assert.equal(await evaluate(`document.querySelectorAll('#mt tr.r:not([hidden])').length`),0);
  }
 }
 await cmd('Emulation.setDeviceMetricsOverride',{width:320,height:640,deviceScaleFactor:1,mobile:true});
 await navigate('index.html');
 assert.equal(await evaluate(`document.documentElement.scrollWidth<=innerWidth`),true,'320px home overflow');
 await cmd('Emulation.setTouchEmulationEnabled',{enabled:true});
 await cmd('Emulation.setDeviceMetricsOverride',{width:768,height:1024,deviceScaleFactor:1,mobile:true});
 await navigate('results.html');
 assert.equal(await evaluate(`matchMedia('(pointer: coarse)').matches`),true);
 assert.equal(await evaluate(`getComputedStyle(document.querySelector('#res tr.r')).display`),'block');
 assert.deepEqual(errors,[]);
 console.log('PASS: 9 phone layouts; bilingual labels; row click/keyboard expansion; filtering; sorting; URL restore/back; ledes; touch controls; no browser errors. All page requests fulfilled offline.');
} finally {
 await call('Browser.close').catch(()=>{});
 browser.kill();
 rmSync(profile,{recursive:true,force:true,maxRetries:5,retryDelay:100});
}
