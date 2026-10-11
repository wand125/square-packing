import {useState} from 'preact/hooks';
import {betaStar,domino,points} from './paperGeometry';
export default function DominoFamily({lang='en'}:{lang?:string}) {
 const ja=lang==='ja',[beta,setBeta]=useState(betaStar),{v,squares}=domino(beta),vmin=domino(betaStar).v;
 const x=(b:number)=>42+350*b/(Math.PI/2), y=(v:number)=>130-(v-vmin)*1400;
 const curve=Array.from({length:181},(_,i)=>{const b=i*Math.PI/360;return `${x(b)},${y(domino(b).v)}`;}).join(' ');
 return <figure class="vz-fig vz-highlight" data-figure="domino-family" data-beta={beta} data-side={v}>
  <svg class="vz-svg" viewBox="-.12 -2.18 4.24 2.3" role="img" aria-label={ja?'4個の正方形の詰め方':'Four-square packing'}>
   <polygon class="vz-cont" points={points([[0,0],[2*v,0],[2*v,v],[0,v]])}/>
   {squares.map((q,i)=><g><polygon class={`vz-sq vz-tone-${i%3}`} points={points(q)}/><text class="vz-label" x={q.reduce((a,p)=>a+p[0],0)/4} y={-q.reduce((a,p)=>a+p[1],0)/4} text-anchor="middle">{['A','B','L','U'][i]}</text></g>)}
  </svg>
  <div class="vz-ctl"><label>β <input type="range" aria-label={ja?'角度 β':'Angle beta'} min="0" max="90" step="0.01" value={beta*180/Math.PI} onInput={e=>setBeta(+e.currentTarget.value*Math.PI/180)}/> {(beta*180/Math.PI).toFixed(3)}°</label><button type="button" onClick={()=>setBeta(betaStar)}>β*</button></div>
  <output class="vz-readout">s(β) = {v.toFixed(10)} · v₄ = {vmin.toFixed(10)}</output>
  <svg class="vz-plot" viewBox="0 0 440 180" role="img" aria-label={ja?'β に対する s(β)、最小点 β*':'s(beta) versus beta, minimum at beta star'}>
   <path class="vz-axis" d="M42 20 V145 H400"/>
   <polyline class="vz-curve" points={curve}/>
   <circle class="vz-min" cx={x(betaStar)} cy={y(vmin)} r="4"/><text x={x(betaStar)+8} y="126">β* ≈ {(betaStar*180/Math.PI).toFixed(3)}°</text>
   <circle class="vz-current" cx={x(beta)} cy={y(v)} r="5"/>
   <text x="4" y="24">s(β)</text><text x="4" y="40">2.00</text><text x="4" y="135">1.93</text><text x="42" y="166">0°</text><text x="210" y="166">45°</text><text x="377" y="166">90° β</text>
  </svg>
 </figure>;
}
