"""Measure the icon situation BEFORE changing anything.

Standing lesson from the MaterialStyle migration: baseline first, then change.
Reports which of the 155 latest-version tools have an icon, which have a
matching file in IconDev/Icons, and which are unmatched in either direction.
Writes nothing to any .hda.
"""
import csv, os, re, collections, hou

LIB = "U:/Git/AssetBashTools"
ICONS = LIB + "/IconDev/Icons"
OUT = "U:/AB_Standardization/icon_audit.csv"

for root, dirs, files in os.walk(LIB):
    r = root.replace("\\", "/") + "/"
    if any(s in r for s in ("/backup/", "/OLD/", "/_Archive/", "/.git")):
        continue
    for f in sorted(files):
        if f.lower().endswith((".hda", ".otl")):
            try: hou.hda.installFile(os.path.join(root, f))
            except Exception: pass

# icon files, keyed by the tool name they encode: SOP_AB__<Name>.svg
icon_by_name = {}
for f in sorted(os.listdir(ICONS)):
    if not f.lower().endswith(".svg"):
        continue
    m = re.match(r"^SOP_AB__(.+)\.svg$", f)
    if m:
        icon_by_name[m.group(1)] = f
    else:
        icon_by_name.setdefault("_OTHER_" + f, f)

best = {}
for cat in (hou.sopNodeTypeCategory(), hou.objNodeTypeCategory()):
    for tn, nt in cat.nodeTypes().items():
        d = nt.definition()
        if d is None: continue
        if not (d.libraryFilePath() or "").replace("\\","/").lower().startswith(LIB.lower()):
            continue
        c = nt.nameComponents(); key = (c[1], c[2]); v = c[3] or "0"
        vk = tuple(int(x) if x.isdigit() else 0 for x in str(v).split("."))
        if key not in best or vk > best[key][0]:
            best[key] = (vk, nt, d)

rows = []
stat = collections.Counter()
for (ns, name), (vk, nt, d) in sorted(best.items()):
    icon = d.icon() or ""
    sections = list(d.sections().keys())
    embedded = [s for s in sections if "icon" in s.lower()]
    match = icon_by_name.get(name, "")
    # a stock icon means Houdini fell back; anything under IconDev means it is ours
    is_stock = (not icon) or icon.startswith("SOP_") and "AB__" not in icon
    state = ("has-custom" if (embedded or (icon and "AB__" in icon))
             else ("stock" if is_stock else "other"))
    stat[state] += 1
    if not match: stat["NO-ICON-FILE"] += 1
    rows.append([nt.name(), name, d.libraryFilePath().replace("\\","/").replace(LIB+"/",""),
                 icon, ";".join(embedded), match, state])

with open(OUT, "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["type","name","file","icon_property","embedded_sections",
                "matching_icon_file","state"])
    w.writerows(rows)

print("latest-version tools : %d" % len(rows))
for k, v in stat.most_common():
    print("   %-16s %d" % (k, v))
used = {r[5] for r in rows if r[5]}
print("\nicon files           : %d" % len(icon_by_name))
print("   matched to a tool : %d" % len(used))
orphan = sorted(set(icon_by_name) - used - {k for k in icon_by_name if k.startswith("_OTHER_")})
print("   NO matching tool  : %d" % len(orphan))
for o in orphan[:20]: print("      %s" % o)
noicon = [r[1] for r in rows if not r[5]]
print("\ntools with NO icon file : %d" % len(noicon))
for n in noicon[:25]: print("      %s" % n)
print("\nwrote %s" % OUT)
