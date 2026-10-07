# Mathematical basis of the point-only verifier

This appendix explains the mathematical rules replayed by the supplied checker.
It is a written argument, not a formalisation of the Python program. Acceptance
also requires the complete numerical replay and assembly described in
`PUBLICATION.md`. A lemma proving a local bound is never, by itself, a proof of
coverage of all poses.

All point weights are nonnegative rational numbers. All squares are closed.
Throughout the representative domain, a pose is `(cx,cy,t)` with
`0 ≤ t ≤ 1/2`, where `t = tan(θ/2)`. Put

```
a = 1−t²,  b = 2t,  r = 1+t²,
u = a(px−cx)+b(py−cy),
v = −b(px−cx)+a(py−cy).
```

Since `a²+b²=r²` and `r>0`, point `p` belongs to the unit square exactly when
`u−r/2`, `−u−r/2`, `v−r/2`, and `−v−r/2` are all nonpositive. Equality is included.
The negation of one of these predicates is a *strictly positive* value.

## 1. Uniform polynomial tests

Each predicate is affine in the two centre coordinates and quadratic in `t`.
Its maximum on a closed rational pose box is therefore obtained by taking the
maximum over the four centre corners of a univariate quadratic maximum. A
quadratic maximum on a closed interval occurs at an endpoint, or at its stationary
point when the quadratic coefficient is negative and that point is in the
interval. Every such value is rational. Minima follow by negating the polynomial.
The same argument applies to rational linear combinations of these predicates.

Thus `max g≤0` proves a point-side predicate throughout the box; `min g>0`
disproves it throughout the box. For a list of points whose four predicates all
pass, the sum of their weights is a valid captured-mass lower bound. Omitting
other nonnegative weights can only weaken that lower bound.

Code: `closed_cover_bridge.py`, `compile_box_capture_rows.py`,
`point_box_sieve.py`. Local polynomial tests alone do not justify deleting a pose
box, nor do samples of `t` justify an interval statement.

## 2. Containment in the physical container

For `0≤t≤1/2`, the axis-aligned half-width of a unit square is
`h(t)=(1+2t−t²)/(2(1+t²))`. A square is in `[0,L]²` exactly when
`h≤cx,cy≤L−h`. Multiplying these four inequalities by `2r>0` gives four
quadratic wall predicates. For example,

```
wleft  = 1−2cx+2t−(1+2cx)t²,
wright = 1−2L+2cx+2t+(−1−2L+2cx)t².
```

The bottom and top predicates replace `cx` by `cy`. These predicates are known
to be nonpositive when reasoning about physically contained squares.

Also `h'(t)=(1−2t−t²)/(1+t²)²` has at most one zero in this interval, a
maximum. Hence the minimum of `h` on any subinterval is the minimum of its
endpoint values. Intersecting a pose box's centre ranges with
`[hmin,L−hmin]²` retains every physical pose. Strictly empty intersections
are impossible; a degenerate closed intersection is not empty.

For a direct point witness, each of the four signed projections in Section 1
can be bounded using either the pose-box centre endpoint or the corresponding
physical wall bound. Either is valid for every physical centre. Substitution
of a wall bound gives, after multiplication by a positive denominator, a
polynomial of degree at most four. On a rational interval, writing this polynomial
in the Bernstein basis proves it nonpositive if all its rational Bernstein
coefficients are nonpositive: the basis functions are nonnegative and sum to one.
This is a sufficient test, not a necessary test. Its failure is not a counterexample.

Code: `physical_pose_enclosure.py`, `physical_predicate_conflict.py`,
`replay_physical_point_witness.py`.

## 3. Predicate relaxation and an exact dual bound

For each uncertain predicate `gᵢ≤0`, let `zᵢ` be its truth indicator. Actual poses
give values zero or one. For instance, `max(gᵢ−gⱼ)≤0` implies `zᵢ≥zⱼ`.
If `α>0` and `max(gᵢ+αgⱼ)≤0`, both predicates cannot be false, so
`zᵢ+zⱼ≥1`. Both implications include all equality cases.

