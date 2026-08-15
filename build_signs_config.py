"""Fold the measured sign data into one config file the HDAs read.

Output: U:/Git/AssetBashTools/config/signs_library.csv

It lives in config/ beside zone_vocabulary.json and material_bindings.json rather
than inside an HDA section. Embedding it would repeat exactly the mistake we spent
2026-08-14 undoing - data baked into binary assets that nothing can update.

Texture paths are stored relative and resolved through $AB_SIGNS at cook time, so a
customer sets one variable rather than editing 1,383 rows.
"""
import csv, os, re, collections

MEASURED = "U:/AB_Standardization/SignsSymbols_measured.csv"
OUT      = "U:/Git/AssetBashTools/config/signs_library.csv"

# SignPlate's Shape menu order - the CSV stores the INDEX so the HDA needs no lookup
SHAPE_INDEX = {"Rectangle": 0, "Circle": 1, "Ellipse": 2, "Diamond": 3,
               "Triangle": 4, "Octagon": 5, "Traced": 6}

SET_LABEL = {
    "Highway_Signs_US": "US Highway",
    "Highway_Signs_International": "Intl Highway",
    "Symbol_Signs_Recreational": "Recreational",
    "Symbol_Signs_Transportation_01": "Transportation 1",
    "Symbol_Signs_Transportation_02": "Transportation 2",
    "International_Icons_Electronic_Labeling": "Electronic",
}

# --- physical width, by MUTCD size class -------------------------------------
# Aspect is measured from pixels; absolute size never can be. The MUTCD tabulates a
# size PER SIGN PER CLASS rather than one multiplier, so the known rows are stated
# outright and everything else is derived from a documented ratio. The size_source
# column says which is which, so nobody mistakes a derived number for a specification.
#
# Widths in inches. Height comes from the measured aspect, not from here.
IN = 0.0254
CLASSES = ("minimum", "conventional", "expressway", "freeway", "oversized")

# Rows taken from the MUTCD size tables (2B regulatory, 2C warning, 2D guide).
# order: minimum, conventional, expressway, freeway, oversized
MUTCD = {
    "Stop":                 (24, 30, 36, 48, 36),   # R1-1
    "Yield":                (30, 36, 48, 60, 48),   # R1-2
    "DoNotEnter":           (24, 30, 36, 48, 36),   # R5-1
    "WrongWay":             (30, 36, 48, 48, 42),   # R5-1a
    "NoPassingZone":        (30, 36, 48, 48, 36),   # W14-3 pennant
    "SchoolCrossing":       (24, 30, 36, 36, 36),   # S1-1
    "SchoolCrossingWithCrosswalk": (24, 30, 36, 36, 36),
    "RailroadCrossbuck":    (48, 48, 48, 48, 48),   # R15-1, one fixed blade length
    "RailroadAdvanceWarning": (24, 36, 36, 48, 36), # W10-1
}

# Speed limit plates and the warning diamonds are the two big families; both follow a
# single row across all their variants.
SPEED_LIMIT = (18, 24, 36, 48, 30)     # R2-1
WARNING_DIAMOND = (24, 30, 36, 48, 36) # W series
ROUTE_SHIELD = (18, 24, 30, 36, 30)    # M1 series

# Everything with no tabulated row scales from its conventional size by these ratios.
DERIVED_RATIO = dict(minimum=0.8, conventional=1.0, expressway=1.2,
                     freeway=1.6, oversized=1.2)

# Non-roadway sets have no size class at all - a restroom pictogram has no freeway
# size - so every class is the same number and the source says so.
FLAT_SETS = {"Symbol_Signs_Recreational", "Symbol_Signs_Transportation_01",
             "Symbol_Signs_Transportation_02",
             "International_Icons_Electronic_Labeling"}

BASE_BY_SET = {
    "Highway_Signs_US": 30,
    "Highway_Signs_International": 24,
    "Symbol_Signs_Recreational": 18,
    "Symbol_Signs_Transportation_01": 12,
    "Symbol_Signs_Transportation_02": 12,
    "International_Icons_Electronic_Labeling": 4,
}


def widths_for(name, folder, shape):
    """Return (dict of class -> metres, source)."""
    if folder in FLAT_SETS:
        w = BASE_BY_SET.get(folder, 20) * IN
        return {c: round(w, 4) for c in CLASSES}, "not a roadway sign"

    row = MUTCD.get(name)
    src = "MUTCD"
    if row is None:
        if name.startswith("SpeedLimit"):
            row = SPEED_LIMIT
        elif shape == "Diamond" and folder == "Highway_Signs_US":
            row = WARNING_DIAMOND
        elif "Shield" in name or "Interstate" in name:
            row = ROUTE_SHIELD
    if row is None:
        base = BASE_BY_SET.get(folder, 24)
        return ({c: round(base * DERIVED_RATIO[c] * IN, 4) for c in CLASSES},
                "derived from set")
    return {c: round(v * IN, 4) for c, v in zip(CLASSES, row)}, src


NAME_RE = re.compile(r"^(?P<name>.+)_(?P<code>[Xx]\d{2}[A-Za-z]\d{2})\.png$")

rows = []
skipped = []
for r in csv.DictReader(open(MEASURED, encoding="utf-8")):
    m = NAME_RE.match(r["file"])
    if not m:
        skipped.append(r["file"])
        continue
    folder = r["folder"]
    shape = r["shape"]
    is_decal = (shape == "Pictogram")
    wd, wsrc = widths_for(m.group("name"), folder, shape)
    rows.append({
        "code": m.group("code"),
        "name": m.group("name"),
        "set": folder,
        "set_label": SET_LABEL.get(folder, folder),
        "shape": shape,
        # decals have no plate of their own; they sit on a Rectangle until told otherwise
        "shape_index": SHAPE_INDEX.get(shape, 0) if not is_decal else 0,
        "is_decal": int(is_decal),
        "aspect": r["aspect"],
        **{("width_" + c): wd[c] for c in CLASSES},
        "width": wd["conventional"],
        "size_source": wsrc,
        "u0": r["u0"], "v0": r["v0"], "u1": r["u1"], "v1": r["v1"],
        "texture": "%s/%s" % (folder, r["file"]),
    })

rows.sort(key=lambda x: (x["set"], x["name"]))
os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, "w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
    w.writeheader()
    w.writerows(rows)

print("rows written : %d -> %s" % (len(rows), OUT))
if skipped:
    print("UNPARSED     : %d %s" % (len(skipped), skipped[:5]))
print("decals       : %d" % sum(r["is_decal"] for r in rows))
print("traced       : %d" % sum(1 for r in rows if r["shape"] == "Traced"))
print()
print("%-42s %5s" % ("set", "count"))
for k, v in collections.Counter(r["set"] for r in rows).most_common():
    print("%-42s %5d" % (k, v))
