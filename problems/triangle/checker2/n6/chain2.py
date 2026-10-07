"""Second check of the stage links (2-h) and of the triple lemma hypotheses on the final boxes (2-b).

Everything is recomputed from certificates/n6/n6_packing.json (pinwheel), the certificate JSON files and the statements in
certificates/n6/PROOF.md and certificates/n6/triple/LEMMA.md.  Interval arithmetic: mpmath iv (outward rounded); exact parts: Q(sqrt3).

2-h, stage links:
  L1  the pinwheel is C3-symmetric with label map sigma = (0 2 4)(1 3 5): rotating square k by 2pi/3 about the
      centroid gives square sigma(k) exactly (same corner set);
  L2  stage 1: the 4 exclusion boxes of cert_e1_100 are exactly c_k* +- 1/100 for k = 0, 1 and their mirror
      images, with u in [0, 1/200]; 2 atan(1/200) <= 1/100 (so X in {0, 1} with |c - c_X*| <= 1/100, |t| <= 1/100);
  L3  stage 2: partners of X are the labels sharing a C3 image of {0,1,3} with X; every exclusion box of the
      stage-2 certificate lies inside the claimed pose box of one partner (|c - c*| <= 3/250, |t - t*| <= 3/250),
      every partner is covered, and the obstacle box in the certificate header is (1/100, 1/100);
  L4  stage 3: each (X, partner) pair maps by a power of sigma to one of {0,1}, {0,3}, {1,3}; a max-norm box of
      half-width D rotated by 2pi/3 lies in the box of half-width D (1/2 + sqrt3/2); 1/100 and 3/250 both map
      inside 41/2500; DTH stays 3/250 >= max(1/100, 3/250); every stage-3 exclusion box lies inside the claimed
      box of the third square; the obstacle header is (41/2500, 3/250); totals 6 - 1 - ... (< 5, < 4) are checked
      by cellgrid.py.
2-b, lemma hypotheses on the final boxes of each stage-3 case (B&B over the 6 pose variables of squares 1, 3,
  and separately over squares 0, 1):
  H1  tilt bounds DTH <= Phi;
  H2  corner shifts |a_i| <= delta, b_i <= delta (b_i >= 0 is admissibility);
  H3  t in [tau, 1 - tau] and P strictly on the inner side of the outer edge of square 3;
  H4  Step 2 of the lemma: no f-axis separates squares 0 and 1, square 1 is not on the low side of e_0, square 0
      is not on the high side of e_1 (checked over the lemma's own hypothesis box), and e_0.e_1 > 0.
"""
import json
import os
import sys
from fractions import Fraction

from mpmath import iv, mp

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from q3 import Q3  # noqa: E402

iv.prec = 80
mp.prec = 120


def iatan(x):
    # atan is increasing; mpmath atan at 120 bits is accurate far below the 1e-30 widening
    return iv.mpf([mp.atan(mp.mpf(x.a)) - mp.mpf('1e-30'), mp.atan(mp.mpf(x.b)) + mp.mpf('1e-30')])


HERE = os.path.dirname(os.path.abspath(__file__))
# certificates/n6 of problems/triangle (override with N6_CERTS)
N6 = os.environ.get('N6_CERTS', os.path.join(os.path.dirname(os.path.dirname(HERE)), 'certificates', 'n6'))
R3 = iv.sqrt(3)
HALF = Fraction(1, 2)


def I(q):
    if isinstance(q, Q3):
        return iv.mpf(int(q.a.numerator)) / int(q.a.denominator) + \
            (iv.mpf(int(q.b.numerator)) / int(q.b.denominator)) * R3
    q = Fraction(q)
    return iv.mpf(q.numerator) / q.denominator


PI = iv.pi
L = Q3.parse('2+4/3*sqrt3')


def load_pinwheel():
    d = json.load(open(os.path.join(N6, 'n6_packing.json')))
    sq = [[(Q3.parse(x), Q3.parse(y)) for x, y in s] for s in d['squares']]
    cen = [(sum((p[0] for p in s), Q3(0)) * Fraction(1, 4), sum((p[1] for p in s), Q3(0)) * Fraction(1, 4)) for s in sq]
    return sq, cen


