"""Inject figures into the AssetBash Handbook.

    python U:/AB_Standardization/build_handbook.py

Pure Python — no Houdini. Reads `assetbash_handbook.html` (the prose), injects
generated figures at named anchors, writes `assetbash_handbook_built.html`.

WHY GENERATED
The handbook should look like the thing it describes. Every figure here is
produced from the same data the claims rest on — the actual icon files, the
measured L-plan skeleton, the profile grammar — so a figure cannot drift from
the text the way a pasted screenshot would.

⚠ Icons are embedded as data URIs, not inlined SVG. All 161 carry internal ids
(`bg`, `oglow`) which would collide the moment two are inlined into one
document, silently cross-wiring gradients and filters between tools.
"""
import base64
import collections
import csv
import math
import os
import re

BASE = "U:/AB_Standardization"
LIB = "U:/Git/AssetBashTools"
ICONS = LIB + "/IconDev/Icons"
SRC = BASE + "/assetbash_handbook.html"
OUT = BASE + "/assetbash_handbook_built.html"

FIGCSS = """
<style>
/* Figures read as plates in a paper: numbered, captioned, on their own ground
   so an embedded SVG with its own light background looks deliberate rather
   than like a hole in the page. */
figure{margin:26px 0;padding:0}
/* Jordan, 2026-08-16: figures on BLACK, objects light. Drawings read better
   inverted and it distinguishes a figure from the page at a glance. */
figure .plate{background:#0B0D0C;border:1px solid #262B28;border-radius:9px;
  padding:16px;overflow-x:auto}
figure .plate img{display:block;width:100%;height:auto}
figcaption{font-family:var(--sans);font-size:12.5px;color:var(--muted);
  margin-top:11px;line-height:1.5}
figcaption b{color:var(--ink);font-weight:700}
.figno{font-family:var(--sans);font-size:10.5px;font-weight:700;
  text-transform:uppercase;letter-spacing:.09em;color:var(--brass);
  display:block;margin-bottom:5px}
.icongrid{display:grid;grid-template-columns:repeat(auto-fill,minmax(34px,1fr));
  gap:7px}
.icongrid img{width:100%;height:auto;border-radius:5px;display:block}
.catrow{margin-bottom:15px}
.catrow .cn{font-family:var(--sans);font-size:10px;text-transform:uppercase;
  letter-spacing:.08em;color:var(--muted);margin-bottom:6px}
.catrow .cn span{color:var(--brass);font-family:var(--mono)}
</style>
"""


def datauri(path):
    with open(path, "rb") as f:
        return "data:image/svg+xml;base64," + base64.b64encode(f.read()).decode()


# ── Figure: the library, by icon ─────────────────────────────────────────────
def fig_icons():
    rows = list(csv.DictReader(open(BASE + "/analysis/tools.csv", encoding="utf-8")))
    bycat = collections.defaultdict(list)
    for r in rows:
        cat = r["file"].replace(LIB + "/", "").rsplit("/", 1)[0]
        p = os.path.join(ICONS, "SOP_AB__%s.svg" % r["name"])
        if os.path.isfile(p):
            bycat[cat].append((r["name"], p))
    order = sorted(bycat, key=lambda c: (-len(bycat[c]), c))
    n = sum(len(v) for v in bycat.values())
    body = []
    for cat in order:
        items = sorted(bycat[cat])
        body.append('<div class="catrow"><div class="cn">%s <span>%d</span></div>'
                    '<div class="icongrid">' % (cat.replace("Sops/", ""), len(items)))
        for name, p in items:
            body.append('<img src="%s" alt="%s" title="%s">'
                        % (datauri(p), name, name))
        body.append("</div></div>")
    return ("""<figure>
<span class="figno">Figure 1</span>
<div class="plate">%s</div>
<figcaption><b>The library, by icon — %d tools across %d categories.</b>
Every tool now carries an authored icon embedded inside its own <code>.hda</code>,
so a customer needs no install step. Until recently 153 of these showed Houdini's
stock subnet icon while 150 finished icons sat unused in the repo. Hover for the
tool name.</figcaption>
</figure>""" % ("\n".join(body), n, len(order)))


