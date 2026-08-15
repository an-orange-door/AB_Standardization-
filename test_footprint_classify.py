"""PHASE 1 test — the classification wrangle, standalone. Writes no .hda.

    hython U:/AB_Standardization/test_footprint_classify.py

RUN WITH THE HOUDINI GUI CLOSED.

Feeds hand-made outlines straight into the wrangle and checks the invariants the
baseline proved must hold. Nothing here touches the shipping tool — the point is
to get the classification provably right BEFORE it goes near an HDA.

The invariants, all measured from the 162-case baseline:
  * prim 2k is a corner, prim 2k+1 is a wall, covering every prim
  * N corners == N walls == N input vertices
  * interior angles sum to (n-2)*180
  * an L has exactly ONE reflex corner; a convex shape has none
  * winding is CCW for every shape (the shipping tools disagree with each other)
  * Wall_k follows Corner_k, so adjacency is arithmetic
"""
import os
import sys

import hou

VEX = "U:/AB_Standardization/vex/footprint_classify.vex"

# name -> (points on the ground plane, expected reflex count)
SHAPES = {
    "Rectangle":   ([(0,0),(100,0),(100,60),(0,60)], 0),
    "Rect CW":     ([(0,0),(0,60),(100,60),(100,0)], 0),   # wound backwards on purpose
    "L":           ([(0,0),(100,0),(100,40),(40,40),(40,100),(0,100)], 1),
    "U":           ([(0,0),(100,0),(100,100),(70,100),(70,40),(30,40),(30,100),(0,100)], 2),
    "T":           ([(0,0),(100,0),(100,30),(65,30),(65,100),(35,100),(35,30),(0,30)], 2),
    "Cross":       ([(30,0),(70,0),(70,30),(100,30),(100,70),(70,70),(70,100),(30,100),
                     (30,70),(0,70),(0,30),(30,30)], 4),
    "Triangle":    ([(0,0),(100,0),(50,80)], 0),
    "Octagon":     ([(30,0),(70,0),(100,30),(100,70),(70,100),(30,100),(0,70),(0,30)], 0),
}


def build_rig(parent):
    sub = parent.createNode("subnet", "Rig")
    ptg = sub.parmTemplateGroup()
    for n, d in (("LegacyNames", 1), ("RoundCorners", 0), ("CornerDivs", 4)):
        ptg.append(hou.IntParmTemplate(n, n, 1, default_value=(d,)))
    ptg.append(hou.FloatParmTemplate("BldCornerSize", "BldCornerSize", 1,
                                     default_value=(4.0,)))
    sub.setParmTemplateGroup(ptg)
    w = sub.createNode("attribwrangle", "classify")
    w.parm("class").set(0)                       # Detail
    with open(VEX, encoding="utf-8") as f:
        w.parm("snippet").set(f.read())
    w.setDisplayFlag(True); w.setRenderFlag(True)
    return sub, w


def feed(sub, pts):
    """Build the closed input polygon inside the subnet and wire it in."""
    old = sub.node("outline")
    if old:
        old.destroy()
    py = sub.createNode("python", "outline")
    py.parm("python").set(
        "import hou\n"
        "geo = hou.pwd().geometry()\n"
        "pts = %r\n"
        "ps = [geo.createPoint() for _ in pts]\n"
        "for p, (x, z) in zip(ps, pts): p.setPosition((x, 0.0, z))\n"
        "poly = geo.createPolygon()\n"
        "for p in ps: poly.addVertex(p)\n"
        "poly.setIsClosed(True)\n" % (pts,))
    sub.node("classify").setInput(0, py)
    return py


def check(name, geo, npts, want_reflex):
    issues = []
    prims = list(geo.prims())
    n = len(prims)
    if n != npts * 2:
        issues.append("prims %d, expected %d" % (n, npts * 2))
        return issues

    nm = geo.findPrimAttrib("name")
    el = geo.findPrimAttrib("element")
    if nm is None or el is None:
        return ["missing name/element prim attribute"]

    corners = walls = 0
    reflex = 0
    total_angle = 0.0
    for i, p in enumerate(prims):
        kind = p.attribValue("element")
        want = "corner" if i % 2 == 0 else "wall"
        if kind != want:
            issues.append("prim %d is %s, expected %s" % (i, kind, want))
        if kind == "corner":
            corners += 1
            total_angle += p.attribValue("corner_angle")
            if p.attribValue("corner_convex") < 0:
                reflex += 1
            expect = "Corner_%02d" % (i // 2 + 1)
        else:
            walls += 1
            expect = "Wall_%02d" % (i // 2 + 1)
        if p.attribValue("name") != expect:
            issues.append("prim %d named %s, expected %s"
                          % (i, p.attribValue("name"), expect))

    if corners != walls:
        issues.append("corners %d != walls %d" % (corners, walls))
    if corners != npts:
        issues.append("corners %d != input vertices %d" % (corners, npts))
    if reflex != want_reflex:
        issues.append("reflex %d, expected %d" % (reflex, want_reflex))
    expect_sum = (npts - 2) * 180.0
    if abs(total_angle - expect_sum) > 0.5:
        issues.append("interior angles %.2f, expected %.2f" % (total_angle, expect_sum))
    a = geo.attribValue("footprint_area") if geo.findGlobalAttrib("footprint_area") else 0
    if a <= 0:
        issues.append("area %.2f is not positive — winding not enforced" % a)
    return issues


def main():
    if not os.path.isfile(VEX):
        print("!! no VEX at %s" % VEX); return 1
    holder = hou.node("/obj").createNode("geo", "ClassifyTest")
    sub, w = build_rig(holder)

    print("%-12s %6s %6s %7s %8s  %s" % ("shape", "verts", "prims", "reflex", "area", "result"))
    fails = 0
    for name, (pts, want_reflex) in SHAPES.items():
        feed(sub, pts)
        try:
            w.cook(force=True)
        except hou.Error as e:
            print("%-12s COOK ERROR %s" % (name, str(e).split("\n")[0][:70]))
            fails += 1
            continue
        errs = w.errors()
        if errs:
            print("%-12s VEX ERROR %s" % (name, errs[0].split("\n")[-1][:70]))
            fails += 1
            continue
        geo = w.geometry()
        issues = check(name, geo, len(pts), want_reflex)
        reflex = sum(1 for p in geo.prims()
                     if p.attribValue("element") == "corner"
                     and p.attribValue("corner_convex") < 0)
        area = geo.attribValue("footprint_area") if geo.findGlobalAttrib("footprint_area") else 0
        print("%-12s %6d %6d %7d %8.0f  %s"
              % (name, len(pts), len(geo.prims()), reflex, area,
                 "ok" if not issues else "FAIL"))
        for i in issues:
            print("               - %s" % i)
        fails += 1 if issues else 0

    print("")
    print("=" * 64)
    print("shapes: %d   failures: %d" % (len(SHAPES), fails))
    if not fails:
        print("")
        print("Every invariant the baseline proved holds for arbitrary N —")
        print("including U, T, Cross and a triangle, none of which the three")
        print("hand-built subnets can make at all.")
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main())
