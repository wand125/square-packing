import {tex} from '../../lib/tex';
// The 34 intervals in full, rendered at build time from the data extracted from intervals.json
// (tools/extract/extract_closed_form.py): the interval, α and β, the formula on the interval, and the margin over δ/2.
type Iv={i:number;d0:string;d1:string;open_left:boolean;alpha:string;beta:string;c:string;two_alpha:string;four_alpha:string;fa:number;fb:number;fc:number;margin0:number;margin1:number};
const frac=(s:string)=>{const [p,q]=s.split('/');return q?`${p.startsWith('-')?'-':''}\\tfrac{${p.replace('-','')}}{${q}}`:s;};
const m=(s:string)=>tex(`\\(${s}\\)`);
const dec=(x:number,n=6)=>(x<0?'−':'')+Math.abs(x).toFixed(n);
export default function ClosedFormTable({data,lang='en'}:{data:{intervals:Iv[]};lang?:string}){
 const ja=lang==='ja';
 return <div class="wrap cf-table"><table>
  <thead><tr><th>i</th><th>{ja?'区間':'interval'} I<sub>i</sub></th><th>α<sub>i</sub></th><th>β<sub>i</sub> ≈</th><th>{ja?'この区間での a(N)（':'a(N) on this interval ('}c<sub>i</sub> = 4α<sub>i</sub>² + 4β<sub>i</sub>{ja?'）':')'}</th><th>{ja?'余裕':'margin'} S<sub>i</sub> − δ/2 {ja?'（両端）':'(ends)'}</th></tr></thead>
  <tbody>{data.intervals.map(it=><tr>
   <td class="num">{it.i}</td>
   <td class="num nw" dangerouslySetInnerHTML={{__html:m(`${it.open_left?'(':'['}${frac(it.d0)},\\ ${frac(it.d1)}]`)}}/>
   <td class="num" dangerouslySetInnerHTML={{__html:m(frac(it.alpha))+`<br><span class="dim">≈ ${it.fa.toFixed(6)}</span>`}}/>
   <td class="num">{dec(it.fb)}<details><summary>{ja?'厳密な値':'exact'}</summary><code class="cf-exact">{it.beta}</code></details></td>
   <td class="num"><span dangerouslySetInnerHTML={{__html:m(`${frac(it.two_alpha)} + \\sqrt{N + c_{${it.i}} - ${frac(it.four_alpha)}\\,k}`)}}/><br/><span class="dim">c<sub>{it.i}</sub> ≈ {it.fc.toFixed(6)}</span><details><summary>{ja?'c の厳密な値':'exact c'}</summary><code class="cf-exact">{it.c}</code></details></td>
   <td class="num nw">{dec(it.margin0,4)}{it.open_left?(ja?'（極限）':' (limit)'):''}<br/>{dec(it.margin1,4)}</td>
  </tr>)}</tbody>
 </table></div>;
}