# ── Figure: the straight skeleton ────────────────────────────────────────────
def fig_skeleton():
    # the measured L-plan from the roof research: 32x20 block, 16x24 wing
    return """<figure>
<span class="figno">Figure 2</span>
<div class="plate">
<svg viewBox="0 0 500 330" style="max-width:500px;margin:0 auto"
     font-family="ui-sans-serif,system-ui,sans-serif">
  <defs><pattern id="hb" width="6" height="6" patternTransform="rotate(45)"
    patternUnits="userSpaceOnUse">
    <line x1="0" y1="0" x2="0" y2="6" stroke="#2E3431" stroke-width="1.4"/>
  </pattern></defs>
  <g transform="translate(46,292) scale(7.6,-7.6)">
    <polygon points="0,0 32,0 32,20 16,20 16,44 0,44" fill="url(#hb)"
             stroke="#EDEDE8" stroke-width="0.3"/>
    <g stroke="#7FA6BA" stroke-width="0.22" stroke-dasharray="1.2 0.8">
      <line x1="0" y1="0" x2="10" y2="10"/><line x1="32" y1="0" x2="22" y2="10"/>
      <line x1="32" y1="20" x2="22" y2="10"/><line x1="16" y1="44" x2="8" y2="36"/>
      <line x1="0" y1="44" x2="8" y2="36"/><line x1="8" y1="12" x2="10" y2="10"/>
    </g>
    <line x1="16" y1="20" x2="8" y2="12" stroke="#D07C68" stroke-width="0.46"/>
    <g stroke="#D4A94F" stroke-width="0.54">
      <line x1="8" y1="12" x2="8" y2="36"/><line x1="10" y1="10" x2="22" y2="10"/>
    </g>
    <g fill="#D4A94F">
      <circle cx="10" cy="10" r="0.45"/><circle cx="22" cy="10" r="0.45"/>
      <circle cx="8" cy="12" r="0.45"/><circle cx="8" cy="36" r="0.45"/>
    </g>
    <circle cx="16" cy="20" r="0.7" fill="#D07C68"/>
  </g>
  <g font-family="ui-monospace,Consolas,monospace" font-size="10.5" fill="#9AA09B">
    <text x="150" y="228">ridge 5.0 ft</text>
    <text x="24" y="112">ridge</text><text x="24" y="125">4.0 ft</text>
    <text x="122" y="200" fill="#D07C68">valley</text>
    <text x="150" y="150" fill="#D07C68">reflex</text>
  </g>
  <g font-size="11">
    <text x="360" y="232" fill="#D4A94F">&#9644; ridge</text>
    <text x="360" y="250" fill="#D07C68">&#9644; valley</text>
    <text x="360" y="268" fill="#7FA6BA">&#9644; hip</text>
  </g>
</svg>
</div>
<figcaption><b>Figure 2 — The straight skeleton: one construction, an arbitrary
polygon.</b> Shrink the footprint inward with every edge staying parallel to
itself; the paths the vertices trace <em>are</em> the ridges, hips and valleys.
The reflex vertex marked in red is the one that generates the valley. Six input
edges give exactly six roof faces — two of them pentagons, so an implementation
assuming quads breaks on precisely the footprints that matter. Plan areas sum to
1024.00&nbsp;ft&sup2; with residual exactly zero. The two ridges sit at
different heights, and that is correct: at one pitch the deeper mass rides
higher.</figcaption>
</figure>"""


