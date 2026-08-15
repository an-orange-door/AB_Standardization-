"""Rebuild config/material_bindings.json around the PolyHaven folder convention.

A zone binds to a MATERIAL NAME, not to six texture paths. Each backend generator
resolves the maps itself from the known layout:

    $AB_TEXTURES/PolyHaven_Derived/<name>/Images/<name>_BaseColor_4k.png
                                                 <name>_ARM_4k.png      (AO/Rough/Metal)
                                                 <name>_nor_gl_4k.png   (OpenGL normal)
                                                 <name>_NormalDX_4k.png (DirectX normal)
                                                 <name>_Height_4k.png
                                          <name>.mtlx                   (MaterialX doc)

That keeps one fact per zone instead of six that must stay in sync, and adding a
backend later touches the generator, not all 161 entries.
"""
import csv, json, os, re, collections

TEXROOT  = r"U:/Textures/PolyHaven_Derived"
OUTDIR   = r"U:/Git/AssetBashTools/config"
HERE     = os.path.dirname(os.path.abspath(__file__))
CLS      = os.path.join(HERE, "zone_classification.tsv")

MAPS = {"basecolor": "_BaseColor_4k.png", "arm": "_ARM_4k.png",
        "normal_gl": "_nor_gl_4k.png",   "normal_dx": "_NormalDX_4k.png",
        "height": "_Height_4k.png",      "ao": "_AO_4k.png",
        "rough": "_Rough_4k.png"}

avail = sorted(d for d in os.listdir(TEXROOT) if os.path.isdir(os.path.join(TEXROOT, d)))

def maps_for(name):
    img = os.path.join(TEXROOT, name, "Images")
    if not os.path.isdir(img):
        return {}
    have = set(os.listdir(img))
    return {k: name + suf for k, suf in MAPS.items() if (name + suf) in have}

# zone -> preferred material keywords, in priority order
PREFER = {
    "Walls": ["concrete_wall", "plaster", "concrete", "brick"],
    "WindowWalls": ["concrete_wall", "brick", "concrete"],
    "Corners": ["concrete", "brick"],
    "Parapet": ["concrete"],
    "Roof": ["roof", "tile"],
    "Trim": ["plaster", "wood"], "BuildingTrim": ["plaster", "wood"],
    "TF_Cornice": ["concrete", "plaster"],
    "WindowSill": ["concrete", "stone"],
    "WindowFrame": ["wood", "painted"], "WindowCasement": ["wood", "painted"],
    "WindowTrim": ["wood"], "WindowTrimSides": ["wood"],
    "WindowTrimTop_01": ["wood"], "WindowTrimLower": ["wood"],
    "DoorFrame": ["wood"], "DoorWood": ["wood"],
    "Underside": ["concrete"], "Railing": ["metal", "rust"],
    "Ladder": ["metal", "rust"], "Bannisters": ["metal", "rust"],
}
FAMILY_FALLBACK = {
    "Masonry": ["concrete", "brick", "plaster", "stone"],
    "Wood": ["wood", "plank"], "Roofing": ["roof", "tile"],
    "Ground": ["asphalt", "gravel", "concrete"], "Fabric": ["fabric", "cloth"],
    "Trim": ["wood", "plaster"], "Metal": ["metal", "rust"],
}
SHADER_ONLY = {"Glass": "authored shader - parallax/refraction, not a scanned material",
               "Emissive": "authored shader plus per-instance lit state",
               "Signage": "authored artwork"}

rows = list(csv.DictReader(open(CLS, encoding="utf-8"), delimiter="\t"))
shading = [r for r in rows if r["kind"] == "SHADING"]

def pick(zone, family):
    for kw in PREFER.get(zone, []) + FAMILY_FALLBACK.get(family, []):
        for m in avail:
            if kw in m and maps_for(m):
                return m
    return ""

bindings, stats = {}, collections.Counter()
for r in sorted(shading, key=lambda x: x["zone"]):
    z, fam = r["zone"], r["family"]
    if fam in SHADER_ONLY:
        bindings[z] = {"material": "", "family": fam, "fill": "shader",
                       "note": SHADER_ONLY[fam]}
        stats["shader"] += 1
        continue
    m = pick(z, fam)
    if m:
        bindings[z] = {"material": m, "family": fam, "source": "polyhaven",
                       "license": "CC0", "maps": maps_for(m)}
        stats["bound"] += 1
    else:
        bindings[z] = {"material": "", "family": fam, "fill": "author",
                       "note": "no CC0 candidate - author in Copernicus"}
        stats["unbound"] += 1

out = {
  "version": "2.0",
  "namespace": "AB",
  "description": "Zone -> CC0 material NAME. Each backend generator resolves the maps from "
                 "$AB_TEXTURES/PolyHaven_Derived/<name>/Images/ using the standard suffixes.",
  "texture_root": "$AB_TEXTURES/PolyHaven_Derived",
  "texture_root_fallback": TEXROOT,
  "map_suffixes": MAPS,
  "license_policy": "CC0 (PolyHaven) or authored in-house only. Megascans is never "
                    "redistributable and must not appear in a shipped binding.",
  "bindings": bindings,
  "stats": {"zones": len(bindings), "bound_cc0": stats["bound"],
            "shader_only": stats["shader"], "needs_authoring": stats["unbound"],
            "materials_available": len(avail)},
}
os.makedirs(OUTDIR, exist_ok=True)
p = os.path.join(OUTDIR, "material_bindings.json")
json.dump(out, open(p, "w", encoding="utf-8"), indent=2)
print("wrote", p, "(%d bytes)" % os.path.getsize(p))
print(json.dumps(out["stats"], indent=2))
print()
print("sample bindings:")
for z in ("Walls", "Roof", "WindowFrame", "Railing", "WindowGlass", "HW_Bolt"):
    if z in bindings:
        b = bindings[z]
        print("  %-14s -> %-28s %s" % (z, b.get("material") or "(none)",
                                       b.get("fill") or b.get("license", "")))
print()
byfill = collections.Counter(v.get("fill", "bound") for v in bindings.values())
print("fill breakdown:", dict(byfill))