SQ, CEN = load_pinwheel()
K6 = [0, 0, 1, 1, 2, 2]          # t* = k pi/6 (checked in L1 via the corner directions)
SIGMA = {0: 2, 2: 4, 4: 0, 1: 3, 3: 5, 5: 1}


def key(p):
    return (p[0].a, p[0].b, p[1].a, p[1].b)


def rot120(p):
    gx, gy = L * HALF, L * Q3(0, Fraction(1, 6))
    dx, dy = p[0] - gx, p[1] - gy
    c, s = Fraction(-1, 2), Q3(0, HALF)
    return (gx + dx * c - dy * s, gy + dx * s + dy * c)


def check_L1():
    ok = True
    for k in range(6):
        img = sorted(key(rot120(p)) for p in SQ[k])
        if img != sorted(key(p) for p in SQ[SIGMA[k]]):
            ok = False
    # corner directions: edge 0->1 of square k has angle k6 * pi/6 mod pi/2
    for k in range(6):
        (x0, y0), (x1, y1) = SQ[k][0], SQ[k][1]
        dx, dy = x1 - x0, y1 - y0
        dirs = {0: [(1, 0), (0, 1), (-1, 0), (0, -1)]}
        c = [Q3(0, HALF), Q3(HALF)]                     # (cos pi/6, sin pi/6)
        cands = {0: [(Q3(1), Q3(0)), (Q3(0), Q3(1)), (Q3(-1), Q3(0)), (Q3(0), Q3(-1))],
                 1: [(Q3(0, HALF), Q3(HALF)), (Q3(-HALF), Q3(0, HALF)), (Q3(0, -HALF), Q3(-HALF)), (Q3(HALF), Q3(0, -HALF))],
                 2: [(Q3(HALF), Q3(0, HALF)), (Q3(0, -HALF), Q3(HALF)), (Q3(-HALF), Q3(0, -HALF)), (Q3(0, HALF), Q3(-HALF))]}
        if not any((dx - a).is_zero() and (dy - b).is_zero() for a, b in cands[K6[k]]):
            ok = False
    return ok


def box_of(k, D, DTH):
    """claimed pose box of label k: centre +- D, t in t* +- DTH (t as an interval)."""
    cx, cy = CEN[k]
    t0 = PI * K6[k] / 6
    return (I(cx) - I(D), I(cx) + I(D)), (I(cy) - I(D), I(cy) + I(D)), (t0 - I(DTH), t0 + I(DTH))


def exc_inside(e, k, D, DTH):
    """exclusion e (x, y, u ranges) inside the claimed box of k (rigorous; t mod pi/2 handled)."""
    _, _, (t0, t1) = box_of(k, D, DTH)
    cx, cy = CEN[k]
    x0, x1 = Q3.parse(e['x'][0]), Q3.parse(e['x'][1])
    y0, y1 = Q3.parse(e['y'][0]), Q3.parse(e['y'][1])
    if not ((x0 - (cx - D)).sign() >= 0 and ((cx + D) - x1).sign() >= 0 and
            (y0 - (cy - D)).sign() >= 0 and ((cy + D) - y1).sign() >= 0):
        return False
    u0, u1 = I(Fraction(e['u'][0])), I(Fraction(e['u'][1]))
    ta, tb = 2 * iatan(u0), 2 * iatan(u1)
    for shift in (0, PI / 2, -PI / 2):        # the square angle has period pi/2
        if ta.a >= (t0 + shift).b and tb.b <= (t1 + shift).a:
            return True
    return False


def triples():
    base = {0, 1, 3}
    out = [base]
    for _ in range(2):
        out.append({SIGMA[k] for k in out[-1]})
    return out


def partners(X):
    return sorted({k for T in triples() if X in T for k in T} - {X})


