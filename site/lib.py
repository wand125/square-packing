"""Shared paths and helpers for the page builders: escaping, the two-language spans, links and the page frame."""
import html, json, os, re

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
CONTENT = os.path.join(REPO, 'docs', 'data')
GH = 'https://github.com/wand125/square-packing'
BLOB = GH + '/blob/main/'
# the preview build (preview.sh sets SP_PREVIEW=1) has the preview-only pages and data; the release build
# (GitHub Actions) leaves them out. Both have the Japanese switch
PREVIEW = os.environ.get('SP_PREVIEW') == '1'
PREVIEW_PAGES = {'explain.html'}

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
    link = lambda p: f'<a href="{"./" if p[0] == "index.html" else p[0]}"{" class=\"cur\"" if p[0] == fn else ""}>{bi(p[1], p[2])}</a>'
    # two rows: results that follow the GitHub repository, and explanations by subject
    row = lambda g: ''.join(link(p) for p in pages if len(p) > 5 and p[5] == g and p[0] != 'about.html')
    nav, nav2 = row('out'), row('exp')
    credits = ''.join(link(p) for p in pages if p[0] == 'about.html')  # placed after the GitHub link
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
  <div class="hrow"><a class="site" href="./">wand125/square-packing</a><span class="tools"><a class="gh" href="{GH}" target="_blank" rel="noopener" aria-label="GitHub" title="GitHub"><svg viewBox="0 0 16 16" width="16" height="16" aria-hidden="true"><path fill="currentColor" d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z"/></svg></a>{credits}<button id="lang" type="button">日本語</button><button id="theme" type="button">Light</button></span></div>
  <nav class="hrow"><a class="nl{" cur" if fn == "guide.html" else ""}" href="guide.html">{bi('Visualize', 'ビジュアライズ')}</a>{nav2}</nav>
  <nav class="hrow"><a class="nl{" cur" if fn == "outcomes.html" else ""}" href="outcomes.html">{bi('Outcomes', '成果')}</a>{nav}</nav>
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
