# Second checker: unit squares in an equilateral triangle (n = 2, 3, 4)

An independent re-check of the certificates behind

- s△(2) = 2 + 2/√3
- s△(3) = 3/2 + √3
- s△(4) = 3 + 2/√3

## What is checked

For a certificate (side `L`, points `p_i` with rational weights `w_i`), `sweep.py` proves:

> every closed unit square Q ⊆ T_L = conv{(0,0), (L,0), (L/2, L√3/2)}, at any position and
> any angle, contains points of total weight ≥ 1 (points on ∂Q count).

The lower bound then follows from the total weight being below `n`, together with the
centre-scaling argument (the certificates' PROOF.md; not re-checked by code). The squares are
translated away from the common centroid by the factor v/L. This makes them pairwise disjoint
closed squares in T_v, and each point is counted at most once.

## Method: an exact angular sweep of a line arrangement

This method is deliberately different from the first checker. It uses no box subdivision, no
Bernstein bounds, no D3 symmetry reduction and no pair lemma: every angle in u ∈ [0, 1] is
checked directly.

1. **Poses.** Q(c, t) = c + R_t[−½, ½]² with u = tan(t/2) ∈ [0, 1]. The square has period
   π/2, so this covers every angle. cos t = (1−u²)/D and sin t = 2u/D, with D = 1+u².
2. **Lines.** For fixed u:
   - "Q ⊆ T_L" is 12 half-planes in the centre c (3 sides × 4 square vertices);
   - "p_i ∈ Q" is 4 half-planes.

   After multiplying by D > 0, each half-plane is A(u)x + B(u)y ≤ C(u), with polynomials of
   degree ≤ 2 over Q(√3).
3. **One angle, exactly.** For fixed u the captured weight is constant on each open cell of the
   arrangement of all these lines. Every open cell inside the admissible region D_u is bounded,
   so it has a vertex, and near that vertex it is one of the open sectors cut out by the lines
   through it. So the minimum over the open cells in int D_u equals the minimum, over
   arrangement vertices v ∈ D_u and over sectors at v inside D_u, of the sector's weight.
   - At a rational u everything lies in Q(√3), and every sign is decided exactly.
   - A sector's membership is decided by the exact slack signs at v and, for the two lines
     through v, by the sign of normal · direction.
   - Floats only order the admissibility tests.
4. **Where the arrangement can change.** Its combinatorial type is constant on every open
   u-interval that avoids the real roots of these polynomials:
   - the 3×3 determinants of line triples (concurrency);
   - the 2×2 normal determinants of line pairs (parallelism);
   - for pairs that are always parallel, the coincidence minors.

   Between such roots, all slack signs at every vertex and all sector signs are non-zero and
   continuous, so they are constant. Each polynomial is multiplied by its Q(√3)-conjugate to get
   rational coefficients, whose roots include the original ones. Its real roots in [0, 1] are
   isolated exactly (sympy `intervals`, then refined with exact rational arithmetic so that the
   isolating intervals are disjoint and bracket their roots). One rational sample is taken in
   every open gap.
5. **Closure (upper semicontinuity).** The set {(u, c, p) : p ∈ Q(c, t(u))} is closed. So the
   captured weight is upper semicontinuous in (u, c): at a limit pose it is ≥ the lim sup of the
   values at nearby poses. Also:
   - D_u is convex and varies continuously with u;
   - D_u contains a disc around the centroid for every u, because the inradius L/(2√3) exceeds
     √2/2.

   Hence every admissible pose is a limit of poses in open cells at non-critical u. The bound
   ≥ 1 therefore extends to all admissible poses, including the critical angles, u = 0, 1, and
   every margin-zero contact. No special treatment of margin-zero contacts or of switching
   families (the n = 4 middle square) is needed.
6. **Failure is explicit.** When the minimum is below 1, the checker turns the offending
   (vertex, sector) into a concrete pose c = v + ε·d at that rational angle. It halves ε until
   the pose is exactly admissible, and reports the pose with its exactly counted captured weight.

`probe.py` is a separate, direct exact evaluator of random admissible poses. It can only find
counterexamples. It also checks the D3 invariance of the point set (reported only; the sweep
does not use symmetry).

## Results

All runs are on one machine (8 processes), on the certificate files in `certificates/`. The
sweep ignores the `symmetry` field and checks every angle. `controls/n2_centroid_none.json`
(the same point, `symmetry: none`) gives the identical result.

| certificate | sha256 | lines | critical roots | samples | vertices | sectors in D | min weight | time | verdict |
|---|---|---|---|---|---|---|---|---|---|
| n = 2, `certificates/n2/n2_cert.json` (centroid, weight 1) | `de9325eb…` | 16 | 157 | 156 | 15,600 | 468 | 1 | 7 s | verified |
| n = 3, `certificates/n3/n3_cert.json` (7 × 1/3) | `ae794baa…` | 40 | 1,447 | 1,446 | 838,680 | 94,674 | 1 | 58 s | verified |
| n = 4, `certificates/n4/n4_cert.json` (3 × 1) | `a0483cf4…` | 24 | 523 | 522 | 119,016 | 35,718 | 1 | 12 s | verified |

Total weights: 1 < 2, 7/3 < 3, 3 < 4.

### Exact random probe (`probe.py`, seed 1)

| certificate | admissible poses | min captured weight | D3 invariant |
|---|---|---|---|
| n = 2 centroid | 20,000 | 1 | yes |
| `n3_cert.json` | 20,000 | 1 | yes |
| `n4_cert.json` | 20,000 | 1 | yes |

(The probe rejects most draws as inadmissible, 2.9–4.5 million draws per run; it is slow but
only a sanity check.)

### Negative controls (each must fail, and each fails with an explicit, exactly checked pose)

| input | min weight | witness |
|---|---|---|
| n = 2, L + 1/100 (centroid moved accordingly), `controls/neg_n2_Lplus.json` | 0 | u = 1/1365, weight 0 |
| n = 2, point shifted by 1/50 in x, `controls/neg_n2_shift.json` | 0 | u = 1/367, weight 0 |
| n = 2, weight 99/100 | 99/100 | (test suite) |
| n = 3, L + 1/100 (the first checker's control), `controls/neg_n3_Lplus.json` | 1/3 | u = 1/3673, weight 1/3 |
| n = 3, first point shifted by 1/50 in x, `controls/neg_n3_shift.json` | 2/3 | u = 1/245, weight 2/3 |
| n = 3, centroid removed, `controls/neg_n3_drop_centroid.json` | 2/3 | u = 3/59, weight 2/3 |
| n = 4, L + 1/100 (the first checker's control), `controls/neg_n4_Lplus.json` | 0 | u = 1/1431, weight 0 |
| n = 4, first point shifted by 1/50 in x, `controls/neg_n4_shift.json` | 0 | u = 1/385, weight 0 |
| n = 4, one weight 99/100, `controls/neg_n4_weight.json` | 99/100 | u = 1/499, weight 99/100 |

### Comparison with the first checker

- **Verdicts.** Both checkers agree on all three certificates (verified) and on the two
  `L + 1/100` controls (not verified).
- **Counts are not comparable.** The first checker reports D3-reduced box counts:
  - n = 3: 386 nodes, depth 30;
  - n = 4: 478 nodes with the pair lemma;
  - `L + 1/100` controls: 1,177 and 63 uncertified boxes.

  This checker reports critical angles and arrangement sectors over the full angle range, without
  symmetry.
- **Pair lemma.** This checker needs no pair lemma for n = 4. The captured weight is counted
  exactly on every cell, so the family in which a pose captures one of two points at unit
  distance, and which one switches, is covered directly.

## Run

From this directory (`checker2/`):

```sh
uv venv .venv && uv pip install --python .venv/bin/python sympy gmpy2 pytest
for n in 2 3 4; do
  .venv/bin/python sweep.py ../certificates/n$n/n${n}_cert.json --n $n --jobs 8 --out n$n.json
done
.venv/bin/python probe.py ../certificates/n3/n3_cert.json --poses 20000
for f in controls/neg_*.json; do .venv/bin/python sweep.py $f --jobs 8; done   # each must fail
.venv/bin/python -m pytest -q tests
```

`runs/` holds the summaries of the recorded runs (`n2.json`, `n3.json`, `n4.json`, `probe.jsonl`).
A failing run prints its counterexample pose in the summary.

## Independence

- Written from the first checker's specification (its `SPEC.md`, including the Extensions), the
  proof notes (`PROOF.md`) and the certificate format only; none of its code was opened.
- Before a correction arrived, the author of this checker had also read the first checker's
  `README.md`. That file summarises the first checker's box and Bernstein method. This checker
  uses a different method (step 4 above) and nothing from that summary.
- Shared inputs: the certificates, the claim, and the centre-scaling argument.
- Tools: Python, gmpy2 (exact rationals), sympy (real-root isolation of rational polynomials).

## The series n = 7, 11, 16, 22, 29, 37 (lattice certificates, side m + 2/√3)

`series_results.json` holds, for `lattice_m4.json` … `lattice_m9.json`:

- the certificate sha256 (identical to the certificate files published here);
- the minimum captured weight;
- the numbers of critical angles and samples;
- the time and the verdict.

The runs used `sweep.py` in this directory. It is the same sweep, plus `--stop-early`, an option
that stops at the first sample of weight < 1; no run stopped early. As before, the sweep uses no
symmetry and no chord-pair lemma, and checks every angle directly.

| m | n | points | critical angles | min weight | time | verdict |
|---|---|---|---|---|---|---|
| 4 | 7 | 6 | 1,231 | 1 | 3 min (6 processes) | verified |
| 5 | 11 | 10 | 2,311 | 1 | 7 min (6 processes) | verified |
| 6 | 16 | 15 | 3,853 | 1 | 3 min (12 processes) | verified |
| 7 | 22 | 21 | 5,959 | 1 | 11 min (12 processes) | verified |
| 8 | 29 | 28 | 8,767 | 1 | 30 min (12 processes) | verified |
| 9 | 37 | 36 | 12,157 | 1 | 92 min (12 processes) | verified |

Each total weight is `n − 1 < n`.

For m = 9 the result is a lower bound only: s△(37) ≥ 9 + 2/√3 ≈ 10.15470. The rows packing
holds 36 squares at this side.

### A floating-point cross-check for m = 9

This check is not a proof. `area_check.py` divides θ ∈ [0°, 90°] into 9,000 steps. At each
angle it subtracts the union of the 36 capture squares from the region of admissible centres,
and reports the largest remaining area.

The result is 1.85 × 10⁻¹⁵, at θ = 30°, where the certificate has a margin-zero contact
(`area_check_m9.json`). No unit square avoiding all 36 points was found.
