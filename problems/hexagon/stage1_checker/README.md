# Stage 1, checker 1: exact unavoidability checker for the regular hexagon

`check_hex.py` is the exact checker of `squares-in-triangle` (wand125/squares-in-triangle), adapted to
the regular hexagon and extended with excused boxes. It proves the stage-1 claim of
`../n3/SPEC_stage1.md`:

    every closed unit square Q ⊆ H_L (any position, any angle) whose reduced pose is not in an
    excused box captures points of total weight ≥ 1.

Here H_L is the regular hexagon of side L with centre (L, L√3/2) and a flat bottom (inside
[0, 2L] × [0, L√3]). Points on ∂Q count.

## Running

```bash
# Python 3.10+, standard library only
python check_hex.py ../n3/stage1_cert.json --n 3 --root 8 --max-depth 32 --u-scale 16 --jobs 4
```

The recorded run is `records/stage1_check_d32.json`: `"status": "verified"`, 5,768 nodes, maximum
depth 23, 742 excused boxes, 0 uncertified boxes, total weight 749319/250000 < 3. It took 301 s with
2 processes. The summary contains the certificate's sha256.

`examples/` holds small certificates (n = 1 and n = 2 at their optimal sides, and two that must
fail).

## Soundness

`SOUNDNESS.md` is the soundness argument of the triangle checker. It applies unchanged to the
field Q(√3), the Bernstein tests, the admissible polygon and the subdivision. The hexagon changes
three things.

1. **Container.** Six side constraints instead of three. Each is an exact half-plane over Q(√3).
2. **Symmetry D6.**
   - The checker verifies exactly that the weighted points are invariant under the generators of
     the symmetry group of H_L (the rotation by π/3 about the centre and a reflection).
   - On angles the group acts as θ ↦ θ + π/3 and θ ↦ −θ (mod π/2). So every pose is equivalent to
     one with θ ∈ [0, π/12].
   - The checker proves θ(U) > π/12 exactly for U = 1/7 (`check_U`), so u = tan(θ/2) ∈ [0, 1/7]
     covers every pose.
3. **Excused boxes.**
   - A box of the subdivision is accepted as EXCUSED only if, by exact rational comparisons, the
     whole box (all centres and all u in it) lies inside one excused box of the certificate.
   - Every other box must be certified as in the triangle checker.

So the claim is proved for every reduced pose outside the union of the excused boxes.
