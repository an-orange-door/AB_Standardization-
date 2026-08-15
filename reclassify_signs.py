"""Re-derive the shape column from SignsSymbols_measured.csv. No re-measuring.

Tuned against the measured data rather than theory:

  Circles are astonishingly tight - 168 of 175 land in 0.777-0.794 around
  pi/4 = 0.7854. The seven that fall outside are, without exception, the route
  shields. So a NARROW circle band is what separates circle from shield; a wide
  one silently turns every US route shield into a disc.

  Anything solid but not confidently one of the primitives goes to Traced. Trace
  is always correct, just slower, so ambiguity should fall that way rather than
  produce a confidently wrong plate.
"""
import csv, collections, os

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "SignsSymbols_measured.csv")

PI4 = 0.7854
CIRCLE_TOL = 0.009          # empirical: covers 96% of true circles, zero shields


def classify(fill, corners, edges, aspect):
    # sparse line-art with no background: a decal, not a sign plate
    if fill < 0.45:
        return "Pictogram"

    # solid rectangle - fills its bbox and owns all four corners
    if fill > 0.96 and corners > 0.9:
        return "Rectangle"

    # circle / ellipse: pi/4 and nothing else
    if abs(fill - PI4) <= CIRCLE_TOL and corners < 0.15:
        return "Circle" if 0.92 <= aspect <= 1.08 else "Ellipse"

    # half the bbox: diamond has bare corners, triangle keeps two of them
    if 0.45 <= fill <= 0.62:
        return "Diamond" if corners < 0.15 else "Triangle"

    # octagon sits well below pi/4
    if 0.63 <= fill <= 0.75 and corners < 0.15:
        return "Octagon"

    return "Traced"


rows = list(csv.DictReader(open(SRC, encoding="utf-8")))
before = collections.Counter(r["shape"] for r in rows)
changed = []
for r in rows:
    new = classify(float(r["fill"]), float(r["corners"]),
                   float(r["edges"]), float(r["aspect"]))
    if new != r["shape"]:
        changed.append((r["file"], r["shape"], new))
    r["shape"] = new

with open(SRC, "w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
    w.writeheader()
    w.writerows(rows)

after = collections.Counter(r["shape"] for r in rows)
print("%-14s %6s %6s" % ("shape", "before", "after"))
for s in sorted(set(before) | set(after)):
    print("%-14s %6d %6d" % (s, before.get(s, 0), after.get(s, 0)))
print("\nreclassified: %d rows" % len(changed))
print("parametric: %d   traced: %d   decals: %d" % (
    sum(v for k, v in after.items() if k not in ("Traced", "Pictogram")),
    after.get("Traced", 0), after.get("Pictogram", 0)))
print("\nshields, now traced:")
for f, o, n in changed:
    if "Shield" in f or "Stop_X02" in f:
        print("   %-46s %s -> %s" % (f, o, n))
