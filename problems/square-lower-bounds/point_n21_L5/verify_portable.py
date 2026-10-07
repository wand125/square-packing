"""Fresh all-domain replay followed by exact assembly. No resume or subset mode."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import argparse
import datetime
import hashlib
import json
import os
import platform
import subprocess
import sys
import time


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--bundle", type=Path, default=Path(__file__).resolve().parent / "bundle")
    ap.add_argument("--workers", type=int, default=1)
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    if not __debug__:
        raise RuntimeError("Python -O disables required assertions")
    if a.workers < 1:
        raise ValueError("workers must be positive")
    bundle = a.bundle.resolve()
    out = a.out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    here = Path(__file__).resolve().parent
    paths = [Path(__file__), here / "assemble_portable.py",
             bundle / "portable_replay.py", bundle / "portable-manifest.json"]
    hashes = {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    env = os.environ.copy()
    for key in ["OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"]:
        env[key] = "1"
    started = time.monotonic()
    records = []
    meta = dict(started_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                python=sys.version, platform=platform.platform(), workers=a.workers, bindings=hashes)
    (out / "run-inputs.json").write_text(json.dumps(meta, indent=2) + "\n")

    def run_stage(stage, shard=None):
        name = stage if shard is None else f"frontier-s{shard}"
        args = [sys.executable, "-u", str(bundle / "portable_replay.py"),
                "--stage", stage, "--out", str(out / name)]
        if shard is not None:
            args += ["--shard", str(shard), "--shards", str(a.workers)]
        before = time.monotonic()
        with (out / f"{name}.log").open("x") as log:
            process = subprocess.run(args, env=env, stdout=log, stderr=subprocess.STDOUT)
        record = dict(stage=stage, shard=shard, argv=args, exit_code=process.returncode,
                      seconds=time.monotonic()-before)
        (out / f"{name}-exit.json").write_text(json.dumps(record, indent=2) + "\n")
        if process.returncode:
            raise RuntimeError(f"{name} failed: exit {process.returncode}; see {name}.log")
        return record

    try:
        records += [run_stage("root"), run_stage("sieve")]
        with ThreadPoolExecutor(max_workers=a.workers) as executor:
            futures = [executor.submit(run_stage, "frontier", i) for i in range(a.workers)]
            records += [f.result() for f in futures]
        for path, digest in hashes.items():
            assert hashlib.sha256(Path(path).read_bytes()).hexdigest() == digest
        from assemble_portable import assemble
        result = assemble(bundle, out / "root", out / "sieve",
                          [out / f"frontier-s{i}" for i in range(a.workers)])
        assert result["status"] == "PORTABLE_COMPLETE_REPLAY_LINKAGE"
        (out / "linkage.json").write_text(json.dumps(result, indent=2) + "\n")
        summary = dict(status="FRESH_ALL_DOMAIN_REPLAY_VERIFIED", candidate_sha256=result["candidate_sha256"],
                       root_count=5000, sieve_count=8758, frontier_count=31678, excluded_count=7052,
                       threshold=result["threshold"], mass=result["mass"], strict_gap=result["strict_gap"],
                       worker_exits=records, seconds=time.monotonic()-started,
                       linkage_sha256=hashlib.sha256((out / "linkage.json").read_bytes()).hexdigest(),
                       independent_external_review=False, formal_verification=False)
        for path, digest in hashes.items():
            assert hashlib.sha256(Path(path).read_bytes()).hexdigest() == digest
        (out / "result.json").write_text(json.dumps(summary, indent=2) + "\n")
        print(json.dumps(summary, indent=2))
    except BaseException as error:
        (out / "failure.json").write_text(json.dumps(dict(status="FAILED", error=repr(error)), indent=2) + "\n")
        raise


if __name__ == "__main__":
    main()
