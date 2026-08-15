"""PHASE 0 — capture the BEFORE state of the footprint tools. Writes no .hda.

    hython U:/AB_Standardization/footprint_baseline.py

RUN WITH THE HOUDINI GUI CLOSED — one FX seat.

WHY THIS EXISTS, AND WHY IT COMES FIRST
The MaterialStyle migration was reverted because 31 "failures" turned out to be
pre-existing breakage that nobody had measured beforehand. The rewrite could not
be judged because there was no BEFORE. This script is the oracle that makes the
footprint rewrite falsifiable: run it now, run it again after, diff.

WHAT IT CAPTURES, per parameter combination
    ordered point positions      - the sweep/extrude seam depends on vertex order
    sorted point positions       - so "shape right, winding wrong" is separable
                                   from "maths wrong", which is a much smaller fix
    signed area                  - winding. A footprint is EXTRUDED, so this
                                   decides which way the wall normals face; the
                                   MetalExtrusionMaker rewrite was caught by
                                   exactly this and nothing else
    every group + MEMBERSHIP     - not just the names. The names are being
                                   standardised deliberately, so the thing that
                                   must not change is WHICH ELEMENTS are in each
                                   group. Membership is the real contract
    prim/point counts, bbox      - cheap sanity
    attributes                   - so a silently dropped attribute is visible

⚠ Groups are captured as SORTED MEMBER INDICES, deliberately. After the rename
`WallLeft` becomes `Wall_01`; the test is that some new group has exactly the old
membership, not that the old name survives.
"""
import itertools
import json
import os
import sys

import hou

LIB = "U:/Git/AssetBashTools"
OUT = "U:/AB_Standardization/baseline"

TARGET = "AB::BuildingFootprintGenerator::1.0"

# the sweep. Deliberately includes degenerate combinations - a corner larger than
# the wall it sits on is exactly where a rewrite diverges quietly.
WIDTHS = (100.0, 40.0, 250.0)
DEPTHS = (100.0, 60.0, 180.0)
CORNERS = (4.0, 0.5, 25.0)
MODULES = (10.0, 25.0)


def install_all():
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


def signed_area_xz(geo):
    """Shoelace on XZ — a footprint lies in the ground plane, not XY."""
    pts = [p.position() for p in geo.points()]
    a = 0.0
    n = len(pts)
    for i in range(n):
        x1, z1 = pts[i][0], pts[i][2]
        x2, z2 = pts[(i + 1) % n][0], pts[(i + 1) % n][2]
        a += x1 * z2 - x2 * z1
    return a * 0.5


def capture(node):
    node.cook(force=True)
    g = node.geometry()
    rec = {}
    rec["npoints"] = len(g.points())
    rec["nprims"] = len(g.prims())
    pos = [[round(c, 5) for c in p.position()] for p in g.points()]
    rec["points_ordered"] = pos
    rec["points_sorted"] = sorted(pos)
    rec["signed_area_xz"] = round(signed_area_xz(g), 6)
    b = g.boundingBox()
    rec["bbox"] = [round(c, 5) for c in (list(b.minvec()) + list(b.maxvec()))]

    # groups by MEMBERSHIP, which is what actually has to survive the rename
    groups = {}
    for gr in g.pointGroups():
        groups["point:" + gr.name()] = sorted(p.number() for p in gr.points())
    for gr in g.primGroups():
        groups["prim:" + gr.name()] = sorted(p.number() for p in gr.prims())
    for gr in g.edgeGroups():
        groups["edge:" + gr.name()] = len(gr.edges())
    rec["groups"] = groups

    rec["attribs"] = {
        "point": sorted(a.name() for a in g.pointAttribs()),
        "prim": sorted(a.name() for a in g.primAttribs()),
        "detail": sorted(a.name() for a in g.globalAttribs()),
        "vertex": sorted(a.name() for a in g.vertexAttribs()),
    }
    return rec


def main():
    if not os.path.isdir(OUT):
        os.makedirs(OUT)
    print("installed %d files" % install_all())

    nt = hou.nodeType(hou.sopNodeTypeCategory(), TARGET)
    if nt is None:
        print("!! %s not found" % TARGET); return 1
    print("target: %s" % nt.definition().libraryFilePath())

    holder = hou.node("/obj").createNode("geo", "Baseline")
    data = {"target": TARGET,
            "menu": list(nt.parmTemplateGroup().find("BuildingShape").menuLabels()),
            "cases": {}}

    n_ok = n_err = 0
    for shape in range(3):                       # 0 Rectangular, 1 L, 2 Rounded
        for W, D, C, M in itertools.product(WIDTHS, DEPTHS, CORNERS, MODULES):
            node = holder.createNode(TARGET, None)   # FRESH every time
            for p, v in (("BuildingShape", shape), ("BuildingWidth", W),
                         ("BuildingDepth", D), ("BldCornerSize", C),
                         ("ModuleWidth", M)):
                if node.parm(p) is not None:
                    node.parm(p).set(v)
            key = "%d|%g|%g|%g|%g" % (shape, W, D, C, M)
            try:
                data["cases"][key] = capture(node)
                n_ok += 1
            except hou.Error as e:
                data["cases"][key] = {"ERROR": str(e).split("\n")[0][:120]}
                n_err += 1
            node.destroy()
        print("  shape %d done (%d cases)" % (shape, len(WIDTHS)*len(DEPTHS)*len(CORNERS)*len(MODULES)))
        sys.stdout.flush()

    path = os.path.join(OUT, "footprint_baseline.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=1)

    # a human-readable summary beside the machine-readable oracle
    allg = {}
    for k, v in data["cases"].items():
        for gname, members in v.get("groups", {}).items():
            allg.setdefault(gname, set()).add(k.split("|")[0])
    print("")
    print("cases captured : %d  (errors: %d)" % (n_ok, n_err))
    print("wrote %s  (%.0f KB)" % (path, os.path.getsize(path)/1024.0))
    print("")
    print("=== every group the tool emits, and which shapes emit it ===")
    for gname in sorted(allg):
        print("   %-34s shapes %s" % (gname, ",".join(sorted(allg[gname]))))
    print("")
    print("=== winding, per shape (sign must be consistent) ===")
    for shape in range(3):
        areas = [v.get("signed_area_xz") for k, v in data["cases"].items()
                 if k.startswith("%d|" % shape) and "signed_area_xz" in v]
        if not areas:
            continue
        pos = sum(1 for a in areas if a > 0); neg = sum(1 for a in areas if a < 0)
        zero = sum(1 for a in areas if a == 0)
        flag = "" if (pos == 0 or neg == 0) else "   <-- INCONSISTENT WINDING"
        print("   shape %d: %d CCW, %d CW, %d degenerate%s" % (shape, pos, neg, zero, flag))
    return 0


if __name__ == "__main__":
    sys.exit(main())
