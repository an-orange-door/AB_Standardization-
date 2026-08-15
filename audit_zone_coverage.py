"""Which AB tools emit s@name zones, and which do not.

    hython U:/AB_Standardization/audit_zone_coverage.py

RUN WITH THE HOUDINI GUI CLOSED - it instantiates and cooks every tool, and
there is one FX seat.

Why this is the gating audit: MaterialStyle cannot be fixed automatically on a
tool that emits no zones. AB::MaterialBinding keys off s@name to derive
s@ab_zone and s@ab_material, and AB::MaterialLibrary builds a shader per bound
zone. No zones -> nothing to bind -> no Principled branch can be generated. So
zone coverage, not MaterialStyle, is the real release blocker.

Measured by COOKING each tool at its defaults and reading the prim attribute.
Static analysis would be cheaper and wrong: a tool can contain a name node on a
branch that never reaches the output.

Only the LATEST version of each tool is audited - Jordan, 2026-08-14.

Zone names are checked against config/zone_vocabulary.json, because a zone name
becomes a USD prim name and an Unreal component name, so a non-canonical one is
a breaking change waiting to happen. Numbered variants (SignFront_0) are
packing keys, not zones, and are reported separately.

Output: U:/AB_Standardization/zone_coverage.csv  - import into Sheets, fill in
Status/Owner/Notes, and I can read the columns back.
"""
import csv
import json
import os
import re
import sys
import traceback

import hou

LIB = "U:/Git/AssetBashTools"
OUT = "U:/AB_Standardization/zone_coverage.csv"
VOCAB = os.path.join(LIB, "config/zone_vocabulary.json")
VER = re.compile(r"^(.*)::(\d+)\.(\d+)$")


def install_library():
    n = 0
    for root, dirs, files in os.walk(LIB):
        r = root.replace("\\", "/") + "/"
        if any(s in r for s in ("/backup/", "/OLD/", "/old/", "/_Archive/", "/.git")):
            continue
        for f in sorted(files):
            if f.lower().endswith((".hda", ".otl")):
                try:
                    hou.hda.installFile(os.path.join(root, f))
                    n += 1
                except Exception:
                    pass
    return n


def latest_types():
    best = {}
    for name, nt in hou.sopNodeTypeCategory().nodeTypes().items():
        if not name.startswith("AB"):
            continue
        d = nt.definition()
        if d is None:
            continue
        p = d.libraryFilePath().replace("\\", "/")
        if "/AssetBashTools/" not in p:
            continue
        m = VER.match(name)
        key, ver = (m.group(1), (int(m.group(2)), int(m.group(3)))) if m else (name, (0, 0))
        if key not in best or ver > best[key][0]:
            best[key] = (ver, name, d)
    return sorted((n, d) for _, n, d in best.values())


def main():
    print("installed %d files" % install_library())
    vocab = json.load(open(VOCAB))
    canon = set(vocab["canonical"])
    aliases = vocab.get("aliases", {})
    ignore = [re.compile(p) for p in vocab.get("ignore_patterns", [])]

    types = latest_types()
    print("latest-version AB tools: %d\n" % len(types))

    rows = []
    holder = hou.node("/obj").createNode("geo", "ZoneAudit")
    try:
        for i, (name, defn) in enumerate(types, 1):
            path = defn.libraryFilePath().replace("\\", "/")
            rel = path.split("/AssetBashTools/")[-1]
            cat = rel.split("/")[1] if rel.count("/") >= 1 else ""
            label = defn.description() or ""
            zones, status, note = [], "", ""
            try:
                node = holder.createNode(name, "z")
                try:
                    node.cook(force=True)
                    g = node.geometry()
                    if g.findPrimAttrib("name"):
                        zones = sorted({p.attribValue("name") for p in g.prims()
                                        if p.attribValue("name")})
                    prims = len(g.prims())
                    status = "OK"
                except hou.Error as e:
                    prims = -1
                    status = "COOK ERROR"
                    note = str(e).replace("\n", " ")[:120]
                node.destroy()
            except Exception as e:
                prims = -1
                status = "CREATE ERROR"
                note = str(e)[:120]

            real = [z for z in zones if not any(rx.match(z) for rx in ignore)]
            noncanon = [z for z in real if z not in canon and z not in aliases]
            has = "YES" if real else "NO"

            rows.append({
                "Tool": name,
                "Label": label,
                "Category": cat,
                "File": rel,
                "Cook": status,
                "Prims": prims,
                "HasZones": has,
                "ZoneCount": len(real),
                "Zones": " ".join(real[:40]),
                "NonCanonical": " ".join(noncanon),
                "PackingKeysIgnored": len(zones) - len(real),
                "Status": "",
                "Owner": "",
                "Notes": note,
            })
            print("[%3d/%d] %-44s %-12s zones=%-3d %s"
                  % (i, len(types), name, status, len(real),
                     ("NON-CANON: " + " ".join(noncanon[:4])) if noncanon else ""))
            sys.stdout.flush()
    finally:
        holder.destroy()

    cols = ["Tool", "Label", "Category", "File", "Cook", "Prims", "HasZones",
            "ZoneCount", "Zones", "NonCanonical", "PackingKeysIgnored",
            "Status", "Owner", "Notes"]
    with open(OUT, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)

    no = [r for r in rows if r["HasZones"] == "NO" and r["Cook"] == "OK"]
    bad = [r for r in rows if r["NonCanonical"]]
    err = [r for r in rows if r["Cook"] != "OK"]
    print("")
    print("=" * 72)
    print("tools audited        : %d" % len(rows))
    print("NO ZONES (to fix)    : %d" % len(no))
    print("non-canonical zones  : %d" % len(bad))
    print("cook/create errors   : %d" % len(err))
    print("")
    print("wrote %s" % OUT)


if __name__ == "__main__":
    main()
