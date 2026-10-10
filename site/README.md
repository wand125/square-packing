# site

Source of the GitHub Pages site. `python3 site/build.py` writes `site/_site/` (no dependencies beyond the
Python standard library).

- The Results page is generated from `INDEX.json`, `problems/right-isosceles/README.md` and
  `problems/n17/manifest.json`.
- The Methods, Themes, Verify and Credits pages are generated from `docs/data/*.json`; each entry carries
  the path or URL it was condensed from.
- Pages are in English with a Japanese version selected by the language switch; dark theme by default.
- `build.py` lists the pages; each page is one module in `pages/`, and shared helpers and the page frame are in `lib.py`.
  Styles and scripts are in `src/`.
- `.github/workflows/pages.yml` builds and deploys the site on pushes to `main`.

Editorial data and source ownership are documented in [docs/README.md](../docs/README.md).