For a point with `k` uncertain predicates and no certainly false predicate,
introduce a capture variable `y`. The actual capture indicator satisfies
`y−Σzᵢ≥1−k`. Certainly captured mass contributes a constant `B`; points
with a certainly false predicate may be omitted. Collect these valid constraints
as `Ax≥b`, with `0≤x≤1`, and use the nonnegative point weights in the objective
`B+cᵀx`. Every physical pose gives a feasible vector with this objective equal
to the captured mass of the included points. Enlarging the feasible set cannot
invalidate a lower bound.

For any rational vector `λ≥0`, put `e=c−Aᵀλ`. Then every feasible vector obeys

```
B+cᵀx = B+λᵀAx+eᵀx
       ≥ B+λᵀb+Σᵢ min(0,eᵢ).
```

The last step uses `0≤xᵢ≤1`. All negative residuals must be subtracted. The
multiplier need not be an exactly feasible LP dual, or be optimal. Floating-point
LP is used to propose certificates during search; the verifier reconstructs the
valid constraints and evaluates this formula with rational arithmetic.

Code: `predicate_lp_capture.py`, `predicate_conflict.py`,
`reoptimize_capture_weights.py`. A saved numeric objective or success flag is not
accepted in place of this calculation.

## 4. Valid conflict cuts, branch coverage, and empty branches

Fix a proposed truth pattern `dᵢ∈{0,1}`. Take nonnegative rational multipliers
`λᵢ`, not all zero, and form `H=Σ λᵢ sᵢ gᵢ`, with `sᵢ=1` if `dᵢ=0`
and `sᵢ=−1` otherwise. At any pose matching the pattern, every summand is
nonnegative. It is strictly positive if a positive multiplier is attached to a
false predicate. Consequently the pattern is impossible if `max H<0`, or if
`max H≤0` and such a strictly positive summand is present. Section 1 provides
an exact test of the maximum. In particular, `max H=0` does *not* exclude an
all-true pattern.

The resulting valid cut is

```
Σ(dᵢ=0) zᵢ + Σ(dᵢ=1)(1−zᵢ) ≥ 1,
```

where the sums use only positive-multiplier indices. Wall predicates may be
included with their truth value fixed to one, but only in the physical domain
of Section 2. Substitution of those fixed values yields a cut on the remaining
variables. Each cut is reconstructed and verified before a leaf dual uses it.

A finite branch tree on a predicate or capture indicator must retain both the
zero and one branches. Every actual pose follows at least one complete path.
At a numerical leaf, Section 3 supplies its lower bound. An empty branch is
accepted only after an exact positive lower bound for the auxiliary total-slack
problem: a feasible original vector would yield zero slack, a contradiction.
Nonpositive slack bounds do not prove emptiness. An unresolved leaf contributes
only its already proved baseline (or zero); it cannot be deleted.

Induction from leaves to the root takes the minimum of the nonempty branch
bounds. Adding a verified conflict cut at an internal node is valid because it
excludes no actual pose. Reusing an old empty leaf requires replaying its old
proof, not its label.

Code: `predicate_branch.py`, `physical_predicate_branch.py`,
`reoptimize_physical_tree_weights.py`, `extend_reweighted_physical_tree.py`.

## 5. Transfer to different point weights

Suppose old weights `wᵢ` have an independently replayed lower bound `m` on a
fixed physical pose domain, and new weights are `vᵢ`. The coordinates and domain
are unchanged. Partition the points into those always captured (`A`), never
captured (`N`), and uncertain (`U`), using valid uniform geometric tests.
For any rational `α≥0` and capture indicators `Iᵢ`,

```
Σ vᵢ Iᵢ = α Σ wᵢ Iᵢ + Σ (vᵢ−αwᵢ) Iᵢ
          ≥ αm + Σ(i∈A)(vᵢ−αwᵢ) + Σ(i∈U)min(0,vᵢ−αwᵢ).
```

The uncertain terms use `0≤Iᵢ≤1`; the never-captured terms vanish. This proves
the transferred bound. Taking the maximum of finitely many independently valid
choices of `α` is safe. At `α=1`, unchanged weights need no classification.
The old candidate need not cover the entire container: the old *local* lower
bound on this same domain must be replayed. Old and new point ordering, geometry,
container and certificate identity are all part of this check.

