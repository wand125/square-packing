import {useEffect,useRef,useState} from 'preact/hooks';
import data from '../../../public/data/cubes4-survey.json';
// What holds the side of a packing of unit 4-cubes (public/data/cubes4-survey.json, from the certificates of
// problems/cubes-n-dim/n4-certs), in three views side by side: the section by a plane through the contacts of the
// chain (2D), the section by a 3D hyperplane containing that plane (3D, seen obliquely), and, small at the top right,
// the whole packing in parallel projection (4D). The plane is x = p0 + αe + βf, the hyperplane x = p0 + αe + γg + βf,
// with e, f, g orthonormal. Each cube is the set |a_m · (x − c)| ≤ 1/2 (a_m its axes), so its sections are a polygon
// and a polyhedron. The cubes of the chain (hold) are in colour, the others faint; the contacts (points) are orange
// dots and the walls the chain presses on are orange. Floating point, for illustration.
type Cube={c:number[];R:number[][];axis_parallel:boolean};
type Row={k:number;s_float:number;cubes:Cube[]};
type V3=[number,number,number];
const rows=(data as {rows:Row[]}).rows;
const dot=(a:number[],b:number[])=>a.reduce((t,x,i)=>t+x*b[i],0);
const det=(m:number[][])=>m[0][0]*(m[1][1]*m[2][2]-m[1][2]*m[2][1])-m[0][1]*(m[1][0]*m[2][2]-m[1][2]*m[2][0])+m[0][2]*(m[1][0]*m[2][1]-m[1][1]*m[2][0]);
// the half-spaces n·y ≤ d of the section of cube q by p0 + Σ y_i B_i
function halfspaces(q:Cube,p0:number[],B:number[][],h=.5){
 const pl:{n:number[];d:number}[]=[];
 for(let m=0;m<4;m++){const ax=q.R.map(r=>r[m]),n=B.map(b=>dot(ax,b)),k=dot(ax,p0.map((x,i)=>x-q.c[i]));pl.push({n,d:h-k},{n:n.map(x=>-x),d:h+k});}
 return pl;
}
function polygon(pl:{n:number[];d:number}[],L:number):number[][]{
 let P=[[-L,-L],[L,-L],[L,L],[-L,L]];
 for(const {n,d} of pl){const g=(p:number[])=>n[0]*p[0]+n[1]*p[1]-d,out:number[][]=[];
  P.forEach((A,i)=>{const B=P[(i+1)%P.length],ga=g(A),gb=g(B);if(ga<=1e-12)out.push(A);if((ga<0&&gb>0)||(ga>0&&gb<0)){const t=ga/(ga-gb);out.push([A[0]+t*(B[0]-A[0]),A[1]+t*(B[1]-A[1])]);}});
  P=out;if(P.length<3)return [];}
 return P;
}
function polyhedron(pl:{n:number[];d:number}[]):{f:V3[];n:number[]}[]{
 const ok=(y:number[])=>pl.every(p=>dot(p.n,y)<=p.d+1e-9),V:V3[]=[];
 for(let i=0;i<pl.length;i++)for(let j=i+1;j<pl.length;j++)for(let l=j+1;l<pl.length;l++){const M=[pl[i].n,pl[j].n,pl[l].n],D=det(M);if(Math.abs(D)<1e-9)continue;
  const b=[pl[i].d,pl[j].d,pl[l].d],y=[0,1,2].map(c=>det(M.map((r,ri)=>r.map((x,ci)=>ci===c?b[ri]:x)))/D) as V3;
  if(ok(y)&&!V.some(w=>Math.hypot(w[0]-y[0],w[1]-y[1],w[2]-y[2])<1e-7))V.push(y);}
 if(V.length<4)return [];
 const faces:{f:V3[];n:number[]}[]=[];
 for(const p of pl){const on=V.filter(y=>Math.abs(dot(p.n,y)-p.d)<1e-7);if(on.length<3)continue;
  const g=[0,1,2].map(c=>on.reduce((t,y)=>t+y[c],0)/on.length),n=p.n,t=Math.abs(n[0])<.9?[1,0,0]:[0,1,0];
  const e1=[n[1]*t[2]-n[2]*t[1],n[2]*t[0]-n[0]*t[2],n[0]*t[1]-n[1]*t[0]],e2=[n[1]*e1[2]-n[2]*e1[1],n[2]*e1[0]-n[0]*e1[2],n[0]*e1[1]-n[1]*e1[0]];
  const ang=(A:number[])=>{const d=[A[0]-g[0],A[1]-g[1],A[2]-g[2]];return Math.atan2(dot(d,e2),dot(d,e1));};
  on.sort((A,B)=>ang(A)-ang(B));faces.push({f:on,n:p.n});}
 return faces;
}
// the 4D view: the starting orientation of cubes4-survey.html (the four axes the same length, the 3D view turned)
const T=[...Array(16)].map((_,m)=>[0,1,2,3].map(j=>(m>>j&1)?.5:-.5));
const E:[number,number][]=[];for(let m=0;m<16;m++)for(let j=0;j<4;j++)if(!(m>>j&1))E.push([m,m|1<<j]);
const W0=(()=>{const a=[0,1,2,3].map(j=>Math.cos(j*Math.PI/4)/Math.SQRT2),b=[0,1,2,3].map(j=>Math.sin(j*Math.PI/4)/Math.SQRT2),e=[0,0,0,1];
 let c=e.map((x,j)=>x-dot(e,a)*a[j]-dot(e,b)*b[j]);const n=Math.hypot(...c);c=c.map(x=>x/n);return [a,c,b];})();
