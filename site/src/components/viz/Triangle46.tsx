import {useEffect,useState} from 'preact/hooks';
import {points,type Point} from './paperGeometry';
type Group='bottom'|'upright'|'left'|'right';
type Packing={side:number;triangle:Point[];squares:Point[][];groups:Group[]};
const GROUPS:[Group,string,string,number][]=[['bottom','Bottom 10','底の10個',1],['upright','Upright 9','軸に平行な9個',0],['left','Tilted 60° 15','60°の15個',2],['right','Tilted −60° 12','−60°の12個',3]];
export default function Triangle46({lang='en'}:{lang?:string}) {
 const ja=lang==='ja',[data,setData]=useState<Packing|null>(null),[part,setPart]=useState('all'),[error,setError]=useState(false);
 useEffect(()=>{const controller=new AbortController();fetch(import.meta.env.BASE_URL.replace(/\/?$/,'/')+'data/papers/triangle-n46.json',{signal:controller.signal}).then(r=>{if(!r.ok)throw new Error('packing');return r.json();}).then(setData).catch(e=>{if(e.name!=='AbortError')setError(true);});return()=>controller.abort();},[]);
 return <figure class="vz-fig vz-highlight" data-figure="triangle-46" data-part={part}>
  <div class="vz-chips">{[['all',ja?'46個すべて':'All 46'],...GROUPS.map(([id,en,jp])=>[id,ja?jp:en])].map(([id,label])=><button type="button" class={part===id?'on':''} aria-pressed={part===id} onClick={()=>setPart(id)}>{label}</button>)}</div>
  {data?<svg class="vz-svg" viewBox={`-.2 ${-data.triangle[2][1]-.2} ${data.side+.4} ${data.triangle[2][1]+.4}`} role="img" aria-label={ja?'46個の正方形の証明書配置':'Certified packing of 46 squares'}>
   <polygon class="vz-cont" points={points(data.triangle)}/>
   {data.squares.map((q,i)=>{const g=data.groups[i],tone=GROUPS.find(x=>x[0]===g)![3];return <polygon data-group={g} class={`vz-sq ${tone?'vz-tone-'+tone:''} ${part!=='all'&&part!==g?'vz-muted':''}`} points={points(q)}/>;})}
  </svg>:<p role="status">{error?(ja?'配置データを読み込めませんでした。':'Could not load packing data.'):'…'}</p>}
  <output class="vz-readout">10 + 9 + 15 + 12 = 46 · v = 10 + 2/√3 ≈ {data?.side.toFixed(7)??'11.1547005'}</output>
 </figure>;
}
