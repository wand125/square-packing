"""Tests of shard.py (SPEC §14): a positive run that completes, a re-split shard, and negative controls.

Run from checker2/ on the Mac (1-2 threads, short):  python3 ../shard/test_shard.py PARENT_CHECKPOINT
PARENT_CHECKPOINT is a copy of a real checker2 checkpoint (sigma 27/20).  Everything is written under checker2/shards_test/.
"""
import json, shutil, subprocess, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent; sys.path.insert(0, str(HERE))
import shard as S

BIN = './target/release/m4b-cert2'; T = Path('shards_test'); TOOL = [sys.executable, str(HERE / 'shard.py')]

def sh(*a, ok=True):
    r = subprocess.run(list(a), capture_output=True, text=True)
    out = r.stdout.strip().splitlines()[-1] if r.stdout.strip() else r.stderr.strip()[-300:]
    if ok is not None and (r.returncode == 0) != ok: raise SystemExit(f'unexpected rc={r.returncode}: {a}\n{out}\n{r.stderr[-500:]}')
    return out

def run(d, sec=60, rounds=None):
    extra = ['--rounds', str(rounds)] if rounds else []
    return json.loads(sh(BIN, '--threads', '2', '--seconds', str(sec), '--sigma', '27/20', '--output', str(d), '--resume', *extra))

def run_to_end(d, tries=15):
    for _ in range(tries):
        r = run(d)
        if r['status'] != 'paused': return r
    raise SystemExit(f'{d} did not finish')

