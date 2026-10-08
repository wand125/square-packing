# Lower bounds for packing 18–21, 26–32, 39, 45, 53, 55, 56, 69, 70 and 72 unit squares

Let `s(n)` be the least side of a square that holds `n` unit squares with
arbitrary orientations, no two overlapping. This repository contains exact
weighted fractional certificates proving

```
s(26) >= 109/20  = 5.45
s(29) >= 557/100 = 5.57
s(39) >= 13/2    = 6.5
s(53) >= 369/50  = 7.38
s(55) >= 377/50  = 7.54
s(56) >= 381/50  = 7.62
s(69) >= 841/100 = 8.41
s(70) >= 171/20  = 8.55
s(72) >= 861/100 = 8.61
```

and, as a cross-check on the generator, a tenth certificate for `s(40) >= 13/2`
that also follows from the `n = 39` bound by monotonicity.

It also contains certificates of a different kind, rectangle-density
certificates in tokoharu's format built here with his solver, proving

<!-- auto:claims:begin -->
```
s(18) >= 939/200    = 4.695
s(19) >= 1927/400   = 4.8175
s(20) >= 49/10      = 4.9
s(26) >= 2213/400   = 5.5325
s(27) >= 1127/200   = 5.635
s(28) >= 2289/400   = 5.7225
s(29) >= 2319/400   = 5.7975
s(30) >= 47/8       = 5.875
s(31) >= 2381/400   = 5.9525
s(37) >= 257/40     = 6.425
s(38) >= 1309/200   = 6.545
s(39) >= 1327/200   = 6.635
s(40) >= 67/10      = 6.7
s(41) >= 169/25     = 6.76
s(42) >= 2731/400   = 6.8275
s(43) >= 551/80     = 6.8875
s(44) >= 2777/400   = 6.9425
s(51) >= 2977/400   = 7.4425
s(52) >= 1507/200   = 7.535
s(53) >= 3043/400   = 7.6075
s(54) >= 3069/400   = 7.6725
s(55) >= 617/80     = 7.7125
s(56) >= 3113/400   = 7.7825
s(57) >= 1567/200   = 7.835
s(58) >= 789/100    = 7.89
s(59) >= 127/16     = 7.9375
s(66) >= 1677/200   = 8.385
s(67) >= 1691/200   = 8.455
s(68) >= 851/100    = 8.51
s(69) >= 1717/200   = 8.585
s(70) >= 3451/400   = 8.6275
s(71) >= 1737/200   = 8.685
s(72) >= 437/50     = 8.74
s(73) >= 439/50     = 8.78
s(74) >= 3539/400   = 8.8475
s(75) >= 89/10      = 8.9
s(76) >= 357/40     = 8.925
s(77) >= 447/50     = 8.94
s(86) >= 1873/200   = 9.365
s(87) >= 941/100    = 9.41
s(88) >= 3791/400   = 9.4775
s(89) >= 1913/200   = 9.565
s(90) >= 3831/400   = 9.5775
s(91) >= 3859/400   = 9.6475
s(93) >= 1947/200   = 9.735
s(94) >= 1961/200   = 9.805
s(95) >= 49259/5000 = 9.8518
```
<!-- auto:claims:end -->

