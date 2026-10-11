import {useState} from 'preact/hooks';
import {series,points,root3} from './paperGeometry';
export default function TriangleSeries({lang='en'}:{lang?:string}) {
 const ja=lang==='ja',[m,setM]=useState(4),[show,setShow]=useState(true),{v,rows,squares,lattice}=series(m),h=v*root3/2;
 return <figure class="vz-fig vz-highlight" data-figure="triangle-series" data-m={m}>
  <div class="vz-chips">{[4,5,6,7,8,9].map(i=><button type="button" class={i===m?'on':''} aria-pressed={i===m} onClick={()=>setM(i)}>m = {i}</button>)}</div>
  <svg class="vz-svg" viewBox={`-.2 ${-h-.2} ${v+.4} ${h+.4}`} role="img" aria-label={ja?'行配置と三角格子':'Square rows and triangular lattice'}>
   <polygon class="vz-cont" points={points([[0,0],[v,0],[v/2,h]])}/>
   {squares.map(q=><polygon class="vz-sq" points={points(q)}/>)}
   {show&&lattice.map(([x,y])=><circle class="vz-pt" cx={x} cy={-y} r=".065"/>)}
  </svg>
  <div class="vz-ctl"><label><input type="checkbox" checked={show} onChange={e=>setShow(e.currentTarget.checked)}/>{ja?'証明書の格子点':'Certificate lattice points'}</label></div>
  <output class="vz-readout">{ja?'行':'Rows'}: {rows.join(' + ')} = {squares.length}<br/>{ja?'重みの総和':'Total weight'}: {lattice.length} · n = {m*(m-1)/2+1} · v = {v.toFixed(6)}</output>
  {m===9&&<p class="vz-note">{ja?'m = 9 の行配置は36個。37個の配置は次の図。':'For m = 9 the rows hold 36. The 37-square packing is shown below.'}</p>}
 </figure>;
}
