import fcntl
import gzip
import json
from pathlib import Path
import pytest
import predicate_cover_campaign as campaign


def configuration(tmp_path):
    candidate=tmp_path/'candidate.txt';candidate.write_text('1 1\n10\n10\n1\n5 5 10\n')
    frontier=tmp_path/'frontier.json'
    frontier.write_text(json.dumps(dict(candidate_sha256=campaign.digest(candidate),pending=[
        dict(box=['0','1/5','2/5','3/5','0','1/100']),
        dict(box=['1/5','2/5','2/5','3/5','0','1/100']),
        dict(box=['2/5','3/5','2/5','3/5','0','1/100'])])))
    c=dict(id='test',parent=str(candidate),frontier=str(frontier),output=str(tmp_path/'output'),
           candidate_sha256=campaign.digest(candidate),frontier_sha256=campaign.digest(frontier),
           code_sha256=campaign.code_hashes(Path(campaign.__file__).parent),
           L='1',n=2,target='3/2',shard=0,shards=1,max_depth=1,max_cuts=0,
           branch_depth=0,branch_nodes=0,physical_cuts=0)
    path=tmp_path/'config.json';path.write_text(json.dumps(c));return path,c


def test_shards_are_disjoint_and_exhaustive():
    shards=[campaign.assigned_indices(38730,j,3) for j in range(3)]
    assert [len(s) for s in shards]==[12910]*3
    assert sorted(x for s in shards for x in s)==list(range(38730))
    with pytest.raises(ValueError):campaign.assigned_indices(4,3,3)


def test_resume_replays_artifacts_after_missing_journal(tmp_path,monkeypatch):
    path,c=configuration(tmp_path);first=campaign.run(path,track_ledger=False)
    assert first['certified']==3 and not first['general_coverage_verified']
    (Path(c['output'])/'summary.jsonl').unlink()
    def forbidden(*a,**k):raise AssertionError('Recomputed saved cover')
    monkeypatch.setattr(campaign,'cover',forbidden)
    resumed=campaign.run(path,track_ledger=False)
    assert resumed['resumed']==3 and resumed['certified']==3
    artifact=Path(c['output'])/'proofs/000002.json.gz'
    proof=json.loads(gzip.decompress(artifact.read_bytes()))
    proof['proof']['records'][0]['proof']['lower']='2'
    campaign.save_gzip(artifact,proof)
    with pytest.raises(ValueError,match='mismatch'):campaign.run(path,track_ledger=False)


def test_rejects_changed_inputs_policy_and_duplicate_runner(tmp_path):
    path,c=configuration(tmp_path);campaign.run(path,track_ledger=False)
    original=path.read_text();c['max_depth']=2;path.write_text(json.dumps(c))
    with pytest.raises(ValueError,match='configuration'):campaign.run(path,track_ledger=False)
    path.write_text(original)
    with (Path(c['output'])/'run.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        with pytest.raises(RuntimeError,match='already running'):campaign.run(path,track_ledger=False)
    Path(c['frontier']).write_text('{}')
    with pytest.raises(ValueError,match='Changed candidate or frontier'):campaign.run(path,track_ledger=False)
