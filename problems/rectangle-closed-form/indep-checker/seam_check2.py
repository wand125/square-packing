"""Second-system check of the rectangle seam certificates (TASK_INDEP_SEAM.md items 1-5 and 7; item 6 from the
leaf-replay reports of seamleaf). Written from TASK_INDEP_SEAM.md, problems/closed-form/SPEC.md (sections 3, 4, 6)
and the rectangle draft spec section 5 only; first-system code (run4d, check_record4d, seam_loop, seam_fix_pieces,
split_driver, make_seam_family, r5_band_exact, m25_paths) not read. Exact rationals throughout.

Measures are compared as line densities: every F row is a vertical or horizontal segment with total mass m, i.e.
density m/length on its support; on each line the densities are summed on the open intervals between all endpoints
(SPEC 3.2). A vertical line belongs to x-range [lo, hi) when lo <= x < hi; horizontal lines are clipped to [lo, hi].

usage: python3 seam_check2.py INPUTS_DIR [--leaf-reports DIR] [--pairs P1,P2] [--out report.json]
"""
import json
import os
import sys
from fractions import Fraction as F
from heapq import heappop, heappush

S_SEAM, D_BAND = F(5), F(2, 5)
WINDOW = (F(17, 4), F(27, 4), F(0), F(13, 5))
U_CUTS = [F(j, 32) for j in range(-13, 15)]
PITCH = F(1, 10)


# ------------------------------------------------------------------ measures as line densities

class Measure:
    def __init__(self):
        self.lines = {}          # ('v', x) or ('h', y) -> list of (lo, hi, density)

    @staticmethod
    def from_rows(rows, where):
        m = Measure()
        for r in rows:
            ax, ay, bx, by, mass = (F(v) for v in r)
            if mass < 0:
                raise ValueError(f'{where}: negative mass {r}')
            if ax == bx and ay == by:
                if mass != 0:
                    raise ValueError(f'{where}: point mass {r}')
                continue
            if ax == bx:
                key, lo, hi = ('v', ax), min(ay, by), max(ay, by)
            elif ay == by:
                key, lo, hi = ('h', ay), min(ax, bx), max(ax, bx)
            else:
                raise ValueError(f'{where}: segment not axis-parallel {r}')
            if mass:
                m.lines.setdefault(key, []).append((lo, hi, mass / (hi - lo)))
        m.normalize()
        return m

    def normalize(self):
        out = {}
        for key, segs in self.lines.items():
            pts = sorted({p for lo, hi, _ in segs for p in (lo, hi)})
            pieces = []
            for a, b in zip(pts, pts[1:]):
                d = sum(dd for lo, hi, dd in segs if lo <= a and b <= hi)
                if d:
                    if pieces and pieces[-1][1] == a and pieces[-1][2] == d:
                        pieces[-1] = (pieces[-1][0], b, d)
                    else:
                        pieces.append((a, b, d))
            if pieces:
                out[key] = pieces
        self.lines = out
        return self

    def shift(self, dx):
        m = Measure()
        for (kind, c), segs in self.lines.items():
            if kind == 'v':
                m.lines[('v', c + dx)] = list(segs)
            else:
                m.lines[('h', c)] = [(lo + dx, hi + dx, d) for lo, hi, d in segs]
        return m

    def restrict_x(self, lo_x, hi_x):
        m = Measure()
        for (kind, c), segs in self.lines.items():
            if kind == 'v':
                if lo_x <= c < hi_x:
                    m.lines[('v', c)] = list(segs)
            else:
                cl = [(max(lo, lo_x), min(hi, hi_x), d) for lo, hi, d in segs if min(hi, hi_x) > max(lo, lo_x)]
                if cl:
                    m.lines[('h', c)] = cl
        return m.normalize()

    def add(self, other):
        m = Measure()
        for src in (self, other):
            for k, segs in src.lines.items():
                m.lines.setdefault(k, []).extend(segs)
        return m.normalize()

    def mass(self):
        return sum((hi - lo) * d for segs in self.lines.values() for lo, hi, d in segs)

    def density_at(self, key, lo, hi):
        """density on the open interval (lo, hi), assumed inside one piece of the common refinement"""
        for a, b, d in self.lines.get(key, []):
            if a <= lo and hi <= b:
                return d
        return F(0)

    def compare(self, other, keys_filter=None, open_x=None):
        """(all >=, all ==) of self against other on every line (optionally a filter on keys, and for horizontal
        lines an open x-interval)."""
        ge = eq = True
        for key in set(self.lines) | set(other.lines):
            if keys_filter and not keys_filter(key):
                continue
            pts = sorted({p for src in (self, other) for a, b, _ in src.lines.get(key, []) for p in (a, b)})
            if key[0] == 'h' and open_x:
                pts = sorted({p for p in pts if open_x[0] < p < open_x[1]} | {open_x[0], open_x[1]})
            for a, b in zip(pts, pts[1:]):
                x, y = self.density_at(key, a, b), other.density_at(key, a, b)
                if x < y:
                    ge = False
                if x != y:
                    eq = False
        return ge, eq


