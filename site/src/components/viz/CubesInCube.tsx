import {useEffect,useRef,useState} from 'preact/hooks';
// The packings of problems/cubes-in-cube/upper/configs.py (exact in Q(√2)), drawn in floating point.
// A cube is [centre, rotated]: rotated = turned 45° about the vertical axis z.
type V3=[number,number,number];
const H=Math.SQRT1_2, S=2+H, M=S/2, LO=.5, HI=S-.5;
const corners:[V3,boolean][]=[];
for(const x of [LO,HI])for(const y of [LO,HI])for(const z of [LO,HI])corners.push([[x,y,z],false]);
const CONFIGS:Record<number,[V3,boolean][]>={9:[...corners,[[M,M,M],true]],10:[...corners,[[M,M,LO],true],[[M,M,HI],true]]};
const V:V3[]=[];for(const x of [1,S-1])for(const y of [1,S-1])for(const z of [1,S-1])V.push([x,y,z]);
// faces of [-1/2, 1/2]^3 as corner sign patterns, with their outward normals
const FACES:[V3,V3[]][]=[0,1,2].flatMap(a=>[-1,1].map(sg=>{const n:V3=[0,0,0];n[a]=sg;const b=(a+1)%3,c=(a+2)%3;
  const q=[[-1,-1],[1,-1],[1,1],[-1,1]].map(([u,v])=>{const p:V3=[0,0,0];p[a]=sg/2;p[b]=u/2;p[c]=v/2;return p;});return [n,q] as [V3,V3[]];}));
