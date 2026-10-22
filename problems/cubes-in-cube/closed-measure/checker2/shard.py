"""M4b-c system 2: split a checkpoint into shards and merge the shard receipts (SPEC §14, 10/19, user approved).

The checker itself is not changed.  A shard is an ordinary checker2 run directory whose checkpoint.json holds a subset of
the parent's pending boxes and zeroed counters; it is run with the same binary and `--resume`.  The checker's fingerprint
(sources + measure metadata, sigma included) is copied unchanged, so a shard only loads under the very same sources.

  split  PARENT_CHECKPOINT DIR --n N          write DIR/manifest.json, DIR/parent_checkpoint.json, DIR/sNN/checkpoint.json
  merge  DIR [--partial]                      check every shard and write DIR/merged_receipt.json

A shard may itself be split later: stop it, then `split DIR/sNN/checkpoint.json DIR/sNN/split --n M`; merge then uses the
sub-tree in place of that shard's own receipt.

Boxes are copied as the exact JSON text the checker wrote (no float re-serialisation).  Volumes are exact integers in
units of 2^-256 of the root (a box of depth d has volume 2^(256-d)); the checker's `closed_volume_fraction` (a float) is
reported but never used in a check.
"""
import argparse, hashlib, json, re, shutil, sys
from pathlib import Path

D = 256; ROOT = 1 << D
BOX = re.compile(r'\{"box":\[(?:\[[^\[\]]*\],?){6}\],"depth":(\d+)\}')
ZERO = dict(boxes=0, max_depth=0, leaves_by_rule=dict(bound=0, outside=0, unresolved=0), closed_volume_fraction=0,
            seconds=0, rounds=0, leaf_bytes=0, lemma_counts=[0] * 6, depth_histogram=[0] * 257)

def sha(b): return hashlib.sha256(b if isinstance(b, bytes) else b.encode()).hexdigest()

class Bad(Exception): pass

def need(cond, msg):
    if not cond: raise Bad(msg)

def boxes_of(text, key):
    """The exact texts of the boxes in the top-level array `key` of a checkpoint."""
    m = re.search(r'"%s":\[' % key, text); need(m, f'no top-level "{key}" array')
    i = m.end(); out = []
    while text[i] != ']':
        b = BOX.match(text, i); need(b, f'bad box text in "{key}" at {i}')
        out.append(b.group(0)); i = b.end()
        if text[i] == ',': i += 1
    need(','.join(out) == text[m.end():i], f'"{key}" does not re-join exactly')
    return out

def depth(t): return int(BOX.fullmatch(t).group(1))
def vol(ts): return sum(1 << (D - depth(t)) for t in ts)
def leaf_vol(p): return sum(h << (D - d) for d, h in enumerate(p['depth_histogram']))

def read_ckpt(path):
    text = Path(path).read_text(); j = json.loads(text)
    need(j['version'] == 2 and j['keep'] is False, f'{path}: version 2 without kept leaves expected')
    need(len(j['progress']['depth_histogram']) == 257, f'{path}: histogram length')
    pend = boxes_of(text, 'pending'); unres = boxes_of(text, 'unresolved')
    need(len(pend) == len(j['pending']) and len(unres) == len(j['unresolved']), f'{path}: box count mismatch')
    return text, j, pend, unres

def ivs(t): return json.loads(t)['box']

def inside(ts, roots):
    """Every box of ts lies in some box of roots (float bounds compare exactly)."""
    R = [ivs(r) for r in roots]
    return all(any(all(r[i][0] <= b[i][0] and b[i][1] <= r[i][1] for i in range(6)) for r in R) for b in map(ivs, ts))

def check_node(text, j, pend, unres, v0, where):
    """Volume conservation at a checkpoint: closed leaves + pending + unresolved = the node's initial volume."""
    p = j['progress']
    need(sum(p['depth_histogram']) == sum(p['leaves_by_rule'].values()), f'{where}: histogram total != leaves')
    need(p['leaves_by_rule']['unresolved'] == len(unres), f'{where}: unresolved count')
    need(len(set(pend + unres)) == len(pend) + len(unres), f'{where}: a box appears twice')
    # unresolved boxes are leaves in the histogram too, so they are not added again
    need(leaf_vol(p) + vol(pend) == v0, f'{where}: volume {leaf_vol(p) + vol(pend)} != {v0} (x 2^-256)')

