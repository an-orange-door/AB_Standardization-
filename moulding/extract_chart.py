"""Read the vectorised WM chart and work out what is actually in it.

    python U:/AB_Standardization/moulding/extract_chart.py

Pure Python. Reports only.

Jordan vectorised the Standard Moulding Profiles chart and KEPT THE LAYOUT, so
each silhouette's position on the page identifies which section it belongs to —
WINDOW, CEILING, FLOOR, WALL, DOOR, PANEL, MISC. That is the key: the SVG has no
text, no groups and no ids, so position is the only handle on identity, and it
is a good one.

This replaces guessing silhouettes from a printed picture. Five of the 26
profiles in the earlier grammar were marked approximate for exactly that reason.
"""
import collections
import os
import re

SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                   "StandardWallChartFeb2024.svg")

# Chart regions as fractions of the 2978 x 2308 viewBox, read off the artwork.
# x0, y0, x1, y1, name
REGIONS = [
    (0.10, 0.00, 0.33, 0.46, "WINDOW"),
    (0.33, 0.00, 0.57, 0.15, "CEILING"),
    (0.57, 0.00, 0.75, 0.15, "CEILING/cove-rake-bed"),
    (0.75, 0.00, 1.00, 0.24, "PANEL"),
    (0.33, 0.15, 0.75, 0.34, "FLOOR"),
    (0.10, 0.34, 0.42, 0.45, "WALL/chair rail"),
    (0.42, 0.34, 0.75, 0.45, "DOOR"),
    (0.75, 0.24, 1.00, 0.45, "PANEL/wainscot"),
    (0.00, 0.45, 1.00, 1.00, "MISC"),
]

NUM = re.compile(r"[-+]?(?:\d*\.\d+|\d+)(?:[eE][-+]?\d+)?")
CMD = re.compile(r"([MmLlHhVvCcSsQqTtAaZz])([^MmLlHhVvCcSsQqTtAaZz]*)")


def subpaths(d):
    """Split a path into subpaths and return each one's points.

    Control points are included in the extent, which slightly overstates a
    curve's bounds. That is fine here: the bounds are used to place a profile on
    the page and to size it, not to reconstruct it.
    """
    out, cur = [], []
    x = y = sx = sy = 0.0
    for cmd, args in CMD.findall(d):
        n = [float(v) for v in NUM.findall(args)]
        rel = cmd.islower()
        c = cmd.upper()
        if c == "M":
            if cur:
                out.append(cur)
            cur = []
            for i in range(0, len(n) - 1, 2):
                px, py = n[i], n[i + 1]
                x, y = (x + px, y + py) if rel else (px, py)
                if i == 0:
                    sx, sy = x, y
                cur.append((x, y))
        elif c in "LT":
            for i in range(0, len(n) - 1, 2):
                px, py = n[i], n[i + 1]
                x, y = (x + px, y + py) if rel else (px, py)
                cur.append((x, y))
        elif c == "H":
            for v in n:
                x = x + v if rel else v
                cur.append((x, y))
        elif c == "V":
            for v in n:
                y = y + v if rel else v
                cur.append((x, y))
        elif c in "CSQA":
            step = {"C": 6, "S": 4, "Q": 4, "A": 7}[c]
            for i in range(0, len(n) - step + 1, step):
                seg = n[i:i + step]
                if c == "A":
                    px, py = seg[5], seg[6]
                    x, y = (x + px, y + py) if rel else (px, py)
                    cur.append((x, y))
                else:
                    for j in range(0, step, 2):
                        px, py = seg[j], seg[j + 1]
                        ax, ay = (x + px, y + py) if rel else (px, py)
                        cur.append((ax, ay))
                    x, y = cur[-1]
        elif c == "Z":
            if cur:
                cur.append((sx, sy))
                out.append(cur)
                cur = []
            x, y = sx, sy
    if cur:
        out.append(cur)
    return [p for p in out if len(p) > 2]


def bbox(pts):
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    return min(xs), min(ys), max(xs), max(ys)


def region(cx, cy, W, H):
    fx, fy = cx / W, cy / H
    for x0, y0, x1, y1, name in REGIONS:
        if x0 <= fx < x1 and y0 <= fy < y1:
            return name
    return "?"


def main():
    s = open(SRC, encoding="utf-8", errors="replace").read()
    vb = re.search(r'viewBox="([\d.\-\s]+)"', s).group(1).split()
    W, H = float(vb[2]), float(vb[3])
    ds = re.findall(r'\sd="([^"]+)"', s)
    print("paths in file      : %d" % len(ds))

    shapes = []
    for i, d in enumerate(ds):
        for sp in subpaths(d):
            x0, y0, x1, y1 = bbox(sp)
            w, h = x1 - x0, y1 - y0
            if w < 3 or h < 3:
                continue                      # rules, ticks, artefacts
            shapes.append({"path": i, "pts": len(sp), "bbox": (x0, y0, x1, y1),
                           "w": w, "h": h, "cx": (x0+x1)/2, "cy": (y0+y1)/2})
    print("closed subpaths    : %d" % len(shapes))
    print("  (a compound path holds several profiles, so this exceeds the path count)")

    big = [s_ for s_ in shapes if s_["w"] > 12 and s_["h"] > 12]
    print("plausible profiles : %d  (bigger than 12 x 12 units)" % len(big))

    by = collections.Counter(region(s_["cx"], s_["cy"], W, H) for s_ in big)
    print("")
    print("=== by chart region ===")
    for name in [r[4] for r in REGIONS] + ["?"]:
        if by.get(name):
            print("   %-24s %d" % (name, by[name]))

    print("")
    print("=== size distribution (units on a %.0f x %.0f page) ===" % (W, H))
    ws = sorted(s_["w"] for s_ in big)
    hs = sorted(s_["h"] for s_ in big)
    print("   width  min %.0f  median %.0f  max %.0f" % (ws[0], ws[len(ws)//2], ws[-1]))
    print("   height min %.0f  median %.0f  max %.0f" % (hs[0], hs[len(hs)//2], hs[-1]))

    print("")
    print("=== the ten largest, which should be the base and crown profiles ===")
    for s_ in sorted(big, key=lambda z: -(z["w"]*z["h"]))[:10]:
        print("   path %-3d %6.0f x %-6.0f at (%5.0f,%5.0f)  %-24s %d pts"
              % (s_["path"], s_["w"], s_["h"], s_["cx"], s_["cy"],
                 region(s_["cx"], s_["cy"], W, H), s_["pts"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
