/** Offline Chromium smoke checks. CDP travels over pipes, all page requests are fulfilled
 * from dist or blocked; no HTTP server, network downloads, or extra npm packages. */
import {spawn} from 'node:child_process';
import {once} from 'node:events';
import {rm} from 'node:fs/promises';
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
 if(process.env.SP_TEST_TRACE)console.log(method);
 return new Promise((resolve,reject)=>{const timer=setTimeout(()=>{pending.delete(id);reject(new Error('CDP timeout: '+method+' '+errors.join(' ')));},20000);pending.set(id,{resolve:v=>{clearTimeout(timer);resolve(v)},reject:e=>{clearTimeout(timer);reject(e)}}); browser.stdio[3].write(JSON.stringify({id,method,params,...(sessionId?{sessionId}:{})})+'\0');});
}
let session;
const cmd=(m,p={})=>call(m,p,session);
const errors=[];
let requests=[], currentFile='';
let heldPath=null, heldResponses=[];
const data=JSON.parse(readFileSync('dist/data/rect-regions.json','utf8'));
const preview=readFileSync('dist/rect-regions.html','utf8').includes('data-preview="1"');
assert.equal(Math.max(...data.ks.map(k=>k.k)),preview?20:15);
if(!preview)assert(!readFileSync('dist/rect-regions.html','utf8').includes('data-sel="16"'));
listeners.add(msg=>{
 if(msg.method==='Log.entryAdded' && msg.params.entry.level==='error') errors.push(msg.params.entry.text);
 if(msg.method==='Runtime.consoleAPICalled' && msg.params.type==='error') errors.push(JSON.stringify(msg.params.args));
 if(msg.method==='Runtime.exceptionThrown') errors.push(msg.params.exceptionDetails.text+': '+JSON.stringify(msg.params.exceptionDetails.exception));
 if(msg.method==='Fetch.requestPaused') {
  const {requestId,request}=msg.params;
  const referer=Object.entries(request.headers).find(([k])=>k.toLowerCase()==='referer')?.[1];
  if(!referer || referer.includes('/'+currentFile+'?'))requests.push(request.url);
  const u=new URL(request.url), rel=decodeURIComponent(u.pathname.replace(/^\/square-packing\/?/,'')) || 'index.html';
  let body='',status=204,type='text/plain';
  if(u.hostname==='reading.invalid' && !rel.includes('..')) {
   try {body=readFileSync(resolve('dist',rel)).toString('base64'); status=200; type=({'.html':'text/html','.js':'text/javascript','.css':'text/css','.json':'application/json','.svg':'image/svg+xml','.woff2':'font/woff2','.mp3':'audio/mpeg'})[extname(rel)]||'application/octet-stream';} catch {status=404;errors.push('Missing local asset: '+rel);}
  }
  const respond=()=>call('Fetch.fulfillRequest',{requestId,responseCode:status,responseHeaders:[{name:'Content-Type',value:type}],body},msg.sessionId).catch(e=>errors.push(e.message));
  if(rel===heldPath)heldResponses.push(respond);else respond();
 }
});
async function evaluate(expression,userGesture=false) {
 const r=await cmd('Runtime.evaluate',{expression,userGesture,returnByValue:true,awaitPromise:true});
 if(r.exceptionDetails) throw new Error(JSON.stringify(r.exceptionDetails));
 return r.result.value;
}
let navSequence=0;
async function navigate(file,query='') {
 requests=[];currentFile=file;
 let timer, listener;
 const loaded=new Promise((resolve,reject)=>{
  listener=m=>{if(m.sessionId===session && m.method==='Page.loadEventFired'){clearTimeout(timer);listeners.delete(listener);resolve();}};
  listeners.add(listener);
  timer=setTimeout(()=>{listeners.delete(listener);reject(new Error('load timeout '+file));},20000);
 });
 await cmd('Page.navigate',{url:`https://reading.invalid/square-packing/${file}?check=${++navSequence}${query}`});
 await loaded;
}
async function waitFor(expression, label=expression) {
 const until=Date.now()+20000;
 while(Date.now()<until) {
  if(errors.length) throw new Error(errors.join('\n'));
  if(await evaluate(expression)) return;
  await new Promise(r=>setTimeout(r,50));
 }
 throw new Error('Timed out: '+label+' '+await evaluate(`JSON.stringify({hash:location.hash,key:document.querySelector('[data-o=key]')?.textContent,errors:document.body.innerText.slice(-200)})`));
}
const click=selector=>evaluate(`document.querySelector(${JSON.stringify(selector)}).click()`,true);
const text=selector=>evaluate(`document.querySelector(${JSON.stringify(selector)}).textContent`);
async function mouse(selector,points) {
 const r=await evaluate(`(()=>{const r=document.querySelector(${JSON.stringify(selector)}).getBoundingClientRect();return {x:r.x,y:r.y,w:r.width,h:r.height}})()`);
 const point=([x,y])=>({x:r.x+x*r.w,y:r.y+y*r.h});
 await cmd('Input.dispatchMouseEvent',{type:'mouseMoved',...point(points[0])});
 await cmd('Input.dispatchMouseEvent',{type:'mousePressed',button:'left',clickCount:1,...point(points[0])});
 for(const p of points.slice(1))await cmd('Input.dispatchMouseEvent',{type:'mouseMoved',button:'left',buttons:1,...point(p)});
 await cmd('Input.dispatchMouseEvent',{type:'mouseReleased',button:'left',clickCount:1,...point(points.at(-1))});
}
async function touch(selector, points) {
 const r=await evaluate(`(()=>{const e=document.querySelector(${JSON.stringify(selector)});e.scrollIntoView({block:'center'});const r=e.getBoundingClientRect();return {x:r.x,y:r.y,w:Math.min(r.width,innerWidth-r.x-1),h:r.height}})()`);
 const point=([x,y])=>({x:r.x+x*r.w,y:r.y+y*r.h,id:1});
 await cmd('Input.dispatchTouchEvent',{type:'touchStart',touchPoints:[point(points[0])]});
 for(const p of points.slice(1))await cmd('Input.dispatchTouchEvent',{type:'touchMove',touchPoints:[point(p)]});
 await cmd('Input.dispatchTouchEvent',{type:'touchEnd',touchPoints:[]});
}
async function ink(selector) {
 return evaluate(`(()=>{const c=document.querySelector(${JSON.stringify(selector)});return c.width>0&&c.getContext('2d').getImageData(0,0,c.width,c.height).data.some((v,i)=>i%4===3&&v>0)})()`);
}
try {
 await call('Browser.getVersion');
 const {targetId}=await call('Target.createTarget',{url:'about:blank'});
 ({sessionId:session}=await call('Target.attachToTarget',{targetId,flatten:true}));
 await cmd('Fetch.enable',{patterns:[{urlPattern:'*'}]});
 await cmd('Page.enable'); await cmd('Runtime.enable'); await cmd('Log.enable');
 await cmd('Emulation.setDeviceMetricsOverride',{width:1280,height:900,deviceScaleFactor:1,mobile:false});
 await navigate('rect-regions.html','#5-5.1');
 await waitFor(`document.querySelector('[data-o="key"]').textContent.startsWith('5.')`);
 assert(await ink('#rr canvas.reg'));
 assert(!requests.some(u=>u.includes('rect-regions.json')));
 assert.deepEqual(requests.filter(u=>/data\/rect\/k\d+\.json/.test(u)).map(u=>u.split('/').pop()),['k5.json']);
 await click('[data-sel="11"]');
 await waitFor(`document.querySelector('[data-o="key"]').textContent.startsWith('11.')`);
 const before=await text('[data-o="ab"]');
 await mouse('#rr canvas.reg',[[.9,.8],[.65,.6],[.2,.25]]);
 assert.notEqual(await text('[data-o="ab"]'),before,'edge drag updates the card');
 assert(await ink('#rr canvas.pk'));
 const dragged=await text('[data-o="key"]');
 await click('[data-c="last"]');assert.notEqual(await text('[data-o="key"]'),dragged);
 heldPath=`data/rect/k${data.ks.at(-1).k}.json`;
 await click('[data-sel="all"]');
 const delayedUntil=Date.now()+20000;
 while(!heldResponses.length && Date.now()<delayedUntil) {if(errors.length)throw new Error(errors.join('\n'));await new Promise(r=>setTimeout(r,50));}
 assert(heldResponses.length,'All reaches delayed shard');
 assert(await ink('#rr canvas.reg'),'All draws while the last shard is still pending');
 assert.equal(await evaluate('location.hash'),'#all');
 heldPath=null;await Promise.all(heldResponses.splice(0).map(respond=>respond()));
 await waitFor(`performance.getEntriesByType('resource').filter(e=>/data\\/rect\\/k\\d+\\.json/.test(e.name)).length>=${data.ks.length}`);
 const r=await evaluate(`(()=>{const r=document.querySelector('canvas.reg').getBoundingClientRect();return {x:r.x+r.width*.5,y:r.y+r.height*.6}})()`);
 await cmd('Input.dispatchMouseEvent',{type:'mouseMoved',...r});
 await waitFor(`document.querySelector('[data-o="zt"]').textContent.startsWith('b ∈')`);
 assert(await ink('canvas.zm'));
 await mouse('canvas.reg',[[.5,.6]]);
 assert.match(await evaluate('location.hash'),/^#cell-\d+-\d+$/);
 assert.match(await text('[data-o="rh"]'),/Cell/);
 await navigate('rect-regions.html','#11-11.1');
 await waitFor(`document.querySelector('[data-o="key"]').textContent.startsWith('11.1')`);
 await click('#lang');assert.match(await text('[data-o="rh"]'),/入り始める/);await click('#lang');
 const formulaK=data.ks.find(k=>k.pieces.some(p=>p.formula_full&&!p.formula));
 if(formulaK){
  const piece=formulaK.pieces.find(p=>p.formula_full&&!p.formula);
  await click('[data-sel="'+formulaK.k+'"]'); await waitFor(`document.querySelector('#rr-rows tr[data-key="${formulaK.pieces.find(p=>p.formula_full&&!p.formula).key}"]')`);await click('#rr-rows tr[data-key="'+piece.key+'"]');
  await click('[data-o="f"] .fft');assert.equal(await evaluate(`document.querySelector('[data-o="ffw"]').hidden`),false);
  await click('[data-o="f"] .fft');assert.equal(await evaluate(`document.querySelector('[data-o="ffw"]').hidden`),true);
 }
 await navigate('rect-regions.html','#cell-3-2');await waitFor(`document.querySelector('[data-o="rh"]').textContent.startsWith('Cell')`);
 console.log('PASS Rectangles: k, edge drag/card, arrows, All hover zoom, cell, piece URL, bilingual redraw.');
 await navigate('rect-player.html','#5');
 await waitFor(`document.querySelector('[data-o="len"]').textContent.includes('s')`);
 assert(await ink('#rp canvas'));
 assert(!requests.some(u=>u.includes('rect-regions.json')));
 assert.deepEqual(requests.filter(u=>/data\/rect\/k\d+\.json/.test(u)).map(u=>u.split('/').pop()),['k5.json']);
 // No music clock in this assertion: independently test the animation clock.
 await evaluate(`document.querySelector('[data-o="mus"]').checked=false`);
 await click('[data-o="play"]');
 await waitFor(`+document.querySelector('[data-o="scrub"]').value>5`);
 await click('[data-o="play"]');
 await click('[data-k="11"]'); await waitFor('SPTimeline().k===11');
 assert.equal(await evaluate('SPTimeline().k'),11);
 await click('[data-k="all"]'); await waitFor('SPTimeline().k===2'); assert.equal(await evaluate('SPTimeline().k'),2);
 await click('[data-o="restart"]');await waitFor(`+document.querySelector('[data-o="scrub"]').value>2`);
 await click('[data-o="home"]');assert.equal(await evaluate(`+document.querySelector('[data-o="scrub"]').value`),0);
 await navigate('rect-player.html','#all');await waitFor(`typeof SPTimeline==='function'&&document.querySelector('[data-o="len"]').textContent.length>0`);
 assert.equal(await evaluate('SPTimeline().k'),2);
 await waitFor(`SPAudio().ready`,'local music becomes ready');
 await click('[data-o="play"]');await waitFor(`!SPAudio().paused && SPAudio().at>0`,'music playback');await click('[data-o="play"]');
 await cmd('Browser.setDownloadBehavior',{behavior:'deny'});
 await click('[data-o="rec"]');await waitFor(`document.querySelector('[data-o="rec"]').textContent.startsWith('■')`);
 await waitFor(`+document.querySelector('[data-o="scrub"]').value>3`);
 await click('[data-o="rec"]');await waitFor(`document.querySelector('[data-o="rec"]').textContent.startsWith('●')`);
 await click('[data-o="home"]');
 console.log('PASS local music and recording start/stop.');
 console.log('PASS Player: frame, advancing time, k switch, All, restart/home.');
 await navigate('certificate.html');
 await waitFor(`document.querySelector('[data-info="items"]').textContent.length>0`);
 assert(await ink('#cv canvas.m'));
 assert((await text('[data-states]')).includes('Condition checked'));
 await click('.cv-items button[data-k="point"]');
 await waitFor(`document.querySelector('[data-info="items"]').textContent.includes('pts')`);
 const mass=await text('#cv [data-o="m"]');
 await mouse('#cv canvas.m',[[.35,.35],[.7,.65]]);
 assert.notEqual(await text('#cv [data-o="m"]'),mass);
 await click('#cv-scan');await waitFor(`document.querySelector('[data-o="scan"]').textContent.includes('@')`);
 await click('#lang');assert((await text('[data-states]')).includes('検査する条件'));await click('#lang');
 console.log('PASS Certificate: data, measure canvas, sidebar, captured mass, scan, bilingual statement.');
 await navigate('containers.html','#triangle-2');
 await waitFor(`document.querySelector('[data-f="claim"]').textContent.length>0`);
 assert(await ink('#ct canvas'));
 const weight=await text('#ct [data-o="m"]');
 await click('#ct-keep');
 await mouse('#ct canvas',[[.5,.5],[.05,.05]]);
 assert.notEqual(await text('#ct [data-o="m"]'),weight);
 await click('#ct-keep');assert.equal(await text('#ct [data-o="fit"]'),'inside the container');
 await evaluate(`const angle=document.querySelector('#ct-a');angle.value=14;angle.dispatchEvent(new Event('input'))`);
 assert.equal(await evaluate(`document.querySelector('#ct-a').value`),'15');
 console.log('PASS Containers: data, drawing, drag/captured weight, keep inside, angle snap.');
 for(const width of [390,768]) {
  await cmd('Emulation.setTouchEmulationEnabled',{enabled:true});
  await cmd('Emulation.setDeviceMetricsOverride',{width,height:844,deviceScaleFactor:1,mobile:true});
  for(const page of ['rect-regions','rect-player','certificate','containers']){
   await navigate(page+'.html');
   await waitFor(`document.querySelector('[data-interactive]').dataset.view==='phone'`);
   await waitFor(`document.querySelector('${page==='rect-regions'?'#rr [data-o="key"]':page==='rect-player'?'#rp [data-o="len"]':page==='certificate'?'#cv [data-info="items"]':'#ct [data-f="claim"]'}').textContent.length>0`);
   if(width===390) {
    if(page==='rect-player') {
     assert.equal(await evaluate(`document.querySelectorAll('#rp [data-k]:not([data-k=all])').length`),preview?19:14,'phone k sheet range');
     assert.equal(await evaluate(`document.querySelectorAll('#rp [data-k].pv').length`),preview?5:0,'preview chips marked only in preview');
     assert(await evaluate(`document.documentElement.scrollHeight<=innerHeight`),'player must not scroll');
     await evaluate(`document.querySelector('[data-o="mus"]').checked=false`);
     await touch('#rp canvas',[[.3,.4]]);
     await waitFor(`document.querySelector('[data-o="play"]').textContent==='❚❚'`);
     await touch('#rp canvas',[[.3,.7],[.3,.35]]); await waitFor('SPTimeline().k===6');
     assert.equal(await evaluate('SPTimeline().k'),6);
     await touch('#rp canvas',[[.3,.35],[.3,.7]]); await waitFor('SPTimeline().k===5');
     assert.equal(await evaluate('SPTimeline().k'),5);
     await click('.phone-k'); assert(await evaluate(`document.querySelector('dialog').open`));
     await click('[data-k="11"]'); await waitFor('SPTimeline().k===11'); assert.equal(await evaluate('SPTimeline().k'),11);
     assert.equal(await evaluate(`document.querySelector('dialog').open`),false);
     await touch('[data-o="scrub"]',[[.2,.5],[.8,.5]]);
     assert(await evaluate(`+document.querySelector('[data-o="scrub"]').value>600`),'finger seek');
     assert.match(await evaluate(`document.querySelector('[data-o="back"]').getAttribute('href')`),/^rect-regions.html#11-11\./);
     await click('[data-o="play"]');
     await evaluate(`{const s=document.querySelector('[data-o="scrub"]');s.value=1000;s.dispatchEvent(new Event('input'));}`);
     await waitFor('SPTimeline().k===12','autoplay next k');
     await touch('#rp canvas',[[.3,.4]]);
     assert.equal(await text('[data-o="play"]'),'▶');
     await evaluate(`{const s=document.querySelector('[data-o="scrub"]');s.value=1000;s.dispatchEvent(new Event('input'));}`);
     await new Promise(r=>setTimeout(r,1100));
     assert.equal(await evaluate('SPTimeline().k'),12,'paused player does not advance');
    } else if(page==='rect-regions') {
     await click('[data-sel="11"]'); await waitFor(`document.querySelector('[data-o=key]').textContent.startsWith('11.')`);
     const ab=await text('[data-o="ab"]');
     await touch('canvas.reg',[[.85,.65],[.25,.25]]);
     assert.notEqual(await text('[data-o="ab"]'),ab);
     assert(await evaluate(`(()=>{const p=document.querySelector('canvas.pk').getBoundingClientRect(),c=document.querySelector('.pc-h').getBoundingClientRect();return p.width>330&&p.bottom<=c.top})()`),'packing precedes card');
     assert(await evaluate(`document.querySelector('canvas.reg').getBoundingClientRect().height>=195`),'edge minimum height');
     await evaluate(`document.querySelector('.pcard').scrollIntoView({block:'end'})`);
     assert(await evaluate(`(()=>{const card=document.querySelector('.pcard'),bar=document.querySelector('.rr-ctl');return card.getBoundingClientRect().bottom-parseFloat(getComputedStyle(card).paddingBottom)<=bar.getBoundingClientRect().top})()`),'piece card last lines clear floating controls');

     await click('[data-c="last"]'); await click('[data-c="first"]');
     if(formulaK){
      await click('[data-sel="'+formulaK.k+'"]'); await waitFor(`document.querySelector('#rr-rows tr[data-key="${formulaK.pieces.find(p=>p.formula_full&&!p.formula).key}"]')`);
      const piece=formulaK.pieces.find(p=>p.formula_full&&!p.formula);
      await click('#rr-rows tr[data-key="'+piece.key+'"]');
      await click('[data-o="f"] .fft');
      assert.equal(await evaluate(`document.querySelector('[data-o="ffw"]').hidden`),false);
     }
     await click('[data-sel="all"]'); await waitFor(`performance.getEntriesByType('resource').filter(e=>/data\\/rect\\/k\\d+\\.json/.test(e.name)).length>=${data.ks.length}`); await touch('canvas.reg',[[.5,.6]]);
     assert.match(await evaluate('location.hash'),/^#cell-/);
     await touch('canvas.reg',[[.6,.4]]);
     assert(await evaluate(`!document.querySelector('[data-o="pside"]').hidden`),'cell line selects a piece');
    } else if(page==='certificate') {
     await click('.cv-items button[data-k="point"]');
     await waitFor(`document.querySelector('[data-info="items"]').textContent.includes('pts')`);
     const mass=await text('#cv [data-o="m"]');
     await touch('canvas.m',[[.35,.35],[.7,.65]]);
     assert.notEqual(await text('#cv [data-o="m"]'),mass);
     assert.equal(await evaluate(`document.querySelector('[data-states]').closest('details').open`),false);
     await click('.phone-section:has([data-states]) summary');
     assert.equal(await evaluate(`document.querySelector('[data-states]').closest('details').open`),true);
     await click('.phone-section:has(#cv-scan) summary'); await click('#cv-scan');
     await waitFor(`document.querySelector('[data-o="scan"]').textContent.includes('@')`);
    } else {
     assert(await evaluate(`document.querySelector('#ct-keep').checked`));
     await click('[data-container="hexagon"]');
     await waitFor(`document.querySelector('[data-container="hexagon"]').getAttribute('aria-pressed')==='true'`);
     const centre=await text('#ct [data-o="c"]');
     await touch('#ct canvas',[[.5,.5],[.65,.6]]);
     assert.notEqual(await text('#ct [data-o="c"]'),centre);
    }
    const hash=await evaluate('location.hash');
    await cmd('Emulation.setDeviceMetricsOverride',{width:1024,height:768,deviceScaleFactor:1,mobile:true});
    await waitFor(`document.querySelector('[data-interactive]').dataset.view==='desktop'`);
    assert.equal(await evaluate('location.hash'),hash,'desktop resize preserves URL');
    await cmd('Emulation.setDeviceMetricsOverride',{width:390,height:844,deviceScaleFactor:1,mobile:true});
    await waitFor(`document.querySelector('[data-interactive]').dataset.view==='phone'`);
    assert.equal(await evaluate('location.hash'),hash,'phone resize preserves URL');
   }
   await click('#lang');
   assert.equal(await evaluate('document.documentElement.scrollWidth<=innerWidth'),true,page+' Japanese phone overflow');
   await click('#lang');
   if(process.env.SP_SCREENSHOTS){const shot=await cmd('Page.captureScreenshot',{format:'png',captureBeyondViewport:false});await import('node:fs/promises').then(fs=>fs.writeFile(join(process.env.SP_SCREENSHOTS,page+'-'+width+'.png'),Buffer.from(shot.data,'base64')));}
   assert.equal(await evaluate('document.documentElement.scrollWidth<=innerWidth'),true,page+' phone overflow at '+width);
   assert.equal(await evaluate(`Array.from(document.querySelectorAll('[data-interactive] button,[data-interactive] select,[data-interactive] input')).every(e=>!e.getClientRects().length||e.getBoundingClientRect().height>=40)`),true,page+' short phone control');
  }
 }
 if(preview) for(const width of [1280,390]) {
  await cmd('Emulation.setDeviceMetricsOverride',{width,height:844,deviceScaleFactor:1,mobile:width===390});
  await cmd('Emulation.setTouchEmulationEnabled',{enabled:width===390});
  await navigate('explain.html');
  await waitFor(`document.querySelector('#ex-bb [data-o=seen]').textContent.length>0`);
  await waitFor(`document.querySelector('#ex-lift canvas').width>300`);
  for(const id of ['ex-net','ex-bb','ex-lift'])assert(await ink('#'+id+' canvas'));
  for(const lang of ['en','ja']) {
   if(await evaluate('document.documentElement.lang')!==lang)await click('#lang');
   const before=await text('#ex-net [data-o=r]');
   await evaluate(`{const i=document.querySelector('#ex-net input');i.value=+i.value+2;i.dispatchEvent(new Event('input'));}`);
   assert.notEqual(await text('#ex-net [data-o=r]'),before);
   await click('#ex-bb button');await waitFor(`+document.querySelector('#ex-bb [data-o=seen]').textContent.replaceAll(',','')>300`);
   await click('#ex-lift input');
   assert(await evaluate('document.documentElement.scrollWidth<=innerWidth'),'explain overflow');
  }
 }
 console.log('PASS split loading and preview explanation controls in both languages, desktop/phone.');
 assert.deepEqual(errors,[]);
 console.log('PASS: four phone views: touch gestures, disclosures, playback, URL-preserving orientation at 390×844 and coarse-pointer 768px; no console errors. All requests fulfilled offline.');
} finally {
 const exited=browser.exitCode===null?once(browser,'exit'):Promise.resolve();
 await call('Browser.close').catch(()=>{});browser.kill();await exited;
 await rm(profile,{recursive:true,force:true,maxRetries:10,retryDelay:100}).catch(e=>console.error('Profile cleanup failed: '+e.code));
}
