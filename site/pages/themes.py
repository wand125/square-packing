"""Themes page from docs/data/themes.json."""
from lib import LANGSW, e, bi, bc, load, missing


def build():
    d = load('themes.json')
    if not d:
        return missing('themes.json')
    tr = []
    for t in d['themes']:
        st = bi('open', '進行中') if t['state'] == 'open' else bi('closed', '完了')
        done = ''.join(f'<li>{bc(x)}</li>' for x in t.get('done', []))
        wo = ''.join(f'<li>{bc(x)}</li>' for x in t.get('working_on', []))
        links = ''.join(f'<a href="{e(l["url"])}">{e(l["label"])}</a>' for l in t.get('links', []))
        extra = ''
        # Target tables are withheld pending publication approval.
        tr.append(f'<tr class="r" data-state="{t["state"]}" data-n="0"><td class="num"><a href="{e(t["url"])}">#{t["issue"]}</a></td>'
                  f'<td><b>{bc(t["title"])}</b></td><td class="nw"><span class="st{" ex" if t["state"] != "open" else ""}">{st}</span></td>'
                  f'<td>{bc(t.get("goal"))}</td><td class="num dim">{e(t.get("updated", ""))}</td></tr>'
                  f'<tr class="x" hidden><td colspan="5"><dl>'
                  f'<dt>{bi("Method", "方法")}</dt><dd>{bc(t.get("method"))}</dd>'
                  + (f'<dt>{bi("Done", "済んだ段階")}</dt><dd><ul class="tight">{done}</ul>{extra}</dd>' if done or extra else '')
                  + (f'<dt>{bi("Working on", "取り組み中")}</dt><dd><ul class="tight">{wo}</ul></dd>' if wo else '')
                  + (f'<dt>{bi("Links", "リンク")}</dt><dd class="links">{links}</dd>' if links else '')
                  + '</dl></td></tr>')
    return f'''<p class="note">{bi("The tracking issues of wand125/square-packing (label theme). Click a row for the method, completed stages and links.", "wand125/square-packing の追跡用 Issue（ラベル theme）。行を押すと方法・済んだ段階・リンクが出る。")}</p>
<div class="bar" data-filterbar="th">
  <label>{bi("State", "状態")} <select data-key="state" id="t-state"><option value="" data-en="all" data-ja="すべて">all</option><option value="open" data-en="open" data-ja="進行中">open</option><option value="closed" data-en="closed" data-ja="完了">closed</option></select></label>
  <span class="count"></span>
</div>
<div class="wrap"><table class="wide"><thead><tr><th>Issue</th><th>{bi("Theme", "テーマ")}</th><th>{bi("State", "状態")}</th><th>{bi("Goal", "目指すもの")}</th><th>{bi("Updated", "更新")}</th></tr></thead>
<tbody id="th">{"".join(tr)}</tbody></table></div>{LANGSW}'''
