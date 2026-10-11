# Formats

## Certificate (`rational-unit-square-v1`)

    {
      "schema": "rational-unit-square-v1",
      "a": "<rational>",          // box height (short side), e.g. "377083101/100000000"
      "b": "<rational>",          // box width
      "n": <integer>,             // number of squares
      "squares": [
        { "x": "<rational>", "y": "<rational>", "tan_half_angle": "<rational>" }, ...
      ]
    }

Rationals are decimal strings or `p/q`. (x, y) is the centre of a unit square in the box
[0, b] × [0, a]. Its angle θ is given by t = tan(θ/2), so cos θ = (1 − t²)/(1 + t²) and
sin θ = 2t/(1 + t²) are rational. The four vertices are (x, y) + ((±cos θ ∓ sin θ)/2, (±sin θ ± cos θ)/2).
A certificate is valid if every vertex lies in the closed box and the interiors of the squares
are pairwise disjoint (contact allowed).

## Edge data (`rectangle-edge/v1`, `data/edges/kNN.json`)

    {
      "schema": "rectangle-edge/v1", "k": 14, "edge": "...", "claim": "...",
      "pieces": [ {
        "key": "14.13",             // k.i in order of a (for k ≤ 10: Friedman's piece number of S_(k−1))
        "a0": 3.74843…, "a1": 3.75503…,   // range of a (numeric)
        "a_text": "3.7484348639… ≤ a < 3.7550391",
        "formula": "…" | null,      // in a and b only: "b = f(a)", "a = c" (step), "P(a, b) = 0",
                                    // or "a = A(p), b = B(p)" with the parameter in "param"
        "formula_full": { "a": "…", "b": "…", "constraints": ["…"], "param": "…" } | null,
                                    // full form where "formula" is null (implicit systems)
        "param": "p = tan(θ/2), …" | null,
        "name": "T35" | null,       // name of our type
        "note": "…" | null,         // kind, tilt angles, form of the curve, composition
        "features": { "kind": "...", "angles": n | null, "form": "...", "vars": n | null },
        "source": "friedman" | "grid" | "ours",
        "basis": "…",               // where the piece comes from
        "friedman": ["9.5"] | null, // Friedman's piece numbers it is (or is translated from)
        "witnesses": [ { "file": "certificates/k14/14.13-1.json", "a": "<rational>", "b": "<rational>",
                         "a_float": …, "b_float": … } ],
        "pts": [ [a, b], … ]        // points on the edge, for drawing
      } ]
    }

Pieces run from a = 1 to the diagonal; consecutive pieces join (pts[-1] of a piece equals pts[0] of
the next). Step pieces have a0 = a1; their witnesses, if any, are boxes at that a with b inside the step.

`features.kind`: grid, staggered (staggered family, exact), friedman (Friedman's piece), line45
(±45° type, rigid), rigid (rigid type), mech1 (one-parameter mechanism, b at its stationary point),
mech2 (two-parameter mechanism, Lagrange condition), step (constant a).
`features.form`: line, rational (curve in p = tan(θ/2)), implicit (polynomial system in `vars`
variables), algebraic (Friedman's algebraic curve).
