# Unit squares in a rectangle just below integer size: at most AB − 5

Let ν(a, b) be the largest number of non-overlapping unit squares (any positions, any angles) that
fit in an a × b rectangle. This folder contains a computer-assisted proof of the following bound.

## What is claimed

**Theorem 1.** Let A, B ≥ 8 be integers. If a < A and b < B, then ν(a, b) ≤ AB − 5.

In other words, if AB − 4 unit squares fit in an a × b rectangle with a ≤ A and b ≤ B, then a = A or b = B. For A = B = k this is the case k ≥ 8 of the
statement s(k² − 4) = k (proved for k ≥ 5) of Evan Daniel's k2m4 certificate in
[evand/square-packing](https://github.com/evand/square-packing) (`s12/certificates/k2m4/`); the measure
used here is built from that certificate's family (for A = B = 9 it is his box cover, checked exactly).

**Theorem 2 (a weaker bound by a separate route).** Let A, B ≥ 8 be integers and ε > 0. Then
ν(A − ε, B − ε) ≤ AB − 4.

Theorem 2 follows from Theorem 1. We include it because its proof uses a different certificate: the
interval (99/100, 1] of our closed-form lower bound for squares
([`problems/closed-form/`](../closed-form/)), and none of the k2m4 material.

Nothing is claimed about how many squares do fit: we give no packing, and we do not claim that AB − 5 is
attained.

**Status.** Computer-assisted. Theorem 1 is proved in Lean 4 with the standard axioms only
(`propext`, `Classical.choice`, `Quot.sound`): the Lean project [`lean/rectangle-k2m4/`](../../lean/rectangle-k2m4/)
proves it from the finite statement ValidTilt9, and ValidTilt9 is proved in the Lean kernel in release
`validtilt9-lean-v1`; the combined theorem `Rect4.rect4` is in `lean/rectangle-k2m4/final/`. Theorem 2 is not
formalised. Not yet reviewed by anyone outside this project.

## The argument for Theorem 1

**Measure principle.** Suppose n unit squares fit in an a × b rectangle with a < A, b < B. Put
λ = max(a/A, b/B) < 1 and scale the packing by 1/λ about a corner. The rectangle becomes a subset of
[0, A] × [0, B], and each square becomes a square of side 1/λ > 1 with disjoint interiors from the others.
The concentric unit square inside each one is therefore a closed unit square in [0, A] × [0, B], and these
n closed squares are pairwise disjoint. If μ is a non-negative measure on [0, A] × [0, B] with μ(Q) ≥ 1 for
every closed unit square Q in the container, then n ≤ Σ μ(Q_i) ≤ μ([0, A] × [0, B]). This is the same
argument as for squares; the scaling is uniform, so the squares do not rotate.

**The measure μ_{A,B}.** Evan Daniel's family `K4_k008_family.txt` consists of a corner module (segments in
[0, 3]², listed as `H`/`V` lines), a period-1 wall profile (`h`/`v` lines; in wall coordinates (s, d), with s the
position along the wall and d the distance from it, every piece lies in 0 ≤ s − j ≤ 1, 0 ≤ d ≤ 3 for a phase
offset j; in the file d ≤ 14/5 and the vertical pieces have phases s − j ≤ 4/5), and Lebesgue measure from a = 14/5. With R = 3 we place, in [0, A] × [0, B]:

- the corner module at the four corners, by (x, y) ↦ (x, y), (A − x, y), (x, B − y), (A − x, B − y);
- the wall profile on each wall of length L (L = A for the bottom and top walls, L = B for the left and right walls)
  at s = j + p for the integers j ≥ R, keeping a piece only if it ends at s ≤ L − R (so the last period
  contributes only its phase-0 vertical pieces at s = L − R); the wall coordinates are mapped by
  bottom (s, d) ↦ (s, d), right (s, d) ↦ (A − d, s), top (s, d) ↦ (A − s, B − d), left (s, d) ↦ (d, B − s);
- Lebesgue measure of density 1 on [a, A − a] × [a, B − a].

