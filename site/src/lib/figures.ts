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
// the player's card: the most nearly square certified packing of 11 squares (where the player starts), with a play mark
export function playerFigure() {
 const k = readFigure('rect-regions.json').ks.find(k => k.k === 11)!;
 const ws = k.pieces.flatMap(p => p.witnesses).filter(w => w.squares?.length);
 const w = ws.reduce((a,b) => Math.abs(b.box[0]-b.box[1]) < Math.abs(a.box[0]-a.box[1]) ? b : a), [bx,by] = w.box, s = (W-8)/Math.max(bx,by), h = by*s+8;
 const polys = w.squares!.map(([cx,cy,th]) => { const c = Math.cos(th)/2, n = Math.sin(th)/2; return `<polygon points="${[[-1,-1],[1,-1],[1,1],[-1,1]].map(([u,v]) => `${(4+(cx+u*c-v*n)*s).toFixed(1)},${(h-4-(cy+u*n+v*c)*s).toFixed(1)}`).join(' ')}" class="th-sq"/>`; }).join('');
 const mx = 4+bx*s/2, my = h/2, r = Math.min(bx*s, by*s)/6;
 return svg(h, `<rect x="4" y="4" width="${(bx*s).toFixed(1)}" height="${(by*s).toFixed(1)}" class="th-c"/>${polys}<circle cx="${mx.toFixed(1)}" cy="${my.toFixed(1)}" r="${r.toFixed(1)}" class="gf-play-c"/><path d="M${(mx-r*0.35).toFixed(1)} ${(my-r*0.5).toFixed(1)}L${(mx+r*0.55).toFixed(1)} ${my.toFixed(1)}L${(mx-r*0.35).toFixed(1)} ${(my+r*0.5).toFixed(1)}Z" class="gf-play"/>`);
}
export function containersFigure() { return '<div class="gf-row">' + readFigure('containers.json').filter(it => it.packing?.length && (it.cont === 'triangle' && it.n === 6 || it.cont === 'hexagon' && it.n === 3 || it.cont === 'domino' && it.n === 4)).map(it => thumb(it,68)).join('') + '</div>'; }