def check_L2():
    c = json.load(open(os.path.join(N6, 'loc3/cert_e1_100.json')))
    want = []
    for k in (0, 1):
        cx, cy = CEN[k]
        for mx in (cx, L - cx):
            want.append(((mx - Fraction(1, 100), mx + Fraction(1, 100)), (cy - Fraction(1, 100), cy + Fraction(1, 100))))
    got = [((Q3.parse(e['x'][0]), Q3.parse(e['x'][1])), (Q3.parse(e['y'][0]), Q3.parse(e['y'][1]))) for e in c['exclusions']]
    us = [tuple(e['u']) for e in c['exclusions']]

    def kk(b):
        return tuple(key(p) for p in b)
    same = sorted(map(kk, want)) == sorted(map(kk, got))
    u_ok = all(u == ('0', '1/200') for u in us)
    th = (2 * iatan(I(Fraction(1, 200)))).b <= I(Fraction(1, 100)).a
    return dict(boxes_match=same, u_ok=u_ok, angle_le_1_100=bool(th))


def check_L3():
    res = {}
    for X, f in ((1, 'stage2/cert_w_o1.json'), (0, 'stage2/cert_w_o0_p13_auto.json')):
        c = json.load(open(os.path.join(N6, f)))
        P = partners(X)
        cover = []
        for e in c['exclusions']:
            ks = [k for k in P if exc_inside(e, k, Fraction(3, 250), Fraction(3, 250))]
            cover.append(ks)
        st = c['stage']
        res[f] = dict(X=X, partners=P, header_partners=st['partners'], partners_match=P == st['partners'],
                      exclusion_owner=cover,
                      all_boxes_inside=all(cover), all_partners_covered=set(P) <= {k for ks in cover for k in ks},
                      header_obstacle=(st['D_obstacle'], st['DTH']) == ('1/100', '1/100'))
    return res


CASES = {'0,1:3': ('stage2/cert_s3u2.json', (0, 1), 3, (Fraction(7, 200), Fraction(9, 200)), (Fraction(1, 20), Fraction(7, 100), Fraction(3, 100))),
         '0,3:1': ('stage2/cert_o03d.json', (0, 3), 1, (Fraction(7, 200), Fraction(9, 200)), (Fraction(1, 20), Fraction(7, 100), Fraction(3, 100))),
         '1,3:0': ('stage2/cert_o13b.json', (1, 3), 0, (Fraction(1, 20), Fraction(9, 100)), (Fraction(1, 10), Fraction(3, 25), Fraction(3, 50)))}
DOB, THOB = Fraction(41, 2500), Fraction(3, 250)


def check_L4():
    canon = {frozenset(k.split(':')[0].split(',')): k for k in CASES}
    canon = {frozenset(int(x) for x in s): k for s, k in canon.items()}
    maps = {}
    for X in (0, 1):
        for p in partners(X):
            pair = {X, p}
            for r in range(3):
                if frozenset(pair) in canon:
                    maps[f'{X}+{p}'] = dict(case=canon[frozenset(pair)], rotations=r)
                    break
                pair = {SIGMA[k] for k in pair}
            else:
                maps[f'{X}+{p}'] = None
    # rotated max-norm boxes: D (1/2 + sqrt3/2) <= 41/2500 for D = 1/100 and 3/250
    grow = {str(D): bool((I(D) * (1 + R3) / 2).b <= I(Fraction(41, 2500)).a) for D in (Fraction(1, 100), Fraction(3, 250))}
    excl = {}
    for case, (f, obs, third, (D3, T3), _) in CASES.items():
        c = json.load(open(os.path.join(N6, f)))
        st = c['stage']
        excl[case] = dict(inside=[exc_inside(e, third, D3, T3) for e in c['exclusions']],
                          header=(st['obstacles'] == list(obs) and st['partners'] == [third] and
                                  st['D_obstacle'] == '41/2500' and st['DTH'] == '3/250' and
                                  Fraction(st['D_partner']) == D3 and Fraction(st['DTH_partner']) == T3))
    return dict(pair_to_case=maps, rotated_box_fits=grow, DTH_ok=THOB >= Fraction(1, 100), stage3=excl)


