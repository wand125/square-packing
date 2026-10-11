#!/usr/bin/env python3
"""Build the static site from the repository (INDEX.json, problem folders) and docs/data/*.json.

python3 site/build.py           -> site/_site/
python3 site/build.py OUTDIR    -> OUTDIR/

One module in pages/ per page; shared helpers and the page frame are in lib.py.
"""
import hashlib, importlib, os, re, shutil, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from lib import PREVIEW, PREVIEW_PAGES, frame  # noqa: E402

OUT = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else os.path.join(HERE, '_site')

PAGES = [  # file, en, ja, <title>, module in pages/, header row ('out': results, 'exp': explanations)
    ('index.html', 'Home', 'トップ', 'wand125 Square Packing', 'home', 'top'),
    ('outcomes.html', 'Outcomes top', '成果トップ', 'Square Packing Outcomes', 'outcomes', 'top-out'),
    ('guide.html', 'Visualize top', 'ビジュアライズトップ', 'Square Packing Visualizations', 'guide', 'top-exp'),
    ('themes.html', 'Themes', 'Themes', 'Square Packing Themes', 'themes', 'out'),
    ('results.html', 'Results', 'Results', 'Square Packing Results', 'results', 'out'),
    ('releases.html', 'Releases', 'Release', 'Square Packing Releases', 'releases', 'out'),
    ('methods.html', 'Methods', 'Methods', 'Square Packing Methods', 'methods', 'out'),
    ('verify.html', 'Verify', 'Verify', 'Checking the Certificates', 'verify', 'out'),
    ('about.html', 'Credits', 'クレジット', 'Square Packing Credits', 'about', 'out'),
    ('certificate.html', 'Certificate', '証明書の中身', 'Certificate Viewer', 'certificate', 'exp'),
    ('rect-player.html', 'Player', '再生', 'Rectangles Player', 'rect_player', ''),
    ('containers.html', 'Other containers', '正方形以外の容器', 'Non-Square Containers', 'containers', 'exp'),
    ('rect-regions.html', 'Rectangles', '長方形の容器', 'Squares in Rectangles', 'rect_regions', 'exp'),
    ('explain.html', 'How it works (preview)', '仕組み (preview)', 'How the Certificates Work', 'explain', 'exp'),
]

PAGES = [p for p in PAGES if PREVIEW or p[0] not in PREVIEW_PAGES]

def stamp(ref):
    p = os.path.join(OUT, ref)
    return hashlib.sha256(open(p, 'rb').read()).hexdigest()[:10] if os.path.exists(p) else '0'


def main():
    if os.path.exists(OUT):
        shutil.rmtree(OUT)
    os.makedirs(OUT)
    for f in ('site.css', 'site.js'):
        shutil.copy(os.path.join(HERE, 'src', f), OUT)
    for src, dst in (('src/viz', 'viz'), ('data', 'data')):
        if os.path.isdir(os.path.join(HERE, src)):
            shutil.copytree(os.path.join(HERE, src), os.path.join(OUT, dst))
    for fn, _, _, _, mod, _ in PAGES:
        body = importlib.import_module('pages.' + mod).build()
        html = frame(PAGES, fn, body)
        # version the scripts and the stylesheet by their content, so a new build is not hidden by the browser cache
        for ref in re.findall(r'(?:src|href)="((?:viz/)?[\w.-]+\.(?:js|css))"', html):
            html = html.replace(f'"{ref}"', f'"{ref}?v={stamp(ref)}"')
        open(os.path.join(OUT, fn), 'w').write(html)
    print('built', OUT, sorted(os.listdir(OUT)))


if __name__ == '__main__':
    main()
