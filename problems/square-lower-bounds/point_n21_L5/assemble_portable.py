"""Check linkage of fresh portable replays; never replaces numerical replay.

This intentionally has no exception for a failed worker. Public reproduction must
run the numerical stages first, check every exit code, then call this assembler.
"""
from pathlib import Path
from fractions import Fraction as F
from collections import defaultdict
import argparse
import hashlib
import importlib.util
import json
import sys


def assemble(bundle, root_output, sieve_output, frontier_outputs):
    if not __debug__:
        raise RuntimeError("Python -O disables required assertions")
    bundle = Path(bundle).resolve()
    spec = importlib.util.spec_from_file_location("portable_io", bundle / "portable_replay.py")
    io = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(io)
    # Bind all executable sources before importing any checker implementation.
    for rel in io.MANIFEST["files"]:
        if rel.endswith(".py"):
            io.checked_bytes(bundle / rel)
    sys.path.insert(0, str(io.R / "n21_L5_refit29_final_replay"))
    import frontier
    assert frontier.ROOT == bundle
    frontier.sha, frontier.load = io.sha, io.load
    ch = frontier.Checker()
    candidate = ch.newsha
    assert candidate == "84a7dae793f05ff72de52ddcd3058e8518c1f84c461f94d11305adefe6137679"
    assert ch.q == F(249987, 250000)
    weights = defaultdict(F)
    for (x, y), w in zip(ch.c, ch.v):
        assert 0 <= x <= 5 and 0 <= y <= 5 and w >= 0
        weights[x, y] += w
    for (x, y), w in list(weights.items()):
        assert all(weights.get(p, F()) == w for p in [(5-x, y), (x, 5-y), (y, x)])
    mass = sum(weights.values(), F())
    assert mass == F(2624862500021, 125000000000) < 21 * ch.q
    artifacts = {}

    def read(path):
        path = Path(path).resolve()
        raw = path.read_bytes()
        artifacts[str(path)] = hashlib.sha256(raw).hexdigest()
        return json.loads(raw)

    def check_reads(bindings):
        assert bindings
        for rel, digest in bindings.items():
            assert io.sha(bundle / rel) == digest

    def exact_files(folder, indices):
        assert {p.name for p in (folder / "proofs").iterdir()} == {
            f"{i:06d}.json" for i in indices
        }

    prefix = []
    for stage, folder, count, repairs in [
        ("root", Path(root_output), 5000, 12),
        ("sieve", Path(sieve_output), 8758, 104),
    ]:
        assert read(folder / "progress.json")["status"] == "COMPLETED"
        result = read(folder / "result.json")
        assert result["stage"] == stage
        assert result["candidate_sha256"] == candidate and F(result["threshold"]) == ch.q
        assert result["local_parts_numerically_replayed"] is True
        assert result["complete_stage_partition_verified"] is True
        assert result["counts"]["repairs"] == repairs
        inputs = read(folder / "inputs.json")
        assert inputs["candidate_sha256"] == candidate and inputs["stage"] == stage
        for path, digest in inputs["bindings"].items():
            assert io.sha(path) == digest
        check_reads(read(folder / "portable-reads.json"))
        exact_files(folder, range(count))
        prefix.append(result)
    root, sieve = prefix
    transfer = io.load(io.R / "n21_L5_refit29_root_transfer_trial/frontier-output.json")
    assert root["pending"] == transfer["inherited_pending"] and len(root["pending"]) == 8758
    assert sieve["pending"] == ch.f["pending"] and len(sieve["pending"]) == 38730
    for i in range(5000):
        d = read(Path(root_output) / "proofs" / f"{i:06d}.json")
        x, z = divmod(i, 200)
        y, t = divmod(z, 8)
        assert d["index"] == i and d["local_parts_numerically_replayed"] is True
        assert frontier.boxkey(d["root"]) == (
            F(x, 10), F(x+1, 10), F(y, 10), F(y+1, 10), F(t, 16), F(t+1, 16))
    for i, parent in enumerate(root["pending"]):
        d = read(Path(sieve_output) / "proofs" / f"{i:06d}.json")
        assert d["index"] == i and frontier.boxkey(d["parent"]) == frontier.boxkey(parent["box"])
        assert d["partition_recomputed"] is True and d["local_parts_numerically_replayed"] is True
    used = set()
    minimum = None
    for folder in map(Path, frontier_outputs):
        result = read(folder / "result.json")
        assert result["status"] == "PORTABLE_NUMERICAL_REPLAY" and result["stage"] == "frontier"
        assert result["candidate_sha256"] == candidate and F(result["threshold"]) == ch.q
        check_reads(result["inputs"])
        ids = result["indices"]
        assert ids and len(ids) == len(set(ids))
        assert not used.intersection(ids) and set(ids) <= ch.required
        exact_files(folder, ids)
        for i in ids:
            used.add(i)
            d = read(folder / "proofs" / f"{i:06d}.json")
            assert d["index"] == i and d["candidate_sha256"] == candidate
            assert d["source_sha256"] == ch.m["entries"][i]["sha256"]
            assert frontier.boxkey(d["parent"]) == frontier.boxkey(sieve["pending"][i]["box"])
            assert d["partition_recomputed"] is True and d["numerically_replayed"] is True
            frontier.validate_partition(d["parent"], [z["box"] for z in d["leaves"]])
            values = []
            for leaf in d["leaves"]:
                if leaf["lower"] is None:
                    assert leaf["method"] in ["GEOMETRIC_EMPTY", "SOURCE_GEOMETRIC_EMPTY",
                                              "DIRECT_EMPTY", "EXTENDED_EMPTY", "MODEL_EMPTY"]
                else:
                    value = F(leaf["lower"])
                    assert value >= ch.q
                    values.append(value)
            lower = min(values, default=None)
            assert (None if d["lower"] is None else F(d["lower"])) == lower
            if lower is not None:
                minimum = lower if minimum is None else min(minimum, lower)
    assert used == ch.required and len(used) == 31678
    excluded = set(range(38730)) - used
    assert len(excluded) == 7052
    assert all(F(sieve["pending"][i]["box"][4]) > F(5, 12) for i in excluded)
    assert F(17, 12)**2 > 2  # sqrt(2)-1 < 5/12
    # Upper bound: distinct integer unit cells, all in the 5 by 5 container.
    cells = [(x, y) for x in range(5) for y in range(4)] + [(0, 4)]
    assert len(set(cells)) == 21 and all(0 <= x < 5 and 0 <= y < 5 for x, y in cells)
    for path, digest in artifacts.items():
        assert hashlib.sha256(Path(path).read_bytes()).hexdigest() == digest
    for rel, digest in list(io.READS.items()):
        assert io.sha(bundle / rel) == digest
    return dict(status="PORTABLE_COMPLETE_REPLAY_LINKAGE", candidate_sha256=candidate,
                root_count=5000, sieve_count=8758, frontier_count=len(used), excluded_count=len(excluded),
                mass=str(mass), threshold=str(ch.q), strict_gap=str(21*ch.q-mass),
                minimum_frontier_leaf=str(minimum), source_reads=io.READS, output_bindings=artifacts,
                numerical_replay_must_precede_assembly=True,
                independent_external_review=False, formal_verification=False)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--bundle", type=Path, required=True)
    ap.add_argument("--root-output", type=Path, required=True)
    ap.add_argument("--sieve-output", type=Path, required=True)
    ap.add_argument("--frontier-output", type=Path, nargs="+", required=True)
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    if a.out.exists():
        raise FileExistsError(a.out)
    result = assemble(a.bundle, a.root_output, a.sieve_output, a.frontier_output)
    a.out.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({k: v for k, v in result.items() if k not in ["source_reads", "output_bindings"]}))
