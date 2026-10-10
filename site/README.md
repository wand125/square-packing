# site

Source of the GitHub Pages site. `python3 site/build.py` writes `site/_site/` (no dependencies beyond the
Python standard library).

- The Results page is generated from `INDEX.json`, `problems/right-isosceles/README.md` and
  `problems/n17/manifest.json`.
- The Methods, Themes, Verify and Credits pages are generated from `site/content/*.json`; each entry carries
  the path or URL it was condensed from.
- Pages are in English with a Japanese version selected by the language switch; dark theme by default.
- `.github/workflows/pages.yml` builds and deploys the site on pushes to `main`.
