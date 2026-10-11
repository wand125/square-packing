/** Differential checks against the read-only original algorithms. No browser or network. */
import {readFileSync} from 'node:fs';
import {resolve} from 'node:path';
import {runInNewContext} from 'node:vm';
import {parse} from 'acorn';
import {build} from 'esbuild';
import assert from 'node:assert/strict';
const json=p=>JSON.parse(readFileSync(p,'utf8'));
async function engine(name) {
 const result=await build({entryPoints:['src/engines/'+name+'.ts'],bundle:true,write:false,format:'esm',platform:'node'});
 return import('data:text/javascript;base64,'+Buffer.from(result.outputFiles[0].text).toString('base64'));
}
function original(name,functions,init='',result=functions.join(',')) {
 const code=readFileSync(resolve(process.env.SP_OLD_SOURCE||'../site-draft/site/src/viz',name+'.js'),'utf8');
 const body=parse(code,{ecmaVersion:'latest'}).body.find(n=>n.type==='ExpressionStatement').expression.callee.body.body;
 const extracted=body.filter(n=>n.type==='FunctionDeclaration'&&functions.includes(n.id.name)).map(n=>code.slice(n.start,n.end)).join('\n');
 return runInNewContext(`(()=>{${init}\n${extracted}\nreturn {${result}}})()`);
}
const plain=v=>JSON.parse(JSON.stringify(v));
const same=(a,b,label)=>assert.deepEqual(plain(a),plain(b),label);
const regions=json('public/data/rect-regions.json');
const edges=await engine('rect-edges');
const oldEdges=original('rect-regions',['along','span','familyAt','inCell','throughCell']);
let samples=0;
for(const K of regions.ks)for(const p of K.pieces){
 for(const c of [0,1]){same(edges.span(p,c),oldEdges.span(p,c),'span');for(const v of edges.span(p,c))same(edges.along(p,c,v),oldEdges.along(p,c,v),'along');}
 for(const a of [p.a0,(p.a0+p.a1)/2,p.a1]){same(edges.familyAt(p,a),oldEdges.familyAt(p,a),'aligned family '+p.key);samples++;}
 for(const q of p.pts.filter((_,i)=>i%15===0)){const b0=Math.floor(q[1]),a0=Math.floor(q[0]);same(edges.throughCell(p,b0,a0),oldEdges.throughCell(p,b0,a0),'cell');}
 const geo={X:b=>b*31,Y:a=>-a*31,px:1},q=p.pts[0];
 const nearest=edges.nearestEdge(null,K,regions,geo,geo.X(q[1]),geo.Y(q[0]));
 assert(Math.hypot(nearest.a-q[0],nearest.b-q[1])<1e-8,'snap reaches edge');
}
const timeline=await engine('player-timeline');
const oldTimeline=original('rect-player',['framesOf','build','close','match','lerp','spring','angLerp','mixFrames','at','shown'],'var K,tl=[],T=0,PER_A=7,STEP=.9,JOIN=.7,HOLD=.25,WIND=.95;', 'set(k){K=k;build();return {segments:tl,duration:T}},at');
for(const K of regions.ks){
 const a=timeline.build(K),b=oldTimeline.set(K);same(a,b,'timeline '+K.k);
 for(let i=0;i<=100;i++){const t=a.duration*i/100;same(timeline.at(a.segments,t),oldTimeline.at(t),'frame '+K.k+' @ '+i);}
}
const cert=await engine('cert-geometry');
const oldCert=original('certificate',['frac','ang','half','mass','segFrac','clipArea','clip','expand'],'var D;', 'set(d){D=d},expand,mass');
const index=json('public/data/certs/index.json');
for(const kind of ['point','rect','mixed','lift']){
 const item=index.find(c=>c.kind===kind),data=json('public/data/certs/'+item.file),a=structuredClone(data),b=structuredClone(data);
 cert.expand(a,cert.frac(a.L));oldCert.expand(b,cert.frac(b.L));same(a,b,'D4 '+kind);
 a.L=cert.frac(a.L);a.B=a.B?cert.frac(a.B):1;oldCert.set(a);
 for(const th of [0,.17,Math.PI/4])for(const f of [.2,.5,.8])same(cert.mass(a,a.L*f,a.L*(1-f),th),oldCert.mass(a.L*f,a.L*(1-f),th),'mass '+kind);
}
const ct=await engine('containers-geometry');
const oldCt=original('containers',['bbox','corners','inside','captured','fits','centroid','cons','project'],'var D,st,EPS=1e-9;', 'set(d,s){D=d;st=s},project,captured,centroid');
for(const D of json('public/data/containers.json'))for(const a of [0,Math.PI/12,Math.PI/4]){
 const st={x:0,y:0,a};oldCt.set(D,st);same(ct.centroid(D,st),oldCt.centroid(),'centroid');
 for(const [x,y]of [...D.poly,ct.centroid(D,st)]){st.x=x;st.y=y;same(ct.project(D,st,x,y),oldCt.project(x,y),'projection');same(ct.captured(D,st),oldCt.captured(),'captured / Lemma P');}
}
console.log(`PASS engines: ${samples} family samples; geometry/cells/snapping; all ${regions.ks.length} timelines and 101 frames each; D4/mass across four certificate kinds; every container's projection and captured weight.`);
