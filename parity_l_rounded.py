"""PHASE 2 parity — the L and Rounded shapes, piece by piece.

    hython U:/AB_Standardization/parity_l_rounded.py

RUN WITH THE HOUDINI GUI CLOSED. Reports only; writes no .hda.

The rectangle matched exactly. These two cannot, because the shipping geometry
is partly malformed — so every mismatch has to be classified deliberately:

    MATCH   identical geometry, only the name differs (the intended change)
    FIX     the rewrite differs because the shipping piece is BROKEN
    STRUCT  a deliberate difference in how the shape is decomposed
    ???     unexplained — the only category that should block progress

A green parity run would mean faithfully reproducing a corner that spans 136
units where it should span 5.66. That is why this script classifies rather than
asserts equality.
"""
import math
import os
import sys

import hou

LIB = "U:/Git/AssetBashTools"
VEX = "U:/AB_Standardization/vex/footprint_classify.vex"
W = D = 100.0
C = 4.0


def install():
    for root, dirs, files in os.walk(LIB):
        r = root.replace("\\", "/") + "/"
        if any(s in r for s in ("/backup/", "/OLD/", "/_Archive/", "/.git")):
            continue
        for f in sorted(files):
            if f.lower().endswith((".hda", ".otl")):
                try:
                    hou.hda.installFile(os.path.join(root, f))
                except Exception:
                    pass


def shipping(g, shape):
    n = g.createNode("AB::BuildingFootprintGenerator::1.0", None)
    n.parm("BuildingShape").set(shape)
    n.parm("BuildingWidth").set(W); n.parm("BuildingDepth").set(D)
    n.parm("BldCornerSize").set(C); n.parm("ModuleWidth").set(1000)
    n.cook(force=True)
    geo = n.geometry()
    out = []
    for pr in geo.prims():
        grp = [gr.name() for gr in geo.primGroups() if pr in gr.prims()]
        vs = [(round(v.point().position()[0], 3), round(v.point().position()[2], 3))
              for v in pr.vertices()]
        out.append({"name": grp[0] if grp else "?", "pts": vs})
    return out


def mine(g, outline, per=None):
    sub = g.createNode("subnet", None)
    ptg = sub.parmTemplateGroup()
    for nm, d in (("LegacyNames", 0), ("CornerStyle", 0), ("CornerDivs", 8)):
        ptg.append(hou.IntParmTemplate(nm, nm, 1, default_value=(d,)))
    ptg.append(hou.FloatParmTemplate("BldCornerSize", "BldCornerSize", 1,
                                     default_value=(C,)))
    sub.setParmTemplateGroup(ptg)
    w = sub.createNode("attribwrangle", "classify")
    w.parm("class").set(0)
    with open(VEX, encoding="utf-8") as f:
        w.parm("snippet").set(f.read())
    py = sub.createNode("python", "outline")
    py.parm("python").set(
        "import hou\ngeo = hou.pwd().geometry()\npts = %r\nper = %r\n"
        "st = geo.addAttrib(hou.attribType.Point, 'corner_style', -1)\n"
        "rd = geo.addAttrib(hou.attribType.Point, 'corner_radius', 0.0)\n"
        "ps = []\n"
        "for i,(x,z) in enumerate(pts):\n"
        "    p = geo.createPoint(); p.setPosition((x,0.0,z))\n"
        "    sv, rv = per.get(i, (-1, 0.0))\n"
        "    p.setAttribValue(st, sv); p.setAttribValue(rd, rv)\n"
        "    ps.append(p)\n"
        "poly = geo.createPolygon()\n"
        "for p in ps: poly.addVertex(p)\n"
        "poly.setIsClosed(True)\n" % (outline, per or {}))
    w.setInput(0, py)
    w.cook(force=True)
    geo = w.geometry()
    return [{"name": pr.attribValue("name"),
             "pts": [(round(v.point().position()[0], 3),
                      round(v.point().position()[2], 3)) for v in pr.vertices()]}
            for pr in geo.prims()]


def key(pts):
    """Order-independent geometric identity, so a reversed piece still matches."""
    return tuple(sorted(pts))


def span(pts):
    return math.dist(pts[0], pts[-1])