def profile(fam_json):
    """one bottom-wall period of an interval family: T at delta = 0 restricted to x in [3, 4), shifted to [0, 1)"""
    return Measure.from_rows(fam_json['T'], 'T').restrict_x(F(3), F(4)).shift(F(-3))


def periodic(P, starts):
    m = Measure()
    for s in starts:
        m = m.add(P.shift(s))
    return m


# ------------------------------------------------------------------ items 1-3

def seam_family_checks(fam, P, Pp, name):
    """item 1 for one seam family: format, outside [S, S+1) exactly 3 periods of P and of P', e."""
    out = {'name': name, 'notes': []}
    ok = True
    for k, want in (('d0', None), ('d1', None), ('UA', '9/5')):
        if k not in fam:
            ok = False; out['notes'].append(f'missing {k}')
    if F(fam['UA']) != F(9, 5):
        ok = False; out['notes'].append('UA is not 9/5')
    if fam.get('T') or fam.get('V'):
        ok = False; out['notes'].append('T or V not empty')
    if 'U' in fam:
        ok = False; out['notes'].append('U present (standard quadrant expected)')
    seam = fam.get('seam', {})
    if not (F(seam.get('S', -1)) == S_SEAM and seam.get('n') == 1):
        ok = False; out['notes'].append(f'seam S/n {seam.get("S")}/{seam.get("n")}')
    M = Measure.from_rows(fam['F'], name)
    left = M.restrict_x(F(2), S_SEAM)
    trans = M.restrict_x(S_SEAM, S_SEAM + 1)
    right = M.restrict_x(S_SEAM + 1, F(9))
    outside = M.restrict_x(F(-10**6), F(2)).add(M.restrict_x(F(9), F(10**6)))
    eq_left = left.compare(periodic(P, [F(2), F(3), F(4)]))[1]
    eq_right = right.compare(periodic(Pp, [F(6), F(7), F(8)]))[1]
    whole = left.add(trans).add(right).compare(M)[1]
    if not (eq_left and eq_right and whole and not outside.lines):
        ok = False
    e = trans.mass() - P.mass()
    out.update({'left_is_3P': eq_left, 'right_is_3Pp': eq_right, 'nothing_outside_[2,9)': not outside.lines,
                'pieces_add_up': whole, 'e': e, 'e_recorded_in_family': seam.get('extra'), 'ok': ok,
                'mass_P': P.mass(), 'mass_Pp': Pp.mass()})
    return out, M, trans


