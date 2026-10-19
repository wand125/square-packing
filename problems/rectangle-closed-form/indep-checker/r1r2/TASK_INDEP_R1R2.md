# Task: an independent checker for Lemmas R1 and R2 on all 34 interval families (second system)

Context. The rectangle version of the closed-form bound (bundle `problems/rectangle-closed-form/`, statements in
its `SPEC.md` §1–§3) places the closed-form family of one interval J in the four corners and along the four walls
of the container [0, a] × [0, b], a = k + δ_a, b = m + δ_b, with δ_a, δ_b ∈ J and k, m ≥ 7. Lemmas R1
(localisation) and R2 (total mass) are checked for each of the 34 interval families by the first checker. The
seams have already been checked independently; this task adds an independent check of R1 and R2 for all 34
families. It is short (exact rational arithmetic on 34 small JSON files; a laptop is enough).

Written from the specifications only. Do not read the first-system code: `checker/validate_rect.py` of the bundle
and `problems/closed-form/structure/validate_family.py` (and its callers). You may read and reuse the published
independent checker `problems/rectangle-upper-bounds/indep-checker/rect_r1r2_indep.py`, which does this for
interval 34 only and is hard-wired to it (interval bounds, `family_right.json`, paths); generalising it to every
interval is allowed and is probably the shortest route. Say in your README which code you reused.

## Inputs (read only; paths shortened to repository and release paths for publication)

- The 34 published families: `families/<asset>/family.json`, one per
  interval, `<asset>` = the `asset` field of `intervals.json` without `.tar.gz` (for example
  `interval_0_0.02`). `families.SHA256SUMS` lists their SHA-256; they equal the `family_sha256` of
  `intervals.json`.
- The interval list: `problems/closed-form/intervals.json` (34 entries: `index`, `d0`, `d1`,
  `open_left`, `closed_right`, `asset`, `family_sha256`, `certified_line` {alpha, beta}).
- The family format and the square construction: `problems/closed-form/SPEC.md` (§1.3 the
  saving S(δ) = 99/25 + (9/5)δ − M_C(δ) − m_v, §2.1 the square construction, §3 the family JSON: d0, d1, UA = 9/5, F, T, V, U; corner pieces,
  one wall period T on 3 ≤ x < 4 owning its phase-0 line and not its phase-1 line, terminal line V).
- The rectangle statements: `problems/rectangle-closed-form/SPEC.md` §1–§3 (layout table, R1, R2).

## The construction to check

σ(x, y) = (a − x, b − y), τ(x, y) = (a − y, x), α = 9/5.
- SW: the corner of the family at δ_a; the bottom wall: the profile period at x = 2 + δ_a + n for n = 0, …, k − 5;
  its terminal line at x = a − 2.
- SE: the same in local coordinates with δ_b and m, mapped by τ (the local bottom wall becomes the right wall).
- NE, NW: the σ-images of SW and SE.
- Lebesgue measure of density 1 on [α, a − α] × [α, b − α].

## Checks, for each of the 34 families

For every (δ_a, δ_b) ∈ {d0, d1}² and the pairs (k, m) ∈ {(7,7), (7,9), (9,7), (8,11), (12,7), (7,13), (8,8), (10,14)}:
1. **R2.** All densities ≥ 0, the support lies in the container, the measure is invariant under σ, and the total
   mass is exactly ab − 2S(δ_a) − 2S(δ_b), with S computed from the family (§1.3 of the closed-form SPEC).
2. **R1 (localisation).** With margin r = 3/4 (> √2/2): on the quarter box [0, a/2 + 3/4] × [0, b/2 + 3/4] the
   global measure equals the local model of SW at δ_a (the corner with both walls continued periodically and the
   Lebesgue part); on the box [0, b/2 + 3/4] × [0, a/2 + 3/4] in the local coordinates of SE (pull back by τ), the
   global measure equals the local model at δ_b. The other two quarters follow by σ.
3. **Walls.** The inner periods of the bottom and right walls equal the profile after integer shifts; the terminal
   lines have phase 0.
4. **Square case.** For k = m and δ_a = δ_b, the measure equals the square construction of the closed-form SPEC.
5. **Saving.** S(d0) and S(d1) are at least the certified line α_J d + β_J of `intervals.json` at the same point.

State in the README, as `rect_r1r2_indep.py` does, why finitely many (δ, k, m) suffice (affine positions and masses
in δ with a fixed structure; larger k or m only add wall periods; both parities of k and m occur).

## Output

A script (one file is fine) that takes the family folder and `intervals.json`, prints PASS/FAIL per check, and ends
with a summary line and a non-zero exit code on any failure; a per-interval report (JSON or text); negative
controls (for example: a perturbed mass in F, a wall period shifted by 1/100, a wrong d1), each of which must fail.
Record the machine generically ("a laptop"), the time and the results as run. English only; no private paths in the
outputs (print paths relative to the family folder). Put everything in a new folder and tell the coordinator where.