const axes=(r:boolean,p:V3):V3=>r?[H*p[0]-H*p[1],H*p[0]+H*p[1],p[2]]:p;
const VIEWS:[string,string,number,number][]=[['Oblique','斜め',-.6,.5],['Top','上',0,Math.PI/2],['Side','横',0,0],['Diagonal','対角',-Math.PI/4,.6155]];
export default function CubesInCube({lang='en',n:n0=9}:{lang?:string;n?:number}) {
  const ja=lang==='ja',[n,setN]=useState(n0),[yaw,setYaw]=useState(VIEWS[0][2]),[pitch,setPitch]=useState(VIEWS[0][3]);
  const [corner,setCorner]=useState<'solid'|'faint'|'hidden'>('faint'),[pts,setPts]=useState(true),[gap,setGap]=useState(0),[spin,setSpin]=useState(false);
  const drag=useRef<null|[number,number,number,number]>(null);
  useEffect(()=>{if(!spin)return;const id=setInterval(()=>setYaw(y=>y+.012),33);return()=>clearInterval(id);},[spin]);
  const cy=Math.cos(yaw),sy=Math.sin(yaw),cp=Math.cos(pitch),sp=Math.sin(pitch);
  // world z is up; after the turn about z the viewer looks along +y1, tilted down by the pitch
  const view=(p:V3):[number,number,number]=>{const x=p[0]-M,y=p[1]-M,z=p[2]-M,x1=cy*x-sy*y,y1=sy*x+cy*y;return [x1,-(z*cp+y1*sp),y1*cp-z*sp];};
  const dir=(p:V3)=>{const x1=cy*p[0]-sy*p[1],y1=sy*p[0]+cy*p[1];return y1*cp-p[2]*sp;};
  // display only: "spread" moves each centre away from the middle of the container
  const spread=(c:V3):V3=>c.map(v=>v+gap*(v-M)) as V3;
  const items:{d:number;el:any}[]=[];
  CONFIGS[n].forEach(([c0,r],i)=>{if(!r&&corner==='hidden')return;const c=spread(c0);
    for(const [nr,q] of FACES){const w=q.map(p=>{const a=axes(r,p);return [c[0]+a[0],c[1]+a[1],c[2]+a[2]] as V3;}),pr=w.map(view),face=-dir(axes(r,nr));
      const d=pr.reduce((s,p)=>s+p[2],0)/4;
      items.push({d,el:<polygon key={`${i}-${nr}`} class={`cb-f ${r?'cb-rot':'cb-cor'}${!r&&corner==='faint'?' cb-faint':''}${face>0?' cb-front':''}`} style={{fillOpacity:(r?.18:.1)+(face>0?(r?.5:.35)*face:0)}} points={pr.map(p=>`${p[0].toFixed(4)},${p[1].toFixed(4)}`).join(' ')}/>});}
  });
  if(pts)V.forEach((p,i)=>{const q=view(p);items.push({d:q[2]-.02,el:<circle key={`v${i}`} class="cb-pt" cx={q[0]} cy={q[1]} r=".055"/>});});
  items.sort((a,b)=>b.d-a.d);
  const box:V3[]=[];for(const x of [0,S])for(const y of [0,S])for(const z of [0,S])box.push([x,y,z]);
  const edges=box.flatMap((a,i)=>box.slice(i+1).filter(b=>a.filter((v,k)=>v!==b[k]).length===1).map(b=>[view(a),view(b)]));
  const half=Math.sqrt(3)*M*(1+gap)+.1; // the container fits in any view
  const down=(e:PointerEvent)=>{setSpin(false);drag.current=[e.clientX,e.clientY,yaw,pitch];(e.currentTarget as Element).setPointerCapture(e.pointerId);};
  const move=(e:PointerEvent)=>{const g=drag.current;if(!g)return;setYaw(g[2]-(e.clientX-g[0])*.01);setPitch(Math.max(-Math.PI/2,Math.min(Math.PI/2,g[3]+(e.clientY-g[1])*.01)));};
  return <figure class="vz-fig vz-highlight cb-fig" data-figure="cubes-in-cube" data-n={n}>
    <div class="vz-chips">{[9,10].map(k=><button type="button" class={k===n?'on':''} aria-pressed={k===n} onClick={()=>setN(k)}>n = {k}</button>)}</div>
    <svg class="vz-svg cb-svg" viewBox={`${-half} ${-half} ${2*half} ${2*half}`} role="img" aria-label={ja?`辺 2 + 1/√2 の立方体に入る ${n} 個の単位立方体`:`${n} unit cubes in the cube of side 2 + 1/√2`}
      onPointerDown={down} onPointerMove={move} onPointerUp={()=>drag.current=null} onPointerCancel={()=>drag.current=null}>
      {edges.filter(([a,b])=>a[2]+b[2]>0).map(([a,b])=><line class="cb-box cb-back" x1={a[0]} y1={a[1]} x2={b[0]} y2={b[1]}/>)}
      {items.map(x=>x.el)}
      {edges.filter(([a,b])=>a[2]+b[2]<=0).map(([a,b])=><line class="cb-box" x1={a[0]} y1={a[1]} x2={b[0]} y2={b[1]}/>)}
    </svg>
    <div class="vz-ctl">
      <span>{VIEWS.map(([en,jp,y,p])=><button type="button" onClick={()=>{setSpin(false);setYaw(y);setPitch(p);}}>{ja?jp:en}</button>)}</span>
      <button type="button" aria-pressed={spin} onClick={()=>setSpin(!spin)}>{spin?(ja?'停止':'Stop'):(ja?'回す':'Rotate')}</button>
      <label>{ja?'隅の 8 個':'8 corner cubes'} <select value={corner} onChange={e=>setCorner(e.currentTarget.value as any)}><option value="solid">{ja?'表示':'shown'}</option><option value="faint">{ja?'薄く':'faint'}</option><option value="hidden">{ja?'隠す':'hidden'}</option></select></label>
      <label><input type="checkbox" checked={pts} onChange={e=>setPts(e.currentTarget.checked)}/> {ja?'8 点 V = {1, s − 1}³':'8 points V = {1, s − 1}³'}</label>
      <label>{ja?'離して見る':'Spread'} <input type="range" min="0" max="0.6" step="0.01" value={gap} onInput={e=>setGap(+e.currentTarget.value)}/></label>
    </div>
    <output class="vz-readout">s = 2 + 1/√2 ≈ {S.toFixed(5)} · {n===9?(ja?'8 隅の立方体と、中心で z 軸まわりに 45° 回した 1 個':'8 corner cubes and 1 cube at the centre, turned 45° about the z axis'):(ja?'8 隅の立方体と、中央の柱で z ∈ [0, 1] と [s − 1, s] に置いた 45° 回した 2 個':'8 corner cubes and 2 cubes turned 45° in the central column, at z ∈ [0, 1] and [s − 1, s]')}</output>
    <p class="dim vz-note">{ja?'ドラッグで回す。「離して見る」は表示だけのためで、各立方体を容器の中心から遠ざける（向きは変えない）。0 のときが upper/configs.py の配置。':'Drag to turn. "Spread" is for display only: it moves each cube away from the centre of the container, keeping its orientation. At 0 the packing is that of upper/configs.py.'}</p>
  </figure>;
}
