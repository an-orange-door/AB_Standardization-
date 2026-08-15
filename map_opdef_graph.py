"""Map the embedded-texture dependency graph across the whole AB library.

For every .hda: which image sections does it OWN, and which opdef: textures does it
REFERENCE (including ones owned by other assets). Offline - hotl only, no Houdini.

Writes opdef_graph.json + a summary to stdout.
"""
import os, re, json, shutil, subprocess, collections, tempfile

ROOT = r"U:/Git/AssetBashTools/Sops"
HOTL = r"C:/Program Files/Side Effects Software/Houdini 22.0.368/bin/hotl.exe"
OUT  = os.path.join(os.path.dirname(os.path.abspath(__file__)), "opdef_graph.json")
IMG  = (".png", ".jpg", ".jpeg", ".tga", ".tif", ".tiff", ".exr", ".bmp", ".hdr")

ref_re = re.compile(rb"opdef:/([^\s\"'?]+)\?([A-Za-z0-9_.\-]+)")

def sections(path):
    try:
        r = subprocess.run([HOTL, "-V", path], capture_output=True, text=True, timeout=180)
    except Exception:
        return []
    m = re.search(r"^Sections:\s*$", r.stdout, re.M)
    if not m:
        return []
    return [l.strip() for l in r.stdout[m.end():].splitlines() if l.strip()]

def refs(path, scratch):
    d = os.path.join(scratch, "x")
    shutil.rmtree(d, ignore_errors=True)
    try:
        subprocess.run([HOTL, "-X", d, path], capture_output=True, timeout=300)
    except Exception:
        return []
    found = set()
    for dp, _, fn in os.walk(d):
        for f in fn:
            try:
                blob = open(os.path.join(dp, f), "rb").read()
            except Exception:
                continue
            for owner, sec in ref_re.findall(blob):
                found.add((owner.decode("utf-8", "replace"), sec.decode("utf-8", "replace")))
    shutil.rmtree(d, ignore_errors=True)
    return sorted(found)

assets, n = {}, 0
scratch = tempfile.mkdtemp(prefix="abopdef_")
try:
    for dp, dn, fn in os.walk(ROOT):
        if "/backup" in dp.lower().replace("\\", "/"):
            continue
        for name in sorted(fn):
            if not name.lower().endswith(".hda"):
                continue
            p = os.path.join(dp, name).replace("\\", "/")
            secs = sections(p)
            owned = [s for s in secs if s.lower().endswith(IMG)]
            rr = refs(p, scratch)
            texrefs = [(o, s) for o, s in rr if s.lower().endswith(IMG)]
            if owned or texrefs:
                assets[name] = {
                    "path": p.replace("U:/Git/AssetBashTools/", ""),
                    "size": os.path.getsize(p),
                    "owns": owned,
                    "refs": ["%s?%s" % (o, s) for o, s in texrefs],
                }
            n += 1
finally:
    shutil.rmtree(scratch, ignore_errors=True)

# ---- analysis -------------------------------------------------------------
owner_of = {}
for a, d in assets.items():
    for s in d["owns"]:
        owner_of.setdefault(s, []).append(a)

referenced = collections.Counter()
cross = []
for a, d in assets.items():
    selfname = re.sub(r"^AB\.", "", a).rsplit(".hda", 1)[0]
    for r in d["refs"]:
        owner, sec = r.split("?", 1)
        referenced[sec] += 1
        short = owner.rsplit("/", 1)[-1].split("::")[0]
        if short not in a:
            cross.append({"asset": a, "needs_from": short, "texture": sec})

orphans = sorted(s for s in owner_of if referenced[s] == 0)
dupes = {s: v for s, v in owner_of.items() if len(v) > 1}

json.dump({"assets": assets,
           "owner_of": owner_of,
           "cross_asset_refs": cross,
           "orphan_sections": orphans,
           "duplicated_sections": dupes}, open(OUT, "w"), indent=1)

print("hdas scanned                :", n)
print("assets owning or referencing:", len(assets))
print("distinct image sections     :", len(owner_of))
print("sections embedded in >1 asset:", len(dupes))
print("ORPHANS (embedded, never referenced):", len(orphans))
print("CROSS-ASSET references      :", len(cross))
print()
print("worst duplication:")
for s, v in sorted(dupes.items(), key=lambda kv: -len(kv[1]))[:8]:
    print("   %-42s in %2d assets" % (s, len(v)))
print()
print("cross-asset dependencies (asset -> needs):")
seen = set()
for c in cross:
    k = (c["asset"], c["needs_from"])
    if k in seen: continue
    seen.add(k)
    print("   %-36s needs %s" % (c["asset"], c["needs_from"]))
print()
print("orphan examples:", orphans[:8])
print("written:", OUT)
