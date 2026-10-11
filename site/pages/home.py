"""Top page: exact values and counts per container, packing thumbnails, the pages, the themes and recent releases."""
import json, os

from lib import GH, HERE, PREVIEW, PREVIEW_PAGES, bi, bd, e, load
from pages import results as R

PAGES = [  # file, en, ja, what it shows en/ja, group
    ('certificate.html', 'Certificate', '証明書の中身', 'Published square-container certificates drawn on [0, L]², with the mass a square captures.', '公開した正方形の容器の証明書を [0, L]² に描き、正方形が拾う質量を出す。', 'exp'),
    ('containers.html', 'Other containers', '正方形以外の容器', 'Triangles, the hexagon and the 1×2 rectangle: packings and certificate points.', '三角形・六角形・1×2 の長方形：詰め方と証明書の点。', 'exp'),
    ('rect-regions.html', 'Rectangles', '長方形の容器', 'For each k, the edge of the rectangles that hold k unit squares, piece by piece, with certified packings.', 'k ごとに、単位正方形が k 個入る長方形の端を、片ごとに証明書付きの配置とともに示す。', 'exp'),
    ('explain.html', 'How it works (preview)', '仕組み (preview)', 'The core square and the angle net, the branch and bound over centres, the k² − c lift.', '芯の正方形と角度の網、中心の分枝限定、k² − c の持ち上げ。', 'exp'),
    ('themes.html', 'Themes', 'Themes', 'The tracking issues: goal, method, completed stages.', '追跡用 Issue：目指すもの・方法・済んだ段階。', 'out'),
    ('results.html', 'Results', 'Results', 'Every certificate and proof: claim, method, check command and release asset.', 'すべての証明書と証明：主張・手法・検算のコマンド・Release の資産。', 'out'),
    ('releases.html', 'Releases', 'Release', 'The published releases and the results each carries.', '公開した Release と、それぞれが含む結果。', 'out'),
    ('methods.html', 'Methods', 'Methods', 'Each method: what the certificate contains, where it was used, origin and code.', '手法ごと：証明書の中身・使った対象・出典・コード。', 'out'),
    ('verify.html', 'Verify', 'Verify', 'How to check a certificate yourself: steps, requirements, checkers, releases.', '自分で検算する方法：手順・必要なもの・検査器・Release。', 'out'),
    ('about.html', 'Credits', 'クレジット', 'Credits, related repositories, moved repositories and licenses.', 'クレジット・関連リポジトリ・移したリポジトリ・ライセンス。', 'out'),
]
PAGES = [p for p in PAGES if PREVIEW or p[0] not in PREVIEW_PAGES]


def thumb(it, w=112):
    xs = [p[0] for p in it['poly']]; ys = [p[1] for p in it['poly']]
    x0, y0, x1, y1 = min(xs), min(ys), max(xs), max(ys)
    sc = (w - 6) / max(x1 - x0, y1 - y0); h = (y1 - y0) * sc + 6
    P = lambda p: f'{3 + (p[0] - x0) * sc:.2f},{h - 3 - (p[1] - y0) * sc:.2f}'
    sq = ''.join(f'<polygon points="{" ".join(P(p) for p in q)}" class="th-sq"/>' for q in it['packing'])
    return (f'<svg viewBox="0 0 {w} {h:.1f}" width="{w}" height="{h:.0f}" aria-hidden="true">'
            f'<polygon points="{" ".join(P(p) for p in it["poly"])}" class="th-c"/>{sq}</svg>')


def _rows():
    idx = json.load(open(os.path.join(R.REPO, 'INDEX.json')))
    rows = R.square_rows(idx) + R.other_rows(idx)
    R.mark_best(rows)
    return rows


def container_table():
    rows = _rows()
    tr = []
    for cont, (en, ja) in R.CONT.items():
        rs = [r for r in rows if r['cont'] == cont]
        best = [r for r in rs if r['best']]
        # s(n) >= k with n <= k^2 is an equality: the k x k grid holds k^2 squares (as the certificate READMEs state)
        grid = lambda r: cont == 'square' and r['kind'] == 'lb' and r['v'] == int(r['v']) and r['n'] <= int(r['v']) ** 2
        exact = sorted((r for r in best if r['kind'] == 'exact' or grid(r)), key=lambda r: r['n'])
        lb = [r for r in best if r['kind'] in ('lb', 'gt') and not grid(r)]
        ns = sorted({r['n'] for r in lb})
        rng = ((f'{len(ns)} n ({ns[0]}–{ns[-1]})' if len(ns) > 1 else f'n = {ns[0]}') if ns else '–') if cont != 'n17' else bi(f'{len(best)} sub-patterns', f'部分型 {len(best)} 件')
        ex = ', '.join(e(r['short'].split(' ≈ ')[0].replace(' ≥ ', ' = ')) for r in exact) or '–'
        tr.append(f'<tr><td class="nw"><a href="results.html?cont={cont}">{bi(en, ja)}</a></td><td>{ex}</td>'
                  f'<td class="num">{rng}</td><td class="num">{len(rs)}</td></tr>')
    return f'''<div class="wrap"><table><thead><tr><th>{bi("Container", "容器")}</th><th>{bi("Optimal values proved", "示した最適値")}</th>
<th>{bi("Lower bounds (best per n)", "下界（n ごとの最良）")}</th><th>{bi("Certificates and proofs", "証明書と証明")}</th></tr></thead><tbody>{"".join(tr)}</tbody></table></div>'''


