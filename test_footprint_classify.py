"""PHASE 1 test — hardened after adversarial review. Writes no .hda.

    hython U:/AB_Standardization/test_footprint_classify.py

RUN WITH THE HOUDINI GUI CLOSED.

⚠ WHY THIS FILE WAS REWRITTEN
The first version reported 8/8 passing while nine real defects sat in the VEX.
An adversarial review found every one of them, and the common cause was that the
test asserted on the wrong things:

  * it never read a single GROUP, so the compass-alias code executed on every
    run and was checked on none — `WallFront` was landing on the back wall;
  * it asserted winding by reading `footprint_area`, a value the code had just
    forced positive, so the assertion could not fail for any non-degenerate
    input;
  * it never set RoundCorners=1, so the entire arc branch was unexecuted;
  * every input was a well-formed convex-or-L polygon, so collinear vertices,
    duplicate points, open polylines, bowties, non-planar input and multiple
    input primitives were all untested — and all are silently accepted.

The rule this file now follows: **an assertion must be able to fail.** For every
check below, the defect that would trip it is named in a comment. A check whose
defect cannot be named is decoration and does not belong here.
"""
import math
import os
import sys

import hou

VEX = "U:/AB_Standardization/vex/footprint_classify.vex"

# (points, expected reflex count) — well-formed shapes
SHAPES = {
    "Rectangle": ([(0,0),(100,0),(100,60),(0,60)], 0),
    "Rect CW":   ([(0,0),(0,60),(100,60),(100,0)], 0),
    "L":         ([(0,0),(100,0),(100,40),(40,40),(40,100),(0,100)], 1),
    "U":         ([(0,0),(100,0),(100,100),(70,100),(70,40),(30,40),(30,100),(0,100)], 2),
    "T":         ([(0,0),(100,0),(100,30),(65,30),(65,100),(35,100),(35,30),(0,30)], 2),
    "Cross":     ([(30,0),(70,0),(70,30),(100,30),(100,70),(70,70),(70,100),(30,100),
                   (30,70),(0,70),(0,30),(30,30)], 4),
    "Triangle":  ([(0,0),(100,0),(50,80)], 0),
    "Octagon":   ([(30,0),(70,0),(100,30),(100,70),(70,100),(30,100),(0,70),(0,30)], 0),
}

# malformed inputs that must be REJECTED or handled, never silently accepted
DEGENERATE = {
    "collinear":    [(0,0),(50,0),(100,0),(100,60),(0,60)],
    "duplicate pt": [(0,0),(100,0),(100,0),(100,60),(0,60)],
    "bowtie":       [(0,0),(100,0),(0,60),(100,60)],
    "non-planar":   None,                       # built specially, one vertex at Y=40
    "two prims":    None,                       # built specially, two closed polygons
    "open":         None,                       # built specially, not closed
}


def build_rig(parent):
    sub = parent.createNode("subnet", "Rig")
    ptg = sub.parmTemplateGroup()
    for n, d in (("LegacyNames", 1), ("CornerStyle", 0), ("CornerDivs", 8)):
        ptg.append(hou.IntParmTemplate(n, n, 1, default_value=(d,)))
    ptg.append(hou.FloatParmTemplate("BldCornerSize", "BldCornerSize", 1,
                                     default_value=(4.0,)))
    sub.setParmTemplateGroup(ptg)
    w = sub.createNode("attribwrangle", "classify")
    w.parm("class").set(0)
    with open(VEX, encoding="utf-8") as f:
        w.parm("snippet").set(f.read())
    w.setDisplayFlag(True); w.setRenderFlag(True)
    return sub, w