The `n = 29` certificate supersedes the point certificate above and, by
monotonicity, also gives `s(30), s(31) >= 5.7775`. See
[s(29): a ladder of rectangle-density certificates](#s29-a-ladder-of-rectangle-density-certificates-built-here),
[n = 32 and n = 45](#n--32-and-n--45-rectangle-density-certificates-from-our-own-parents)
and [n = 18 to 28](#n--18-to-28-rectangle-density-certificates-past-the-register).
A further rectangle certificate for `n = 26` reaches a value that
others already hold. They are included as independent certificates of those
values; see [Matching certificates](#matching-certificates).

### Standing rectangle certificates

The highest published rectangle certificate for each `n`. The table is
regenerated on every publication, so it is always current. The sections
further down explain how the certificates were built and list earlier rungs.
"previous record" is the best bound held without our rectangle certificates.
It includes our own point certificates. A certificate also covers every
larger `n` above its total mass.

<!-- auto:standing:begin -->
| `n` | bound | exact | total mass | directory | previous record | kind | verifier nodes |
|---|---|---|---|---|---|---|---|
| 18 | **4.695** | 939/200 | 17.990000 | `rect_n18_L4695` | 4.679000 (jlevy/squares) | record | 25,076,758 |
| 19 | **4.8175** | 1927/400 | 18.990000 | `rect_n19_L48175` | 4.800000 (jlevy/squares) | record | 32,216,311 |
| 20 | **4.9** | 49/10 | 19.990000 | `rect_n20_L49` | 4.850000 (jlevy/squares) | record | 20,862,964 |
| 21 | **4.9875** | 399/80 | 20.999000 | `rect_n21_L49875` | 5.000000 (evand) | match | 45,191,252 |
| 26 | **5.5325** | 2213/400 | 25.990000 | `rect_n26_L55325` | 5.508000 (tokoharu) | record | 19,832,060 |
| 27 | **5.635** | 1127/200 | 26.990000 | `rect_n27_L5635` | 5.508000 (tokoharu) | record | 22,428,190 |
| 28 | **5.7225** | 2289/400 | 27.990000 | `rect_n28_L57225` | 5.511709 (Green) | record | 24,221,209 |
| 29 | **5.7975** | 2319/400 | 28.990000 | `rect_n29_L57975` | 5.710000 (tokoharu) | record | 20,667,842 |
| 30 | **5.875** | 47/8 | 29.990000 | `rect_n30_L5875` | 5.710000 (tokoharu) | record | 25,234,338 |
| 31 | **5.9525** | 2381/400 | 30.990000 | `rect_n31_L59525` | 5.710000 (tokoharu) | record | 19,219,226 |
| 32 | **5.95** | 119/20 | 31.990000 | `rect_n32_L595` | 6.000000 (evand) | match | 5,808,912 |
| 37 | **6.425** | 257/40 | 36.990000 | `rect_n37_L6425` | 6.350603 (Green) | record | 28,286,611 |
| 38 | **6.545** | 1309/200 | 37.990000 | `rect_n38_L6545` | 6.350603 (Green) | record | 24,946,254 |
| 39 | **6.635** | 1327/200 | 38.990000 | `rect_n39_L6635` | 6.500000 (this work) | record | 25,772,759 |
| 40 | **6.7** | 67/10 | 39.990000 | `rect_n40_L67` | 6.500000 (this work) | record | 21,501,387 |
| 41 | **6.76** | 169/25 | 40.990000 | `rect_n41_L676` | 6.500000 (this work) | record | 25,438,093 |
| 42 | **6.8275** | 2731/400 | 41.990000 | `rect_n42_L68275` | 6.567764 (Nagamochi) | record | 28,399,704 |
| 43 | **6.8875** | 551/80 | 42.990000 | `rect_n43_L68875` | 6.656854 (Nagamochi) | record | 36,873,467 |
| 44 | **6.9425** | 2777/400 | 43.990000 | `rect_n44_L69425` | 6.744563 (Nagamochi) | record | 36,809,903 |
| 45 | **6.955** | 1391/200 | 44.990000 | `rect_n45_L6955` | 7.000000 (evand) | match | 15,360,958 |
| 51 | **7.4425** | 2977/400 | 50.990000 | `rect_n51_L74425` | 7.317426 (Green) | record | 22,911,774 |
| 52 | **7.535** | 1507/200 | 51.990000 | `rect_n52_L7535` | 7.380000 (this work) | record | 24,539,623 |
| 53 | **7.6075** | 3043/400 | 52.990000 | `rect_n53_L76075` | 7.380000 (this work) | record | 31,105,567 |
| 54 | **7.6725** | 3069/400 | 53.990000 | `rect_n54_L76725` | 7.403124 (Nagamochi) | record | 28,051,952 |
| 55 | **7.7125** | 617/80 | 54.990000 | `rect_n55_L77125` | 7.540000 (this work) | record | 31,849,467 |
| 56 | **7.7825** | 3113/400 | 55.990000 | `rect_n56_L77825` | 7.620000 (this work) | record | 32,540,810 |
| 57 | **7.835** | 1567/200 | 56.990000 | `rect_n57_L7835` | 7.633250 (Nagamochi) | record | 28,668,321 |
| 58 | **7.89** | 789/100 | 57.990000 | `rect_n58_L789` | 7.708204 (Nagamochi) | record | 31,706,414 |
| 59 | **7.9375** | 127/16 | 58.990000 | `rect_n59_L79375` | 7.782330 (Nagamochi) | record | 38,103,520 |
| 60 | **7.94** | 397/50 | 59.990000 | `rect_n60_L794` | 8.000000 (evand) | match | 32,869,712 |
| 61 | **7.96** | 199/25 | 60.990000 | `rect_n61_L796` | 8.000000 (evand) | match | 20,526,671 |
| 66 | **8.385** | 1677/200 | 65.990000 | `rect_n66_L8385` | 8.289966 (Green) | record | 27,095,146 |
| 67 | **8.455** | 1691/200 | 66.990000 | `rect_n67_L8455` | 8.289966 (Green) | record | 25,217,361 |
| 68 | **8.51** | 851/100 | 67.990000 | `rect_n68_L851` | 8.410000 (this work) | record | 32,919,625 |
| 69 | **8.585** | 1717/200 | 68.990000 | `rect_n69_L8585` | 8.410000 (this work) | record | 30,214,587 |
| 70 | **8.6275** | 3451/400 | 69.990000 | `rect_n70_L86275` | 8.550000 (this work) | record | 38,607,528 |
| 71 | **8.685** | 1737/200 | 70.990000 | `rect_n71_L8685` | 8.550000 (this work) | record | 26,773,005 |
| 72 | **8.74** | 437/50 | 71.990000 | `rect_n72_L874` | 8.610000 (this work) | record | 28,630,683 |
| 73 | **8.78** | 439/50 | 72.990000 | `rect_n73_L878` | 8.615773 (Nagamochi) | record | 27,329,821 |
| 74 | **8.8475** | 3539/400 | 73.990000 | `rect_n74_L88475` | 8.681146 (Nagamochi) | record | 36,661,111 |
| 75 | **8.9** | 89/10 | 74.990000 | `rect_n75_L89` | 8.745967 (Nagamochi) | record | 29,959,986 |
| 76 | **8.925** | 357/40 | 75.990000 | `rect_n76_L8925` | 8.810250 (Nagamochi) | record | 32,186,322 |
| 77 | **8.94** | 447/50 | 76.990000 | `rect_n77_L894` | 8.874008 (Nagamochi) | record | 35,716,875 |
| 78 | **8.965** | 1793/200 | 77.990000 | `rect_n78_L8965` | 9.000000 (evand) | match | 36,841,320 |
| 86 | **9.365** | 1873/200 | 85.990000 | `rect_n86_L9365` | 9.306624 (Nagamochi) | record | 32,172,329 |
| 87 | **9.41** | 941/100 | 86.990000 | `rect_n87_L941` | 9.366600 (Nagamochi) | record | 36,458,927 |
| 88 | **9.4775** | 3791/400 | 87.990000 | `rect_n88_L94775` | 9.426150 (Nagamochi) | record | 30,817,677 |
| 89 | **9.565** | 1913/200 | 88.990000 | `rect_n89_L9565` | 9.485281 (Nagamochi) | record | 32,887,546 |
| 90 | **9.5775** | 3831/400 | 89.990000 | `rect_n90_L95775` | 9.544004 (Nagamochi) | record | 38,413,584 |
| 91 | **9.6475** | 3859/400 | 90.990000 | `rect_n91_L96475` | 9.602325 (Nagamochi) | record | 35,649,266 |
| 93 | **9.735** | 1947/200 | 92.990000 | `rect_n93_L9735` | 9.717798 (Nagamochi) | record | 45,473,527 |
| 94 | **9.805** | 1961/200 | 93.990000 | `rect_n94_L9805` | 9.774964 (Nagamochi) | record | 34,535,827 |
| 95 | **9.8518** | 49259/5000 | 94.990000 | `rect_n95_L98518` | 9.831761 (Nagamochi) | record | 34,416,768 |
<!-- auto:standing:end -->

The previous figures for these cases come from a private communication from
Trevor Green to Erich Friedman, reported in Friedman's survey *Packing Unit
Squares in Squares* (Electronic Journal of Combinatorics, DS7), whose last
revision is dated 14 August 2009. The underlying argument has not been
published. The bounds here are the first to improve them, and they arrive with
certificates anyone can re-check.

| `n` | previously reported | this repository | improvement |
|---|---|---|---|
| 26 | 5.3923 | 5.45 (since improved elsewhere, see below) | +0.0577 |
| 29 | 5.5119 | 5.57 (superseded here by 5.7775, see below) | +0.0581 |
| 32 | 5.7958 | **5.82** (rectangle density, see below) | +0.0242 |
| 39 | 6.3512 | **6.5** | +0.1488 |
| 45 | 6.8310 | **6.8725** (rectangle density, see below) | +0.0415 |
| 53 | 7.3246 | **7.38** | +0.0554 |
| 55 | 7.4807 | **7.54** | +0.0593 |
| 56 | 7.5574 | **7.62** | +0.0626 |
| 69 | 8.3485 | **8.41** | +0.0615 |
| 70 | 8.4162 | **8.55** | +0.1338 |
| 72 | 8.5498 | **8.61** | +0.0602 |
| 40 | 6.4061 | 6.5 (follows from `n = 39`) | +0.0939 |

For `n = 32, 45, 53, 55, 56, 69, 70, 72` the standing figure is Nagamochi's closed form, which
is the strongest independently verified bound the survey records for those
cases; for `n = 26, 29, 39` it is Green's. By monotonicity `s(39) >= 6.5` also
covers `n = 40..44` against the DS7 table and `s(70) >= 8.55` covers `n = 71`.

The `n = 53`, `n = 56`, `n = 69` and `n = 72` certificates carry no further
entries with them. Nagamochi's closed form already exceeds 7.38 from `n = 54`
on, 7.62 from `n = 57` on and 8.61 from `n = 73` on, and this repository's own
`s(70) >= 8.55` covers everything above `n = 69`, so monotonicity gives nothing
there; these four improve their own cases only.

`s(56)` and `s(72)` improve on what our own earlier certificates already gave.
Monotonicity from `s(55) >= 7.54` put `s(56)` at 7.54 and from `s(70) >= 8.55`
put `s(72)` at 8.55; the direct certificates raise those by 0.08 and 0.06.

## n = 26 and n = 29 have since been improved

[tokoharu/square-packing-density-bounds](https://github.com/tokoharu/square-packing-density-bounds)
proves `s(26) >= 1377/250 = 5.508` and `s(29) >= 571/100 = 5.71`, past the two
point certificates here, and by monotonicity those also carry `n = 27, 30, 31`.
We have since carried his method further ourselves: `n = 29` to
`2311/400 = 5.7775`, and `n = 27, 28` to `277/50 = 5.54`. For `n = 26` we
have an independent certificate at his 5.508 but nothing beyond it.

That work generalizes the basis from point masses to uniform densities on
axis-aligned rectangles, D4-symmetrized about the centre, so the quantity a
placement captures is an area integral rather than a sum of point weights. A
point is caught or missed outright; a rectangle is captured in proportion to
the overlap, which gives the optimizer a degree of freedom the point basis does
not have. For `n = 29` it reaches the better bound with *fewer* basis elements
(552 rectangles against 748 atoms here), so the gain is in what each element
can express, not in how many there are.

The certificates here are unaffected as proofs -- they still establish what
they claim -- but for these two cases they are no longer the strongest known.
Both of tokoharu's certificates were re-checked against their verifier,
compiled and run independently, as part of confirming this.

## s(29): a ladder of rectangle-density certificates built here

`certificates/rect_n29_L*/` holds twenty-one certificates in tokoharu's format, each
proving a better lower bound on `s(29)` than his own `571/100 = 5.71`:

| directory | `L` | exact | total mass | budget | verifier nodes |
|---|---|---|---|---|---|
| `rect_n29_L574` | 5.74 | 287/50 | 28.307500 | 29 | 6,220,710 |
| `rect_n29_L57403125` | 5.7403125 | 18369/3200 | 28.312239 | 29 | 6,259,495 |
| `rect_n29_L5740625` | 5.740625 | 1837/320 | 28.292811 | 29 | 6,801,596 |
| `rect_n29_L574125` | 5.74125 | 4593/800 | 28.900000 | 29 | 4,861,306 |
| `rect_n29_L574375` | 5.74375 | 919/160 | 28.317278 | 29 | 6,821,444 |
| `rect_n29_L574625` | 5.74625 | 4597/800 | 28.358148 | 29 | 6,734,510 |
| `rect_n29_L574875` | 5.74875 | 4599/800 | 28.376913 | 29 | 7,091,278 |
| `rect_n29_L575125` | 5.75125 | 4601/800 | 28.414424 | 29 | 7,132,455 |
| `rect_n29_L5751875` | 5.751875 | 9203/1600 | 28.413163 | 29 | 7,326,490 |
| `rect_n29_L57525` | 5.7525 | 2301/400 | 28.418591 | 29 | 7,357,544 |
| `rect_n29_L575375` | 5.75375 | 4603/800 | 28.990000 | 29 | 5,222,853 |
| `rect_n29_L5755` | 5.755 | 1151/200 | 28.990000 | 29 | 5,246,956 |
| `rect_n29_L57575` | 5.7575 | 2303/400 | 28.990000 | 29 | 5,530,431 |
| `rect_n29_L576` | 5.76 | 144/25 | 28.990000 | 29 | 5,470,623 |
| `rect_n29_L57625` | 5.7625 | 461/80 | 28.990000 | 29 | 5,435,964 |
| `rect_n29_L5765` | 5.765 | 1153/200 | 28.990000 | 29 | 5,726,956 |
| `rect_n29_L57675` | 5.7675 | 2307/400 | 28.990000 | 29 | 6,020,892 |
| `rect_n29_L577` | 5.77 | 577/100 | 28.990000 | 29 | 6,180,299 |
| `rect_n29_L57725` | 5.7725 | 2309/400 | 28.990000 | 29 | 6,391,897 |
| `rect_n29_L5775` | 5.775 | 231/40 | 28.990000 | 29 | 6,682,472 |
| **`rect_n29_L57775`** | **5.7775** | **2311/400** | **28.990000** | 29 | 6,974,142 |

The last row is the standing bound: **`s(29) >= 2311/400 = 5.7775`**. Its total
mass is `2899/100 < 30 < 31`, so the same certificate also proves
`s(30) >= 5.7775` and `s(31) >= 5.7775`.

They were produced with tokoharu's solver, driven by `push.py`, the ladder
driver we contributed to his repository
([PR #1](https://github.com/tokoharu/square-packing-density-bounds/pull/1),
[PR #2](https://github.com/tokoharu/square-packing-density-bounds/pull/2), both
merged). Starting from his certified `n = 29` certificate at 5.71, the driver
raises the side one rung at a time, running his `engine.py` search, then his
`certify.py`, and keeping a rung only when the certificate is accepted. The
rungs were 5.73, 5.7325, 5.73375, 5.735, 5.7375, 5.738125, 5.73875, 5.74,
5.7403125, 5.740625, 5.74125, 5.74375, 5.74625, 5.74875, 5.75125 and
5.751875; every one of them was certified before the next was attempted.

The last rung is smaller than the others because the two attempts above it,
at 5.75375 and 5.7525, were both rejected by the solver's own LP residual
check, so the driver halved its step twice, from 1/400 to 1/1600, and the
rung that then certified advances the bound by 1/1600 rather than 1/400.
No tolerance was relaxed to obtain it. The ladder then certified 5.7525 as an
ordinary rung.

### The rungs from 5.75375 on: fixed support, then scaling

Every rung from `5.75375` to `5.7775` came from a second route, which keeps
the parent's rectangles instead of searching for new ones. For each rung the
previous certified rung is the parent. Its rectangles are carried to the new
side with their positions scaled, and his LP is solved again over that fixed
support. Placements that fall short in his screen are added as rows. For
`5.75375` the rows also included 13 counterexamples saved from an earlier
attempt at that side. Once the screen found no violation, every weight was
multiplied by one exact rational factor that brings the total mass to exactly
`2899/100 = 28.99`. This is the scaling step described in the next subsection,
used here with a reserve of 0.01 instead of 0.1. The factor is recorded in
each `certified_candidate.json` under `scaling_experiment` (for `5.7775` it takes
28.890942 to 28.99). The scaled certificate then went through the unmodified
verifier.

This route did not use `push.py`. The reserve is thinner than on the ladder
rungs, 0.01 under the budget rather than about 0.6, but that affects only how
easily the next rung can be found, not the validity of the certificate.

### How the 5.74125 rung was obtained

`5.74125` did not come from the ladder. The search had spent six hours on that
side without converging: its incumbent sat at mass 28.2747354324, and each
further repair round shaved off less than the round before. Rather than keep
minimising, we used the room left under the budget. Every weight of that stalled
incumbent was multiplied by the exact rational

```
289000000000000000000/282747354324056990663
```

which takes the total mass to exactly `289/10 = 28.9`, still strictly below 29.
Scaling every weight by a common factor preserves the covering structure and
raises every captured amount by the same factor, so a placement that fell short
of 1 by less than that factor now clears it. The scaled certificate was then put
through the unmodified verifier, which accepted all 201 angle cases in 538
seconds.

The trade is margin for time: that certificate leaves only 0.1 under the budget
where the 5.740625 rung leaves 0.707. It is a certificate either way — the
budget condition is met — but it is a thinner foundation for the next rung.

**The next rung repaired it.** Restarting the ladder from the scaled certificate,
`5.74375` came back with mass 28.317278, a margin of 0.683 — within a whisker of
the 0.707 the ordinary rungs carry, and 6.8 times the margin it started from. The
thin foundation lasts exactly one rung. That is what makes the scaling step worth
repeating rather than a one-off rescue: it costs one rung of margin to convert a
stalled search into a certificate.

### Checking them

Each directory holds the data the verifier reads and the verifier itself:

| file | meaning |
|---|---|
| `certified_candidate.json` | the certificate: `L`, `B = 9977/10000`, and the rectangles with exact rational densities |
| `certificate_input.txt` | the same data in the text form `verify.cpp` parses, as outward-rounded interval endpoints; its header counts the D4 images of the positive-weight rectangles |
| `certificate_metadata.json` | exact total mass and the SHA-256 of the input |
| `verify.cpp`, `run_verify.py` | tokoharu's interval verifier and its runner, unchanged (MIT; `verify.cpp` SHA-256 `a75140df…`) |
| `verification_summary.json`, `verified_angles.jsonl` | the record of the accepting run: 201 angle cases and every leaf lower bound at least `10001/10000` |

To re-check one (needs `g++`; a few minutes on four cores):

```bash
cd certificates/rect_n29_L576 && python3 run_verify.py --workers 4
```

It ends by writing `verification_summary.json` with `"status": "VERIFIED"`.
That happens only when all 201 angle cases (`r = 0..200`) finish and every
case reports `status: verified` with a leaf lower bound of at least
`10001/10000`. A missing or failed case makes the runner exit nonzero, and it
writes no summary. The runner does not check the budget condition. Check it
from `certificate_metadata.json`: `mass_exact` must be strictly below `n`. The
`n` of a certificate is the one in its directory name, and any larger `n` also
satisfies the condition. For every rectangle certificate here, the
`input_sha256` recorded by the accepting run matches the one in its metadata,
so the bytes verified are the bytes published.

Before publication, every standing certificate (the highest one for each
`n`, including the matching ones) was replayed on a second machine from the
published files alone. Each
`certificate_input.txt` was regenerated from `certified_candidate.json` and
matched byte for byte. The exact mass was recomputed from the rational weights.
The unmodified verifier was run again, and every replay was accepted with the
same node count as the original run. The other rungs were checked for hash
agreement and exact mass.

The argument
behind `verify.cpp` — outward-rounded interval arithmetic, a certified
inscribed-polygon area for each rectangle overlap, derivative bounds over centre
boxes, and the same rational angular net as above — is tokoharu's and is
documented in his repository; nothing in the mathematics is ours. What is ours
is the driver, the machine time, the fixed-support route, the scaling step
described above, and the choice of parents described below.

`src/verify.py` does not read this format: it checks point certificates only.

## n = 32 and n = 45: rectangle-density certificates from our own parents

Two more certificates in the same format and checked by the same unmodified
verifier improve cases nobody had a certificate for. The standing figure for
both was Nagamochi's closed form:

| directory | `L` | exact | total mass | budget | previous | verifier nodes |
|---|---|---|---|---|---|---|
| **`rect_n32_L582`** | **5.82** | **291/50** | 31.990000 | 32 | `1 + sqrt(23)` = 5.795832 | 2,766,145 |
| `rect_n45_L68525` | 6.8525 | 2741/400 | 44.990000 | 45 | `1 + sqrt(34)` = 6.830952 | 7,443,908 |
| `rect_n45_L687` | 6.87 | 687/100 | 44.990000 | 45 | `1 + sqrt(34)` = 6.830952 | 7,995,368 |
| **`rect_n45_L68725`** | **6.8725** | **2749/400** | 44.990000 | 45 | `1 + sqrt(34)` = 6.830952 | 8,174,359 |

Both beat the previous figure exactly: `(5.82 - 1)^2 = 23.2324 > 23` and
`(6.8725 - 1)^2 = 34.48625625 > 34`.

**n = 32.** The first rung, 5.80, took its rectangles from the `n = 29`
certificate at 5.751875 above, scaled to the new side. His LP was solved again
with row generation against the budget of 32. Fixed-support rungs then gave
5.81 and 5.82. For 5.82 the LP solution, at mass 30.325272, was scaled up to
exactly `3199/100` as described above, and the factor is in the file. The
certificate has 54 rectangles of positive weight, each of which stands for its
D4 images.

**n = 45.** No rectangle certificate existed near this size, so the parent is
our point certificate for `n = 39` at 6.5. The positions of its positive-weight
atoms were scaled to the new side and each one was replaced by a small square
support. Wall-anchored supports and a coarse full-container fallback were
added. His LP then optimized from scratch, so no point weight is carried over
as a rectangle weight. The first rung to certify was 6.84. From there,
fixed-support rungs as for `n = 29` raised it through 6.8425, 6.845, 6.8475
and 6.85 to 6.8525, and later in steps of 1/400 to 6.8725. Every rung was
scaled to mass `4499/100` and verified before the next was attempted. Only
6.8525, 6.87 and 6.8725 are published here.

## n = 18 to 28: rectangle-density certificates past the register

Six more certificates, in the same format and checked by the same unmodified
verifier, go past the verified lane of the
[jlevy/squares](https://github.com/jlevy/squares) register (as of its commit
`db3f5f3`, 2026-09-25):

| directory | `L` | exact | total mass | budget | register, verified lane | verifier nodes |
|---|---|---|---|---|---|---|
| **`rect_n18_L469`** | **4.69** | **469/100** | 17.990000 | 18 | 4.679 (jlevy/squares) | 12,577,765 |
| **`rect_n19_L481`** | **4.81** | **481/100** | 18.990000 | 19 | 4.80 (jlevy/squares) | 10,759,911 |
| **`rect_n20_L488`** | **4.88** | **122/25** | 19.990000 | 20 | 4.85 (jlevy/squares) | 7,981,881 |
| `rect_n21_L493` | 4.93 | 493/100 | 20.990000 | 21 | 4.88 (jlevy/squares) | 11,243,723 |
| **`rect_n21_L494`** | **4.94** | **247/50** | 20.990000 | 21 | 4.88 (jlevy/squares) | 8,690,560 |
| **`rect_n27_L554`** | **5.54** | **277/50** | 26.990000 | 27 | 5.508 (tokoharu, by monotonicity) | 11,903,829 |
| **`rect_n28_L554`** | **5.54** | **277/50** | 27.990000 | 28 | 5.508 (tokoharu, by monotonicity) | 20,615,178 |

For `n = 28` the register's reported lane also carries Green's
`2*sqrt(2) + 6/sqrt(5)` = 5.511709, and 5.54 is above that as well. The
`n = 27` certificate has mass 26.99, so it also proves `s(28) >= 5.54`. The
`n = 28` certificate was found separately and is a direct one.

The chains for `n = 18`, `19`, `21` and `28` go back to our own point
certificates for those sizes. `n = 20` started from the `n = 19` rectangle
certificate at 4.62. As for `n = 45`, the positive-weight atoms were
replaced by small rectangle supports, and his LP optimized the weights from
scratch. Each chain then climbed rung by rung. Most rungs used the fixed-support
route described for `n = 29`. Some rungs also added columns: new free-standing
rectangles priced against the LP duals. For `n = 19` and `n = 21` the LP was
first solved by an interior-point method rather than simplex. That changes how
the optimum is found, not the certificate the verifier checks. `n = 27` takes
its rectangles from the `n = 26` certificate below, with fixed support at
side 5.54. Every certificate was scaled to mass exactly `n - 1/100` before
verification, and the factor is in the file.

## Matching certificates

These reach values that other people had already proved. They are included
because they were reached independently and pass the same unmodified verifier.
They do not improve any record.

| directory | `L` | exact | total mass | budget | value already held by | verifier nodes |
|---|---|---|---|---|---|---|
| `rect_n18_L4679` | 4.679 | 4679/1000 | 17.990000 | 18 | jlevy/squares, point certificate (now superseded here by 4.69) | 9,971,192 |
| `rect_n26_L5508` | 5.508 | 1377/250 | 25.990000 | 26 | tokoharu | 19,606,206 |
| `rect_n21_L488` | 4.88 | 122/25 | 20.990000 | 21 | jlevy/squares (now superseded here by 4.94) | 9,136,007 |
| `rect_n28_L5508` | 5.508 | 1377/250 | 27.990000 | 28 | tokoharu, by monotonicity (now superseded here by 5.54) | 18,949,885 |

The `n = 26` certificate is a direct one for `n = 26`, found independently of
tokoharu's. Its last stage fixed a support that had been grown by
free-rectangle pricing and repaired it at 5.508.

## n = 50: certificates past Green's bound, checked with their own verifiers

[`certificates/mixed_n50_L740`](certificates/mixed_n50_L740/README.md) proves

```
s(50) >= 37/5 = 7.4
```

This is above Green's `7.3174260…` by more than `0.0825`. The measure is 553 uniform-density rectangles
with total mass `4999999/100000`, built directly at L = 7.4. Every net angle has coverage `>= 1`, and
the lowest is `1.0000000004…`. It uses the same verifier as `mixed_n65_L835`. The full 201-angle replay
was run again from the published tarball before publication. It supersedes the certificate below.

[`certificates/mixed_n50_L735`](certificates/mixed_n50_L735/README.md) proves

```
s(50) >= 147/20 = 7.35
```

This is above Green's `7.3174260…` by more than `0.0325`. The measure is 499 uniform-density
rectangles with total mass `4999999/100000`. Every net angle has coverage `>= 1`; the lowest is
`1.0000000005…`. It was checked with the verifier shipped in its bundle, and the audit and the
full 201-angle replay were run again from the published tarball before publication.

An earlier certificate, `s(50) >= 3659/500 = 7.318` (`mixed_n50_L7318`, the first past Green's bound here),
was withdrawn on 2 October 2026 because the two above supersede it. It remains in the history of this
repository at commit `b08fb24`.

## n = 65: a certificate past Green's bound

[`certificates/mixed_n65_L835`](certificates/mixed_n65_L835/README.md) proves

```
s(65) >= 167/20 = 8.35
```

This is above Green's `2√2 + 71/13 = 8.2899658…` by more than `0.0600`. The measure is 787
uniform-density rectangles with total mass `6499999/100000`. It was obtained by contracting a
search state at L = 8.40 exactly by `167/168`, then repairing it against counterexamples on the
full net. Every net angle has coverage `>= 1`, and the lowest is `1.0000000004…`. It uses the same
verifier as the n = 50 certificates above. The full 201-angle replay was run again from the
published tarball before publication.

## n = 37: a certificate past Green's bound

[`certificates/mixed_n37_L644`](certificates/mixed_n37_L644/README.md) proves

```
s(37) >= 161/25 = 6.44
```

This is above Green's `2√2 + (113 + 10√3)/37 = 6.3506030…` by more than `0.0893`, and above the
rectangle certificate `rect_n37_L6425`. The measure is 350 uniform-density rectangles with total
mass `3699999/100000`, generated directly at L = 6.44 and repaired on the full net. Every net angle
has coverage `>= 1`, and the lowest is `1.0000000054…`. It uses the same verifier as the n = 50 and
n = 65 certificates. The full 201-angle replay was run again from the published tarball before
publication.

## n = 59: s(59) = 8, the k = 8 case of the k² − 5 series

[`certificates/k2m5_n59_L8`](certificates/k2m5_n59_L8/README.md) proves

```
s(59) = 8
```

(the previous lower bound was 7.93). The cover follows Evan Daniel's line-cover method for s(60) = 8
([evand/square-packing](https://github.com/evand/square-packing), MIT): his LP, format and checkers, with
his s(60) cover as the warm start. It has 26,308 points and 5,240 segments of length 1/50 on the interior
lattice lines, total `1474762899/25000000 = 58.99051596 < 59`, and is exactly D4-invariant. Evan
Daniel's checkers, pinned to an upstream commit by `verify.sh`, accept it: `zmx2 --d4` (6,400 roots),
`zmx2 --full` (51,200 roots, no symmetry), and `zm_mixed --d4 --cert-mode` (102,400 roots at depth 24,
with the single remaining root rerun at depth 34). It has not been reviewed outside this project.

## n = 77: s(77) = 9, the k = 9 case of the k² − 4 series

[`certificates/k2m4_n77_L9`](certificates/k2m4_n77_L9/README.md) proves

```
s(77) = 9
```

(and, by monotonicity, s(78) = 9, already known from Evan Daniel's k² − 3 series). It extends Evan
Daniel's mixed cover for s(60) = 8 ([evand/square-packing](https://github.com/evand/square-packing), MIT)
to the 9 × 9 container by inserting a central band and adding a D4-symmetric band measure; the total
mass is `76.999984600031… < 77`. The cover is checked with Evan Daniel's own checkers, pinned to an
upstream commit by `verify.sh`: `zmx2 --d4` (8,100 roots), `zmx2 --full` (64,800 roots, no symmetry)
and `zm_mixed --d4 --cert-mode` (129,600 roots, rational arithmetic), all with no uncertified root.
It has not been reviewed outside this project.

## n = 66: a structured certificate past the rectangle ladder

[`certificates/mixed_n66_L842`](certificates/mixed_n66_L842/README.md) proves

```
s(66) >= 421/50 = 8.42
```

This is above the rectangle certificate `rect_n66_L8385` (8.385) by `0.035`. The measure is 631
uniform-density rectangles with total mass `6599999/100000`, built from scratch at L = 8.42 from a
structured initial measure (bands at integer distances from the walls, as in the Green-series
certificates) and repaired on the full net. Every net angle has coverage `>= 1`, and the lowest is
`1.0000000009…`. It uses the same verifier as the n = 50 and n = 65 certificates. The full 201-angle
replay was run again from the published tarball before publication.

## n = 76: a structured certificate past the rectangle ladder

[`certificates/mixed_n76_L894`](certificates/mixed_n76_L894/README.md) proves

```
s(76) >= 447/50 = 8.94
```

This is above the rectangle certificate `rect_n76_L8925` (8.925) by `0.015`. The measure is 317
uniform-density rectangles with total mass `7599999/100000`, built from scratch from a structured initial
measure and repaired on the full net. Every net angle has coverage `>= 1`, and the lowest is
`1.0000000005…`. It uses the same verifier as the n = 66, 84 and 85 certificates. The full 201-angle
replay was run again from the published tarball before publication.

## n = 84, 85: certificates past Green's bound

[`certificates/mixed_n84_L940`](certificates/mixed_n84_L940/README.md) and
[`certificates/mixed_n85_L942`](certificates/mixed_n85_L942/README.md) prove

```
s(84) >= 47/5 = 9.4
s(85) >= 471/50 = 9.42
```

Both are above Green's reported bound `2√2 + (247 + 12√2)/41 = 9.2667…` for n = 82–85 (Friedman DS7,
Theorem 9 with k = 9), by `0.133` and `0.153`. The measures are 661 and 587 uniform-density rectangles
with total masses `8399999/100000` and `8499999/100000`, built from scratch from a structured initial
measure and repaired on the full net. Every net angle has coverage `>= 1`; the lowest are
`1.0000000008…` and `1.0000000017…`. They use the same verifier as the n = 50, 65 and 66 certificates.
The full 201-angle replay was run again from each published tarball before publication.

## n = 85: a certificate past the n = 85 certificate above

[`certificates/mixed_n85_L946`](certificates/mixed_n85_L946/README.md) proves

```
s(85) >= 473/50 = 9.46
```

This supersedes `mixed_n85_L942` (9.42) and, by monotonicity, also gives `s(86) >= 9.46` and `s(87) >= 9.46`. It is
above Green's reported bound `9.2667…` for n = 82–85 by `0.193`. The measure was built from scratch from a structured
initial measure and repaired on the full net, with the same verifier as the n = 84 and 85 certificates above. Before
publication the full 201-angle replay was run again from the bundle on a fresh Ubuntu 24.04 machine with only the
README's requirements installed.

## n = 101: a linear certificate past Green's bound

[`certificates/mixed_n101_L1028`](certificates/mixed_n101_L1028/README.md) proves

```
s(101) >= 257/25 = 10.28
```

This is above Green's reported bound for `k = 10` (Friedman DS7, Theorem 9),
`2√2 − 1 + (810 + 18√5)/101 = 10.2467…`, by more than `0.0332`. The measure is linear: 333 point masses,
897 segments and 4 rectangles, total mass `10099999/100000`, checked at all 201 net angles with the verifier of
`mixed_n50_L735` (`unified_linear_verify.cpp`). The full replay was run again from the published tarball before
publication.

## n = 83: a linear certificate past Green's bound

[`certificates/mixed_n83_L935`](certificates/mixed_n83_L935/README.md) proves

```
s(83) >= 187/20 = 9.35
```

This is above Green's reported bound `2√2 + (247 + 12√2)/41 = 9.2667…` for n = 82–85 by more than `0.0833`. The
measure is linear (86 point masses, 222 segments and 774 rectangles, total mass `8299999/100000`), checked at all 201
net angles with the verifier of `mixed_n101_L1028` (`unified_linear_verify.cpp`). The full replay was run again from
the published tarball before publication.

## n = 82: a linear certificate past Green's bound

[`certificates/mixed_n82_L932`](certificates/mixed_n82_L932/README.md) proves

```
s(82) >= 233/25 = 9.32
```

This is above Green's reported bound `2√2 + (247 + 12√2)/41 = 9.2667…` for n = 82 by more than `0.0532`; with the
n = 83, 84 and 85 certificates above, every n in 82–85 now has a verified bound past Green's value. The measure is linear
(86 point masses, 222 segments and 774 rectangles, total mass `8199999/100000`), checked at all 201 net angles with the
verifier of `mixed_n83_L935`. Before publication the full replay was run again from the published tarball on a fresh
Ubuntu 24.04 machine with only the README's requirements installed.

## n = 87, 91, 92: Green-series certificates

| certificate | bound | previous value here | Nagamochi's closed form (reference) |
|---|---|---|---|
| [`mixed_n87_L948`](certificates/mixed_n87_L948/README.md) | `s(87) >= 237/25 = 9.48` | 9.46 (from n = 85) | `1 + √70 = 9.3666…` |
| [`mixed_n91_L970`](certificates/mixed_n91_L970/README.md) | `s(91) >= 97/10 = 9.70` | 9.645 | `1 + √74 = 9.6023…` |
| [`mixed_n92_L975`](certificates/mixed_n92_L975/README.md) | `s(92) >= 39/4 = 9.75` | 9.69 | `1 + √75 = 9.6603…` |

Each was built from scratch from a structured initial measure (bands at integer distances from the walls) and repaired on
the full net, with the same verifier as the n = 84 and 85 certificates. By monotonicity they also give `s(88) >= 9.48`
and `s(93) >= 9.75`. Before publication each full 201-angle replay was run again from its tarball on a fresh Ubuntu 24.04
machine with only the README's requirements installed.

## n = 83: a certificate past the linear one above

[`certificates/mixed_n83_L937`](certificates/mixed_n83_L937/README.md) proves

```
s(83) >= 937/100 = 9.37
```

This supersedes the linear certificate `mixed_n83_L935` (9.35). It is a rectangle density built from scratch from a
structured initial measure and repaired on the full net, with the same verifier as the n = 84 and 85 certificates.
Before publication the full 201-angle replay was run again from the bundle on a fresh Ubuntu 24.04 machine with only
the README's requirements installed.

## n = 87, 90, 92: certificates past Nagamochi's bound

| certificate | bound | Nagamochi's closed form | previous value here | rectangles | lowest coverage |
|---|---|---|---|---:|---|
| [`mixed_n87_L940`](certificates/mixed_n87_L940/README.md) | `s(87) >= 47/5 = 9.40` | `1 + √70 = 9.3666…` | 9.39 | 634 | `1.0000000235` |
| [`mixed_n90_L960`](certificates/mixed_n90_L960/README.md) | `s(90) >= 48/5 = 9.60` | `1 + √73 = 9.5440…` | 9.5675 | 762 | `1.000000000042` |
| [`mixed_n92_L969`](certificates/mixed_n92_L969/README.md) | `s(92) >= 969/100 = 9.69` | `1 + √75 = 9.6603…` | 9.645 | 832 | `1.0000000034` |

Each was obtained from the published certificate for `n − 1` (`rect_n86_L9365`, `rect_n89_L9565`,
`rect_n91_L9645`), read with the budget of `n`, stretched with the walls' bands kept in place
(a central stretch for n = 87, the wall variant for n = 90 and 92), and repaired on the full net.
They use the same verifier as the n = 50 and n = 65 certificates above, and each full 201-angle
replay was run again from the published tarball before publication. The n = 87 certificate
supersedes the earlier one below.

[`certificates/mixed_n87_L939`](certificates/mixed_n87_L939/README.md) proves

```
s(87) >= 939/100 = 9.39
```

This is above Nagamochi's `1 + √70 = 9.3666002…` by more than `0.0233`. The measure is 659
uniform-density rectangles with total mass `8699999/100000`. It was obtained from the n = 86
certificate `rect_n86_L9365`, read with the n = 87 budget and stretched to L = 9.39 by a central
stretch that keeps the wall bands in place, then repaired on the full net. Every net angle has coverage `>= 1`, and the
lowest is `1.0000000058…`. It uses the same verifier as the n = 50 and n = 65 certificates above.
The full 201-angle replay was run again from the published tarball before publication.

## n = 96: 9.96, superseding 9.92

[`certificates/mixed_n96_L996`](certificates/mixed_n96_L996/README.md) proves

```
s(96) >= 249/25 = 9.96
```

This supersedes `mixed_n96_L992` below; the gap to the best known packing (side 10) is now `0.04`. Built from scratch
from a structured initial measure and repaired on the full net, with the same verifier; the pre-publication replay was
run from the bundle on a fresh Ubuntu 24.04 machine with only the README's requirements installed.

## n = 96: a certificate past Nagamochi's closed form

[`certificates/mixed_n96_L992`](certificates/mixed_n96_L992/README.md) proves

```
s(96) >= 248/25 = 9.92
```

This is above Nagamochi's closed form `1 + √79 = 9.8882…` (a reference value: the score lemma behind it is
false, see jlevy/squares#295) by `0.0318`, and above our rectangle bound 9.8518 for n = 96. The measure is 195
uniform-density rectangles with total mass `9599999/100000`, built from scratch from a structured initial
measure and repaired on the full net. Every net angle has coverage `>= 1`; the lowest is `1.0000000004…`. It
uses the same verifier as the n = 84 and 85 certificates. Before publication the full 201-angle replay was run
again from the published tarball on a fresh Ubuntu 24.04 machine with only the README's requirements installed.

## n = 95: a Green-series certificate past Nagamochi's closed form

[`certificates/mixed_n95_L996`](certificates/mixed_n95_L996/README.md) proves

```
s(95) >= 249/25 = 9.96
```

This exceeds our rectangle certificate `rect_n95_L98518` (9.8518) and Nagamochi's closed form `1 + √78 = 9.8317…`
(a reference value). The measure is 438 rectangles, built from scratch from a structured initial measure and repaired
on the full net, with the same verifier as `mixed_n96_L996`; the pre-publication replay was run from the bundle on a
fresh Ubuntu 24.04 machine with only the README's requirements installed.

## n = 94: a Green-series certificate past Nagamochi's closed form

[`certificates/mixed_n94_L992`](certificates/mixed_n94_L992/README.md) proves

```
s(94) >= 248/25 = 9.92
```

This exceeds our rectangle certificate `rect_n94_L9805` (9.805) and Nagamochi's closed form `1 + √77 = 9.7749…`
(a reference value). The measure is 488 rectangles, built from scratch from a structured initial measure and repaired
on the full net, with the same verifier as `mixed_n96_L996`; the pre-publication replay was run from the bundle on a
fresh Ubuntu 24.04 machine with only the README's requirements installed.

## n = 86: a Green-series certificate

[`certificates/mixed_n86_L950`](certificates/mixed_n86_L950/README.md) proves

```
s(86) >= 19/2 = 9.5
```

This exceeds the bound 9.46 that `mixed_n85_L946` gives for n = 86 by monotonicity, our rectangle certificate
`rect_n86_L9365` (9.365), and Nagamochi's closed form `1 + √69 = 9.3066…` (a reference value). The measure is 509
rectangles, built from scratch from a structured initial measure and repaired on the full net, with the same verifier
as `mixed_n96_L996`; the pre-publication replay was run from the bundle on a fresh Ubuntu 24.04 machine with only the
README's requirements installed.

## n = 87: 9.55, superseding 9.48

[`certificates/mixed_n87_L955`](certificates/mixed_n87_L955/README.md) proves

```
s(87) >= 191/20 = 9.55
```

This supersedes `mixed_n87_L948` above and exceeds the bound 9.5 that `mixed_n86_L950` gives for n = 87 by
monotonicity. The measure is 509 rectangles, built from scratch from a structured initial measure and repaired on the
full net, with the same verifier as `mixed_n96_L996`; the pre-publication replay was run from the bundle on a fresh
Ubuntu 24.04 machine with only the README's requirements installed.

## n = 93: a Green-series certificate

[`certificates/mixed_n93_L986`](certificates/mixed_n93_L986/README.md) proves

```
s(93) >= 493/50 = 9.86
```

This exceeds the bound 9.75 that `mixed_n92_L975` gives for n = 93 by monotonicity, our rectangle certificate
`rect_n93_L9735` (9.735), and Nagamochi's closed form `1 + √76 = 9.7178…` (a reference value). The measure is 443
rectangles, built from scratch from a structured initial measure and repaired on the full net, with the same verifier
as `mixed_n96_L996`; the pre-publication replay was run from the bundle on a fresh Ubuntu 24.04 machine with only the
README's requirements installed.

## n = 89: a Green-series certificate past Nagamochi's closed form

[`certificates/mixed_n89_L965`](certificates/mixed_n89_L965/README.md) proves

```
s(89) >= 193/20 = 9.65
```

This exceeds our rectangle certificate `rect_n89_L9565` (9.565) and Nagamochi's closed form `1 + √72 = 9.4853…`
(a reference value). The measure is 416 rectangles, built from scratch from a structured initial measure and repaired
on the full net, with the same verifier as `mixed_n96_L996`; the pre-publication replay was run from the bundle on a
fresh Ubuntu 24.04 machine with only the README's requirements installed.

## n = 52: a Green-series certificate

[`certificates/mixed_n52_L755`](certificates/mixed_n52_L755/README.md) proves

```
s(52) >= 151/20 = 7.55
```

This exceeds our rectangle certificate `rect_n52_L7535` (7.535) and Green's reported bound for k = 7, `7.3174…`
(a reference value). The measure is 455 rectangles, built from scratch from a structured initial measure and repaired
on the full net, with the same verifier as `mixed_n96_L996`; the pre-publication replay was run from the bundle on a
fresh Ubuntu 24.04 machine with only the README's requirements installed.

## n = 75: a Green-series certificate past Nagamochi's closed form

[`certificates/mixed_n75_L892`](certificates/mixed_n75_L892/README.md) proves

```
s(75) >= 223/25 = 8.92
```

This exceeds our rectangle certificate `rect_n75_L89` (8.9) and Nagamochi's closed form `1 + √60 = 8.7459…`
(a reference value). The measure is 340 rectangles, built from scratch from a structured initial measure and repaired
on the full net, with the same verifier as `mixed_n96_L996`; the pre-publication replay was run from the bundle on a
fresh Ubuntu 24.04 machine with only the README's requirements installed.

## n = 51: a Green-series certificate

[`certificates/mixed_n51_L746`](certificates/mixed_n51_L746/README.md) proves

```
s(51) >= 373/50 = 7.46
```

This exceeds our rectangle certificate `rect_n51_L74425` (7.4425) and Green's reported bound for k = 7, `7.3174…`
(a reference value). The measure is 446 rectangles, built from scratch from a structured initial measure and repaired
on the full net, with the same verifier as `mixed_n96_L996`; the pre-publication replay was run from the bundle on a
fresh Ubuntu 24.04 machine with only the README's requirements installed.

## n = 88: 9.60, a Green-series certificate

[`certificates/mixed_n88_L960`](certificates/mixed_n88_L960/README.md) proves

```
s(88) >= 48/5 = 9.6
```

This exceeds the bound 9.55 that `mixed_n87_L955` gives for n = 88 by monotonicity, and Nagamochi's closed form `1 + √71 = 9.4261…` (a reference value). The measure is 443 rectangles, built from scratch from a structured initial measure and repaired on the full net, with the same verifier as `mixed_n96_L996`; the pre-publication replay was run from the bundle on a fresh Ubuntu 24.04 machine with only the README's requirements installed.

## n = 58: 7.905, a Green-series certificate

[`certificates/mixed_n58_L7905`](certificates/mixed_n58_L7905/README.md) proves

```
s(58) >= 1581/200 = 7.905
```

This exceeds our rectangle certificate `rect_n58_L789` (7.89) and Nagamochi's closed form `1 + √45 = 7.7082…` (a reference value). The measure is 319 rectangles, built from scratch from a structured initial measure and repaired on the full net, with the same verifier as `mixed_n96_L996`; the pre-publication replay was run from the bundle on a fresh Ubuntu 24.04 machine with only the README's requirements installed.

## n = 91: 9.75, a Green-series certificate

[`certificates/mixed_n91_L975`](certificates/mixed_n91_L975/README.md) proves

```
s(91) >= 39/4 = 9.75
```

This supersedes `mixed_n91_L970` above. This exceeds our earlier certificate `mixed_n91_L970` (9.7) and Nagamochi's closed form `1 + √74 = 9.6023…` (a reference value). The measure is 457 rectangles, built from scratch from a structured initial measure and repaired on the full net, with the same verifier as `mixed_n96_L996`; the pre-publication replay was run from the bundle on a fresh Ubuntu 24.04 machine with only the README's requirements installed.

## n = 55: 7.728, a Green-series certificate

[`certificates/mixed_n55_L7728`](certificates/mixed_n55_L7728/README.md) proves

```
s(55) >= 966/125 = 7.728
```

This exceeds our rectangle certificate `rect_n55_L77125` (7.7125) and Nagamochi's closed form `1 + √42 = 7.4807…` (a reference value). The measure is 303 rectangles, built from scratch from a structured initial measure and repaired on the full net, with the same verifier as `mixed_n96_L996`; the pre-publication replay was run from the bundle on a fresh Ubuntu 24.04 machine with only the README's requirements installed.

## n = 90: 9.725, a Green-series certificate

[`certificates/mixed_n90_L9725`](certificates/mixed_n90_L9725/README.md) proves

```
s(90) >= 389/40 = 9.725
```

This supersedes `mixed_n90_L960` above. This exceeds our earlier certificate `mixed_n90_L960`, the bound 9.65 that `mixed_n89_L965` gives for n = 90 by monotonicity, and Nagamochi's closed form `1 + √73 = 9.5440…` (a reference value). The measure is 571 rectangles, built from scratch from a structured initial measure and repaired on the full net, with the same verifier as `mixed_n96_L996`; the pre-publication replay was run from the bundle on a fresh Ubuntu 24.04 machine with only the README's requirements installed.

## n = 92: 9.77, a Green-series certificate

[`certificates/mixed_n92_L977`](certificates/mixed_n92_L977/README.md) proves

```
s(92) >= 977/100 = 9.77
```

This supersedes `mixed_n92_L975` above. This exceeds our earlier certificate `mixed_n92_L975` (9.75) and Nagamochi's closed form `1 + √75 = 9.6603…` (a reference value). The measure is 345 rectangles, built from scratch from a structured initial measure and repaired on the full net, with the same verifier as `mixed_n96_L996`; the pre-publication replay was run from the bundle on a fresh Ubuntu 24.04 machine with only the README's requirements installed.

## n = 76: 8.96, a Green-series certificate

[`certificates/mixed_n76_L896`](certificates/mixed_n76_L896/README.md) proves

```
s(76) >= 224/25 = 8.96
```

This supersedes `mixed_n76_L894` above. This exceeds our earlier certificate `mixed_n76_L894` (8.94) and Nagamochi's closed form `1 + √61 = 8.8102…` (a reference value). The measure is 341 rectangles, built from scratch from a structured initial measure and repaired on the full net, with the same verifier as `mixed_n96_L996`; the pre-publication replay was run from the bundle on a fresh Ubuntu 24.04 machine with only the README's requirements installed.

## n = 74: 8.8675, a Green-series certificate

[`certificates/mixed_n74_L88675`](certificates/mixed_n74_L88675/README.md) proves

```
s(74) >= 3547/400 = 8.8675
```

This exceeds our rectangle certificate `rect_n74_L88475` (8.8475) and Nagamochi's closed form `1 + √59 = 8.6811…` (a reference value). The measure is 505 rectangles, built from scratch from a structured initial measure and repaired on the full net, with the same verifier as `mixed_n96_L996`; the pre-publication replay was run from the bundle on a fresh Ubuntu 24.04 machine with only the README's requirements installed.

## n = 71: 8.705, a Green-series certificate

[`certificates/mixed_n71_L8705`](certificates/mixed_n71_L8705/README.md) proves

```
s(71) >= 1741/200 = 8.705
```

This exceeds our rectangle certificate `rect_n71_L8685` (8.685) and Nagamochi's closed form `1 + √56 = 8.4833…` (a reference value). The measure is 471 rectangles, built from scratch from a structured initial measure and repaired on the full net, with the same verifier as `mixed_n96_L996`; the pre-publication replay was run from the bundle on a fresh Ubuntu 24.04 machine with only the README's requirements installed.

## n = 70: 8.6475, a Green-series certificate

[`certificates/mixed_n70_L86475`](certificates/mixed_n70_L86475/README.md) proves

```
s(70) >= 3459/400 = 8.6475
```

This exceeds our rectangle certificate `rect_n70_L86275` (8.6275) and Nagamochi's closed form `1 + √55 = 8.4162…` (a reference value). The measure is 495 rectangles, built from scratch from a structured initial measure and repaired on the full net, with the same verifier as `mixed_n96_L996`; the pre-publication replay was run from the bundle on a fresh Ubuntu 24.04 machine with only the README's requirements installed.

## n = 73: 8.809, a Green-series certificate

[`certificates/mixed_n73_L8809`](certificates/mixed_n73_L8809/README.md) proves

```
s(73) >= 8809/1000 = 8.809
```

This exceeds our rectangle certificate `rect_n73_L878` (8.78) and Nagamochi's closed form `1 + √58 = 8.6158…` (a reference value). The measure is 450 rectangles, built from scratch from a structured initial measure and repaired on the full net, with the same verifier as `mixed_n96_L996`; the pre-publication replay was run from the bundle on a fresh Ubuntu 24.04 machine with only the README's requirements installed.

## n = 96: 9.97, a Green-series certificate

[`certificates/mixed_n96_L997`](certificates/mixed_n96_L997/README.md) proves

```
s(96) >= 997/100 = 9.97
```

This supersedes `mixed_n96_L996` above. This exceeds our earlier certificate `mixed_n96_L996` (9.96) and Nagamochi's closed form `1 + √79 = 9.8882…` (a reference value). The measure is 376 rectangles, built from scratch from a structured initial measure and repaired on the full net, with the same verifier as `mixed_n96_L996`; the pre-publication replay was run from the bundle on a fresh Ubuntu 24.04 machine with only the README's requirements installed.

## n = 69: 8.612, a Green-series certificate

[`certificates/mixed_n69_L8612`](certificates/mixed_n69_L8612/README.md) proves

```
s(69) >= 2153/250 = 8.612
```

This exceeds our rectangle certificate `rect_n69_L8585` (8.585) and Nagamochi's closed form `1 + √54 = 8.3485…` (a reference value). The measure is 556 rectangles, built from scratch from a structured initial measure and repaired on the full net, with the same verifier as `mixed_n96_L996`; the pre-publication replay was run from the bundle on a fresh Ubuntu 24.04 machine with only the README's requirements installed.

## n = 93: 9.88, a Green-series certificate

[`certificates/mixed_n93_L988`](certificates/mixed_n93_L988/README.md) proves

```
s(93) >= 247/25 = 9.88
```

This supersedes `mixed_n93_L986` above. This exceeds our earlier certificate `mixed_n93_L986` (9.86) and Nagamochi's closed form `1 + √76 = 9.7178…` (a reference value). The measure is 501 rectangles, built from scratch from a structured initial measure and repaired on the full net, with the same verifier as `mixed_n96_L996`; the pre-publication replay was run from the bundle on a fresh Ubuntu 24.04 machine with only the README's requirements installed.

## n = 44: 6.9725, a Green-series certificate

[`certificates/mixed_n44_L69725`](certificates/mixed_n44_L69725/README.md) proves

```
s(44) >= 2789/400 = 6.9725
```

This exceeds our rectangle certificate `rect_n44_L69425` (6.9425) and Nagamochi's closed form `1 + √33 = 6.7446…` (a reference value). The measure is 399 rectangles, built from scratch from a structured initial measure and repaired on the full net, with the same verifier as `mixed_n96_L996`; the pre-publication replay was run from the bundle on a fresh Ubuntu 24.04 machine with only the README's requirements installed.

## n = 56: 7.8025, a Green-series certificate

[`certificates/mixed_n56_L78025`](certificates/mixed_n56_L78025/README.md) proves

```
s(56) >= 3121/400 = 7.8025
```

This exceeds our rectangle certificate `rect_n56_L77825` (7.7825) and Nagamochi's closed form `1 + √43 = 7.5574…` (a reference value). The measure is 453 rectangles, built from scratch from a structured initial measure and repaired on the full net, with the same verifier as `mixed_n96_L996`; the pre-publication replay was run from the bundle on a fresh Ubuntu 24.04 machine with only the README's requirements installed.

## n = 84: 9.4075, a Green-series certificate

[`certificates/mixed_n84_L94075`](certificates/mixed_n84_L94075/README.md) proves

```
s(84) >= 3763/400 = 9.4075
```

This supersedes `mixed_n84_L940` above. This exceeds our earlier certificate `mixed_n84_L940` (9.4) and Green's reported bound `9.2667…` (a reference value). The measure is 569 rectangles, built from scratch from a structured initial measure and repaired on the full net, with the same verifier as `mixed_n96_L996`; the pre-publication replay was run from the bundle on a fresh Ubuntu 24.04 machine with only the README's requirements installed.

## n = 67: 8.475, a Green-series certificate

[`certificates/mixed_n67_L8475`](certificates/mixed_n67_L8475/README.md) proves

```
s(67) >= 339/40 = 8.475
```

This exceeds our rectangle certificate `rect_n67_L8455` (8.455) and Green's reported bound `8.2900…` (a reference value). The measure is 485 rectangles, built from scratch from a structured initial measure and repaired on the full net, with the same verifier as `mixed_n96_L996`; the pre-publication replay was run from the bundle on a fresh Ubuntu 24.04 machine with only the README's requirements installed.

## n = 88: 9.6125, a Green-series certificate

[`certificates/mixed_n88_L96125`](certificates/mixed_n88_L96125/README.md) proves

```
s(88) >= 769/80 = 9.6125
```

This supersedes `mixed_n88_L960` above. This exceeds our earlier certificate `mixed_n88_L960` (9.6) and Nagamochi's closed form `1 + √71 = 9.4261…` (a reference value). The measure is 502 rectangles, built from scratch from a structured initial measure and repaired on the full net, with the same verifier as `mixed_n96_L996`; the pre-publication replay was run from the bundle on a fresh Ubuntu 24.04 machine with only the README's requirements installed.

## n = 94: 9.94, a Green-series certificate

[`certificates/mixed_n94_L994`](certificates/mixed_n94_L994/README.md) proves

```
s(94) >= 497/50 = 9.94
```

This supersedes `mixed_n94_L992` above. This exceeds our earlier certificate `mixed_n94_L992` (9.92) and Nagamochi's closed form `1 + √77 = 9.7750…` (a reference value). The measure is 630 rectangles, built from scratch from a structured initial measure and repaired on the full net, with the same verifier as `mixed_n96_L996`; the pre-publication replay was run from the bundle on a fresh Ubuntu 24.04 machine with only the README's requirements installed.

## n = 51: 7.47, a Green-series certificate

[`certificates/mixed_n51_L747`](certificates/mixed_n51_L747/README.md) proves

```
s(51) >= 747/100 = 7.47
```

This supersedes `mixed_n51_L746` above. This exceeds our earlier certificate `mixed_n51_L746` (7.46) and Green's reported bound `7.3174…` (a reference value). The measure is 489 rectangles, built from scratch from a structured initial measure and repaired on the full net, with the same verifier as `mixed_n96_L996`; the pre-publication replay was run from the bundle on a fresh Ubuntu 24.04 machine with only the README's requirements installed.

## n = 75: 8.94, a Green-series certificate

[`certificates/mixed_n75_L894`](certificates/mixed_n75_L894/README.md) proves

```
s(75) >= 447/50 = 8.94
```

This supersedes `mixed_n75_L892` above. This exceeds our earlier certificate `mixed_n75_L892` (8.92) and Nagamochi's closed form `1 + √60 = 8.7460…` (a reference value). The measure is 589 rectangles, built from scratch from a structured initial measure and repaired on the full net, with the same verifier as `mixed_n96_L996`; the pre-publication replay was run from the bundle on a fresh Ubuntu 24.04 machine with only the README's requirements installed.

## n = 72: 8.76, a Green-series certificate

[`certificates/mixed_n72_L876`](certificates/mixed_n72_L876/README.md) proves

```
s(72) >= 219/25 = 8.76
```

This exceeds our rectangle certificate `rect_n72_L874` (8.74) and Nagamochi's closed form `1 + √57 = 8.5498…` (a reference value). The measure is 488 rectangles, built from scratch from a structured initial measure and repaired on the full net, with the same verifier as `mixed_n96_L996`; the pre-publication replay was run from the bundle on a fresh Ubuntu 24.04 machine with only the README's requirements installed.

## n = 57: 7.8725, a Green-series certificate

[`certificates/mixed_n57_L78725`](certificates/mixed_n57_L78725/README.md) proves

```
s(57) >= 3149/400 = 7.8725
```

This exceeds our rectangle certificate `rect_n57_L7835` (7.835) and Nagamochi's closed form `1 + √44 = 7.6332…` (a reference value). The measure is 532 rectangles, built from scratch from a structured initial measure and repaired on the full net, with the same verifier as `mixed_n96_L996`; the pre-publication replay was run from the bundle on a fresh Ubuntu 24.04 machine with only the README's requirements installed.

## n = 43: 6.9075, a Green-series certificate

[`certificates/mixed_n43_L69075`](certificates/mixed_n43_L69075/README.md) proves

```
s(43) >= 2763/400 = 6.9075
```

This exceeds our rectangle certificate `rect_n43_L68875` (6.8875) and Nagamochi's closed form `1 + √32 = 6.6569…` (a reference value). The measure is 358 rectangles, built from scratch from a structured initial measure and repaired on the full net, with the same verifier as `mixed_n96_L996`; the pre-publication replay was run from the bundle on a fresh Ubuntu 24.04 machine with only the README's requirements installed.

## n = 42: 6.8475, a Green-series certificate

[`certificates/mixed_n42_L68475`](certificates/mixed_n42_L68475/README.md) proves

```
s(42) >= 2739/400 = 6.8475
```

This exceeds our rectangle certificate `rect_n42_L68275` (6.8275) and Nagamochi's closed form `1 + √31 = 6.5678…` (a reference value). The measure is 431 rectangles, built from scratch from a structured initial measure and repaired on the full net, with the same verifier as `mixed_n96_L996`; the pre-publication replay was run from the bundle on a fresh Ubuntu 24.04 machine with only the README's requirements installed.

## n = 95: 9.965, a Green-series certificate

[`certificates/mixed_n95_L9965`](certificates/mixed_n95_L9965/README.md) proves

```
s(95) >= 1993/200 = 9.965
```

This supersedes `mixed_n95_L996` above. This exceeds our earlier certificate `mixed_n95_L996` (9.96) and Nagamochi's closed form `1 + √78 = 9.8318…` (a reference value). The measure is 480 rectangles, built from scratch from a structured initial measure and repaired on the full net, with the same verifier as `mixed_n96_L996`; the pre-publication replay was run from the bundle on a fresh Ubuntu 24.04 machine with only the README's requirements installed.

## n = 86: 9.503, a Green-series certificate

[`certificates/mixed_n86_L9503`](certificates/mixed_n86_L9503/README.md) proves

```
s(86) >= 9503/1000 = 9.503
```

This supersedes `mixed_n86_L950` above. This exceeds our earlier certificate `mixed_n86_L950` (9.5) and Nagamochi's closed form `1 + √69 = 9.3066…` (a reference value). The measure is 533 rectangles, built from scratch from a structured initial measure and repaired on the full net, with the same verifier as `mixed_n96_L996`; the pre-publication replay was run from the bundle on a fresh Ubuntu 24.04 machine with only the README's requirements installed.

## n = 69: 8.62, a Green-series certificate

[`certificates/mixed_n69_L862`](certificates/mixed_n69_L862/README.md) proves

```
s(69) >= 431/50 = 8.62
```

This supersedes `mixed_n69_L8612` above. This exceeds our earlier certificate `mixed_n69_L8612` (8.612) and Nagamochi's closed form `1 + √54 = 8.3485…` (a reference value). The measure is 547 rectangles, built from scratch from a structured initial measure and repaired on the full net, with the same verifier as `mixed_n96_L996`; the pre-publication replay was run from the bundle on a fresh Ubuntu 24.04 machine with only the README's requirements installed.

## n = 91: 9.7625, a Green-series certificate

[`certificates/mixed_n91_L97625`](certificates/mixed_n91_L97625/README.md) proves

```
s(91) >= 781/80 = 9.7625
```

This supersedes `mixed_n91_L975` above. This exceeds our earlier certificate `mixed_n91_L975` (9.75) and Nagamochi's closed form `1 + √74 = 9.6023…` (a reference value). The measure is 438 rectangles, built from scratch from a structured initial measure and repaired on the full net, with the same verifier as `mixed_n96_L996`; the pre-publication replay was run from the bundle on a fresh Ubuntu 24.04 machine with only the README's requirements installed.

## n = 76: 8.965, a Green-series certificate

[`certificates/mixed_n76_L8965`](certificates/mixed_n76_L8965/README.md) proves

```
s(76) >= 1793/200 = 8.965
```

This supersedes `mixed_n76_L896` above. This exceeds our earlier certificate `mixed_n76_L896` (8.96) and Nagamochi's closed form `1 + √61 = 8.8102…` (a reference value). The measure is 312 rectangles, built from scratch from a structured initial measure and repaired on the full net, with the same verifier as `mixed_n96_L996`; the pre-publication replay was run from the bundle on a fresh Ubuntu 24.04 machine with only the README's requirements installed.

## n = 90: 9.73, a Green-series certificate

[`certificates/mixed_n90_L973`](certificates/mixed_n90_L973/README.md) proves

```
s(90) >= 973/100 = 9.73
```

This supersedes `mixed_n90_L9725` above. This exceeds our earlier certificate `mixed_n90_L9725` (9.725) and Nagamochi's closed form `1 + √73 = 9.5440…` (a reference value). The measure is 525 rectangles, built from scratch from a structured initial measure and repaired on the full net, with the same verifier as `mixed_n96_L996`; the pre-publication replay was run from the bundle on a fresh Ubuntu 24.04 machine with only the README's requirements installed.

## n = 71: 8.721, a Green-series certificate

[`certificates/mixed_n71_L8721`](certificates/mixed_n71_L8721/README.md) proves

```
s(71) >= 8721/1000 = 8.721
```

This supersedes `mixed_n71_L8705` above. This exceeds our earlier certificate `mixed_n71_L8705` (8.705) and Nagamochi's closed form `1 + √56 = 8.4833…` (a reference value). The measure is 529 rectangles, built from scratch from a structured initial measure and repaired on the full net, with the same verifier as `mixed_n96_L996`; the pre-publication replay was run from the bundle on a fresh Ubuntu 24.04 machine with only the README's requirements installed.

## n = 87: 9.58, a Green-series certificate

[`certificates/mixed_n87_L958`](certificates/mixed_n87_L958/README.md) proves

```
s(87) >= 479/50 = 9.58
```

This supersedes `mixed_n87_L955` above. This exceeds our earlier certificate `mixed_n87_L955` (9.55) and Nagamochi's closed form `1 + √70 = 9.3666…` (a reference value). The measure is 594 rectangles, built from scratch from a structured initial measure and repaired on the full net, with the same verifier as `mixed_n96_L996`; the pre-publication replay was run from the bundle on a fresh Ubuntu 24.04 machine with only the README's requirements installed.

## n = 54: 7.685, a Green-series certificate

[`certificates/mixed_n54_L7685`](certificates/mixed_n54_L7685/README.md) proves

```
s(54) >= 1537/200 = 7.685
```

This exceeds our rectangle certificate `rect_n54_L76725` (7.6725) and Nagamochi's closed form `1 + √41 = 7.4031…` (a reference value). The measure is 364 rectangles, built from scratch from a structured initial measure and repaired on the full net, with the same verifier as `mixed_n96_L996`; the pre-publication replay was run from the bundle on a fresh Ubuntu 24.04 machine with only the README's requirements installed.

## n = 73: 8.813, a Green-series certificate

[`certificates/mixed_n73_L8813`](certificates/mixed_n73_L8813/README.md) proves

```
s(73) >= 8813/1000 = 8.813
```

This supersedes `mixed_n73_L8809` above. This exceeds our earlier certificate `mixed_n73_L8809` (8.809) and Nagamochi's closed form `1 + √58 = 8.6158…` (a reference value). The measure is 462 rectangles, built from scratch from a structured initial measure and repaired on the full net, with the same verifier as `mixed_n96_L996`; the pre-publication replay was run from the bundle on a fresh Ubuntu 24.04 machine with only the README's requirements installed.

## n = 94: 9.95, a Green-series certificate

[`certificates/mixed_n94_L995`](certificates/mixed_n94_L995/README.md) proves

```
s(94) >= 199/20 = 9.95
```

This supersedes `mixed_n94_L994` above. This exceeds our earlier certificate `mixed_n94_L994` (9.94) and Nagamochi's closed form `1 + √77 = 9.7750…` (a reference value). The measure is 853 rectangles, built from scratch from a structured initial measure and repaired on the full net, with the same verifier as `mixed_n96_L996`; the pre-publication replay was run from the bundle on a fresh Ubuntu 24.04 machine with only the README's requirements installed.

## n = 53: 7.6275, a Green-series certificate

[`certificates/mixed_n53_L76275`](certificates/mixed_n53_L76275/README.md) proves

```
s(53) >= 3051/400 = 7.6275
```

This exceeds our rectangle certificate `rect_n53_L76075` (7.6075) and Nagamochi's closed form `1 + √40 = 7.3246…` (a reference value). The measure is 505 rectangles, built from scratch from a structured initial measure and repaired on the full net, with the same verifier as `mixed_n96_L996`; the pre-publication replay was run from the bundle on a fresh Ubuntu 24.04 machine with only the README's requirements installed.

## n = 88: 9.62, a Green-series certificate

[`certificates/mixed_n88_L962`](certificates/mixed_n88_L962/README.md) proves

```
s(88) >= 481/50 = 9.62
```

This supersedes `mixed_n88_L96125` above. This exceeds our earlier certificate `mixed_n88_L96125` (9.6125) and Nagamochi's closed form `1 + √71 = 9.4261…` (a reference value). The measure is 562 rectangles, built from scratch from a structured initial measure and repaired on the full net, with the same verifier as `mixed_n96_L996`; the pre-publication replay was run from the bundle on a fresh Ubuntu 24.04 machine with only the README's requirements installed.

## n = 70: 8.6575, a Green-series certificate

[`certificates/mixed_n70_L86575`](certificates/mixed_n70_L86575/README.md) proves

```
s(70) >= 3463/400 = 8.6575
```

This supersedes `mixed_n70_L86475` above. This exceeds our earlier certificate `mixed_n70_L86475` (8.6475) and Nagamochi's closed form `1 + √55 = 8.4162…` (a reference value). The measure is 513 rectangles, built from scratch from a structured initial measure and repaired on the full net, with the same verifier as `mixed_n96_L996`; the pre-publication replay was run from the bundle on a fresh Ubuntu 24.04 machine with only the README's requirements installed.

## n = 58: 7.935, a Green-series certificate

[`certificates/mixed_n58_L7935`](certificates/mixed_n58_L7935/README.md) proves

```
s(58) >= 1587/200 = 7.935
```

This supersedes `mixed_n58_L7905` above. This exceeds our earlier certificate `mixed_n58_L7905` (7.905) and Nagamochi's closed form `1 + √45 = 7.7082…` (a reference value). The measure is 543 rectangles, built from scratch from a structured initial measure and repaired on the full net, with the same verifier as `mixed_n96_L996`; the pre-publication replay was run from the bundle on a fresh Ubuntu 24.04 machine with only the README's requirements installed.

## n = 67: 8.48, a Green-series certificate

[`certificates/mixed_n67_L848`](certificates/mixed_n67_L848/README.md) proves

```
s(67) >= 212/25 = 8.48
```

This supersedes `mixed_n67_L8475` above. This exceeds our earlier certificate `mixed_n67_L8475` (8.475) and Green's reported bound `8.2900…` (a reference value). The measure is 536 rectangles, built from scratch from a structured initial measure and repaired on the full net, with the same verifier as `mixed_n96_L996`; the pre-publication replay was run from the bundle on a fresh Ubuntu 24.04 machine with only the README's requirements installed.

## n = 84: 9.411, a Green-series certificate

[`certificates/mixed_n84_L9411`](certificates/mixed_n84_L9411/README.md) proves

```
s(84) >= 9411/1000 = 9.411
```

This supersedes `mixed_n84_L94075` above. This exceeds our earlier certificate `mixed_n84_L94075` (9.4075) and Green's reported bound `9.2667…` (a reference value). The measure is 686 rectangles, built from scratch from a structured initial measure and repaired on the full net, with the same verifier as `mixed_n96_L996`; the pre-publication replay was run from the bundle on a fresh Ubuntu 24.04 machine with only the README's requirements installed.

## n = 66: 8.43, a Green-series certificate

[`certificates/mixed_n66_L843`](certificates/mixed_n66_L843/README.md) proves

```
s(66) >= 843/100 = 8.43
```

This supersedes `mixed_n66_L842` above. This exceeds our earlier certificate `mixed_n66_L842` (8.42) and Green's reported bound `8.2900…` (a reference value). The measure is 713 rectangles, built from scratch from a structured initial measure and repaired on the full net, with the same verifier as `mixed_n96_L996`; the pre-publication replay was run from the bundle on a fresh Ubuntu 24.04 machine with only the README's requirements installed.

## n = 18: 4.7, a mixed certificate on a finer angle net

[`certificates/mixed_n18_L470`](certificates/mixed_n18_L470/README.md) proves

```
s(18) >= 47/10 = 4.7
```

This exceeds our rectangle certificate `rect_n18_L4695` (4.695). The measure is 136 rectangles, built from scratch from a structured initial measure and repaired on the full net, with the same verifier as `mixed_n96_L996` and a finer angle net (see the certificate README); the pre-publication replay was run from the bundle on a fresh Ubuntu 24.04 machine with only the README's requirements installed.

## Finer-net improvements: n = 18 and 19

| n | Lower bound | Certificate | Supersedes |
|---|---|---|---|
| 18 | **588/125 = 4.704** | [mixed_n18_L4704](certificates/mixed_n18_L4704/README.md) | mixed_n18_L470 (4.7) |
| 19 | **48229/10000 = 4.8229** | [mixed_n19_L48229](certificates/mixed_n19_L48229/README.md) | rect_n19_L48175 (4.8175) |

Both use rational rectangle measures of mass n - 1/100000 and a finer declared
angle net: n18 uses core 1999/2000 and 832 directions of step 1/2006; n19 uses
core 999/1000 and 416 directions of step 1/1001. Complete bundled proof/replay
records and separate Rust verification receipts are supplied. The READMEs
separate original replay, independent verification and publication metadata
checks; the exact adapted Rust source is included under verification/sqverify-net.
These are lower bounds, not optimality claims.

## n = 29: 5.81, a mixed certificate on a finer angle net

[`certificates/mixed_n29_L581`](certificates/mixed_n29_L581/README.md) proves

```
s(29) >= 581/100 = 5.81
```

This exceeds our rectangle certificate `rect_n29_L57975` (5.7975) and Nagamochi's closed form `1 + √20 = 5.4721…` (a reference value). The measure is 505 rectangles, built from scratch from a structured initial measure and repaired on the full net, with the same verifier as `mixed_n96_L996` and a finer angle net (see the certificate README); before publication the candidate was checked with the independent `sqverify_fast` on a fresh Ubuntu 24.04 machine (see the certificate README).

## n = 20: 4.905, a mixed certificate on a finer angle net

[`certificates/mixed_n20_L4905`](certificates/mixed_n20_L4905/README.md) proves

```
s(20) >= 981/200 = 4.905
```

This exceeds our earlier certificate rect_n20_L49 (4.9) and Nagamochi's closed form `4.6056…` (a reference value). The certificate is a rational rectangle measure of mass 1999999/100000 with core B = 1999/2000 on a declared half-angle net of 832 directions. It is checked with the independently implemented `sqverify_fast` (source and reproduction notes in the bundle); before publication the check was run again on a fresh Ubuntu 24.04 machine (see the certificate README).

## n = 26: 5.545, a mixed certificate on a finer angle net

[`certificates/mixed_n26_L5545`](certificates/mixed_n26_L5545/README.md) proves

```
s(26) >= 1109/200 = 5.545
```

This exceeds our earlier certificate rect_n26_L55325 (5.5325) and Green's reported bound `5.3919…` (a reference value). The certificate is a rational rectangle measure of mass 2599999/100000 with core B = 1999/2000 on a declared half-angle net of 832 directions. It is checked with the independently implemented `sqverify_fast` (source and reproduction notes in the bundle); before publication the check was run again on a fresh Ubuntu 24.04 machine (see the certificate README).

## n = 27: 5.6435, a mixed certificate on a finer angle net

[`certificates/mixed_n27_L56435`](certificates/mixed_n27_L56435/README.md) proves

```
s(27) >= 11287/2000 = 5.6435
```

This exceeds our earlier certificate rect_n27_L5635 (5.635) and Green's reported bound `5.3919…` (a reference value). The certificate is a rational rectangle measure of mass 2699999/100000 with core B = 1999/2000 on a declared half-angle net of 832 directions. It is checked with the independently implemented `sqverify_fast` (source and reproduction notes in the bundle); before publication the check was run again on a fresh Ubuntu 24.04 machine (see the certificate README).

## n = 28: 5.735, a mixed certificate on a finer angle net

[`certificates/mixed_n28_L5735`](certificates/mixed_n28_L5735/README.md) proves

```
s(28) >= 1147/200 = 5.735
```

This exceeds our earlier certificate rect_n28_L57225 (5.7225) and Green's reported bound `5.3919…` (a reference value). The certificate is a rational rectangle measure of mass 2799999/100000 with core B = 999/1000 on a declared half-angle net of 416 directions. It is checked with the independently implemented `sqverify_fast` (source and reproduction notes in the bundle); before publication the check was run again on a fresh Ubuntu 24.04 machine (see the certificate README).

## n = 30: 5.8835, a mixed certificate on a finer angle net

[`certificates/mixed_n30_L58835`](certificates/mixed_n30_L58835/README.md) proves

```
s(30) >= 11767/2000 = 5.8835
```

This exceeds our earlier certificate rect_n30_L5875 (5.875) and Nagamochi's closed form `5.5826…` (a reference value). The certificate is a rational rectangle measure of mass 2999999/100000 with core B = 1999/2000 on a declared half-angle net of 832 directions. It is checked with the independently implemented `sqverify_fast` (source and reproduction notes in the bundle); before publication the check was run again on a fresh Ubuntu 24.04 machine (see the certificate README).

## n = 18: 4.705, a mixed certificate on a finer angle net

[`certificates/mixed_n18_L4705`](certificates/mixed_n18_L4705/README.md) proves

```
s(18) >= 941/200 = 4.705
```

This supersedes `mixed_n18_L4704` above. This exceeds our earlier certificate mixed_n18_L4704 (4.704) and Green's reported bound `4.4452…` (a reference value). The certificate is a rational rectangle measure of mass 1799999/100000 with core B = 4999/5000 on a declared half-angle net of 2073 directions. It is checked with the independently implemented `sqverify_fast` (source and reproduction notes in the bundle); before publication the check was run again on a fresh Ubuntu 24.04 machine (see the certificate README).

## n = 19: 4.825, a mixed certificate on a finer angle net

[`certificates/mixed_n19_L4825`](certificates/mixed_n19_L4825/README.md) proves

```
s(19) >= 193/40 = 4.825
```

This supersedes `mixed_n19_L48229` above. This exceeds our earlier certificate mixed_n19_L48229 (4.8229) and Nagamochi's closed form `4.4641…` (a reference value). The certificate is a rational rectangle measure of mass 1899999/100000 with core B = 4999/5000 on a declared half-angle net of 2073 directions. It is checked with the independently implemented `sqverify_fast` (source and reproduction notes in the bundle); before publication the check was run again on a fresh Ubuntu 24.04 machine (see the certificate README).

## n = 39: 6.65, a mixed certificate on a finer angle net

[`certificates/mixed_n39_L665`](certificates/mixed_n39_L665/README.md) proves

```
s(39) >= 133/20 = 6.65
```

This exceeds our earlier certificate rect_n39_L6635 (6.635) and Green's reported bound `6.3506…` (a reference value). The certificate is a rational rectangle measure of mass 3899999/100000 with core B = 999/1000 on a declared half-angle net of 416 directions. It is checked with the independently implemented `sqverify_fast` (source and reproduction notes in the bundle); before publication the check was run again on a fresh Ubuntu 24.04 machine (see the certificate README).

## n = 41: 6.775, a mixed certificate on a finer angle net

[`certificates/mixed_n41_L6775`](certificates/mixed_n41_L6775/README.md) proves

```
s(41) >= 271/40 = 6.775
```

This exceeds our earlier certificate rect_n41_L676 (6.76) and Nagamochi's closed form `6.4772…` (a reference value). The certificate is a rational rectangle measure of mass 4099999/100000 with core B = 999/1000 on a declared half-angle net of 416 directions. It is checked with the independently implemented `sqverify_fast` (source and reproduction notes in the bundle); before publication the check was run again on a fresh Ubuntu 24.04 machine (see the certificate README).

## n = 31: 5.97, a mixed certificate on a finer angle net

[`certificates/mixed_n31_L597`](certificates/mixed_n31_L597/README.md) proves

```
s(31) >= 597/100 = 5.97
```

This exceeds our earlier certificate rect_n31_L59525 (5.9525) and Nagamochi's closed form `5.6904…` (a reference value). The certificate is a rational rectangle measure of mass 3099999/100000 with core B = 1999/2000 on a declared half-angle net of 832 directions. It is checked with the independently implemented `sqverify_fast` (source and reproduction notes in the bundle); before publication the check was run again on a fresh Ubuntu 24.04 machine (see the certificate README).

## n = 19: 4.8275, a mixed certificate on a finer angle net

[`certificates/mixed_n19_L48275`](certificates/mixed_n19_L48275/README.md) proves

```
s(19) >= 1931/400 = 4.8275
```

This supersedes `mixed_n19_L4825` above. This exceeds our earlier certificate mixed_n19_L4825 (4.825) and Nagamochi's closed form `4.4641…` (a reference value). The certificate is a rational rectangle measure of mass 1899999/100000 with core B = 4999/5000 on a declared half-angle net of 2073 directions. It is checked with the independently implemented `sqverify_fast` (source and reproduction notes in the bundle); before publication the check was run again on a fresh Ubuntu 24.04 machine (see the certificate README).

## n = 28: 5.74, a mixed certificate on a finer angle net

[`certificates/mixed_n28_L574`](certificates/mixed_n28_L574/README.md) proves

```
s(28) >= 287/50 = 5.74
```

This supersedes `mixed_n28_L5735` above. This exceeds our earlier certificate mixed_n28_L5735 (5.735) and Green's reported bound `5.3919…` (a reference value). The certificate is a rational rectangle measure of mass 2799999/100000 with core B = 1999/2000 on a declared half-angle net of 832 directions. It is checked with the independently implemented `sqverify_fast` (source and reproduction notes in the bundle); before publication the check was run again on a fresh Ubuntu 24.04 machine (see the certificate README).

## n = 29: 5.815, a mixed certificate on a finer angle net

[`certificates/mixed_n29_L5815`](certificates/mixed_n29_L5815/README.md) proves

```
s(29) >= 1163/200 = 5.815
```

This supersedes `mixed_n29_L581` above. This exceeds our earlier certificate mixed_n29_L581 (5.81) and Nagamochi's closed form `5.4721…` (a reference value). The certificate is a rational rectangle measure of mass 2899999/100000 with core B = 1999/2000 on a declared half-angle net of 832 directions. It is checked with the independently implemented `sqverify_fast` (source and reproduction notes in the bundle); before publication the check was run again on a fresh Ubuntu 24.04 machine (see the certificate README).

## n = 27: 5.6525, a mixed certificate on a finer angle net

[`certificates/mixed_n27_L56525`](certificates/mixed_n27_L56525/README.md) proves

```
s(27) >= 2261/400 = 5.6525
```

This supersedes `mixed_n27_L56435` above. This exceeds our earlier certificate mixed_n27_L56435 (5.6435) and Green's reported bound `5.3919…` (a reference value). The certificate is a rational rectangle measure of mass 2699999/100000 with core B = 4999/5000 on a declared half-angle net of 2073 directions. It is checked with the independently implemented `sqverify_fast` (source and reproduction notes in the bundle); before publication the check was run again on a fresh Ubuntu 24.04 machine (see the certificate README).

## n = 26: 5.555, a mixed certificate on a finer angle net

[`certificates/mixed_n26_L5555`](certificates/mixed_n26_L5555/README.md) proves

```
s(26) >= 1111/200 = 5.555
```

This supersedes `mixed_n26_L5545` above. This exceeds our earlier certificate mixed_n26_L5545 (5.545) and Green's reported bound `5.3919…` (a reference value). The certificate is a rational rectangle measure of mass 2599999/100000 with core B = 4999/5000 on a declared half-angle net of 2073 directions. It is checked with the independently implemented `sqverify_fast` (source and reproduction notes in the bundle); before publication the check was run again on a fresh Ubuntu 24.04 machine (see the certificate README).

## n = 20: 4.9125, a mixed certificate on a finer angle net

[`certificates/mixed_n20_L49125`](certificates/mixed_n20_L49125/README.md) proves

```
s(20) >= 393/80 = 4.9125
```

This supersedes `mixed_n20_L4905` above. This exceeds our earlier certificate mixed_n20_L4905 (4.905) and Nagamochi's closed form `4.6056…` (a reference value). The certificate is a rational rectangle measure of mass 1999999/100000 with core B = 4999/5000 on a declared half-angle net of 2073 directions. It is checked with the independently implemented `sqverify_fast` (source and reproduction notes in the bundle); before publication the check was run again on a fresh Ubuntu 24.04 machine (see the certificate README). The certificate data are in the release `square-lower-bounds-v1` (see `certificates/mixed_n20_L49125/ASSET.json`).

## n = 27: 5.655, a mixed certificate on a finer angle net

[`certificates/mixed_n27_L5655`](certificates/mixed_n27_L5655/README.md) proves

```
s(27) >= 1131/200 = 5.655
```

This supersedes `mixed_n27_L56525` above. This exceeds our earlier certificate mixed_n27_L56525 (5.6525) and Green's reported bound `5.3919…` (a reference value). The certificate is a rational rectangle measure of mass 2699999/100000 with core B = 4999/5000 on a declared half-angle net of 2073 directions. It is checked with the independently implemented `sqverify_fast` (source and reproduction notes in the bundle); before publication the check was run again on a fresh Ubuntu 24.04 machine (see the certificate README). The certificate data are in the release `square-lower-bounds-v1` (see `certificates/mixed_n27_L5655/ASSET.json`).

## Closed-square endpoint certificate for n = 21

The separate [point-only endpoint bundle](point_n21_L5/README.md) proves
`s(21)=5` by a rational all-position, all-angle computational check and an
explicit boundary-contact argument. Its complete split replay and a fresh
one-command M1 run have passed. Monotonicity also gives `s(n)=5` for `22..25`.
Evan Daniel's earlier mixed-measure proof is acknowledged; priority for the
exact value is not claimed. The same certificate also gives a hypothesis-free Lean 4
proof of `minSide 21 = 5`, kernel-checked through Evan Daniel's zero-margin box tree with only
the standard axioms ([lean/zero-margin/](point_n21_L5/lean/zero-margin/README.md)).

The [point-only s(45) bundle](point_n45_L7/README.md) proves `s(45)=7` with a D4-invariant
point measure of total `44.99999100001… < 45`, checked over every position and angle by
Evan Daniel's unmodified `zmx2` (`VERIFIED-D4`, 4,900 roots, no uncertified box), built from
the pinned upstream commit by `verify.sh`. His mixed-measure proof of the same value came
first; this is a separate points-only route.

The [point-only s(61) bundle](point_n61_L8/README.md) proves `s(61)=8` with a D4-invariant
point measure of total `60.99998780001… < 61`, checked the same way (`VERIFIED-D4`, 6,400
roots, no uncertified box). It was lifted from the s(45) cover by inserting a central band
in each direction and adding mass on the cross bands. `s(61)=8` also follows from Evan
Daniel's earlier mixed-measure proof of `s(60)=8`; this is a separate points-only route.
The earlier tables and instructions below describe the other certificate
families; use the endpoint bundle's own reproduction instructions for this proof.

## How the proof works

Scatter finitely many points in the container and give each a nonnegative
rational weight. If every unit square that fits, at every orientation and
position, covers total weight at least 1, then `n` non-overlapping squares
cover at least `n`. Choose the weights so the total is strictly below `n` and
no such packing exists.

The certificate is the list of points and weights. Checking it means checking
five conditions, of which the fifth — that *every* placement covers mass 1 —
is the one that needs a computer. Two devices make it finite: a shrunken square
of side `B < 1` tested against a rational net of 201 directions, with
`B(1 + D) < 1` so the shrink absorbs the net's angular gap; and a sweep over
regions of centre positions rather than individual points.

This is the weighted fractional unavoidable-set method. It is not ours; see
[Attribution](#attribution).

## Verifying the certificates

### With this repository's checker

Requires Python 3.10+, NumPy.

```bash
pip install -r requirements.txt
python3 src/verify.py certificates/cert_n29_L557.json
```

It prints each condition as it decides it and ends with `VERIFIED`. It accepts
only JSON; a certificate is data, and loading one from a pickle would run
whatever the file contained.

Conditions 1 to 4 are decided exactly in `Fraction`. Condition 5 runs a
branch-and-bound recursion over centre boxes in float64 under a stated error
budget: `EPS = 1e-9` on geometric comparisons, mass threshold `1 + 1e-9`, boxes
not subdivided below `1e-7`. Coordinates stay under 100 in magnitude and each
compared quantity takes at most six floating-point operations, so rounding error
stays near `1e-13`; the mass is a sum of at most `10^4` nonnegative terms below
1, so its error stays near `1e-11`. Weights are rounded *up* to multiples of
`1e-8`, so rounding can only add mass.

Box counts, zero failures in each: 4,811,681 (`n=26`), 2,524,711 (`n=29`),
8,409,303 (`n=39`), 7,531,281 (`n=40`). Counts vary slightly between runs
because the split order is not deterministic; the outcome does not.

### With jlevy/squares' checker

[`jlevy/squares`](https://github.com/jlevy/squares) carries an independent
implementation that decides Condition 5 in exact integers on the weights'
common scale and returns the true minimum over event cells, rather than testing
a threshold in floating point. **It is the stronger check**, and all four
certificates pass it unmodified.

```bash
git clone https://github.com/jlevy/squares.git
cp src/check_with_sqpack.py certificates/*.json squares/
cd squares && python3 check_with_sqpack.py cert_n29_L557.json
```

```
n = 29   L = 557/100 = 5.57
atoms = 748   total mass = 453011/15625 = 28.992704   budget = 29
accepted = True   (13.8s)
  [ok  ] Condition 1 atoms carry the declared symmetry: 748 atoms closed under D4 about the centre
  [ok  ] Condition 2 total mass below n: total 453011/15625 against n = 29
  [ok  ] Condition 3 net reaches pi/4: final half-tangent 83/200, t^2 + 2t - 1 = 89/40000
  [ok  ] Condition 4 containment B(1 + D) < 1: B = 9977/10000, D = 83/40000, B(1 + D) = 399908091/400000000
  [ok  ] Condition 5 every reachable cell carries mass 1: least cell mass 1000003/1000000 at direction 0
=> s(29) >= 557/100 = 5.57
```

Results on one core, single worker:

| `n` | atoms | distinct under `D4` | total mass | margin under `n` | `verify` |
|---|---|---|---|---|---|
| 26 | 1376 | 179 | 646393601/25000000 = 25.855744 | 0.144256 | accepted, 28.2s |
| 29 | 748 | 100 | 453011/15625 = 28.992704 | **0.007296** | accepted, 13.8s |
| 39 | 2724 | 362 | 481487971/12500000 = 38.519038 | 0.480962 | accepted, 73.4s |
| 55 | 3196 | 410 | 1362984297/25000000 = 54.519372 | 0.480628 | accepted, 131.4s |
| 70 | 8060 | 1058 | 108946291/1562500 = 69.725626 | 0.274374 | accepted, 548.5s |
| 40 | 1892 | 250 | 975019903/25000000 = 39.000796 | 0.999204 | accepted, 45.1s |

The `n = 29` margin is the interesting one: the weights land `0.0073` under
budget, close to the ceiling the method allows. That is why `n = 29` was the
hardest of the three to find, while `n = 39` had room to spare.

## Certificate format

Each JSON file carries

| field | meaning |
|---|---|
| `n` | number of unit squares |
| `L` | container side, exact rational string |
| `B` | shrink factor `9977/10000` |
| `net` | the direction net as a rule: `theta_r = 2*atan(r*83/40000)`, `r = 0..200` |
| `atoms` | `[x, y, weight]` triples, exact rational strings |
| `total_mass` | sum of weights |
| `claim`, `verification` | the statement proved and the command that checks it |

The net is stored as a rule rather than a list; the half-angle tangents are
exactly `r * 83/40000`. `src/check_with_sqpack.py` shows the one-line
conversion to the form `jlevy/squares` expects.

## Finding the certificates

`src/lp.py` and `src/certify.py` search for them. The program is a covering
linear program over `D4` orbit representatives, solved with HiGHS through SciPy,
with rows generated by using the Condition 5 sweep as a separation oracle and
columns generated from dual reduced costs. A run is abandoned once the LP
optimum reaches `n`, since further rows only raise it.

```bash
python3 src/certify.py --n 29 --L 557/100
```

Runs are long and memory-hungry; the searches behind these four certificates
took hours each on a 128 GB machine, and `certify.py` checkpoints its own
progress so a run can resume. Those checkpoints are pickles it wrote itself
and are not part of the verification path.

## Attribution

The method is not ours.

- **Walter Stromquist** introduced unavoidable point sets with unit weights
  (unpublished memos 1984–85; *Packing 10 or 11 Unit Squares in a Square*,
  Electron. J. Combin. 10 (2003) #R8).
- **Hiroshi Nagamochi** introduced weighted score systems tuned by hand
  (Electron. J. Combin. 12 (2005) #R37).
- **Sam Burns** and **Gustavo Massaccesi** fractionalized the weights and
  introduced the exact rational direction net with the `B(1 + D) < 1` shrink,
  in August 2026. Our `B = 9977/10000` on 201 directions is a parameter choice
  within their framework.
- **[jlevy/squares](https://github.com/jlevy/squares)** added row generation
  via a separation oracle, dual-priced column generation, and branch-and-bound
  as a second Condition 5 decider, and documents the whole pipeline.

What is ours is the observation that nobody had run this machinery above
`n = 21`, the search runs, and the certificates. [`docs/prior-art-method.md`](docs/prior-art-method.md)
breaks the method into six components and attributes each;
[`docs/prior-art-results.md`](docs/prior-art-results.md) records the search for
prior publication of the bounds themselves. Japanese originals are alongside as
`*.ja.md`.

If any attribution here is wrong, please open an issue and we will correct it.

## Layout

```
certificates/   the ten point certificates as JSON, and rect_n*_L*/ in tokoharu's format
src/verify.py            our checker
src/check_with_sqpack.py adapter for the jlevy/squares checker
src/lp.py, src/certify.py the search
docs/lower-bounds.md      write-up of the argument and the numbers
docs/prior-art-method.md  which parts of the method are prior art, and whose
docs/prior-art-results.md search for prior publication of these bounds
docs/prior-art-*.ja.md    Japanese originals of the two notes above
```

## Status

Computer-assisted certificates. The point certificates are checked by two
independent implementations. The rectangle certificates are checked by
tokoharu's verifier, which was run again on a second machine for the standing
ones (see above). None of them has been peer reviewed. [jlevy/squares](https://github.com/jlevy/squares)
records the point bounds for `n = 39, 40, 53, 55, 56, 69, 70, 72` in its
frontier register, in both the reported and the verified lane, after an exact
replay of these files with its own checker (evidence
`E-wand125-point-source-replay`, 2026-09-22). As of its commit `db3f5f3`
(2026-09-25), the register does not yet include the rectangle certificates
here.

Parts of this work were produced with AI assistance under human direction.

## License

MIT. See `LICENSE`.
