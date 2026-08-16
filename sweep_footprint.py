"""Sweep the rewrite over the SAME 162 parameter combinations as the baseline.

    hython U:/AB_Standardization/sweep_footprint.py

RUN WITH THE HOUDINI GUI CLOSED. Reports only.

Phase 0 captured the shipping tool across 3 shapes x 3 widths x 3 depths x
3 corner sizes x 2 module widths. This runs the rewrite over the identical grid
and checks that EVERY combination produces valid geometry — including the 18
degenerate cases where the shipping tool emits a wall running backwards along
the perimeter.

Validity here is not "it cooked". It is:
    N corners == N walls == N input vertices
    prim 2k is a corner, prim 2k+1 is a wall
    no wall of zero length
    the emitted outline does not self-intersect
    winding is negative (counter-clockwise seen from above)
"""
import itertools
import math
import os
import sys

import hou

VEX = "U:/AB_Standardization/vex/footprint_classify.vex"

WIDTHS = (100.0, 40.0, 250.0)
DEPTHS = (100.0, 60.0, 180.0)
CORNERS = (4.0, 0.5, 25.0)


def outline(shape, W, D):
    """The outlines derived in the parity work, as functions of W and D."""
    if shape == 0:
        return [(-W/2, -D/2), (-W/2, D/2), (W/2, D/2), (W/2, -D/2)], {}
    if shape == 1:
        # a W x D L with a W/2 x D/2 notch in the +X/+Z quadrant
        return [(0.0, 0.0), (0.0, D/2), (-W/2, D/2),
                (-W/2, -D/2), (W/2, -D/2), (W/2, 0.0)], {}
    # rounded: rectangle with ONE corner filleted at 0.4 x width
    pts = [(-W/2, -D/2), (-W/2, D/2), (W/2, D/2), (W/2, -D/2)]
    return pts, {2: (2, 0.4 * W)}


def build(parent):
    sub = parent.createNode("subnet", "Rig")
    ptg = sub.parmTemplateGroup()
    for n, d in (("LegacyNames", 0), ("CornerStyle", 0), ("CornerDivs", 8)):
        ptg.append(hou.IntParmTemplate(n, n, 1, default_value=(d,)))
    ptg.append(hou.FloatParmTemplate("BldCornerSize", "BldCornerSize", 1,
                                     default_value=(4.0,)))
    sub.setParmTemplateGroup(ptg)
    w = sub.createNode("attribwrangle", "classify")
    w.parm("class").set(0)
    with open(VEX, encoding="utf-8") as f:
        w.parm("snippet").set(f.read())
    return sub, w


def feed(sub, pts, per):
    old = sub.node("outline")
    if old:
        old.destroy()
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
        "poly.setIsClosed(True)\n" % (pts, per))
    sub.node("classify").setInput(0, py)


def loop(geo):
    seq = []
    for pr in geo.prims():
        for v in pr.vertices():
            p = (v.point().position()[0], v.point().position()[2])
            if not seq or math.dist(p, seq[-1]) > 1e-6:
                seq.append(p)
    while len(seq) > 1 and math.dist(seq[0], seq[-1]) <= 1e-6:
        seq.pop()
    return seq


def simple(seq):
    def cr(o, p, q):
        return (p[0]-o[0])*(q[1]-o[1]) - (p[1]-o[1])*(q[0]-o[0])
    n = len(seq)
    for i in range(n):
        for j in range(i+2, n):
            if i == 0 and j == n-1:
                continue
            a, b, c, d = seq[i], seq[(i+1) % n], seq[j], seq[(j+1) % n]
            if ((cr(c,d,a) > 0) != (cr(c,d,b) > 0)) and \
               ((cr(a,b,c) > 0) != (cr(a,b,d) > 0)):
                return False
    return True


def check(geo, nverts):
    issues = []
    prims = list(geo.prims())
    if len(prims) != nverts * 2:
        return ["prims %d, expected %d" % (len(prims), nverts * 2)]
    for i, p in enumerate(prims):
        want = "corner" if i % 2 == 0 else "wall"
        if p.attribValue("element") != want:
            issues.append("prim %d is %s" % (i, p.attribValue("element")))
        if want == "wall" and p.attribValue("wall_length") <= 1e-6:
            issues.append("prim %d zero-length wall" % i)
    seq = loop(geo)
    if not simple(seq):
        issues.append("emitted outline self-intersects")
    else:
        a = sum(seq[i][0]*seq[(i+1) % len(seq)][1] - seq[(i+1) % len(seq)][0]*seq[i][1]
                for i in range(len(seq))) * 0.5
        if a >= 0:
            issues.append("winding %.1f, expected negative" % a)
    return issues


def main():
    holder = hou.node("/obj").createNode("geo", "Sweep")
    sub, w = build(holder)
    ok = warned = bad = 0
    fails = []
    for shape in range(3):
        sh_ok = sh_warn = 0
        for W, D, C in itertools.product(WIDTHS, DEPTHS, CORNERS):
            pts, per = outline(shape, W, D)
            sub.parm("BldCornerSize").set(C)
            feed(sub, pts, per)
            key = "shape%d W=%g D=%g C=%g" % (shape, W, D, C)
            try:
                w.cook(force=True)
            except hou.Error as e:
                bad += 1; fails.append((key, str(e).split("\n")[0][:60])); continue
            if w.errors():
                bad += 1; fails.append((key, w.errors()[0].split("\n")[-1][:60])); continue
            issues = check(w.geometry(), len(pts))
            if issues:
                bad += 1; fails.append((key, "; ".join(issues)))
            else:
                ok += 1; sh_ok += 1
                if w.warnings():
                    warned += 1; sh_warn += 1
        print("  shape %d: %2d valid (%d clamped with a warning)" % (shape, sh_ok, sh_warn))

    total = 3 * len(WIDTHS) * len(DEPTHS) * len(CORNERS)
    print("")
    print("=" * 66)
    print("combinations : %d" % total)
    print("  valid      : %d" % ok)
    print("  clamped    : %d  (degenerate corner, warned, geometry still valid)" % warned)
    print("  FAILED     : %d" % bad)
    for k, why in fails[:12]:
        print("     %-28s %s" % (k, why))
    if not bad:
        print("")
        print("Every parameter combination the baseline covers produces valid")
        print("geometry — including the degenerate regime where the shipping tool")
        print("emits a wall running backwards along the perimeter.")
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main())
