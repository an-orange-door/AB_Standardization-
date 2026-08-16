"""Install the outline + classify wrangles into AB::BuildingFootprintGenerator.

    hython U:/AB_Standardization/install_footprint_vex.py [--apply]

RUN WITH THE HOUDINI GUI CLOSED. Without --apply this is a dry run.

FIRST STEP THAT TOUCHES A SHIPPING TOOL. Everything up to here was standalone.

Reversible by construction, the same way the MetalExtrusionMaker swap was:
  * the three hand-built subnets and their switches are LEFT IN PLACE, merely
    disconnected from the output, so they no longer cook. Reconnecting one wire
    restores the current behaviour exactly.
  * the library is tagged `pre-footprint-rewrite` at 0b81e2c.
  * a backup of the .hda is written beside this script before anything is saved.

⚠ THE INTERFACE GOES ON THE DEFINITION, NOT THE NODE. Setting the parm template
group on a live instance and then calling updateFromNode saves the CONTENTS but
NOT the interface — the MetalExtrusionMaker install shipped that way and a fresh
instance came out with no parms at all, so the VEX read a non-existent
parameter, got 0, and produced flangeless profiles. Use
definition.setParmTemplateGroup, then verify on a FRESH instance.
"""
import os
import shutil
import sys

import hou

LIB = "U:/Git/AssetBashTools"
TYPE = "AB::BuildingFootprintGenerator::1.0"
OUTLINE_VEX = "U:/AB_Standardization/vex/footprint_outline.vex"
CLASSIFY_VEX = "U:/AB_Standardization/vex/footprint_classify.vex"
BACKUP = "U:/AB_Standardization/_backup_footprint"

APPLY = "--apply" in sys.argv


def install_all():
    for root, dirs, files in os.walk(LIB):
        r = root.replace("\\", "/") + "/"
        if any(s in r for s in ("/backup/", "/OLD/", "/_Archive/", "/.git")):
            continue
        for f in sorted(files):
            if f.lower().endswith((".hda", ".otl")):
                try:
                    hou.hda.installFile(os.path.join(root, f))
                except Exception:
                    pass


