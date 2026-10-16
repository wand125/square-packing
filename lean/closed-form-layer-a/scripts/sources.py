#!/usr/bin/env python3
"""Check the per-file manifest and safely install the generated Release sources."""
import hashlib
from pathlib import Path, PurePosixPath
import sys
import tarfile

ROOT = Path(__file__).resolve().parent.parent

def manifest(root=ROOT):
    result = {}
    for line in (root / 'generated-sources.sha256').read_text().splitlines():
        digest, name = line.split('  ', 1)
        path = PurePosixPath(name)
        if (len(digest) != 64 or any(c not in '0123456789abcdef' for c in digest)
                or path.is_absolute() or '..' in path.parts or str(path) != name
                or not name.startswith('ClosedForm/') or not name.endswith('.lean')
                or name in result):
            raise ValueError('Invalid generated source manifest')
        result[name] = digest
    if not result:
        raise ValueError('Empty generated source manifest')
    return result

def safe_target(root, name):
    target = root / name
    if any(p.is_symlink() for p in [target, *target.parents] if p != root.parent):
        raise ValueError('Symbolic link in destination: ' + name)
    if not target.resolve().is_relative_to(root.resolve()):
        raise ValueError('Destination escapes bundle')
    return target

def check(root=ROOT):
    expected = manifest(root)
    for name, digest in expected.items():
        p = safe_target(root, name)
        if not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest() != digest:
            raise ValueError('Missing or changed generated source: ' + name)
    return len(expected)

def install(archive, root=ROOT):
    expected = manifest(root)
    with tarfile.open(archive, 'r:xz') as tf:
        members = tf.getmembers()
        if len(members) != len(expected) or {m.name for m in members} != set(expected):
            raise ValueError('Archive file list differs from manifest')
        # Validate every member and digest before writing any source.
        for m in members:
            if not m.isfile():
                raise ValueError('Archive contains a non-regular file')
            safe_target(root, m.name)
            with tf.extractfile(m) as f:
                if hashlib.sha256(f.read()).hexdigest() != expected[m.name]:
                    raise ValueError('Archive checksum mismatch: ' + m.name)
        for m in members:
            p = safe_target(root, m.name)
            p.parent.mkdir(parents=True, exist_ok=True)
            with tf.extractfile(m) as f:
                p.write_bytes(f.read())
    return check(root)

if __name__ == '__main__':
    try:
        count = install(sys.argv[1]) if len(sys.argv) == 2 else check()
        print(f'Generated source hashes match: {count} files')
    except (OSError, ValueError, tarfile.TarError) as exc:
        raise SystemExit(str(exc))
