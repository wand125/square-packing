import {useMemo,useState} from 'preact/hooks';
// F_k(R) = Σ_i |R_ik| (2 − w_i), w_i the ℓ¹ norm of row i (problems/cubes-n-dim/PROOF.md), for R ∈ SO(4) built from
// six plane rotations; c = max_e |R_e1|. Floating point, for illustration only.
type M=number[][];
const I4=():M=>[0,1,2,3].map(i=>[0,1,2,3].map(j=>i===j?1:0));
const PLANES:[number,number][]=[[0,1],[0,2],[0,3],[1,2],[1,3],[2,3]];
function rot(angles:number[]):M{
 let R=I4();
 PLANES.forEach(([i,j],k)=>{const t=angles[k]*Math.PI/180,c=Math.cos(t),s=Math.sin(t);
  R=R.map(row=>{const r=[...row],a=row[i],b=row[j];r[i]=c*a-s*b;r[j]=s*a+c*b;return r;});});
 return R;
}
const F=(R:M,k:number)=>R.reduce((sum,row)=>sum+Math.abs(row[k])*(2-row.reduce((w,x)=>w+Math.abs(x),0)),0);
const C2=(R:M)=>Math.max(...R.map(row=>row[0]*row[0]));
// a fixed cloud of random rotations (Gram–Schmidt of a seeded Gaussian matrix)
function cloud(n:number):[number,number][]{
 let s=12345;const u=()=>{s=(s+0x6d2b79f5)|0;let t=Math.imul(s^(s>>>15),1|s);t=(t+Math.imul(t^(t>>>7),61|t))^t;return ((t^(t>>>14))>>>0)/4294967296;};
 const g=()=>Math.sqrt(-2*Math.log(u()||1e-12))*Math.cos(2*Math.PI*u());
 const out:[number,number][]=[];
 for(let m=0;m<n;m++){const Q:number[][]=[];
  for(let k=0;k<4;k++){let v=[g(),g(),g(),g()];for(const q of Q){const d=v.reduce((a,x,i)=>a+x*q[i],0);v=v.map((x,i)=>x-d*q[i]);}
   const l=Math.hypot(...v);Q.push(v.map(x=>x/l));}
  const R=[0,1,2,3].map(i=>Q.map(q=>q[i]));out.push([C2(R),F(R,0)]);}
 return out;
}
const B=Math.acos(Math.sqrt(2/3))*180/Math.PI;   // the rotation in the plane (1, 2) that puts c² on 2/3
const PRESETS:[string,string,number[]][]=[['On an axis (R = I)','軸の上（R = I）',[0,0,0,0,0,0]],['c² = 2/3','c² = 2/3',[B,0,0,0,0,0]],['A far rotation','遠い領域の回転',[30,25,20,40,-30,15]]];
// plot window: c² in [1/4, 1] (c ≥ 1/2 for a unit vector in R⁴), F₁ in [0.2, 1.05]
const X0=.25,X1=1,Y0=.2,Y1=1.05,PX=(x:number)=>10+(x-X0)/(X1-X0)*180,PY=(y:number)=>116-(y-Y0)/(Y1-Y0)*100;
export default function Cube4Centre({lang='en'}:{lang?:string}){
 const ja=lang==='ja',[ang,setAng]=useState<number[]>(PRESETS[1][2]);
 const dots=useMemo(()=>cloud(1200),[]);
 const R=rot(ang),c2=C2(R),f=[0,1,2,3].map(k=>F(R,k)),near=c2>=2/3-1e-12;
 const label=(en:string,jp:string)=>ja?jp:en;
 const xb=PX(2/3);
 return <figure class="vz-fig vz-highlight c4-fig" data-figure="cube4-centre" data-c2={c2.toFixed(6)} data-f1={f[0].toFixed(6)} data-region={near?'near':'far'}>
  <div class="vz-chips">{PRESETS.map(([en,jp,a])=><button type="button" class={a.every((x,i)=>x===ang[i])?'on':''} aria-pressed={a.every((x,i)=>x===ang[i])} onClick={()=>setAng(a)}>{label(en,jp)}</button>)}</div>
  <svg class="vz-svg c4-svg" viewBox="0 0 200 138" role="img" aria-label={label('F₁ against c² for rotations of R⁴','R⁴ の回転についての c² と F₁')}>
   <polygon class="c4-far" points={`${PX(X0)},${PY(Y1)} ${xb},${PY(Y1)} ${xb},${PY(Y0)} ${PX(X0)},${PY(Y0)}`}/>
   <polygon class="c4-near" points={`${xb},${PY(Y1)} ${PX(X1)},${PY(Y1)} ${PX(X1)},${PY(Y0)} ${xb},${PY(Y0)}`}/>
   <line class="c4-one" x1={PX(X0)} x2={PX(X1)} y1={PY(1)} y2={PY(1)}/>
   {dots.map(([x,y])=><circle class="c4-dot" cx={PX(x)} cy={PY(Math.max(Y0,y))} r=".7"/>)}
   <circle class="c4-now" cx={PX(c2)} cy={PY(Math.max(Y0,f[0]))} r="2.4"/>
   <text class="c4-t" x={PX(X0)+2} y="12">{label('far: computer (§4)','遠い領域：計算機（§4）')}</text>
   <text class="c4-t" x={xb+2} y="12">{label('near: by hand (§3)','近い領域：手（§3）')}</text>
   <text class="c4-t" x={PX(X1)-1} y={PY(1)-1.5} text-anchor="end">F₁ = 1</text>
   {[.25,.5,2/3,.75,1].map(x=><text class="c4-t" x={PX(x)} y="128" text-anchor="middle">{x===2/3?'2/3':String(x)}</text>)}
   <text class="c4-t" x="100" y="136" text-anchor="middle">c² = max_e R_e1²</text>
   {[.2,.4,.6,.8,1].map(y=><text class="c4-t" x="8.5" y={PY(y)+1.5} text-anchor="end">{y.toFixed(1)}</text>)}
  </svg>
  <div class="vz-ctl c4-ctl">{PLANES.map(([i,j],k)=><label>{label('plane','平面')} ({i+1}, {j+1}) <input type="range" min="-90" max="90" step="0.5" value={ang[k]} onInput={e=>{const a=[...ang];a[k]=+e.currentTarget.value;setAng(a);}}/> <span class="num">{ang[k].toFixed(1)}°</span></label>)}</div>
  <output class="vz-readout">c² = {c2.toFixed(4)} · F₁ = {f[0].toFixed(4)} · F₂, F₃, F₄ = {f.slice(1).map(x=>x.toFixed(4)).join(', ')} · {near?label('near region c² ≥ 2/3: proved by hand (§3)','近い領域 c² ≥ 2/3：手で証明（§3）'):label('far region c² < 2/3: checked by computer (§4)','遠い領域 c² < 2/3：計算機で検査（§4）')}</output>
  <p class="dim vz-note">{label('R is the product of rotations in the six coordinate planes, by the angles of the sliders. The grey dots are 1,200 random rotations. Computed in the browser in floating point; an illustration, not part of the proof.','R は 6 つの座標平面での回転（角はつまみの値）の積。灰色の点は 1,200 個のランダムな回転。ブラウザで浮動小数点で計算した図で、証明の一部ではない。')}</p>
 </figure>;
}
