# Six unit squares in an equilateral triangle

**Theorem (computer-assisted).** The smallest equilateral triangle containing six non-overlapping unit
squares has side v = 2 + 4/√3 ≈ 4.3094.

The packing (Friedman's table) is a pinwheel of three pairs of side-by-side squares, one pair on each side,
with C3 symmetry; its exact coordinates are in `n6_packing.json`. The lower bound needs more than one point
certificate: it is a localization tree of six certificates closed by a local lemma for three squares.

Verification:

- **First system.** The six certificates by the exact checker `../../checker/check.py` (records in
  `check_record.json`); the triple lemma, its hypotheses and the obstacle points by interval arithmetic
  (`triple/`, `stage2/`).
- **Second system.** Every part again, by a checker written from the specification
  (`../../checker/SPEC.md`, section "Exclusion boxes and obstacle points") and this outline, without reading
  the first checker or the witness generators: `../../checker2/n6/` (README.md, RESULTS.md). Negative controls
  (L + 1/100, dropped points, removed exclusions or wall points, chain condition dropped, δ = 0.15) all fail as
  expected.

Paths below are relative to this folder. The data files come from the release asset (see `ASSET.json`).

## Statement

v = 2 + 4/√3, and T_L is the equilateral triangle of side L. No 6 unit squares with pairwise disjoint interiors
fit in T_L for L < v. The packing `n6_packing.json` reaches v.

## Reduction

Suppose 6 such squares lie in T_L with L < v.

1. Scale the centres by v/L about the corner (0, 0). This gives 6 pairwise strictly disjoint closed unit squares
   in T_v. Everything below is about this one configuration.
2. A point certificate gives every point a weight. It shows that every admissible pose, except the exempt ones,
   captures weight ≥ 1, and that the total weight is < m. Then m strictly disjoint squares cannot all be
   non-exempt: their captures would add up to ≥ m.

The labels 0 to 5 are those of the stored pinwheel. The packing has C3 symmetry, acting on labels as
0→2→4 and 1→3→5. The lemma below is about the triple {0, 1, 3}.

## How a stage certificate is used

Labels name **positions** of the pinwheel, not squares. "Square k is in its box" means some square of
the packing has a pose in the box around position k.

A stage certificate with obstacles O (squares already placed in their boxes) and exclusion boxes E
gives a contradiction unless some other square has a pose in E:

1. Every square other than the obstacles is disjoint from them. So it contains no obstacle point
   (each obstacle point lies in the open obstacle square, or no square disjoint from it can contain
   the point; see "Obstacle points" below).
2. If none of these 6 − |O| squares is in E, all of them are non-exempt. Each captures weight ≥ 1,
   and the captures are disjoint because the squares are strictly disjoint closed sets. So the total
   weight is ≥ 6 − |O|.
3. The certificate's total is < 6 − |O|: < 6 for stage 1, < 5 for stage 2 and < 4 for stage 3.

So some square is in E, and the next stage starts from it. The tree:

| stage | given | conclusion |
|---|---|---|
| 1 | — | after a D3 symmetry, X ∈ {0, 1} is in its box (± 0.01) |
| 2 | X | a partner of X is in its box (± 0.012) |
| 3 | X and the partner, after C3 (boxes ± 0.0164, θ ± 0.012) | the third square of the triple is in its box |
| leaf | squares 0, 1 and 3 (up to C3) in their boxes | the triple lemma gives L ≥ v, a contradiction |

## Obstacle points

Three kinds, each proved for **every** pose of the obstacle square in its box:

- **Inner points** (`stage2/stage_inputs.py`). p = c0 + R(θ0)w, where w = 0 or w lies on the boundary of
  [−H, H]². The exact check √2·D + DTH·|w|₂ + |w|∞ < 1/2 puts p in the open square for every pose
  with |c − c0|∞ ≤ D and |θ − θ0| ≤ DTH.
- **Wall witnesses** (`stage2/wall_witness2.py`). p = w + (1 − ε)u, where w is on a side W of T with
  inward normal n_W, and u is an exact direction with u·n_W > 0.
  - Interval arithmetic over the pose box: p is strictly inside the near edge E1 and both lateral edges,
    and the point q1 of E1 on the line through p along u lies on the segment E1.
  - Analytic step: q1 is in the closed square, hence in T. So the parameter of q1 is ≤ 1 − ε, while the
    chord of the square along u has length 1/(u·n1) ≥ 1. So p is strictly before the far edge.
  - Hence p is in the open obstacle square, for every admissible pose in the box.
- **Chain witnesses** (`stage2/chain_witness.py`, case 1,3:0 only). Step 1 of the triple lemma, with
  square 3 in its box, gives d_R(P) ≥ cos(DTH3) for the top-right corner P of square 1. This needs the
  foot parameter t ∈ (0, 1) over B1 × B3, which `triple/validity_box.py` checks: t ∈ [0.094, 0.216].
  Interval branch-and-bound over B1 then proves that p is in the open square 1 on every sub-box where
  d_R(P) ≥ cos(DTH3) is possible.

Note: the `obstacle_points` of a certificate carry no kind label, and the `stage.wall_witnesses` field of
`cert_o13b.json` names only the chain file. The witness rule strings say `wall_witness.py`; the tool is
`wall_witness2.py`. The split above is the authoritative one. `stage2/reprove_obstacles.py` reruns the three generators with the
parameters in each certificate's `stage` field and checks that the obstacle points and exclusion boxes are exactly
the regenerated ones.

## Stage 1: some square is near a pinwheel position

- Certificate `loc3/cert_e1_100.json`:
  - symmetry D3;
  - 138 points, total weight 137013/22900 < 6;
  - exclusions are the 4 fundamental boxes: x, y within ± 1/100 of the pinwheel centres, u ≤ 1/200, so θ ≤ 0.01.
- Check: `check.py --n 6` gives **verified** (sha256 bbf90e7a…).
- Conclusion: some square has a D3 image in an exclusion box.
  - Apply that symmetry.
  - The reflection identifies the boxes at (2.232, 0.5) and (3.232, 0.5) with those of squares 1 and 0 for tilts
    in [−0.01, 0].
  - So square X ∈ {0, 1} has |c − c_X|∞ ≤ 0.01 and |θ| ≤ 0.01.
- Zero margin. For poses with θ = 0 and centre near y = 0.5, x ≈ 2.05 to 2.22, the bottom wall and the square's
  top edge are tight at the same time, so the capture margin is 0 at θ = 0 and only grows like θ. A grid check with Lipschitz
  shrinking therefore never closes u ∈ [0, h]. The second system handles the window x ∈ [2, 2.3],
  y ∈ [0.4999, 0.50001], u ∈ [0, 10⁻⁸] by an exact angular sweep: no event polynomial has a root in (0, 10⁻⁸],
  and the minimum captured weight there is 109/100.

## Stage 2: a partner of X is near its position

- Certificates use symmetry none and total < 5. X is an obstacle, given by obstacle points:
  - **inner points**: `stage_inputs.py` proves exactly that √2·D + DTH·|w|₂ + |w|∞ < 1/2;
  - **wall witnesses**: `wall_witness2.py` proves them by an analytic step plus interval arithmetic; the
    statement and proof are in the file header.
- The exclusions are the partners of X, meaning the squares that share a C3 image of {0, 1, 3} with X. Each
  partner box is ± 0.012 in x, y and θ.

| case | partners | certificate | total | check |
|---|---|---|---|---|
| X = 1 | 0, 3, 4, 5 | `stage2/cert_w_o1.json` (4 points; obstacle points 81 inner + 97 wall `ww2_o1_p0345.json`) | 4 | **verified** (sha256 f041908c…, 4 s) |
| X = 0 | 1, 3 | `stage2/cert_w_o0_p13_auto.json` (14 points; obstacle points 81 inner + 375 wall `ww2_o0_p13.json`) | 14/3 | **verified** (sha256 cf8b6d7d…, 1,774,260 nodes, 6543 s) |

## Stage 3: the third square of the triple is near its position

- Up to C3 there are three pairs: {0,1}, {0,3} and {1,3}.
  - From X = 1, the pair {1,4} maps to {3,0} under C3, and {1,5} maps to {3,1}.
  - Rotating a max-norm box by 120° enlarges it by the factor 1/2 + √3/2. So the obstacles use D = 0.0164 and
    DTH = 0.012. This covers both the stage-1 box 0.01 and the stage-2 box 0.012 after rotation.
- Certificates use total < 4.
- The obstacle points are of up to three kinds (0,1:3 uses inner points only):
  - inner points;
  - wall witnesses;
  - for case 1,3:0 only, **chain witnesses** (`stage2/chain_witness.py`). Square 1 cannot move right because Step 1 of
    the lemma gives d_R(P) ≥ cos(DTH3). This holds when t ∈ (0, 1) over B1 × B3, and `triple/validity_box.py` gives
    t ∈ [0.094, 0.216].

| case | third square's box (D, DTH) | certificate | total | check |
|---|---|---|---|---|
| 0,1:3 | 0.035, 0.045 | `cert_s3u2.json` (162 inner) | 7/2 | **verified** (e1162d62…, 24 s) |
| 0,3:1 | 0.035, 0.045 | `cert_o03d.json` (162 inner + 460 wall `ww2_o03_p1.json`) | 3 | **verified** (5803379a…, 11 s) |
| 1,3:0 | 0.05, 0.09 | `cert_o13b.json` (162 inner + 189 wall `ww2_o13_p0.json` + 41 chain `cw_o13_p0.json`) | 3 | **verified** (d670f9a8…, 2 s) |

## The triple lemma (`triple/LEMMA.md`)

**Lemma.** Suppose squares 0, 1 and 3 lie in T_v with pairwise disjoint interiors and satisfy:

- tilts ≤ Φ;
- corner shifts of squares 0 and 1 ≤ δ;
- the contact parameter t ∈ [τ, 1 − τ].

Then L ≥ v, and equality forces the weighted contacts to be tight. Strict disjointness contradicts this,
because g_sep > 0.

The inequality (M) is checked by `triple/lemma_check.py` at the following (Φ, δ, τ); it fails at (0.1, 0.15, 0.06).

| (Φ, δ, τ) | worst coefficient |
|---|---|
| (0.1, 0.12, 0.06) | −0.0097 |
| (0.05, 0.07, 0.03) | −0.0050 |
| (0.1, 0.1, 0.08) | — (also checked) |

Hypotheses on the final boxes (`triple/validity_box.py`, intervals):

| case | t range | corner shift | lemma used |
|---|---|---|---|
| 0,1:3 | [0.047, 0.267] | ≤ 0.025 | (0.05, 0.07, 0.03) |
| 0,3:1 | [0.046, 0.265] | ≤ 0.067 | (0.05, 0.07, 0.03) |
| 1,3:0 | [0.094, 0.216] | square 0 ≤ 0.05 + 0.09/√2 = 0.114, tilt ≤ 0.09 | (0.1, 0.12, 0.06) |

The second system measured t at the box corners as [0.055, 0.257], [0.048, 0.262] and [0.096, 0.214], inside the
intervals above, and rederived the lemma's coefficients (worst c₃ ≥ 0.0099, 0.0050, 0.0299 for the three
parameter sets).

