pub mod bound;
pub mod dual;
pub mod interval;
pub mod measure;
pub mod search;
#[cfg(test)]
mod tests {
    use super::{bound::*, interval::*, measure, search::*};
    fn init() {
        measure::DATA.get_or_init(|| measure::load("../measure.json", "27/20", 2));
    }
    #[test]
    fn dual_preserves_naive_geometry() {
        for b in [root(), [I::p(0.); 6], [I::p(0.25); 6]] {
            let (r, h, c) = geometry(&b);
            let (rd, hd, cd) = crate::dual::geometry(&b);
            for w in 0..3 {
                for j in 0..3 {
                    assert_eq!((r[w][j].lo, r[w][j].hi), (rd[w][j].v.lo, rd[w][j].v.hi));
                }
                assert_eq!((h[w].lo, h[w].hi), (hd[w].v.lo, hd[w].v.hi));
                assert_eq!((c[w].lo, c[w].hi), (cd[w].v.lo, cd[w].v.hi));
            }
        }
    }
    #[test]
    fn outward_underflow_and_rationals() {
        let x = I::rational(1., 3.);
        assert!(x.lo < 1. / 3. && x.hi > 1. / 3.);
        let x = I::p(f64::from_bits(1)) * I::p(0.5);
        assert!(x.lo <= 0. && x.hi >= f64::from_bits(1));
        let x = I::p(2.).sqrt();
        assert!(x.lo * x.lo < 2. && x.hi * x.hi > 2.);
        let x = ONE / I::new(-1., 1.);
        assert!(x.lo.is_infinite() && x.hi.is_infinite());
    }
    #[test]
    fn symmetry_ties_and_strict_outside() {
        let mut b = root();
        b[0] = I::p(0.25);
        b[1] = I::p(0.25);
        b[2] = I::p(-0.25);
        assert!(!outside(&b));
        b[1] = I::p(0.3);
        assert!(outside(&b));
        b[1] = I::p(0.25);
        b[3] = I::p(0.5);
        assert!(!outside(&b));
    }
    #[test]
    fn dyadic_partition_and_unresolved_leaf() {
        init();
        let root = root();
        let n = Node::root();
        let [a, b] = n.children(2);
        assert_eq!(a.depth(), 1);
        assert_eq!(b.grid[2], 1);
        assert!(a.bounds(root)[2].hi >= b.bounds(root)[2].lo);
        let c = chunk(n, root, 0);
        assert_eq!(c.unresolved.len(), 1);
        assert_eq!(c.leaves.len(), 1);
        assert_eq!(c.leaves[0].result.reason, Reason::Unresolved);
    }
    #[test]
    fn collected_centre_at_both_corners() {
        init();
        for upper in [false, true] {
            let mut b = [I::new(-0.002, 0.002); 6];
            for v in &mut b[3..] {
                *v = I::p(if upper { 1. } else { 0. });
            }
            let r = bound(&b, false);
            assert_eq!(r.reason, Reason::Bound);
            assert!(r.lemmas[1] > 0);
        }
    }
    #[test]
    fn measure_partner_counts_and_inside_rule() {
        init();
        let b = [I::p(0.); 6];
        let y = [I::p(0.5), I::p(0.5), I::p(0.5)];
        // The diagonal direction is nonzero, but the cell is not on a wall support.
        let flags = rule_flags(&b, y, 0);
        assert!(flags[0]);
        let info = &measure::DATA.get().unwrap().receipt;
        assert_eq!(
            info["pair_counts_by_dimension"],
            serde_json::json!([15, 24, 60])
        );
        assert_eq!(info["n_claim"], 25);
    }
}
