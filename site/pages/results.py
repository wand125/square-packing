"""Results page: every certificate and proof from INDEX.json, the right-isosceles README and the n17 manifest."""
import json, os, re
from fractions import Fraction

from lib import GH, BLOB, REPO, e, bi, bd, load

CONT = {
    'square': ('Square', '正方形'),
    'triangle': ('Equilateral triangle', '正三角形'),
    'right-isosceles': ('Right isosceles triangle', '直角二等辺三角形'),
    'hexagon': ('Regular hexagon', '正六角形'),
    'domino': ('1×2 rectangle', '1×2 の長方形'),
    'n17': ('Square, n = 17 sub-patterns', '正方形 n = 17 の部分型'),
}
METH = {
    'point': ('weighted points', '点の重み'),
    'rect': ('rectangle density', '矩形密度'),
    'mixed': ('mixed', '混合'),
    'lift': ('k² − c lift (points + segments)', 'k² − c の持ち上げ（点＋線分）'),
    'points-lemma': ('points + local lemma', '点＋局所補題'),
    'two-stage': ('two stages + local lemma', '2 段＋局所補題'),
    'bb': ('sub-pattern branch and bound', '部分型の分枝限定'),
}
NUMW = {'two': '2', 'three': '3', 'four': '4', 'six': '6'}


def frac_val(s):
    s = s.strip()
    try:
        return float(Fraction(s))
    except Exception:
        return float(s)


def square_rows(idx):
    rows = []
    for c in idx['problems']['square-lower-bounds']:
        cl, i = c['claim'], c['id']
        m = re.match(r's\((\d+)\) (>=|=) ([0-9./]+)(?: = ([0-9./]+))?$', cl)
        if m:
            n, op, a = int(m.group(1)), m.group(2), m.group(3)
            v = frac_val(m.group(4) or a)
            dec = None if '/' not in a else f'{v:g}'
            short = f's({n}) {"≥" if op == ">=" else "="} {a}' + (f' = {dec}' if dec else '')
            kind = 'exact' if op == '=' else 'lb'
            ja = cl
        else:
            m = re.match(r'No packing of (\d+) closed unit squares fits in the closed square of side ([0-9/]+) \(= ([0-9.]+)\)\.', cl)
            assert m, cl
            n, a, d = int(m.group(1)), m.group(2), m.group(3)
            v, kind = float(d), 'gt'
            short = f's({n}) > {a} = {d}'
            ja = f'{n} 個の閉じた単位正方形は、辺 {a}（= {d}）の閉じた正方形に入らない。'
        key = i.split(':', 1)[1]
        meth = ('rect' if 'rect_n' in key else 'mixed' if 'mixed_n' in key else 'lift' if re.search(r'/k2m\d', key)
                else 'point')
        rows.append(dict(cont='square', n=n, v=v, kind=kind, short=short, claim_en=cl, claim_ja=ja, meth=meth,
                         rel=c['release_tag'], assets=c['assets'], check=c['check'], cwd=c['check_cwd'],
                         docs=c['documents'], id=i))
    return rows


