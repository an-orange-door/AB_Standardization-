"""Generate the AssetBashTools README — tool list with icons, correct install block.

    hython U:/AB_Standardization/build_readme.py

RUN WITH THE HOUDINI GUI CLOSED — one FX seat. Writes only README.md.

WHY GENERATED RATHER THAN HAND-WRITTEN
The old README's HOUDINI_OTLSCAN_PATH block was hand-maintained and had drifted:
`Sops/Signs` was missing entirely, so a fresh install could not see any of the
15 sign tools — the path list is NOT recursive, so a folder absent from it is
invisible. Seven listed folders no longer contain any HDA. A hand-typed list of
25 paths and 150+ tools will drift again; a generated one cannot.

Re-run it after adding a tool, a category, or an icon.
"""
import collections
import os
import re
import sys

import hou

LIB = "U:/Git/AssetBashTools"
OUT = os.path.join(LIB, "README.md")
ICONS_REL = "IconDev/Icons"

# Folders that hold HDAs we do NOT want a customer to load.
EXCLUDE_DIRS = ("/backup", "/OLD", "/_Archive", "/.git")

HERO = ("https://assetbash-public.s3.us-west-2.amazonaws.com/Images/"
        "3D-Houdini-Asset-Bash-Article-Images/"
        "Asset-Bash-Procedural-3D-Modeling-Cities-Featured-001.webp")

# One line per category, written by hand because it is editorial, not derivable.
CATEGORY_BLURB = {
    "Buildings": "Whole-building generators — footprint to facade.",
    "BuildingProps": "Parts that hang off a building: doors, windows, balconies, stairs.",
    "BuildingHelpers": "Grouping and preparation utilities used inside the building tools.",
    "CityGen": "Block and grid generators that lay out a city.",
    "CityHelpers": "Support tools for the city generators.",
    "CityProps": "Street furniture — hydrants, benches, planters, poles.",
    "Signs": "The sign toolchain, built on a 1,383-sign public-domain library.",
    "Modules": "Style libraries — pick articulated parts by architectural period.",
    "Curves": "Profile and trim generators: metal extrusions, mouldings, fancy curves.",
    "Modeling": "General modelling utilities.",
    "Natural": "Organic generators — trees, rock, crystal, foliage.",
    "PlantOns": "Surface detail applied onto an existing form.",
    "Panels": "Panelling and cladding systems.",
    "Parts": "Reusable hard-surface components.",
    "Scatters": "Distribution tools.",
    "SetDressing": "Dressing passes that turn a shape into a place.",
    "CopyTools": "Copy and instancing helpers.",
    "MotionGraphics": "Motion-graphics generators.",
    "Utilities": "Pipeline utilities — zones, material binding, export packing.",
    "VFX": "Effects setups.",
    "Volume": "Volume tools.",
    "WorldBuilding": "Terrain, roads and large-scale layout.",
}


def install_all():
    n = 0
    for root, dirs, files in os.walk(LIB):
        r = root.replace("\\", "/") + "/"
        if any(s + "/" in r or r.endswith(s + "/") for s in EXCLUDE_DIRS):
            continue
        for f in sorted(files):
            if f.lower().endswith((".hda", ".otl")):
                try:
                    hou.hda.installFile(os.path.join(root, f)); n += 1
                except Exception:
                    pass
    return n


def scan_dirs():
    """Folders that actually contain a shippable HDA — the install path, generated."""
    found = set()
    for root, dirs, files in os.walk(LIB):
        r = root.replace("\\", "/")
        rel = r[len(LIB) + 1:] if len(r) > len(LIB) else ""
        if not rel or any(s.strip("/") in rel.split("/") for s in
                          ("backup", "OLD", "_Archive", ".git")):
            continue
        if any(f.lower().endswith((".hda", ".otl")) for f in files):
            found.add(rel.replace("\\", "/"))
    return sorted(found)


def latest_tools():
    best = {}
    for cat in (hou.sopNodeTypeCategory(), hou.objNodeTypeCategory(),
                hou.cop2NodeTypeCategory()):
        for tn, nt in cat.nodeTypes().items():
            d = nt.definition()
            if d is None:
                continue
            p = (d.libraryFilePath() or "").replace("\\", "/")
            if not p.lower().startswith(LIB.lower()):
                continue
            if any(s.strip("/") in p.split("/") for s in ("backup", "OLD", "_Archive")):
                continue
            c = nt.nameComponents()
            key = (c[1], c[2])
            v = c[3] or "0"
            vk = tuple(int(x) if x.isdigit() else 0 for x in str(v).split("."))
            if key not in best or vk > best[key][0]:
                best[key] = (vk, nt, d, p)
    return best


