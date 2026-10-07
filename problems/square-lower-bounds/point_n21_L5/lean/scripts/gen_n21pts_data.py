#!/usr/bin/env python3
"""Exact transcription of refit29: X/D, Y/D, w/W; duplicates add.

Run in the overlaid Lean project:
  python3 scripts/gen_n21pts_data.py --source <n21-original.txt> [--check].
The Source line in the generated header keeps the original research path.
The source hash, header, nonnegativity, support, total and aggregated D4
symmetry are checked. No floating point arithmetic or rounding is used.
"""
import argparse
from collections import defaultdict
from fractions import Fraction
from hashlib import sha256
from pathlib import Path
from gen_s21_data import emit

PROJECT = Path(__file__).resolve().parents[1]
SOURCE = Path('../../runs/evand_n21_n32_bridge_20260927/results/n21_L5_refit29_counterexample_trial/refit/candidate.txt')
SHA = '84a7dae793f05ff72de52ddcd3058e8518c1f84c461f94d11305adefe6137679'


def render(path):
    raw = Path(path).read_bytes()
    assert sha256(raw).hexdigest() == SHA, 'source hash mismatch'
    tokens = [int(t) for line in raw.decode().splitlines()
              for t in line.split('#', 1)[0].split()]
    assert tokens[:5] == [5, 1, 1000, 1000000000000, 4604]
    assert len(tokens) == 5 + 3 * 4604, 'incorrect entry count or trailing data'
    weights = defaultdict(int)
    for i in range(5, len(tokens), 3):
        x, y, w = tokens[i:i + 3]
        assert 0 <= x <= 5000 and 0 <= y <= 5000 and w >= 0
        weights[x, y] += w
    assert Fraction(sum(weights.values()), 10**12) == Fraction(2624862500021, 125000000000)
    for (x, y), w in list(weights.items()):
        assert weights.get((5000-x, y)) == w and weights.get((y, x)) == w
    points = sorted((x, y, w) for (x, y), w in weights.items())
    defs, root = emit(points, 'p', lambda e: f'{e[0]} {e[1]} {e[2]}')
    out = ['import Sqpack.Cover', '', '/-!', '# Point-only n=21 certificate (generated)',
           f'Source: `{SOURCE.as_posix()}`', f'SHA256: `{SHA}`',
           f'4604 ordered entries aggregated by coordinate into {len(points)} unique keys.',
           'Each node X Y w means (X/1000, Y/1000), mass w/1000000000000.',
           'Duplicate weights are added as integers; zero weights are retained.',
           f'Integer mass sum: {sum(weights.values())}.', '-/', '',
           'set_option linter.style.longLine false', '', 'namespace SquarePacking.N21PtsData', '']
    out += [f'def {name} : PTree :=\n  {body}\n' for name, body in defs]
    out += [f'def ptree : PTree :=\n  {root}\n', 'end SquarePacking.N21PtsData', '']
    return '\n'.join(out), len(points), sum(weights.values())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', required=True, help='certificates/n21-original.txt')
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    text, count, total = render(args.source)
    target = PROJECT / 'Sqpack/N21PtsData.lean'
    if args.check:
        assert target.read_text() == text, 'generated data differs'
        print('Sqpack/N21PtsData.lean matches source')
    else:
        target.write_text(text)
        print(f'Wrote Sqpack/N21PtsData.lean: {count} unique points, integer total {total}')
    print(f'Source SHA256: {SHA}')


if __name__ == '__main__':
    main()