So in every leaf the triple lemma applies and gives a contradiction. Hence L ≥ v. ∎

## Reproducing

From `problems/triangle`, after unpacking the release asset:

```bash
python checker/check.py certificates/n6/loc3/cert_e1_100.json --n 6 --max-depth 40 --jobs 8
python checker/check.py certificates/n6/stage2/cert_w_o1.json --n 5 --max-depth 40 --jobs 8
python checker/check.py certificates/n6/stage2/cert_w_o0_p13_auto.json --n 5 --max-depth 40 --jobs 16   # about 2 hours
python checker/check.py certificates/n6/stage2/cert_s3u2.json --n 4 --max-depth 40 --jobs 8
python checker/check.py certificates/n6/stage2/cert_o03d.json --n 4 --max-depth 40 --jobs 8
python checker/check.py certificates/n6/stage2/cert_o13b.json --n 4 --max-depth 40 --jobs 8
python certificates/n6/stage2/reprove_obstacles.py            # needs mpmath
cd certificates/n6/triple            # needs mpmath and sympy
python lemma_check.py 0.1 0.12 0.06      # prints "=> PROVED"
python lemma_check.py 0.05 0.07 0.03
python validity_box.py 0.0164 0.012 0.05 0.07 0.03 3 0.035 0.045    # case 0,1:3
python validity_box.py 0.035 0.045 0.05 0.07 0.03 3 0.0164 0.012    # case 0,3:1 (square 0 given the larger box)
python validity_box.py 0.0164 0.012 0.1 0.12 0.06 3 0.0164 0.012    # case 1,3:0 (t and squares 1, 3)
```

