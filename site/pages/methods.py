"""Methods page from docs/data/methods.json."""
from lib import BLOB, e, bi, bd, bc, load, missing, src_links


def build():
    d = load('methods.json')
    if not d:
        return missing('methods.json')
    tr = []
    for r in d['rows']:
        tools = ''.join(f'<a href="{BLOB}{e(t.rstrip("/"))}">{e(t.rstrip("/").split("/")[-1])}</a>' for t in r.get('tools', []))
        tr.append(f'<tr class="r" data-n="0"><td><b>{bd(r.get("name"))}</b></td><td>{bc(r.get("what") or r.get("consists") or r.get("description"))}</td>'
                  f'<td>{bc(r.get("used") or r.get("used_for"))}{(" " + bc(r["review_status"])) if r.get("review_status") else ""}</td><td>{bc(r.get("origin") or r.get("credit"))}</td>'
                  f'<td class="links">{tools}</td><td class="links">{src_links(r.get("sources"))}</td></tr>')
    return f'''<div class="bar" data-filterbar="mt"><input type="search" data-key="q" id="m-q" data-ph-en="filter text" data-ph-ja="文字で絞り込み" aria-label="filter"><span class="count"></span></div>
<div class="wrap"><table class="wide methods-table"><thead><tr><th>{bi("Method", "手法")}</th><th>{bi("Certificate and check", "証明書と検査")}</th>
<th>{bi("Used for", "使った対象")}</th><th>{bi("Origin and credit", "出典")}</th><th>{bi("Code", "コード")}</th><th>{bi("Source", "記述の元")}</th></tr></thead>
<tbody id="mt">{"".join(tr)}</tbody></table></div>'''
