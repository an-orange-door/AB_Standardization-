"""Build AB_Assets.csv - one row per TOOL, carrying its release state.

This is a different table from AB_Tracker.csv:
  AB_Tracker.csv  = one row per defect,  'Status' tracks the fix
  AB_Assets.csv   = one row per tool,    'State'  tracks release readiness

The State column is the source of truth for the release branch: a script filters
State == Shippable and writes an orphan branch. It is also the skip-list for bulk
jobs - never spend effort on a tool marked Dev or Deprecated.
"""
import os, re, csv, json, collections

ROOT = r"U:/Git/AssetBashTools/Sops"
HERE = os.path.dirname(os.path.abspath(__file__))
OUT  = os.path.join(HERE, "AB_Assets.csv")

STATES = ["Dev", "Standardizing", "Review", "Shippable", "Deprecated"]

fr = re.compile(r"^AB\.(.+?)\.(\d+)\.(\d+)\.hda$")


def load(n):
    p = os.path.join(HERE, n)
    return json.load(open(p, encoding="utf-8")) if os.path.isfile(p) else {}


nested = load("nested_versions.json")
auth   = load("authoritative_versions.json")
graph  = load("opdef_graph.json")

# ---- walk the library ------------------------------------------------------
tools = collections.defaultdict(list)
for dp, dn, fn in os.walk(ROOT):
    if "backup" in dp.lower().replace("\\", "/"):
        continue
    for f in fn:
        if not f.lower().endswith(".hda"):
            continue
        m = fr.match(f)
        if not m:
            tools.setdefault("_UNPARSEABLE_" + f, []).append(
                (0, 0, os.path.join(dp, f).replace("\\", "/")))
            continue
        tools[m.group(1)].append(
            (int(m.group(2)), int(m.group(3)), os.path.join(dp, f).replace("\\", "/")))

# ---- defect counts per tool, from the audits -------------------------------
defects = collections.Counter()
notes   = collections.defaultdict(list)

for m in auth.get("filename_type_mismatch", []):
    mm = fr.match(os.path.basename(m["file"]))
    t = mm.group(1) if mm else m["file"]
    defects[t] += 1
    notes[t].append("filename/type mismatch (%s)" % m["type"])

for parent, d in nested.get("results", {}).items():
    t = parent.split("::")[1]
    for s in d.get("stale", []):
        defects[t] += 1
        notes[t].append("stale nested %s" % s["nested"])
    for miss in d.get("missing", []):
        defects[t] += 1
        notes[t].append("MISSING nested %s" % miss)

# ---- inventory (icons / help / std parms) ----------------------------------
inv = {}
p = os.path.join(HERE, "ab_inventory.tsv")
if os.path.isfile(p):
    for r in csv.DictReader(open(p, encoding="utf-8"), delimiter="\t"):
        b = r["base"]
        if b not in inv or (r["version"] > inv[b]["version"]):
            inv[b] = r

# ---- textures embedded per tool --------------------------------------------
embeds = collections.Counter()
for a, d in graph.get("assets", {}).items():
    mm = fr.match(a)
    if mm:
        embeds[mm.group(1)] += len(d.get("owns", []))


def vkey(v):
    return (v[0], v[1])


rows = []
for t in sorted(tools):
    vs = sorted(tools[t], key=vkey)
    newest = vs[-1]
    cat = os.path.dirname(newest[2]).replace("\\", "/").split("/Sops/")[-1]
    mb = sum(os.path.getsize(x[2]) for x in vs) / 1e6
    i = inv.get(t, {})

    # a proposed starting state - Jordan overrides in the sheet
    if defects[t] >= 1 and any("MISSING" in n for n in notes[t]):
        state = "Dev"
    elif len(vs) > 4:
        state = "Dev"
    else:
        state = "Standardizing"

    rows.append({
        "Tool": t,
        "State": state,
        "Category": cat,
        "Versions": len(vs),
        "Shipping Version": "%d.%d" % (newest[0], newest[1]),
        "All Versions": " ".join("%d.%d" % (a, b) for a, b, _ in vs),
        "Size MB": round(mb, 1),
        "Embedded Textures": embeds.get(t, 0),
        "Std Parms": i.get("std_hits", ""),
        "Stock Icon": "yes" if i.get("stock_icon") == "1" else "",
        "Has Help": "" if i.get("has_help") == "0" else "yes",
        "Defects": defects[t],
        "Defect Notes": "; ".join(notes[t][:3]),
        "Owner": "",
        "Notes": "",
    })

cols = ["Tool", "State", "Category", "Versions", "Shipping Version", "All Versions",
        "Size MB", "Embedded Textures", "Std Parms", "Stock Icon", "Has Help",
        "Defects", "Defect Notes", "Owner", "Notes"]

with open(OUT, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=cols)
    w.writeheader()
    w.writerows(rows)

print("wrote", OUT, "(%d tools)" % len(rows))
print()
print("proposed starting state:")
for s, c in collections.Counter(r["State"] for r in rows).most_common():
    print("   %-16s %4d" % (s, c))
print()
print("tools with more than 2 versions (sprawl):")
for r in sorted(rows, key=lambda r: -r["Versions"])[:12]:
    if r["Versions"] > 2:
        print("   %-34s %2d versions  %6.1f MB  %s" %
              (r["Tool"], r["Versions"], r["Size MB"], r["Category"]))
print()
print("largest tools on disk:")
for r in sorted(rows, key=lambda r: -r["Size MB"])[:10]:
    print("   %-34s %8.1f MB  %d embedded textures" %
          (r["Tool"], r["Size MB"], r["Embedded Textures"]))
print()
print("total library size: %.1f MB" % sum(r["Size MB"] for r in rows))
print("STATES for the dropdown:", " / ".join(STATES))
