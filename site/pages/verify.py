"""Verify page from docs/data/verify.json."""
from lib import BLOB, e, bi, bc, load, missing, src_links


def build():
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