# ------------------------------------------------------------ lemma hypotheses (2-b)

def corner(cx, cy, t, sx, sy):
    c, s = iv.cos(t), iv.sin(t)
    return cx + c * sx - s * sy, cy + s * sx + c * sy


def split(box, k):
    lo, hi = box[k]
    m = (lo + hi) / 2
    a, b = list(box), list(box)
    a[k] = (lo, m)
    b[k] = (m, hi)
    return a, b


def bb(box, test, max_nodes=400000):
    """test(env) -> True (proved), False (refuted surely), None (split)."""
    st = [box]
    n = 0
    while st:
        b = st.pop()
        n += 1
        if n > max_nodes:
            return False, n
        env = [iv.mpf([lo, hi]) for lo, hi in b]
        r = test(env)
        if r is True:
            continue
        if r is False:
            return False, n
        w = [float(hi - lo) for lo, hi in b]
        k = w.index(max(w))
        if w[k] < 1e-12:
            return False, n
        st.extend(split(b, k))
    return True, n


def flt(x):
    return (float(x.a), float(x.b))


def pose_box(k, D, DTH):
    (x0, x1), (y0, y1), (t0, t1) = box_of(k, D, DTH)
    return [(float(x0.a), float(x1.b)), (float(y0.a), float(y1.b)), (float(t0.a), float(t1.b))]


Lv = I(L)


def dR(x, y):
    return (R3 * (Lv - x) - y) / 2


def boxes_for(case):
    f, obs, third, (D3, T3), lem = CASES[case]
    b = {}
    for k in (0, 1, 3):
        b[k] = pose_box(k, D3, T3) if k == third else pose_box(k, DOB, THOB)
    return b, lem, (D3, T3)


def check_H(case):
    b, (Phi, delta, tau), (D3, T3) = boxes_for(case)
    out = {}
    dlo, dhi = I(delta).a, I(delta).b
    tlo, thi = I(tau).a, I(tau).b
    one_m_tau_lo, one_m_tau_hi = (1 - I(tau)).a, (1 - I(tau)).b
    out['H1'] = all(DTH <= Phi for DTH in ((T3 if k == CASES[case][2] else THOB) for k in (0, 1, 3)))
    # H2: corner Q_i = c + R(t)(-1/2,-1/2), Q_i* = c* - (1/2, 1/2)
    h2 = {}
    for i in (0, 1):
        Qs = (I(CEN[i][0]) - HALF_I, I(CEN[i][1]) - HALF_I)

        def t2(env, Qs=Qs):
            qx, qy = corner(env[0], env[1], env[2], -HALF_I, -HALF_I)
            a = qx - Qs[0]
            bq = qy - Qs[1]
            if abs(a).b <= dlo and bq.b <= dlo:
                return True
            if abs(a).a > dhi or bq.a > dhi:
                return False
            return None
        h2[i] = bb(b[i], t2)[0]
    out['H2'] = h2

    # H3: t in [tau, 1 - tau], P inner side of the outer edge (P - A).f3 > 0
    def t3(env):
        x1, y1, a1, x3, y3, a3 = env
        Px, Py = corner(x1, y1, a1, HALF_I, HALF_I)
        Dx, Dy = corner(x3, y3, a3, -HALF_I, -HALF_I)
        Ax, Ay = corner(x3, y3, a3, HALF_I, -HALF_I)
        c3, s3 = iv.cos(a3), iv.sin(a3)
        e3 = (-s3, c3)
        f3 = (-c3, -s3)
        t = (Px - Dx) * e3[0] + (Py - Dy) * e3[1]
        inner = (Px - Ax) * f3[0] + (Py - Ay) * f3[1]
        if t.a >= thi and t.b <= one_m_tau_lo and inner.a > 0:
            return True
        if t.b < tlo or t.a > one_m_tau_hi or inner.b <= 0:
            return False
        return None
    ok3, n3 = bb(b[1] + b[3], t3)
    out['H3'] = ok3
    # float range of t for the record
    lo, hi = 9, -9
    import itertools
    for corners in itertools.product(*[(l, h) for l, h in b[1] + b[3]]):
        env = [iv.mpf(v) for v in corners]
        x1, y1, a1, x3, y3, a3 = env
        Px, Py = corner(x1, y1, a1, HALF_I, HALF_I)
        Dx, Dy = corner(x3, y3, a3, -HALF_I, -HALF_I)
        c3, s3 = iv.cos(a3), iv.sin(a3)
        t = float(((Px - Dx) * (-s3) + (Py - Dy) * c3).mid)
        lo, hi = min(lo, t), max(hi, t)
    out['t_range_at_box_corners'] = [round(lo, 4), round(hi, 4)]
    return out


