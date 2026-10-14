#!/usr/bin/env python3
"""Deterministic CLI/checkpoint/receipt checks; run under nice, serial processes."""
import json
import pathlib
import subprocess
import tempfile
ROOT = pathlib.Path(__file__).resolve().parent
BIN = ROOT / 'target/release/m5-check2'

def run(name, threads, rounds, resume=False, binary=BIN):
    out = base / name
    cmd = [str(binary), '--threads', str(threads), '--seconds', '30', '--depth', '24', '--rounds', str(rounds), '--output', str(out), '--keep-leaves', '--checkpoint-seconds', '0.03']
    if resume:
        cmd += ['--resume']
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=35, check=True)
    return json.loads(result.stdout), json.loads((out / 'checkpoint.json').read_text()), (out / 'leaves.txt').read_bytes()

with tempfile.TemporaryDirectory(prefix='integration-', dir=ROOT) as directory:
    base = pathlib.Path(directory)
    one = run('one', 1, 6)  # r3: a round is up to 64 tasks x 4096 boxes
    two = run('two', 2, 6)
    run('resume', 1, 2)
    # Simulate a crash leaving uncommitted bytes after the durable leaf offset.
    with (base / 'resume/leaves.txt').open('ab') as f:
        f.write(b'UNCOMMITTED CRASH TAIL\n')
    resumed = run('resume', 2, 6, True)
    old = run('rust186', 2, 6, binary=ROOT / 'target186/release/m5-check2')
    for label, other in [('two threads', two), ('resume + thread change + crash tail', resumed), ('Rust 1.86', old)]:
        for key in ['boxes', 'leaves_by_reason', 'closed_volume_fraction', 'pending', 'unresolved', 'max_depth', 'digest', 'rounds', 'leaf_bytes']:
            assert one[0][key] == other[0][key], (label, key)
        assert one[1]['pending'] == other[1]['pending']
        assert one[1]['unresolved'] == other[1]['unresolved']
        assert one[2] == other[2]
        print(label, 'identical counters, ordered frontier, unresolved boxes, digest and leaf stream')
    for args in [['--threads','3'],['--seconds','1201'],['--server']]:
        p = subprocess.run([str(BIN), *args], capture_output=True, timeout=5)
        assert p.returncode != 0
    print('Mac guards: 3 refusals passed')
    box = {'box': [[0,0],[0,0],[0,0],[0,0],[0,0],[0,0]]}
    p = subprocess.run([str(BIN),'--batch'],input=json.dumps(box)+'\n',text=True,capture_output=True,check=True,timeout=5)
    assert json.loads(p.stdout)['rule'] == 2
    print('JSON-lines batch: exact corner closes by centre lemma')
    # At depth zero the unclosed root must be retained, not dropped or marked complete.
    p = subprocess.run([str(BIN),'--depth','0','--seconds','5','--output',str(base/'depth0')],text=True,capture_output=True,check=True,timeout=10)
    result = json.loads(p.stdout)
    assert result['status']=='unresolved' and result['unresolved']==1 and result['pending']==0
    print('Depth-cap handling: root retained as unresolved')
    print('6-round digest:',one[0]['digest'])
print('integration passed')
