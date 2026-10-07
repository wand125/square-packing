"""Run bb_rig.py over many excused boxes with several worker processes; one JSON line per box in the results
file, so an interrupted run resumes (boxes already in the file are skipped).
Usage: python bb_rig_batch.py --workers 16 --out rig_results.jsonl [--boxes 0-741] [--eps 0.004]
"""
import argparse, json, os, subprocess, sys, time
from multiprocessing import Pool

HERE = os.path.dirname(os.path.abspath(__file__))


def one(args):
    k, eps, py = args
    t0 = time.time()
    r = subprocess.run([py, os.path.join(HERE, "bb_rig.py"), "--box", str(k), "--eps", str(eps)],
                       capture_output=True, text=True, env=dict(os.environ, NUMBA_NUM_THREADS="1",
                                                                OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1"))
    line = [l for l in r.stdout.splitlines() if l.startswith("box ")]
    return {"box": k, "eps": eps, "line": line[-1] if line else None, "proved": bool(line and "PROVED" in line[-1]),
            "seconds": round(time.time() - t0, 1), "returncode": r.returncode, "stderr_tail": r.stderr[-400:]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=2)
    ap.add_argument("--out", default="rig_results.jsonl")
    ap.add_argument("--boxes", default="0-741")
    ap.add_argument("--eps", type=float, default=0.004)
    a = ap.parse_args()
    lo, hi = map(int, a.boxes.split("-"))
    done = set()
    if os.path.exists(a.out):
        for l in open(a.out):
            try:
                d = json.loads(l)
                if d.get("line"):
                    done.add(d["box"])
            except Exception:
                pass
    todo = [k for k in range(lo, hi + 1) if k not in done]
    print(f"{len(todo)} boxes to do ({len(done)} already in {a.out})", flush=True)
    # warm the numba cache once
    subprocess.run([sys.executable, os.path.join(HERE, "bb_rig.py"), "--box", str(todo[0] if todo else 0), "--eps", "0.5"],
                   capture_output=True)
    with Pool(a.workers) as pool, open(a.out, "a") as f:
        for res in pool.imap_unordered(one, [(k, a.eps, sys.executable) for k in todo]):
            f.write(json.dumps(res) + "\n"); f.flush()
            print(f"box {res['box']}: {'PROVED' if res['proved'] else 'NOT PROVED'} {res['seconds']}s", flush=True)


if __name__ == "__main__":
    main()