def result_map():
    """n across, one row per container; a cell is coloured when a published result for that n exists."""
    rows = [r for r in _rows() if r['best'] and r['cont'] != 'n17']
    grid = lambda r: r['cont'] == 'square' and r['kind'] == 'lb' and r['v'] == int(r['v']) and r['n'] <= int(r['v']) ** 2
    conts = [c for c in R.CONT if any(r['cont'] == c for r in rows)]
    nmax = max(r['n'] for r in rows)
    cw, ch, top = 6, 16, 16
    W = (nmax + 1) * cw
    out = []
    # the n labels are HTML placed in percent, since the SVG stretches to the width
    ticks = ''.join(f'<span style="left:{(i * cw + cw / 2) / W * 100:.2f}%">{i}</span>' for i in range(10, nmax + 1, 10))
    for j, c in enumerate(conts):
        y = j * (ch + 4)
        out.append(f'<rect x="{cw:.1f}" y="{y}" width="{W - cw:.1f}" height="{ch}" class="rm-bg"/>')
        for r in sorted((r for r in rows if r['cont'] == c), key=lambda r: r['n']):
            k = 'rm-ex' if r['kind'] == 'exact' or grid(r) else 'rm-lb'
            out.append(f'<a href="results.html?cont={c}"><rect x="{r["n"] * cw:.1f}" y="{y}" width="{cw - 1}" height="{ch}" class="{k}">'
                       f'<title>{e(r["short"])}</title></rect></a>')
    H = len(conts) * (ch + 4)
    labels = ''.join(f'<div style="height:{ch}px">{bi(*R.CONT[c])}</div>' for c in conts)
    key = (f'<span class="rm-key"><i class="rm-ex"></i>{bi("optimal value proved", "最適値を証明")}</span>'
           f'<span class="rm-key"><i class="rm-lb"></i>{bi("lower bound with a certificate", "証明書付きの下界")}</span>'
           f'<span class="rm-key"><i class="rm-bg"></i>{bi("no result", "結果なし")}</span>')
    return (f'<div class="rmap"><div class="rm-l" style="padding-top:{top}px">{labels}</div>'
            f'<div class="rm-f"><div class="rm-n">{ticks}</div><svg viewBox="0 0 {W} {H}" preserveAspectRatio="none" style="height:{H}px">{"".join(out)}</svg></div></div>'
            f'<p class="rm-keys">{key} <span class="dim">n = 1 … {nmax}</span></p>')


def thumbs():
    cont = json.load(open(os.path.join(HERE, 'data', 'containers.json')))
    th = ''.join(f'<a class="th" href="containers.html#{it["cont"]}-{it["n"]}">{thumb(it)}<span class="num">{e(it["claim"])}</span></a>'
                 for it in cont if it['packing'])
    return f'<div class="thumbs">{th}</div>'


def page_table(group):
    return '<div class="wrap"><table><tbody>' + ''.join(
        f'<tr><td class="nw"><a href="{f}">{bi(en, ja)}</a></td><td>{bi(we, wj)}</td></tr>' for f, en, ja, we, wj, g in PAGES if g == group) + '</tbody></table></div>'


def themes_table():
    t = load('themes.json')
    return '<div class="wrap"><table><tbody>' + ''.join(
        f'<tr><td class="num"><a href="{e(x["url"])}">#{x["issue"]}</a></td>'
        f'<td class="nw"><span class="st{" ex" if x["state"] != "open" else ""}">{bi("open", "進行中") if x["state"] == "open" else bi("closed", "完了")}</span></td><td>{bd(x["title"])}</td>'
        f'<td class="num dim">{e(x.get("updated", ""))}</td></tr>' for x in sorted(t['themes'], key=lambda x: x['state'] == 'open')) + '</tbody></table></div>'


def releases_table(k=6):
    v = load('verify.json')
    return '<div class="wrap"><table><tbody>' + ''.join(
        f'<tr><td class="nw"><a href="{GH}/releases/tag/{e(r["tag"])}"><code>{e(r["tag"])}</code></a></td><td>{e(r.get("name", ""))}</td>'
        f'<td class="num dim">{e(r.get("date", ""))}</td></tr>' for r in v['releases'][:k]) + '</tbody></table></div>'


def build():
    # the top page: the visualize top, then the results top, as they are
    from pages import guide, outcomes
    raw = lambda en, ja: f'<span data-l="en">{en}</span><span data-l="ja">{ja}</span>'   # both languages, with links kept
    intro = (f'<div class="intro"><p>' + raw('Research themes and results on packing unit squares, mainly by wand125. '
             'Most of them are proofs of optimal values and lower bounds, in squares and in other containers (triangles, a regular hexagon, rectangles); '
             f'the proofs are published on <a href="{GH}">GitHub</a>.',
             '主に wand125 による、単位正方形の詰め込みの研究テーマと成果をまとめたページ。'
             f'主に最適値と下界の証明で、容器は正方形のほか三角形・正六角形・長方形。証明は <a href="{GH}">GitHub</a> で公開している。') + '</p>'
             '<p>' + bi('For the best known packings, and for solved and open problems, see also:', '既知最良の詰め方や、解決済み・未解決の取り組みは、以下も参考になる。') + '</p><ul class="tight">'
             '<li><a href="https://jlevy.github.io/squares/">The Squares Project</a> (jlevy)</li>'
             '<li><a href="https://evand.github.io/square-packing/">Square Packing Atlas</a> (evand)</li>'
             '<li><a href="https://erich-friedman.github.io/packing/">Packing Center</a> (Erich Friedman)</li></ul></div>')
    return (intro + f'<h2 class="top-h"><a href="guide.html">{bi("Visualize", "ビジュアライズ")}</a></h2>{guide.build()}'
            f'<h2 class="top-h"><a href="outcomes.html">{bi("Outcomes", "成果")}</a></h2>{outcomes.build()}')
