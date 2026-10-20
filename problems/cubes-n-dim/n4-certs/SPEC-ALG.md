# Certificates over a quadratic field — specification for an independent checker (alg-v1)

Purpose: certify that k unit n-cubes fit in the n-cube [0, s]^n where s is an element of Q(√d) such as 2 + (1/2)√2,
exactly, with no rounding. Everything below is to be decided with exact arithmetic in Q(√d).

## Numbers
A number is a JSON array of two strings `["a", "b"]`, meaning a + b·√d, where a and b are rationals written as
`"p/q"` or `"p"` (q > 0; the strings must be accepted by Python's `fractions.Fraction`). d is 2 or 3 (field of the
certificate). Arithmetic: (a + b√d) + (a′ + b′√d) = (a + a′) + (b + b′)√d; (a + b√d)(a′ + b′√d) = (aa′ + d·bb′) + (ab′ + ba′)√d.
Sign of a + b√d: 0 if a = b = 0; if a and b are both ≥ 0 it is +; both ≤ 0 it is −; otherwise (opposite signs)
the sign is that of a when a² > d·b², else that of b. |x| = x if sign(x) ≥ 0 else −x. x ≥ y means sign(x − y) ≥ 0.

## File
```
{"format": "alg-v1", "n": 3, "k": 9, "d": 2, "s": ["2", "1/2"],
 "c": [[num, ...], ...],            // k centres, each n numbers
 "R": [[[num, ...], ...], ...],     // k frames, each an n x n matrix of numbers; column m of R_i is the m-th axis of cube i
 "note": "..."}                     // informational, ignored
```
Cube i is the closed set c_i + R_i [−½, ½]^n; the container is the closed cube [0, s]^n. Any other field is ignored.
Reject the file if n < 2, k < 1, d ∉ {2, 3}, `c` or `R` do not have k entries of the stated shape, or any number is
not of the form above (a JSON number instead of a string, a decimal, a bare √, etc.).

## Accept iff all of the following hold
1. Orthogonality: for every i and every pair of columns p, q of R_i, the dot product (sum of products of entries) is
   1 if p = q and 0 otherwise. (det ±1 both allowed: the cube is symmetric under reflections.)
2. Container: for every i and coordinate r, with h_i[r] = ½ · Σ_m |R_i[r][m]| (sum over the row r of absolute
   values): c_i[r] − h_i[r] ≥ 0 and s − c_i[r] − h_i[r] ≥ 0.
3. Separation: for every pair i < j there is a candidate axis a with
   2·|a · (c_i − c_j)| ≥ Σ_m |a · R_i[:, m]| + Σ_m |a · R_j[:, m]|,
   where the candidate axes are the generalised cross products of k′ columns of R_i and n − 1 − k′ columns of R_j
   (k′ = 0, …, n − 1; every choice of columns, in the column order of the matrices), and an axis whose entries are all
   zero is skipped. The generalised cross product of n − 1 vectors v_1, …, v_{n−1} ∈ Q(√d)^n is the vector whose
   m-th entry is (−1)^m times the determinant of the (n − 1) × (n − 1) matrix obtained from the rows v_1, …, v_{n−1}
   by deleting column m (m = 0, …, n − 1). For n = 3 this is the usual cross product; for n = 4 there are C(8, 3) = 56
   candidate axes per pair.
   Condition 3 is a sufficient condition for disjoint interiors (separating-axis theorem; scaling of a does not matter).

Output ACCEPT/REJECT with the reason, exit code 0 only on ACCEPT; print s as the exact pair and as a decimal.

## Reference values
2 + 1/√2 = ["2", "1/2"] with d = 2 (since 1/√2 = √2/2); 3 + 1/√2 = ["3", "1/2"]; 2 + 7√2/10 = ["2", "7/10"];
2 + 1/√3 = ["2", "1/3"] with d = 3. The checker must not read these from anywhere but the certificate's `s`.

## Suggested negative tests
A frame with one entry changed (not orthogonal); s decreased by ["0", "1/1000000"]; a centre moved by 1/64 into a
neighbour; two centres made equal; a number given as a JSON float; d changed from 2 to 3 (the same file must then be
rejected at orthogonality or at the container, since √2 entries become √3).