def other_rows(idx):
    rows = []
    for c in idx['problems']['triangle']:
        cl = c['claim']
        m = re.match(r'The smallest equilateral triangle containing (\w+) non-overlapping unit squares has side v = (.+?) ≈ ([0-9.]+)\.$', cl)
        if m:
            n = int(NUMW.get(m.group(1), m.group(1)))
            short, v, kind = f's({n}) = {m.group(2)} ≈ {m.group(3)}', float(m.group(3)), 'exact'
            ja = f'{n} 個の重ならない単位正方形が入る最小の正三角形の辺は v = {m.group(2)} ≈ {m.group(3)}。'
        else:
            m = re.match(r'No (\d+) non-overlapping unit squares fit in an equilateral triangle of side less than v = (.+?) ≈ ([0-9.]+)', cl)
            assert m, cl
            n = int(m.group(1))
            short, v, kind = f's({n}) ≥ {m.group(2)} ≈ {m.group(3)}', float(m.group(3)), 'lb'
            ja = f'{n} 個の重ならない単位正方形は、辺が v = {m.group(2)} ≈ {m.group(3)} 未満の正三角形には入らない。'
            rest = cl[m.end():].strip(' ;,.')
            if rest:
                ja += '（原文：' + rest + '）'
        meth = 'points-lemma' if n in (4, 6) else 'point'
        rows.append(dict(cont='triangle', n=n, v=v, kind=kind, short=short, claim_en=cl, claim_ja=ja, meth=meth,
                         rel=c['release_tag'], assets=c['assets'], check=c['check'], cwd=c['check_cwd'],
                         docs=c['documents'], id=c['id']))
    for c in idx['problems']['hexagon']:
        rows.append(dict(cont='hexagon', n=3, v=(1 + 3 ** .5) / 2, kind='exact', short='s(3) = (1 + √3)/2 ≈ 1.36603',
                         claim_en=c['claim'], claim_ja='重ならない単位正方形 3 個が入る最小の正六角形の辺は s(3) = v = (1 + √3)/2 ≈ 1.36603。',
                         meth='two-stage', rel=c['release_tag'], assets=c['assets'], check=c['check'], cwd=c['check_cwd'],
                         docs=c['documents'], id=c['id']))
    for c in idx['problems']['domino']:
        rows.append(dict(cont='domino', n=4, v=1.93028330671426938847, kind='exact', short='s(4) = v4 ≈ 1.930283',
                         claim_en=c['claim'], claim_ja='s(4) = v4。v4 ≈ 1.93028330671426938847 は 5x³ + 8x² − 32x − 4 の最大の実根。',
                         meth='points-lemma', rel=c['release_tag'], assets=c['assets'], check=c['check'], cwd=c['check_cwd'],
                         docs=c['documents'], id=c['id']))
    # right isosceles: README table (certificates are in git, no release)
    ri = open(os.path.join(REPO, 'problems/right-isosceles/README.md')).read()
    cmds = dict(re.findall(r'(python3 checker/check\.py certificates/n(\d+)/\S+ .*)', ri) and
                [(m[1], m[0]) for m in re.findall(r'(python3 checker/check\.py certificates/n(\d+)/\S+[^\n]*)', ri)])
    for line in ri.splitlines():
        m = re.match(r'\| (\d+) \| ([^|]+) \| ([0-9.]+) \| ([^|]+) \| ([^|]+) \|$', line)
        if not m:
            continue
        n, val, approx, cert = int(m.group(1)), m.group(2).strip(), m.group(3), m.group(5).strip()
        rows.append(dict(cont='right-isosceles', n=n, v=float(approx), kind='exact', short=f's({n}) = {val} ≈ {approx}',
                         claim_en=f'The smallest right isosceles triangle containing {n} non-overlapping unit squares has leg s({n}) = {val} ≈ {approx}. Certificate: {cert}.',
                         claim_ja=f'{n} 個の重ならない単位正方形が入る最小の直角二等辺三角形の脚は s({n}) = {val} ≈ {approx}。証明書：{cert}。',
                         meth='points-lemma' if 'Lemma P' in cert else 'point', rel='', assets=[],
                         check=cmds.get(str(n), ''), cwd='problems/right-isosceles',
                         docs=[f'problems/right-isosceles/certificates/n{n}/PROOF.md', 'problems/right-isosceles/README.md'],
                         id=f'right-isosceles:n{n}'))
    man = json.load(open(os.path.join(REPO, 'problems/n17/manifest.json')))
    for c in man['published']:
        rows.append(dict(cont='n17', n=17, v=4.676, kind='sub', short=f'{c["class"]}: {len(c["cells"])} cells, {c["nodes"]:,} nodes',
                         claim_en=c['claim'],
                         claim_ja='認証済みの不可能：辺 1169/250 以下の正方形に重ならない単位正方形 17 個を、型の各セルに中心が 1 つずつあるように置くことはできない（jlevy/squares の 24 セルの被覆 \'ring-3-voronoi-8-tabbed-unique\'）。',
                         meth='bb', rel='', rel_url=c['data']['release_url'], assets=[],
                         check='\n'.join(c['checks']), cwd='', docs=[c['manifest'], 'problems/n17/manifest.json'], id=c['id']))
    return rows


def mark_best(rows):
    best = {}
    for r in rows:
        if r['cont'] == 'n17':
            r['best'] = True
            continue
        k = (r['cont'], r['n'])
        score = (r['v'], 2 if r['kind'] == 'exact' else 1 if r['kind'] == 'gt' else 0)
        if k not in best or score > best[k][0]:
            best[k] = (score, r)
    for r in rows:
        if r['cont'] != 'n17':
            r['best'] = best[(r['cont'], r['n'])][1] is r


