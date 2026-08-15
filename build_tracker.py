"""Build the AB standardization tracker as a single flat CSV for Google Sheets.

One row per decision or action, with a stable ID so we can refer to items by number.
Status / Decision / Notes are left blank for Jordan and Claude to fill in together.
"""
import json, os, csv, collections, re

HERE = os.path.dirname(os.path.abspath(__file__))
OUT  = os.path.join(HERE, "AB_Tracker.csv")

def load(n):
    p = os.path.join(HERE, n)
    return json.load(open(p, encoding="utf-8")) if os.path.isfile(p) else {}

graph  = load("opdef_graph.json")
nested = load("nested_versions.json")
auth   = load("authoritative_versions.json")
inv    = os.path.join(HERE, "ab_inventory.tsv")
cls    = os.path.join(HERE, "zone_classification.json")

rows = []
def add(area, sev, asset, item, detail, action, scriptable):
    rows.append({
        "ID": "", "Area": area, "Severity": sev, "Asset": asset, "Item": item,
        "Detail": detail, "Proposed Action": action, "Scriptable": scriptable,
        "Status": "", "Decision": "", "Notes": "",
    })

# ---- 1. IDENTITY: filename vs type mismatches, bad filenames ---------------
for m in auth.get("filename_type_mismatch", []):
    add("Identity", "HIGH", m["file"], m["type"],
        "Filename version/name does not match the type it defines",
        "Rename file to match type, or bump type to match file - decide which is canonical", "No")

# ---- 2. VERSIONS: stale + missing nested ------------------------------------
for parent, d in sorted(nested.get("results", {}).items()):
    for s in d.get("stale", []):
        add("Versions", "MED", parent, s["nested"],
            "Nested sub-asset pinned at an old version; newest is %s" % s["newest"],
            "Unlock parent, retype nested node, re-save definition", "Yes")
    for m in d.get("missing", []):
        add("Versions", "HIGH", parent, m,
            "Nested type does not exist on disk (renamed or deleted)",
            "Identify the replacement tool and repoint, or remove the node", "No")

# ---- 3. TEXTURES ------------------------------------------------------------
owned_by = graph.get("owner_of", {})
existing = set()
for a in graph.get("assets", {}):
    mm = re.match(r"^AB\.(.+?)\.\d+\.\d+\.hda$", a)
    if mm:
        existing.add(mm.group(1))

seen = set()
for a, d in sorted(graph.get("assets", {}).items()):
    own = set(d["owns"])
    for r in d["refs"]:
        owner, tex = r.split("?", 1)
        short = owner.rsplit("/", 1)[-1].split("::")[0]
        if short in existing:
            continue
        k = (a, tex)
        if k in seen:
            continue
        seen.add(k)
        if tex in own:
            where, sev, act = "self-owned", "MED", "Repoint to shared texture (extraction fixes automatically)"
        elif tex in owned_by:
            where, sev, act = "in sibling " + owned_by[tex][0], "MED", "Repoint to shared texture (extraction fixes automatically)"
        else:
            where, sev, act = "NOT IN LIBRARY", "HIGH", "Source or re-author this texture"
        add("Textures", sev, a, tex,
            "opdef: points at '%s' which no longer exists; file is %s" % (short, where), act, "Yes")

for t in sorted(graph.get("orphan_sections", [])):
    add("Textures", "LOW", ", ".join(owned_by.get(t, [])), t,
        "Embedded in %d asset(s) but referenced by nothing" % len(owned_by.get(t, [])),
        "Delete rather than extract", "Yes")

for t, v in sorted(graph.get("duplicated_sections", {}).items(), key=lambda kv: -len(kv[1])):
    add("Textures", "LOW", "%d assets" % len(v), t,
        "Same texture embedded %d times: %s" % (len(v), ", ".join(sorted(v)[:4])),
        "Extract once to U:/Textures/AB_Embedded/, repoint all", "Yes")

# ---- 4. INTERFACE (from the inventory tsv) ---------------------------------
if os.path.isfile(inv):
    latest = {}
    for r in csv.DictReader(open(inv, encoding="utf-8"), delimiter="\t"):
        b = r["base"]
        if b not in latest or r["version"] > latest[b]["version"]:
            latest[b] = r
    for b, r in sorted(latest.items()):
        if r["std_missing"] and int(r["std_hits"]) == 0:
            add("Interface", "MED", os.path.basename(r["path"]), "no standard parms",
                "Tool exposes none of the 8 standard interface parameters",
                "Assign a tier, then inject the parms that tier requires", "Partial")
        if r["stock_icon"] == "1":
            add("Presentation", "LOW", os.path.basename(r["path"]), "stock icon",
                "Uses the default SOP_subnet icon", "Install the existing SVG from IconDev/Icons", "Yes")
        if r["has_help"] == "0":
            add("Presentation", "MED", os.path.basename(r["path"]), "no Help section",
                "Asset ships with no documentation", "Write a Help section", "No")

# ---- number and write -------------------------------------------------------
order = {"HIGH": 0, "MED": 1, "LOW": 2}
rows.sort(key=lambda r: (order.get(r["Severity"], 3), r["Area"], r["Asset"]))
for i, r in enumerate(rows, start=1):
    r["ID"] = "AB-%03d" % i

cols = ["ID", "Area", "Severity", "Asset", "Item", "Detail",
        "Proposed Action", "Scriptable", "Status", "Decision", "Notes"]
with open(OUT, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=cols)
    w.writeheader()
    w.writerows(rows)

print("wrote", OUT, "(%d rows)" % len(rows))
print()
print("by area:")
for a, c in collections.Counter(r["Area"] for r in rows).most_common():
    print("   %-14s %4d" % (a, c))
print("by severity:")
for s, c in collections.Counter(r["Severity"] for r in rows).most_common():
    print("   %-14s %4d" % (s, c))
print("scriptable:")
for s, c in collections.Counter(r["Scriptable"] for r in rows).most_common():
    print("   %-14s %4d" % (s, c))
print("bytes:", os.path.getsize(OUT))
