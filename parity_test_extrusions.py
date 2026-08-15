"""Prove the VEX profiles reproduce the Add SOPs exactly before replacing them.

    hython U:/AB_Standardization/parity_test_extrusions.py

RUN WITH THE HOUDINI GUI CLOSED — one FX seat.

The rewrite is only safe if the five shipped profiles come out identical with
web_thick = flange_thick = thick. This sweeps a range of width/height/thickness
and compares the VEX output against the live Add SOPs point for point.

Two comparisons, because they fail differently:
  ORDERED  positions in vertex order. Must match for the sweep to behave the
           same - a correct shape with a rotated start point still sweeps
           differently at the seam.
  SORTED   positions ignoring order. If ORDERED fails but SORTED passes, the
           shape is right and only the winding or start vertex moved, which is
           a much smaller fix than bad maths.

Nothing is written. This only reports.
"""
import itertools
import os
import sys

import hou

LIB = "U:/Git/AssetBashTools"
T = "AB::MetalExtrusionMaker::2.0"
VEX = "U:/AB_Standardization/vex/metal_extrusion_profiles.vex"

# menu index -> the null carrying that profile inside the HDA
SHIPPED = {
    0: "I_BEAM_CURVE_OUT",
    1: "C_CHANNEL_CURVE_OUT",
    2: "T_BEAM_CURVE_OUT",
    3: "ANGLE_CURVE_OUT",
    4: "SQUARE_CURVE_OUT",
}

TOL = 1e-5

# MEASURED, not assumed: inside the shipped HDA only add5/pt2y and add5/pt3x are
# hooked to parms. pt1y and pt2x are hardcoded to 1.0, so the Square Tube is a
# correct square ONLY at width == height == 1. At 2.5 x 1 it emits the bent
# quadrilateral (0,0) (0,1) (1,1) (2.5,0). Divergence here is the VEX being
# right and 2.0 being broken, so it is reported separately rather than as a
# parity failure - otherwise a real regression could hide inside the noise.
SHIPPED_BROKEN = {4: "Square Tube: pt1y/pt2x hardcoded to 1.0 in add5"}


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


def build_vex_rig(parent):
    """A subnet carrying the parms the wrangle reads through ../, plus the wrangle."""
    sub = parent.createNode("subnet", "VexRig")
    ptg = sub.parmTemplateGroup()
    for name, default in (("ext_type", 0), ("divisions", 2),
                          ("legacy_ibeam_web", 1)):
        ptg.append(hou.IntParmTemplate(name, name, 1, default_value=(default,)))
    for name, default in (("width", 1.0), ("height", 1.0), ("thick", 0.1),
                          ("web_thick", 0.1), ("flange_thick", 0.1)):
        ptg.append(hou.FloatParmTemplate(name, name, 1, default_value=(default,)))
    sub.setParmTemplateGroup(ptg)

    w = sub.createNode("attribwrangle", "profile")
    w.parm("class").set(0)                       # 0 = Detail (run once)
    with open(VEX, "r", encoding="utf-8") as fh:
        w.parm("snippet").set(fh.read())
    w.setDisplayFlag(True)
    w.setRenderFlag(True)
    return sub, w


def points_of(node):
    node.cook(force=True)
    g = node.geometry()
    return [tuple(round(c, 6) for c in p.position()) for p in g.points()]


def signed_area(pts):
    """Shoelace on XY. >0 counter-clockwise, <0 clockwise.

    Reported for both versions because the VEX now ENFORCES winding, so a
    disagreement here is not a bug - it tells us which convention the shipped
    Add SOPs use, and therefore which way to set `want` in emit().
    """
    a = 0.0
    n = len(pts)
    for i in range(n):
        x1, y1 = pts[i][0], pts[i][1]
        x2, y2 = pts[(i + 1) % n][0], pts[(i + 1) % n][1]
        a += x1 * y2 - x2 * y1
    return a * 0.5


def compare(a, b):
    if len(a) != len(b):
        return "COUNT %d vs %d" % (len(a), len(b)), None
    ordered = max((max(abs(x - y) for x, y in zip(pa, pb)) for pa, pb in zip(a, b)),
                  default=0.0)
    sa, sb = sorted(a), sorted(b)
    unordered = max((max(abs(x - y) for x, y in zip(pa, pb)) for pa, pb in zip(sa, sb)),
                    default=0.0)
    return ordered, unordered


def main():
    print("installed %d" % install())
    if not os.path.isfile(VEX):
        print("!! no VEX file at %s" % VEX); return

    obj = hou.node("/obj")
    holder = obj.createNode("geo", "ParityTest")
    shipped = holder.createNode(T, "shipped")
    shipped.allowEditingOfContents()
    rig, wrangle = build_vex_rig(holder)

    widths = (1.0, 0.35, 2.5)
    heights = (1.0, 0.6, 3.0)
    thicks = (0.1, 0.02, 0.25)

    fails, expected, checks = [], [], 0
    for etype, nullname in sorted(SHIPPED.items()):
        src = shipped.node(nullname)
        if src is None:
            print("  %-20s MISSING inside the HDA" % nullname); continue
        for W, H, t in itertools.product(widths, heights, thicks):
            for n, v in (("width", W), ("height", H), ("thick", t)):
                shipped.parm(n).set(v)
                rig.parm(n).set(v)
            rig.parm("ext_type").set(etype)
            # the whole point of the compatibility default
            rig.parm("web_thick").set(t)
            rig.parm("flange_thick").set(t)

            try:
                a = points_of(src)
                b = points_of(wrangle)
            except hou.Error as e:
                fails.append((etype, W, H, t, "COOK %s" % str(e)[:60])); continue

            ordered, unordered = compare(a, b)
            checks += 1
            if W == 1.0 and H == 1.0 and t == 0.1:
                print("      type=%d winding: shipped=%+.4f  vex=%+.4f  %s"
                      % (etype, signed_area(a), signed_area(b),
                         "same" if (signed_area(a) > 0) == (signed_area(b) > 0)
                         else "OPPOSITE"))
            broken = etype in SHIPPED_BROKEN and not (abs(W - 1.0) < TOL
                                                     and abs(H - 1.0) < TOL)
            bucket = expected if broken else fails
            if isinstance(ordered, str):
                bucket.append((etype, W, H, t, ordered))
            elif ordered > TOL:
                bucket.append((etype, W, H, t,
                              "ordered=%.6f unordered=%.6f%s"
                              % (ordered, unordered,
                                 "  (shape OK, winding/start differs)"
                                 if unordered <= TOL else "  (SHAPE DIFFERS)")))
        print("  checked %-14s (%d combinations)" % (nullname, len(widths) * len(heights) * len(thicks)))
        sys.stdout.flush()

    holder.destroy()
    print("")
    print("=" * 68)
    print("comparisons        : %d" % checks)
    print("parity failures    : %d" % len(fails))
    print("expected divergence: %d  (shipped tool is broken there)" % len(expected))
    for etype, why in sorted(SHIPPED_BROKEN.items()):
        if any(e[0] == etype for e in expected):
            print("     type=%d  %s" % (etype, why))
    for etype, W, H, t, why in fails[:25]:
        print("   type=%d w=%.2f h=%.2f t=%.3f  %s" % (etype, W, H, t, why))
    if not fails:
        print("")
        print("Every shipped profile reproduces exactly wherever 2.0 itself is")
        print("correct. The VEX version is a drop-in, and web_thick/flange_thick")
        print("are purely additive.")


if __name__ == "__main__":
    main()
