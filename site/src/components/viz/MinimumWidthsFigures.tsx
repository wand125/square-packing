import {useState} from 'preact/hooks';
import data from './minimumWidthsFigures.json';

/** Formula drawings; neither floating point coordinates nor plots are certificates. */
export default function MinimumWidthsFigures({lang='en',kind='parity-packing'}:{lang?:string,kind?:'parity-packing'|'height-width'}) {
 const ja=lang==='ja', [centres,setCentres]=useState(false);
 const drawing=data.drawings[kind];
 const palette:Record<string,string>={'#17212b':'var(--fg)','#2563a6':'var(--link)','#6b7280':'var(--fg2)','#b36b14':'var(--acc)','#d1d5db':'var(--line)','#dbeafe':'color-mix(in srgb, var(--link) 16%, var(--bg2))','#ffedd5':'color-mix(in srgb, var(--acc) 16%, var(--bg2))','#f8fafc':'var(--bg2)','white':'var(--bg2)'};
 const color=(value:string)=>palette[value]||value;
 return <figure class="vz-fig vz-highlight" data-figure={`minimum-widths-${kind}`}>
  <div style={{overflowX:'auto'}} role="group" aria-label={ja?'数式による説明図':'Illustration of the formulas'}>
   <svg class={kind==='height-width'?'vz-plot':'vz-svg'}
    style={{maxWidth:'100%',minWidth:kind==='parity-packing'?'640px':'0',width:'100%',cursor:'default'}}
    viewBox={`0 0 ${drawing.width} ${drawing.height}`} role="img"
    aria-label={kind==='parity-packing'?(ja?'両端に直立正方形を持つ11個と12個の交互配置':'Alternating eleven- and twelve-square constructions with upright end caps'):(ja?'高さと幅：奇数の厳密式と偶数の構成による上界':'Height and width: exact odd formula and constructed even upper bounds')}>
    {drawing.primitives.map((raw,i)=>{
     const p=raw as any;
     if(p.group==='centres'&&!centres)return null;
     const common={stroke:color(p.color),strokeWidth:p.width||1.1};
     if(p.type==='text')return <text key={i} x={p.x} y={p.y} text-anchor={p.anchor} style={{fontSize:`${p.size}px`,fill:color(p.color)}}>{ja?p.ja:p.en}</text>;
     if(p.type==='polygon')return <polygon key={i} points={p.points.map((q:number[])=>q.join(',')).join(' ')} fill={color(p.fill)} {...common}/>;
     if(p.type==='line')return <line key={i} x1={p.x1} y1={p.y1} x2={p.x2} y2={p.y2} stroke-dasharray={p.dash?'6 4':undefined} {...common}/>;
     return <circle key={i} cx={p.x} cy={p.y} r={p.r} fill={color(p.fill)} {...common}/>;
    })}
   </svg>
  </div>
  {kind==='parity-packing'&&<div class="vz-ctl"><label><input type="checkbox" checked={centres} onChange={e=>setCentres(e.currentTarget.checked)}/>{ja?'中心を表示':'Show centres'}</label><span>{ja?'小画面では図を横にスクロールできます。':'Scroll the drawing horizontally on small screens.'}</span></div>}
 </figure>;
}