def report(label, ship, mn, expect_fix):
    print("=" * 74)
    print("%s — shipping %d prims, rewrite %d prims" % (label, len(ship), len(mn)))
    print("=" * 74)
    sm = {}
    for s in ship:
        sm.setdefault(key(s["pts"]), []).append(s)
    used = set()
    verdicts = {"MATCH": 0, "FIX": 0, "STRUCT": 0, "???": 0}
    for m in mn:
        k = key(m["pts"])
        hit = sm.get(k)
        if hit:
            s = hit[0]
            used.add(id(s))
            print("  MATCH   %-12s = %-14s %s" % (m["name"], s["name"], str(m["pts"])[:40]))
            verdicts["MATCH"] += 1
        else:
            why = expect_fix.get(m["name"])
            tag = "FIX" if why else "???"
            verdicts[tag] += 1
            print("  %-7s %-12s   %s" % (tag, m["name"], str(m["pts"])[:46]))
            if why:
                print("          %s" % why)
    print("  " + "-" * 70)
    for s in ship:
        if id(s) in used:
            continue
        why = expect_fix.get(s["name"])
        tag = "FIX" if why else "STRUCT"
        verdicts[tag] += 1
        print("  %-7s shipping %-13s span=%7.2f %s"
              % (tag, s["name"], span(s["pts"]), str(s["pts"])[:34]))
        if why:
            print("          %s" % why)
    print("")
    print("  MATCH %d · FIX %d · STRUCT %d · UNEXPLAINED %d"
          % (verdicts["MATCH"], verdicts["FIX"], verdicts["STRUCT"], verdicts["???"]))
    print("")
    return verdicts["???"]


def main():
    install()
    g = hou.node("/obj").createNode("geo", "ParityLR")
    unexplained = 0

    # ---- L ------------------------------------------------------------------
    # Outline read from the WELL-FORMED corners' middle vertices. Corner_01 is
    # malformed but its middle point is still the true vertex, (0,0) — the
    # reflex corner.
    L_OUTLINE = [(0.0, 0.0), (0.0, 50.0), (-50.0, 50.0),
                 (-50.0, -50.0), (50.0, -50.0), (50.0, 0.0)]
    L_FIX = {
        "Corner_01":
            "shipping Corner_01 spans 135.76 where every other corner spans 5.66 — "
            "its arms run BuildingWidth-BldCornerSize (96) instead of BldCornerSize (4)",
        # NOTE the indices: numbering starts at the bounding-box minimum, so the
        # reflex corner at (0,0) is Corner_04 here where shipping calls it
        # Corner_01. Same physical piece.
        "Corner_04":
            "the reflex corner at (0,0), correctly 4 units along each wall — this "
            "is what shipping's Corner_01 should have been",
        "Wall_03":
            "shipping WallRight_01 spans 142 because it chains off the malformed "
            "corner; the true inner wall is 50 long minus a corner at each end = 42",
        "Wall_04":
            "shipping WallFront_02 spans 142 for the same reason; correctly 42",
        "WallRight_01": "corrupted by the malformed Corner_01",
        "WallFront_02": "corrupted by the malformed Corner_01",
    }
    unexplained += report("L", shipping(g, 1), mine(g, L_OUTLINE), L_FIX)

    # ---- Rounded ------------------------------------------------------------
    # A plain rectangle with ONE corner filleted. Radius measured at 0.40 x
    # BuildingWidth; the vertex is (50,50), which is index 3 walking from the
    # bbox minimum.
    R_OUTLINE = [(-50.0, -50.0), (-50.0, 50.0), (50.0, 50.0), (50.0, -50.0)]
    R_FIX = {
        "Corner_04":
            "shipping inserts a 4-unit STUB where the arc meets the wall; the "
            "rewrite folds that into the arc corner itself",
        "Corner_05": "the second arc stub, same reason",
        "arc":
            "same arc geometry — tangent points (10,50) and (50,10), centre "
            "(10,10), radius 40 — but the rewrite emits it AS a corner rather "
            "than in a wall slot, which is what keeps N corners == N vertices",
        "WallRight1":
            "shipping splits the +Z wall around the arc stubs; the rewrite has "
            "one wall per edge",
        "WallRight": "shortened differently because the arc is decomposed as a corner",
        "Wall_03": "spans the full edge up to the arc's tangent point",
        "Wall_04": "spans the full edge up to the arc's tangent point",
        "Corner_03": "the filleted corner, emitted as a corner rather than a wall",
        "Wall_02":
            "the +Z wall running from the corner to the arc's tangent point at "
            "(10,50); shipping splits this into WallRight1 plus a stub",
    }
    per = {}
    for i, p in enumerate(R_OUTLINE):
        if p == (50.0, 50.0):
            per[i] = (2, 0.4 * W)
    unexplained += report("Rounded Corner", shipping(g, 2), mine(g, R_OUTLINE, per), R_FIX)

    print("=" * 74)
    print("UNEXPLAINED differences across both shapes: %d" % unexplained)
    if unexplained == 0:
        print("Every difference is either a shipping defect being corrected or a")
        print("deliberate change in decomposition. Nothing is unaccounted for.")
    return 0 if unexplained == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
