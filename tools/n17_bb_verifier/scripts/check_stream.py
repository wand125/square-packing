#!/usr/bin/env python3
"""Compare all retained fixtures and local versions of check_v3.py's six mutants."""
import copy
import gzip
import json
from pathlib import Path
import tempfile

from compare_stream import ROOT, compare


def read(directory, name):
    return json.loads(gzip.decompress((directory / (name + '.json.gz')).read_bytes()))


def write(directory, name, value):
    (directory / (name + '.json.gz')).write_bytes(gzip.compress(json.dumps(value).encode(), mtime=0))


def main():
    fixtures = ROOT / 'tests/fixtures'
    cells = fixtures / 'v3-cells.json'
    for directory in sorted(fixtures.iterdir()):
        if directory.is_dir():
            receipt, stderr = compare(directory, cells=cells if directory.name.startswith('v3-') else None)
            print(f"{directory.name}: {receipt['status']}, identical, fallback={'stream fallback:' in stderr}")
    for name in ['drop_partner_interval', 'pair_as_wall', 'widen_eliminated', 'angle_not_empty', 'wrong_pair_index', 'drop_window']:
        source = fixtures / ('small-certificate' if name == 'drop_window' else 'v3-angle')
        manifest_name = (source / 'README.txt').read_text().strip().splitlines()[-1].split(':')[-1].strip().removesuffix('.json.gz')
        manifest = read(source, manifest_name)
        nodes = [node for chunk in manifest['chunks'] for node in read(source, chunk)['nodes']]
        if name == 'drop_window':
            node = next(n for n in nodes if n['windows'])
            node['windows'].pop()
        else:
            node = nodes[0]
            if name == 'drop_partner_interval':
                node['angle'][0][5] = []
            elif name == 'pair_as_wall':
                node['angle'] = [[0, '0/1', '2/1', 'wall']]
            elif name == 'widen_eliminated':
                node['angle'][0][2] = '100/1'
            elif name == 'angle_not_empty':
                node['angle'] = []
            elif name == 'wrong_pair_index':
                node['angle'][0][4] = 1
        with tempfile.TemporaryDirectory(prefix='n17-stream-') as temporary:
            directory = Path(temporary)
            trig = read(source, manifest['trig'])
            manifest = copy.deepcopy(manifest)
            manifest.update(chunks=['nodes'], trig='trig')
            for key, value in [('manifest', manifest), ('nodes', dict(nodes=nodes)), ('trig', trig)]:
                write(directory, key, value)
            (directory / 'README.txt').write_text('manifest: manifest\n')
            receipt, stderr = compare(directory, cells=None if name == 'drop_window' else cells)
            assert receipt['status'] == 'FAIL' and 'stream fallback:' in stderr, (name, receipt, stderr)
            print(f"local-{name}: FAIL, identical, fallback=True")


if __name__ == '__main__':
    main()