def build():
    idx = json.load(open(os.path.join(REPO, 'INDEX.json')))
    rows = square_rows(idx) + other_rows(idx)
    mark_best(rows)
    order = list(CONT)
    rows.sort(key=lambda r: (order.index(r['cont']), r['n'], -r['v']))
    KIND = {'exact': ('optimal value', '最適値'), 'lb': ('lower bound', '下界'), 'gt': ('lower bound (strict)', '下界（真に大きい）'),
            'sub': ('sub-pattern excluded', '部分型の除外')}
    notes = {}
    for method in load('methods.json')['rows']:
        for result_id, note in method.get('result_notes', {}).items():
            notes[result_id] = dict(note, review_status=method.get('review_status'))
    tr = []
    for r in rows:
        relurl = r.get('rel_url') or (f'{GH}/releases/tag/{r["rel"]}' if r['rel'] else '')
        rel = f'<a href="{e(relurl)}">{e(r["rel"] or "release")}</a>' if relurl else bi('in git', 'git 内')
        docs = ''.join(f'<a href="{BLOB}{e(d)}">{e(d.split("/")[-1] if d.count("/") < 3 else "/".join(d.split("/")[-2:]))}</a>'
                       for d in r['docs'][:2])
        st = 'ex' if r['kind'] in ('exact',) else ''
        note = notes.get(r['id'])
        consequence = ''
        if note:
            consequence = (
                f'<dt>{bi("Consequence in the source", "原典での帰結")}</dt><dd>'
                + bd(note['consequence']) + ' ' + bd(note.get('review_status'))
                + f' <a href="{BLOB}{e(note["source"])}">README · {bi("statement and status", "主張と検証状況")}</a></dd>')
        tr.append(
            f'<tr class="r{"" if r["best"] else " old"}" data-cont="{r["cont"]}" data-meth="{r["meth"]}" data-best="{"1" if r["best"] else ""}" '
            f'data-kind="{r["kind"]}" data-n="{r["n"]}" data-v="{r["v"]:.6f}">'
            f'<td class="nw">{bi(*CONT[r["cont"]])}</td><td class="num">{r["n"]}</td><td class="num">{e(r["short"])}</td>'
            f'<td class="nw"><span class="st {st}">{bi(*KIND[r["kind"]])}</span></td><td class="nw dim">{bi(*METH[r["meth"]])}</td>'
            f'<td class="links">{rel}</td><td class="links">{docs}</td></tr>'
            f'<tr class="x" hidden><td colspan="7"><dl>'
            f'<dt>{bi("Certificate claim", "証明書の主張") if note else bi("Claim", "主張")}</dt><dd>{bi(r["claim_en"], r["claim_ja"])}</dd>'
            + consequence
            + (f'<dt>{bi("Assets", "資産")}</dt><dd><code>{e(" ".join(r["assets"]))}</code></dd>' if r['assets'] else '')
            + (f'<dt>{bi("Check", "検算")}</dt><dd><pre>{e(r["check"])}</pre></dd>' if r['check'] else '')
            + (f'<dt>{bi("Run in", "実行場所")}</dt><dd><code>{e(r["cwd"])}</code></dd>' if r['cwd'] else '')
            + f'<dt>id</dt><dd><code>{e(r["id"])}</code></dd></dl></td></tr>')
    # <option> cannot hold spans: render options per language via data attributes
    opts_c = ''.join(f'<option value="{k}" data-en="{e(v[0])}" data-ja="{e(v[1])}">{e(v[0])}</option>' for k, v in CONT.items())
    opts_m = ''.join(f'<option value="{k}" data-en="{e(v[0])}" data-ja="{e(v[1])}">{e(v[0])}</option>' for k, v in METH.items())
    opts_k = ''.join(f'<option value="{k}" data-en="{e(v[0])}" data-ja="{e(v[1])}">{e(v[0])}</option>' for k, v in KIND.items())
    nbest = sum(r['best'] for r in rows)
    body = f'''<p class="note">{bi(f"{len(rows)} certificates and proofs from INDEX.json and the problem folders of wand125/square-packing; {nbest} are selected by the strongest recorded bound for each container and n (including the published n = 17 sub-patterns). Click a row for the claim, the check command and the release assets.",
                f"wand125/square-packing の INDEX.json と問題のフォルダから、証明書と証明 {len(rows)} 件。容器と n ごとの記録内の最強の下界（公開済み n = 17 の部分型を含む）として {nbest} 件を選択。行を押すと主張・検算のコマンド・Release の資産が出る。")}</p>
<div class="bar" data-filterbar="res">
  <label>{bi("Container", "容器")} <select data-key="cont" id="f-cont"><option value="" data-en="all" data-ja="すべて">all</option>{opts_c}</select></label>
  <label>{bi("Method", "手法")} <select data-key="meth" id="f-meth"><option value="" data-en="all" data-ja="すべて">all</option>{opts_m}</select></label>
  <label>{bi("Kind", "種類")} <select data-key="kind" id="f-kind"><option value="" data-en="all" data-ja="すべて">all</option>{opts_k}</select></label>
  <label>n <input type="number" data-key="nmin" id="f-nmin" min="1" aria-label="n min"> – <input type="number" data-key="nmax" id="f-nmax" min="1" aria-label="n max"></label>
  <label><input type="checkbox" data-key="best" id="f-best" checked> {bi("strongest per n only", "n ごとの最強のみ")}</label>
  <input type="search" data-key="q" id="f-q" data-ph-en="filter text" data-ph-ja="文字で絞り込み" aria-label="filter">
  <span class="count"></span>
</div>
<div class="wrap"><table class="wide">
<thead><tr><th class="sort" data-sort="cont">{bi("Container", "容器")}</th><th class="sort" data-sort="n">n</th><th class="sort" data-sort="v">{bi("Result", "結果")}</th>
<th>{bi("Kind", "種類")}</th><th class="sort" data-sort="meth">{bi("Method", "手法")}</th><th>{bi("Data", "データ")}</th><th>{bi("Documents", "文書")}</th></tr></thead>
<tbody id="res">
{chr(10).join(tr)}
</tbody></table></div>
<script>document.addEventListener("langchange",function(){{var l=SP.L();document.querySelectorAll("option[data-en]").forEach(function(o){{o.textContent=o.getAttribute("data-"+l);}});}});</script>'''
    return body
