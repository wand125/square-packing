# Upper bounds: exact packings

`configs.py` writes three packings exactly in Q(√2), with s = 2 + 1/√2:

| Packing | Side | Cubes | Gives |
|---|---|---|---|
| n8_side2 | 2 | 2×2×2 axis-parallel grid | s₃(n) ≤ 2 for n ≤ 8 |
| n9_s | s | 8 corner cubes, plus 1 cube at the centre rotated 45° about z | s₃(9) ≤ s |
| n10_s | s | 8 corner cubes, plus 2 such rotated cubes in the central column, at z ∈ [0, 1] and [s − 1, s] | s₃(10) ≤ s |

The horizontal section of a rotated cube is the diamond |x − s/2| + |y − s/2| ≤ 1/√2. It touches the corner cubes
only at points such as (1, 1).

The packings are those listed on Erich Friedman's Packing Center page "Cubes in Cubes"
(https://erich-friedman.github.io/packing/cubincub/). We claim no originality for them.

## Two independent exact checks
- `check_sympy.py` (exact arithmetic in sympy):
  - every vertex lies in [0, s]³;
  - interiors are pairwise disjoint, by the separating-axis theorem over the 15 axes (touching is allowed);
  - every R is orthogonal with determinant 1.
- `check_q2.py` (no sympy; its own field Q(√2) on Python Fractions, with an exact sign test):
  - containment by vertices;
  - disjoint interiors, by computing the exact volume of A ∩ B. Each cube's faces are clipped by the other's
    closed half-spaces and the divergence theorem is applied. The volume must be exactly 0.

Both checkers accept all three packings and reject the negative controls:
- two stacked rotated cubes overlapping by 0.4 in height;
- a cube protruding through the floor (`check_q2.py`).

As a sanity check of the volume routine:
- the cube with itself gives 1;
- a half-shifted copy gives ½;
- the cube rotated 45° about its own centre gives 2(√2 − 1).

Reproduce: `python3 check_sympy.py` and `python3 check_q2.py`. The outputs must equal `check_sympy.out` and
`check_q2.out`.
