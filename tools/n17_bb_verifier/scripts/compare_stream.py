#!/usr/bin/env python3
"""Compare classic/stream receipts, ignoring ONLY seconds (and compare exit codes).

Usage: compare_stream.py CERT_DIR [--cells FILE] [--manifest NAME] [--threads N]
The cells digest is computed locally. --binary can select a debug/test binary.
"""
import argparse
import difflib
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def compare(directory, *, cells=None, manifest=None, threads=2, binary=None):
    command = [str(binary or ROOT / 'target/release/n17bb-verify'), str(directory),
               '--threads', str(threads)]
    if cells:
        command += ['--cells', str(cells), '--cells-sha256',
                    hashlib.sha256(Path(cells).read_bytes()).hexdigest()]
    if manifest:
        command += ['--manifest', manifest]
    runs = [subprocess.run(command + flags, capture_output=True, text=True)
            for flags in ([], ['--stream'])]
    receipts = [json.loads(run.stdout) for run in runs]
    for receipt in receipts:
        del receipt['seconds']
    if receipts[0] != receipts[1] or runs[0].returncode != runs[1].returncode:
        diff = ''.join(difflib.unified_diff(
            *[json.dumps(r, sort_keys=True, indent=2).splitlines(True) for r in receipts],
            fromfile='classic', tofile='stream'))
        raise AssertionError(f'{directory}: exits {[r.returncode for r in runs]}\n{diff}')
    return receipts[1], runs[1].stderr


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path)
    parser.add_argument('--cells', type=Path)
    parser.add_argument('--manifest')
    parser.add_argument('--threads', type=int, default=2)
    parser.add_argument('--binary', type=Path)
    args = vars(parser.parse_args())
    receipt, diagnostics = compare(**args)
    print(f"{args['directory'].name}: identical; {receipt['status']}; nodes={receipt.get('nodes', '-')}")
    print(diagnostics, end='')


if __name__ == '__main__':
    main()
