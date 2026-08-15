"""Generate AB config/zone_vocabulary.json + config/material_bindings.json.

Sources, all real data - nothing hand-typed:
  * W:/HoudiniMCP/data/ab_name_attributes.csv   library-wide s@name values (June audit)
  * today's verified cooked zones from the six building tools
  * G:/.../PolyHaven_Derived/PolyHaven_materials.json   CC0 material index

Writes into U:/Git/AssetBashTools/config/ .
"""
import csv, json, os, re, collections

NAMECSV  = r"W:/HoudiniMCP/data/ab_name_attributes.csv"
PHJSON   = r"G:/SC_UXO_SyntheticData/Assets/Textures/PolyHaven_Derived/PolyHaven_materials.json"
OUTDIR   = r"U:/Git/AssetBashTools/config"

# --- canonical synonym map (Jordan-ruled 2026-08-13) -----------------------
ALIASES = {
    "RoofPlane": "Roof", "BuildingRoof": "Roof",
    "RoofParapet": "Parapet",
    "BuildingWalls": "Walls",
    "WindowWall": "WindowWalls",
    "GuardRail": "Railing", "FrontFence": "Railing",
    "WinCasement": "WindowCasement",
    "WindowsLit": "WindowGlass", "WindowsUnlit": "WindowGlass",
    "WindowGlassLit": "WindowGlass", "WindowPlanes": "WindowGlass",
    # case-divergent duplicate found in the June audit
    "BackPlate": "Backplate",
}

# names that are packing keys, not shading zones -- these must NOT be governed
IGNORE_PATTERNS = [
    r"^piece\d+$",          # CityGridGenerator: 200 of them
    r"^\d",                 # leading digit: illegal as a USD prim name anyway
]

# zones verified today from cooked output of the six building tools
VERIFIED = ["Backplate", "BuildingTrim", "Corners", "DoorFrame", "DoorGlass",
            "LightBase", "LightEmit", "LightMetal", "Parapet", "PullBar",
            "Railing", "Roof", "TF_Cornice", "Trim", "Underside", "Walls",
            "WindowCasement", "WindowFrame", "WindowGlass", "WindowSill",
            "WindowTrim", "WindowTrimLower", "WindowTrimSides",
            "WindowTrimTop_01", "WindowWalls"]

ILLEGAL = ("/", chr(92), " ")


def sanitise(z):
    for ch in ILLEGAL:
        z = z.replace(ch, "_")
    return z.strip("_")


def ignored(z):
    return KIND.get(z, "SHADING") == "PACKING"


# ---------------------------------------------------------------- zones ----
counts = collections.Counter()
rows = list(csv.DictReader(open(NAMECSV, encoding="utf-8-sig")))
for r in rows:
    for v in re.split(r"[;,|]", r.get("name_values") or ""):
        v = v.strip()
        if v:
            counts[v] += 1

# single source of truth: the ruled classification from classify_zones.py
CLS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "zone_classification.tsv")
KIND, FAMOF = {}, {}
for r in csv.DictReader(open(CLS, encoding="utf-8"), delimiter="	"):
    KIND[r["zone"]] = r["kind"]
    FAMOF[r["zone"]] = r["family"]

canonical, aliases, ignored_out, needs_fix = {}, dict(ALIASES), [], []
for z, n in counts.items():
    if ignored(z):
        ignored_out.append(z)
        continue
    s = sanitise(z)
    if s != z:
        needs_fix.append({"found": z, "sanitised": s, "reason": "illegal character"})
        z = s
    z = ALIASES.get(z, z)
    canonical[z] = canonical.get(z, 0) + n
for z in VERIFIED:
    canonical.setdefault(z, 0)

