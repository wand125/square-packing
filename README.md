# square-packing

Computer-assisted results on packing unit squares: exact certificates, independent checkers, Lean
formalizations and the tools that produced them. Everything here was previously spread over ten repositories;
they are archived, except n11-optimality-lean, which stays active until its current work is merged; each points
here (see "Moved from" below).

`INDEX.json` is the machine-readable index: every certificate with its claim, release asset, SHA-256 and check
command, and every checker, tool and Lean project.

## Layout

| Folder | Contents |
|---|---|
| `problems/square-lower-bounds/` | Lower bounds for s(n), n unit squares in the smallest square: point, rectangle-density and mixed certificates (n = 18 to 101) |
| `problems/n17/` | Sub-pattern branch-and-bound certificates for n = 17 (for jlevy/squares): receipts, SHA-256, node counts and provenance; the data are available on request |
| `problems/triangle/` | Unit squares in an equilateral triangle |
| `problems/right-isosceles/` | Unit squares in a right isosceles triangle: optimality for n = 2, 3, 4, 6, 10 |
| `problems/domino/` | Unit squares in a 1:2 rectangle |
| `problems/hexagon/` | Unit squares in a regular hexagon |
| `checks/valid7/` | An independent exact check of Valid7 (evand/square-packing) |
| `tools/` | Solvers, verifiers and transfer tools (each tool folder has its own CI) |
| `lean/n11-optimality/` | Lean 4 formalization toward s(11) |
| `lean/triangle/` | Lean 4 proofs for the triangle results |

## Certificates: documents in git, data in releases

Every certificate folder is readable without downloading anything: its README, PROOF, SPEC and FORMAT
documents, its checker code, its small metadata and check records, and an `ASSET.json` are in git. Only the
certificate data (weights, covers, trees, bundles) is in a release.

```json
{"id": "domino-v1:certificates/n4",
 "claim": "s(4) = v4, where v4 ≈ 1.93028330671426938847 is the largest real root of 5x³ + 8x² − 32x − 4.",
 "release_tag": "domino-v1",
 "assets": [{"asset": "certificates__n4.tar.gz", "size": 1630, "sha256": "eba36dac…"}],
 "unpack": "tar xzf certificates__n4.tar.gz -C problems/domino",
 "check": "python checker/check.py certificates/n4/n4_cert.json --n 4 --max-depth 30 --jobs 4 ...",
 "check_cwd": "problems/domino",
 "documents": ["problems/domino/certificates/n4/PROOF.md"]}
```

To check a certificate: download its asset(s) from the release named in `release_tag`, compare the SHA-256 (each
release also has `SHA256SUMS`), run `unpack` from the repository root (it puts the data files back next to the
documents, restoring the original layout), then run `check` in `check_cwd`. Assets larger than 1.9 GiB are
split into `.partNNN` files; `unpack` joins them. `INDEX.json` lists every certificate with its claim and
check command.

## Moved from

| Old repository | New place |
|---|---|
| wand125/square-packing-bounds | `problems/square-lower-bounds/` (certificates in release `square-lower-bounds-v1`) |
| wand125/square-packing-tools | `tools/` |
| wand125/n17-certificates | `problems/n17/b2-classes-20261005/` |
| wand125/n17-bb-verifier | `tools/n17_bb_verifier/` (a later version of the same verifier) |
| wand125/squares-in-triangle | `problems/triangle/`, `lean/triangle/` |
| wand125/squares-in-domino | `problems/domino/` |
| wand125/squares-in-hexagon | `problems/hexagon/` |
| wand125/valid7-independent-check | `checks/valid7/` |
| wand125/n11-optimality-lean | `lean/n11-optimality/` |
| wand125/square-packing-density-bounds | `problems/square-lower-bounds/history/density-bounds/` |

Each old repository keeps its full history and releases and has a `MOVED.json` mapping every old path to its new
path or release asset (with SHA-256); all except n11-optimality-lean are archived (read-only). Links to old
commits, files and release downloads keep working.

The n = 17 certificate data are not in a release. `problems/n17/manifest.json` records, for each class, the
claim, node count, SHA-256, verifier receipts and the tools that made it: certificate data are available on
request; they can be regenerated deterministically with the recorded tools and inputs and checked against the
SHA-256 listed there. The two classes already published (C1, C2) stay in the original release of
wand125/n17-certificates.

## Licenses

Each folder carries the license of its origin (`LICENSE`, and `UPSTREAM-LICENSE.txt` or
`THIRD_PARTY_NOTICES.md` where code from other authors is included). See `LICENSE.md`.

## Credits

Hiroaki Hosono (GitHub: wand125). Code and formats from other authors are credited in the folders that use them,
in particular Evan Daniel (evand/square-packing), tokoharu, and jlevy/squares.
