#!/usr/bin/env python3
"""The lower-bound table for N = 1..3600 that accompanies the closed-form release.

python3 tools/closed_form_table.py --intervals intervals.json --evand-lb lower_bounds.json --evand-ub timeline.json \
    --index INDEX.json --out-csv table_N3600.csv --out-json public/data/papers/closed-form-table.json

Inputs (all published):
  intervals.json    problems/closed-form/intervals.json (the certified lines S_i(δ) = α_i δ + β_i)
  lower_bounds.json evand/square-packing site/www/data/lower_bounds.json (known lower bounds, n <= 324, with sources; the family s(m² − 4) = m is cited to Evan Daniel)
  timeline.json     evand/square-packing site/www/data/timeline.json (known upper bounds, with finder and year)
  INDEX.json        wand125/square-packing INDEX.json (our published certificates, claims "s(n) >= x")
The column of reference only is Nagamochi's formula (its proof has a publicly discussed gap); it is never used as a
known bound. Green's values (reported without a recoverable proof) are left out. Lower bounds are printed rounded down, upper bounds rounded up, to 9 decimals.
"""
import argparse, csv, json, math, re
from decimal import Decimal, getcontext
from fractions import Fraction as F

getcontext().prec = 80
P = 10 ** 9
GAP = {'Nagamochi2005', 'Green2000'}           # reference only
EXCLUDE = {'wand125_2026'}                      # ours are taken from INDEX.json (current), not from the mirror


def down(x):  # Fraction or Decimal -> string rounded down to 9 places
    q = F(x) if not isinstance(x, F) else x
    return _fmt(math.floor(q * P))


def up(x):
    q = F(x) if not isinstance(x, F) else x
    return _fmt(-math.floor(-q * P))


def _fmt(m):
    s = '-' if m < 0 else ''
    m = abs(m)
    return f'{s}{m // P}.{m % P:09d}'


def sqrt_down(r):  # a Fraction <= sqrt(r), within 1e-15
    if r <= 0:
        return F(0)
    S = 10 ** 15
    return F(math.isqrt(math.floor(r * S * S)), S)


def sqrt_dec(r):
    return (Decimal(r.numerator) / Decimal(r.denominator)).sqrt()


