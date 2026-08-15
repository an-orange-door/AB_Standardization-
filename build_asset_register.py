"""One review sheet covering BOTH the version collapse and the icon install.

Output: U:/AB_Standardization/AB_Assets.csv - one row per FILE, grouped by tool.

Per tool it answers: which version ships, which files are superseded and can leave
the scan path, whether the filename version agrees with the type the file actually
defines, and which icon SVG it should get.

Houdini's icon convention for type AB::Foo is SOP_AB__Foo.svg - the namespace colons
become a double underscore. That makes icon matching mechanical rather than a guess,
and anything that does NOT match exactly is reported rather than fuzzy-matched into
place, because a wrong icon is worse than a missing one.

The shipping version is chosen by NUMERIC comparison of the type version, so 4.10
correctly beats 4.9, and the type is read from the file rather than trusted from the
filename - those disagree in a dozen assets.
"""
import os, re, csv, subprocess, collections

ROOT  = "U:/Git/AssetBashTools/Sops"
ICONS = "U:/Git/AssetBashTools/IconDev/Icons"
HOTL  = "C:/Program Files/Side Effects Software/Houdini 22.0.368/bin/hotl.exe"
OUT   = "U:/AB_Standardization/AB_Assets.csv"

FNAME = re.compile(r"^(?:sop_)?AB\.+(?P<tool>.+?)\.(?P<maj>\d+)\.(?P<min>\d+)\.hda$", re.I)


def type_of(path):
    """The type a file actually defines - authoritative, unlike the filename."""
    try:
        r = subprocess.run([HOTL, "-V", path], capture_output=True, text=True, timeout=120)
    except Exception:
        return None
    m = re.search(r"^Operator:\s+(\S+)", r.stdout, re.M)
    return m.group(1) if m else None


# ---- Jordan's icon spec, read straight out of the generator -----------------
# IconDev/generate_icons.py holds TOOL_MAP: tool -> (motif fn, palette, variant,
# category), grouped by "# City / Urban" style comments. That IS the icon design
# note, so it is surfaced here rather than restated somewhere it can drift.
GEN = "U:/Git/AssetBashTools/IconDev/generate_icons.py"
SPEC_RE = re.compile(
    r"^\s*'(?P<name>[^']+)'\s*:\s*\(\s*(?P<fn>\w+)\s*,\s*'(?P<pal>[^']*)'\s*,"
    r"\s*(?P<var>\d+)\s*,\s*'(?P<cat>[^']*)'\s*\)")
GROUP_RE = re.compile(r"^\s*#\s*(?P<g>[A-Za-z][\w /&-]*)\s*$")

spec, group = {}, ""
try:
    inmap = False
    for line in open(GEN, encoding="utf-8"):
        if line.startswith("TOOL_MAP"):
            inmap = True
            continue
        if inmap and line.startswith("}"):
            break
        if not inmap:
            continue
        g = GROUP_RE.match(line)
        if g:
            group = g.group("g").strip()
            continue
        m2 = SPEC_RE.match(line)
        if m2:
            spec[m2.group("name").lower()] = {
                "motif": m2.group("fn")[2:] if m2.group("fn").startswith("m_") else m2.group("fn"),
                "palette": m2.group("pal"),
                "variant": m2.group("var"),
                "group": group,
            }
except Exception as e:
    print("could not read icon spec:", e)
print("icon spec entries: %d" % len(spec))

# ---- notes typed into the previous sheet, preserved --------------------------
# Regenerating must never wipe a decision someone typed in. Keyed on File, which
# is stable even when a tool is renamed.
prev = {}
if os.path.exists(OUT):
    for r in csv.DictReader(open(OUT, encoding="utf-8")):
        prev[r.get("File", "")] = {"Notes": r.get("Notes", ""),
                                   "Decision": r.get("Decision", "")}
print("notes carried forward: %d" % sum(1 for v in prev.values()
                                        if v["Notes"] or v["Decision"]))

icons = {}
for f in sorted(os.listdir(ICONS)):
    if not f.lower().endswith(".svg"):
        continue
    stem = os.path.splitext(f)[0]
    for prefix in ("SOP_AB__", "HDA_", ""):
        if stem.startswith(prefix):
            icons[stem[len(prefix):].lower()] = f
            break

