"""INDEX.json must list exactly the ASSET.json files, with the same claim/assets/check; every ASSET.json has the
required fields and every listed document exists.  Does not touch releases."""
import json, sys
from pathlib import Path
R = Path(__file__).resolve().parents[2]
idx = json.loads((R / "INDEX.json").read_text())
listed = {x["path"]: x for v in idx["problems"].values() for x in v if "path" in x}
found = {str(p.relative_to(R)) for p in list(R.rglob("ASSET.json")) + list(R.rglob("*.ASSET.json"))}
err = []
if set(listed) != found:
    err.append(f"INDEX/ASSET mismatch: only in INDEX {sorted(set(listed) - found)[:5]}, only on disk {sorted(found - set(listed))[:5]}")
for p in sorted(found):
    a = json.loads((R / p).read_text())
    for k in ("id", "claim", "assets", "check", "check_cwd", "source"):
        if a.get(k) in (None, "") and not (k == "assets"): err.append(f"{p}: missing {k}")
    for d in a.get("documents", []):
        if not (R / d).exists(): err.append(f"{p}: document missing {d}")
    if not (R / a["check_cwd"]).is_dir(): err.append(f"{p}: check_cwd missing {a['check_cwd']}")
    x = listed.get(p)
    if x and (x["claim"] != a["claim"] or x["check"] != a["check"] or x["assets"] != [d["asset"] for d in a["assets"]]):
        err.append(f"{p}: differs from INDEX.json")
    for d in a["assets"]:
        if len(d.get("sha256", "")) != 64: err.append(f"{p}: bad sha256 for {d.get('asset')}")
print(f"{len(found)} ASSET.json, {len(err)} problems")
for e in err[:50]: print(" ", e)
sys.exit(1 if err else 0)
