import {useEffect,useState} from 'preact/hooks';
// The certified savings S_i(δ) = α_i δ + β_i of the 34 intervals against Nagamochi's δ/2 and Karakuş's δ/4, and the
// bound a(N) for a chosen N. Floats are for drawing; the exact values are in intervals.json.
type Iv={i:number;d0:string;d1:string;open_left:boolean;fd0:number;fd1:number;fa:number;fb:number};
const isqrt=(n:number)=>{let k=Math.floor(Math.sqrt(n));while(k*k>n)k--;while((k+1)*(k+1)<=n)k++;return k;};
export function bound(ivs:Iv[],N:number){
 const k=isqrt(N);let a=k,at:Iv|null=null;
 if(k*k===N)return {k,a,at,F:k,K:k};
 for(const it of ivs){const d=4*it.fa*it.fa+N+4*it.fb-4*it.fa*k;if(d<0)continue;const r=2*it.fa+Math.sqrt(d);if(r>k+it.fd0+1e-12){const v=Math.min(r,k+it.fd1);if(v>a){a=v;at=it;}}}
 return {k,a,at,F:Math.min(1+Math.sqrt(N-2*k+1),k+1),K:Math.min(.5+Math.sqrt(N-k+.25),k+1)};
}
// data may be passed at build time, so the figure is drawn in the page itself (and in print) before any script runs
export default function ClosedFormBound({lang='en',data}:{lang?:string;data?:{intervals:Iv[]}}){
 const ja=lang==='ja',[ivs,setIvs]=useState<Iv[]|null>(data?.intervals??null),[error,setError]=useState(false),[N,setN]=useState(97);
 useEffect(()=>{if(data)return;const c=new AbortController();fetch(import.meta.env.BASE_URL.replace(/\/?$/,'/')+'data/papers/closed-form.json',{signal:c.signal}).then(r=>{if(!r.ok)throw new Error('data');return r.json();}).then(d=>setIvs(d.intervals)).catch(e=>{if(e.name!=='AbortError')setError(true);});return()=>c.abort();},[]);
 if(!ivs)return <figure class="vz-fig vz-highlight"><p role="status">{error?(ja?'データを読み込めませんでした。':'Could not load the data.'):'…'}</p></figure>;
 // plot: δ across [0, 1], saving up to 0.9
 const W=440,H=230,L=40,R=10,T=10,B=30,X=(d:number)=>L+d*(W-L-R),Y=(s:number)=>H-B-s/0.9*(H-T-B);
 const b=bound(ivs,N),dN=b.a-b.k;
 const ticks=[0,.2,.4,.6,.8,1];
 return <figure class="vz-fig vz-highlight" data-figure="closed-form">
  <svg class="vz-plot" viewBox={`0 0 ${W} ${H}`} role="img" aria-label={ja?'認証された節約と既知の式の比較':'Certified saving compared with the known formulas'}>
   <line class="vz-axis" x1={L} y1={H-B} x2={W-R} y2={H-B}/><line class="vz-axis" x1={L} y1={T} x2={L} y2={H-B}/>
   {ticks.map(t=><g><line class="vz-axis" x1={X(t)} y1={H-B} x2={X(t)} y2={H-B+4}/><text x={X(t)} y={H-B+16} text-anchor="middle">{t}</text></g>)}
   {[0,.25,.5,.75].map(s=><g><line class="vz-axis" x1={L-4} y1={Y(s)} x2={L} y2={Y(s)}/><text x={L-6} y={Y(s)+4} text-anchor="end">{s}</text></g>)}
   <text x={W-R} y={H-4} text-anchor="end">δ</text>
   <line x1={X(0)} y1={Y(0)} x2={X(1)} y2={Y(.5)} stroke="var(--fg2)" stroke-dasharray="5 4"/>
   <line x1={X(0)} y1={Y(0)} x2={X(1)} y2={Y(.25)} stroke="var(--line)" stroke-dasharray="2 4"/>
   <text x={X(1)-4} y={Y(.5)+14} text-anchor="end">δ/2 (Nagamochi)</text>
   <text x={X(1)-4} y={Y(.25)+14} text-anchor="end">δ/4 (Karakuş)</text>
   {ivs.map(it=><line class={b.at&&b.at.i===it.i?'vz-cur-iv':''} x1={X(it.fd0)} y1={Y(it.fa*it.fd0+it.fb)} x2={X(it.fd1)} y2={Y(it.fa*it.fd1+it.fb)} stroke={b.at&&b.at.i===it.i?'var(--acc)':'var(--link)'} stroke-width={b.at&&b.at.i===it.i?4:2}/>)}
   <line x1={X(0)} y1={Y(.75)} x2={X(1)} y2={Y(.75)} stroke="var(--line)"/>
   <text x={L+4} y={Y(.75)-4}>3/4</text>
   {b.at&&<circle class="vz-current" cx={X(dN)} cy={Y(b.at.fa*dN+b.at.fb)} r="4"/>}
  </svg>
  <div class="vz-ctl">
   <label>N <input type="number" min="49" max="1000000" step="1" value={N} onInput={e=>{const v=Math.round(+(e.target as HTMLInputElement).value);if(v>=49&&v<=1000000)setN(v);}} style="width:7em"/></label>
   <input type="range" min="49" max="400" step="1" value={Math.min(N,400)} aria-label="N" onInput={e=>setN(+(e.target as HTMLInputElement).value)}/>
  </div>
  <output class="vz-readout">
   {b.k*b.k===N?(ja?`N = ${N} は平方数：s(N) = ${b.k}（面積の下界）`:`N = ${N} is a square: s(N) = ${b.k} (area bound)`):<>
    k = {b.k}, a(N) = {b.a.toFixed(6)}{b.at?` (I${b.at.i})`:''}<br/>
    F(N) = {b.F.toFixed(6)} {ja?'（Nagamochi）、差':'(Nagamochi), difference'} {(b.a-b.F).toFixed(6)}{Math.abs(b.a-b.F)<1e-9?(ja?'（等しい）':' (equal)'):''}<br/>
    {ja?'Karakuş の値':'Karakuş'} {b.K.toFixed(6)}
   </>}
  </output>
 </figure>;
}