def main():
    parent = Path(sys.argv[1]); shutil.rmtree(T, ignore_errors=True); T.mkdir()
    text, j, pend, unres = S.read_ckpt(parent)
    # 1. a small node: the 6 deepest pending boxes of the real checkpoint, as a pseudo-parent (counters zero)
    deep = sorted(pend, key=S.depth)[-12:]; deep = [t for t in pend if t in deep]
    node = S.shard_text(j['fingerprint'], j, deep, S.sha('test-node')); (T / 'node.json').write_text(node)
    v = S.vol(deep)
    print('split', sh(*TOOL, 'split', str(T / 'node.json'), str(T / 'pos'), '--n', '3', '--sigma', '27/20', '--volume', str(v)))
    # 2. run s00 a little, re-split it into 2, run everything to the end
    r = run(T / 'pos/s00', 60, rounds=2); print('s00 short run', r['status'], r['boxes'], r['pending'])
    man = json.loads((T / 'pos/manifest.json').read_text()); v0 = man['shards'][0]['volume']
    if r['status'] == 'paused' and r['pending'] >= 2:
        print('re-split', sh(*TOOL, 'split', str(T / 'pos/s00/checkpoint.json'), str(T / 'pos/s00/split'), '--n', '2',
                             '--sigma', '27/20', '--volume', v0))
        for k in ('s00', 's01'): print('sub', k, run_to_end(T / 'pos/s00/split' / k)['status'])
    else:
        print('s00 could not be re-split (finished or too few boxes); re-split not tested')
        if r['status'] == 'paused': run_to_end(T / 'pos/s00')
    for k in ('s01', 's02'): print(k, run_to_end(T / 'pos' / k)['status'])
    print('POSITIVE complete:', sh(*TOOL, 'merge', str(T / 'pos'), '--subtree'))
    print('root guard (expect fail):', sh(*TOOL, 'merge', str(T / 'pos'), ok=False))
    # 3. negative controls, each on a fresh copy of the completed tree
    def neg(name, edit):
        d = T / f'neg_{name}'; shutil.copytree(T / 'pos', d); edit(d)
        out = sh(*TOOL, 'merge', str(d), '--subtree', ok=False); print(f'NEG {name}: {out}')
    def jl(p): return json.loads(p.read_text())
    def jw(p, x): p.write_text(json.dumps(x, separators=(',', ':')))
    def drop_shard(d):  # a shard left out of the manifest and its directory removed: a box is missing
        m = jl(d / 'manifest.json'); m['shards'] = m['shards'][:-1]; jw(d / 'manifest.json', m); shutil.rmtree(d / 's02')
    def stray_dir(d): shutil.copytree(d / 's02', d / 's03')
    def dup_box(d):  # s01's initial list gets a box of s02 as well (manifest made consistent with it)
        m = jl(d / 'manifest.json'); a = S.read_ckpt(d / 's01/shard_init.json'); b = S.read_ckpt(d / 's02/shard_init.json')
        ps = a[2] + b[2][:1]; st = S.shard_text(a[1]['fingerprint'], a[1], ps, S.init_chain(m['parent_sha256'], m['parent_leaf_chain'], 's01', ps))
        (d / 's01/shard_init.json').write_text(st)
        m['shards'][1].update(boxes=len(ps), volume=str(S.vol(ps)), pending_sha256=S.sha(','.join(ps)), init_sha256=S.sha(st))
        jw(d / 'manifest.json', m)
    def edit_init(d):
        p = d / 's01/shard_init.json'; x = jl(p); c = x['progress']['leaf_chain']; p.write_text(p.read_text().replace(c, c[::-1]))
    def parent_hist(d):  # one more closed leaf claimed in the parent
        p = d / 'parent_checkpoint.json'; x = jl(p); x['progress']['depth_histogram'][40] += 1
        x['progress']['leaves_by_rule']['bound'] += 1; t = json.dumps(x, separators=(',', ':')); p.write_text(t)
        m = jl(d / 'manifest.json'); m['parent_sha256'] = S.sha(t); jw(d / 'manifest.json', m)
    def fingerprint(d):
        p = d / 's01/checkpoint.json'; x = p.read_text(); f = jl(p)['fingerprint']; p.write_text(x.replace(f, '0' * 64))
    def swapped(d):  # s01's results copied into s02
        for f in ('checkpoint.json', 'receipt.json'): shutil.copy(d / 's01' / f, d / 's02' / f)
    def receipt_unresolved(d):
        p = d / 's01/receipt.json'; x = jl(p); x['unresolved'] = 1; x['status'] = 'unresolved'; jw(p, x)
    def receipt_sigma(d):
        p = d / 's01/receipt.json'; x = jl(p); x['sigma'] = '3/1'; jw(p, x)
    def fewer_leaves(d):  # a completed shard whose histogram lost a leaf (receipt edited to agree)
        for f in ('checkpoint.json', 'receipt.json'):
            p = d / 's01' / f; x = jl(p); h = x['progress']['depth_histogram'] if f == 'checkpoint.json' else x['depth_histogram']
            k = max(i for i, c in enumerate(h) if c); h[k] -= 1
            lb = x['progress']['leaves_by_rule'] if f == 'checkpoint.json' else x['leaves_by_rule']; lb['bound'] -= 1
            jw(p, x)
    def not_resumed(d):
        p = d / 's01/receipt.json'; x = jl(p); x['command_line'] = [c for c in x['command_line'] if c != '--resume']; jw(p, x)
    for name, f in [('drop_shard', drop_shard), ('stray_dir', stray_dir), ('dup_box', dup_box), ('edit_init', edit_init),
                    ('parent_hist', parent_hist), ('fingerprint', fingerprint), ('swapped', swapped),
                    ('receipt_unresolved', receipt_unresolved), ('receipt_sigma', receipt_sigma), ('fewer_leaves', fewer_leaves),
                    ('not_resumed', not_resumed)]:
        neg(name, f)
    # 4. negative controls on a split that has not run (partial merge): the partition and directory checks themselves
    print('partial split', sh(*TOOL, 'split', str(T / 'node.json'), str(T / 'fresh'), '--n', '3', '--sigma', '27/20', '--volume', str(v)))
    print('POSITIVE partial:', sh(*TOOL, 'merge', str(T / 'fresh'), '--partial'))
    def negp(name, edit):
        d = T / f'negp_{name}'; shutil.copytree(T / 'fresh', d); edit(d)
        print(f'NEGP {name}:', sh(*TOOL, 'merge', str(d), '--partial', ok=False))
    def dup_fresh(d):
        dup_box(d); shutil.copy(d / 's01/shard_init.json', d / 's01/checkpoint.json')
    def swap_ckpt(d): shutil.copy(d / 's01/checkpoint.json', d / 's02/checkpoint.json')
    def foreign_box(d):  # s01 gets a box that is not in the parent (a parent box with its depth changed)
        m = jl(d / 'manifest.json'); a = S.read_ckpt(d / 's01/shard_init.json'); t = a[2][0]
        k = S.depth(t); f = t.replace(f'"depth":{k}', f'"depth":{k + 1}'); ps = a[2] + [f]
        st = S.shard_text(a[1]['fingerprint'], a[1], ps, S.init_chain(m['parent_sha256'], m['parent_leaf_chain'], 's01', ps))
        for n in ('shard_init.json', 'checkpoint.json'): (d / 's01' / n).write_text(st)
        m['shards'][1].update(boxes=len(ps), volume=str(S.vol(ps)), pending_sha256=S.sha(','.join(ps)), init_sha256=S.sha(st))
        jw(d / 'manifest.json', m)
    # a shard taken from a split of another parent (the other 12 boxes of the real checkpoint), manifest entry copied too
    other = [t for t in pend if t not in deep][-12:]
    (T / 'node2.json').write_text(S.shard_text(j['fingerprint'], j, other, S.sha('test-node-2')))
    sh(*TOOL, 'split', str(T / 'node2.json'), str(T / 'other'), '--n', '3', '--sigma', '27/20', '--volume', str(S.vol(other)))
    def other_parent(d):
        m = jl(d / 'manifest.json'); mo = jl(T / 'other/manifest.json'); shutil.rmtree(d / 's01')
        shutil.copytree(T / 'other/s01', d / 's01'); m['shards'][1] = mo['shards'][1]; jw(d / 'manifest.json', m)
    def other_parent_rechained(d):  # same, but the shard's start rewritten to claim this parent: the partition fails
        other_parent(d); m = jl(d / 'manifest.json'); a = S.read_ckpt(d / 's01/shard_init.json')
        st = S.shard_text(a[1]['fingerprint'], a[1], a[2], S.init_chain(m['parent_sha256'], m['parent_leaf_chain'], 's01', a[2]))
        for n in ('shard_init.json', 'checkpoint.json'): (d / 's01' / n).write_text(st)
        m['shards'][1]['init_sha256'] = S.sha(st); jw(d / 'manifest.json', m)
    for name, f in [('other_parent', other_parent), ('other_parent_rechained', other_parent_rechained), ('dup_box', dup_fresh), ('swap_ckpt', swap_ckpt), ('foreign_box', foreign_box), ('drop_shard', drop_shard)]:
        negp(name, f)
    print('ALL TESTS PASSED')

if __name__ == '__main__': main()
