"""Extract every embedded texture from the AB library to a shared folder.

Also hashes every copy, because dedup is only safe if the copies are byte-identical.
If two assets embed different images under the same name, extracting one and
repointing both would silently change how one of them looks.

Writes the files plus a manifest. Read-only with respect to the HDAs.
"""
import os, re, json, shutil, subprocess, tempfile, hashlib, collections

ROOT = r"U:/Git/AssetBashTools/Sops"
DEST = r"U:/Textures/AB_Embedded"
HOTL = r"C:/Program Files/Side Effects Software/Houdini 22.0.368/bin/hotl.exe"
HERE = os.path.dirname(os.path.abspath(__file__))

TEX = re.compile(r"\.(png|tga|jpg|jpeg|exr|tif|tiff|rat|hdr)$", re.I)

os.makedirs(DEST, exist_ok=True)

# name -> {sha1 -> {"size":n, "assets":[...], "src": path}}
variants = collections.defaultdict(dict)

hdas = []
for dp, dn, fn in os.walk(ROOT):
    if "backup" in dp.lower().replace("\\", "/"):
        continue
    for f in fn:
        if f.lower().endswith(".hda"):
            hdas.append(os.path.join(dp, f).replace("\\", "/"))

scratch = tempfile.mkdtemp(prefix="abtex_")
try:
    for i, p in enumerate(sorted(hdas), 1):
        asset = os.path.basename(p)
        d = os.path.join(scratch, "x")
        shutil.rmtree(d, ignore_errors=True)
        try:
            subprocess.run([HOTL, "-X", d, p], capture_output=True, timeout=300)
        except Exception:
            continue
        for ddp, _, ffn in os.walk(d):
            for f in ffn:
                if not TEX.search(f):
                    continue
                fp = os.path.join(ddp, f)
                try:
                    blob = open(fp, "rb").read()
                except Exception:
                    continue
                if len(blob) < 512:            # section stubs, not real images
                    continue
                h = hashlib.sha1(blob).hexdigest()
                v = variants[f].setdefault(h, {"size": len(blob), "assets": [], "blob": None})
                v["assets"].append(asset)
                if v["blob"] is None:
                    v["blob"] = blob
        shutil.rmtree(d, ignore_errors=True)
        if i % 40 == 0:
            print("  ...%d/%d hdas" % (i, len(hdas)))
finally:
    shutil.rmtree(scratch, ignore_errors=True)


def dims(blob, name):
    """Width/height without PIL - just enough header parsing for PNG and TGA."""
    try:
        if blob[:8] == b"\x89PNG\r\n\x1a\n":
            w = int.from_bytes(blob[16:20], "big"); h = int.from_bytes(blob[20:24], "big")
            return w, h
        if name.lower().endswith(".tga"):
            w = int.from_bytes(blob[12:14], "little"); h = int.from_bytes(blob[14:16], "little")
            return w, h
    except Exception:
        pass
    return None, None


manifest, conflicts = [], []
for name in sorted(variants):
    vs = variants[name]
    if len(vs) > 1:
        conflicts.append((name, vs))
    for j, (h, v) in enumerate(sorted(vs.items(), key=lambda kv: -len(kv[1]["assets"]))):
        out = name if j == 0 else "%s__variant%d%s" % (
            os.path.splitext(name)[0], j + 1, os.path.splitext(name)[1])
        with open(os.path.join(DEST, out), "wb") as fh:
            fh.write(v["blob"])
        w, hh = dims(v["blob"], name)
        manifest.append({
            "file": out, "original_name": name, "sha1": h, "bytes": v["size"],
            "width": w, "height": hh, "copies": len(v["assets"]),
            "assets": sorted(set(v["assets"])),
        })

json.dump(manifest, open(os.path.join(HERE, "texture_manifest.json"), "w"), indent=1)

print()
print("hdas scanned          :", len(hdas))
print("distinct texture names:", len(variants))
print("files written to      :", DEST, "(%d)" % len(manifest))
print("total copies found    :", sum(m["copies"] for m in manifest))
print("bytes written         : %.1f MB" % (sum(m["bytes"] for m in manifest) / 1e6))
print("bytes previously embedded: %.1f MB"
      % (sum(m["bytes"] * m["copies"] for m in manifest) / 1e6))
print()
if conflicts:
    print("!! SAME NAME, DIFFERENT IMAGE - dedup is NOT safe for these:")
    for name, vs in conflicts:
        print("   ", name)
        for h, v in vs.items():
            print("       %s  %8d bytes  %s" % (h[:10], v["size"], ", ".join(sorted(set(v["assets"])))))
else:
    print("all duplicate copies are byte-identical - dedup is safe")
print()
print("%-46s %10s %11s %s" % ("FILE", "BYTES", "PIXELS", "COPIES"))
for m in sorted(manifest, key=lambda m: -m["bytes"]):
    px = "%dx%d" % (m["width"], m["height"]) if m["width"] else "?"
    print("%-46s %10d %11s %5d" % (m["file"], m["bytes"], px, m["copies"]))
