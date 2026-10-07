"""Re-prove the obstacle points and exclusion boxes of the five stage-2/3 certificates of n = 6.

For each certificate this reruns the generators with the parameters recorded in its `stage` field:
  * stage_inputs.py: inner points (exact check sqrt2*D + DTH*|w|_2 + |w|_inf < 1/2) and the partner exclusion boxes;
  * wall_witness2.py: wall witnesses (interval arithmetic plus the analytic chord step, see its header);
  * chain_witness.py: chain witnesses (case 1,3:0 only, see its header).
Each generator keeps only points it proves.  The script then checks that the certificate's obstacle_points are
exactly the union of the regenerated points and that its exclusions are exactly the regenerated boxes.
Run from problems/triangle (needs mpmath):  python certificates/n6/stage2/reprove_obstacles.py"""
import json, os, subprocess, sys, tempfile

HERE = "certificates/n6/stage2"
# certificate -> (wall-witness file kept for comparison, chain-witness arguments or None)
CERTS = {
    "cert_w_o1.json": ("ww2_o1_p0345.json", None),
    "cert_w_o0_p13_auto.json": ("ww2_o0_p13.json", None),
    "cert_s3u2.json": (None, None),
    "cert_o03d.json": ("ww2_o03_p1.json", None),
    "cert_o13b.json": ("ww2_o13_p0.json", ("41/2500", "3/250", "3/250")),
}


def tagof(case):
    o, p = case.split(":")
    return "o" + o.replace(",", "") + "_p" + p.replace(",", "")


def run(*args):
    r = subprocess.run([sys.executable, *args], capture_output=True, text=True)
    if r.returncode:
        sys.exit(f"failed: {' '.join(args)}\n{r.stderr}")
    return r.stdout.strip()


def key(p):
    return (p["x"], p["y"])


def main():
    bad = 0
    tmp = tempfile.mkdtemp()
    for cert, (wwfile, chain) in CERTS.items():
        c = json.load(open(f"{HERE}/{cert}"))
        st = c["stage"]
        case = st["case"]
        run(f"{HERE}/stage_inputs.py", case, st["D_obstacle"], st["DTH"], st["H"], st["STEP"], st["D_partner"], st["DTH_partner"])
        tag = tagof(case)
        gen = [f"{HERE}/{tag}.{ext}" for ext in ("inputs.json", "wit.json", "excl.json")]
        inp = json.load(open(gen[0]))
        for f in gen:
            os.remove(f)
        pts = [key(p) for p in inp["obstacle_points"]]
        n_inner = len(pts)
        n_wall = n_chain = 0
        if wwfile:
            out = os.path.join(tmp, wwfile)
            ref = json.load(open(f"{HERE}/{wwfile}"))
            run(f"{HERE}/wall_witness2.py", case, st["D_obstacle"], st["DTH"], out, ref["EPS"])
            ww = [key(p) for p in json.load(open(out))["points"]]
            if ww != [key(p) for p in ref["points"]]:
                print(f"  note: regenerated {wwfile} differs from the stored file")
            pts += ww; n_wall = len(ww)
        if chain:
            out = os.path.join(tmp, "chain.json")
            run(f"{HERE}/chain_witness.py", *chain, out)
            cw = [key(p) for p in json.load(open(out))["points"]]
            pts += cw; n_chain = len(cw)
        same_pts = sorted(pts) == sorted(key(p) for p in c["obstacle_points"])
        same_ex = inp["exclusions"] == c["exclusions"]
        ok = same_pts and same_ex
        bad += not ok
        print(f"{cert}: {n_inner} inner + {n_wall} wall + {n_chain} chain = {len(pts)} "
              f"(certificate {len(c['obstacle_points'])}); obstacle points {'match' if same_pts else 'DIFFER'}, "
              f"exclusions {'match' if same_ex else 'DIFFER'}")
    print("all re-proved" if not bad else f"{bad} certificate(s) differ")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