def band_check(trans, P, Pp):
    """item 2: transition >= P (shifted to [S, S+1)) on x < S + d, >= P' on x > S + 1 - d, pointwise densities"""
    P5, Pp5 = P.shift(S_SEAM), Pp.shift(S_SEAM)
    lb, rb = S_SEAM + D_BAND, S_SEAM + 1 - D_BAND
    lv = trans.compare(P5, keys_filter=lambda k: k[0] == 'v' and S_SEAM <= k[1] < lb)[0]
    lh = trans.compare(P5, keys_filter=lambda k: k[0] == 'h', open_x=(S_SEAM, lb))[0]
    rv = trans.compare(Pp5, keys_filter=lambda k: k[0] == 'v' and rb < k[1] < S_SEAM + 1)[0]
    rh = trans.compare(Pp5, keys_filter=lambda k: k[0] == 'h', open_x=(rb, S_SEAM + 1))[0]
    return {'left_vertical': lv, 'left_horizontal': lh, 'right_vertical': rv, 'right_horizontal': rh,
            'ok': lv and lh and rv and rh}


def dominates(fa, fb, Ma, Mb):
    """fa >= fb as families: same d0, d1, UA, empty T and V, no U, F measure >= pointwise"""
    same = all(F(fa[k]) == F(fb[k]) for k in ('d0', 'd1', 'UA')) and not fa.get('T') and not fb.get('T') \
        and not fa.get('V') and not fb.get('V') and 'U' not in fa and 'U' not in fb
    ge, eq = Ma.compare(Mb)
    return same and ge, eq


# ------------------------------------------------------------------ items 4, 5

def wmax_ge(u0, u1):
    """max over [u0, u1] of w(u) = (c + |s|)/2, as ('rat', value) or ('sqrt2half',)"""
    a, b = (abs(u0), abs(u1)) if u0 >= 0 or u1 <= 0 else (F(0), max(abs(u0), abs(u1)))
    a, b = min(a, b), max(a, b)
    if a * a + 2 * a - 1 <= 0 <= b * b + 2 * b - 1:     # sqrt 2 - 1 in [a, b]
        return ('sqrt2half',)
    def w(t):
        d = 1 + t * t
        return ((1 - t * t) + 2 * t) / d / 2
    return ('rat', max(w(a), w(b)))


def ge_w(lhs_rat, wm, rhs):
    """lhs + wmax >= rhs, exactly"""
    gap = rhs - lhs_rat
    if wm[0] == 'rat':
        return wm[1] >= gap
    return gap <= 0 or 2 * gap * gap <= 1           # sqrt2/2 >= gap > 0  <=>  1/2 >= gap^2


def le_w(lhs_rat, wm, rhs):
    """lhs - wmax <= rhs"""
    gap = lhs_rat - rhs
    if wm[0] == 'rat':
        return gap <= wm[1]
    return gap <= 0 or 2 * gap * gap <= 1


def cuts(lo, hi, step):
    out = [lo]
    while out[-1] + step < hi:
        out.append(out[-1] + step)
    out.append(hi)
    return out


def r5_roots():
    xs, ys = cuts(WINDOW[0], WINDOW[1], PITCH), cuts(WINDOW[2], WINDOW[3], PITCH)
    allr, touch = 0, []
    for x0, x1 in zip(xs, xs[1:]):
        for y0, y1 in zip(ys, ys[1:]):
            for u0, u1 in zip(U_CUTS, U_CUTS[1:]):
                allr += 1
                wm = wmax_ge(u0, u1)
                if ge_w(x1, wm, S_SEAM + D_BAND) and le_w(x0, wm, S_SEAM + 1 - D_BAND):
                    touch.append((x0, x1, y0, y1, u0, u1))
    return allr, touch


def record_roots(path):
    out = []
    with open(path) as f:
        for line in f:
            if line.startswith('{"header"'):
                continue
            i = line.index('"root"')
            j = line.index('[', i)
            k = line.index(']', j)
            out.append(tuple(F(v.strip().strip('"')) for v in line[j + 1:k].split(',')))
    return out


