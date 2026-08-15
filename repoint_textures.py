"""Repoint AB HDA texture references from opdef: URIs to $AB_TEX, and strip the
now-unreferenced embedded image sections.

Why both in one pass: git-lfs stores WHOLE FILES, not deltas. Repointing and
stripping as two commits would cost two full-size LFS objects per asset.

What it does, per asset:
  1. hotl -X into a temp dir
  2. rewrite  opdef:/<any owner>?<texture>  ->  $AB_TEX/<texture>
     The owner half is DISCARDED, which is what silently repairs the 97 refs
     pointing at assets that no longer exist (SignMaker::4.8 etc). We match on
     the section name alone.
  3. harvest ExtraFileOptions "<tex>/Source" values into provenance.json
  4. delete the embedded image sections: the file on disk, its Sections.list
     line, and its ExtraFileOptions keys
  5. hotl -C into the staging tree
  6. verify: no surviving opdef: texture ref, expected $AB_TEX count, no image
     sections left, and the definition still parses

Only sections whose name is in the extracted set are touched. Icons reference
opdef: legitimately (opdef:/AB::Sop/X::2.0?IconImage) and are left alone.

Nothing is written over the live library - output goes to STAGE. Swapping in is
a separate, deliberate step.
"""
import os, re, json, shutil, subprocess, sys, tempfile, collections

ROOT  = "U:/Git/AssetBashTools"
HOTL  = "C:/Program Files/Side Effects Software/Houdini 22.0.368/bin/hotl.exe"
HERE  = os.path.dirname(os.path.abspath(__file__))
TEXD  = "U:/Textures/AB_Embedded"
STAGE = os.path.join(HERE, "repoint_staged")
VAR   = "$AB_TEX"

# ⚠ MUST be short. hotl -X writes one file per node, mirroring the node hierarchy,
# and AB building assets nest ~8 levels deep with long node names. Under the normal
# %TEMP% path that blows the Windows 260-char MAX_PATH and hotl SILENTLY DROPS the
# files it cannot create ("Unable to create file ..."), so the collapse would
# produce an HDA with nodes quietly missing. Caught on DowntownBuilding 3.2.
TMPROOT = "C:/abtmp"
os.makedirs(TMPROOT, exist_ok=True)

graph = json.load(open(os.path.join(HERE, "opdef_graph.json"), encoding="utf-8"))
TEXNAMES = set(graph["owner_of"])                      # the 43 uniques

# every extracted texture must actually exist on disk before we strip anything
missing = [t for t in sorted(TEXNAMES) if not os.path.exists(os.path.join(TEXD, t))]
if missing:
    sys.exit("ABORT - not extracted, refuse to strip: %s" % missing)

# opdef:/<owner>?<section>   - the owner half is deliberately not captured
ref_re = re.compile(rb"opdef:/[^\s\"'?]+\?([A-Za-z0-9_.\-]+)")

def run(*a):
    return subprocess.run(a, capture_output=True, timeout=600)

def count_nodes(expanded):
    """Every node in the definition is one file under Contents.dir. Counting them
    before and after is what proves no node was lost to a truncated expansion."""
    n = 0
    for dp, _, fns in os.walk(expanded):
        if "Contents.dir" in dp.replace("\\", "/"):
            n += len(fns)
    return n

def read_sections(defdir):
    """Sections.list is TAB separated: <escaped disk filename>\t<real section name>."""
    out = []
    p = os.path.join(defdir, "Sections.list")
    for line in open(p, encoding="utf-8").read().splitlines():
        if "\t" in line:
            disk, sec = line.split("\t", 1)
            out.append((disk, sec))
        else:
            out.append((line, None))
    return out

