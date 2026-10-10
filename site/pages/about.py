"""Credits page from docs/data/about.json."""
from lib import e, bi, bc, load, missing, src_links


def build():
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
