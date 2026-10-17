#!/usr/bin/env python3
"""Rebuild valid7-lean-v2 and compare its statement and axioms with expected/.

    verify.py LEAN_DIR [--jobs N]

LEAN_DIR is the `lean/` directory of a checkout of the library commit named in README.md, with the
generated sources unpacked by fetch.sh.  The script
  1. checks the library files of the import closure against library.sha256,
  2. builds the library modules the roots import (`lake build`),
  3. checks every generated module with `lake env lean -o`, in import order, N at a time,
  4. checks Sqpack/V7/Main.lean and runs Axioms7.lean (this folder),
  5. compares the `#check` and `#print axioms` lines with expected/statement.txt and expected/axioms.txt.
It prints VERIFIED only when every module returned 0 and both comparisons agree.
"""
import argparse, hashlib, os, re, subprocess, sys
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
LIB = ["Sqpack.ExTreeTilt", "Sqpack.ValidSplit7", "Sqpack.V7.Bridge", "Sqpack.V7.Data", "Sqpack.LemmaEDec",
       "Sqpack.LemmaESplit", "Sqpack.CapK", "Sqpack.ExTreeX", "Sqpack.LemmaESplitX", "Sqpack.LemmaELeafX",
       "Sqpack.LemmaEKM", "Sqpack.RowMinN"]
IMP = re.compile(r"^import (Sqpack\.V7\.R\S+)", re.M)


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def fail(msg):
    print("NOT VERIFIED:", msg)
    sys.exit(1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("lean_dir")
    ap.add_argument("--jobs", type=int, default=os.cpu_count())
    a = ap.parse_args()
    L = os.path.abspath(a.lean_dir)
    # 1. the library
    for line in open(os.path.join(HERE, "library.sha256")):
        s, p = line.split(None, 1)
        p = p.strip()
        if not os.path.exists(os.path.join(L, p)) or sha(os.path.join(L, p)) != s:
            fail(f"library file differs: {p}")
    # 2. its modules
    if subprocess.run(["lake", "build"] + LIB, cwd=L).returncode:
        fail("lake build of the library")
    # 3. the generated modules, in import order
    src = os.path.join(L, "Sqpack", "V7")
    mods = {}
    for d, _, fs in os.walk(src):
        for f in fs:
            p = os.path.join(d, f)
            rel = os.path.relpath(p, L)
            if f.endswith(".lean") and rel.startswith(os.path.join("Sqpack", "V7", "R")):
                mods[rel[:-5].replace(os.sep, ".")] = set(IMP.findall(open(p).read()))
    print(len(mods), "generated modules")
    done, order = set(), []
    while len(done) < len(mods):
        wave = [m for m in mods if m not in done and mods[m] <= done]
        if not wave:
            fail("import cycle or missing module")
        order.append(wave); done |= set(wave)
    B = os.path.join(L, ".lake", "build", "lib", "lean")

    def lean_o(m):
        p = m.replace(".", "/")
        os.makedirs(os.path.dirname(os.path.join(B, p)), exist_ok=True)
        r = subprocess.run(["lake", "env", "lean", "-o", os.path.join(B, p + ".olean"), p + ".lean"], cwd=L,
                           capture_output=True, text=True)
        return m, r.returncode, (r.stdout + r.stderr)[-500:]

    for i, wave in enumerate(order):
        with ThreadPoolExecutor(a.jobs) as ex:
            for m, rc, out in ex.map(lean_o, wave):
                if rc:
                    fail(f"{m}: {out}")
        print(f"wave {i + 1}/{len(order)}: {len(wave)} modules", flush=True)
    # 4. Main and the axioms
    m, rc, out = lean_o("Sqpack.V7.Main")
    if rc:
        fail(f"Main: {out}")
    r = subprocess.run(["lake", "env", "lean", os.path.join(HERE, "Axioms7.lean")], cwd=L, capture_output=True,
                       text=True)
    if r.returncode:
        fail("Axioms7.lean: " + (r.stdout + r.stderr)[-500:])
    got = [l for l in r.stdout.splitlines() if l.strip()]
    # 5. the comparison
    want_s = [l for l in open(os.path.join(HERE, "expected", "statement.txt")).read().splitlines() if l.strip()]
    want_a = [l for l in open(os.path.join(HERE, "expected", "axioms.txt")).read().splitlines() if l.strip()]
    got_a = [l for l in got if "depends on axioms" in l]
    got_s = [l for l in got if "depends on axioms" not in l]
    if got_s != want_s:
        fail("statement differs:\n" + "\n".join(got_s))
    if got_a != want_a:
        fail("axioms differ:\n" + "\n".join(got_a))
    print("VERIFIED")


if __name__ == "__main__":
    main()