vocab = {
    "version": "1.0",
    "namespace": "AB",
    "description": "Governed s@ab_zone vocabulary. A zone name becomes a USD prim name and "
                   "an Unreal component name, so changes are breaking after release.",
    "rules": [
        "One name per concept - synonyms resolve through aliases.",
        "State (lit/unlit/variant) never appears in a zone name; it belongs in per-instance data.",
        "No empty zone names - an unnamed prim cannot be material-bound.",
        "PascalCase; every underscore-separated segment starts capitalised.",
        "Characters illegal in USD prim names or Unreal component names are rejected."
    ],
    "canonical": sorted(canonical),
    "aliases": dict(sorted(aliases.items())),
    "ignore_patterns": IGNORE_PATTERNS,
    "ignored_examples": sorted(ignored_out)[:5],
    "needs_fix": needs_fix,
    "stats": {
        "tools_audited": len(rows),
        "tools_with_zones": sum(1 for r in rows if (r.get("name_values") or "").strip()),
        "raw_distinct_values": len(counts),
        "ignored_as_packing_keys": len(ignored_out),
        "canonical_zones": len(canonical),
    },
}

# ------------------------------------------------------------- bindings ----
ph = json.load(open(PHJSON))
ph_by_name = {m["name"]: m for m in ph["materials"]}

# keyword -> preferred PolyHaven material, matched against the CC0 index
PREFER = {
    "Walls": ["concrete", "plaster", "brick"],
    "Corners": ["concrete", "brick"],
    "Trim": ["wood", "plaster"],
    "BuildingTrim": ["wood", "plaster"],
    "TF_Cornice": ["concrete", "plaster"],
    "Roof": ["roof", "tile"],
    "Parapet": ["concrete"],
    "WindowSill": ["concrete", "stone"],
    "WindowFrame": ["wood", "metal"],
    "WindowCasement": ["wood", "metal"],
    "WindowTrim": ["wood"],
    "WindowWalls": ["concrete", "brick"],
    "DoorFrame": ["wood"],
    "Railing": ["metal"],
    "PullBar": ["metal"],
    "Backplate": ["metal"],
    "LightMetal": ["metal"],
    "LightBase": ["metal"],
    "HW_Bolt": ["metal"], "HW_Nut": ["metal"], "HW_Washer": ["metal"],
}
SHADER_ZONES = {"WindowGlass", "DoorGlass", "LightEmit"}   # shader, not a scanned texture


def pick(zone):
    for kw in PREFER.get(zone, []):
        for name in sorted(ph_by_name):
            if kw in name:
                return ph_by_name[name]
    return None


bindings = {}
for z in sorted(canonical):
    if z in SHADER_ZONES:
        bindings[z] = {"note": "authored shader, not a scanned material",
                       "houdini": "", "usd": "", "unreal": ""}
        continue
    m = pick(z)
    bindings[z] = {
        "houdini": m["path"] if m else "",
        "usd": m["path"] if m else "",
        "unreal": "",
        "source": m["name"] if m else "",
        "license": "CC0" if m else "",
    }

bind = {
    "version": "1.0",
    "namespace": "AB",
    "description": "Zone -> material target per backend. Paths may use $POLYHAVEN_DERIVED or "
                   "$AB_CONTENT_ROOT. A per-project override file layers on top of this.",
    "license_policy": "Shipped bindings must be CC0 (PolyHaven) or authored in-house. "
                      "Megascans-derived content is never redistributable.",
    "bindings": bindings,
    "stats": {
        "zones": len(bindings),
        "auto_bound_cc0": sum(1 for v in bindings.values() if v.get("source")),
        "shader_zones": len(SHADER_ZONES),
        "unbound": sum(1 for v in bindings.values()
                       if not v.get("source") and "note" not in v),
    },
}

os.makedirs(OUTDIR, exist_ok=True)
for fn, data in (("zone_vocabulary.json", vocab), ("material_bindings.json", bind)):
    p = os.path.join(OUTDIR, fn)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    print("wrote", p, "(%d bytes)" % os.path.getsize(p))

print()
print("VOCABULARY :", json.dumps(vocab["stats"], indent=2))
print("BINDINGS   :", json.dumps(bind["stats"], indent=2))
print()
print("needs_fix  :", json.dumps(vocab["needs_fix"], indent=1))
print("unbound zones:", [z for z, v in bindings.items()
                         if not v.get("source") and "note" not in v][:25])
