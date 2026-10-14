import { readIndex, readRepoText, readManifest, type Index, type Certificate } from './data';
export const CONT: Record<string, [string, string]> = {square: ['Square', '正方形'], triangle: ['Equilateral triangle', '正三角形'], 'right-isosceles': ['Right isosceles triangle', '直角二等辺三角形'], hexagon: ['Regular hexagon', '正六角形'], domino: ['1×2 rectangle', '1×2 の長方形'], n17: ['Square, n = 17 sub-patterns', '正方形 n = 17 の部分型']};
export const METH: Record<string, [string, string]> = {point: ['weighted points', '点の重み'], rect: ['rectangle density', '矩形密度'], mixed: ['mixed', '混合'], lift: ['k² − c lift (points + segments)', 'k² − c の持ち上げ（点＋線分）'], 'points-lemma': ['points + local lemma', '点＋局所補題'], 'two-stage': ['two stages + local lemma', '2 段＋局所補題'], bb: ['sub-pattern branch and bound', '部分型の分枝限定']};
export const KIND: Record<string, [string, string]> = {exact: ['optimal value', '最適値'], lb: ['lower bound', '下界'], gt: ['lower bound (strict)', '下界（真に大きい）'], sub: ['sub-pattern excluded', '部分型の除外']};
export interface Result {cont: string; n: number; v: number; kind: string; short: string; claim_en: string; claim_ja: string; meth: string; rel: string; rel_url?: string; assets: string[]; check: string; cwd: string; docs: string[]; id: string; best?: boolean}
export const fraction = (s: string) => { const [n,d] = s.trim().split('/').map(Number); return d === undefined ? n : n / d; };
const common = (c: Certificate) => ({rel: c.release_tag, assets: c.assets, check: c.check, cwd: c.check_cwd, docs: c.documents, id: c.id});
export function squareRows(idx: Index): Result[] {
 return idx.problems['square-lower-bounds'].map(c => {
  const cl = c.claim, m = cl.match(/^s\((\d+)\) (>=|=) ([0-9./]+)(?: = ([0-9./]+))?$/);
  let n: number, v: number, short: string, kind: string, ja: string;
  if (m) { n = +m[1]; v = fraction(m[4] || m[3]); short = `s(${n}) ${m[2] === '>=' ? '≥' : '='} ${m[3]}` + (m[3].includes('/') ? ` = ${Number(v.toPrecision(6))}` : ''); kind = m[2] === '=' ? 'exact' : 'lb'; ja = cl; }
  else { const m = cl.match(/^No packing of (\d+) closed unit squares fits in the closed square of side ([0-9/]+) \(= ([0-9.]+)\)\./); if (!m) throw new Error('Unrecognized square claim: ' + cl); n = +m[1]; v = +m[3]; kind = 'gt'; short = `s(${n}) > ${m[2]} = ${m[3]}`; ja = `${n} 個の閉じた単位正方形は、辺 ${m[2]}（= ${m[3]}）の閉じた正方形に入らない。`; }
  const key = c.id.slice(c.id.indexOf(':') + 1);
  const meth = key.includes('rect_n') || (c.release_tag === 'square-lower-bounds-history-v1' && key.includes('/cert_n')) ? 'rect' : key.includes('mixed_n') ? 'mixed' : /\/k2m\d/.test(key) ? 'lift' : 'point';
  return {cont: 'square', n, v, kind, short, claim_en: cl, claim_ja: ja, meth, ...common(c)};
 });
}
export function otherRows(idx: Index): Result[] {
 const rows: Result[] = [], words: Record<string, number> = {two: 2, three: 3, four: 4, six: 6};
 for (const c of idx.problems.triangle) {
  const cl = c.claim, m = cl.match(/^The smallest equilateral triangle containing (\w+) non-overlapping unit squares has side v = (.+?) ≈ ([0-9.]+)\.$/);
  let n: number, v: number, short: string, kind: string, ja: string;
  if (m) { n = words[m[1]] || +m[1]; v = +m[3]; kind = 'exact'; short = `s(${n}) = ${m[2]} ≈ ${m[3]}`; ja = `${n} 個の重ならない単位正方形が入る最小の正三角形の辺は v = ${m[2]} ≈ ${m[3]}。`; }
  else { const m = cl.match(/^No (\d+) non-overlapping unit squares fit in an equilateral triangle of side less than v = (.+?) ≈ ([0-9.]+)/); if (!m) throw new Error('Unrecognized triangle claim: ' + cl); n = +m[1]; v = +m[3]; kind = 'lb'; short = `s(${n}) ≥ ${m[2]} ≈ ${m[3]}`; ja = `${n} 個の重ならない単位正方形は、辺が v = ${m[2]} ≈ ${m[3]} 未満の正三角形には入らない。`; const rest = cl.slice(m[0].length).replace(/^[ ;,.]+|[ ;,.]+$/g, ''); if (rest) ja += '（原文：' + rest + '）'; }
  rows.push({cont: 'triangle', n, v, kind, short, claim_en: cl, claim_ja: ja, meth: [4,6].includes(n) ? 'points-lemma' : 'point', ...common(c)});
 }
 for (const c of idx.problems.hexagon) rows.push({cont: 'hexagon', n: 3, v: (1 + Math.sqrt(3)) / 2, kind: 'exact', short: 's(3) = (1 + √3)/2 ≈ 1.36603', claim_en: c.claim, claim_ja: '重ならない単位正方形 3 個が入る最小の正六角形の辺は s(3) = v = (1 + √3)/2 ≈ 1.36603。', meth: 'two-stage', ...common(c)});
 for (const c of idx.problems.domino) rows.push({cont: 'domino', n: 4, v: 1.93028330671426938847, kind: 'exact', short: 's(4) = v4 ≈ 1.930283', claim_en: c.claim, claim_ja: 's(4) = v4。v4 ≈ 1.93028330671426938847 は 5x³ + 8x² − 32x − 4 の最大の実根。', meth: 'points-lemma', ...common(c)});
 const ri = readRepoText('problems/right-isosceles/README.md');
 // a command may continue on the next line after a backslash; the trailing comment is dropped
 const cmds = Object.fromEntries([...ri.matchAll(/(python3 checker\/check\.py certificates\/n(\d+)\/(?:[^\n]*\\\n)*[^\n]*)/g)].map(m => [m[2], m[1].replace(/\s+#[^\n]*$/, '')]));
 // the n = 15 certificate also has its own Release
 const riRel: Record<number, [string, string[]]> = {15: ['right-isosceles-n15-v1', ['n15_cert.json', 'n15_packing.json', 'n15_check1_record.json', 'n15_check1_roots.jsonl', 'n15_check2_record.json', 'SHA256SUMS']]};
 for (const line of ri.split('\n')) { const m = line.match(/^\| (\d+) \| ([^|]+) \| ([0-9.]+) \| ([^|]+) \| ([^|]+) \|$/); if (!m) continue;
 const n = +m[1], val = m[2].trim(), approx = m[3], cert = m[5].trim();
 rows.push({cont: 'right-isosceles', n, v: +approx, kind: 'exact', short: `s(${n}) = ${val} ≈ ${approx}`, claim_en: `The smallest right isosceles triangle containing ${n} non-overlapping unit squares has leg s(${n}) = ${val} ≈ ${approx}. Certificate: ${cert}.`, claim_ja: `${n} 個の重ならない単位正方形が入る最小の直角二等辺三角形の脚は s(${n}) = ${val} ≈ ${approx}。証明書：${cert}。`, meth: cert.includes('Lemma P') ? 'points-lemma' : 'point', rel: riRel[n]?.[0] || '', assets: riRel[n]?.[1] || [], check: cmds[n] || '', cwd: 'problems/right-isosceles', docs: [`problems/right-isosceles/certificates/n${n}/PROOF.md`, 'problems/right-isosceles/README.md'], id: `right-isosceles:n${n}`});
 }
 for (const c of readManifest().published) rows.push({cont: 'n17', n: 17, v: 4.676, kind: 'sub', short: `${c.class}: ${c.cells.length} cells, ${c.nodes.toLocaleString('en-US')} nodes`, claim_en: c.claim, claim_ja: "認証済みの不可能：辺 1169/250 以下の正方形に重ならない単位正方形 17 個を、型の各セルに中心が 1 つずつあるように置くことはできない（jlevy/squares の 24 セルの被覆 'ring-3-voronoi-8-tabbed-unique'）。", meth: 'bb', rel: '', rel_url: c.data.release_url, assets: [], check: c.checks.join('\n'), cwd: '', docs: [c.manifest, 'problems/n17/manifest.json'], id: c.id});
 return rows;
}
export function markBest(rows: Result[]) {
 const best = new Map<string, Result>(), rank = (r: Result) => r.kind === 'exact' ? 2 : r.kind === 'gt' ? 1 : 0;
 for (const r of rows) { if (r.cont === 'n17') continue; const k = `${r.cont}:${r.n}`, old = best.get(k); if (!old || r.v > old.v || (r.v === old.v && rank(r) > rank(old))) best.set(k, r); }
 for (const r of rows) r.best = r.cont === 'n17' || best.get(`${r.cont}:${r.n}`) === r;
}
export const resultOrder = (a: Result, b: Result) => Object.keys(CONT).indexOf(a.cont) - Object.keys(CONT).indexOf(b.cont) || a.n - b.n || b.v - a.v;
export function results() { const idx = readIndex(), rows = [...squareRows(idx), ...otherRows(idx)]; markBest(rows); return rows; }
export const gridExact = (r: Result) => r.cont === 'square' && r.kind === 'lb' && Number.isInteger(r.v) && r.n <= r.v ** 2;
/** The old containers × n map, including grid equalities inferred in home.py. */
export function resultsMap(rows = results()) { const best = rows.filter(r => r.best && r.cont !== 'n17'); return {nmax: Math.max(...best.map(r => r.n)), containers: Object.keys(CONT).filter(c => best.some(r => r.cont === c)).map(cont => ({cont, cells: best.filter(r => r.cont === cont).sort((a,b) => a.n-b.n).map(r => ({...r, exact: r.kind === 'exact' || gridExact(r)}))}))}; }