def shard_text(fp, j, pend, chain):
    prog = dict(status='running', pending=len(pend), unresolved=0, **{k: v for k, v in ZERO.items()}, leaf_chain=chain)
    order = ['status', 'pending', 'unresolved', 'boxes', 'max_depth', 'leaves_by_rule', 'closed_volume_fraction',
             'leaf_chain', 'seconds', 'rounds', 'leaf_bytes', 'lemma_counts', 'depth_histogram']
    ptxt = '{' + ','.join(f'"{k}":{json.dumps(prog[k], separators=(",", ":"))}' for k in order) + '}'
    return (f'{{"version":2,"fingerprint":"{fp}","depth_cap":{j["depth_cap"]},"cell_depth":{j["cell_depth"]},'
            f'"keep":false,"progress":{ptxt},"pending":[{",".join(pend)}],"unresolved":[]}}')

def init_chain(parent_sha, parent_chain, name, pend):
    """The shard's starting leaf chain names its parent checkpoint (sha256 of the file and its chain), its name and boxes."""
    return sha(f'{parent_sha}|{parent_chain}|shard|{name}|{sha(",".join(pend))}')

def split(a):
    src = Path(a.checkpoint); out = Path(a.dir)
    need(not out.exists(), f'{out} exists')
    text, j, pend, unres = read_ckpt(src)
    need(not unres, 'parent has unresolved boxes; not split')
    v0 = int(a.volume) if a.volume else ROOT
    check_node(text, j, pend, unres, v0, 'parent')
    need(a.n >= 2 and len(pend) >= a.n, f'need 2 <= n <= {len(pend)} pending boxes')
    # largest volume first into the lightest shard (ties: the lower index); within a shard the parent's stack order
    bins = [[] for _ in range(a.n)]; load = [0] * a.n
    for i in sorted(range(len(pend)), key=lambda i: (depth(pend[i]), i)):
        k = min(range(a.n), key=lambda k: (load[k], k)); bins[k].append(i); load[k] += 1 << (D - depth(pend[i]))
    out.mkdir(parents=True); (out / 'parent_checkpoint.json').write_text(text)
    shards = []
    for k, idx in enumerate(bins):
        name = f's{k:02d}'; ps = [pend[i] for i in sorted(idx)]
        chain = init_chain(sha(text), j['progress']['leaf_chain'], name, ps)
        st = shard_text(j['fingerprint'], j, ps, chain); json.loads(st)
        (out / name).mkdir(); (out / name / 'checkpoint.json').write_text(st); (out / name / 'shard_init.json').write_text(st)
        shards.append(dict(name=name, boxes=len(ps), volume=str(vol(ps)), pending_sha256=sha(','.join(ps)),
                           init_sha256=sha(st), init_chain=chain))
    man = dict(version=1, parent_sha256=sha(text), parent_volume=str(v0), fingerprint=j['fingerprint'],
               depth_cap=j['depth_cap'], cell_depth=j['cell_depth'], sigma=a.sigma, parent_leaf_chain=j['progress']['leaf_chain'],
               parent_pending=len(pend), shards=shards)
    (out / 'manifest.json').write_text(json.dumps(man, indent=1))
    print(json.dumps(dict(dir=str(out), n=a.n, volume_fraction={s['name']: int(s['volume']) / ROOT for s in shards})))

