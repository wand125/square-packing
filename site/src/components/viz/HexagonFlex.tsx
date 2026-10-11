import {useEffect,useState} from 'preact/hooks';
import {flex,points,rotate,type Point} from './paperGeometry';
export default function HexagonFlex({lang='en'}:{lang?:string}) {
  const ja=lang==='ja', [t,setT]=useState(0),[playing,setPlaying]=useState(false),[sym,setSym]=useState(0);
  useEffect(()=>{if(!playing)return;const id=setInterval(()=>setT(x=>x>=.52?-.03:Math.min(.52,x+.002)),40);return()=>clearInterval(id);},[playing]);
  const {v,V,squares,gaps}=flex(t);
  const transform=(p:Point)=>rotate([p[0],sym>=6?-p[1]:p[1]],(sym%6)*Math.PI/3);
  const hex=Array.from({length:6},(_,i)=>rotate([v,0],i*Math.PI/3));
  return <figure class="vz-fig vz-highlight" data-figure="hexagon-flex" data-t={t} data-gap={gaps[0]}>
    <svg class="vz-svg" viewBox="-1.55 -1.55 3.1 3.1" role="img" aria-label={ja?'風車形の揺れ':'Pinwheel flex'}>
      <polygon class="vz-cont" points={points(hex)}/>
      {squares.map((q,i)=><g><polygon class={`vz-sq vz-tone-${i}`} points={points(q.map(transform))}/><circle class="vz-pt" cx={transform(q[0])[0]} cy={-transform(q[0])[1]} r=".026"/></g>)}
      <text class="vz-label" x={transform(V)[0]-.12} y={-transform(V)[1]+.13}>V</text>
    </svg>
    <div class="vz-ctl"><label>t <input aria-label={ja?'揺れの角度 t':'Flex angle t'} type="range" min="-0.03" max="0.52" step="0.001" value={t} onInput={e=>{setPlaying(false);setT(+e.currentTarget.value);}}/> {t.toFixed(3)} rad</label>
      <button type="button" aria-pressed={playing} onClick={()=>setPlaying(!playing)}>{playing?(ja?'停止':'Pause'):(ja?'再生':'Play')}</button>
      <button type="button" onClick={()=>{setPlaying(false);setT(0);}}>{ja?'t = 0 に戻す':'Reset t = 0'}</button>
      <label>D₆ <select aria-label={ja?'対称変換':'Symmetry'} value={sym} onChange={e=>setSym(+e.currentTarget.value)}>{Array.from({length:12},(_,i)=><option value={i}>{i>=6?(ja?'鏡映 + ':'Reflect + '):''}{i%6*60}°</option>)}</select></label>
    </div>
    <output class="vz-readout">{ja?'接触ごとの符号付き距離 k':'Signed contact distance k'}: {gaps.map(g=>g.toFixed(7)).join(' / ')}<br/>{Math.abs(t)>1e-8?`k/t² = ${(gaps[0]/(t*t)).toFixed(6)}`:(ja?'t = 0：接触':'t = 0: contact')}</output>
    <p class="dim vz-note">{ja?'負の k は接触頂点が隣の辺の内側に入ることを示す（重なりの面積ではない）。これは揺れの曲線であり、動かした3個が有効な詰め方になるとは限らない。':'Negative k places the contact vertex inside the neighbouring edge line (not overlap area). This is the flex curve; the moving triple need not be a valid packing.'}</p>
  </figure>;
}