// a small square icon for each paper: its container with the optimal packing; for Valid7, the k × k grid with 3 squares missing (the fallback)
type V3 = [number, number, number];
// unit cubes [centre, turned 45° about the vertical axis] in a cube of side S, seen obliquely (as in CubesInCube.tsx); the last cube is drawn solid
function cubesIcon(S: number, cubes: [V3, boolean][], dot = false) {
 const M = S / 2, yaw = -0.6, pitch = 0.5, cy = Math.cos(yaw), sy = Math.sin(yaw), cp = Math.cos(pitch), sp = Math.sin(pitch), H = Math.SQRT1_2;
 const view = (p: V3): V3 => { const x = p[0] - M, y = p[1] - M, z = p[2] - M, x1 = cy * x - sy * y, y1 = sy * x + cy * y; return [x1, -(z * cp + y1 * sp), y1 * cp - z * sp]; };
 const dir = (n: V3) => sy * n[0] + cy * n[1] === 0 && n[2] === 0 ? 0 : (sy * n[0] + cy * n[1]) * cp - n[2] * sp;
 const axes = (r: boolean, p: V3): V3 => r ? [H * p[0] - H * p[1], H * p[0] + H * p[1], p[2]] : p;
 const box: V3[] = []; for (const x of [0, S]) for (const y of [0, S]) for (const z of [0, S]) box.push([x, y, z]);
 const pts = box.map(view), r = Math.max(...pts.map(p => Math.max(Math.abs(p[0]), Math.abs(p[1])))), sc = 29 / r, P = (p: V3) => `${(32 + p[0] * sc).toFixed(1)},${(32 + p[1] * sc).toFixed(1)}`;
 const edges = box.flatMap((a, i) => box.slice(i + 1).filter(b => a.filter((v, k) => v !== b[k]).length === 1).map(b => [view(a), view(b)]));
 const line = ([a, b]: V3[], o: number) => `<path d="M${P(a)}L${P(b)}" stroke="currentColor" stroke-width="1" opacity="${o}"/>`;
 const faces: [number, string][] = [];
 cubes.forEach(([c, rot], i) => { const solid = i === cubes.length - 1 || cubes.length <= 2;
  for (const a of [0, 1, 2]) for (const sg of [-1, 1]) { const n: V3 = [0, 0, 0]; n[a] = sg; const nn = axes(rot, n); if (dir(nn) >= 0) continue;
   const b = (a + 1) % 3, d = (a + 2) % 3, q = [[-1, -1], [1, -1], [1, 1], [-1, 1]].map(([u, v]) => { const p: V3 = [0, 0, 0]; p[a] = sg / 2; p[b] = u / 2; p[d] = v / 2; const w = axes(rot, p); return view([c[0] + w[0], c[1] + w[1], c[2] + w[2]]); });
   faces.push([q.reduce((t, p) => t + p[2], 0) / 4, `<polygon points="${q.map(P).join(' ')}" class="th-sq" style="fill-opacity:${solid ? 0.35 + 0.4 * -dir(nn) : 0.2};stroke-opacity:${solid ? 1 : 0.6}"/>`]); } });
 faces.sort((a, b) => b[0] - a[0]);
 const c = view([M, M, M]);
 return `<svg viewBox="0 0 64 64" width="64" height="64" aria-hidden="true">${edges.filter(([a, b]) => a[2] + b[2] > 0).map(e => line(e, 0.35)).join('')}${faces.map(f => f[1]).join('')}${edges.filter(([a, b]) => a[2] + b[2] <= 0).map(e => line(e, 0.8)).join('')}${dot ? `<circle cx="${(32 + c[0] * sc).toFixed(1)}" cy="${(32 + c[1] * sc).toFixed(1)}" r="2.2" fill="currentColor"/>` : ''}</svg>`;
}
const PAPER_ICON: Record<string, [string, number]> = {'paper-hexagon-n3.html': ['hexagon', 3], 'paper-domino.html': ['domino', 4], 'paper-triangle.html': ['triangle', 6], 'paper-right-isosceles.html': ['right-isosceles', 10]};
export function paperIcon(file: string) {
 // the 4-cubes paper: the container (a 4-cube) in the page's starting view, the cell in front in colour
 if (file === 'paper-cubes-n4-upper.html') return fourCubeFigure(64, false);
 // the closed-form bound: a square container with its four walls and corners of segments
 if (file === 'paper-closed-form.html') return `<svg viewBox="0 0 64 64" width="64" height="64" aria-hidden="true"><rect x="3" y="3" width="58" height="58" class="th-c"/><rect x="13" y="13" width="38" height="38" class="th-sq"/>${[7, 9, 11].map(v => `<path d="M${v} 3V61M${64 - v} 3V61M3 ${v}H61M3 ${64 - v}H61" stroke="currentColor" stroke-width="0.6" opacity="0.55"/>`).join('')}</svg>`;
 // the plots: the closed-form bound against the known lower bounds, by block
 if (file === 'paper-closed-form-plots.html') return `<svg viewBox="0 0 64 64" width="64" height="64" aria-hidden="true"><rect x="3" y="3" width="58" height="58" class="th-c"/><path d="M10 54H56M10 54V9" stroke="currentColor" stroke-width="1" opacity="0.6"/><path d="M12 47L19 41L26 37L33 30L40 26L47 19L54 14" class="th-sq" style="fill:none;stroke-width:1.8"/><path d="M12 50L19 46L26 43L33 37L40 34L47 29L54 26" fill="none" stroke="currentColor" stroke-width="1" stroke-dasharray="2 2" opacity="0.7"/></svg>`;
 // the table: rows of N with the bound, one row marked
 if (file === 'paper-closed-form-table.html') return `<svg viewBox="0 0 64 64" width="64" height="64" aria-hidden="true"><rect x="3" y="3" width="58" height="58" class="th-c"/><rect x="3" y="3" width="58" height="10" class="th-sq"/><rect x="3" y="33" width="58" height="8" class="th-sq" style="fill-opacity:0.18;stroke:none"/>${[21, 29, 37, 45, 53].map(y => `<path d="M3 ${y}H61" stroke="currentColor" stroke-width="0.7" opacity="0.5"/>`).join('')}<path d="M22 3V61M42 3V61" stroke="currentColor" stroke-width="0.7" opacity="0.5"/></svg>`;
 // unit cubes in a cube: s₃(9) = 2 + 1/√2, eight corner cubes and one turned 45° at the centre
 if (file === 'paper-cubes-in-cube.html') { const S = 2 + Math.SQRT1_2, lo = 0.5, hi = S - 0.5, cs: [V3, boolean][] = [];
  for (const x of [lo, hi]) for (const y of [lo, hi]) for (const z of [lo, hi]) cs.push([[x, y, z], false]);
  cs.push([[S / 2, S / 2, S / 2], true]); return cubesIcon(S, cs); }
 // two unit cubes in a cube of side 2, and the centre that every unit cube inside contains
 if (file === 'paper-cubes-n-dim.html') return cubesIcon(2, [[[0.5, 0.5, 0.5], false], [[1.5, 0.5, 0.5], false]], true);
 const c = PAPER_ICON[file];
 if (c) { const it = readFigure('containers.json').find(x => x.cont === c[0] && +x.n === c[1]); if (it) return thumb(it, 64); }
 const k = 7, s = 58 / k;
 return `<svg viewBox="0 0 64 64" width="64" height="64" aria-hidden="true"><rect x="3" y="3" width="58" height="58" class="th-c"/>${Array.from({length: k * k}, (_, i) => i).filter(i => i < k * k - 3).map(i => `<rect x="${(3 + (i % k) * s).toFixed(1)}" y="${(3 + Math.floor(i / k) * s).toFixed(1)}" width="${s.toFixed(1)}" height="${s.toFixed(1)}" class="th-sq"/>`).join('')}</svg>`;
}