def main():
    install_all()
    nt = hou.nodeType(hou.sopNodeTypeCategory(), TYPE)
    if nt is None:
        print("!! %s not found" % TYPE); return 1
    d = nt.definition()
    path = d.libraryFilePath()
    print("target : %s" % path)
    print("mode   : %s" % ("APPLY" if APPLY else "DRY RUN (pass --apply)"))

    holder = hou.node("/obj").createNode("geo", "FootprintInstall")
    node = holder.createNode(TYPE, "live")
    node.allowEditingOfContents()

    # what currently drives the output, so the rewire is against fact
    out = node.node("output0") or next(
        (c for c in node.children() if c.type().name() == "output"), None)
    if out is None:
        print("!! no output node found"); return 1
    driver = out.inputs()[0] if out.inputs() else None
    print("output0 currently fed by: %s" % (driver.name() if driver else "(nothing)"))

    # ---- 1. interface, ON THE DEFINITION -----------------------------------
    ptg = d.parmTemplateGroup()
    added = []

    def put(t, after):
        if ptg.find(t.name()) is not None:
            ptg.replace(t.name(), t)
        else:
            anchor = ptg.find(after)
            if anchor is not None:
                ptg.insertAfter(anchor, t)
            else:
                ptg.append(t)
        added.append(t.name())

    cs = hou.MenuParmTemplate(
        "CornerStyle", "Corner Style",
        menu_items=("0", "1", "2"),
        menu_labels=("Right Angle", "Chamfer", "Fillet"),
        default_value=0)
    cs.setHelp("Right Angle keeps the true corner; Chamfer cuts across it; "
               "Fillet rounds it. Overridable per corner with a corner_style "
               "point attribute on the outline.")
    put(cs, "BldCornerSize")

    rr = hou.FloatParmTemplate("RoundCornerRatio", "Round Corner Ratio", 1,
                               default_value=(0.4,), min=0.0, max=0.5)
    rr.setHelp("Fillet radius of the Rounded Corner shape, as a fraction of "
               "Building Width. 0.4 reproduces the previous hardcoded value.")
    put(rr, "CornerStyle")

    cd = hou.IntParmTemplate("CornerDivs", "Corner Divisions", 1,
                             default_value=(12,), min=2, max=64)
    cd.setHelp("Segments in a filleted corner.")
    put(cd, "RoundCornerRatio")

    ln = hou.ToggleParmTemplate("LegacyNames", "Legacy Group Names",
                                default_value=True)
    ln.setHelp("Also emit WallFront / WallBack / WallLeft / WallRight for "
               "four-cornered footprints, so existing tools keep working while "
               "they are migrated to Wall_01..NN. Deprecated.")
    put(ln, "CornerDivs")
    print("parms added/replaced: %s" % ", ".join(added))

    # ---- 2. the two wrangles ------------------------------------------------
    o = node.node("FootprintOutline") or node.createNode("attribwrangle", "FootprintOutline")
    o.parm("class").set(0)
    with open(OUTLINE_VEX, encoding="utf-8") as f:
        o.parm("snippet").set(f.read())
    c = node.node("FootprintClassify") or node.createNode("attribwrangle", "FootprintClassify")
    c.parm("class").set(0)
    with open(CLASSIFY_VEX, encoding="utf-8") as f:
        c.parm("snippet").set(f.read())
    c.setInput(0, o)
    for n_, col in ((o, (0.35, 0.55, 0.75)), (c, (0.35, 0.55, 0.75))):
        n_.setColor(hou.Color(*col))
    o.setComment("Outline only. Shape is data; structure is computed downstream.")
    c.setComment("Classification. Replaces 277 nodes across three subnets.\n"
                 "Parity-checked against the shipping shapes; see "
                 "parity_l_rounded.py.")
    for n_ in (o, c):
        n_.setGenericFlag(hou.nodeFlag.DisplayComment, True)
    if driver is not None:
        o.setPosition(driver.position() + hou.Vector2(3, 2))
        c.setPosition(driver.position() + hou.Vector2(3, 1))

    # ---- 3. rewire ----------------------------------------------------------
    out.setInput(0, c)
    print("rewired output0 <- FootprintClassify (was %s)"
          % (driver.name() if driver else "nothing"))

    # ---- 4. cook every shape BEFORE writing anything ------------------------
    fails = []
    for shape in range(3):
        node.parm("BuildingShape").set(shape)
        try:
            node.cook(force=True)
            g = node.geometry()
            if not len(g.prims()):
                fails.append("shape %d produced no prims" % shape)
        except hou.Error as e:
            fails.append("shape %d: %s" % (shape, str(e).split("\n")[0][:70]))
    node.parm("BuildingShape").set(0)
    if fails:
        print("\n!! NOT SAVING:")
        for f in fails:
            print("   %s" % f)
        return 1
    print("all three shapes cook")

    if not APPLY:
        print("\ndry run complete — nothing written")
        return 0

    if not os.path.isdir(BACKUP):
        os.makedirs(BACKUP)
    shutil.copy2(path, os.path.join(BACKUP, os.path.basename(path)))
    print("backed up to %s" % BACKUP)

    before = os.path.getsize(path)
    d.updateFromNode(node)          # contents
    d.setParmTemplateGroup(ptg)     # interface — MUST be on the definition
    after = os.path.getsize(path)
    print("saved %s (%d -> %d bytes)" % (path, before, after))

    # ---- 5. verify on a FRESH instance -------------------------------------
    print("\nverifying a fresh instance...")
    fresh = holder.createNode(TYPE, "fresh")
    missing = [n for n in ("CornerStyle", "RoundCornerRatio", "CornerDivs",
                           "LegacyNames") if fresh.parm(n) is None]
    print("  parms missing: %s" % (missing or "none"))
    for shape in range(3):
        fresh.parm("BuildingShape").set(shape)
        fresh.cook(force=True)
        g = fresh.geometry()
        groups = sorted(gr.name() for gr in g.primGroups())
        print("  shape %d: %d prims, groups %s%s"
              % (shape, len(g.prims()), groups[:4],
                 " +%d" % (len(groups) - 4) if len(groups) > 4 else ""))
    return 1 if missing else 0


if __name__ == "__main__":
    sys.exit(main())