Let μ_9 be the measure of the box cover `K4_k008_box9.txt`. Both checkers verify that μ_{9,9} = μ_9 exactly.
(The second checker places the walls by reflections instead of rotations; this gives the same measure because the
profile is symmetric under s ↦ −s (mod 1), which its comparison with the box file confirms.)

**Lemma R6 (localisation).** Let A, B ≥ 8. For every closed unit square Q ⊆ [0, A] × [0, B] there are integers
s, t with Q + (s, t) ⊆ [0, 9]² and μ_{A,B}(Q) = μ_9(Q + (s, t)).

*Proof.* We first compare μ_{A,B} with μ_{9,B} in the x-direction, B ≥ 8 fixed. Consider three vertical strips.

(i) *Left strip* [0, 5) × [0, B]. The pieces of μ_{A,B} that meet it are the two left corner modules (x ≤ 3), the
left wall (x ≤ 3), the bottom and top walls at positions x ∈ [3, 5), and Lebesgue measure on [a, 5). The right
corner modules and the right wall lie in x ≥ A − 3 ≥ 5, and A − a > 5. On the bottom wall the pieces in x < 5 have
j ∈ {3, 4} and end at x ≤ 5 ≤ A − 3, so the cut-off at L − R removes none of them; on the top wall the pieces have
x = n − p with n = A − j, and the conditions j ≥ 3 and j + p ≤ A − 3 become n ≤ A − 3 (automatic for n ≤ 5) and
x ≥ 3. So the restriction of μ_{A,B} to the left strip does not depend on A ≥ 8.

(ii) *Right strip* (A − 5, A] × [0, B]. By the same count, the pieces that meet it are the right corner modules,
the right wall, the bottom and top walls at positions in (A − 5, A − 3], and Lebesgue measure on (A − 5, A − a]
(the left corner modules, the left wall and the line x = 3 lie in x ≤ 3 ≤ A − 5). A bottom-wall piece that meets
x > A − 5 has j ≥ A − 5 ≥ 3, and a top-wall piece there has x > 3, so the conditions j ≥ 3 and j + p ≤ A − 3 reduce
to conditions measured from x = A. All of these pieces are placed relative to x = A, with integer offsets, so the translation x ↦ x + (9 − A) maps the restriction of μ_{A,B} to this strip
onto the restriction of μ_{9,B} to (4, 9] × [0, B].

(iii) *Middle strip* (3, A − 3) × [0, B]. Here only the bottom and top walls and Lebesgue measure contribute: the
corner modules lie in x ≤ 3 or x ≥ A − 3, the side walls in x ≤ 3 or x ≥ A − 3, and a < 3. A wall piece with
offset j ≤ A − 4 ends at s ≤ j + 1 ≤ A − 3, so no piece meeting the open strip is cut off, and the pieces with
j = A − 3 lie on the line x = A − 3. On the top wall the offsets are A − j, again integers. (Even if the full periods with j ≤ 2 or j ≥ A − 3 were added, they would touch the open strip at most
in endpoints: their horizontal pieces end at x ≤ 3 or start at x ≥ A − 3, and vertical phases are below 1. So the
restriction equals that of the full ℤ-periodic pattern.) Hence the restriction
to the middle strip is a fixed pattern of period 1 in x (independent of A, since A is an integer) plus Lebesgue
measure with density 1 on 14/5 ≤ y ≤ B − 14/5, and an integer translation that keeps a set inside the middle strips
(3, A − 3) and (3, 6) preserves its measure.

Now take x0 on the 1/5-grid with 0 ≤ x0 ≤ A − 2, the window W = [x0, x0 + 2) (closed, [A − 2, A], when
x0 = A − 2), and the shift s = s_A(x0) with s_A(x0) = 0 if x0 ≤ 3, 9 − A if x0 > A − 5, and 4 − ⌈x0⌉ otherwise.
The cases do not overlap because A ≥ 8. If x0 ≤ 3, W ⊆ [0, 5) and s = 0: use (i). If x0 > A − 5, W ⊆ (A − 5, A]
and W + s ⊆ (4, 9]: use (ii). Otherwise 3 < x0 ≤ A − 5, so W ⊆ (3, A − 3), and x0 + s ∈ (3, 4], so
W + s ⊆ (3, 6): use (iii). Note that W + s then avoids both lines x = 3 and x = 6 of the 9-box, which carry corner
mass. In every case the restriction of μ_{A,B} to W × [0, B], translated by s, equals the restriction of μ_{9,B} to
(W + s) × [0, B].

