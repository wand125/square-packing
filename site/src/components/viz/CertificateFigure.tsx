// An interactive figure for the paper pages (one container; several n are offered as chips): the container, the packing and the certificate's points (area by weight),
// with a unit square to drag and turn. It shows the weight the closed square captures; at least 1 turns it green.
// Data: data/containers.json (the site's extract of the published certificates).
import { useEffect, useRef, useState } from 'preact/hooks';
import {pairChord, type Point} from './paperGeometry';

type Item = { cont: string; n: string; poly: number[][]; points: number[][]; pairs?: [number, number][]; packing: number[][][] | false };

// ns: the n shown as choices, in this order; start: the n shown first (default the first of ns)
export default function CertificateFigure({ cont = "hexagon", ns = "3", start = "", lang = "en" }: { cont?: string; ns?: string; start?: string; lang?: string }) {
  const ja = lang === 'ja';
  const [showPairs, setShowPairs] = useState(true);
  const [error, setError] = useState(false);
  const list = ns.split(',').map((x) => x.trim());
  const [n, setN] = useState(list.includes(start) ? start : list[0]);
  const [it, setIt] = useState<Item | null>(null);
  const [c, setC] = useState<[number, number] | null>(null);
  const [deg, setDeg] = useState(0);
  const svg = useRef<SVGSVGElement>(null);
  useEffect(() => {
    let active = true;
    setError(false);
    fetch(import.meta.env.BASE_URL.replace(/\/?$/, '/') + 'data/containers.json').then((r) => { if (!r.ok) throw new Error("certificate"); return r.json(); }).then((all: Item[]) => {
      if (!active) return;
      const x = all.find((y) => y.cont === cont && String(y.n) === String(n)) || null;
      setIt(x);
      if (x) { const xs = x.poly.map((p) => p[0]), ys = x.poly.map((p) => p[1]); setC([(Math.min(...xs) + Math.max(...xs)) / 2, (Math.min(...ys) + Math.max(...ys)) / 2]); }
    }).catch(() => { if (active) setError(true); });
    return () => { active = false; };
  }, [cont, n]);
  if (error) return <p role="status">{ja ? "証明書データを読み込めませんでした。" : "Could not load certificate data."}</p>;
  if (!it || !c) return <div class="vz-fig dim">…</div>;
  const xs = it.poly.map((p) => p[0]), ys = it.poly.map((p) => p[1]);
  const x0 = Math.min(...xs) - 0.1, x1 = Math.max(...xs) + 0.1, y0 = Math.min(...ys) - 0.1, y1 = Math.max(...ys) + 0.1;
  const P = (p: number[]) => `${p[0]},${y1 + y0 - p[1]}`;   // y up
  const wmax = Math.max(...it.points.map((p) => p[2]));
  const th = (deg * Math.PI) / 180, cs = Math.cos(th), sn = Math.sin(th);
  const corner = (u: number, v: number) => [c[0] + u * cs - v * sn, c[1] + u * sn + v * cs];
  const sq = [[-0.5, -0.5], [0.5, -0.5], [0.5, 0.5], [-0.5, 0.5]].map(([u, v]) => corner(u, v));
  // captured weight: points in the closed square (a 1e-9 tolerance on its edges)
  const inside = it.points.map(([px, py]) => {
    const dx=px-c[0],dy=py-c[1];
    return Math.abs(dx*cs+dy*sn)<=.5+1e-9 && Math.abs(-dx*sn+dy*cs)<=.5+1e-9;
  });
  const cap = it.points.reduce((sum,p,i)=>sum+(inside[i]?p[2]:0),0);
  const used = new Set<number>();
  let pairCredit=0;
  const credited = new Set<number>();
  // Show a conservative Lemma P count separately from actual point mass.
  // Pair-first, in certificate order, with disjoint endpoints; then unused captured points.
  (it.pairs||[]).forEach(([a,b],i)=>{
    if(!used.has(a)&&!used.has(b)&&pairChord(it.points[a] as Point,it.points[b] as Point,c,th)) {
      used.add(a);used.add(b);credited.add(i);
      pairCredit+=Math.min(it.points[a][2],it.points[b][2]);
    }
  });
  const lemmaCap=pairCredit+it.points.reduce((sum,p,i)=>sum+(inside[i]&&!used.has(i)?p[2]:0),0);
  const move = (ev: PointerEvent) => {
    const matrix=svg.current?.getScreenCTM();
    if(!matrix)return;
    const p=new DOMPoint(ev.clientX,ev.clientY).matrixTransform(matrix.inverse());
    setC([p.x,y1+y0-p.y]);
  };
  return (
    <figure class="vz-fig" data-figure="certificate" data-cont={cont} data-n={it.n} data-captured={cap} data-lemma={lemmaCap} data-pair-credit={pairCredit}>
      {list.length > 1 && <div class="vz-chips">{list.map((x) => <button type="button" class={x === n ? 'on' : ''} aria-pressed={x === n} onClick={() => setN(x)}>n = {x}</button>)}</div>}
      <svg ref={svg} viewBox={`${x0} ${y0} ${x1 - x0} ${y1 - y0}`} class="vz-svg" role="img" aria-label={ja ? "証明書：正方形をドラッグ" : "Certificate: drag the unit square"}
        onPointerDown={(e) => { (e.currentTarget as Element).setPointerCapture(e.pointerId); move(e); }}
        onPointerMove={(e) => { if (e.buttons) move(e); }}>
        <polygon class="vz-cont" points={it.poly.map(P).join(' ')} />
        {it.packing && it.packing.map((q) => <polygon class="vz-sq" points={q.map(P).join(' ')} />)}
        {showPairs && (it.pairs||[]).map(([a,b],i)=><line class={credited.has(i)?'vz-pair active':'vz-pair'} x1={it.points[a][0]} y1={y1+y0-it.points[a][1]} x2={it.points[b][0]} y2={y1+y0-it.points[b][1]}/>)}
        {it.points.map(([x, y, w]) => <circle class="vz-pt" cx={x} cy={y1 + y0 - y} r={0.006 + 0.03 * Math.sqrt(w / wmax)} />)}
        <polygon class={cap >= 1 - 1e-9 ? 'vz-test ok' : 'vz-test'} points={sq.map(P).join(' ')} />
      </svg>
      <div class="vz-ctl">
        <label><span class="dim">{ja ? "角度" : "Angle"}</span> <input aria-label={ja ? "正方形の角度" : "Square angle"} type="range" min="0" max="90" step="0.5" value={deg} onInput={(e) => setDeg(+(e.currentTarget as HTMLInputElement).value)} /> <span class="num">{deg.toFixed(1)}°</span></label>
        <output class="num">{ja ? "捕捉した点の重み" : "Captured point weight"} {cap.toFixed(6)}</output>
        {!!it.pairs?.length && <><button type="button" data-pair-pose onClick={()=>{const [a,b]=it.pairs![0],p=it.points[a],q=it.points[b];setC([(p[0]+q[0])/2,(p[1]+q[1])/2]);setDeg(((Math.atan2(q[1]-p[1],q[0]-p[0])*180/Math.PI)%90+90)%90);}}>{ja ? "対が両辺に触れる位置" : "Pair on opposite edges"}</button><label><input type="checkbox" checked={showPairs} onChange={e=>setShowPairs(e.currentTarget.checked)}/>{ja ? "距離1の対" : "Distance-1 pairs"}</label><output class="vz-readout">{ja ? "補題Pの計数" : "Lemma P count"}: {lemmaCap.toFixed(6)} ({ja ? "対の寄与" : "pair credit"}: {pairCredit.toFixed(6)})</output></>}
      </div>
      {!!it.pairs?.length && <p class="dim vz-note">{ja ? "破線は証明書の対。緑は弦の条件を満たし、今回計数した対。対には小さい方の重みを与え、その両端を残りの点の計数から外す。正方形をドラッグして比較できる。" : "Dashed lines are certificate pairs. Green pairs satisfy the chord condition and contribute the smaller endpoint weight; both endpoints are then excluded from the remaining point count. Drag the square to compare."}</p>}
    </figure>
  );
}