def coverage(pieces, roots, d0, d1):
    """every piece inside one root x [d0, d1], pieces pairwise interior-disjoint, volumes add up per root"""
    index = {}
    for r in roots:
        index.setdefault((r[0], r[2], r[4]), []).append(r)
    by_root = {r: [] for r in roots}
    outside = 0
    xs = sorted({r[0] for r in roots}); ys = sorted({r[2] for r in roots}); us = sorted({r[4] for r in roots})
    import bisect
    for p in pieces:
        if not (d0 <= p[6] < p[7] <= d1):
            outside += 1; continue
        # the root containing p has the largest grid start <= p's lower corner
        cand = None
        ix = bisect.bisect_right(xs, p[0]) - 1; iy = bisect.bisect_right(ys, p[2]) - 1; iu = bisect.bisect_right(us, p[4]) - 1
        if min(ix, iy, iu) >= 0:
            for r in index.get((xs[ix], ys[iy], us[iu]), []):
                if r[0] <= p[0] and p[1] <= r[1] and r[2] <= p[2] and p[3] <= r[3] and r[4] <= p[4] and p[5] <= r[5]:
                    cand = r
        if cand is None:
            outside += 1
        else:
            by_root[cand].append(p)
    overlap = vol_bad = empty = 0
    for r, ps in by_root.items():
        if not ps:
            empty += 1; continue
        vr = (r[1] - r[0]) * (r[3] - r[2]) * (r[5] - r[4]) * (d1 - d0)
        vp = sum((p[1] - p[0]) * (p[3] - p[2]) * (p[5] - p[4]) * (p[7] - p[6]) for p in ps)
        if vp != vr:
            vol_bad += 1
        if len(ps) > 1:
            for i in range(len(ps)):
                for j in range(i + 1, len(ps)):
                    a, b = ps[i], ps[j]
                    if all(max(a[2 * t], b[2 * t]) < min(a[2 * t + 1], b[2 * t + 1]) for t in range(4)):
                        overlap += 1
    return {'pieces': len(pieces), 'roots': len(roots), 'pieces_outside_roots': outside, 'roots_uncovered': empty,
            'roots_volume_mismatch': vol_bad, 'overlapping_piece_pairs': overlap,
            'ok': outside == 0 and empty == 0 and vol_bad == 0 and overlap == 0}


# ------------------------------------------------------------------ per pair

def levels_of(pdir):
    """[(label, family file, [record files])] in level order, and the final family file"""
    out = []
    if os.path.exists(f'{pdir}/fam.json'):
        out.append(('L0', 'fam.json', ['merged.rec']))
        k = 1
        while os.path.isdir(f'{pdir}/L{k}'):
            out.append((f'L{k}', f'L{k}/fam_fix.json', [f'L{k}/merged.rec']))
            k += 1
    else:
        recs = sorted(f for f in os.listdir(pdir) if f.endswith('.rec'))
        out.append(('R1', 'fam_r1.json', recs))
    final = 'fam_r5.json' if os.path.exists(f'{pdir}/fam_r5.json') else out[-1][1]
    return out, final


