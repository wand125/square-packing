import {readFigure, type Container} from './data';
import {fraction} from './results';
export function thumb(it: Container, w = 112) {
 const xs = it.poly.map(p => p[0]), ys = it.poly.map(p => p[1]), x0 = Math.min(...xs), y0 = Math.min(...ys), x1 = Math.max(...xs), y1 = Math.max(...ys);
 const sc = (w - 6) / Math.max(x1-x0, y1-y0), h = (y1-y0)*sc+6;
 const point = (p: number[]) => `${(3+(p[0]-x0)*sc).toFixed(2)},${(h-3-(p[1]-y0)*sc).toFixed(2)}`;
 return `<svg viewBox="0 0 ${w} ${h.toFixed(1)}" width="${w}" height="${h.toFixed(0)}" aria-hidden="true"><polygon points="${it.poly.map(point).join(' ')}" class="th-c"/>${(it.packing || []).map(q => `<polygon points="${q.map(point).join(' ')}" class="th-sq"/>`).join('')}</svg>`;
}
const W = 220, svg = (h: number, body: string) => `<svg viewBox="0 0 ${W} ${h.toFixed(0)}" width="${W}" height="${h.toFixed(0)}" aria-hidden="true">${body}</svg>`;
export function certificateFigure() { const d = readFigure('cert-point-n29.json'), L = fraction(d.L), s = (W-8)/L, max = Math.max(...d.atoms.map(a => a[2])); return svg(W, `<rect x="4" y="4" width="${(L*s).toFixed(1)}" height="${(L*s).toFixed(1)}" class="gf-box"/><g class="gf-dot">${d.atoms.map(([x,y,w]) => `<circle cx="${(4+x*s).toFixed(1)}" cy="${(4+(L-y)*s).toFixed(1)}" r="${(0.6+3.2*Math.sqrt(w/max)).toFixed(2)}"/>`).join('')}</g>`); }
export function rectanglesFigure() {
 const k = readFigure('rect-regions.json').ks.find(k => k.k === 11)!;
 const ws = k.pieces.flatMap(p => p.witnesses).filter(w => w.squares?.length);
 const tilted = (w: typeof ws[number]) => w.squares!.filter(q => Math.abs(Math.sin(2*q[2])) > 1e-6).length;
 const w = ws.reduce((a,b) => tilted(b) > tilted(a) ? b : a), [bx,by] = w.box, s = (W-8)/bx, h = by*s+8;
 const polys = w.squares!.map(([cx,cy,th]) => { const c = Math.cos(th)/2, n = Math.sin(th)/2; return `<polygon points="${[[-1,-1],[1,-1],[1,1],[-1,1]].map(([u,v]) => `${(4+(cx+u*c-v*n)*s).toFixed(1)},${(h-4-(cy+u*n+v*c)*s).toFixed(1)}`).join(' ')}" class="th-sq"/>`; }).join('');
 return svg(h, `<rect x="4" y="4" width="${(bx*s).toFixed(1)}" height="${(by*s).toFixed(1)}" class="th-c"/>${polys}`);
}
export function containersFigure() { return '<div class="gf-row">' + readFigure('containers.json').filter(it => it.packing?.length && (it.cont === 'triangle' && it.n === 6 || it.cont === 'hexagon' && it.n === 3 || it.cont === 'domino' && it.n === 4)).map(it => thumb(it,68)).join('') + '</div>'; }