def our_bound(ivs, N):
    """a(N) = max over admissible i of min(k + d1, 2α + sqrt(N + c − 4αk)); exact comparisons, Decimal for the max."""
    k = math.isqrt(N)
    best, bi, how = Decimal(k), None, 'area'
    for it in ivs:
        a, b, d0, d1 = it['A'], it['B'], it['D0'], it['D1']
        r = N + 4 * a * a + 4 * b - 4 * a * k             # a_i(N) = 2a + sqrt(r)
        if r < 0:
            continue
        t0 = k + d0 - 2 * a                                 # admissible: sqrt(r) > t0
        if not (t0 < 0 or r > t0 * t0):
            continue
        t1 = k + d1 - 2 * a                                 # capped at k + d1 when sqrt(r) >= t1
        capped = t1 <= 0 or r >= t1 * t1
        v = Decimal((k + d1).numerator) / Decimal((k + d1).denominator) if capped else Decimal(2 * a.numerator) / Decimal(a.denominator) + sqrt_dec(r)
        if v > best:
            best, bi, how = v, it, ('cap' if capped else 'root')
    if bi is None:
        return {'k': k, 'value': F(k), 'interval': '', 'formula': 'k (area)', 'exact': str(k)}
    a, b = bi['A'], bi['B']
    r = N + 4 * a * a + 4 * b - 4 * a * k
    if how == 'cap':
        val = k + bi['D1']
        return {'k': k, 'value': val, 'interval': bi['i'], 'formula': f"k + d1 = {k} + {bi['d1']}", 'exact': str(val)}
    return {'k': k, 'value': 2 * a + sqrt_down(r), 'interval': bi['i'], 'formula': f"2*alpha_{bi['i']} + sqrt(N + c_{bi['i']} - 4*alpha_{bi['i']}*k)",
            'exact': f"{2 * a} + sqrt({r})" if len(str(r)) < 60 else f"2*alpha_{bi['i']} + sqrt(r), r = N + 4*alpha^2 + 4*beta - 4*alpha*k"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--intervals', required=True); ap.add_argument('--evand-lb', required=True)
    ap.add_argument('--evand-ub', required=True); ap.add_argument('--index', required=True)
    ap.add_argument('--nmax', type=int, default=3600)
    ap.add_argument('--out-csv', required=True); ap.add_argument('--out-json')
    o = ap.parse_args()
    ivs = []
    for it in json.load(open(o.intervals))['intervals']:
        ivs.append({'i': int(it['index']), 'd1': it['d1'], 'A': F(it['certified_line']['alpha']), 'B': F(it['certified_line']['beta']),
                    'D0': F(it['d0']), 'D1': F(it['d1'])})
    lb = json.load(open(o.evand_lb)); src = lb.get('sources', {})
    tl = json.load(open(o.evand_ub))
    ours = {}
    for e in json.load(open(o.index))['problems']['square-lower-bounds']:
        m = re.fullmatch(r's\((\d+)\)\s*(>=|=)\s*([0-9./]+)', e['claim'].replace(' ', ' ').strip())
        if m:
            n, v = int(m.group(1)), F(m.group(3))
            if n not in ours or v > ours[n][0]:
                ours[n] = (v, e['id'])

    def is_k2m4(n, h):
        m = math.isqrt(n + 4)
        # only the general family (certificates/k2m4); an individual bundle such as certificates/s60 counts as established
        return h['source'] == 'EvanDaniel2026' and m * m == n + 4 and 'certificates/k2m4' in (h.get('url') or '')

    def k2m4(n):
        """s(m² − 4) = m for m ≥ 5 (Evan Daniel, conditional on the ValidTilt9 certificate; jlevy/squares#316): shown apart"""
        m = math.isqrt(n + 4)
        return Decimal(m) if m * m == n + 4 and m >= 5 else None

    def known_lb(n):
        """the largest published lower bound for n (not Nagamochi/Green; ours from INDEX.json), with its source"""
        c = [(Decimal(n).sqrt(), 'area bound', '', 'classical', '', '', '')]
        r = math.isqrt(n + 3)   # Valid7: s(m² − 3) = m for every m ≥ 6 (Evan Daniel; Lean kernel proof and an independent check)
        if r * r == n + 3 and r >= 6:
            c.append((Decimal(r), 'Evan Daniel (Valid7)', 2026, 'preprint', 'https://github.com/evand/square-packing',
                      'independently re-checked by wand125 with a separately written exact checker (records-v1)', 'https://github.com/wand125/valid7-independent-check/releases/tag/records-v1'))
        if str(n) in lb:
            for h in lb[str(n)]['history']:
                if h['source'] in GAP or h['source'] in EXCLUDE:
                    continue
                if is_k2m4(n, h):   # the general family s(m² − 4) = m: added below with its own label
                    continue
                s = src.get(h['source'], {})
                name = 'H. Karakuş (arXiv:2609.37410)' if h['source'] == 'Karakus2026' else s.get('authors', h['source'])
                c.append((Decimal(str(h['value'])), name, h.get('year') or '', h['status'], h.get('url') or '', '', ''))
        m = math.isqrt(n + 4)   # s(m² − 4) = m for m ≥ 5 (Evan Daniel; ValidTilt9 checked independently by wand125)
        if m * m == n + 4 and m >= 5:
            ours_m = f'; our certificate {ours[n][1].split(":")[1]} gives the same value' if n in ours and ours[n][0] >= m else ''
            c.append((Decimal(m), 'Evan Daniel, s(k²−4) = k', 2026, 'preprint', 'https://github.com/evand/square-packing/tree/main/s12/certificates/k2m4',
                      ('ValidTilt9 independently re-checked by wand125 with a separately written exact checker (records-tilt9-v1; a Lean formalization is in progress)' + ours_m) if m >= 8 else '',
                      'https://github.com/wand125/valid7-independent-check/releases/tag/records-tilt9-v1' if m >= 8 else ''))
        if n in ours:
            v, i = ours[n]
            c.append((Decimal(v.numerator) / Decimal(v.denominator), 'wand125 (' + i + ')', 2026, 'certificate (not peer reviewed)',
                      'https://github.com/wand125/square-packing/tree/main/problems/square-lower-bounds/' + i.split(':')[1], 'release square-lower-bounds-v1', 'https://github.com/wand125/square-packing/releases/tag/square-lower-bounds-v1'))
        if n >= 8 and math.isqrt(n) ** 2 != n:   # Karakuş, Corollary 6.2 (arXiv:2609.37410)
            k = math.isqrt(n)
            c.append((Decimal(1) / 2 + (Decimal(n - k) + Decimal(1) / 4).sqrt(), 'H. Karakuş (arXiv:2609.37410)', 2026, 'preprint', 'https://arxiv.org/abs/2609.37410', '', ''))
        # on a tie the s(k²−4) = k family is cited (N = 77, 96 also have our certificates at the same value)
        return max(c, key=lambda x: (x[0], x[1].startswith('Evan Daniel, s(k²−4)')))

    ubn = {int(k): v[-1] for k, v in tl.items() if k.isdigit()}

    def known_ub(n):
        k = math.isqrt(n); triv = k if k * k == n else k + 1
        best = (Decimal(triv), 'trivial (⌈√N⌉, grid)', '', True)
        # a record counts only when it is below the trivial bound (a record equal to ⌈√N⌉ is about optimality, not the bound)
        for m, rec in sorted(ubn.items(), key=lambda x: x[0] != n):
            if m >= n and Decimal(str(rec['s'])) < best[0]:
                ev = rec['events'][0] if rec.get('events') else {}
                who, yr = ev.get('who', ''), (ev.get('date') or {}).get('year', '')
                best = (Decimal(str(rec['s'])), who + ('' if m == n else f' (via s({n}) ≤ s({m}))'), yr, False)
        return best

    # s is nondecreasing, so a lower bound for M ≤ N is one for N: take the running maximum, naming the N it comes from
    own = {N: known_lb(N) for N in range(1, o.nmax + 1)}
    mono, best = {}, None
    for N in range(1, o.nmax + 1):
        v = own[N]
        if best is None or v[0] >= best[0]:
            best = (*v, N)
        mono[N] = best if best[-1] == N else (best[0], f'{best[1]} (from N = {best[-1]})', *best[2:])
    rows = []
    for N in range(1, o.nmax + 1):
        k = math.isqrt(N); sq = k * k == N
        a = our_bound(ivs, N) if (N >= 49 and not sq) else None
        kl = mono[N]; ku = known_ub(N)
        kar = (Decimal(1) / 2 + (Decimal(N - k) + Decimal(1) / 4).sqrt()) if (N >= 8 and not sq) else None
        nag = min(1 + Decimal(N - 2 * k + 1).sqrt(), Decimal(k + 1)) if not sq else None
        av = Decimal(a['value'].numerator) / Decimal(a['value'].denominator) if a else None
        dfmt = lambda x: '' if x is None else f'{x:.9f}'
        rows.append({
            'N': N, 'k': k, 'square': 'yes' if sq else '',
            'a_N': down(a['value']) if a else '', 'a_interval': a['interval'] if a else '', 'a_formula': a['formula'] if a else ('s(N) = k' if sq else 'no claim (N < 49)'),
            'known_lb': down(F(str(kl[0]))) if kl[0] is not None else '', 'known_lb_source': kl[1], 'known_lb_year': kl[2], 'known_lb_status': kl[3], 'known_lb_url': kl[4], 'known_lb_note': kl[5], 'known_lb_note_url': kl[6],
            'known_ub': up(F(str(ku[0]))), 'known_ub_source': ku[1], 'known_ub_year': ku[2], 'known_ub_trivial': 'yes' if ku[3] else '',
            'karakus': down(F(str(kar))) if kar is not None else '',
            'ref_nagamochi': down(F(str(nag))) if nag is not None else '',
            'a_minus_known_lb': dfmt(av - kl[0]) if av is not None else '', 'a_minus_karakus': dfmt(av - kar) if (av is not None and kar is not None) else '',
            'a_minus_nagamochi': dfmt(av - nag) if (av is not None and nag is not None) else '', 'known_ub_minus_a': dfmt(ku[0] - av) if av is not None else '',
        })
    with open(o.out_csv, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
    if o.out_json:
        json.dump({'columns': list(rows[0].keys()), 'rows': [list(r.values()) for r in rows]}, open(o.out_json, 'w'), ensure_ascii=False, separators=(',', ':'))
    print(len(rows), 'rows')


if __name__ == '__main__':
    main()