# ── Figure: metal extrusion profiles, computed ───────────────────────────────
def fig_extrusions():
    # ⚠ A SINGLE W:H FOR EVERY PROFILE IS WRONG. Jordan, 2026-08-16: "the
    # I-Beams look weird, the horizontal parts are too long, most I beams don't
    # look like this. Same thing as the Angle - both sides should be equal."
    # Real sections have characteristic proportions: a W-section is DEEPER than
    # it is wide (W12x26 is 12.2 x 6.5), an angle is usually EQUAL-LEG (L4x4),
    # a flat bar is wide and thin. Drawing them all at 2:1 made the I-beam look
    # like a girder nobody rolls and the angle unequal for no reason.
    tw, tf, wall, segs = 0.15, 0.15, 0.12, 28
    PROP = {                      # width, height — representative, not arbitrary
        "I Beam":      (1.15, 1.9),   # deeper than wide, like a W-section
        "C Channel":   (0.9,  1.9),   # tall and narrow
        "T Bar":       (1.5,  1.4),
        "Angle":       (1.5,  1.5),   # EQUAL LEG
        "Square Tube": (1.5,  1.5),
        "Round Tube":  (1.5,  1.5),
        "Round Bar":   (1.5,  1.5),
        "Flat Bar":    (2.0,  0.5),   # wide and thin
        "Hat Channel": (2.0,  1.0),
        "Z Purlin":    (1.2,  1.9),
    }

    def ring(cx, cz, rx, rz, n, rev=False):
        return [(cx + math.cos(2*math.pi*(n-i if rev else i)/n) * rx,
                 cz + math.sin(2*math.pi*(n-i if rev else i)/n) * rz)
                for i in range(n)]

    def geom(name):
        W, H = PROP[name]
        xc, hw = W / 2, tw / 2
        if name == "I Beam":
            return [[(0,0),(0,tf),(xc-hw,tf),(xc-hw,H-tf),(0,H-tf),(0,H),
                     (W,H),(W,H-tf),(xc+hw,H-tf),(xc+hw,tf),(W,tf),(W,0)]]
        if name == "C Channel":
            return [[(0,0),(0,H),(W,H),(W,H-tf),(tw,H-tf),(tw,tf),(W,tf),(W,0)]]
        if name == "T Bar":
            return [[(0,0),(0,tf),(xc-hw,tf),(xc-hw,H),(xc+hw,H),(xc+hw,tf),(W,tf),(W,0)]]
        if name == "Angle":
            return [[(0,0),(0,H),(tw,H),(tw,tf),(W,tf),(W,0)]]
        if name in ("Square Tube", "Flat Bar"):
            return [[(0,0),(0,H),(W,H),(W,0)]]
        if name == "Round Tube":
            return [ring(xc,H/2,H/2,H/2,segs), ring(xc,H/2,H/2-wall,H/2-wall,segs,True)]
        if name == "Round Bar":
            return [ring(xc,H/2,H/2,H/2,segs)]
        if name == "Hat Channel":
            return [[(0,0),(0,H),(W,H),(W,0),(W-tf,0),(W-tf,H-tw),(tf,H-tw),(tf,0)]]
        return [[(0,0),(0,tf),(xc-hw,tf),(xc-hw,H),(W,H),(W,H-tf),(xc+hw,H-tf),(xc+hw,0)]]

    P = {n: geom(n) for n in PROP}
    _unused = {
        # ⚠ drawn CIRCULAR here (radius = H/2) rather than at the figure's
        # W:H of 2:1. The VEX maps width and height to the two radii
        # independently, so a Round Tube at W != H is an ELLIPSE — faithful to
        # the tool, but it raises a real question: should a round section take
        # width as a diameter and ignore height? Flagged, not silently changed.
    }
    cell, cols, S = 140, 5, 46
    rows = (len(P) + cols - 1) // cols
    out = []
    for i, (name, loops) in enumerate(P.items()):
        pw, ph = PROP[name]
        ox = 14 + (i % cols) * cell + (cell - pw * S) / 2
        oy = 24 + (i // cols) * cell + ph * S + 14
        for j, loop in enumerate(loops):
            pts = " ".join("%.2f,%.2f" % (ox + x*S, oy - y*S) for x, y in loop)
            # BLUEPRINT CONVENTION (Jordan, 2026-08-16): white outlines on
            # black, never filled. A filled silhouette hides the interior — on
            # a hollow section you cannot see the wall at all — and reads as a
            # logo rather than a drawing.
            out.append('<polygon points="%s" fill="none" stroke="%s" '
                       'stroke-width="1.4" stroke-linejoin="round"/>'
                       % (pts, "#EDEDE8"))
        out.append('<text x="%.1f" y="%.1f" font-size="10.5" fill="#EDEDE8" '
                   'text-anchor="middle" font-weight="700">%s</text>'
                   % (14 + (i % cols) * cell + cell/2, oy + 20, name))
        out.append('<text x="%.1f" y="%.1f" font-size="9" fill="#9AA09B" '
                   'text-anchor="middle" font-family="ui-monospace,Consolas,monospace">'
                   '%d</text>' % (14 + (i % cols) * cell + cell/2, oy + 33, i))
    h = 24 + rows * cell + 20
    return """<figure>
<span class="figno">Figure 3</span>
<div class="plate">
<svg viewBox="0 0 %d %d" style="max-width:720px;margin:0 auto"
     font-family="ui-sans-serif,system-ui,sans-serif">%s</svg>
</div>
<figcaption><b>Figure 3 — Ten structural profiles from one Detail wrangle.</b>
Menu indices 0–4 are the shipped set, reproduced point-for-point across 135
comparisons; 5–9 are new. Menus are append-only because the ordinal is stored in
every saved scene. <b>Round Tube is the profile the tool could not previously
make</b> — and the one every sign post, gantry, handrail and utility pole
actually is. Square Tube had been broken for years: correct only at exactly
1&nbsp;&times;&nbsp;1.</figcaption>
</figure>""" % (14 + cols * cell, h, "\n".join(out))


def fig_embed(path, num, caption, maxw=980):
    if not os.path.isfile(path):
        return ""
    return """<figure>
<span class="figno">Figure %d</span>
<div class="plate"><img src="%s" style="max-width:%dpx;margin:0 auto" alt=""></div>
<figcaption>%s</figcaption>
</figure>""" % (num, datauri(path), maxw, caption)


def main():
    s = open(SRC, encoding="utf-8").read()
    s = s.replace("</style>\n\n<div class=\"hero\">", "</style>\n" + FIGCSS + "\n<div class=\"hero\">", 1)

    inject = [
        ("<p>Every number above is measured rather than estimated", fig_icons()),
        # the skeleton belongs with the roof workstream, where the claim is made
        ('<dt>Key</dt><dd><code>w = cot', fig_skeleton()),
        ('<div class="card">\n<h4>2 · Grammar', fig_embed(
            BASE + "/moulding/wm_profile_sheet.svg", 4,
            "<b>Figure 4 — The WM Standard Moulding chart, vectorised.</b> 130 "
            "distinct profiles carrying roughly 200 codes: several codes share a "
            "silhouette at different sizes, which is the catalog pattern in "
            "miniature — shape and dimensions are separate columns. Every one of "
            "these is a stack from a small classical vocabulary (fillet, bead, "
            "ovolo, cove, scotia, cyma, quirk, chamfer), which is not a modelling "
            "trick but how they are milled: one shaper knife per element. Traced "
            "by Jordan from the Wholesale Millwork chart; the layout is preserved "
            "so position identifies the section.")),
        ('<div class="card">\n<h4>3 · Classification', fig_embed(
            BASE + "/footprint_sheet.svg", 5,
            "<b>Figure 5 — Footprint classification for arbitrary polygons.</b> "
            "Walls in blue, convex corners amber, reflex corners oxide; "
            "<code>C01</code> marks the index origin. The three shipped shapes "
            "needed 277 hand-authored nodes and could not produce a U, T, cross or "
            "curve at all. Corner treatment is per corner — the bottom row shows "
            "chamfer, all-filleted, and the real shipping shape: one large arc on "
            "a single corner at 0.4&nbsp;&times;&nbsp;width.")),
    ]
    for anchor, block in inject:
        if not block:
            continue
        if anchor in s:
            s = s.replace(anchor, block + "\n" + anchor, 1)
        else:
            print("  !! anchor not found: %s" % anchor[:44])

    # extrusions go inside the metal extrusion workstream
    a = "<dt>Next</dt><dd><code>steel_sections.csv</code>"
    if a in s:
        s = s.replace("</dl>\n</div>\n\n<div class=\"ws\">\n<div class=\"hd\"><h4>Mouldings",
                      "</dl>\n" + fig_extrusions() + "\n</div>\n\n<div class=\"ws\">"
                      "\n<div class=\"hd\"><h4>Mouldings", 1)

    open(OUT, "w", encoding="utf-8").write(s)
    print("wrote %s (%.1f MB)" % (OUT, os.path.getsize(OUT) / 1048576.0))
    print("figures: %d" % s.count("<figcaption>"))


if __name__ == "__main__":
    main()
