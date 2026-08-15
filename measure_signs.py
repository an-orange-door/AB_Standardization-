"""Measure every sign PNG so geometry can be generated from data, not by hand.

For each image, using ImageMagick only (no PIL):
  - content bounding box   : the pixels that are actually opaque, not the 2048 frame
  - fill ratio             : opaque px / bbox area   -> the primary shape signature
  - corner occupancy       : are the 4 bbox corners opaque -> separates diamond/triangle
  - edge-midpoint occupancy: separates octagon/shield from circle
  - component count        : one blob = a sign plate, many = a pictogram/decal

Writes SignsSymbols_measured.csv. Shape classification happens in classify(), which
is deliberately a pure function of the measured numbers so it can be re-tuned
without re-measuring.
"""
import os, csv, math, subprocess, sys

ROOT = "U:/Textures/SignsSymbols"
OUT  = "U:/AB_Standardization/SignsSymbols_measured.csv"
MAGICK = "magick"


def sh(args):
    try:
        r = subprocess.run(args, capture_output=True, text=True, timeout=120)
        return r.stdout.strip()
    except Exception:
        return ""


def measure(path):
    # one call: trimmed size, offset into the original frame, and mean alpha in bbox
    out = sh([MAGICK, path, "-alpha", "extract", "-trim",
              "-format", "%w %h %X %Y %[fx:mean] %[fx:w] %[fx:h]", "info:"])
    p = out.replace("+", " ").split()
    if len(p) < 5:
        return None
    w, h, ox, oy = int(p[0]), int(p[1]), int(p[2]), int(p[3])
    fill = float(p[4])

    # second call: 20x20 thumbnail of the trimmed alpha for corner / edge probes
    probe = sh([MAGICK, path, "-alpha", "extract", "-trim", "-resize", "20x20!",
                "-format",
                "%[fx:(p{1,1}+p{18,1}+p{1,18}+p{18,18})/4] "      # corners
                "%[fx:(p{10,0}+p{10,19}+p{0,10}+p{19,10})/4] "     # edge midpoints
                "%[fx:p{10,10}]",                                  # centre
                "info:"])
    q = probe.split()
    corners = float(q[0]) if len(q) > 0 else -1.0
    edges   = float(q[1]) if len(q) > 1 else -1.0
    centre  = float(q[2]) if len(q) > 2 else -1.0

    # original frame size, to turn the bbox into a UV window
    fw, fh = sh([MAGICK, path, "-format", "%w %h", "info:"]).split()[:2]
    return dict(w=w, h=h, ox=ox, oy=oy, fw=int(fw), fh=int(fh),
                fill=fill, corners=corners, edges=edges, centre=centre)


def classify(m):
    """Shape from measured numbers. Tuned against a hand-checked sample."""
    f, c, e = m["fill"], m["corners"], m["edges"]
    asp = m["w"] / float(m["h"])

    # a plate is a solid blob; a pictogram is sparse line-art with no background
    if f < 0.45:
        return "Pictogram"

    if f > 0.96 and c > 0.9:
        return "Rectangle"
    if 0.88 <= f <= 0.99 and 0.2 < c < 0.9:
        return "RectangleCut"          # one or more corners clipped
    if 0.74 <= f <= 0.82 and c < 0.15:
        return "Circle" if 0.9 <= asp <= 1.1 else "Ellipse"
    if 0.45 <= f <= 0.62 and c < 0.15:
        return "Diamond"
    if 0.45 <= f <= 0.65 and c >= 0.15:
        return "Triangle"
    if 0.63 <= f <= 0.74 and c < 0.15:
        return "Octagon"
    if 0.78 < f <= 0.88 and c < 0.15:
        return "Shield"
    if 0.78 < f <= 0.9 and c >= 0.15:
        return "Trapezoid"
    return "Misc"                       # -> trace SOP


rows = []
files = []
for dp, dn, fn in os.walk(ROOT):
    for fnm in sorted(fn):
        if fnm.lower().endswith(".png"):
            files.append((os.path.relpath(dp, ROOT).replace(os.sep, "/"),
                          fnm, os.path.join(dp, fnm)))

print("measuring %d images" % len(files))
for i, (rel, fnm, path) in enumerate(files):
    m = measure(path)
    if not m:
        print("  FAILED", fnm)
        continue
    shape = classify(m)
    # UV window: where the content sits inside the original frame, v flipped
    u0 = m["ox"] / float(m["fw"])
    u1 = (m["ox"] + m["w"]) / float(m["fw"])
    v1 = 1.0 - m["oy"] / float(m["fh"])
    v0 = 1.0 - (m["oy"] + m["h"]) / float(m["fh"])
    rows.append(dict(
        folder=rel, file=fnm, shape=shape,
        content_w=m["w"], content_h=m["h"],
        aspect=round(m["w"] / float(m["h"]), 4),
        fill=round(m["fill"], 4), corners=round(m["corners"], 3),
        edges=round(m["edges"], 3),
        u0=round(u0, 6), v0=round(v0, 6), u1=round(u1, 6), v1=round(v1, 6),
    ))
    if i % 100 == 0:
        print("  %d/%d" % (i, len(files)))
        sys.stdout.flush()

with open(OUT, "w", newline="", encoding="utf-8") as fh:
    wtr = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
    wtr.writeheader()
    wtr.writerows(rows)

import collections
print("\nshape distribution:")
for s, n in collections.Counter(r["shape"] for r in rows).most_common():
    print("  %-14s %4d" % (s, n))
print("\nwritten:", OUT, len(rows), "rows")