files = []
for dp, dn, fn in os.walk(ROOT):
    if "backup" in dp.lower().replace("\\", "/"):
        continue
    for f in sorted(fn):
        if f.lower().endswith(".hda"):
            files.append(os.path.join(dp, f).replace("\\", "/"))

rows = []
for i, p in enumerate(files):
    f = os.path.basename(p)
    m = FNAME.match(f)
    tname = type_of(p)
    tool_from_type = ver_from_type = ""
    if tname:
        parts = tname.split("::")
        tool_from_type = parts[1] if len(parts) > 2 else (parts[0] if len(parts) == 1 else parts[-2])
        ver_from_type = parts[-1] if len(parts) > 1 else ""
    tool = tool_from_type or (m.group("tool") if m else os.path.splitext(f)[0])
    ver_from_file = "%s.%s" % (m.group("maj"), m.group("min")) if m else ""
    rows.append({
        "Tool": tool,
        "File": os.path.relpath(p, "U:/Git/AssetBashTools").replace("\\", "/"),
        "TypeName": tname or "",
        "VersionInFilename": ver_from_file,
        "VersionInType": ver_from_type,
        "SizeMB": round(os.path.getsize(p) / 1e6, 2),
        "_v": tuple(int(x) for x in re.findall(r"\d+", ver_from_type or ver_from_file or "0")),
    })
    if i % 40 == 0:
        print("  %d/%d" % (i, len(files)))

by_tool = collections.defaultdict(list)
for r in rows:
    by_tool[r["Tool"]].append(r)

for tool, group in by_tool.items():
    group.sort(key=lambda r: r["_v"])
    newest = group[-1]
    icon = icons.get(tool.lower(), "")
    for r in group:
        r["VersionsOnDisk"] = len(group)
        r["Ships"] = "SHIP" if r is newest else "superseded"
        r["FilenameTypeMismatch"] = (
            "MISMATCH" if r["VersionInFilename"] and r["VersionInType"]
            and r["VersionInFilename"] != r["VersionInType"] else "")
        r["Icon"] = icon
        sp = spec.get(tool.lower(), {})
        r["IconGroup"] = sp.get("group", "")
        r["IconMotif"] = sp.get("motif", "")
        r["IconPalette"] = sp.get("palette", "")
        if r is not newest:
            r["IconStatus"] = ""
        elif icon and sp:
            r["IconStatus"] = "ok"
        elif icon and not sp:
            r["IconStatus"] = "no spec"        # svg exists, not in TOOL_MAP
        elif sp and not icon:
            r["IconStatus"] = "spec, not generated"
        else:
            r["IconStatus"] = "MISSING"
        r["ArchiveMB"] = 0 if r is newest else r["SizeMB"]
        carried = prev.get(r["File"], {})
        r["Notes"] = carried.get("Notes", "")
        r["Decision"] = carried.get("Decision", "")

for r in rows:
    r.pop("_v")

rows.sort(key=lambda r: (r["Tool"].lower(), r["VersionInType"] or r["VersionInFilename"]))
cols = ["Tool", "Ships", "VersionsOnDisk", "File", "TypeName", "VersionInFilename",
        "VersionInType", "FilenameTypeMismatch",
        "Icon", "IconStatus", "IconGroup", "IconMotif", "IconPalette",
        "SizeMB", "ArchiveMB", "Notes", "Decision"]
with open(OUT, "w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=cols)
    w.writeheader()
    w.writerows(rows)

ship = [r for r in rows if r["Ships"] == "SHIP"]
sup = [r for r in rows if r["Ships"] != "SHIP"]
print()
print("files                  : %d" % len(rows))
print("tools                  : %d" % len(by_tool))
print("shipping               : %d" % len(ship))
print("superseded             : %d   (%.0f MB leaves the scan path)"
      % (len(sup), sum(r["ArchiveMB"] for r in sup)))
print("filename/type mismatch : %d" % sum(1 for r in rows if r["FilenameTypeMismatch"]))
print("icons matched          : %d of %d shipping tools" % (
    sum(1 for r in ship if r["Icon"]), len(ship)))
print("icons MISSING          : %d" % sum(1 for r in ship if not r["Icon"]))
print("icons unused           : %d" % (len(icons) - len({r["Icon"] for r in ship if r["Icon"]})))
print()
print("worst version sprawl:")
for tool, group in sorted(by_tool.items(), key=lambda kv: -len(kv[1]))[:10]:
    print("   %-34s %2d versions" % (tool, len(group)))
print("\nwritten:", OUT)
