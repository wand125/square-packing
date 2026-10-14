/** Offline Chromium smoke checks. CDP travels over pipes, all page requests are fulfilled
 * from dist or blocked; no HTTP server, network downloads, or extra npm packages. */
import {spawn} from 'node:child_process';
import {once} from 'node:events';
import {rm} from 'node:fs/promises';
import {readFileSync, mkdtempSync, rmSync, readdirSync, existsSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {resolve, extname, join} from 'node:path';
import assert from 'node:assert/strict';
// paper versions: every paper has versions, oldest first with ascending dates and numbers 1, 2, …,
// and the built page shows the latest one in its header
for (const slug of readdirSync('src/content/papers')) {
 const meta = JSON.parse(readFileSync(`src/content/papers/${slug}/meta.json`, 'utf8')), vs = meta.versions;
 assert.ok(Array.isArray(vs) && vs.length > 0, `${slug}: versions missing`);
 vs.forEach((v, i) => {
  assert.equal(v.v, String(i + 1), `${slug}: version numbers must be 1, 2, …`);
  assert.match(v.date, /^\d{4}-\d{2}-\d{2}$/, `${slug}: date`);
  // the newest version may wait for its commit until the push that publishes it
  if (!(i === vs.length - 1 && v.commit === '')) assert.match(v.commit, /^[0-9a-f]{7,40}$/, `${slug}: commit`);
  assert.ok(v.en && v.ja, `${slug}: changes in both languages`);
  if (i) assert.ok(v.date >= vs[i - 1].date, `${slug}: dates must be ascending`);
 });
 const page = `dist/paper-${slug}.html`, last = vs.at(-1);
 if (existsSync(page)) {
  const html = readFileSync(page, 'utf8');
  assert.ok(html.includes(`data-version="${last.v}"`) && html.includes(`Version ${last.v} · ${last.date}`), `${slug}: header must show version ${last.v} · ${last.date}`);
 }
}
console.log('PASS versions: every paper has ascending versions and shows the latest in its header.');
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
  const u=new URL(request.url), rel=decodeURIComponent(u.pathname.replace(/^\/square-packing\/?/,'')) || 'index.html';
  let body='',status=204,type='text/plain';
  if(u.hostname==='reading.invalid' && !rel.includes('..')) {
   try {body=readFileSync(resolve('dist',rel)).toString('base64'); status=200; type=({'.html':'text/html','.js':'text/javascript','.css':'text/css','.json':'application/json','.svg':'image/svg+xml','.woff2':'font/woff2','.mp3':'audio/mpeg'})[extname(rel)]||'application/octet-stream';} catch {status=404;errors.push('Missing local asset: '+rel);}
  }
  call('Fetch.fulfillRequest',{requestId,responseCode:status,responseHeaders:[{name:'Content-Type',value:type}],body},msg.sessionId).catch(e=>errors.push(e.message));
 }
});
async function evaluate(expression,userGesture=false) {
 const r=await cmd('Runtime.evaluate',{expression,userGesture,returnByValue:true,awaitPromise:true});
 if(r.exceptionDetails) throw new Error(JSON.stringify(r.exceptionDetails));
 return r.result.value;
}
let navSequence=0;
async function navigate(file,query='') {
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
// Drawing invariants are independent of the DOM assertions below.
const {stripTypeScriptTypes}=await import('node:module');
const geometry=await import('data:text/javascript,'+encodeURIComponent(stripTypeScriptTypes(readFileSync('src/components/viz/paperGeometry.ts','utf8'))));
const {flex,domino,betaStar,series,pairChord}=geometry;
function packingCheck(poly,squares) {
 for(const q of squares) {
  for(let i=0;i<4;i++)assert(Math.abs(Math.hypot(q[i][0]-q[(i+1)%4][0],q[i][1]-q[(i+1)%4][1])-1)<1e-8,'unit edge');
  const area=Math.abs(q.reduce((sum,p,i)=>sum+p[0]*q[(i+1)%4][1]-p[1]*q[(i+1)%4][0],0))/2;
  assert(Math.abs(area-1)<1e-8,'unit area');
  for(const p of q)for(let i=0;i<poly.length;i++){const a=poly[i],b=poly[(i+1)%poly.length];assert((b[0]-a[0])*(p[1]-a[1])-(b[1]-a[1])*(p[0]-a[0])>=-1e-8,'container');}
 }
 for(let a=0;a<squares.length;a++)for(let b=0;b<a;b++){
  const axes=[squares[a],squares[b]].flatMap(q=>q.map((p,i)=>[q[(i+1)%4][1]-p[1],p[0]-q[(i+1)%4][0]]));
  assert(axes.some(([x,y])=>{const p=squares[a].map(t=>x*t[0]+y*t[1]),q=squares[b].map(t=>x*t[0]+y*t[1]);return Math.max(...p)<=Math.min(...q)+1e-8||Math.max(...q)<=Math.min(...p)+1e-8;}),'disjoint interiors');
 }
}
async function input(selector,value){await evaluate(`(()=>{const e=document.querySelector(${JSON.stringify(selector)});e.value=${JSON.stringify(value)};e.dispatchEvent(new Event('input',{bubbles:true}));})()`,true);}
try {
 for(const t of [-.03,-.01,0,.01,.1,.52])for(const gap of flex(t).gaps)assert(Math.abs(gap-(1+flex(t).v)*(Math.cos(t)-1))<1e-12);
 assert(Math.abs(flex(.001).gaps[0]/1e-6+1.1830127)<1e-6);
 assert(Math.abs(domino(betaStar).v-1.9302833067142694)<1e-12);
 for(let i=0;i<=900;i++){const {v,squares}=domino(i*Math.PI/1800);packingCheck([[0,0],[2*v,0],[2*v,v],[0,v]],squares);assert(v>=domino(betaStar).v-1e-12);}
 for(let m=4;m<=9;m++){const {v,squares,lattice}=series(m);assert.equal(squares.length,[7,11,16,22,29,36][m-4]);assert.equal(lattice.length,m*(m-1)/2);packingCheck([[0,0],[v,0],[v/2,v*Math.sqrt(3)/2]],squares);}
 const n37=JSON.parse(readFileSync('dist/data/papers/triangle-n37.json','utf8'));
 assert.equal(n37.squares.length,37);packingCheck(n37.triangle,n37.squares);
 assert(pairChord([0,0],[1,0],[.5,0],0));assert(!pairChord([0,0],[1,0],[2,0],0));
 console.log('PASS geometry: flex distances, 901 domino poses, six series, 37-square packing, chord conditions.');
 await call('Browser.getVersion');
 const {targetId}=await call('Target.createTarget',{url:'about:blank'});
 ({sessionId:session}=await call('Target.attachToTarget',{targetId,flatten:true}));
 await cmd('Fetch.enable',{patterns:[{urlPattern:'*'}]});
 await cmd('Page.enable');await cmd('Runtime.enable');await cmd('Log.enable');
 for(const width of [1280,390]) {
  await cmd('Emulation.setDeviceMetricsOverride',{width,height:844,deviceScaleFactor:1,mobile:width===390});
  await cmd('Emulation.setTouchEmulationEnabled',{enabled:width===390});
  for(const [slug,figures] of [['hexagon-n3',['hexagon-flex']],['domino',['domino-family']],['triangle',['triangle-series','triangle-37']],['right-isosceles',['certificate']],['cubes-in-cube',['cubes-in-cube']]]) {
   await navigate('paper-'+slug+'.html');
   for(const lang of ['en','ja']) {
    // Use the site's language control rather than changing display styles.
    if(await evaluate('document.documentElement.lang')!==lang)await click('#lang');
    for(const figure of figures) {
     const sel=`.pp-main > [data-l="${lang}"] [data-figure="${figure}"]`;
     // Certificate is initially a loading div; scroll its island into view first.
     if(figure==='certificate')await evaluate(`document.querySelector('.pp-main > [data-l="${lang}"] astro-island .vz-fig').scrollIntoView({block:'center'})`);
     else await evaluate(`document.querySelector(${JSON.stringify(sel)}).scrollIntoView({block:'center'})`);
     await waitFor(`document.querySelector(${JSON.stringify(sel)})?.closest('astro-island') && !document.querySelector(${JSON.stringify(sel)}).closest('astro-island').hasAttribute('ssr')`);
     await waitFor(`document.querySelector(${JSON.stringify(sel+' svg polygon')})`);
     if(figure==='hexagon-flex'){
      await input(sel+' input',.01);await waitFor(`Math.abs(+document.querySelector(${JSON.stringify(sel)}).dataset.gap/0.0001+1.183)<0.001`);
      const before=await evaluate(`document.querySelector(${JSON.stringify(sel+' .vz-sq')}).getAttribute('points')`);
      await evaluate(`{const e=document.querySelector(${JSON.stringify(sel+' select')});e.value=7;e.dispatchEvent(new Event('change',{bubbles:true}));}`);
      await waitFor(`document.querySelector(${JSON.stringify(sel+' .vz-sq')}).getAttribute('points')!==${JSON.stringify(before)}`);
      await click(sel+' button');await waitFor(`+document.querySelector(${JSON.stringify(sel)}).dataset.t>.015`);await click(sel+' button');
     } else if(figure==='domino-family'){
      await input(sel+' input',60);await waitFor(`+document.querySelector(${JSON.stringify(sel)}).dataset.side>1.94`);
      await click(sel+' button');await waitFor(`Math.abs(+document.querySelector(${JSON.stringify(sel)}).dataset.side-1.9302833067)<1e-9`);
      assert.equal(await evaluate(`document.querySelectorAll(${JSON.stringify(sel+' .vz-sq')}).length`),4);
     } else if(figure==='triangle-series'){
      for(let m=4;m<=9;m++){
       await click(sel+` button:nth-child(${m-3})`);await waitFor(`+document.querySelector(${JSON.stringify(sel)}).dataset.m===${m}`);
       assert.equal(await evaluate(`document.querySelectorAll(${JSON.stringify(sel+' .vz-sq')}).length`),[7,11,16,22,29,36][m-4]);
       assert.equal(await evaluate(`document.querySelectorAll(${JSON.stringify(sel+' .vz-pt')}).length`),m*(m-1)/2);
      }
      await click(sel+' input');await waitFor(`document.querySelectorAll(${JSON.stringify(sel+' .vz-pt')}).length===0`);await click(sel+' input');
     } else if(figure==='triangle-37'){
      assert.equal(await evaluate(`document.querySelectorAll(${JSON.stringify(sel+' [data-group="bottom"]')}).length`),9);
      assert.equal(await evaluate(`document.querySelectorAll(${JSON.stringify(sel+' [data-group="upper"]')}).length`),28);
      await click(sel+' button:nth-child(2)');await waitFor(`document.querySelectorAll(${JSON.stringify(sel+' .vz-muted')}).length===28`);
      await click(sel+' button:nth-child(3)');await waitFor(`document.querySelectorAll(${JSON.stringify(sel+' .vz-muted')}).length===9`);
     } else if(figure==='cubes-in-cube'){
      // 6 faces per cube, the 8 points of V; n = 10 adds one cube; hiding the corners leaves the rotated cubes
      const faces=()=>evaluate(`document.querySelectorAll(${JSON.stringify(sel+' .cb-f')}).length`);
      assert.equal(await faces(),54);assert.equal(await evaluate(`document.querySelectorAll(${JSON.stringify(sel+' .cb-pt')}).length`),8);
      await click(sel+' .vz-chips button:nth-child(2)');await waitFor(`+document.querySelector(${JSON.stringify(sel)}).dataset.n===10`);
      assert.equal(await faces(),60);
      await evaluate(`{const e=document.querySelector(${JSON.stringify(sel+' select')});e.value='hidden';e.dispatchEvent(new Event('change',{bubbles:true}));}`);
      await waitFor(`document.querySelectorAll(${JSON.stringify(sel+' .cb-f')}).length===12`);
      const before=await evaluate(`document.querySelector(${JSON.stringify(sel+' .cb-rot')}).getAttribute('points')`);
      if(width!==390){await evaluate(`document.querySelector(${JSON.stringify(sel+' svg')}).scrollIntoView({block:'center'})`);await mouse(sel+' svg',[[.4,.5],[.6,.6]]);}
      else await click(sel+' .vz-ctl button:nth-child(2)');
      await waitFor(`document.querySelector(${JSON.stringify(sel+' .cb-rot')}).getAttribute('points')!==${JSON.stringify(before)}`);
     } else {
      await waitFor(`+document.querySelector(${JSON.stringify(sel)}).dataset.n===4`); // the figure opens on n = 4 (start)
      for(const [index,n,count] of [[1,2,0],[2,3,0],[3,4,1],[4,6,4],[5,10,8],[6,15,152]]){
       await click(sel+` .vz-chips button:nth-child(${index})`);await waitFor(`+document.querySelector(${JSON.stringify(sel)}).dataset.n===${n}`);
       assert.equal(await evaluate(`document.querySelectorAll(${JSON.stringify(sel+' .vz-pair')}).length`),count);
      }
      await click(sel+' .vz-chips button:nth-child(3)');await waitFor(`+document.querySelector(${JSON.stringify(sel)}).dataset.n===4`);
      await click(sel+' [data-pair-pose]');await waitFor(`+document.querySelector(${JSON.stringify(sel)}).dataset.pairCredit===1`);
      assert.equal(await evaluate(`+document.querySelector(${JSON.stringify(sel)}).dataset.captured`),2);
      assert.equal(await evaluate(`+document.querySelector(${JSON.stringify(sel)}).dataset.lemma`),1);
      const before=await evaluate(`document.querySelector(${JSON.stringify(sel+' .vz-test')}).getAttribute('points')`);
      if(width===390)await touch(sel+' svg',[[.4,.5],[.6,.7]]);else {await evaluate(`document.querySelector(${JSON.stringify(sel+' svg')}).scrollIntoView({block:'center'})`);await mouse(sel+' svg',[[.4,.5],[.6,.7]]);}
      await waitFor(`document.querySelector(${JSON.stringify(sel+' .vz-test')}).getAttribute('points')!==${JSON.stringify(before)}`);
      await input(sel+' input[type="range"]',20);await waitFor(`document.querySelector(${JSON.stringify(sel+' input[type="range"]')}).value==='20'`);
     }
     if(width===390 && ['hexagon-flex','domino-family'].includes(figure)){
      const before=await evaluate(`document.querySelector(${JSON.stringify(sel+' input')}).value`);
      await touch(sel+' input',[[.2,.5],[.7,.5]]);
      await waitFor(`document.querySelector(${JSON.stringify(sel+' input')}).value!==${JSON.stringify(before)}`);
     }
     assert(await evaluate('document.documentElement.scrollWidth<=innerWidth'),slug+' '+lang+' overflow '+width);
     if(process.env.SP_SCREENSHOTS){await evaluate(`document.querySelector(${JSON.stringify(sel)}).scrollIntoView({block:'center'})`);const shot=await cmd('Page.captureScreenshot',{format:'png',captureBeyondViewport:false});await import('node:fs/promises').then(fs=>fs.writeFile(join(process.env.SP_SCREENSHOTS,figure+'-'+lang+'-'+width+'.png'),Buffer.from(shot.data,'base64')));}
    }
   }
  }
 }
 assert.deepEqual(errors,[]);
 console.log('PASS papers: all five highlights, English/Japanese, mouse/touch controls, 390px overflow, no console errors; offline requests only.');
} finally {
 const exited=browser.exitCode===null?once(browser,'exit'):Promise.resolve();
 await call('Browser.close').catch(()=>{});browser.kill();if(browser.exitCode===null&&!browser.signalCode)await exited;
 await rm(profile,{recursive:true,force:true,maxRetries:10,retryDelay:100});
}