def merge_dir(out, partial, log, path='root'):
    """Returns the totals of the tree under DIR; raises Bad on any failed check."""
    man = json.loads((out / 'manifest.json').read_text())
    text, j, pend, unres = read_ckpt(out / 'parent_checkpoint.json')
    need(sha(text) == man['parent_sha256'], f'{path}: parent checkpoint changed')
    need(j['fingerprint'] == man['fingerprint'] and j['depth_cap'] == man['depth_cap'] and j['cell_depth'] == man['cell_depth'],
         f'{path}: parent fingerprint or caps differ from the manifest')
    need(not unres, f'{path}: parent has unresolved boxes')
    v0 = int(man['parent_volume']); check_node(text, j, pend, unres, v0, f'{path}/parent')
    p = j['progress']
    tot = dict(boxes=p['boxes'], bound=p['leaves_by_rule']['bound'], outside=p['leaves_by_rule']['outside'], unresolved=0,
               lemmas=list(p['lemma_counts']), max_depth=p['max_depth'], seconds=p['seconds'], leaf_vol=leaf_vol(p),
               pending=0, pending_vol=0, chains=[(path, p['leaf_chain'])], shards=0,
               tree=dict(parent_checkpoint_sha256=man['parent_sha256'], parent_volume=man['parent_volume'],
                         parent_leaf_chain=p['leaf_chain'], parent_boxes=p['boxes'], shards=[]))
    seen = []
    names = [s['name'] for s in man['shards']]
    need(len(set(names)) == len(names) and all(re.fullmatch(r's\d\d', n) for n in names), f'{path}: shard names')
    extra = sorted(q.name for q in out.iterdir() if q.is_dir() and q.name not in names)
    need(not extra, f'{path}: shard directories not in the manifest: {extra}')
    for s in man['shards']:
        sd = out / s['name']; where = f'{path}/{s["name"]}'
        itext, ij, ipend, iunres = read_ckpt(sd / 'shard_init.json')
        need(sha(itext) == s['init_sha256'], f'{where}: shard_init.json changed')
        need(ij['fingerprint'] == man['fingerprint'], f'{where}: fingerprint')
        need(sha(','.join(ipend)) == s['pending_sha256'] and len(ipend) == s['boxes'] and not iunres, f'{where}: pending list')
        need(vol(ipend) == int(s['volume']), f'{where}: volume')
        need(ij['progress']['leaf_chain'] == init_chain(man['parent_sha256'], man['parent_leaf_chain'], s['name'], ipend),
             f'{where}: initial chain (a shard of another parent?)')
        need(sum(ij['progress']['depth_histogram']) == 0 and ij['progress']['boxes'] == 0, f'{where}: counters not zero')
        seen += ipend
        if (sd / 'split' / 'manifest.json').exists():
            sub = merge_dir(sd / 'split', partial, log, where)
            sman = json.loads((sd / 'split' / 'manifest.json').read_text())
            need(int(sman['parent_volume']) == int(s['volume']), f'{where}: sub-tree volume')
            need(sman['fingerprint'] == man['fingerprint'] and sman['sigma'] == man['sigma'], f'{where}: sub-tree fingerprint or sigma')
            stext, sj, spend, _ = read_ckpt(sd / 'split' / 'parent_checkpoint.json')
            need(inside(spend, ipend), f'{where}: sub-tree parent boxes are not inside this shard')
            r = sub; node = dict(name=s['name'], init_sha256=s['init_sha256'], split=sub['tree'])
        else:
            text2, j2, pend2, unres2 = read_ckpt(sd / 'checkpoint.json')
            need(j2['fingerprint'] == man['fingerprint'] and j2['depth_cap'] == man['depth_cap']
                 and j2['cell_depth'] == man['cell_depth'], f'{where}: fingerprint or caps')
            check_node(text2, j2, pend2, unres2, int(s['volume']), where)
            need(inside(pend2 + unres2, ipend), f'{where}: checkpoint boxes are not inside this shard (wrong directory?)')
            p2 = j2['progress']; rec = sd / 'receipt.json'
            if not partial:
                need(rec.exists(), f'{where}: no receipt')
                r2 = json.loads(rec.read_text())
                need(r2['status'] == 'complete' and r2['pending'] == 0 and r2['unresolved'] == 0, f'{where}: not complete')
                need(r2['leaf_chain'] == p2['leaf_chain'] and r2['boxes'] == p2['boxes']
                     and r2['depth_histogram'] == p2['depth_histogram'], f'{where}: receipt and checkpoint differ')
                need(r2['sigma'] == man['sigma'] and r2['max_depth_cap'] == man['depth_cap']
                     and r2['cell_depth'] == man['cell_depth'], f'{where}: sigma or caps in the receipt')
                cl = r2['command_line']
                need('--resume' in cl and cl[cl.index('--output') + 1].rstrip('/').endswith(f'/{s["name"]}'),
                     f'{where}: receipt is not a resumed run of this shard')
                need(not pend2 and not unres2, f'{where}: pending or unresolved left')
            node = dict(name=s['name'], init_sha256=s['init_sha256'], checkpoint_sha256=sha(text2),
                        receipt_sha256=sha(rec.read_bytes()) if rec.exists() else None)
            r = dict(boxes=p2['boxes'], bound=p2['leaves_by_rule']['bound'], outside=p2['leaves_by_rule']['outside'],
                     unresolved=len(unres2), lemmas=list(p2['lemma_counts']), max_depth=p2['max_depth'],
                     seconds=p2['seconds'], leaf_vol=leaf_vol(p2), pending=len(pend2), pending_vol=vol(pend2),
                     chains=[(where, p2['leaf_chain'])], shards=1)
            log.append(dict(shard=where, status=p2['status'], boxes=p2['boxes'], pending=len(pend2),
                            closed=leaf_vol(p2) / int(s['volume'])))
        need(r['leaf_vol'] + r['pending_vol'] == int(s['volume']), f'{where}: shard volume not conserved')
        tot['tree']['shards'].append(node)
        for k in ('boxes', 'bound', 'outside', 'unresolved', 'pending', 'leaf_vol', 'pending_vol', 'shards'): tot[k] += r[k]
        tot['lemmas'] = [x + y for x, y in zip(tot['lemmas'], r['lemmas'])]
        tot['max_depth'] = max(tot['max_depth'], r['max_depth']); tot['seconds'] += r['seconds']; tot['chains'] += r['chains']
    # the shards' initial lists are exactly the parent's pending boxes: same multiset, no repeats, nothing left out
    need(len(seen) == len(set(seen)), f'{path}: a box is in two shards')
    need(sorted(seen) == sorted(pend), f'{path}: shards are not a partition of the parent pending list '
         f'(missing {len(set(pend) - set(seen))}, foreign {len(set(seen) - set(pend))})')
    need(tot['leaf_vol'] + tot['pending_vol'] == v0, f'{path}: tree volume not conserved')
    return tot

