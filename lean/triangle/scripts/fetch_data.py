#!/usr/bin/env python3
"""Fetch and verify the generated Lean certificate data that is too large for the repository.

The data of a dataset (for example `M9`, the n = 37 lower bound) is the directory
`Sqtri/Data/<dataset>/`.  It is published as the release asset `tri-lean-<dataset>.tar.xz`,
together with `SHA256SUMS`.  `data/MANIFEST-<dataset>.txt` in this repository lists every file
of the directory with its sha256.  This script

1. downloads the archive and `SHA256SUMS` (or takes them from a local directory),
2. checks the archive against `SHA256SUMS`,
3. extracts it into a temporary directory, accepting only regular files directly inside
   `Sqtri/Data/<dataset>/`,
4. checks the exact set of files and every sha256 against the MANIFEST, and only then
5. moves the directory into place.

Nothing is placed for a dataset that fails a check.  The trusted part is the Lean kernel; this
script only makes sure that the files built are the published ones.

Python standard library only.  Run from the `lean/` directory.

    python3 scripts/fetch_data.py M6 M9                 # download from the release
    python3 scripts/fetch_data.py M6 M9 --from-dir DIR  # assets already downloaded to DIR
    python3 scripts/fetch_data.py M6 M9 --verify-only   # check what is in place
"""
import argparse
import hashlib
import os
import shutil
import sys
import tarfile
import tempfile
import urllib.request

REPO = 'wand125/squares-in-triangle'
TAG = 'lean-data-v1'


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for block in iter(lambda: f.read(1 << 20), b''):
            h.update(block)
    return h.hexdigest()


def read_manifest(path):
    """{file name: sha256} of `<sha256>  <file name>` lines; `#` lines are the header."""
    files = {}
    with open(path) as f:
        for line in f:
            line = line.rstrip('\n')
            if not line.strip() or line.startswith('#'):
                continue
            h, name = line.split(None, 1)
            if '/' in name or name in ('.', '..'):
                raise ValueError(f'bad MANIFEST entry: {name}')
            files[name] = h
    return files


def read_sums(path):
    sums = {}
    with open(path) as f:
        for line in f:
            if line.strip():
                h, name = line.split(None, 1)
                sums[name.strip().lstrip('*')] = h
    return sums


def verify_dir(d, want):
    if not os.path.isdir(d):
        return False, 'missing directory'
    have = sorted(os.listdir(d))
    if have != sorted(want):
        extra = sorted(set(have) - set(want))[:3]
        missing = sorted(set(want) - set(have))[:3]
        return False, f'file set differs (extra {extra}, missing {missing})'
    for name, h in want.items():
        p = os.path.join(d, name)
        if not os.path.isfile(p) or os.path.islink(p):
            return False, f'not a regular file: {name}'
        if sha256_file(p) != h:
            return False, f'sha256 mismatch: {name}'
    return True, 'ok'


def safe_extract(archive, dest, prefix):
    with tarfile.open(archive, 'r:xz') as tf:
        members = tf.getmembers()
        for m in members:
            name = m.name
            while name.startswith('./'):
                name = name[2:]
            if m.isdir() and (name + '/' == prefix or prefix.startswith(name + '/')):
                continue
            rest = name[len(prefix):]
            if not m.isfile() or not name.startswith(prefix) or not rest or '/' in rest \
                    or '..' in name.split('/'):
                raise ValueError(f'unexpected archive member: {m.name}')
        for m in members:
            if m.isfile():
                name = m.name
                while name.startswith('./'):
                    name = name[2:]
                out = os.path.join(dest, *name.split('/'))
                os.makedirs(os.path.dirname(out), exist_ok=True)
                with tf.extractfile(m) as src, open(out, 'wb') as f:
                    shutil.copyfileobj(src, f)


def fetch(dataset, a):
    want = read_manifest(os.path.join('data', f'MANIFEST-{dataset}.txt'))
    target = os.path.join('Sqtri', 'Data', dataset)
    if a.verify_only:
        ok, why = verify_dir(target, want)
        print(f'{dataset}: {"OK" if ok else "FAIL " + why}')
        return ok
    asset = f'tri-lean-{dataset}.tar.xz'
    base = f'https://github.com/{a.repo}/releases/download/{a.tag}'
    with tempfile.TemporaryDirectory() as tmp:
        if a.from_dir:
            sums_path = os.path.join(a.from_dir, 'SHA256SUMS')
            arch = os.path.join(a.from_dir, asset)
        else:
            sums_path = os.path.join(tmp, 'SHA256SUMS')
            arch = os.path.join(tmp, asset)
            urllib.request.urlretrieve(f'{base}/SHA256SUMS', sums_path)
            urllib.request.urlretrieve(f'{base}/{asset}', arch)
        sums = read_sums(sums_path)
        if sums.get(asset) != sha256_file(arch):
            print(f'{dataset}: FAIL archive sha256 does not match SHA256SUMS')
            return False
        ex = os.path.join(tmp, 'x')
        try:
            safe_extract(arch, ex, f'Sqtri/Data/{dataset}/')
        except ValueError as e:
            print(f'{dataset}: FAIL {e}')
            return False
        ok, why = verify_dir(os.path.join(ex, 'Sqtri', 'Data', dataset), want)
        if not ok:
            print(f'{dataset}: FAIL {why}')
            return False
        if os.path.exists(target):
            shutil.rmtree(target)
        shutil.move(os.path.join(ex, 'Sqtri', 'Data', dataset), target)
        print(f'{dataset}: OK, {len(want)} files placed in {target}')
        return True


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('datasets', nargs='+')
    ap.add_argument('--from-dir')
    ap.add_argument('--verify-only', action='store_true')
    ap.add_argument('--repo', default=REPO)
    ap.add_argument('--tag', default=TAG)
    a = ap.parse_args()
    ok = all([fetch(d, a) for d in a.datasets])
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
