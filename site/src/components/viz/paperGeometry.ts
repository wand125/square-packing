// Drawing arithmetic only; sources: hexagon/n3/PROOF.md and local_lemma/LOCAL_LEMMA.md,
// domino/certificates/n4/PROOF.md, triangle/SERIES.md (under problems/).
export type Point = [number, number];
export const root3 = Math.sqrt(3);
export const rotate = ([x,y]: Point, t: number): Point => [x*Math.cos(t)-y*Math.sin(t), x*Math.sin(t)+y*Math.cos(t)];
export const unit: Point[] = [[0,0],[1,0],[1,1],[0,1]];
export const points = (p: Point[]) => p.map(([x,y])=>`${x},${-y}`).join(' ');
export function flex(t: number) {
  const v=(1+root3)/2, V: Point=[-v/2,-v*root3/2];
  const squares=[0,1,2].map(i=>unit.map(p=>{const q=rotate(p,t);return rotate([V[0]+q[0],V[1]+q[1]],i*2*Math.PI/3);}));
  // Signed distance of T_i beyond the top edge of Q_(i+1), not intersection area.
  const gaps=squares.map((q,i)=>{
    const next=squares[(i+1)%3], a=next[3], b=next[2], corner=q[2];
    const dx=b[0]-a[0], dy=b[1]-a[1];
    return (-dy*(corner[0]-a[0])+dx*(corner[1]-a[1]))/Math.hypot(dx,dy);
  });
  return {v,V,squares,gaps};
}
let lo=0,hi=1;
for(let i=0;i<60;i++){const t=(lo+hi)/2; if(t*t*t-5*t*t-t+1>0)lo=t;else hi=t;}
export const betaStar=2*Math.atan((lo+hi)/2);
export function domino(beta: number) {
  const c=Math.cos(beta),s=Math.sin(beta),v=2*(s+c)*(1+s)/((s+c)**2+s*s);
  // Solve the A/L contact and the L/U contact through (v,v/2) together.
  // b=2c holds at betaStar only, not for the whole family.
  const b=((1+c+s)*(s+c/2)-s)/(c*(s+c/2)+s*s);
  const L: Point[]=[[b,0],[b-c,s],[b-c+s,s+c],[b+s,c]];
  const squares: Point[][]=[[[0,v-1],[1,v-1],[1,v],[0,v]],[[2*v-1,0],[2*v,0],[2*v,1],[2*v-1,1]],L,L.map(([x,y])=>[2*v-x,v-y])];
  return {v,squares};
}
export function series(m: number) {
  const v=m+2/root3, rows: number[]=[], squares: Point[][]=[], lattice: Point[]=[];
  for(let j=0;Math.floor(m-2*j/root3)>0;j++) {
    const count=Math.floor(m-2*j/root3);rows.push(count);
    for(let i=0;i<count;i++)squares.push(unit.map(([x,y])=>[(j+1)/root3+i+x,j+y]));
  }
  for(let j=0;j<m-1;j++)for(let i=0;i<m-1-j;i++)lattice.push([1+1/root3+i+j/2,1/3+1/root3+j*root3/2]);
  return {v,rows,squares,lattice};
}
// Lemma P at a single displayed pose, using the opposite-edge chord criterion.
export function pairChord(p: Point,q: Point,c: Point,theta: number) {
  const a=rotate([p[0]-c[0],p[1]-c[1]],-theta),d=rotate([q[0]-p[0],q[1]-p[1]],-theta);
  if(Math.abs(Math.hypot(...d)-1)>1e-8)return false;
  return [0,1].some(k=>{
    if(Math.abs(d[k])<1e-12)return false;
    const ts=[(-.5-a[k])/d[k],(.5-a[k])/d[k]],j=1-k;
    return ts.every(t=>Math.abs(a[j]+t*d[j])<=.5+1e-9)&&Math.min(...ts)<=1+1e-9&&Math.max(...ts)>=-1e-9;
  });
}
