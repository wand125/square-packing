pub mod bound;
pub mod interval;
pub mod search;
#[cfg(test)]
mod tests {
    use super::{bound::*, interval::*, search::*};
    #[test]
    fn outward_and_underflow() {
        let x = I::p(1.) / I::p(3.);
        assert!(x.lo < 1. / 3. && x.hi > 1. / 3.);
        let x = I::p(f64::from_bits(1)) * I::p(0.5);
        assert!(x.lo <= 0. && x.hi >= f64::from_bits(1));
        let x = I::p(2.).sqrt();
        assert!(x.lo * x.lo < 2. && x.hi * x.hi > 2.);
        let x = ONE / I::new(-1., 1.);
        assert!(x.lo.is_infinite() && x.hi.is_infinite());
    }
    #[test]
    fn corner_and_mirror_use_correlation() {
        for upper in [false, true] {
            let mut b = [I::new(-0.001, 0.001); 6];
            for v in &mut b[3..] {
                *v = if upper {
                    I::new(0.999, 1.)
                } else {
                    I::new(0., 0.001)
                };
            }
            let r = bound(&b, false);
            assert_eq!(r.reason, Reason::Centre);
        }
    }
    #[test]
    fn symmetry_boundary_is_retained() {
        let mut b = root();
        b[0] = I::p(0.25);
        b[1] = I::p(0.25);
        b[2] = I::p(-0.25);
        assert!(!outside(&b));
        b[1] = I::p(0.3);
        assert!(outside(&b));
    }
    #[test]
    fn dyadic_children_and_depth_cap() {
        let root = root();
        let n = Node::root();
        let [a, b] = n.children(2);
        assert_eq!(a.depth(), 1);
        assert_eq!(b.grid[2], 1);
        assert!(a.bounds(root)[2].hi >= b.bounds(root)[2].lo);
        let c = chunk(n, root, 0);
        assert_eq!(c.unresolved.len(), 1);
        assert!(c.frontier.is_empty());
        assert!(c.leaves.is_empty());
    }
    #[test]
    fn wide_centre_is_not_starved() {
        let mut n = Node::root();
        n.levels = [25, 25, 25, 0, 0, 0];
        n.grid = [20000000, 10000000, 18000000, 0, 0, 0];
        let root = root();
        let r = bound(&n.bounds(root), true);
        assert_eq!(r.reason, Reason::Split);
        assert!(choose(&n, root, &r).unwrap() >= 3);
    }
}