`--n` is the budget: 6 for stage 1, 5 for stage 2 (one obstacle square) and 4 for stage 3 (two).
`validity_box.py D DTH PHI DELTA TAU N D3 DTH3` gives squares 0 and 1 the box (D, DTH) and square 3 the box
(D3, DTH3); each run prints the t range and "HYPOTHESES HOLD". In case 1,3:0 square 0 is the free square with
box (0.05, 0.09); its corner shift 0.05 + 0.09/√2 < 0.12 and tilt 0.09 < 0.1 are checked by hand.

## How the certificates were found

An LP over a finite set of poses gives the weights; a float branch-and-bound searches for poses that capture
less than 1, and they are added back. Two observations were needed to make the stage-2 and stage-3 LPs close:

1. **Fractional packings just outside the boxes.** The LP lets each obstacle and each excluded square move
   independently inside its box, and fractional mixtures of poses just outside a box reach the budget. Wall
   and chain witnesses remove these: they exempt overlaps that the walls, or a neighbour pinned by a wall, make
   impossible. Smaller boxes alone did not help.
2. **Which obstacle points matter.** `cert_o13b.json` still passes with one eighth of its obstacle points, while
   `cert_w_o0_p13_auto.json` fails with the 81 inner points alone: there the wall witnesses are needed.
