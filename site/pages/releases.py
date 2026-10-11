"""Releases page: each published release of wand125/square-packing and the certificates and proofs it carries."""
import json, os, re

from lib import GH, REPO, bi, e, load
from pages import results as R


def build():
    idx = json.load(open(os.path.join(REPO, 'INDEX.json')))
    rows = R.square_rows(idx) + R.other_rows(idx)
    R.mark_best(rows)
    man = json.load(open(os.path.join(REPO, 'problems/n17/manifest.json')))
    # the tracking issues that link to each release (themes.json)
    th = {}
    for t in load('themes.json')['themes']:
        for tag in set(re.findall(r'releases/tag/([\w/.\-]+)', json.dumps(t))) | set(t.get('releases', [])):
            th.setdefault(tag, []).append(t)
    tr = []
    for rel in load('verify.json')['releases']:
        tag = rel['tag']
        items = [r for r in rows if r.get('rel') == tag or (r.get('rel_url') or '').endswith('/' + tag)]
        items.sort(key=lambda r: (list(R.CONT).index(r['cont']), r['n'], -r['v']))
        conts = sorted({r['cont'] for r in items}, key=list(R.CONT).index)
        meth = {}
        for r in items:
            meth[r['meth']] = meth.get(r['meth'], 0) + 1
        best = [r for r in items if r['best']]
        summ = ', '.join(f'{bi(*R.METH[m])} {k}' for m, k in sorted(meth.items(), key=lambda x: -x[1])) or '–'
        old = ' <span class="dim">(' + bi('superseded', '更新済み') + ')</span>'
        lst = ''.join(f'<li><span class="num">{e(r["short"])}</span> <span class="dim">{bi(*R.CONT[r["cont"]])}</span>'
                      f'{"" if r["best"] else old}</li>' for r in items)
        link = f'results.html?q={e(tag)}&amp;best=0' if items else ''
        tr.append(f'<tr class="r" data-n="0"><td class="nw"><a href="{GH}/releases/tag/{e(tag)}"><code>{e(tag)}</code></a></td>'
                  f'<td>{e(rel.get("name", ""))}</td><td class="num dim">{e(rel.get("date", ""))}</td>'
                  f'<td class="nw">{" ".join(f'<a href="{e(t["url"])}">#{t["issue"]}</a>' for t in th.get(tag, [])) or "–"}</td>'
                  f'<td class="nw">{", ".join(bi(*R.CONT[c]) for c in conts) or "–"}</td><td class="num">{len(items) or "–"}</td><td class="num">{len(best) or "–"}</td></tr>'
                  f'<tr class="x" hidden><td colspan="7"><dl>'
                  + (f'<dt>{bi("Methods", "手法")}</dt><dd>{summ}</dd>' if items else '')
                  + (f'<dt>{bi("Results", "結果")}</dt><dd><a href="{link}">{bi("open in the Results table", "結果の表で開く")}</a><ul class="tight rel-list">{lst}</ul></dd>' if items else
                     f'<dt>{bi("Contents", "内容")}</dt><dd>{e(rel.get("name", ""))}</dd>')
                  + '</dl></td></tr>')
    return f'''<p class="note">{bi("The published releases of wand125/square-packing, newest first. Click a row for the results it carries; the counts come from INDEX.json and the n = 17 manifest.",
  "wand125/square-packing の公開済みの Release（新しい順）。行を押すと含まれる結果が出る。件数は INDEX.json と n = 17 の manifest から。")}</p>
<div class="bar" data-filterbar="rl"><input type="search" data-key="q" id="r-q" data-ph-en="filter text" data-ph-ja="文字で絞り込み" aria-label="filter"><span class="count"></span></div>
<div class="wrap"><table class="wide"><thead><tr><th>{bi("Tag", "タグ")}</th><th>{bi("Name", "名前")}</th><th>{bi("Date", "日付")}</th><th>{bi("Theme", "テーマ")}</th><th>{bi("Containers", "容器")}</th>
<th>{bi("Certificates and proofs", "証明書と証明")}</th><th>{bi("Best for their n", "n ごとの最良")}</th></tr></thead>
<tbody id="rl">{"".join(tr)}</tbody></table></div>'''
