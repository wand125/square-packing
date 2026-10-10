#!/usr/bin/env python3
"""Build the static site from the repository (INDEX.json, problem folders) and docs/data/*.json.

python3 site/build.py           -> site/_site/
python3 site/build.py OUTDIR    -> OUTDIR/

One module in pages/ per page; shared helpers and the page frame are in lib.py.
"""
import importlib, os, shutil, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from lib import frame  # noqa: E402

OUT = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else os.path.join(HERE, '_site')

PAGES = [  # file, en, ja, <title>, module in pages/
    ('index.html', 'Results', '結果', 'Square Packing Results', 'results'),
    ('methods.html', 'Methods', '手法', 'Square Packing Methods', 'methods'),
    ('themes.html', 'Themes', 'テーマ', 'Square Packing Themes', 'themes'),
    ('verify.html', 'Verify', '検算', 'Checking the Certificates', 'verify'),
    ('about.html', 'Credits', 'クレジット', 'Square Packing Credits', 'about'),
]


def main():
    if os.path.exists(OUT):
        shutil.rmtree(OUT)
    os.makedirs(OUT)
    for f in ('site.css', 'site.js'):
        shutil.copy(os.path.join(HERE, 'src', f), OUT)
    for fn, *_, mod in PAGES:
        body = importlib.import_module('pages.' + mod).build()
        open(os.path.join(OUT, fn), 'w').write(frame(PAGES, fn, body))
    print('built', OUT, sorted(os.listdir(OUT)))


if __name__ == '__main__':
    main()
