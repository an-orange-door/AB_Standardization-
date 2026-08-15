"""Merge the per-sheet name CSVs into one rename manifest and validate it.

Checks that every file on disk got a name, that no name was invented for a file
that does not exist, and that the new names are unique within their folder.
"""
import os, csv, glob, collections, json

ROOT = r"U:/Textures/SignsSymbols"
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "SignsSymbols_rename_manifest.csv")

SETS = {
    "X01": "Highway_Signs_US",
    "X02": "Highway_Signs_International",
    "X03": "Symbol_Signs_Recreational",
    "X04": "Symbol_Signs_Transportation_01",
    "X05": "Symbol_Signs_Transportation_02",
    "X06": "International_Icons_Electronic_Labeling",
}

# ---- what is actually on disk -------------------------------------------
disk = {}
for dp, dn, fn in os.walk(ROOT):
    rel = os.path.relpath(dp, ROOT).replace(os.sep, "/")
    for f in fn:
        if f.lower().endswith(".png"):
            disk[os.path.splitext(f)[0]] = (rel, f)

# ---- what we named -------------------------------------------------------
named, dupe_codes = {}, []
for p in sorted(glob.glob(os.path.join(HERE, "names_*.csv"))):
    for row in csv.DictReader(open(p, encoding="utf-8")):
        code = row["code"].strip()
        if code in named:
            dupe_codes.append(code)
        named[code] = (row["name"].strip(), row["confidence"].strip())

print("files on disk : %d" % len(disk))
print("codes named   : %d" % len(named))

missing = sorted(set(disk) - set(named))
extra = sorted(set(named) - set(disk))
print("UNNAMED files : %d %s" % (len(missing), missing[:12]))
print("names with no file: %d %s" % (len(extra), extra[:12]))
if dupe_codes:
    print("DUPLICATE code rows: %s" % sorted(set(dupe_codes))[:12])

# ---- collisions: same new name twice inside one folder -------------------
byfolder = collections.defaultdict(collections.Counter)
for code, (name, conf) in named.items():
    if code in disk:
        byfolder[disk[code][0]][name] += 1
collisions = {d: [n for n, c in cnt.items() if c > 1] for d, cnt in byfolder.items()}
collisions = {d: v for d, v in collisions.items() if v}
print("\nname collisions within a folder:")
for d, v in collisions.items():
    print("  %-42s %s" % (d, v))
if not collisions:
    print("  none")

# ---- write the manifest --------------------------------------------------
rows = []
for code in sorted(disk):
    folder, oldfile = disk[code]
    name, conf = named.get(code, ("UNNAMED", "none"))
    rows.append({
        "folder": folder,
        "old_name": oldfile,
        # code uppercased: 38 files ship as x01h*/x01i* and lowercase breaks
        # both the PascalCase standard and case-sensitive USD/Linux paths
        "new_name": "%s_%s.png" % (name, code.upper()),
        "descriptive_name": name,
        "code": code,
        "set": SETS.get(code[:3].upper(), "?"),   # x01h* files are lowercase
        "confidence": conf,
    })

with open(OUT, "w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
    w.writeheader()
    w.writerows(rows)

# the code suffix is what guarantees the FILENAME stays unique even where two
# different signs earned the same descriptive name
seen = collections.Counter((r["folder"], r["new_name"]) for r in rows)
clash = [k for k, v in seen.items() if v > 1]
print("\nduplicate FINAL FILENAMES: %d %s" % (len(clash), clash[:5]))

bad = [r["new_name"] for r in rows if not r["new_name"][0].isupper()]
print("names not starting uppercase: %d %s" % (len(bad), bad[:5]))

conf = collections.Counter(r["confidence"] for r in rows)
print("\nconfidence: %s" % dict(conf))
print("rows written: %d -> %s" % (len(rows), OUT))

# per-set confidence, so the weak areas are visible
per = collections.defaultdict(collections.Counter)
for r in rows:
    per[r["set"]][r["confidence"]] += 1
print("\n%-42s %5s %6s %6s %5s" % ("set", "high", "medium", "low", "tot"))
for s, c in sorted(per.items()):
    print("%-42s %5d %6d %6d %5d" % (s, c["high"], c["medium"], c["low"], sum(c.values())))