The same argument in the y-direction, applied to μ_{9,B} and μ_{9,9}, gives the shift t = s_B(y0). Combining,
μ_{A,B} restricted to W_x × W_y, translated by (s, t), equals μ_{9,9} = μ_9 restricted to (W_x + s) × (W_y + t).

Finally, each side of the axis-parallel bounding box of Q is at most √2 < 9/5. Let x0 be the left edge u of the box
rounded down to the 1/5-grid, or A − 2 if that is larger. If x0 < A − 2 then u + √2 < x0 + 1/5 + 9/5 = x0 + 2, and
otherwise Q lies in [A − 2, A]; either way the x-extent of Q lies in W_x, and likewise in y. Since Q ⊆ W_x × W_y, its
mass is determined by the restriction of the measure to the window, so μ_{A,B}(Q) = μ_9(Q + (s, t)), and
Q + (s, t) ⊆ [0, 9]². ∎

**Role of the finite checks.** Lemma R6 is proved by the argument above for all A, B ≥ 8. The window checks of
both checkers test it, window by window and with the shift rule above, for finitely many sizes; they confirm the
construction and the implementation. At 9 × 9 every shift is 0, so the shift rule is exercised only by the sizes
with A ≥ 10 or B ≥ 10 (for example 10 × 11, 14 × 14, 17 × 19).

**Valid9.** Every closed unit square in [0, 9]² has μ_9-mass at least 1. This is the finite statement behind
Evan Daniel's proof of s(k² − 4) = k: the axis-parallel case and the symmetry reduction are proved in Lean in
evand/square-packing, and the tilted case is certified by his `qx2_zm` run. It is also checked independently
by our checker for the tilted case, **ValidTilt9**
([`checks/valid7/`](../../checks/valid7/), release `records-tilt9-v1`): 28,350 roots, 0 uncertified,
9,537,343 leaves, `RECORD OK`. ValidTilt9 is also proved in the Lean kernel (release `validtilt9-lean-v1`).

**Total mass.** Each wall of length L carries L − 6 full periods of singular (segment) mass P = 14/5 and one phase-0 line of
segment mass E, so with C the segment mass of one corner module (none of P, C, E includes the Lebesgue part),
μ_{A,B}([0, A] × [0, B]) = 4C + 2(A + B − 12)P + 4E + (A − 28/5)(B − 28/5) = AB − 4D for all A, B ≥ 8
(the second checker verifies the coefficients of this polynomial identity; both checkers sum the measure directly
for each listed size), with D = 214770225571/200000000000 = 1.0738511…, so
4D = 4.2954… > 4 and the total is less than AB − 4. With the measure principle, n < AB − 4, so n ≤ AB − 5.

## The argument for Theorem 2

Write a = k + δ_a and b = m + δ_b with k = A − 1, m = B − 1 (both ≥ 7) and δ_a = δ_b = 1 − ε ∈ (99/100, 1).
It is enough to treat ε < 1/100, because ν does not increase when the container shrinks.

- **Family.** Interval 34, (99/100, 1], of the closed-form lower bound for squares. Its family is certified
  there (both checkers of [`problems/closed-form/`](../closed-form/)); the saving is
  S(δ) = α δ + β on the interval with S(99/100) = 0.84282… and S(1) = 0.85285….
- **Lemma R1 (reduction to the square case).** For k, m ≥ 7 and δ_a, δ_b in the same interval, place the
  family's corners at the four corners (with the corner of the b-side transposed), its wall profile along the
  four walls, and Lebesgue measure in the middle. A closed unit square with centre in one quarter of the
  rectangle only meets parts that also appear, in the same position, in the local model of the square
  case. Hence μ(Q) ≥ 1 for every Q, by the square-case certificate.
