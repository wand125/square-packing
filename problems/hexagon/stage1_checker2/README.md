# Second check of the stage-1 certificate (three unit squares in the regular hexagon)

Written from `SPEC_stage1.md` and the certificate only; the first checker's code was not read.

## Result

`stage1_cert.json` (sha256 `ab0bdfdd…3e623d27`, 630 points, 742 excused boxes): **verified**.

| | |
|---|---|
| D6 invariance of the weighted points | checked exactly |
| total weight 749319/250000 < 3 | checked exactly |
| boxes | 58,894 (max depth 22), from 512 root pieces |
| covered / empty / excused / local sweep | 11,728 / 10,687 / 1,264 / 6,024 |
| failed | 0 |
| time | 2 h 48 min with 14 processes (`hexcheck.py --jobs 14 --grid 8`) |

## Method (`hexcheck.py`)

Boxes in (centre x, centre y, u = tan(θ/2)), u ∈ [0, 1/7], are split recursively.

- **Covered:** points of total weight ≥ 1 are captured at every pose of the box, admissible or
  not. For u ∈ [0, 1/7], cos θ and sin θ are ≥ 0, so each capture inequality has a fixed worst
  corner of the centre rectangle. There it is a quadratic in u (times 1 + u²), bounded below by
  its three Bernstein coefficients.
- **Empty:** one container constraint (a square vertex beyond one hexagon side) fails on the whole
  box, at its most favourable corner.
- **Excused:** the box lies inside one closed excused box. This is tried only after the box failed
  to be covered or empty; a box that meets an excused box partly is split, at the excused face
  when that face is central.
- **Local sweep:** small boxes where the captured point switches get the exact angular
  line-arrangement sweep of check2 (`sweep.py`), restricted to the box.
  - Points captured on the whole box add a constant.
  - Points never captured in the box are dropped; dropping a point can only lower the count.
  - The remaining points' capture lines, the box sides and the container constraints that do
    not hold on the whole box form the arrangement.
- **Closure:** an admissible pose that is not excused has a neighbourhood free of the (closed)
  excused boxes. Poses with centre in the interior of the admissible region, interior to a box
  and at a non-critical angle are dense there, and each lies in a covered box or in a checked
  open cell. The captured weight of a closed square is upper semicontinuous in the pose, so the
  bound extends to every admissible, non-excused pose. The admissible region has interior at
  every angle (inradius L√3/2 > √2/2).
- Every accepted sign is exact in Q(√3); floats only order candidate points.

## Negative control: the excused boxes are needed

`hexwitness.py` tries grid poses inside each excused box and checks, exactly, admissibility and the
captured weight. In 54 of the 742 excused boxes it finds an admissible pose whose captured weight is
< 1 (`witness_excused.json`). An example is centre (303253/250000, 1/2), u = 0, with weight
495031/500000. So the claim fails without the excused boxes, as it should.