def main():
    print("installed %d" % install_all())
    dirs = scan_dirs()
    tools = latest_tools()
    print("categories: %d   tools: %d" % (len(dirs), len(tools)))

    by_cat = collections.defaultdict(list)
    missing_icon = []
    for (ns, name), (vk, nt, d, path) in sorted(tools.items(), key=lambda x: x[0][1].lower()):
        cat = path[len(LIB) + 1:].rsplit("/", 1)[0]
        label = (d.description() or name).strip()
        icon = "%s/SOP_AB__%s.svg" % (ICONS_REL, name)
        if not os.path.isfile(os.path.join(LIB, icon)):
            icon = None
            missing_icon.append(name)
        ver = ".".join(str(x) for x in vk)
        by_cat[cat].append((name, label, ver, icon))

    L = []
    A = L.append
    A("# Asset Bash Tools")
    A("")
    A("![Asset Bash](%s)" % HERO)
    A("")
    A("**Procedural architecture and city generation for Houdini.** %d tools, built"
      % len(tools))
    A("over years of production work, exporting to USD and Unreal.")
    A("")
    A("The point is what a kit of baked models cannot do: change the proportions.")
    A("Every building, sign, road and prop here is generated from parameters and")
    A("real-world standards rather than shipped as a frozen mesh, so it fits the shot")
    A("instead of the shot fitting it.")
    A("")
    A("---")
    A("")
    A("## Requirements")
    A("")
    A("- Houdini **%s** or newer" % hou.applicationVersionString())
    A("- No third-party dependencies")
    A("")
    A("## Install")
    A("")
    A("**1.** Put the `AssetBashTools` folder anywhere you like.")
    A("")
    A("**2.** Open your `houdini.env`. It lives in your Houdini preferences folder —")
    A("`Documents/houdini%s/houdini.env` on Windows,"
      % ".".join(hou.applicationVersionString().split(".")[:2]))
    A("`~/Library/Preferences/houdini/%s/houdini.env` on macOS."
      % ".".join(hou.applicationVersionString().split(".")[:2]))
    A("")
    A("**3.** Add the two lines below, changing `ASSETBASH` to your path:")
    A("")
    A("```")
    A("ASSETBASH = /path/to/AssetBashTools")
    A("")
    A("HOUDINI_OTLSCAN_PATH = " + ";".join("$ASSETBASH/" + d for d in dirs) + ";&")
    A("```")
    A("")
    A("**4.** Restart Houdini. The tools appear in the **Tab menu under `Asset Bash`**.")
    A("")
    A("> **Why the long path list?** `HOUDINI_OTLSCAN_PATH` names directories")
    A("> explicitly and is **not recursive** — a folder missing from the list is")
    A("> invisible to Houdini. The trailing `&` preserves Houdini's own paths;")
    A("> without it you lose the standard assets. This list is generated from the")
    A("> repo, so it stays correct as categories are added.")
    A("")
    A("### Textures")
    A("")
    A("Tools that reference external textures resolve them through `$AB_TEX`:")
    A("")
    A("```")
    A("AB_TEX = $ASSETBASH/../Textures")
    A("```")
    A("")
    A("---")
    A("")
    A("## Tools")
    A("")
    A("%d tools across %d categories. Every tool is a SOP unless noted."
      % (len(tools), len(by_cat)))
    A("")

    for cat in sorted(by_cat, key=lambda c: (c.split("/")[0], c)):
        rows = by_cat[cat]
        short = cat.split("/")[-1]
        A("### %s" % cat)
        blurb = CATEGORY_BLURB.get(short)
        if blurb:
            A("")
            A("%s" % blurb)
        A("")
        A("| | Tool | Version |")
        A("|---|---|---|")
        for name, label, ver, icon in rows:
            img = ('<img src="%s" width="26" alt="">' % icon) if icon else ""
            A("| %s | **%s** | %s |" % (img, label, ver))
        A("")

    A("---")
    A("")
    A("## Conventions worth knowing")
    A("")
    A("- **Tab menu** — everything lives under `Asset Bash/<Category>`.")
    A("- **`MaterialStyle`** — most tools offer `Principled | Unreal | USD`. The")
    A("  Principled shader translates directly into other engines, including Unity.")
    A("- **`UseColor`** — writes vertex colours for material IDs, which is what you")
    A("  want when taking a mesh into Substance Painter.")
    A("- **`s@name` zones** — tools tag their geometry by region (wall, trim, glass)")
    A("  so materials can be bound per zone in Solaris or Unreal. Zone names are")
    A("  part of the interface; do not strip them.")
    A("- **Packed primitives** — tools that instance emit packed prims sharing one")
    A("  prototype, which is what lets Houdini Engine build an Unreal ISM rather")
    A("  than hundreds of separate meshes.")
    A("")
    A("## Licensing")
    A("")
    A("Bundled textures are **CC0** (PolyHaven-derived). Sign artwork is public")
    A("domain. Nothing here redistributes licensed third-party content.")
    A("")

    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(L))
    print("wrote %s (%.1f KB)" % (OUT, os.path.getsize(OUT) / 1024.0))
    print("categories in install path: %d" % len(dirs))
    if missing_icon:
        print("tools with no icon file: %d  %s"
              % (len(missing_icon), ", ".join(missing_icon[:8])))
    return 0


if __name__ == "__main__":
    sys.exit(main())