def merge(a):
    out = Path(a.dir); log = []
    try:
        t = merge_dir(out, a.partial, log)
        if not a.partial:
            v0 = int(json.loads((out / 'manifest.json').read_text())['parent_volume'])
            need(a.subtree or v0 == ROOT, 'the top manifest is not the root (use --subtree only in tests)')
            need(t['pending'] == 0 and t['unresolved'] == 0 and t['leaf_vol'] == v0, 'not every box is closed')
    except Bad as e:
        print(json.dumps(dict(ok=False, error=str(e)))); sys.exit(1)
    man = json.loads((out / 'manifest.json').read_text())
    res = dict(ok=True, status='partial' if a.partial else 'complete', sigma=man['sigma'], fingerprint=man['fingerprint'],
               shards=t['shards'], boxes=t['boxes'], leaves_by_rule=dict(bound=t['bound'], outside=t['outside'], unresolved=t['unresolved']),
               pending=t['pending'], closed_volume_exact=f'{t["leaf_vol"]} / 2^256', closed_fraction=t['leaf_vol'] / ROOT,
               max_depth=t['max_depth'], lemma_counts=t['lemmas'], seconds=t['seconds'],
               merged_chain=sha('\n'.join(f'{w}:{c}' for w, c in t['chains'])), chains=dict(t['chains']),
               shard_status=log, tool_sha256=sha(Path(__file__).read_bytes()), tree=t['tree'],
               provenance=(f"leaves up to the checkpoint {man['parent_sha256']} ({t['tree']['parent_boxes']:,} boxes) are "
                           f"from the unsplit run that wrote it; after it, {t['shards']} shard runs of the same binary "
                           f"(fingerprint {man['fingerprint']}); see tree"))
    if not a.partial: (out / 'merged_receipt.json').write_text(json.dumps(res, indent=1))
    print(json.dumps({k: v for k, v in res.items() if k not in ('chains', 'shard_status', 'tree', 'provenance')}))

def main():
    ap = argparse.ArgumentParser(); sp = ap.add_subparsers(dest='cmd', required=True)
    s = sp.add_parser('split'); s.add_argument('checkpoint'); s.add_argument('dir'); s.add_argument('--n', type=int, required=True)
    s.add_argument('--sigma', required=True, help='as the checker prints it, e.g. 27/20 (checked against every receipt)')
    s.add_argument('--volume', default=None, help='initial volume of the node (x 2^-256); default the root, give the '
                   'shard volume from the manifest when splitting a shard')
    m = sp.add_parser('merge'); m.add_argument('dir'); m.add_argument('--partial', action='store_true')
    m.add_argument('--subtree', action='store_true', help='tests only: accept a top manifest whose parent is not the root')
    a = ap.parse_args()
    try: split(a) if a.cmd == 'split' else merge(a)
    except Bad as e: print(json.dumps(dict(ok=False, error=str(e)))); sys.exit(1)

if __name__ == '__main__': main()
