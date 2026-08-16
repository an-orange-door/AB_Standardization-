"""Draw the classified footprints to SVG so the geometry can be eyeballed.

    hython U:/AB_Standardization/draw_footprints.py

RUN WITH THE HOUDINI GUI CLOSED. Writes only the SVG.

A green test says the invariants hold. It does not say the shapes LOOK right —
so this renders exactly what the wrangle emits: walls, corners, the reflex
corners, the index origin, and the compass aliases.
"""
import math
import os

import hou

VEX = "U:/AB_Standardization/vex/footprint_classify.vex"
OUT = "U:/AB_Standardization/footprint_sheet.svg"

SHAPES = [
    # (name, points, global style, per-corner overrides)
    ("Rectangle", [(0,0),(100,0),(100,60),(0,60)], 0),
    ("L",         [(0,0),(100,0),(100,40),(40,40),(40,100),(0,100)], 0),
    ("U",         [(0,0),(100,0),(100,100),(70,100),(70,40),(30,40),(30,100),(0,100)], 0),
    ("T",         [(0,0),(100,0),(100,30),(65,30),(65,100),(35,100),(35,30),(0,30)], 0),
    ("Cross",     [(30,0),(70,0),(70,30),(100,30),(100,70),(70,70),(70,100),(30,100),
                   (30,70),(0,70),(0,30),(30,30)], 0),
    ("Octagon",   [(30,0),(70,0),(100,30),(100,70),(70,100),(30,100),(0,70),(0,30)], 0),
    ("Rectangle - chamfered", [(0,0),(100,0),(100,60),(0,60)], 1),
    ("Rectangle - all filleted", [(0,0),(100,0),(100,60),(0,60)], 2),
    # the shipping shape: ONE corner, radius 0.4 x width
    ("Rounded corner (0.4W)", [(0,0),(100,0),(100,60),(0,60)], 0, {2: (2, 40.0)}),
    ("L - one big fillet",    [(0,0),(100,0),(100,40),(40,40),(40,100),(0,100)], 0, {1: (2, 30.0)}),
]


def build(parent):
    sub = parent.createNode("subnet", "Rig")
    ptg = sub.parmTemplateGroup()
    for n, d in (("LegacyNames", 1), ("CornerStyle", 0), ("CornerDivs", 16)):
        ptg.append(hou.IntParmTemplate(n, n, 1, default_value=(d,)))
    ptg.append(hou.FloatParmTemplate("BldCornerSize", "BldCornerSize", 1,
                                     default_value=(8.0,)))
    sub.setParmTemplateGroup(ptg)
    w = sub.createNode("attribwrangle", "classify")
    w.parm("class").set(0)
    with open(VEX, encoding="utf-8") as f:
        w.parm("snippet").set(f.read())
    w.setDisplayFlag(True); w.setRenderFlag(True)
    return sub, w


def feed(sub, pts, per=None):
    """per: {vertex_index: (style, radius)} — per-corner overrides.

    The shipping "Rounded Corner" shape is ONE big arc on ONE corner at radius
    0.4 x BuildingWidth, not every corner filleted at the corner size. That is
    only expressible per corner, which is why style and radius are point
    attributes on the outline rather than a single global toggle.
    """
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
        "    sv, rv = per.get(i, (None, 8.0))\n"
        "    if sv is not None: p.setAttribValue(st, sv)\n"
        "    p.setAttribValue(rd, rv)\n"
        "    ps.append(p)\n"
        "poly = geo.createPolygon()\n"
        "for p in ps: poly.addVertex(p)\n"
        "poly.setIsClosed(True)\n" % (pts, per or {}))
    sub.node("classify").setInput(0, py)


CELL, PAD, SCALE = 268, 30, 1.55


def cell(rec, ox, oy):
    """One footprint. y is negated so +Z points UP, as in a Houdini top view."""
    out = []
    for e in rec["elems"]:
        pts = " ".join("%.2f,%.2f" % (ox + x * SCALE, oy - z * SCALE)
                       for x, z in e["pts"])
        if e["kind"] == "wall":
            out.append('<polyline points="%s" class="wall"/>' % pts)
        else:
            cls = "corner" + (" reflex" if e["convex"] < 0 else "")
            out.append('<polyline points="%s" class="%s"/>' % (pts, cls))
        mx, mz = e["mid"]
        X, Y = ox + mx * SCALE, oy - mz * SCALE
        if e["kind"] == "wall":
            out.append('<text x="%.1f" y="%.1f" class="lbl">%s</text>'
                       % (X, Y - 4, e["name"].replace("Wall_", "W")))
            if e.get("compass"):
                out.append('<text x="%.1f" y="%.1f" class="cmp">%s</text>'
                           % (X, Y + 9, e["compass"].replace("Wall", "")))
        else:
            out.append('<circle cx="%.1f" cy="%.1f" r="%.1f" class="%s"/>'
                       % (X, Y, 3.4 if e["convex"] < 0 else 2.4,
                          "cdot reflexdot" if e["convex"] < 0 else "cdot"))
            if e["name"] == "Corner_01":
                out.append('<text x="%.1f" y="%.1f" class="origin">C01</text>'
                           % (X + 6, Y - 5))
    return out