// the 4-cubes page: k = 17 in the starting view of cubes4-survey.astro (the octagon orientation in 4D, the 3D view turned
// so the container shows as two cubes); the 16 axis-parallel cubes faint, the rotated one in colour, the cell in front orange
export function cubes4Figure() { return fourCubeFigure(220, true); }
// the 4-cubes paper: the container alone in the same view, the cell in front in colour
function fourCubeFigure(size: number, packing: boolean) {
 const d = readFigure('cubes4-survey.json').rows.find(r => r.k === 17)!, s = d.s_float;
 const a = [0, 1, 2, 3].map(j => Math.cos(j * Math.PI / 4) / Math.SQRT2), b = [0, 1, 2, 3].map(j => Math.sin(j * Math.PI / 4) / Math.SQRT2);
 const e4 = [0, 0, 0, 1], dot = (u: number[], v: number[]) => u.reduce((t, x, j) => t + x * v[j], 0);
 let c = e4.map((x, j) => x - dot(e4, a) * a[j] - dot(e4, b) * b[j]); const nc = Math.hypot(...c); c = c.map(x => x / nc);
 const [yaw, pitch] = [-0.6152, -2.7794], cy = Math.cos(yaw), sy = Math.sin(yaw), cp = Math.cos(pitch), sp = Math.sin(pitch);
 const pr = (v: number[]) => { const X = dot(a, v), Y = dot(c, v), Z = dot(b, v), x1 = cy * X - sy * Y, y1 = sy * X + cy * Y; return [x1, -(Z * cp + y1 * sp)]; };
 const T = [...Array(16)].map((_, m) => [0, 1, 2, 3].map(j => (m >> j & 1) ? .5 : -.5)), E: [number, number][] = [];
 for (let m = 0; m < 16; m++) for (let j = 0; j < 4; j++) if (!(m >> j & 1)) E.push([m, m | 1 << j]);
 const sc = size / 2.2, P = (q: number[]) => `${(size / 2 + q[0] * sc).toFixed(1)} ${(size / 2 + q[1] * sc).toFixed(1)}`;
 const path = (V: number[][], es: [number, number][], cls: string) => `<path class="${cls}" d="${es.map(([u, w]) => `M${P(pr(V[u]))}L${P(pr(V[w]))}`).join('')}"/>`;
 const cube = (q: {c: number[]; R: number[][]}) => T.map(t => [0, 1, 2, 3].map(i => (q.c[i] + q.R[i].reduce((u, r, j) => u + r * t[j], 0)) / s - .5));
 // the cell in front: the sign and coordinate of the largest entry of the hidden direction
 const h = [0, 1, 2, 3].map(j => { const m = [a, c, b].map(r => r.filter((_, k) => k !== j)); const det = m[0][0] * (m[1][1] * m[2][2] - m[1][2] * m[2][1]) - m[0][1] * (m[1][0] * m[2][2] - m[1][2] * m[2][0]) + m[0][2] * (m[1][0] * m[2][1] - m[1][1] * m[2][0]); return ((j % 2) ? 1 : -1) * det; });
 const fj = h.map(Math.abs).indexOf(Math.max(...h.map(Math.abs))), bit = h[fj] < 0 ? 0 : 1;
 const body = path(T, E, 'gf4-box') + (packing ? d.cubes.filter(q => q.axis_parallel).map(q => path(cube(q), E, 'gf4-ax')).join('') + d.cubes.filter(q => !q.axis_parallel).map(q => path(cube(q), E, 'gf4-rot')).join('') : '') + path(T, E.filter(([u, w]) => (u >> fj & 1) === bit && (w >> fj & 1) === bit), 'gf4-cell');
 return `<svg viewBox="0 0 ${size} ${size}" width="${size}" height="${size}" aria-hidden="true">${body}</svg>`;
}
// the cubes page: the 9 unit cubes in the cube of side 2 + 1/√2, eight corner cubes and one turned 45° at the centre
export function cubesFigure() { const S = 2 + Math.SQRT1_2, lo = 0.5, hi = S - 0.5, cs: [V3, boolean][] = [];
 for (const x of [lo, hi]) for (const y of [lo, hi]) for (const z of [lo, hi]) cs.push([[x, y, z], false]);
 cs.push([[S / 2, S / 2, S / 2], true]); return cubesIcon(S, cs).replace('width="64" height="64"', 'width="150" height="150"'); }