- **Lemma R2 (total).** μ([0, a] × [0, b]) = ab − 2S(δ_a) − 2S(δ_b).

**Measure principle.** Suppose n unit squares fit in (A − ε) × (B − ε) with ε < 1/100. Choose λ < 1 so close to 1
that a = (A − ε)/λ < A and b = (B − ε)/λ < B; then δ_a, δ_b ∈ (99/100, 1) and k = A − 1, m = B − 1. Scaling the
packing by 1/λ gives, exactly as for Theorem 1, n pairwise disjoint closed unit squares in [0, a] × [0, b], each of
μ-mass at least 1 by Lemma R1. By Lemma R2,
n ≤ ab − 2S(δ_a) − 2S(δ_b) < ab − 4 · 3/4 < AB − 3, and n is an integer, so n ≤ AB − 4.

## What was checked, and how

Every finite statement used by the two proofs is checked in exact rational arithmetic. The statements specific to
this folder are each checked by two separately written programs: `checker/` and `indep-checker/` (the latter was
written from the statements and the published specifications only, without access to the code in `checker/`).

| Statement | Checks | Result |
|---|---|---|
| Valid9, axis-parallel case and the symmetry reduction | Evan Daniel's Lean proof in evand/square-packing (kernel-checked) | as published there |
| Valid9, tilted case | Evan Daniel's exact `qx2_zm` run; independently our ValidTilt9 run ([`checks/valid7/`](../../checks/valid7/), release `records-tilt9-v1`) | both pass; ours: 28,350 roots, 0 uncertified, `RECORD OK` |
| Theorem 1: μ_{9,9} equals the box cover `K4_k008_box9.txt`; masses non-negative; total AB − 4D < AB − 4; the window agreement of Lemma R6 with the shift rule, for every window of the listed sizes | `checker/k2m4_rect_check.py` (14 sizes from 8 × 8 to 15 × 8 and 14 × 14); `indep-checker/rect_k2m4_indep.py` (17 sizes up to 20 × 8 and 17 × 19, and the total as a polynomial identity in A, B) | 0 mismatched windows in both; 38,342 window pairs in the second |
| Theorem 1 (all of it) | Lean 4: [`lean/rectangle-k2m4/`](../../lean/rectangle-k2m4/) (the rectangle measure, Lemma R6, the total for all A, B, the measure principle; extends Evan Daniel's square proof, whose files are reused unchanged) together with the kernel proof of ValidTilt9 (release `validtilt9-lean-v1`) | `Rect4.rect4`, no hypotheses, standard axioms only |
| Theorem 2: interval 34 of the closed form | [`problems/closed-form/`](../closed-form/): the Rust replay and the independent checker `cfcheck` | as published there |
| Theorem 2: Lemmas R1 and R2 for interval 34, at δ_a, δ_b ∈ {99/100, 1} and k, m ∈ {(7,7), (7,9), (9,7), (8,11), (12,7), (7,13), (8,8), (10,14)}; S > 3/4 at both ends | `checker/validate_rect.py` (uses `../closed-form/structure/validate_family.py`); `indep-checker/rect_r1r2_indep.py` (its own reading of the family from `SPEC.md`) | all pass in both (132 and 313 checks); both give the same exact S(99/100) and S(1) |

The outputs are in `receipts/`. For Theorem 1 the finite window checks test Lemma R6 for the listed sizes; the
statement for all A, B ≥ 8 is the proof of Lemma R6 above. For Theorem 2 the checks at δ ∈ {99/100, 1} and the
listed (k, m) extend to the whole interval and all k, m ≥ 7 because positions and masses are affine in δ with a
fixed structure and, for larger k or m, only the number of wall periods changes (as in `../closed-form/SPEC.md`
§2.3); both checkers explain this in their comments.

## Files

- `checker/k2m4_rect_check.py`, `checker/validate_rect.py`: the first checkers.
- `indep-checker/rect_k2m4_indep.py`, `indep-checker/rect_r1r2_indep.py`: the independent checkers, with a README.
- `fetch_inputs.sh`, `inputs.sha256`: download the inputs into `inputs/` and check their sha256.
- `run_checks.sh`: run all four checks and write `receipts/`.
- `receipts/`: the outputs of a full run.

## Inputs

No release is needed for this folder; the inputs are fetched from their published places.

- `K4_k008_family.txt` and `K4_k008_box9.txt` from evand/square-packing at commit `2eb15455`
  (`s12/certificates/k2m4/`, MIT licence), sha256 `a66668d9d414ad1cf78b19826ce592c540c9033a0234a06b207eb776b3e8ff0f`
  and `4151d7c4059d5dcf56130c9373e6b5b60635e1a4250f46562d7ecc4d64a27801`.
- `family.json` (sha256 `cb43f468985a35164ccdf5d449f7d5fb345978c1d645c4755a89a1a1bc31cc02`) and `family_right.json`
  of interval 34, from the asset `interval_0.99_1.tar.gz` of release `closed-form-v1`.

## How to check

Python 3 (standard library only), git, curl and sha256sum. From `problems/rectangle-upper-bounds`:

    ./fetch_inputs.sh
    ./run_checks.sh

The run takes about five minutes on a laptop, almost all of it in `checker/k2m4_rect_check.py`; it ends with
`K2M4_RECT OK`, `VALIDATE_RECT OK`, `PASS ALL CHECKS` and `SUMMARY: 313/313 checks passed; 0 failed`.

## Relation to earlier work

Here ν(a, b) counts squares in an a × b rectangle itself. Nagamochi and Karakuş count squares in a
rectangle with both sides strictly smaller than a and b, so for integer A, B their bounds are bounds on
ν(A − ε, B − ε′), the quantity in Theorems 1 and 2.

- **Nagamochi** (H. Nagamochi, Packing unit squares in a rectangle, Electron. J. Combin. 12 (2005) #R37),
  Theorem 1 states that this number is less than ab − (a + 1 − ⌈a⌉) − (b + 1 − ⌈b⌉) for real a, b ≥ 2.
  For integer sides that is at most AB − 3. Its proof rests on the scoring assertion of his Lemma 1, for
  which counterexamples have since been given (Karakuş, below; independently by chelokot). The bound is
  therefore stated but its published proof is incomplete. Our Theorems 1 and 2 do not use that lemma.
- **Karakuş** (H. Karakuş, A counterexample to Nagamochi's scoring lemma and a new rectangle packing bound,
  arXiv:2609.37410, 2026) proves the bound ab − max(Δ(a), Δ(b)) with Δ(t) = t + 1 − ⌈t⌉ (a, b ≥ 3), which
  for integer sides gives at most AB − 2.
- **Evan Daniel** (evand/square-packing, `s12/certificates/k2m4/`, commit `2eb15455`) proves
  s(k² − 4) = k for all k ≥ 5 in square containers; for k ≥ 8 the proof uses the family and the finite
  statement Valid9 that we reuse. Theorem 1 with A = B is that statement for k ≥ 8 and is not new. The square
  cases of Theorem 2 (s(k² − 3) = k) were also known: Kearney–Shiu and Bentz for small k, Evan Daniel for all k ≥ 5.
  Rectangles appear in his notes only as open questions (the one-side-shrunk value c*(a, b), and
  fixed-height rectangles).
- We found no earlier statement of AB − 4 or AB − 5 for rectangles with A ≠ B in the literature we checked
  (the papers above; Roth–Vaughan; Erdős–Graham; Chung–Graham; Stromquist; Kearney–Shiu; Bentz; Friedman's
  survey; Arslanov–Mustafin–Shangitbayev 2021), in evand/square-packing, or in the register of
  [jlevy/squares](https://github.com/jlevy/squares). We do not claim that no such statement exists.

## Credits

The measure family, the box cover and the proof of Valid9 are Evan Daniel's (evand/square-packing, MIT
licence). The rectangle construction, Lemma R6, Lemmas R1 and R2, the checks in this folder and the
independent ValidTilt9 run are by Hiroaki Hosono (wand125). The bounds of Nagamochi and Karakuş and the
square cases are credited above.

## Licence

MIT (see `LICENSE`).
