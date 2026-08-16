"""Baseline SkyscraperGenerator BEFORE the footprint HDA is touched.

    hython U:/AB_Standardization/baseline_skyscraper.py

RUN WITH THE HOUDINI GUI CLOSED. Writes only the baseline JSON.

SkyscraperGenerator 2.1 is the only tool that already consumes
AB::BuildingFootprintGenerator, which makes it the free canary: if the rewrite
goes into that HDA and this tool's output changes, the repoint is wrong and we
find out before the other four tools are touched.

Without this capture the repoint is unfalsifiable — exactly the mistake that got
the MaterialStyle migration reverted, where 31 apparent failures turned out to
be pre-existing breakage nobody had baselined.

Captured per parameter combination:
    point / prim / vertex counts        gross shape
    bounding box                        overall massing
    primitive group names + SIZES       the group contract downstream tools read
    attribute names per class           so a silently dropped attribute shows up
    a position checksum                 cheap detection of any geometry change
"""
import hashlib
import itertools
import json
import os
import sys

import hou

LIB = "U:/Git/AssetBashTools"
OUT = "U:/AB_Standardization/baseline"
TARGET = "AB::SkyscraperGenerator::2.1"
FOOTPRINT = "BuildingFootprintGenerator"


def install():
    n = 0
    for root, dirs, files in os.walk(LIB):
        r = root.replace("\\", "/") + "/"
        if any(s in r for s in ("/backup/", "/OLD/", "/_Archive/", "/.git")):
            continue
        for f in sorted(files):
            if f.lower().endswith((".hda", ".otl")):
                try:
                    hou.hda.installFile(os.path.join(root, f)); n += 1
                except Exception:
                    pass
    return n


def capture(node):
    node.cook(force=True)
    g = node.geometry()
    rec = {
        "npoints": len(g.points()),
        "nprims": len(g.prims()),
        "nverts": sum(len(p.vertices()) for p in g.prims()),
    }
    b = g.boundingBox()
    rec["bbox"] = [round(c, 4) for c in (list(b.minvec()) + list(b.maxvec()))]
    # group NAMES and SIZES — the contract a repoint could silently change
    rec["prim_groups"] = {gr.name(): len(gr.prims()) for gr in g.primGroups()}
    rec["point_groups"] = {gr.name(): len(gr.points()) for gr in g.pointGroups()}
    rec["attribs"] = {
        "point": sorted(a.name() for a in g.pointAttribs()),
        "prim": sorted(a.name() for a in g.primAttribs()),
        "detail": sorted(a.name() for a in g.globalAttribs()),
        "vertex": sorted(a.name() for a in g.vertexAttribs()),
    }
    # a checksum over positions: cheap, and any geometry change moves it
    h = hashlib.sha1()
    for p in g.points():
        h.update(("%.4f,%.4f,%.4f;" % tuple(p.position())).encode())
    rec["pos_sha1"] = h.hexdigest()
    return rec


def main():
    print("installed %d" % install())
    nt = hou.nodeType(hou.sopNodeTypeCategory(), TARGET)
    if nt is None:
        print("!! %s not found" % TARGET); return 1
    print("target: %s" % nt.definition().libraryFilePath())

    holder = hou.node("/obj").createNode("geo", "SkyBase")
    probe = holder.createNode(TARGET, "probe")
    probe.allowEditingOfContents()

    # where does it consume the footprint tool, and how many instances?
    users = [c for c in probe.allSubChildren(top_down=True, recurse_in_locked_nodes=True)
             if FOOTPRINT in c.type().name()]
    print("footprint instances inside: %d" % len(users))
    for u in users:
        print("   %s   type=%s" % (u.path().split("probe", 1)[-1], u.type().name()))

    # the parms worth sweeping — whatever it exposes that drives the footprint
    names = [p.name() for p in probe.parms()]
    interesting = [n for n in ("BuildingShape", "BuildingWidth", "BuildingDepth",
                               "BldCornerSize", "ModuleWidth", "Floors", "Height")
                   if n in names]
    print("sweepable parms: %s" % ", ".join(interesting))
    probe.destroy()

    data = {"target": TARGET, "cases": {}}
    combos = list(itertools.product(
        [0, 1, 2] if "BuildingShape" in interesting else [None],
        [100.0, 60.0] if "BuildingWidth" in interesting else [None],
        [100.0, 140.0] if "BuildingDepth" in interesting else [None],
        [4.0, 12.0] if "BldCornerSize" in interesting else [None]))

    n_ok = n_err = 0
    for shape, W, D, C in combos:
        node = holder.createNode(TARGET, None)     # FRESH instance every time
        for nm, v in (("BuildingShape", shape), ("BuildingWidth", W),
                      ("BuildingDepth", D), ("BldCornerSize", C)):
            if v is not None and node.parm(nm) is not None:
                node.parm(nm).set(v)
        key = "%s|%s|%s|%s" % (shape, W, D, C)
        try:
            data["cases"][key] = capture(node)
            n_ok += 1
        except hou.Error as e:
            data["cases"][key] = {"ERROR": str(e).split("\n")[0][:120]}
            n_err += 1
        node.destroy()
        print("  %-22s %s" % (key, "ok" if key in data["cases"]
                              and "ERROR" not in data["cases"][key] else "ERROR"))
        sys.stdout.flush()

    if not os.path.isdir(OUT):
        os.makedirs(OUT)
    path = os.path.join(OUT, "skyscraper_baseline.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=1)
    print("")
    print("captured %d cases (%d errored)" % (n_ok, n_err))
    print("wrote %s (%.0f KB)" % (path, os.path.getsize(path) / 1024.0))

    # what the group contract looks like, so a change is legible later
    allg = {}
    for v in data["cases"].values():
        for gname, size in v.get("prim_groups", {}).items():
            allg.setdefault(gname, set()).add(size)
    print("")
    print("=== prim groups it emits (name -> sizes seen) ===")
    for gname in sorted(allg):
        sizes = sorted(allg[gname])
        print("   %-28s %s" % (gname, sizes if len(sizes) < 6 else
                               "%d distinct sizes" % len(sizes)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
