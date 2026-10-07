"""Reassemble and hash-check the published bundle. This does not verify its mathematics."""
from pathlib import Path, PurePosixPath
import argparse
import hashlib
import json
import shutil
import tarfile
import tempfile


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def unpack(package, destination):
    package, destination = Path(package).resolve(), Path(destination).resolve()
    if destination.exists():
        raise FileExistsError(destination)
    index = json.loads((package / 'archive-index.json').read_text())
    parts = index['parts']
    if not parts or len({p['name'] for p in parts}) != len(parts):
        raise ValueError('Empty or duplicate archive parts')
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.n21-unpack-', dir=destination.parent) as tmp:
        tmp = Path(tmp)
        archive = tmp / 'bundle.tar.gz'
        with archive.open('xb') as combined:
            for part in parts:
                name = part['name']
                if Path(name).name != name or not name.startswith('bundle.tar.gz.part-'):
                    raise ValueError('Invalid archive part name')
                path = package / 'data' / name
                if path.stat().st_size != part['bytes'] or digest(path) != part['sha256']:
                    raise ValueError('Archive part mismatch: ' + name)
                with path.open('rb') as source:
                    shutil.copyfileobj(source, combined)
        if archive.stat().st_size != index['archive_bytes'] or digest(archive) != index['archive_sha256']:
            raise ValueError('Combined archive mismatch')
        extracted = tmp / 'extracted'
        extracted.mkdir()
        with tarfile.open(archive, 'r:gz') as tar:
            members = tar.getmembers()
            seen = set()
            for member in members:
                rel = PurePosixPath(member.name)
                if (rel.is_absolute() or '..' in rel.parts or not rel.parts or rel.parts[0] != 'bundle'
                        or not (member.isfile() or member.isdir()) or member.name in seen):
                    raise ValueError('Invalid archive member: ' + member.name)
                seen.add(member.name)
            tar.extractall(extracted, members=members, filter='data')
        bundle = extracted / 'bundle'
        manifest_path = bundle / 'portable-manifest.json'
        if digest(manifest_path) != index['manifest_sha256']:
            raise ValueError('Manifest mismatch')
        manifest = json.loads(manifest_path.read_text())
        actual = {p.relative_to(bundle).as_posix() for p in bundle.rglob('*') if p.is_file()}
        if actual != set(manifest['files']) | {'portable-manifest.json'}:
            raise ValueError('Bundle file set mismatch')
        for rel, record in manifest['files'].items():
            path = bundle / rel
            if path.stat().st_size != record['bytes'] or digest(path) != record['sha256']:
                raise ValueError('Bundle file mismatch: ' + rel)
            if rel.endswith('.py'):
                preview = package / 'verifier-source' / rel
                if digest(preview) != record['sha256']:
                    raise ValueError('Readable source mismatch: ' + rel)
        bundle.rename(destination)
    return dict(status='BUNDLE_BYTES_VERIFIED', files=len(manifest['files']),
                manifest_sha256=index['manifest_sha256'], mathematical_verification_performed=False)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--package', type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument('--out', type=Path)
    args = parser.parse_args()
    result = unpack(args.package, args.out or args.package / 'bundle')
    print(json.dumps(result, indent=2))
