"""Render the vectorised chart with every silhouette numbered, in position.

    python U:/AB_Standardization/moulding/index_chart.py

Pure Python. Writes moulding/chart_indexed.svg.

The SVG carries no text, no groups and no ids, so a shape's identity has to come
from somewhere. Guessing region boundaries from fractions of the page was wrong
— it put 65 of 130 shapes in "MISC". So instead: draw what is actually there,
keep the original coordinates, and put an index on each shape. Jordan reads the
chart, and the numbers become the key.

That is faster and more reliable than any heuristic, because he already knows
which silhouette is which and the chart layout is preserved.
"""
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "StandardWallChartFeb2024.svg")
OUT = os.path.join(HERE, "chart_indexed.svg")

NUM = re.compile(r"[-+]?(?:\d*\.\d+|\d+)(?:[eE][-+]?\d+)?")
CMD = re.compile(r"([MmLlHhVvCcSsQqTtAaZz])([^MmLlHhVvCcSsQqTtAaZz]*)")


def extents(d):
    """Bounding box of a path, accumulating relative commands correctly."""
    x = y = sx = sy = 0.0
    xs, ys = [], []
    for cmd, args in CMD.findall(d):
        n = [float(v) for v in NUM.findall(args)]
        rel = cmd.islower()
        c = cmd.upper()
        if c == "M":
            for i in range(0, len(n) - 1, 2):
                x, y = (x + n[i], y + n[i+1]) if rel else (n[i], n[i+1])
                if i == 0:
                    sx, sy = x, y
                xs.append(x); ys.append(y)
        elif c in "LT":
            for i in range(0, len(n) - 1, 2):
                x, y = (x + n[i], y + n[i+1]) if rel else (n[i], n[i+1])
                xs.append(x); ys.append(y)
        elif c == "H":
            for v in n:
                x = x + v if rel else v
                xs.append(x); ys.append(y)
        elif c == "V":
            for v in n:
                y = y + v if rel else v
                xs.append(x); ys.append(y)
        elif c in "CSQA":
            step = {"C": 6, "S": 4, "Q": 4, "A": 7}[c]
            for i in range(0, len(n) - step + 1, step):
                seg = n[i:i+step]
                if c == "A":
                    x, y = (x + seg[5], y + seg[6]) if rel else (seg[5], seg[6])
                    xs.append(x); ys.append(y)
                else:
                    for j in range(0, step, 2):
                        ax, ay = (x + seg[j], y + seg[j+1]) if rel else (seg[j], seg[j+1])
                        xs.append(ax); ys.append(ay)
                    x, y = xs[-1], ys[-1]
        elif c == "Z":
            x, y = sx, sy
    return (min(xs), min(ys), max(xs), max(ys)) if xs else None


def main():
    s = open(SRC, encoding="utf-8", errors="replace").read()
    vb = re.search(r'viewBox="([\d.\-\s]+)"', s).group(1).split()
    W, H = float(vb[2]), float(vb[3])
    ds = re.findall(r'\sd="([^"]+)"', s)

    body = []
    labels = []
    rows = []
    for i, d in enumerate(ds):
        # Blueprint convention: white outline on black, never filled. The
        # source already sets fill:none — what it lacks is a stroke, so the
        # shapes render invisible. Give them one.
        body.append('<path d="%s" fill="none" stroke="#EDEDE8" stroke-width="2" '
                    'fill-rule="evenodd"/>' % d)
        b = extents(d)
        if not b:
            continue
        x0, y0, x1, y1 = b
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        labels.append(
            '<circle cx="%.1f" cy="%.1f" r="13" fill="#D4A94F"/>'
            '<text x="%.1f" y="%.1f" font-size="15" font-weight="700" '
            'text-anchor="middle" fill="#0B0D0C" '
            'font-family="ui-sans-serif,system-ui,sans-serif">%d</text>'
            % (cx, cy, cx, cy + 5, i))
        rows.append((i, x0, y0, x1 - x0, y1 - y0))

    svg = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %g %g" '
           'width="%g" height="%g">\n'
           '<rect width="100%%" height="100%%" fill="#0B0D0C"/>\n'
           '%s\n%s\n</svg>' % (W, H, W, H, "\n".join(body), "\n".join(labels)))
    open(OUT, "w", encoding="utf-8", newline="\n").write(svg)
    print("wrote %s (%.0f KB) — %d shapes numbered 0..%d"
          % (OUT, os.path.getsize(OUT) / 1024.0, len(rows), len(rows) - 1))

    # a companion table, so the numbers can be matched to positions in text
    csvp = os.path.join(HERE, "chart_index.csv")
    with open(csvp, "w", encoding="utf-8", newline="") as f:
        f.write("index,x,y,width,height,wm_code,section,subsection,notes\n")
        for i, x, y, w, h in rows:
            f.write("%d,%.0f,%.0f,%.0f,%.0f,,,,\n" % (i, x, y, w, h))
    print("wrote %s — blank wm_code / section columns to fill in" % csvp)
    print("")
    print("The chart has roughly 200 profiles and this file holds %d shapes, so"
          % len(rows))
    print("some did not trace or are merged. Worth checking against the poster.")


if __name__ == "__main__":
    main()