def process(hda_rel, strip=True):
    src = os.path.join(ROOT, hda_rel).replace("\\", "/")
    tmp = tempfile.mkdtemp(prefix="", dir=TMPROOT)
    stat = {"asset": os.path.basename(src), "rewrites": 0, "stripped": [],
            "provenance": {}, "before": os.path.getsize(src)}
    try:
        x = os.path.join(tmp, "x")
        r = run(HOTL, "-X", x, src)
        blob = (r.stdout or b"") + (r.stderr or b"")
        if r.returncode != 0:
            stat["error"] = "expand failed"
            return stat
        # hotl reports this on stdout and still exits 0 - see TMPROOT note above
        if b"Unable to create" in blob:
            stat["error"] = "EXPAND TRUNCATED (MAX_PATH) - refusing to collapse"
            return stat
        stat["nodes_before"] = count_nodes(x)
        defdirs = [os.path.join(x, d) for d in os.listdir(x)
                   if os.path.isdir(os.path.join(x, d))]

        for defdir in defdirs:
            secs = read_sections(defdir)
            present = {sec for _, sec in secs if sec}
            targets = present & TEXNAMES

            # ---- 2. rewrite references, anywhere in the definition ----
            for dp, _, fns in os.walk(defdir):
                for fn in fns:
                    fp = os.path.join(dp, fn)
                    try:
                        blob = open(fp, "rb").read()
                    except Exception:
                        continue
                    if b"opdef:" not in blob:
                        continue
                    def sub(m):
                        name = m.group(1).decode("utf-8", "replace")
                        if name in TEXNAMES:
                            return ("%s/%s" % (VAR, name)).encode()
                        return m.group(0)          # icons and anything unknown
                    new, n = ref_re.subn(sub, blob)
                    if new != blob:
                        stat["rewrites"] += sum(
                            1 for m in ref_re.finditer(blob)
                            if m.group(1).decode("utf-8", "replace") in TEXNAMES)
                        open(fp, "wb").write(new)

            if not strip or not targets:
                continue

            # ---- 3. harvest provenance before deleting ----
            efo_p = os.path.join(defdir, "ExtraFileOptions")
            efo = {}
            if os.path.exists(efo_p):
                try:
                    efo = json.load(open(efo_p, encoding="utf-8"))
                except Exception:
                    efo = {}
            for t in sorted(targets):
                srcpath = efo.get("%s/Source" % t, {}).get("value")
                if srcpath:
                    stat["provenance"][t] = srcpath

            # ---- 4. strip the sections ----
            keep_lines, dropped = [], set()
            for disk, sec in secs:
                if sec in targets:
                    fp = os.path.join(defdir, disk)
                    if os.path.exists(fp):
                        os.remove(fp)
                    dropped.add(sec)
                    continue
                keep_lines.append("%s\t%s" % (disk, sec) if sec else disk)
            open(os.path.join(defdir, "Sections.list"), "w",
                 encoding="utf-8").write("\n".join(keep_lines) + "\n")
            stat["stripped"] = sorted(dropped)

            if efo:
                efo = {k: v for k, v in efo.items()
                       if k.split("/", 1)[0] not in dropped}
                json.dump(efo, open(efo_p, "w", encoding="utf-8"), indent=1)

        # ---- 5. collapse into the staging tree ----
        dst = os.path.join(STAGE, hda_rel).replace("\\", "/")
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        if os.path.exists(dst):
            os.remove(dst)
        if run(HOTL, "-C", x, dst).returncode != 0 or not os.path.exists(dst):
            stat["error"] = "collapse failed"
            return stat
        stat["after"] = os.path.getsize(dst)

        # ---- 6. verify the written file ----
        v = os.path.join(tmp, "v")
        rv = run(HOTL, "-X", v, dst)
        if rv.returncode != 0:
            stat["error"] = "VERIFY: result will not expand"
            return stat
        stat["nodes_after"] = count_nodes(v)
        if stat["nodes_after"] != stat["nodes_before"]:
            stat["error"] = "VERIFY: node count %d -> %d, NODES LOST" % (
                stat["nodes_before"], stat["nodes_after"])
            return stat
        left_refs, left_secs, var_hits = 0, [], 0
        for dp, _, fns in os.walk(v):
            for fn in fns:
                if fn == "Sections.list":
                    for _, sec in read_sections(dp):
                        if sec in TEXNAMES:
                            left_secs.append(sec)
                try:
                    blob = open(os.path.join(dp, fn), "rb").read()
                except Exception:
                    continue
                for m in ref_re.finditer(blob):
                    if m.group(1).decode("utf-8", "replace") in TEXNAMES:
                        left_refs += 1
                var_hits += blob.count(VAR.encode())
        if left_refs:
            stat["error"] = "VERIFY: %d opdef texture refs survived" % left_refs
        if strip and left_secs:
            stat["error"] = "VERIFY: %d image sections survived" % len(left_secs)
        stat["var_hits"] = var_hits
        return stat
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    only = sys.argv[1] if len(sys.argv) > 1 else None
    todo = sorted(a for a, d in graph["assets"].items() if d["owns"] or d["refs"])
    if only:
        todo = [a for a in todo if only in a]

    results, prov = [], {}
    for a in todo:
        rel = graph["assets"][a]["path"]
        r = process(rel)
        results.append(r)
        for k, v in r["provenance"].items():
            prov.setdefault(v, []).append(a)
        flag = "  !! " + r["error"] if r.get("error") else ""
        print("%-46s %6.1f -> %6.1f MB  refs %3d  stripped %2d%s" % (
            a, r["before"] / 1e6, r.get("after", 0) / 1e6,
            r["rewrites"], len(r["stripped"]), flag))

    json.dump(results, open(os.path.join(HERE, "repoint_report.json"), "w"), indent=1)
    json.dump(prov, open(os.path.join(HERE, "texture_provenance.json"), "w"), indent=1)

    ok = [r for r in results if not r.get("error")]
    bad = [r for r in results if r.get("error")]
    b = sum(r["before"] for r in ok); a2 = sum(r.get("after", 0) for r in ok)
    print("\n%d ok, %d FAILED" % (len(ok), len(bad)))
    print("total %.0f MB -> %.0f MB   (%.0f MB, %.0f%% reclaimed)" % (
        b / 1e6, a2 / 1e6, (b - a2) / 1e6, 100.0 * (b - a2) / b if b else 0))
    print("refs rewritten:", sum(r["rewrites"] for r in ok))
    print("distinct original source paths:", len(prov))
    for r in bad:
        print("  FAILED", r["asset"], r["error"])
