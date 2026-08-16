"""A moulding profile as a GRAMMAR of classical elements, not a hand-built curve.

    python U:/AB_Standardization/moulding/moulding_grammar.py

Pure Python + SVG. No Houdini, no license - so the silhouettes can be checked
against the WM chart before any of this goes near an HDA.

─── THE IDEA ──────────────────────────────────────────────────────────────────
Every profile on the WM Standard Moulding chart is a stack from a small
vocabulary - fillet, bead, ovolo, cove, scotia, cyma, quirk, chamfer. That is
not a modelling trick, it is how they are milled: one shaper knife per element.
So a profile is DATA - an ordered list - and ~10 element generators produce the
whole chart plus anything custom. 200 hand-built networks is the alternative,
and FancyCurves already shows where that ends (53 parms and 10 separate
division controls for SIX profiles).

─── WHY EACH ELEMENT TAKES (dx, dy) RATHER THAN A RADIUS ──────────────────────
The authoring case is someone looking at the poster. Reading "this ogee occupies
about a quarter of the height and projects about a third" is easy; deriving its
radius and arc centre is not. So every element declares the BOX it consumes and
fills that box with its characteristic curve.
Two things fall out of that for free:
  - elements chain without anyone computing absolute coordinates (the cursor
    just advances), and
  - the dy values must sum to the profile's stated width, which makes the
    catalog dimension a MECHANICAL CHECK rather than a claim. See verify().

─── AXES ──────────────────────────────────────────────────────────────────────
    X = projection from the wall  (the chart's first number, e.g. 11/16)
    Y = along the wall / face      (the chart's second number, e.g. 5-1/4)
Origin is the wall at the bottom of the piece, matching how it would be swept.
Grammar is authored NORMALISED (x and y both 0..1) and scaled by the catalog
row, so one grammar serves every size in a family.

⚠ CONVEXITY RULE, derived once so it is not re-guessed per element:
from P0 to P1 = P0+(dx,dy), a quarter arc centred at (P0.x, P1.y) bulges AWAY
from the wall (convex); centred at (P1.x, P0.y) it hollows toward it (concave).
"""
import math
import os
import re

OUT = os.path.dirname(os.path.abspath(__file__))
SEGS = 24                       # arc subdivision; the HDA will expose this


# ── element library ──────────────────────────────────────────────────────────
# Each returns the points AFTER the entry point, walking from (0,0) to (dx,dy)
# in its own local box. The cursor translates them into place.

def _arc(dx, dy, cx, cy, segs):
    """Quarter arc from (0,0) to (dx,dy) about (cx,cy)."""
    r0 = math.atan2(0 - cy, 0 - cx)
    r1 = math.atan2(dy - cy, dx - cx)
    # take the short way round
    while r1 - r0 > math.pi:
        r1 -= 2 * math.pi
    while r0 - r1 > math.pi:
        r1 += 2 * math.pi
    rx, ry = abs(dx), abs(dy)
    return [(cx + math.cos(r0 + (r1 - r0) * i / segs) * rx,
             cy + math.sin(r0 + (r1 - r0) * i / segs) * ry)
            for i in range(1, segs + 1)]


def line(dx, dy, segs=SEGS):
    """FILLET - a flat band. The connective tissue of every profile."""
    return [(dx, dy)]


fillet = line


def chamfer(dx, dy, segs=SEGS):
    """A 45-degree cut. Geometrically a line; named separately because the
    catalog distinguishes it and a reader should see the intent."""
    return [(dx, dy)]


def ovolo(dx, dy, segs=SEGS):
    """Convex quarter round - bulges away from the wall."""
    return _arc(dx, dy, 0, dy, segs)


def cove(dx, dy, segs=SEGS):
    """CAVETTO - concave quarter round, hollows toward the wall."""
    return _arc(dx, dy, dx, 0, segs)


cavetto = cove


def bead(dx, dy, segs=SEGS):
    """ASTRAGAL - a half-round bump. dy is the diameter, dx the projection."""
    pts = []
    for i in range(1, segs + 1):
        t = math.pi * i / segs
        pts.append((math.sin(t) * dx, (1 - math.cos(t)) * 0.5 * dy))
    return pts


astragal = bead


def round_(dx, dy, segs=SEGS):
    """Full half-round, used for dowel-like stock (WM232 etc)."""
    return bead(dx, dy, segs)