Code: `transfer_point_capture.py`, `replay_capture_margin.py`, `frontier.py`.

## 6. Fixed-angle full-centre minimum, including boundaries

Fix a rational sine and cosine. In rotated centre coordinates `(U,V)`, each
point is captured on a closed axis-aligned rectangle. Its four boundary lines
and the rotated physical-centre parallelogram form a finite arrangement. Captured
mass is constant on each two-dimensional open cell. Search every such cell that
meets the physical domain's interior.

Why are lower-dimensional faces not missing a smaller value? At any allowed
boundary centre, the finitely many points not captured have a neighbourhood
where they remain not captured. The physical-centre parallelogram has nonempty
interior (here `L=5>√2`), so that neighbourhood contains an interior centre
avoiding all arrangement lines. Its captured-point set is a subset of the
original one. Nonnegative weights therefore cannot give it larger mass. The
minimum over open cells equals the full closed-domain minimum. Rational
coefficients also allow a rational witness in every nonempty open cell.

A sweep in `U`, with exact range additions in `V`, evaluates these cell masses.
Intersections with the physical domain are checked by exact projection and
interval intersection, not by sampling a centre grid.

Code: `exact_fixed_angle_separator.py` and the fixed-angle components called by
`near_axis_partition_bridge.py`.

## 7. An entire near-axis angle band

For `0<t<1`, use scaled rotated coordinates
`U=2D(a cx+b cy)`, `V=2D(−b cx+a cy)`. Set
`ℓ=Dr(a+b)` and `H=2LDr²−ℓ`. The physical-centre inequalities become
`ℓ≤aU−bV≤H` and `ℓ≤bU+aV≤H`. For a strip `u₀≤U≤u₁`, its physical
intersection projects to the following closed `V` interval, or is empty if
its lower endpoint exceeds its upper endpoint:

```
v₀ = max((a u₀−H)/b, (ℓ−b u₁)/a, (aℓ−bH)/r²),
v₁ = min((H−b u₀)/a, (a u₁−ℓ)/b, (aH−bℓ)/r²).
```

To derive this, the possible `U` interval at fixed `V` has lower endpoint
`max(u₀,(ℓ+bV)/a,(ℓ−aV)/b)` and upper endpoint
`min(u₁,(H+bV)/a,(H−aV)/b)`. Comparing all three lower terms with all
three upper terms gives three automatic conditions and exactly the six
displayed inequalities on `V`. Here `a,b,r` are positive.

In these coordinates, a point at `(X/D,Y/D)` has capture boundaries

```
U± = (2X±D)+4Yt+(−2X±D)t²,
V± = (2Y±D)−4Xt+(−2Y±D)t².
```

The verifier proves that all comparisons used by the cell sweep stay fixed
through a positive interval `(0,T]`: boundary order, projection maximum and
minimum choices, empty-strip decisions, and the interval searches selecting
physical `V` cells. Comparisons of rational functions are reduced to polynomial
signs after proving denominator positivity.

For a nonzero polynomial `P(t)=cₖtᵏ+Σⱼ>ₖcⱼtʲ`, let
`S=Σⱼ>ₖ|cⱼ|`. With `0<Tcap≤1`, choose
`T=min(Tcap,|cₖ|/(2S))` when `S>0`, and `T=Tcap` otherwise.
For `0<t≤T`, the tail after factoring `tᵏ` has absolute value at most
`St≤|cₖ|/2`. The sign is consequently that of `cₖ`. Identically zero
comparisons are handled separately. Each certified comparison therefore holds
through the entire band, not just at a sampled small angle.

The cell membership and exact masses in the sweep are now fixed throughout
the band. Section 6 justifies the boundary treatment for each positive angle.
The axis `t=0` is checked independently by the fixed-angle sweep. Taking the
minimum of the axis bound and the positive-band bound gives a bound on `[0,T]`.
When joined to a subdivision on `[T,t₁]`, the shared face is included by both
parts; no face is lost and masses are not added between overlapping pose domains.

Code: `certify_near_axis_sweep.py`, `certify_n21_near_axis_path.py`,
`near_axis_partition_bridge.py`. The bound is specific to its candidate weights
and verified band; it cannot be transferred to an arbitrary angle or candidate.

