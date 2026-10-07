# n = 4: the smallest 1:2 rectangle that holds 4 unit squares

Let s(n) be the smallest v such that n non-overlapping unit squares (any positions, any angles)
fit in the rectangle R_v = [0, 2v] × [0, v].

**Theorem.** s(4) = v4, where v4 ≈ 1.93028330671426938847 is the largest real root of
5x³ + 8x² − 32x − 4.

## Upper bound: the packing (Stenlund, 2010)

Let β ≈ 40.518° be such that t = tan(β/2) is the root of t³ − 5t² − t + 1 = 0 in (0, 1). Write
c = cos β and s = sin β. The four squares in R_v, with v = v4, are:

- A = [0, 1] × [v − 1, v] and B = [2v − 1, 2v] × [0, 1] (axis-parallel, in opposite corners);
- L, the square with vertices
  b, b + (−c, s), b + (s, c), b + (s − c, s + c), where b = (2c, 0);
- U = the image of L under the point reflection through the centre (v, v/2).

L touches the bottom side at b. The corner (1, v − 1) of A lies on its upper-left edge. Its
upper-right edge lies on a line through the centre, where it meets the corresponding edge of U.

For a general angle, the same contacts give a one-parameter family of packings, with short side

    s(β) = 2(sin β + cos β)(1 + sin β) / ((sin β + cos β)² + sin² β).

Its derivative vanishes exactly at tan(β/2) ∈ {0, ±1} or at a root of t³ − 5t² − t + 1, and
v4 = s(β*) is the minimum. The minimal polynomial 5x³ + 8x² − 32x − 4 of v4 is the resultant of
x − s(t) and t³ − 5t² − t + 1. The packing is the one shown on Friedman's page.

## Lower bound: the weighted point set

The certificate `n4_cert.json` lives in K = Q(v4). It has 7 points of weight 1/2 each
(total 7/2):

| points | weight | role |
|---|---|---|
| (1, v−1), (2v−1, v−1), (1, 1), (2v−1, 1) | 1/2 each | corners of the axis-parallel squares (and mirror images) |
| (v, v/2) | 1/2 | the centre, on the contact line of L and U |
| (v, v/2 ± 2286/10000) | 1/2 each | on the vertical axis |

It also lists 4 wedges: each corner point paired with the centre.

1. **Capture.** Every closed unit square Q ⊆ R_{v4}, at any position and any angle, contains
   weight ≥ 1. This is proved by `checker/` at L = v4 exactly, with margin zero, and
   independently by `checker2/` (without the wedges and without symmetry).
2. **Budget.** 7/2 < 4.
3. **Scaling.** Suppose 4 squares Q_i with disjoint interiors fit in R_L with L < v4.
   Put λ = v4/L > 1, m = (L, L/2) and m′ = (v4, v4/2).
   - Move each square without rotating it, so that its centre goes from c_i to
     c_i′ = m′ + λ(c_i − m).
   - **Containment.** A unit square at angle θ has half-widths h_x, h_y ≤ v4/2. It lies in R_L iff
     |c_x − L| ≤ L − h_x and |c_y − L/2| ≤ L/2 − h_y. Then
     |c′_x − v4| = λ|c_x − L| ≤ λ(L − h_x) = v4 − λh_x ≤ v4 − h_x. The y-coordinate is handled the
     same way, so each moved square lies in R_{v4}.
   - **Disjointness.** For two of them, let D = (Q_i − c_i) + (c_j − Q_j). D is a convex set with
     0 in its interior, and int Q_i ∩ int Q_j = ∅ means c_j − c_i ∉ int D.
     - If λ(c_j − c_i) were in D, then c_j − c_i = (1/λ)·λ(c_j − c_i) + (1 − 1/λ)·0 would be in
       int D, a contradiction.
     - So the moved closed squares are disjoint.
   - Each moved square captures weight ≥ 1, and they share no point. So the total weight is ≥ 4,
     which contradicts 7/2 < 4.

Hence s(4) ≥ v4, and with the packing, s(4) = v4.

## Where margin zero happens

In the packing, every square captures exactly what it must, and the shared points lie on two
squares at once:

- A captures (1, v−1) and (1, 1), both on its boundary;
- L captures (1, v−1) (on an edge), the centre (on an edge) and (v, v/2 − 2286/10000) (inside);
- U and B are the images under the point reflection.

So the corner points and the centre carry the overlap: 4 squares × weight 1 = 4, but the total
is only 7/2.

The packing is not rigid to first order. L and U can rotate together, with overlap only of order
t². Near the extremal pose, a square captures the corner point or the centre, and which one
switches. The wedge lemma (`checker/README.md`, 6b) proves "corner or centre" on such boxes. Its
key inequality is exactly v ≤ s(β), whose equality case is β*.

## Lower bounds below v4 (rational L)

`below/` holds certificates for rational L < v4. They are not needed for the theorem; they show
the route there.

| file | L | points | total |
|---|---|---|---|
| `n4_L957_500.json` | 1.914 | 3 on the midline y = L/2 | 3 |
| `n4_L77_40.json` | 1.925 | 12 | 77/20 |
| `n4_L1927_1000.json` | 1.927 | 12 | 77/20 |
| `n4_L9651_5000.json` | 1.9302 | the 7-point form above | 7/2 |

The 3-point bound works exactly up to v = (1 + 2√2)/2 ≈ 1.91421. Beyond that, a square at 45°
standing on the bottom side fits between two of the three points.
