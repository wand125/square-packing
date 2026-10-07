# Stage 2 claim for three unit squares in the regular hexagon

This is the specification of what stage 2 must establish, written for an independent re-implementation. It
deliberately does not describe how the first implementation works (`stage2_checker/`). Do not read that code.

## Setting

- H is the closed regular hexagon with side v = (1 + √3)/2.
- Use centre 0 and a flat bottom. Its vertices are (±v, 0) and (±v/2, ±v√3/2).
- A pose is (c, θ). It denotes the closed unit square Q(c, θ) = c + R_θ[−1/2, 1/2]². θ is taken modulo π/2.

## Input

`stage1_cert.json` (sha256 ab0bdfdd8662c9dfb7827f36bd2b520604f3f76e5657b80c4f7123f83e623d27), field
"excused": 742 boxes [x0, x1, y0, y1, u0, u1] with rational endpoints. These are given in the
certificate's frame:

- the centre of H is at (v, v√3/2), so subtract it to get the centre-0 frame;
- u = tan(θ/2) with u ∈ [0, 1/7].

## Claim for each box E_k (k = 0, …, 741)

There are no three closed unit squares Q_1, Q_2, Q_3 such that:

- all three lie in H;
- they are pairwise disjoint (as closed sets);
- the pose of Q_1 lies in E_k (after converting to the centre-0 frame with θ = 2 arctan u).

Q_2 and Q_3 are unrestricted.

Together with stage 1 this proves s(3) = v. Stage 1 is verified twice. It says that in any triple of
pairwise disjoint closed unit squares in H, some D6 image of the triple has a square with pose in some E_k.

## Tools you may use

You may use the **local lemma** (`local_lemma/LOCAL_LEMMA.md`). It is a separate proof with its own checks;
read it and check it if you want.

Statement:

- Let P_i = R^i B for i = 0, 1, 2 be the pinwheel squares.
  - B = [−v/2, −v/2 + 1] × [−v√3/2, −v√3/2 + 1].
  - R is the rotation by 2π/3.
- No triple of pairwise disjoint closed unit squares in H has the following form, for each i in the frame
  rotated by R^{−i}:
  - the tilt is within 0.08 rad of P_i;
  - the lower-left corner is within 0.05 of the lower-left vertex (−v/2, −v√3/2).
- The same holds for every D6 image of the pinwheel.

The lemma's proof also gives two inequalities on the contact functions. They are stated in §2–§3 of the
lemma. You may use them wherever their hypothesis holds. You may also find your own way through the region
near the pinwheel.

## What to report

For each k, report proved or not proved, plus any statistics you like. All 742 must be proved.

A useful negative control: at side 1.01·v, the pinwheel scaled by 1.01 from the centre is a genuine packing,
and your pruning must not discard it.
