# Unit 4-cubes in a 4-cube, k = 17–29: exact certificates for the best known packings (v2)

Let s_4(k) be the side of the smallest 4-cube that contains k unit 4-cubes with pairwise disjoint interiors (any
positions, any orientations). This bundle gives, for k = 17–29, an exact certificate of a packing in a quadratic field: the side is exactly
2 + 1/√3 (k = 17), 2 + 1/√2 (k = 18–25) or 2 + 2√2/3 (k = 26–29). **Version 2 (this version) improves the best known
side for k = 27, 28 and 29**: the published packings for k = 26–29 (hockyy/tesseract-packing) have sides 2.942809042,
2.942809214, 2.942826011 and 2.942830937; with the frames of the cubes fixed to signed permutations composed with
45° turns and the centres re-solved by a linear programme, all four fit in the side 2 + 2√2/3 = 2.9428090416
exactly, which is below the published side by 1.7·10⁻⁷ (k = 27), 1.7·10⁻⁵ (k = 28) and 2.2·10⁻⁵ (k = 29), and
confirms the conjectured closed form for k = 26. Version 1 of this bundle (Release `cubes-n-dim-n4-certs-v1`) had
rational certificates at the published values for k = 26–29. The record for k = 30 (side 2.9876881, improving
2.9895684) is published separately in the Release `cubes-n-dim-n4k30-v1`. The accompanying survey page shows the
packings in projection.

| k | best known s | published by | packing in this bundle | certified s |
|---|---|---|---|---|
| 17 | 2.577350 ≈ 2 + 1/√3 | xavierdmello/tesseract-packing | our search: the 16-grid opened up plus one cube tilted in all four coordinates | 2 + (1/3)√3 = 2 + 1/√3 exactly |
| 18–24 | 2.707107 = 2 + 1/√2 | xavierdmello/tesseract-packing (product of two 5-square packings) | nested subsets of our k = 25 packing: the 16 axis-parallel cubes kept, the doubly rotated centre cube removed first, then singly rotated cubes one at a time | 2 + (1/2)√2 exactly |
| 25 | 2.707107 = 2 + 1/√2 | xavierdmello/tesseract-packing (product of two 5-square packings) | our construction: the product of two 5-square packings of side 2 + 1/√2, tightened | 2 + (1/2)√2 exactly |
| 26 | 2.942809042 ≈ 2 + 2√2/3 | hockyy/tesseract-packing | published coordinates (a), frames fixed to 45° turns, centres re-solved by LP | 2 + (2/3)√2 exactly |
| 27 | 2.942809214 | hockyy/tesseract-packing | subset of our k = 28 packing (one cube removed) | 2 + (2/3)√2 exactly (**new**, −1.7·10⁻⁷) |
| 28 | 2.942826011 | hockyy/tesseract-packing | published coordinates (a), frames fixed to 45° turns, centres re-solved by LP | 2 + (2/3)√2 exactly (**new**, −1.7·10⁻⁵) |
| 29 | 2.942830937 | hockyy/tesseract-packing (coordinates: xavierdmello) | published coordinates (b), frames fixed to 45° turns, centres re-solved by LP | 2 + (2/3)√2 exactly (**new**, −2.2·10⁻⁵) |

Sources: xavierdmello/tesseract-packing (https://github.com/xavierdmello/tesseract-packing, branch research, commit
fb230875c852da2199e3036ad6b09633d6eacb7b) and hockyy/tesseract-packing (https://github.com/hockyy/tesseract-packing,
branch main, commit e75c790976a051b973341e21eedeaa8c2f66fae8). Both repositories check their packings in floating
point and publish no exact certificates; neither carries a licence file. (a) hockyy `results/n26_side_2.942809042.json`,
`n27_side_2.942809214.json`, `n28_side_2.942826011.json`; the same coordinates are in xavierdmello `results/best/d4_n26.json`
etc. (b) xavierdmello `results/best/d4_n29.json` (2.9428309369), which refines hockyy's 2.942833710. For k = 26–29 the
published coordinates were the starting point: the discovery of the arrangement (the opened 25-cube product frame with
cubes in "cross cells") belongs to its authors; replacing every frame by the nearest signed permutation composed with
45° turns in one or two coordinate planes, re-solving the centres by a linear programme (the separation conditions are
linear in the centres once the frames are fixed), reading the optimal vertex off exactly in Q(√2) and certifying it is
our work. The published packings carry small tilts of the frames (up to about 13°); the exact packings show that the
tilts are not needed. For k = 17 the packing was found by
our own search and reaches the published value exactly; for k = 18–25 the packings are our own construction.

## Two certificate formats

**Rational (none in this version; kept in the specification for the first checker).** `{"n", "k", "s", "A", "c", "bits", "delta", "s_float", "note"}`
with rationals as strings `"p/q"`. Cube i has centre `c[i]` and frame R_i = (I − A_i)⁻¹(I + A_i), the Cayley transform of
the skew-symmetric matrix `A[i]` (an optional `P[i]`, a rational orthogonal matrix, multiplies on the right); its point
set is c_i + R_i [−½, ½]⁴, the container is [0, s]⁴. Accepted iff every `A[i]` is skew-symmetric, every cube is inside
the container (c_i[r] ± ½ Σ_m |R_i[r][m]| ∈ [0, s]), and every pair i < j is separated by one of the C(8, 3) = 56
candidate axes a (generalised cross products of k′ columns of R_i and 3 − k′ columns of R_j): 2 |a · (c_i − c_j)| ≥
Σ_m |a · R_i[:, m]| + Σ_m |a · R_j[:, m]|. The fields `bits`, `delta`, `s_float`, `note` are informational.

**Quadratic field (`n4k17.json`–`n4k29.json`, format `alg-v1`).** Numbers are pairs `["a", "b"]` meaning a + b√d with
d = 3 for k = 17 and d = 2 for k = 18–29; frames are given directly as `R` and must be exactly orthogonal; the container, separation and sign rules are in
`SPEC-ALG.md`. The side is `["2", "1/3"]` = 2 + √3/3 = 2 + 1/√3 exactly for k = 17, `["2", "1/2"]` = 2 + √2/2 = 2 + 1/√2 exactly for k = 18–25,
and `["2", "2/3"]` = 2 + 2√2/3 exactly for k = 26–29.

Both formats certify s_4(k) ≤ s with s exactly the number in the file; condition 3 is the separating-axis theorem for
two convex polytopes, and all arithmetic is exact.

## Checkers

| Path | What |
|---|---|
| `check_cert.py` | first system, rational format (no rational certificate in this version; kept for version 1) |
| `check_alg.py` | first system, quadratic-field format: `python3 -I check_alg.py certs/n4k17.json … certs/n4k29.json` |
| `check2/` | second system (both formats), written independently from the specifications alone; see `check2/README.md` for its corruption and hand-made tests |

Every certificate is accepted by both systems; each check takes about a second.

## Files

`certs/n4k{17..29}.json`, `check_cert.py`, `check_alg.py`, `check2/`, `SPEC-ALG.md`, `SHA256SUMS`.

Certificates, checkers and survey: Hiroaki Hosono (wand125), 2026. Packings for k = 26–29: Hiroaki Hosono (wand125),
starting from the published packings of hockyy/tesseract-packing and xavierdmello/tesseract-packing (commits above).
