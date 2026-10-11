import {useEffect,useState} from 'preact/hooks';
import {points,type Point} from './paperGeometry';
type Packing={side:number;triangle:Point[];squares:Point[][]};
export default function Triangle37({lang='en'}:{lang?:string}) {
 const ja=lang==='ja',[data,setData]=useState<Packing|null>(null),[part,setPart]=useState('all'),[error,setError]=useState(false);
 useEffect(()=>{const controller=new AbortController();fetch(import.meta.env.BASE_URL.replace(/\/?$/,'/')+'data/papers/triangle-n37.json',{signal:controller.signal}).then(r=>{if(!r.ok)throw new Error('packing');return r.json();}).then(setData).catch(e=>{if(e.name!=='AbortError')setError(true);});return()=>controller.abort();},[]);
 return <figure class="vz-fig vz-highlight" data-figure="triangle-37" data-part={part}>
  <div class="vz-chips">{[['all',ja?'37個すべて':'All 37'],['bottom',ja?'底の9個':'Bottom 9'],['upper',ja?'上の28個':'Upper 28']].map(([id,label])=><button type="button" class={part===id?'on':''} aria-pressed={part===id} onClick={()=>setPart(id)}>{label}</button>)}</div>
  {data?<svg class="vz-svg" viewBox={`-.2 ${-data.triangle[2][1]-.2} ${data.side+.4} ${data.triangle[2][1]+.4}`} role="img" aria-label={ja?'37個の正方形の証明書配置':'Certified packing of 37 squares'}>
   <polygon class="vz-cont" points={points(data.triangle)}/>
   {data.squares.map(q=>{const bottom=Math.max(...q.map(p=>p[1]))<=1+1e-10;return <polygon data-group={bottom?'bottom':'upper'} class={`vz-sq ${bottom?'vz-tone-1':''} ${part!=='all'&&part!==(bottom?'bottom':'upper')?'vz-muted':''}`} points={points(q)}/>;})}
  </svg>:<p role="status">{error?(ja?'配置データを読み込めませんでした。':'Could not load packing data.'):'…'}</p>}
  <output class="vz-readout">9 + 28 = 37 · v = 9 + 2/√3 ≈ {data?.side.toFixed(7)??'10.1547005'}</output>
 </figure>;
}
