#!/usr/bin/env python3
"""Like emit.py, but one kernel-checked theorem per leaf, glued with check_sx/sy/su/lin.
Splitting keeps each `decide +kernel` small; one monolithic decide is much slower."""
import argparse
import json
from pathlib import Path

from q3 import Q3
from emit import q3, aff, rat, emit_tree


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('tree_json')
    ap.add_argument('cert_json')
    ap.add_argument('name')
    ap.add_argument('outdir')
    ap.add_argument('--per-file', type=int, default=40, help='leaf theorems per file')
    a = ap.parse_args()
    d = json.loads(Path(a.tree_json).read_text())
    c = json.loads(Path(a.cert_json).read_text())
    L = Q3.parse(c['L'])
    ytop = L * Q3(0, 1) / 2
    pts = ', '.join(f'({q3(p["x"])}, {q3(p["y"])}, {rat(p["w"])})' for p in c['points'])
    ns = f'SquarePacking.Tri.{a.name}'
    out = Path(a.outdir)
    out.mkdir(parents=True, exist_ok=True)
    head = ['import Sqtri.Check', '', f'namespace {ns}', '',
            f'def L : Q3 := {q3(L)}', f'def yTop : Q3 := {q3(ytop)}', f'def pts : List Pt := [{pts}]', '',
            'theorem weights : weightsOk pts = true := by decide +kernel', '', f'end {ns}', '']
    (out / 'Base.lean').write_text('\n'.join(head))
    leaves = []          # (name, statement, term)

    def walk(n, box, U, lins):
        """Returns the Lean proof term for check ... n = true."""
        x0, x1, y0, y1 = box
        if 'leaf' in n:
            k = len(leaves)
            stmt = (f'check L pts ({x0}) ({x1}) ({y0}) ({y1}) ({U[0]}) ({U[1]}) ({lins}) '
                    f'lf{k} = true')
            leaves.append((f'leaf{k}', stmt, f'lf{k}', emit_tree(n)))
            return f'leaf{k}'
        s = n['split']
        if s == 'lin':
            f = aff(n['form'])
            p = walk(n['pos'], box, U, f'({lins} ++ [{f}])')
            q = walk(n['neg'], box, U, f'({lins} ++ [Aff.neg {f}])')
            return f'(check_lin {p} {q})'
        m = q3(n['at'])
        if s == 'x':
            lo = walk(n['lo'], (x0, m, y0, y1), U, lins); hi = walk(n['hi'], (m, x1, y0, y1), U, lins)
        elif s == 'y':
            lo = walk(n['lo'], (x0, x1, y0, m), U, lins); hi = walk(n['hi'], (x0, x1, m, y1), U, lins)
        else:
            lo = walk(n['lo'], box, (U[0], m), lins); hi = walk(n['hi'], box, (m, U[1]), lins)
        return f'(check_s{s} {lo} {hi})'

    roots = []
    for k, r in enumerate(d['roots']):
        U0, U1 = (q3(x) for x in r['u'])
        start = len(leaves)
        term = walk(r['tree'], ('Q3.zero', 'L', 'Q3.zero', 'yTop'), (U0, U1), '[]')
        counter = [start]

        def skel(n):
            if 'leaf' in n:
                j = counter[0]; counter[0] += 1
                return f'lf{j}'
            s = n['split']
            if s == 'lin':
                return f'(.lin {aff(n["form"])} {skel(n["pos"])} {skel(n["neg"])})'
            return f'(.s{s} ({q3(n["at"])}) {skel(n["lo"])} {skel(n["hi"])})'
        roots.append((k, U0, U1, term, skel(r['tree'])))
    files = []
    for i in range(0, len(leaves), a.per_file):
        fname = f'Leaves{i // a.per_file}'
        files.append(fname)
        body = [f'import Sqtri.Data.{a.name}.Base', '', f'namespace {ns}', '']
        for name, stmt, dname, dterm in leaves[i:i + a.per_file]:
            body += [f'def {dname} : Tree := {dterm}', '',
                     f'theorem {name} : {stmt} := by', '  decide +kernel', '']
        body.append(f'end {ns}')
        (out / f'{fname}.lean').write_text('\n'.join(body) + '\n')
    top = [f'import Sqtri.Data.{a.name}.{f}' for f in files] + [
        '', '-- The tree skeletons and their glue proofs are large terms; elaboration needs more time.',
        'set_option maxHeartbeats 0', '', f'namespace {ns}', '']
    for k, U0, U1, term, tree in roots:
        top += [f'noncomputable def tree{k} : Tree := {tree}', '',
                f'theorem check{k} : check L pts Q3.zero L Q3.zero yTop ({U0}) ({U1}) [] tree{k} = true :=',
                f'  {term}', '']
    top.append(f'end {ns}')
    (out / 'All.lean').write_text('\n'.join(top) + '\n')
    print(len(leaves), 'leaves in', len(files), 'files')


if __name__ == '__main__':
    main()
