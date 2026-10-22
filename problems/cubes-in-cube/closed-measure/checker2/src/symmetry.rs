//! Floating orbit representatives for validation only. Certification uses
//! the exact strict box predicate in geometry, never these floating maps.
use std::f64::consts::{FRAC_PI_2, TAU};
pub const PERMUTATIONS: [[usize; 3]; 6] = [
    [0, 1, 2],
    [0, 2, 1],
    [1, 0, 2],
    [1, 2, 0],
    [2, 0, 1],
    [2, 1, 0],
];
pub fn image(
    r: [[f64; 3]; 3],
    u: [f64; 3],
    perm: [usize; 3],
    mask: usize,
) -> ([[f64; 3]; 3], [f64; 3]) {
    let mut rr =
        std::array::from_fn(|w| r[perm[w]].map(|v| if mask & (1 << w) == 0 { v } else { -v }));
    let uu = std::array::from_fn(|w| {
        if mask & (1 << w) == 0 {
            u[perm[w]]
        } else {
            1. - u[perm[w]]
        }
    });
    let inversions = (0..3)
        .map(|i| (i + 1..3).filter(|&j| perm[i] > perm[j]).count())
        .sum::<usize>();
    if (inversions + mask.count_ones() as usize) % 2 != 0 {
        // Right cube reflection restores determinant +1 without changing Q.
        for row in &mut rr {
            row[0] = -row[0];
        }
    }
    (rr, uu)
}
pub fn euler(r: [[f64; 3]; 3], u: [f64; 3]) -> [f64; 6] {
    let sb = r[0][2].hypot(r[1][2]);
    let b = sb.atan2(r[2][2]);
    let (a, g) = if sb == 0. {
        // At either Euler pole choose gamma = 0.
        (
            (if r[2][2] >= 0. { r[1][0] } else { -r[1][0] }).atan2(if r[2][2] >= 0. {
                r[0][0]
            } else {
                -r[0][0]
            }),
            0.,
        )
    } else {
        (r[1][2].atan2(r[0][2]), r[2][1].atan2(-r[2][0]))
    };
    // Right quarter turns commute with all world symmetries.
    [
        a.rem_euclid(TAU),
        b,
        g.rem_euclid(FRAC_PI_2),
        u[0],
        u[1],
        u[2],
    ]
}
pub fn canonical(r: [[f64; 3]; 3], u: [f64; 3]) -> [f64; 6] {
    let mask = (0..3).fold(0, |m, w| m | if u[w] > 0.5 { 1 << w } else { 0 });
    let (r, u) = image(r, u, [0, 1, 2], mask);
    let mut perm = [0, 1, 2];
    perm.sort_by(|&i, &j| u[i].total_cmp(&u[j]));
    let (r, u) = image(r, u, perm, 0);
    euler(r, u)
}