def feed(sub, pts, closed=True, y_of=None, twice=False):
    old = sub.node("outline")
    if old:
        old.destroy()
    py = sub.createNode("python", "outline")
    py.parm("python").set(
        "import hou\n"
        "geo = hou.pwd().geometry()\n"
        "pts = %r\n"
        "yof = %r\n"
        "def mk(off):\n"
        "    ps = []\n"
        "    for i, (x, z) in enumerate(pts):\n"
        "        p = geo.createPoint()\n"
        "        y = yof.get(i, 0.0) if yof else 0.0\n"
        "        p.setPosition((x + off, y, z))\n"
        "        ps.append(p)\n"
        "    poly = geo.createPolygon()\n"
        "    for p in ps: poly.addVertex(p)\n"
        "    poly.setIsClosed(%r)\n"
        "mk(0.0)\n"
        "%s\n" % (pts, y_of, closed, "mk(500.0)" if twice else "pass"))
    sub.node("classify").setInput(0, py)
    return py


# ── helpers that recompute from the EMITTED geometry ─────────────────────────

def emitted_loop(geo):
    """Concatenate the emitted prims in order into one point sequence.

    ⚠ The closing point must be dropped too. Consecutive prims share endpoints,
    which the running dedupe handles, but the LAST point also coincides with the
    first - leaving it in creates a zero-length closing edge that the
    self-intersection test reports as a crossing on every shape, including a
    clean rectangle. That false positive masked every other check.
    """
    seq = []
    for pr in geo.prims():
        for v in pr.vertices():
            p = (v.point().position()[0], v.point().position()[2])
            if not seq or math.dist(p, seq[-1]) > 1e-6:
                seq.append(p)
    while len(seq) > 1 and math.dist(seq[0], seq[-1]) <= 1e-6:
        seq.pop()
    return seq


def shoelace(seq):
    return sum(seq[i][0] * seq[(i+1) % len(seq)][1]
               - seq[(i+1) % len(seq)][0] * seq[i][1]
               for i in range(len(seq))) * 0.5


def simple(seq):
    """Does the loop self-intersect? Signed area only means anything if not."""
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


def groups_of(geo, prim):
    return sorted(g.name() for g in geo.primGroups() if prim in g.prims())


def check(geo, npts, want_reflex, legacy):
    issues = []
    prims = list(geo.prims())

    # --- structure -----------------------------------------------------------
    # trips if: the source outline survives, or a second input prim shifts
    # indices, or a corner/wall fails to emit
    if len(prims) != npts * 2:
        return ["prims %d, expected %d" % (len(prims), npts * 2)]

    corners = walls = reflex = 0
    total_angle = 0.0
    for i, p in enumerate(prims):
        kind = p.attribValue("element")
        want = "corner" if i % 2 == 0 else "wall"
        if kind != want:
            issues.append("prim %d is %r, expected %s" % (i, kind, want))
        idx = i // 2 + 1
        expect = ("Corner_%02d" if i % 2 == 0 else "Wall_%02d") % idx
        if p.attribValue("name") != expect:
            issues.append("prim %d named %s, expected %s" % (i, p.attribValue("name"), expect))

        # trips if: a group is named differently from the prim it is on
        if expect not in groups_of(geo, p):
            issues.append("prim %d not in group %s (groups: %s)"
                          % (i, expect, groups_of(geo, p)))

        if kind == "corner":
            corners += 1
            total_angle += p.attribValue("corner_angle")
            if p.attribValue("corner_convex") < 0:
                reflex += 1
        else:
            walls += 1
            # trips if: BldCornerSize eats the whole wall and a zero-length
            # degenerate prim is emitted silently
            if p.attribValue("wall_length") <= 1e-6:
                issues.append("prim %d is a ZERO-LENGTH wall" % i)

    if corners != walls:
        issues.append("corners %d != walls %d" % (corners, walls))
    if corners != npts:
        issues.append("corners %d != input vertices %d" % (corners, npts))

    # trips if: the convex/reflex sign convention flips, or a collinear vertex
    # is misclassified
    if reflex != want_reflex:
        issues.append("reflex %d, expected %d" % (reflex, want_reflex))
    if abs(total_angle - (npts - 2) * 180.0) > 0.5:
        issues.append("interior angles %.2f, expected %.2f"
                      % (total_angle, (npts - 2) * 180.0))

    # --- winding, recomputed from what was EMITTED ---------------------------
    # The old test read footprint_area, which the code forces positive - so it
    # could not fail. This walks the emitted prims instead.
    seq = emitted_loop(geo)
    if not simple(seq):
        issues.append("emitted outline SELF-INTERSECTS — winding undefined")
    else:
        a = shoelace(seq)
        if a <= 0:
            issues.append("emitted winding is %.1f, expected CCW (positive)" % a)
        # trips if: footprint_area reports the INPUT outline rather than the
        # geometry actually produced
        fa = geo.attribValue("footprint_area") if geo.findGlobalAttrib("footprint_area") else None
        if fa is not None and abs(fa - a) > max(1.0, abs(a) * 0.02):
            issues.append("footprint_area %.1f but emitted area %.1f" % (fa, a))

    # --- compass aliases, if enabled ----------------------------------------
    # trips if: compass names are assigned by loop index rather than by
    # direction. WallFront must be the +Z wall, WallRight the +X wall.
    if legacy and npts == 4:
        want_dir = {"WallFront": (0, 1), "WallBack": (0, -1),
                    "WallRight": (1, 0), "WallLeft": (-1, 0)}
        cx = sum(p[0] for p in seq) / len(seq)
        cz = sum(p[1] for p in seq) / len(seq)
        for gname, (wx, wz) in want_dir.items():
            grp = [p for p in prims if gname in groups_of(geo, p)]
            if not grp:
                issues.append("compass group %s missing" % gname)
                continue
            vs = [v.point().position() for v in grp[0].vertices()]
            mx = sum(v[0] for v in vs) / len(vs) - cx
            mz = sum(v[2] for v in vs) / len(vs) - cz
            if (mx * wx + mz * wz) <= 0:
                issues.append("%s is on the wrong side (offset %.1f,%.1f)"
                              % (gname, mx, mz))
    return issues


