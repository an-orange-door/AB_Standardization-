"""Audit NESTED sub-HDA versions inside every AB asset's definition.

ab_upgrade.py fixes stale instances in a SCENE. This finds the other problem: an
AB:: sub-asset baked into a producer HDA's definition at an old version, which stays
old for every customer until someone opens the parent and updates it.

Offline - hotl only, no Houdini, no licence. Read-only.
"""
import os, re, json, shutil, subprocess, collections, tempfile

ROOT = r"U:/Git/AssetBashTools/Sops"
HOTL = r"C:/Program Files/Side Effects Software/Houdini 22.0.368/bin/hotl.exe"
OUT  = os.path.join(os.path.dirname(os.path.abspath(__file__)), "nested_versions.json")

# AB::Name::MAJ.MIN as it appears in a Contents stream
type_re = re.compile(rb"\b(AB::[A-Za-z_][A-Za-z0-9_]*::\d+\.\d+)\b")
file_re = re.compile(r"^AB\.(.+?)\.(\d+\.\d+)\.hda$")

# what versions exist on disk, per tool
installed = collections.defaultdict(set)
paths = {}
for dp, dn, fn in os.walk(ROOT):
    if "backup" in dp.lower().replace("\\", "/"):
        continue
    for f in fn:
        if not f.lower().endswith(".hda"):
            continue
        m = file_re.match(f)
        if m:
            installed[m.group(1)].add(m.group(2))
            paths[(m.group(1), m.group(2))] = os.path.join(dp, f).replace("\\", "/")

def vkey(v):
    return tuple(int(x) for x in v.split("."))

newest = {t: max(vs, key=vkey) for t, vs in installed.items()}

results, scratch = {}, tempfile.mkdtemp(prefix="abnest_")
try:
    for (tool, ver), p in sorted(paths.items()):
        if ver != newest.get(tool):
            continue                       # only audit the latest of each tool
        d = os.path.join(scratch, "x")
        shutil.rmtree(d, ignore_errors=True)
        try:
            subprocess.run([HOTL, "-X", d, p], capture_output=True, timeout=300)
        except Exception:
            continue
        found = set()
        for ddp, _, ffn in os.walk(d):
            for f in ffn:
                try:
                    blob = open(os.path.join(ddp, f), "rb").read()
                except Exception:
                    continue
                for t in type_re.findall(blob):
                    found.add(t.decode("utf-8", "replace"))
        shutil.rmtree(d, ignore_errors=True)

        stale, missing = [], []
        self_type = "AB::%s::%s" % (tool, ver)
        for t in sorted(found):
            _, nm, v = t.split("::")
            if t == self_type:
                continue
            if nm not in installed:
                missing.append(t)
            elif v != newest[nm]:
                stale.append({"nested": t, "newest": "AB::%s::%s" % (nm, newest[nm])})
        if stale or missing:
            results["AB::%s::%s" % (tool, ver)] = {"stale": stale, "missing": missing}
finally:
    shutil.rmtree(scratch, ignore_errors=True)

json.dump({"newest": newest, "results": results}, open(OUT, "w"), indent=1)

nstale = sum(len(v["stale"]) for v in results.values())
nmiss  = sum(len(v["missing"]) for v in results.values())
print("tools audited (latest version each) :", len(newest))
print("assets containing a stale/missing nested AB asset:", len(results))
print("  stale nested references  :", nstale)
print("  missing nested types     :", nmiss)
print()
worst = collections.Counter()
for a, v in results.items():
    for s in v["stale"]:
        worst[(s["nested"], s["newest"])] += 1
print("most common stale nested sub-assets:")
for (old, new), c in worst.most_common(12):
    print("   %-38s -> %-30s in %2d assets" % (old, new, c))
print()
missw = collections.Counter()
for a, v in results.items():
    for m in v["missing"]:
        missw[m] += 1
if missw:
    print("nested types that DO NOT EXIST on disk:")
    for m, c in missw.most_common(12):
        print("   %-42s referenced by %2d assets" % (m, c))
print()
print("written:", OUT)
