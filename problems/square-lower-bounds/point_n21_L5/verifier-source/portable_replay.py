"""Replay with byte-preserving path relocation; no access to original source paths."""
from pathlib import Path
import argparse,hashlib,json,gzip,sys,runpy
ROOT=Path(__file__).resolve().parent
MANIFEST=json.loads((ROOT/'portable-manifest.json').read_text())
OLD=Path(MANIFEST['original_root']).resolve()
R=ROOT/'runs/evand_n21_n32_bridge_20260927/results'
READS={}

def forbid_original_tree(event,args):
    if event!='open' or not args or not isinstance(args[0],(str,bytes)):return
    p=Path(args[0].decode() if isinstance(args[0],bytes) else args[0]).resolve()
    if p.is_relative_to(OLD) and not p.is_relative_to(ROOT):
        raise PermissionError('Portable replay may not access original tree: '+str(p))

def locate(path):
    path=Path(path)
    if ".." in path.parts:raise ValueError("Parent traversal in source path")
    if not path.is_absolute():path=ROOT/path
    if not path.is_relative_to(ROOT):
        path=path.resolve()
        if path.is_relative_to(OLD):path=ROOT/path.relative_to(OLD)
    resolved=path.resolve()
    if not resolved.is_relative_to(ROOT):raise ValueError('Source outside portable root: '+str(path))
    rel=str(resolved.relative_to(ROOT))
    if rel not in MANIFEST['files']:raise ValueError('Source not in manifest: '+rel)
    return resolved,rel

def checked_bytes(path):
    path,rel=locate(path);raw=path.read_bytes();h=hashlib.sha256(raw).hexdigest()
    if h!=MANIFEST['files'][rel]['sha256']:raise ValueError('Changed portable source: '+rel)
    READS[rel]=h
    return raw

def sha(path):return hashlib.sha256(checked_bytes(path)).hexdigest()
def load(path,expected=None):
    raw=checked_bytes(path)
    if expected is not None and hashlib.sha256(raw).hexdigest()!=expected:raise ValueError('Original artifact SHA mismatch')
    return json.loads(gzip.decompress(raw) if str(path).endswith('.gz') else raw)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--stage',choices=['root','sieve','frontier'],required=True);ap.add_argument('--out',type=Path,required=True);ap.add_argument('--indices',type=int,nargs='+');ap.add_argument('--shard',type=int,default=0);ap.add_argument('--shards',type=int,default=1);a=ap.parse_args()
    if not __debug__:raise RuntimeError('Python optimization disables required assertions')
    sys.addaudithook(forbid_original_tree)
    # Check executable source before imports; all local imports remain in this tree.
    for rel in MANIFEST['files']:
        if rel.endswith('.py'):checked_bytes(ROOT/rel)
    sys.path.insert(0,str(R/'n21_L5_refit29_final_replay'))
    import frontier
    if frontier.ROOT!=ROOT:raise ValueError('Unexpected frontier root')
    frontier.sha=sha;frontier.load=load
    if a.stage=='frontier':
        from checkpoint_external_cover import atomic
        checker=frontier.Checker()
        assert 0<=a.shard<a.shards
        ids=a.indices if a.indices is not None else [i for i in sorted(checker.required) if i%a.shards==a.shard]
        assert len(ids)==len(set(ids)) and set(ids)<=checker.required
        a.out.mkdir(exist_ok=False,parents=True);(a.out/'proofs').mkdir()
        for index in ids:
            result=checker.parent(index);atomic(a.out/'proofs'/f'{index:06d}.json',result)
            print(index,result['lower'],flush=True)
        for rel,h in list(READS.items()):assert sha(ROOT/rel)==h
        atomic(a.out/'result.json',dict(status='PORTABLE_NUMERICAL_REPLAY',stage='frontier',indices=ids,candidate_sha256=checker.newsha,threshold=str(checker.q),inputs=READS,general_coverage_verified=False))
    else:
        if a.indices is not None or a.shard!=0 or a.shards!=1:raise ValueError('Prefix stages are indivisible')
        sys.argv=['run_prefix.py','--stage',a.stage,'--out',str(a.out)]
        runpy.run_path(str(R/'n21_L5_refit29_final_replay/run_prefix.py'),run_name='__main__')
        (a.out/'portable-reads.json').write_text(json.dumps(READS,indent=2)+'\n')
if __name__=='__main__':main()