def main():
    if not os.path.isfile(VEX):
        print("!! no VEX at %s" % VEX); return 1
    holder = hou.node("/obj").createNode("geo", "ClassifyTest")
    sub, w = build_rig(holder)
    fails = 0

    def run(label, expect_ok=True):
        try:
            w.cook(force=True)
        except hou.Error as e:
            return None, str(e).split("\n")[0][:70]
        if w.errors():
            return None, w.errors()[0].split("\n")[-1][:70]
        return w.geometry(), None

    print("── well-formed shapes " + "─" * 44)
    print("%-12s %6s %6s %7s  %s" % ("shape", "verts", "prims", "reflex", "result"))
    for name, (pts, want_reflex) in SHAPES.items():
        feed(sub, pts)
        geo, err = run(name)
        if err:
            print("%-12s ERROR %s" % (name, err)); fails += 1; continue
        issues = check(geo, len(pts), want_reflex, legacy=True)
        reflex = sum(1 for p in geo.prims()
                     if p.attribValue("element") == "corner"
                     and p.attribValue("corner_convex") < 0)
        print("%-12s %6d %6d %7d  %s"
              % (name, len(pts), len(geo.prims()), reflex, "ok" if not issues else "FAIL"))
        for i in issues[:6]:
            print("               - %s" % i)
        fails += 1 if issues else 0

    print("")
    print("── rounded corners (the arc branch, previously never executed) " + "─" * 3)
    sub.parm("CornerStyle").set(2)
    for name in ("Rectangle", "L"):
        pts, want_reflex = SHAPES[name]
        feed(sub, pts)
        geo, err = run(name)
        if err:
            print("%-12s ERROR %s" % (name, err)); fails += 1; continue
        issues = check(geo, len(pts), want_reflex, legacy=True)
        # trips if: the "arc" is not actually circular. Measured against the
        # shipping tool, whose arc holds radius to within 0.002.
        arc = geo.prims()[0]
        vs = [v.point().position() for v in arc.vertices()]
        if len(vs) < 3:
            issues.append("rounded corner has only %d points" % len(vs))
        else:
            # circumcentre of first / middle / last — NOT the centroid, which
            # for a 90-degree arc sits well inside the circle and makes even a
            # perfect arc look 83% out. Measuring the wrong thing is the exact
            # failure the review caught elsewhere; do not repeat it here.
            a, b, c = vs[0], vs[len(vs)//2], vs[-1]
            ax, az, bx, bz, cx0, cz0 = a[0], a[2], b[0], b[2], c[0], c[2]
            dd = 2*(ax*(bz-cz0) + bx*(cz0-az) + cx0*(az-bz))
            if abs(dd) < 1e-9:
                issues.append("rounded corner points are collinear — not an arc")
            else:
                ux = ((ax*ax+az*az)*(bz-cz0) + (bx*bx+bz*bz)*(cz0-az)
                      + (cx0*cx0+cz0*cz0)*(az-bz)) / dd
                uz = ((ax*ax+az*az)*(cx0-bx) + (bx*bx+bz*bz)*(ax-cx0)
                      + (cx0*cx0+cz0*cz0)*(bx-ax)) / dd
                rr = [math.dist((v[0], v[2]), (ux, uz)) for v in vs]
                if max(rr) - min(rr) > 0.005 * max(rr):
                    issues.append("corner is not circular: radius varies %.2f%%"
                                  % (100*(max(rr)-min(rr))/max(rr)))
        print("%-12s %6d %6d %7s  %s"
              % (name+" rnd", len(pts), len(geo.prims()), "-",
                 "ok" if not issues else "FAIL"))
        for i in issues[:4]:
            print("               - %s" % i)
        fails += 1 if issues else 0
    sub.parm("CornerStyle").set(0)

    print("")
    print("── degenerate input: must error, never silently accept " + "─" * 10)
    cases = [
        ("duplicate pt", dict(pts=DEGENERATE["duplicate pt"])),
        ("bowtie",       dict(pts=DEGENERATE["bowtie"])),
        ("non-planar",   dict(pts=SHAPES["Rectangle"][0], y_of={2: 40.0})),
        ("two prims",    dict(pts=SHAPES["Rectangle"][0], twice=True)),
        ("open polyline",dict(pts=SHAPES["Rectangle"][0], closed=False)),
        ("corner>wall",  dict(pts=SHAPES["Rectangle"][0])),
    ]
    for label, kw in cases:
        if label == "corner>wall":
            sub.parm("BldCornerSize").set(1000.0)
        feed(sub, kw.pop("pts"), **kw)
        geo, err = run(label)
        if err:
            print("%-14s rejected: %s" % (label, err[:52]))
        else:
            n = len(geo.prims())
            print("%-14s ACCEPTED SILENTLY — %d prims emitted   <-- defect" % (label, n))
            fails += 1
        sub.parm("BldCornerSize").set(4.0)

    # collinear is ACCEPTED and must be classified as collinear — a straight
    # vertex is legal input from any resampled curve, so erroring would be
    # wrong. What must not happen is it being called reflex and getting an
    # inner fillet cut into a flat wall, which is what it used to do.
    print("")
    print("── collinear vertex: accepted, but must classify as collinear " + "─" * 4)
    feed(sub, DEGENERATE["collinear"])
    geo, err = run("collinear")
    if err:
        print("collinear     unexpectedly REJECTED: %s" % err[:50]); fails += 1
    else:
        flat = [p for p in geo.prims()
                if p.attribValue("element") == "corner"
                and p.attribValue("corner_convex") == 0]
        reflex = [p for p in geo.prims()
                  if p.attribValue("element") == "corner"
                  and p.attribValue("corner_convex") < 0]
        ok = len(flat) == 1 and len(reflex) == 0
        print("collinear     %d collinear, %d reflex  %s"
              % (len(flat), len(reflex),
                 "ok" if ok else "FAIL — expected 1 collinear, 0 reflex"))
        fails += 0 if ok else 1

    print("")
    print("=" * 66)
    print("failures: %d" % fails)
    print("A green run here means every named defect is closed. Red is the")
    print("expected state until the VEX is fixed.")
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main())