def scotia(dx, dy, segs=SEGS):
    """A deep concave hollow with two radii - the lower one larger. A single
    arc reads as a plain cove; the asymmetry is what makes it a scotia."""
    a = _arc(dx * 0.62, dy * 0.5, dx * 0.62, 0, segs // 2)
    b = _arc(dx * 0.38, dy * 0.5, dx * 0.38, 0, segs // 2)
    return a + [(a[-1][0] + p[0], a[-1][1] + p[1]) for p in b]


def cyma_recta(dx, dy, segs=SEGS, split=0.5):
    """S-curve, CONCAVE first then convex, reading in the direction of travel."""
    h1, h2 = dy * split, dy * (1 - split)
    w1, w2 = dx * split, dx * (1 - split)
    a = cove(w1, h1, max(segs // 2, 2))
    b = ovolo(w2, h2, max(segs // 2, 2))
    return a + [(a[-1][0] + p[0], a[-1][1] + p[1]) for p in b]


def cyma_reversa(dx, dy, segs=SEGS, split=0.5):
    """OGEE - convex first then concave. The most common decorative element."""
    h1, h2 = dy * split, dy * (1 - split)
    w1, w2 = dx * split, dx * (1 - split)
    a = ovolo(w1, h1, max(segs // 2, 2))
    b = cove(w2, h2, max(segs // 2, 2))
    return a + [(a[-1][0] + p[0], a[-1][1] + p[1]) for p in b]


ogee = cyma_reversa


def quirk(dx, dy, segs=SEGS):
    """A narrow square groove that separates two elements and casts a shadow
    line. Cuts IN toward the wall, runs, and comes back out."""
    return [(-abs(dx), 0), (-abs(dx), dy), (0, dy)]


ELEMENTS = {n: f for n, f in list(globals().items())
            if callable(f) and not n.startswith("_")
            and n in ("line", "fillet", "chamfer", "ovolo", "cove", "cavetto",
                      "bead", "astragal", "round_", "scotia", "cyma_recta",
                      "cyma_reversa", "ogee", "quirk")}

TOKEN = re.compile(r"([a-z_]+)\s*\(([^)]*)\)")


def build(grammar, segs=SEGS):
    """Walk the grammar with a cursor. Returns the face curve, normalised."""
    pts = [(0.0, 0.0)]
    for name, args in TOKEN.findall(grammar):
        fn = ELEMENTS.get(name)
        if fn is None:
            raise ValueError("unknown element %r in %r" % (name, grammar))
        a = [float(x) for x in args.split(",") if x.strip() != ""]
        cx, cy = pts[-1]
        for px, py in fn(*a, segs=segs):
            pts.append((cx + px, cy + py))
    return pts


def verify(profile, tol=1e-6):
    """The dimension check the catalog makes possible.

    A grammar's extents MUST reach 1.0 in y (it spans the full face) and must
    not exceed 1.0 in x (it cannot project past its own thickness). Anything
    else means the row is mis-authored, and it is caught here rather than by
    someone noticing the moulding looks wrong three tools downstream.
    """
    pts = build(profile["grammar"])
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    issues = []
    if abs(max(ys) - 1.0) > 0.02:
        issues.append("y extent %.3f, expected 1.0" % max(ys))
    if max(xs) > 1.0 + 0.02:
        issues.append("x extent %.3f exceeds 1.0" % max(xs))
    if min(xs) < -0.02:
        issues.append("x goes %.3f behind the wall" % min(xs))
    return issues


def frac(s):
    """'1-5/8' -> 1.625. The chart is entirely in fractional inches."""
    s = s.strip()
    whole = 0.0
    if "-" in s:
        w, s = s.split("-", 1)
        whole = float(w)
    if "/" in s:
        n, d = s.split("/")
        return whole + float(n) / float(d)
    return whole + float(s)


# ── catalog ──────────────────────────────────────────────────────────────────
# thickness x width are TRANSCRIBED FROM THE CHART TEXT and are exact.
# ⚠ The grammars are my reading of the printed silhouettes at poster scale.
# The simple sections are unambiguous; the ones marked ~ are approximations to
# be refined against a real profile drawing before anything ships.
CATALOG = [
    # code, category, sub, thickness, width, grammar, confident?
    ("WM104", "Floor", "Quarter Round", "1", "1", "ovolo(1,1)", True),
    ("WM105", "Floor", "Quarter Round", "3/4", "3/4", "ovolo(1,1)", True),
    ("WM108", "Floor", "Quarter Round", "1/2", "1/2", "ovolo(1,1)", True),
    ("WM110", "Floor", "Quarter Round", "1/4", "1/4", "ovolo(1,1)", True),

    ("WM126", "Floor", "Shoe", "1/2", "3/4", "line(0,.18) ovolo(1,.82)", True),
    ("WM127", "Floor", "Shoe", "7/16", "3/4", "line(0,.15) ovolo(1,.85)", True),
    ("WM130", "Floor", "Shoe", "1/2", "1", "line(0,.2) ovolo(1,.8)", True),

    ("WM120", "Panel", "Half Round", "1/2", "1", "bead(1,1)", True),
    ("WM122", "Panel", "Half Round", "3/8", "1", "bead(1,1)", True),
    ("WM124", "Panel", "Half Round", "1/4", "1/2", "bead(1,1)", True),
    ("WM232", "Misc", "Full Round", "1-9/16", "1-9/16", "bead(1,1)", True),

    ("WM100", "Ceiling", "Cove", "11/16", "11/16", "cove(1,1)", True),
    ("WM101", "Ceiling", "Cove", "1/2", "1/2", "cove(1,1)", True),

    ("WM995", "Misc", "Chamfer", "3/4", "3/4", "chamfer(1,1)", True),
    ("WM996", "Misc", "Chamfer", "1", "1", "chamfer(1,1)", True),

    ("WM254", "Misc", "Parting Bead", "1/2", "3/4",
     "line(1,0) line(0,1) line(-1,0)", True),
    ("WM265W", "Misc", "Lattice", "1/4", "1-3/4",
     "line(1,0) line(0,1) line(-1,0)", True),
    ("WM246", "Misc", "S4S", "11/16", "2-5/8",
     "line(1,0) line(0,1) line(-1,0)", True),

    ("WM138", "Panel", "Screen Bead", "5/16", "5/8", "bead(1,1)", True),
    ("WM142", "Panel", "Screen Bead", "1/4", "3/4",
     "line(1,.15) line(0,.7) line(-1,.15)", True),

    ("WM202", "Misc", "Corner Guard", "11/16", "1-1/16",
     "line(1,0) line(0,1) line(-1,0)", True),

    # ~ approximations from the printed silhouette
    ("WM70", "Ceiling", "Bed", "9/16", "1-5/8",
     "line(0,.12) cove(.55,.5) line(.45,.1) ovolo(0,.28)", False),
    ("WM426", "Floor", "Base Cap", "11/16", "1-1/8",
     "line(0,.1) cyma_reversa(.8,.62) line(.2,.1) ovolo(0,.18)", False),
    ("WM77", "Wall", "Chair Rail", "11/16", "2-1/4",
     "line(0,.08) ovolo(.35,.14) quirk(.08,.05) cyma_reversa(.5,.4) "
     "line(.15,.08) cove(-.4,.16) line(-.6,.09)", False),
    ("WM163E", "Floor", "Base", "11/16", "5-1/4",
     "line(0,.72) cyma_reversa(.62,.14) quirk(.06,.02) ovolo(.32,.06) "
     "line(.06,.04) cove(-1,.02)", False),
    ("WM49", "Ceiling", "Crown", "9/16", "3-5/8",
     "line(0,.08) cove(.42,.34) line(.1,.06) cyma_recta(.48,.44) "
     "line(0,.08)", False),
]


def main():
    rows = []
    for code, cat, sub, th, wd, gram, sure in CATALOG:
        p = {"code": code, "cat": cat, "sub": sub, "grammar": gram,
             "th": frac(th), "wd": frac(wd), "th_s": th, "wd_s": wd,
             "sure": sure}
        p["issues"] = verify(p)
        p["pts"] = build(gram)
        rows.append(p)

    bad = [r for r in rows if r["issues"]]
    print("profiles          : %d" % len(rows))
    print("  transcribed     : %d confident, %d approximate"
          % (sum(1 for r in rows if r["sure"]),
             sum(1 for r in rows if not r["sure"])))
    print("  dimension check : %d clean, %d flagged" % (len(rows) - len(bad), len(bad)))
    for r in bad:
        print("     %-8s %s" % (r["code"], "; ".join(r["issues"])))

    svg = render(rows)
    path = os.path.join(OUT, "wm_profile_sheet.svg")
    with open(path, "w", encoding="utf-8") as f:
        f.write(svg)
    print("\nwrote %s (%.0f KB)" % (path, os.path.getsize(path) / 1024.0))

    csvp = os.path.join(OUT, "moulding_catalog.csv")
    with open(csvp, "w", encoding="utf-8", newline="") as f:
        f.write("wm_code,category,sub,thickness,width,grammar,confidence\n")
        for r in rows:
            f.write('%s,%s,%s,%s,%s,"%s",%s\n' % (
                r["code"], r["cat"], r["sub"], r["th_s"], r["wd_s"],
                r["grammar"], "measured" if r["sure"] else "approximate"))
    print("wrote %s" % csvp)


# ── SVG sheet ────────────────────────────────────────────────────────────────
PPI = 46.0          # px per inch: everything is drawn to a common real scale,
                    # so a 1/4" quarter round really is a quarter the size of a
                    # 1" one - which is how the chart reads and how a mistake in
                    # the catalog dimensions becomes visible.
COLW, ROWH, PAD = 178, 250, 26


def render(rows):
    groups = {}
    for r in rows:
        groups.setdefault(r["cat"], []).append(r)
    order = ["Floor", "Ceiling", "Wall", "Panel", "Misc"]
    cats = [c for c in order if c in groups] + \
           [c for c in groups if c not in order]

    body, y = [], 66
    for cat in cats:
        body.append('<text x="%d" y="%d" class="cat">%s</text>'
                    % (PAD, y, cat.upper()))
        y += 16
        for i, r in enumerate(groups[cat]):
            col = i % 5
            if col == 0 and i:
                y += ROWH
            body.append(cell(r, PAD + col * COLW, y))
        y += ROWH + 26

    h = y + 40
    return SVG_HEAD % (max(h, 400), max(h, 400)) + "\n".join(body) + "</svg>"


def cell(r, x, y):
    sx, sy = r["th"] * PPI, r["wd"] * PPI
    pts = [(x + px * sx, y + 176 - py * sy) for px, py in r["pts"]]
    # close the silhouette back down the wall face, which is what makes it read
    # as a solid section rather than a stray line
    # close back along the wall so it reads as a solid section, not a stray line
    closed = pts + [(x, y + 176 - r["pts"][-1][1] * sy), (x, y + 176)]
    path = ("M %.2f %.2f " % closed[0]
            + " ".join("L %.2f %.2f" % p for p in closed[1:]) + " Z")
    flag = "" if r["sure"] else ' <tspan class="approx">~</tspan>'
    return ('<g><line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" class="wall"/>'
            '<path d="%s" class="prof"/>'
            '<text x="%.1f" y="%.1f" class="code">%s%s</text>'
            '<text x="%.1f" y="%.1f" class="dim">%s &#215; %s</text>'
            '<text x="%.1f" y="%.1f" class="sub">%s</text></g>'
            % (x, y + 176 - sy, x, y + 176,
               path,
               x, y + 198, r["code"], flag,
               x, y + 211, r["th_s"], r["wd_s"],
               x, y + 224, r["sub"]))


SVG_HEAD = """<svg xmlns="http://www.w3.org/2000/svg" width="960" height="%d"
 viewBox="0 0 960 %d" font-family="ui-sans-serif,system-ui,Segoe UI,sans-serif">
<style>
  .bg{fill:#0B0D0C}
  .prof{fill:none;stroke:#EDEDE8;stroke-width:1.5;stroke-linejoin:round}
  .wall{stroke:#7FA6BA;stroke-width:1;stroke-dasharray:3 3;opacity:.65}
  .cat{font-size:12px;font-weight:700;letter-spacing:.09em;fill:#8A9088}
  .code{font-size:11px;font-weight:700;fill:#EDEDE8}
  .dim{font-size:10.5px;fill:#8A9088;font-family:ui-monospace,Consolas,monospace}
  .sub{font-size:10px;fill:#6E756D}
  .approx{fill:#D4A94F;font-weight:700}
  .t{font-size:17px;font-weight:700;fill:#EDEDE8}
  .s{font-size:11.5px;fill:#8A9088}
</style>
<rect width="960" height="100%%" class="bg"/>
<text x="26" y="34" class="t">WM profiles from grammar</text>
<text x="26" y="52" class="s">Built from 10 elements. Blue dashes mark the wall
face. Drawn to a common scale, so sizes compare directly.
<tspan class="approx">~</tspan> = silhouette approximated from the poster.</text>
"""


if __name__ == "__main__":
    main()