## 8. Closed partitions and one-sided exclusions

Let a full-dimensional closed rational box `R` be divided into finitely many
closed subboxes `Bᵢ⊆R`, with disjoint interiors and total volume equal to that
of `R`. Their union is closed and has full volume in `R`. If a point of `R`
were outside that union, a small ball around it would avoid the union and have
positive-volume intersection with `R`, even at an edge or corner of `R`. This
contradicts volume equality. Thus the subboxes cover every boundary point too.
Containment and interior disjointness are essential; volume equality alone is
insufficient.

For a mixture of closed boxes and boxes open at an angular endpoint, that
argument cannot be used. Instead collect all coordinate endpoints and partition
each coordinate axis into singleton endpoints and open intervals between them.
Their Cartesian products form finitely many strata. Membership in each input
box is constant on every stratum, so checking an interior representative of
every stratum proves exact coverage, including all lower-dimensional faces.

The one-sided angular exclusion uses physical width
`w(t)=(1+2t−t²)/(1+t²)`. In a pose box, containment requires
`w(t)≤K=2 min(x₁,L−x₀,y₁,L−y₀)`. On an interval with
`t₁²+2t₁≤1`, the derivative is positive except possibly at its upper endpoint.
If `w(cut)≥K`, then `t>cut` is impossible. The equality face `t=cut` is
not excluded. The stratified coverage check preserves it.

Code: `compile_box_capture_rows.validate_partition`, `stratified_box_cover.py`,
`verify_angle_clip.py`, `run_prefix.py`.

## 9. From local certificates to the theorem

### Boundary closure principle

For a finite nonnegative point measure, captured mass is upper semicontinuous
as a function of the square's pose. More concretely, fix a pose `z`. Each point
outside its closed square violates at least one continuous containment
predicate strictly. It remains outside in some neighbourhood of `z`. There
are finitely many such points, so a common neighbourhood exists in which every
captured point was already captured at `z`. Nonnegative weights imply
`μ(Q(z'))≤μ(Q(z))` throughout that neighbourhood.

Consequently, if `D` is any physical pose domain and `E` is dense in `D` in
the relative topology, a uniform bound `μ(Q(z'))≥q` for **every** `z'∈E`
implies the same bound for every `z∈D`: intersect the neighbourhood above
with `E`, and compare masses. Density in the ambient parameter space alone
does not suffice if it misses a component of `D`.

For the full physical domain at side `L>√2`, every allowed orientation has
a nonempty open centre square, since its axis-aligned width is at most `√2`.
Boundary centres can be moved slightly toward `(L/2,L/2)`, gaining strict
wall slack. Continuity then permits small angle perturbations. Thus physical
interior poses, with the angle in the interior of its allowed interval, are
relatively dense even at wall and angular endpoints. Section 6 uses the
fixed-angle version of this argument.

This principle does not justify a finite angle sample, an unverified open
region, or omitting an isolated physical component. The present checker still
requires the explicit closed and stratified coverage checks in Section 8;
no numerical acceptance condition is weakened by this observation.

### Complete assembly

The assembly must match exactly the pending regions from each stage to the next.
Every required final parent must have a complete numerical replay, and every
nonempty final leaf must have lower bound at least `q`. Exclusion of a parent
with `t` lower endpoint greater than `5/12` is justified only by the
representative-domain reduction, not by physical impossibility. Parents crossing
that cutoff are retained.

D4 invariance of the *aggregated* point weights, nonnegativity, support containment,
the exact total mass, and `21q−M>0` are checked separately. The D4 reduction,
centre-dilation argument and explicit upper packing in `PUBLICATION.md` then
give `s(21)=5`. These reductions do not turn missing local proofs into a theorem.

## Attribution and trust boundary

The weighted-cover and centre-dilation framework precedes this implementation.
The support comes from Evan Daniel's earlier point certificate. His published
mixed-measure proof of `s(21)=5` is prior work, not this certificate. The local
predicate, transfer, partition and near-axis rules above document the route
implemented here; their correctness depends on both these arguments and their
faithful implementation in the pinned source. Neither this appendix nor a
successful execution is a claim that the checker is formally verified or that
an external reviewer has validated the result.
