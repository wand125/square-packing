"""Renderers for the text pages (methods, themes, verify, about) from docs/data/*.json."""
import re
from build import bi, bd, e, load, missing, BLOB

LANGSW = ('<script>document.addEventListener("langchange",function(){var l=SP.L();'
          'document.querySelectorAll("option[data-en]").forEach(function(o){o.textContent=o.getAttribute("data-"+l);});});</script>')


def code(s):
    """Inline `code` spans in already-plain text."""
    return re.sub(r'`([^`]+)`', r'<code>\1</code>', e(s))


def bc(d):
    if not d:
        return ''
    if isinstance(d, str):
        return code(d)
    en, ja = d.get('en', ''), d.get('ja', '') or d.get('en', '')
    return code(en) if en == ja else f'<span data-l="en">{code(en)}</span><span data-l="ja">{code(ja)}</span>'


def src_links(s):
    if not s:
        return ''
    items = s if isinstance(s, list) else re.split(r';\s*', s)
    expanded = []
    for item in items:
        # A source can name several line ranges in one file.
        parts = re.split(r',\s*(?=L\d)', item)
        expanded.append(parts[0])
        expanded.extend(parts[0].split('#')[0] + '#' + part for part in parts[1:])
    out = []
    for it in expanded:
        it = it.strip()
        if not it:
            continue
        if it.startswith('http'):
            out.append(f'<a href="{e(it)}">{e(it.split("github.com/")[-1])}</a>')
        else:
            path = it.split(' ')[0]
            label = path.split('#')[0]
            label = '/'.join(label.split('/')[-2:]) if label.count('/') >= 2 else label
            out.append(f'<a href="{BLOB}{e(path)}">{e(label)}</a>')
    return ''.join(out)


def methods():
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


def themes():
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


def verify():
    d = load('verify.json')
    if not d:
        return missing('verify.json')
    steps = ''.join(f'<tr><td class="num">{i}</td><td>{bc(s)}</td><td>{("<pre>" + e(s["cmd"]) + "</pre>") if s.get("cmd") else ""}</td>'
                    f'<td class="links">{src_links(s.get("source"))}</td></tr>' for i, s in enumerate(d['steps'], 1))
    tools = ''.join(f'<tr><td class="nw"><a href="{BLOB}{e(t["path"])}"><code>{e(t["path"])}</code></a></td><td>{bc(t.get("what"))}</td>'
                    f'<td class="nw dim">{e(t.get("runtime", ""))}</td><td class="links">{src_links(t.get("source"))}</td></tr>' for t in d['tools'])
    req = ''.join(f'<tr><td><code>{e(r["tool"])}</code></td><td>{bc(r)}</td><td class="links">{src_links(r.get("source"))}</td></tr>' for r in d['requirements'])
    rel = ''.join(f'<tr><td class="nw"><a href="https://github.com/wand125/square-packing/releases/tag/{e(r["tag"])}"><code>{e(r["tag"])}</code></a></td>'
                  f'<td>{e(r.get("name", ""))}</td><td class="num dim">{e(r.get("date", ""))}</td></tr>' for r in d['releases'])
    n17 = ''.join(f'<li>{bc(x)}</li>' for x in d.get('n17', []))
    return f'''<h2>{bi("Checking one certificate", "証明書 1 件の検算")}</h2>
<p class="note">{bi("The check command, its folder and the asset names of each certificate are in its row on the Results page and in INDEX.json.", "各証明書の検算のコマンド・実行場所・資産の名前は、結果のページの行と INDEX.json にある。")}</p>
<div class="wrap"><table class="wide"><thead><tr><th>#</th><th>{bi("Step", "手順")}</th><th>{bi("Command", "コマンド")}</th><th>{bi("Source", "記述の元")}</th></tr></thead><tbody>{steps}</tbody></table></div>
<h2>{bi("Checkers, tools and Lean projects", "検査器・道具・Lean のプロジェクト")}</h2>
<div class="wrap"><table class="wide"><thead><tr><th>{bi("Folder", "フォルダ")}</th><th>{bi("What it does", "内容")}</th><th>{bi("Runtime", "実行環境")}</th><th>{bi("Source", "記述の元")}</th></tr></thead><tbody>{tools}</tbody></table></div>
<h2>{bi("Requirements", "必要なもの")}</h2>
<div class="wrap"><table class="wide"><thead><tr><th>{bi("Folder", "フォルダ")}</th><th>{bi("Requirement", "内容")}</th><th>{bi("Source", "記述の元")}</th></tr></thead><tbody>{req}</tbody></table></div>
<h2>{bi("Releases", "Release")}</h2>
<div class="wrap"><table><thead><tr><th>{bi("Tag", "タグ")}</th><th>{bi("Name", "名前")}</th><th>{bi("Date", "日付")}</th></tr></thead><tbody>{rel}</tbody></table></div>
<h2>n = 17</h2><ul class="tight">{n17}</ul>'''


def about():
    d = load('about.json')
    if not d:
        return missing('about.json')
    a = d['author']
    cr = ''.join(f'<tr><td><b>{e(c["who"])}</b></td><td>{bc(c.get("for"))}</td><td class="links">{src_links(c.get("source"))}</td></tr>' for c in d['credits'])
    rel = ''.join(f'<tr><td class="nw"><a href="{e(r["url"])}">{e(r["name"])}</a></td><td>{bc(r)}</td></tr>' for r in d['related'])
    mv = ''.join(f'<tr><td class="nw"><code>{e(m["old"])}</code></td><td><code>{e(m["new"])}</code></td></tr>' for m in d['moved']['table'])
    mvnote = d['moved'].get('note', {})
    return f'''<h2>{bi("Author", "著者")}</h2>
<p><a href="https://github.com/{e(a["github"])}">{e(a["github"])}</a> ({e(a["name"])})</p>
<h2>{bi("Credits", "クレジット")}</h2>
<div class="wrap"><table class="wide credits-table"><thead><tr><th>{bi("Who", "誰")}</th><th>{bi("For", "内容")}</th><th>{bi("Source", "記述の元")}</th></tr></thead><tbody>{cr}</tbody></table></div>
<h2>{bi("Related repositories and pages", "関連するリポジトリとページ")}</h2>
<div class="wrap"><table><thead><tr><th>{bi("Name", "名前")}</th><th>{bi("Relation", "関係")}</th></tr></thead><tbody>{rel}</tbody></table></div>
<h2>{bi("Moved repositories", "移したリポジトリ")}</h2>
<p class="note">{bc(mvnote)}</p>
<div class="wrap"><table><thead><tr><th>{bi("Old repository", "元のリポジトリ")}</th><th>{bi("New place", "移した先")}</th></tr></thead><tbody>{mv}</tbody></table></div>
<h2>{bi("Licenses", "ライセンス")}</h2>
<p>{bc(d["licenses"])}</p>'''