def check_pair(base, pair, fams, recorded_e, r5_set, leaf_dir):
    pdir = f'{base}/seams/{pair}'
    a, b = pair.split('__')
    P, Pp = fams[a], fams[b]
    levels, final = levels_of(pdir)
    rep = {'pair': pair, 'levels': [l[0] for l in levels], 'final_family': final}
    famj = {fn: json.load(open(f'{pdir}/{fn}')) for fn in {l[1] for l in levels} | {final}}
    item1 = {}
    meas = {}
    trans_final = None
    for fn, fj in famj.items():
        r, M, trans = seam_family_checks(fj, P, Pp, fn)
        item1[fn] = r
        meas[fn] = M
        if fn == final:
            trans_final = trans
    e_final = item1[final]['e']
    rec_e = recorded_e.get(pair)
    rep['item1'] = {'ok': all(r['ok'] for r in item1.values()),
                    'families': {fn: {k: (str(v) if isinstance(v, F) else v) for k, v in r.items() if k != 'name'}
                                 for fn, r in item1.items()},
                    'e_final': str(e_final), 'e_recorded': rec_e,
                    'e_equal': rec_e is not None and F(rec_e) == e_final,
                    'e_not_above_recorded': rec_e is not None and e_final <= F(rec_e),
                    'e_in_final_family': famj[final]['seam'].get('extra')}
    rep['item2'] = band_check(trans_final, P, Pp)
    rep['item2']['by_level'] = {l[1]: band_check(Measure.from_rows(famj[l[1]]['F'], l[1]).restrict_x(S_SEAM, S_SEAM + 1), P, Pp)['ok']
                                for l in levels if l[1] != final}
    dom = []
    for (l1, f1, _), (l2, f2, _) in zip(levels, levels[1:]):
        ok, eq = dominates(famj[f2], famj[f1], meas[f2], meas[f1])
        dom.append({'from': f1, 'to': f2, 'dominates': ok, 'equal': eq})
    if final not in [l[1] for l in levels]:
        for l, f1, _ in levels:
            ok, eq = dominates(famj[final], famj[f1], meas[final], meas[f1])
            dom.append({'from': f1, 'to': final, 'dominates': ok, 'equal': eq})
    rep['item3'] = {'steps': dom, 'ok': all(d['dominates'] for d in dom)}
    # item 4 (pair's own root list) and item 5
    own = f'{pdir}/roots_r5.json'
    rlist = [tuple(F(v) for v in r) for r in json.load(open(own if os.path.exists(own) else f'{base}/seams/roots_r5.json'))]
    rep['item4'] = {'list': 'own' if os.path.exists(own) else 'shared', 'count': len(rlist),
                    'equals_recomputed': set(rlist) == r5_set and len(rlist) == len(set(rlist))}
    d0, d1 = F(famj[final]['d0']), F(famj[final]['d1'])
    pieces = []
    for _, _, recs in levels:
        for rf in recs:
            pieces += record_roots(f'{pdir}/{rf}')
    rep['item5'] = coverage(pieces, rlist, d0, d1)
    # item 6 from the leaf-replay reports
    if leaf_dir:
        rep['item6'] = leaf_item(base, pdir, pair, levels, leaf_dir)
    rep['ok'] = all(rep[k]['ok'] for k in ('item1', 'item2', 'item3', 'item5')) and rep['item4']['equals_recomputed'] \
        and rep['item1']['e_not_above_recorded'] and (not leaf_dir or rep['item6']['ok'])
    return rep, e_final


def leaf_item(base, pdir, pair, levels, leaf_dir):
    import glob
    import hashlib
    out = {'records': [], 'ok': True}
    for lab, fam, recs in levels:
        for rf in recs:
            # job names as make_jobs.py: merged.rec is level L0 (also in an R1 family), other R1 records by file name
            lev = lab if lab != 'R1' else ('L0' if rf == 'merged.rec' else rf[:-4])
            files = sorted(glob.glob(f'{leaf_dir}/{pair}__{lev}__*of*.json'))
            rsha = hashlib.sha256(open(f'{pdir}/{rf}', 'rb').read()).hexdigest()
            fsha = hashlib.sha256(open(f'{pdir}/{fam}', 'rb').read()).hexdigest()
            reps = [json.load(open(f)) for f in files]
            M = reps[0]['part'][1] if reps else 0
            parts = sorted(r['part'][0] for r in reps)
            good = (bool(reps) and parts == list(range(M)) and all(r['part'][1] == M for r in reps)
                    and all(r['record_sha256'] == rsha and r['family_sha256'] == fsha for r in reps)
                    and all(not r['refusals'] and r['every'] == 1 and r['checked_leaves'] == r['part_leaves'] for r in reps)
                    and sum(r['part_roots'] for r in reps) == reps[0]['roots']
                    and sum(r['part_leaves'] for r in reps) == reps[0]['leaves'])
            kinds = {}
            for r in reps:
                for k, v in r['kinds'].items():
                    kinds[k] = kinds.get(k, 0) + v['leaves']
            out['records'].append({'record': rf, 'family': fam, 'parts': f'{len(parts)}/{M}', 'ok': good,
                                   'roots': reps[0]['roots'] if reps else None, 'leaves': reps[0]['leaves'] if reps else None,
                                   'refusals': sum(len(r['refusals']) for r in reps), 'kinds': kinds,
                                   'cpu_seconds': sum(v['seconds'] for r in reps for v in r['kinds'].values())})
            out['ok'] &= good
    return out