HALF_I = iv.mpf(1) / 2


def check_H4(Phi, delta):
    """Step 2 claims over the lemma hypothesis box (a_i, b_i, p_i for squares 0 and 1)."""
    Q0s = (1 / R3, iv.mpf(0))
    Q1s = (1 + 1 / R3, iv.mpf(0))
    box = [(-float(delta), float(delta)), (0.0, float(delta)), (-float(Phi), float(Phi))] * 2

    def test(env):
        a0, b0, p0, a1, b1, p1 = env
        Q0 = (Q0s[0] + a0, Q0s[1] + b0)
        Q1 = (Q1s[0] + a1, Q1s[1] + b1)
        e0, f0 = (iv.cos(p0), iv.sin(p0)), (-iv.sin(p0), iv.cos(p0))
        e1, f1 = (iv.cos(p1), iv.sin(p1)), (-iv.sin(p1), iv.cos(p1))

        def dot(u, w):
            return u[0] * w[0] + u[1] * w[1]

        def add(*vs):
            return (sum((v[0] for v in vs), iv.mpf(0)), sum((v[1] for v in vs), iv.mpf(0)))
        conds = [
            dot(f0, add(Q1, f1)) - dot(f0, Q0),              # some corner of 1 above f0-low end of 0 -> > 0
            dot(f0, Q0) + 1 - dot(f0, Q1),                   # 0's top above 1's bottom along f0 -> > 0
            dot(f1, add(Q0, f0)) - dot(f1, Q1),
            dot(f1, Q1) + 1 - dot(f1, Q0),
            dot(e0, add(Q1, e1)) - dot(e0, Q0),              # square 1 not on the low side of e0
            dot(e1, Q1) + 1 - dot(e1, Q0),                   # square 0 not on the high side of e1
            dot(e0, e1),
        ]
        if all(c.a > 0 for c in conds):
            return True
        if any(c.b <= 0 for c in conds):
            return False
        return None
    return bb(box, test)[0]


def main():
    out = {'L1_pinwheel_C3': check_L1(), 'L2_stage1': check_L2(), 'L3_stage2': check_L3(), 'L4_stage3': check_L4()}
    out['lemma_hypotheses'] = {case: check_H(case) for case in CASES}
    out['H4_step2'] = {f'{Phi},{d}': check_H4(Phi, d) for Phi, d in ((Fraction(1, 20), Fraction(7, 100)), (Fraction(1, 10), Fraction(3, 25)))}
    def bools(x):
        if isinstance(x, bool):
            yield x
        elif x is None:
            yield False
        elif isinstance(x, dict):
            for k, v in x.items():
                if k not in ('partners', 'header_partners', 'exclusion_owner', 't_range_at_box_corners', 'X',
                             'rotations', 'case'):
                    yield from bools(v)
        elif isinstance(x, list):
            for v in x:
                yield from bools(v)
    out['status'] = 'verified' if all(bools(out)) else 'failed'
    js = json.dumps(out, indent=1, default=str)
    print(js)
    open(os.path.join(HERE, 'out/chain2.json'), 'w').write(js + '\n')


if __name__ == '__main__':
    main()
