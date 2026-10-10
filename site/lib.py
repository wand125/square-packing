"""Shared paths and helpers for the page builders: escaping, the two-language spans, links and the page frame."""
import html, json, os, re

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
CONTENT = os.path.join(REPO, 'docs', 'data')
GH = 'https://github.com/wand125/square-packing'
BLOB = GH + '/blob/main/'

DESC = {
    'en': 'Lower bounds and optimality proofs for packing unit squares in squares, triangles, a regular hexagon and a 1×2 rectangle, with certificates, checkers and Lean proofs.',
    'ja': '単位正方形の詰め込みの下界と最適性の証明（容器は正方形・三角形・正六角形・1×2 の長方形）。証明書・検査器・Lean の証明つき。',
}
def e(s):
    return html.escape(str(s), quote=True)


def bi(en, ja=None, tag='span'):
    """Both languages; ja falls back to en."""
    ja = en if ja is None or ja == '' else ja
    if en == ja:
        return e(en)
    return f'<{tag} data-l="en">{e(en)}</{tag}><{tag} data-l="ja">{e(ja)}</{tag}>'


def bd(d, key=None, tag='span'):
    if d is None:
        return ''
    if isinstance(d, str):
        return e(d)
    return bi(d.get('en', ''), d.get('ja', ''), tag)


def frame(pages, fn, body):
    """pages: (file, en, ja, <title>) for the nav; fn: this page."""
    cur = [p for p in pages if p[0] == fn][0]
    nav = ''.join(f'<a href="{"./" if p[0] == "index.html" else p[0]}"{" class=\"cur\"" if p[0] == fn else ""}>{bi(p[1], p[2])}</a>' for p in pages)
    head = f'''<title>{e(cur[3])}</title>
<meta name="description" content="{e(DESC['en'])}">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono&family=IBM+Plex+Sans:wght@400;600&display=swap">
<link rel="stylesheet" href="site.css">
<script>
(function(){{var H=document.documentElement;if(H.lang!=="ja")H.lang="en";if(!H.dataset.theme)H.dataset.theme="dark";
try{{var t=localStorage.getItem("sp-theme");if(t)H.dataset.theme=t;var l=localStorage.getItem("sp-lang");if(l)H.lang=l;}}catch(e){{}}}})();
</script>
<script src="site.js"></script>'''
    top = f'''<header class="top">
  <span class="site">wand125/square-packing</span>
  <nav>{nav}<a href="{GH}">GitHub</a></nav>
  <span class="sw"><button id="lang" type="button">日本語</button><button id="theme" type="button">Light</button></span>
  <span class="desc">{bi(DESC['en'], DESC['ja'])}</span>
</header>
<main>
{body}
</main>'''
    return f'''<!doctype html>
<html lang="en" data-theme="dark">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
{head}
</head>
<body>
{top}
</body>
</html>
'''


def load(name):
    p = os.path.join(CONTENT, name)
    return json.load(open(p)) if os.path.exists(p) else None


def missing(name):
    return f'<p class="note">{bi(f"(docs/data/{name} not built yet)", f"（docs/data/{name} はまだ）")}</p>'



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