# ------------------------------------------------------------------ item 7

def paths(names, edges):
    """for every pair of intervals: the minimal-E path (ties: fewest seams), E, r, k0; and the frontier over r
    (for each number of seams r, the least E; kept when E strictly decreases)"""
    adj = {n: [] for n in names}
    for (u, v), e in edges.items():
        adj[u].append((v, e)); adj[v].append((u, e))
    res = {}
    for s in names:
        best = {s: (F(0), 0, [s])}
        heap = [(F(0), 0, [s])]
        while heap:
            E, r, path = heappop(heap)
            u = path[-1]
            if best.get(u, (None,))[:2] != (E, r):
                continue
            for v, e in adj[u]:
                cand = (E + e, r + (e > 0), path + [v])
                if v not in best or cand[:2] < best[v][:2]:
                    best[v] = cand
                    heappush(heap, cand)
        # frontier: L_r(v) = least E over paths with at most r seams (zero edges are free), by layers
        def zero_closure(L):
            L = dict(L)
            changed = True
            while changed:
                changed = False
                for u, E in list(L.items()):
                    for v, e in adj[u]:
                        if e == 0 and (v not in L or E < L[v]):
                            L[v] = E
                            changed = True
            return L
        layers = [zero_closure({s: F(0)})]
        for _ in range(len(names)):
            prev = layers[-1]
            cur = dict(prev)
            for u, E in prev.items():
                for v, e in adj[u]:
                    if e > 0 and (v not in cur or E + e < cur[v]):
                        cur[v] = E + e
            layers.append(zero_closure(cur))
        for t in names:
            fr = []
            for r, L in enumerate(layers):
                if t in L and (not fr or L[t] < fr[-1][1]):
                    fr.append((r, L[t]))
            E, r, path = best[t]
            res[(s, t)] = {'E': E, 'r': r, 'k0': 7 if r == 0 else max(7, 6 + 3 * r), 'path': path,
                           'frontier': [{'r': rr, 'k0': 7 if rr == 0 else max(7, 6 + 3 * rr), 'E': EE} for rr, EE in fr]}
    return res