// the 4D view keeps turning: the three rows of the projection are turned in the plane of the hidden direction h and the
// screen's horizontal u (both in R⁴), then made orthonormal again
const det3=(M:number[][])=>det(M);
const hidden=(P:number[][])=>[0,1,2,3].map(j=>((j%2)?1:-1)*det3(P.map(r=>r.filter((_,k)=>k!==j))));
function turn4(P:number[][],d:number){const u3=[cy4,-sy4,0],u=[0,1,2,3].map(j=>u3[0]*P[0][j]+u3[1]*P[1][j]+u3[2]*P[2][j]),h=hidden(P),c=Math.cos(d)-1,sn=Math.sin(d);
 const Q=P.map(r=>{const a=dot(r,h),b=dot(r,u);return r.map((x,j)=>x+c*(a*h[j]+b*u[j])+sn*(a*u[j]-b*h[j]));}),out:number[][]=[];
 for(const r of Q){let v=r;for(const w of out){const t=dot(v,w);v=v.map((x,j)=>x-t*w[j]);}const n=Math.hypot(...v);out.push(v.map(x=>x/n));}return out;}
const Y4=-0.6152,P4=-2.7794,cy4=Math.cos(Y4),sy4=Math.sin(Y4),cp4=Math.cos(P4),sp4=Math.sin(P4);
// the 4D view's 3D part can be turned by dragging (yaw about the vertical, pitch)
const pr4=(W4:number[][],v:number[],vw:number[])=>{const cy=Math.cos(vw[0]),sy=Math.sin(vw[0]),cp=Math.cos(vw[1]),sp=Math.sin(vw[1]),X=dot(W4[0],v),Y=dot(W4[1],v),Z=dot(W4[2],v),x1=cy*X-sy*Y,y1=sy*X+cy*Y;return `${x1.toFixed(4)} ${(-(Z*cp+y1*sp)).toFixed(4)}`;};
export default function Cube4Tight({lang='en',k,p0,e,f,g,lab,hold,points=[],walls=[]}:{lang?:string;k:number;p0:number[];e:number[];f:number[];g:number[];lab:[string,string,string];hold:number[];points?:number[][];walls?:[number,number][]}){
 const ja=lang==='ja',row=rows.find(r=>r.k===k)!,s=row.s_float;
 const [W4,setW4]=useState(W0),fig=useRef<HTMLElement>(null),[vw4,setVw4]=useState([Y4,P4]),[vw3,setVw3]=useState([-0.6,0.5]);
 // drag to turn a view: [x, y, yaw, pitch] at the start of the drag
 const cur3=useRef(vw3),cur4=useRef(vw4);cur3.current=vw3;cur4.current=vw4;
 const drag=(get:{current:number[]},set:(v:number[])=>void)=>{let g:null|number[]=null;return {
  onPointerDown:(ev:PointerEvent)=>{g=[ev.clientX,ev.clientY,get.current[0],get.current[1]];try{(ev.currentTarget as Element).setPointerCapture(ev.pointerId);}catch{/* not a live pointer */}},
  onPointerMove:(ev:PointerEvent)=>{if(!g)return;set([g[2]-(ev.clientX-g[0])*.01,g[3]+(ev.clientY-g[1])*.01]);},
  onPointerUp:()=>{g=null;},onPointerCancel:()=>{g=null;}};};
 const d3=useRef(drag(cur3,setVw3)),d4=useRef(drag(cur4,setVw4));
 useEffect(()=>{let raf=0,last=0;
  const tick=(now:number)=>{const dt=Math.min(50,now-(last||now));last=now;setW4(P=>turn4(P,dt*0.0005));raf=requestAnimationFrame(tick);};
  const io=new IntersectionObserver(es=>{cancelAnimationFrame(raf);last=0;if(es[0].isIntersecting)raf=requestAnimationFrame(tick);});
  io.observe(fig.current!);return()=>{io.disconnect();cancelAnimationFrame(raf);};},[]);
 const cls=(i:number)=>hold.includes(i)?'c4h-hold':'c4h-far';
 const box:Cube={c:[s/2,s/2,s/2,s/2],R:[[1,0,0,0],[0,1,0,0],[0,0,1,0],[0,0,0,1]],axis_parallel:true};
 const coord=(y:number[],B:number[][])=>p0.map((x,i)=>x+B.reduce((t,b,j)=>t+y[j]*b[i],0));
 const onWall=(x:number[])=>walls.some(([r,side])=>Math.abs(x[r]-side*s)<1e-6);
 // 2D: α right, β up
 const B2=[e,f],L=2*s,cont2=polygon(halfspaces(box,p0,B2,s/2),L),polys=row.cubes.map(q=>polygon(halfspaces(q,p0,B2),L));
 const xs=cont2.map(p=>p[0]),ys=cont2.map(p=>p[1]),a0=Math.min(...xs),a1=Math.max(...xs),b0=Math.min(...ys),b1=Math.max(...ys);
 const Wd=100,sc=Wd/Math.max(a1-a0,b1-b0),X=(a:number)=>(a-a0)*sc,Y=(b:number)=>(b1-b)*sc,H=(b1-b0)*sc,Wx=(a1-a0)*sc;
 const proj2=(p:number[])=>{const d=p.map((x,i)=>x-p0[i]);return [dot(d,e),dot(d,f)];};
 const wall2=cont2.map((A,i)=>{const B=cont2[(i+1)%cont2.length];return onWall(coord(A,B2))&&onWall(coord(B,B2))&&walls.some(([r,side])=>Math.abs(coord(A,B2)[r]-side*s)<1e-6&&Math.abs(coord(B,B2)[r]-side*s)<1e-6)?<line class="c4h-wall" x1={X(A[0])} y1={Y(A[1])} x2={X(B[0])} y2={Y(B[1])}/>:null;});
 const pt=(p:number[][])=>p.map(([a,b])=>`${X(a).toFixed(2)},${Y(b).toFixed(2)}`).join(' ');
 // 3D: α right (e), γ depth (g), β up (f)
 const B3=[e,g,f],M=0,yaw=vw3[0],pitch=vw3[1],cy=Math.cos(yaw),sy=Math.sin(yaw),cp=Math.cos(pitch),sp=Math.sin(pitch);
 const view=(p:number[]):V3=>{const x=p[0]-M,y=p[1]-M,z=p[2]-M,x1=cy*x-sy*y,y1=sy*x+cy*y;return [x1,-(z*cp+y1*sp),y1*cp-z*sp];};
 const items:{d:number;el:any}[]=[];
 row.cubes.forEach((q,i)=>polyhedron(halfspaces(q,p0,B3)).forEach(({f:fc},j)=>{const pr=fc.map(view);
  items.push({d:pr.reduce((t,p)=>t+p[2],0)/pr.length,el:<polygon key={`${i}-${j}`} class={cls(i)} points={pr.map(p=>`${p[0].toFixed(4)},${p[1].toFixed(4)}`).join(' ')}/>});}));
 items.sort((A,B)=>B.d-A.d);
 const cont3=polyhedron(halfspaces(box,p0,B3,s/2));
 const R3=Math.max(...cont3.flatMap(({f:fc})=>fc.map(y=>Math.hypot(...y))))+.1;
 const vb=`${-R3} ${-R3} ${2*R3} ${2*R3}`;
 const proj3=(p:number[])=>{const d=p.map((x,i)=>x-p0[i]);return view([dot(d,e),dot(d,g),dot(d,f)]);};
 // 4D: the packing, the chain in colour
 const V4=row.cubes.map(q=>T.map(t=>[0,1,2,3].map(a=>(q.c[a]+q.R[a].reduce((u,r,j)=>u+r*t[j],0))/s-.5)));
 const to4=(x:number[])=>x.map(v=>v/s-.5);
 const cut3=cont3.map(({f:fc})=>{const q=fc.map(y=>to4(coord(y,B3)));return q.map((v,i)=>`${i?'L':'M'}${pr4(W4,v,vw4)}`).join('')+'Z';}).join('');
 const cut2=cont2.map(y=>to4(coord(y,B2))).map((v,i)=>`${i?'L':'M'}${pr4(W4,v,vw4)}`).join('')+'Z';
 const path4=(P:number[][])=>E.map(([u,w])=>`M${pr4(W4,P[u],vw4)}L${pr4(W4,P[w],vw4)}`).join('');
 const desc=ja?`k = ${k}。左：平面（横 ${lab[0]}、縦 ${lab[1]}）での断面。右上：配置全体の平行投影（4 次元で回り続け、ドラッグで見る向きも変えられる）に、3 次元の断面（橙の輪郭）と平面（橙）を重ねたもの。右下（ドラッグで回せる）：その平面（橙）を含み ${lab[2]} の向きにも広がる 3 次元の断面。容器の辺 s = ${s.toFixed(6)}`:`k = ${k}. Left: the section by the plane (across ${lab[0]}, up ${lab[1]}). Right, top: the whole packing in parallel projection, turning in four dimensions (drag to turn the view), with the 3D section (orange outline) and the plane (orange) in it; bottom: the 3D section containing the plane (orange; drag to turn), extending also along ${lab[2]}. Side s = ${s.toFixed(6)}`;
 return <figure ref={fig} class="vz-fig vz-highlight c4h-fig" data-figure="cube4-tight" data-k={k}>
  <div class="c4h-row">
   <svg class="c4h-2d" viewBox={`-9 -3 ${Wx+12} ${H+12}`} role="img" aria-label="2D">
    <polygon class="c4h-box" points={pt(cont2)}/>{wall2}
    {polys.map((pg,i)=>pg.length?<polygon class={cls(i)} points={pt(pg)}/>:null)}
    {points.map(p=>{const [a,b]=proj2(p);return <circle class="c4h-pt" cx={X(a)} cy={Y(b)} r="1.8"/>;})}
    {polys.map((pg,i)=>pg.length&&hold.includes(i)?<text class="c4h-num" x={X(pg.reduce((t,p)=>t+p[0],0)/pg.length)} y={Y(pg.reduce((t,p)=>t+p[1],0)/pg.length)+2} text-anchor="middle">{i}</text>:null)}
    <text class="c4h-lab" x={Wx/2} y={H+8} text-anchor="middle">{lab[0]}</text><text class="c4h-lab" x="-1" y={H/2} text-anchor="end">{lab[1].length>3?'':lab[1]}</text>
   </svg>
   <div class="c4h-side">
    <svg class="c4h-4d" {...d4.current} viewBox="-1.02 -1.02 2.04 2.04" role="img" aria-label={ja?'配置全体の平行投影':'the whole packing in parallel projection'}>
     <path class="c4h-4box" d={path4(T)}/>
     {V4.map((P,i)=><path class={hold.includes(i)?'c4h-4hold':'c4h-4far'} d={path4(P)}/>)}
     <path class="c4h-4cut3" d={cut3}/><path class="c4h-4cut2" d={cut2}/>
    </svg>
   <svg class="c4h-3d" {...d3.current} viewBox={vb} role="img" aria-label="3D">
    {cont3.filter(({f:fc})=>{const w=fc.map(y=>coord(y,B3));return walls.some(([r,side])=>w.every(x=>Math.abs(x[r]-side*s)<1e-6));}).map(({f:fc})=><polygon class="c4h-wallf" points={fc.map(view).map(p=>`${p[0].toFixed(4)},${p[1].toFixed(4)}`).join(' ')}/>)}
    {cont3.map(({f:fc})=><polygon class="c4h-edge back" points={fc.map(view).map(p=>`${p[0].toFixed(4)},${p[1].toFixed(4)}`).join(' ')}/>)}
    {items.map(x=>x.el)}
    <polygon class="c4h-cutp" points={cont2.map(([a,b])=>view([a,0,b])).map(p=>`${p[0].toFixed(4)},${p[1].toFixed(4)}`).join(' ')}/>
    {points.map(p=>{const v=proj3(p);return <circle class="c4h-pt3" cx={v[0]} cy={v[1]} r=".05"/>;})}
   </svg>
   </div>
  </div>
  <output class="vz-readout">{desc}</output>
 </figure>;
}