def main():
    holder = hou.node("/obj").createNode("geo", "Draw")
    sub, w = build(holder)
    recs = []
    for entry in SHAPES:
        name, pts, style = entry[0], entry[1], entry[2]
        per = entry[3] if len(entry) > 3 else None
        sub.parm("CornerStyle").set(style)
        feed(sub, pts, per)
        w.cook(force=True)
        geo = w.geometry()
        elems = []
        for pr in geo.prims():
            vs = [(v.point().position()[0], v.point().position()[2])
                  for v in pr.vertices()]
            mid = vs[len(vs) // 2] if len(vs) > 2 else (
                ((vs[0][0] + vs[-1][0]) / 2, (vs[0][1] + vs[-1][1]) / 2))
            elems.append({
                "kind": pr.attribValue("element"),
                "name": pr.attribValue("name"),
                "convex": pr.attribValue("corner_convex")
                          if pr.attribValue("element") == "corner" else 1,
                "compass": pr.attribValue("compass")
                           if geo.findPrimAttrib("compass") else "",
                "pts": vs, "mid": mid})
        xs = [p[0] for e in elems for p in e["pts"]]
        zs = [p[1] for e in elems for p in e["pts"]]
        recs.append({"name": name, "elems": elems,
                     "w": max(xs) - min(xs), "h": max(zs) - min(zs),
                     "minx": min(xs), "minz": min(zs),
                     "corners": geo.attribValue("footprint_corners"),
                     "area": geo.attribValue("footprint_area")})

    cols = 4
    rows = (len(recs) + cols - 1) // cols
    W = PAD * 2 + cols * CELL
    H = 118 + rows * CELL
    body = []
    for i, r in enumerate(recs):
        cx = PAD + (i % cols) * CELL
        cy = 118 + (i // cols) * CELL
        # centre the shape in its cell
        ox = cx + (CELL - r["w"] * SCALE) / 2 - r["minx"] * SCALE
        oy = cy + (CELL - 60) / 2 + r["h"] * SCALE - 12 + r["minz"] * SCALE
        body += cell(r, ox, oy)
        body.append('<text x="%d" y="%d" class="title">%s</text>'
                    % (cx + 8, cy + CELL - 26, r["name"]))
        body.append('<text x="%d" y="%d" class="meta">%d corners · %d walls · '
                    'area %.0f</text>'
                    % (cx + 8, cy + CELL - 12, r["corners"], r["corners"], r["area"]))

    svg = HEAD % (W, H, W, H) + "\n".join(body) + "</svg>"
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(svg)
    print("wrote %s (%.0f KB)" % (OUT, os.path.getsize(OUT) / 1024.0))
    for r in recs:
        print("  %-22s %2d corners  area %8.1f" % (r["name"], r["corners"], r["area"]))


HEAD = """<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d"
 viewBox="0 0 %d %d" font-family="ui-sans-serif,system-ui,Segoe UI,sans-serif">
<style>
  .bg{fill:#0B0D0C}
  .wall{fill:none;stroke:#7FA6BA;stroke-width:2.6;stroke-linecap:round}
  .corner{fill:none;stroke:#D4A94F;stroke-width:2.6;stroke-linecap:round}
  .corner.reflex{stroke:#D07C68}
  .cdot{fill:#D4A94F}
  .cdot.reflexdot{fill:#D07C68}
  .lbl{font-size:8.5px;fill:#7FA6BA;text-anchor:middle;font-weight:700}
  .cmp{font-size:7.5px;fill:#8A9088;text-anchor:middle}
  .origin{font-size:8.5px;fill:#EDEDE8;font-weight:700}
  .title{font-size:13px;font-weight:700;fill:#EDEDE8}
  .meta{font-size:10.5px;fill:#8A9088;font-family:ui-monospace,Consolas,monospace}
  .h1{font-size:19px;font-weight:700;fill:#EDEDE8}
  .h2{font-size:12px;fill:#8A9088}
  .key{font-size:11px}
</style>
<rect width="100%%" height="100%%" class="bg"/>
<text x="30" y="38" class="h1">Footprint classification</text>
<text x="30" y="58" class="h2">Emitted by footprint_classify.vex. +Z is up, as in a Houdini top view.
Corner size 8. Default corners are true right angles; chamfer and fillet are opt-in.</text>
<text x="30" y="86" class="key" fill="#2F4B7C">&#9644; wall</text>
<text x="95" y="86" class="key" fill="#8A6A16">&#9644; convex corner</text>
<text x="210" y="86" class="key" fill="#9C4A2F">&#9644; reflex corner</text>
<text x="325" y="86" class="key" fill="#1A1D21">C01 = index origin (bbox minimum)</text>
"""


if __name__ == "__main__":
    main()
