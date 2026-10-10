# Research documentation data

The bilingual editorial summaries used by the site are maintained in [data/](data/).
Edit these JSON files once; the site reads them directly. Do not maintain a second
handwritten copy of the same summaries in the rendering code or generated HTML.

| File | Content |
|---|---|
| [methods.json](data/methods.json) | Methods, applications, attribution, review qualifications and result-specific explanatory notes |
| [themes.json](data/themes.json) | Published tracking themes, completed stages and source links |
| [verify.json](data/verify.json) | Checking instructions, requirements, tools and releases |
| [about.json](data/about.json) | Credits, related projects, repository moves and licenses |

## Source documents

[INDEX.json](../INDEX.json), the per-certificate ASSET.json files, README/PROOF documents
under [problems/](../problems/), and existing Releases retain their original locations
and roles. These summaries do not replace the certificate claims or verification records.
Follow each entry's source references for the full argument and its qualifications.

The Results table is built from INDEX.json, the right-isosceles README and the published
entries of the n17 manifest. In methods.json, `result_notes` is keyed by the original
result ID; its source-backed consequences supplement the recorded claim without changing
it. A method's `review_status` is shared by its method summary and result notes.
Text pairs use `en` and `ja`; source paths are relative to the repository root, or URLs.

## Build

Run `python3 site/build.py` from the repository root (Python 3.12 or newer). This writes
five static pages and their assets to `site/_site/`. Rendering code and styling remain
in [site/](../site/). Generated files are not another editorial source.
