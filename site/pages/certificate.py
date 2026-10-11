"""Certificate page: one published square-container certificate drawn on [0, L]^2, with the mass a core square captures."""
import json, os

from lib import BLOB, HERE, bi, e

SRC_LB = 'problems/square-lower-bounds/docs/lower-bounds.md'
SRC_SPEC = 'problems/square-lower-bounds/certificates/mixed_n41_L6775/check2/src/SPEC.md'


def build():
    # the sidebar lists every certificate in data/certs/index.json (tools/extract_all_certs.py), by n
    idx = json.load(open(os.path.join(HERE, 'data', 'certs', 'index.json')))
    KIND = {'point': ('points', '点'), 'lift': ('points + segments', '点＋線分'), 'rect': ('rectangles', '長方形'), 'mixed': ('mixed', '混合')}
    # one small icon per kind (14 x 14, currentColor): dots / dots on a line / one rectangle / rectangles with a dot
    ICON = {
        'point': '<circle cx="3.5" cy="4" r="1.6"/><circle cx="10" cy="3.5" r="1.6"/><circle cx="6.5" cy="10" r="1.6"/><circle cx="11.5" cy="10.5" r="1.2"/>',
        'lift': '<path d="M1 7H13" stroke="currentColor" stroke-width="1.4" fill="none"/><circle cx="3.5" cy="3" r="1.4"/><circle cx="10.5" cy="11" r="1.4"/>',
        'rect': '<rect x="2" y="3" width="10" height="8" rx="0.5" fill="currentColor" opacity="0.55"/>',
        'mixed': '<rect x="1.5" y="2" width="6.5" height="5" fill="currentColor" opacity="0.55"/><rect x="5" y="7" width="7.5" height="5" fill="currentColor" opacity="0.8"/>',
    }
    icon = lambda k: (f'<svg class="ki" viewBox="0 0 14 14" width="14" height="14" fill="currentColor" role="img" aria-label="{KIND[k][0]}">'
                      f'<title>{KIND[k][0]}</title>{ICON[k]}</svg>')
    best = [c for c in idx if c.get('best', True)]
    # every certificate of each n, best (largest side) first, for the selector beside the drawing
    versions = {}
    for c in sorted(idx, key=lambda c: (c['n'], -c['v'], c['file'])):
        versions.setdefault(c['n'], []).append([f'certs/{c["file"][:-5]}', f'{c["v"]:.6f}'.rstrip('0').rstrip('.'), c['kind'], bool(c.get('best', True))])
    side = ''.join(f'<button type="button" data-cert="certs/{c["file"][:-5]}" aria-pressed="false" data-k="{c["kind"]}" data-n="{c["n"]}">'
                   f'<span class="num cv-n">{c["n"]}</span><span class="num">{c["v"]:.6f}'.rstrip('0').rstrip('.') + f'</span>'
                   f'<span class="dim">{icon(c["kind"])}</span></button>' for c in best)
    info = ''.join(f'<dt>{bi(en, ja)}</dt><dd class="num" data-info="{k}"></dd>' for k, en, ja in [
        ('claim', 'Claim', '主張'), ('n', 'n', 'n'), ('L', 'Side L', '辺 L'), ('B', 'Core side B', '芯の辺 B'),
        ('net', 'Net', '角度の網'), ('total_mass', 'Total mass', '総質量'), ('items', 'Items', '要素の数')])
    first = next((c for c in best if c['n'] == 41), best[0])
    return f'''<div class="cv" id="cv" data-first="certs/{first["file"][:-5]}" data-versions="{e(json.dumps(versions))}">
<div class="cv3">
<aside class="cv-list"><div class="cv-head dim"><span>n</span><span>{bi("lower bound", "下界")}</span><span></span></div><div class="cv-items">{side}</div></aside>
<div class="cv-main">
<div class="cv-grid">
<div class="cv-fig"><canvas class="m" width="600" height="600" aria-label="measure"></canvas>
</div>
<div class="cv-side">
<label class="cv-r">{bi("Certificate", "証明書")} <select id="cv-ver" aria-label="certificate"></select></label>
<dl class="kv">{info}<dt>{bi("Data", "データ")}</dt><dd><a data-rel href="#"></a><div class="dim" data-note hidden></div></dd><dt>{bi("Documents", "文書")}</dt><dd class="links" data-docs data-blob="{BLOB}"></dd></dl>
<label><input type="checkbox" id="cv-keep" checked> {bi("keep the unit square inside the container while dragging", "ドラッグ中も単位正方形を容器の中に留める")}</label>
<label class="cv-r">{bi("Direction", "角度")} <input type="range" id="cv-r" min="0" max="200" value="0" step="1"></label>
<dl class="kv">
<dt data-net="1">r</dt><dd data-net="1" class="num" data-o="t"></dd>
<dt><span data-net="1">θ = 2 arctan(r · step)</span><span data-net="0">θ</span></dt><dd class="num" data-o="theta"></dd>
<dt>{bi("Centre", "中心")}</dt><dd class="num" data-o="c"></dd>
<dt>{bi("Captured mass", "拾う質量")}</dt><dd class="num" data-o="m"></dd>
</dl>
<div data-kind="rect"><p class="note">{bi("Verifier's lower bound on the captured mass at each direction (verified_angles.jsonl in the Release asset). Click to choose r.",
  "各角度で検証器が出した、拾う質量の下界（Release の資産の verified_angles.jsonl）。押すと r を選べる。")}</p>
<canvas class="strip" aria-label="per-direction lower bound"></canvas>
<dl class="kv"><dt>{bi("Verifier's bound at r", "r での検証器の下界")}</dt><dd class="num" data-o="lb"></dd></dl></div>
<p><button type="button" id="cv-scan">{bi("Scan this direction (64 × 64 centres)", "この角度を走査（中心 64 × 64）")}</button></p>
<dl class="kv"><dt>{bi("Smallest captured mass", "拾う質量の最小")}</dt><dd class="num" data-o="scan">–</dd></dl>
<p class="note">{bi("Computed in the browser in floating point from values rounded to 9 digits. The exact data and the checker are in the Release asset.",
  "ブラウザで、9 桁に丸めた値から浮動小数点で計算している。厳密なデータと検査器は Release の資産にある。")}</p>
</div></div>
<h2>{bi("What the certificate states", "証明書が示すこと")}</h2>
<dl class="kv cv-states" data-states data-blob="{BLOB}" data-lb="{BLOB}{SRC_LB}#L60-L106" data-spec="{BLOB}{SRC_SPEC}"></dl>
</div></div>
</div>
<script src="viz/certificate.js" defer></script>'''
