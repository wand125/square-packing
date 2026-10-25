import { useEffect, useState } from 'preact/hooks';
import { packingDrawing, UI_MIN_N, UI_MAX_N, UI_MIN_A, UI_MAX_A } from './minimumWidthsInteractiveMath';

type Parameters = { n: number; a: number };
let current: Parameters = { n: 11, a: 1900 };
const subscribers = new Set<(value: Parameters) => void>();
function update(patch: Partial<Parameters>) {
  current = { ...current, ...patch };
  subscribers.forEach(subscribe => subscribe(current));
}

export default function MinimumWidthsInteractive({ lang = 'en' }: { lang?: string }) {
  const ja = lang === 'ja', [value, setValue] = useState(current), [fit, setFit] = useState(true);
  useEffect(() => {
    setValue(current); subscribers.add(setValue);
    return () => { subscribers.delete(setValue); };
  }, []);
  const uid = `minimum-width-live-${lang}`;
  let drawing: ReturnType<typeof packingDrawing> | undefined;
  try { drawing = packingDrawing(value.n, value.a); } catch { /* keep the controls usable */ }
  const setN = (n: number) => { if (Number.isFinite(n)) update({ n: Math.max(UI_MIN_N, Math.min(UI_MAX_N, Math.round(n))) }); };
  const setA = (a: number) => { if (Number.isFinite(a)) update({ a: Math.max(UI_MIN_A, Math.min(UI_MAX_A, Math.round(a))) }); };
  return <figure class="vz-fig vz-highlight" data-figure="minimum-widths-interactive" data-lang={lang}
    data-n={value.n} data-height={(value.a / 1000).toFixed(3)}>
    <figcaption><strong>{ja ? '個数と高さを変えて、最小幅を達成する配置を見る' : 'Vary the number and height: see the attaining family'}</strong></figcaption>
    <div class="vz-ctl">
      <label for={`${uid}-n`}>{ja ? '正方形の個数 N' : 'Number of squares, N'}
        <input id={`${uid}-n`} type="range" min={UI_MIN_N} max={UI_MAX_N} step="1" value={value.n}
          aria-label={ja ? '正方形の個数 N' : 'Number of squares, N'}
          aria-valuetext={ja ? `${value.n}個` : `${value.n} squares`}
          onInput={e => setN(+e.currentTarget.value)} />
        <output for={`${uid}-n`}>{value.n}</output>
      </label>
      <span style={{ display: 'flex', gap: '6px' }}>
        <button type="button" style={{ minWidth: '44px' }} disabled={value.n === UI_MIN_N} aria-label={ja ? '正方形を1個減らす' : 'One fewer square'} onClick={() => setN(current.n - 1)}>−</button>
        <button type="button" style={{ minWidth: '44px' }} disabled={value.n === UI_MAX_N} aria-label={ja ? '正方形を1個増やす' : 'One more square'} onClick={() => setN(current.n + 1)}>+</button>
      </span>
    </div>
    <div class="vz-ctl"><label for={`${uid}-a`}>{ja ? '高さ a' : 'Height a'}
      <input id={`${uid}-a`} type="range" min={UI_MIN_A} max={UI_MAX_A} step="1" value={value.a}
        aria-label={ja ? '高さ a' : 'Height a'} aria-valuetext={(value.a / 1000).toFixed(3)}
        onInput={e => setA(+e.currentTarget.value)} />
      <output for={`${uid}-a`}>{(value.a / 1000).toFixed(3)}</output>
    </label></div>
    <p class="vz-note">{ja ? '操作範囲は N=11〜60、高さは0.001刻みです。定理はすべての整数 N≥11、すべての高さ 1.851≤a<2 で成立します。' : 'Controls show N=11–60 and height steps of 0.001. The theorem covers every integer N≥11 and every height 1.851≤a<2.'}</p>
    {drawing ? <>
      <output class="vz-readout" aria-live="polite" data-width={drawing.width} data-angle={drawing.angle}>
        B<sub>N</sub>(a) ≈ {drawing.width.toFixed(9)} · θ {drawing.odd ? '= 45°' : `≈ ${drawing.angle.toFixed(6)}°`}
      </output>
      <p class="vz-note" data-wall={drawing.odd ? 'same' : 'opposite'}>{drawing.odd
        ? (ja ? '奇数：両端の直立正方形は同じ壁に接する。' : 'Odd N: the upright end caps touch the same wall.')
        : (ja ? '偶数：両端は反対の壁に接する。幅と最適角の表示は数値近似。' : 'Even N: the caps touch opposite walls. Displayed width and minimising angle are numerical approximations.')}</p>
      <div style={{ overflowX: 'auto' }} tabIndex={fit ? undefined : 0} role="group" aria-label={ja ? '正方形の配置図' : 'Square packing drawing'}>
        <svg class="vz-svg" viewBox={`-.15 -.15 ${drawing.width + .3} ${drawing.a + .3}`}
          style={{ maxWidth: 'none', width: fit ? '100%' : `${Math.ceil((drawing.width + .3) * 64)}px`, cursor: 'default', touchAction: 'pan-x pan-y' }}
          role="img" aria-label={ja ? `${value.n}個、高さ${drawing.a}、両端は${drawing.odd ? '同じ' : '反対の'}壁` : `${value.n} squares at height ${drawing.a}, caps on ${drawing.odd ? 'the same wall' : 'opposite walls'}`}>
          <rect class="vz-cont" x="0" y="0" width={drawing.width} height={drawing.a} />
          {drawing.squares.map((q, i) => <polygon key={i} class={q.cap ? 'vz-sq vz-tone-1' : 'vz-sq'} data-cap={q.cap ? 'true' : 'false'}
            points={q.vertices.map(([x, y]) => `${x},${drawing!.a - y}`).join(' ')} />)}
        </svg>
      </div>
      <div class="vz-ctl"><label><input type="checkbox" checked={!fit} onChange={e => setFit(!e.currentTarget.checked)} />
        {ja ? '拡大して横スクロール' : 'Enlarge and scroll horizontally'}</label></div>
      <p class="vz-note">{ja ? '描画と小数値は数値近似です。達成する配置の族を示す図であり、証明は本文の定理と検証の議論によります。' : 'The drawing and decimal values use floating-point approximations. They illustrate the attaining family; the proof is the theorem and verification in the text.'}</p>
    </> : <p role="status">{ja ? '描画値を計算できません。個数または高さを変更してください。' : 'Could not calculate this drawing. Change the number or height.'}</p>}
  </figure>;
}