def main(argv):
    base = argv[1]
    opt = lambda k: argv[argv.index(k) + 1] if k in argv else None
    leaf_dir = opt('--leaf-reports')
    only = set(opt('--pairs').split(',')) if opt('--pairs') else None
    out_path = opt('--out') or 'seam_check2_report.json'
    fams = {}
    for fn in sorted(os.listdir(f'{base}/families')):
        fj = json.load(open(f'{base}/families/{fn}'))
        fams[fn[:-5]] = profile(fj)
    report = {'profiles': {n: {'mass': str(P.mass()), 'mass_is_9/5': P.mass() == F(9, 5)} for n, P in fams.items()}}
    allr, touch = r5_roots()
    r5_set = set(touch)
    report['item4'] = {'grid_roots': allr, 'touching_roots': len(touch),
                       'shared_list_equal': set(tuple(F(v) for v in r) for r in json.load(open(f'{base}/seams/roots_r5.json'))) == r5_set}
    print(f'item 4: grid {allr} roots, {len(touch)} touch the bands; shared roots_r5.json equal: {report["item4"]["shared_list_equal"]}')
    ej = json.load(open(f'{base}/tables/seam_e_rigorous.json'))
    recorded_e = {f'{p["a"]}__{p["b"]}': p['e'] for p in ej['pairs']}
    pairs = sorted(d for d in os.listdir(f'{base}/seams') if os.path.isdir(f'{base}/seams/{d}'))
    report['pairs'] = {}
    e_mine = {}
    for p in pairs:
        if only and p not in only:
            continue
        rep, e = check_pair(base, p, fams, recorded_e, r5_set, leaf_dir)
        report['pairs'][p] = rep
        e_mine[p] = e
        i6 = rep.get('item6', {}).get('ok', '-')
        print(f'{p}: item1 {rep["item1"]["ok"]} (e {rep["item1"]["e_final"]} recorded {rep["item1"]["e_recorded"]} '
              f'equal {rep["item1"]["e_equal"]}), item2 {rep["item2"]["ok"]}, item3 {rep["item3"]["ok"]}, '
              f'item4 {rep["item4"]["equals_recomputed"]}, item5 {rep["item5"]["ok"]} ({rep["item5"]["pieces"]} pieces), '
              f'item6 {i6}: {"PASS" if rep["ok"] else "FAIL"}', flush=True)
    if not only:
        order = [r['name'].replace('interval_', '') for r in json.load(open(f'{base}/tables/m25_table.json'))]
        seamed = {tuple(p.split('__')) for p in pairs}
        eq_pairs = []
        for u, v in zip(order, order[1:]):
            if (u, v) not in seamed and (v, u) not in seamed:
                eq_pairs.append((u, v, fams[u].compare(fams[v])[1]))
        report['adjacent_without_seam'] = [{'a': u, 'b': v, 'profiles_equal': eq} for u, v, eq in eq_pairs]
        eq_pairs = [(u, v, eq) for u, v, eq in eq_pairs if eq]      # only equal profiles join without a seam
        report['equal_profile_pairs'] = [{'a': u, 'b': v} for u, v, _ in eq_pairs]
        edges = {tuple(p.split('__')): F(recorded_e[p]) for p in pairs}
        for u, v, eq in eq_pairs:
            edges[(u, v)] = F(0)
        res = paths(order, edges)
        pj = json.load(open(f'{base}/tables/paths.json'))
        mism = []
        for row in pj:
            m = res[(row['a'], row['b'])]
            fr = [{'r': f['r'], 'k0': f['k0'], 'E': F(f['E'])} for f in row['frontier']]
            if not (F(row['E']) == m['E'] and row['r'] == m['r'] and row['k0'] == m['k0'] and row['path'] == m['path']
                    and fr == m['frontier']):
                mism.append([row['a'], row['b']])
        report['item7'] = {'equal_profile_pairs': len(eq_pairs), 'all_equal_profiles': all(e for _, _, e in eq_pairs),
                           'rows': len(pj), 'mismatches': mism[:20], 'mismatch_count': len(mism),
                           'e_used': 'recorded e (each checked against the recomputed e in item 1)',
                           'ok': not mism and len(eq_pairs) == 4 and all(e for _, _, e in eq_pairs) and len(pj) == 595}
        Emax = max(res.values(), key=lambda m: m['E'])
        print(f'item 7: {len(eq_pairs)} equal-profile adjacent pairs (equal: {all(e for _, _, e in eq_pairs)}), '
              f'{len(pj)} rows compared, {len(mism)} mismatches; max E {Emax["E"]} (r {Emax["r"]}, k0 {Emax["k0"]})')
    def enc(o):
        if isinstance(o, F):
            return str(o)
        raise TypeError
    json.dump(report, open(out_path, 'w'), indent=1, default=enc)
    ok = all(r['ok'] for r in report['pairs'].values()) and report['item4']['touching_roots'] == 11206 \
        and report['item4']['shared_list_equal'] and (only or report['item7']['ok'])
    print('ALL PASS' if ok else 'FAIL')
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main(sys.argv))
