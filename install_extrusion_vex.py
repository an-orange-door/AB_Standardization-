"""Install the parity-proven VEX profile generator into AB::MetalExtrusionMaker::2.0.

    hython U:/AB_Standardization/install_extrusion_vex.py

RUN WITH THE HOUDINI GUI CLOSED - one FX seat.
Backup already taken at U:/AB_Standardization/_backup_20260815/.

WHAT THIS CHANGES
    + parms  web_thick, flange_thick   (default EXPRESSION ch("thick"), so every
             existing scene is byte-identical until someone changes them)
    + parm   legacy_ibeam_web          (default ON - see below)
    + menu   ext_type gains 5..9. Entries 0-4 are UNTOUCHED: the ordinal is what
             saved scenes store, so reordering would silently repoint nodes.
    + node   ProfileVEX, one Detail wrangle replacing six Add SOPs
    ~ wires  switchAddBevels[0] and polybevel1[0] now read ProfileVEX

WHAT THIS DELIBERATELY DOES NOT DO
    The six Add SOPs, their nulls, the object_merges and switchExtrusionType are
    LEFT IN PLACE, merely disconnected from the downstream chain (so they no
    longer cook). Deleting them is a second, separately reviewable step. If
    anything is wrong, reconnecting switchExtrusionType -> switchAddBevels[0]
    restores 2.0 exactly.

WHY legacy_ibeam_web DEFAULTS ON
    2.0's `thick` means the FLANGE thickness but HALF the web thickness on the
    I-beam only - measured, at w=h=1 t=0.1 the web spans x 0.40..0.60 while the
    T-bar stem spans 0.45..0.55. Preserving that is the only way the I-beam is
    backward compatible, so it stays on by default. Turning it off gives a web
    that means what it says, consistent with the other four profiles and with
    AISC (a W8x31 web is THINNER than its flange, the opposite of what 2.0 makes).

Verified afterwards by re-running parity_test_extrusions.py against the backup.
"""
import os
import sys

import hou

LIB = "U:/Git/AssetBashTools"
TYPE = "AB::MetalExtrusionMaker::2.0"
VEX = "U:/AB_Standardization/vex/metal_extrusion_profiles.vex"

NEW_MENU = [("5", "Round Tube"), ("6", "Round Bar"), ("7", "Flat Bar"),
            ("8", "Hat Channel"), ("9", "Z Purlin")]


def install_all():
    n = 0
    for root, dirs, files in os.walk(LIB):
        r = root.replace("\\", "/") + "/"
        if any(s in r for s in ("/backup/", "/OLD/", "/_Archive/", "/.git")):
            continue
        for f in sorted(files):
            if f.lower().endswith((".hda", ".otl")):
                try:
                    hou.hda.installFile(os.path.join(root, f)); n += 1
                except Exception:
                    pass
    return n


def main():
    print("installed %d files" % install_all())
    ntype = hou.nodeType(hou.sopNodeTypeCategory(), TYPE)
    if ntype is None:
        print("!! %s not found" % TYPE); return 1
    d = ntype.definition()
    print("target file: %s" % d.libraryFilePath())

    holder = hou.node("/obj").createNode("geo", "InstallRig")
    node = holder.createNode(TYPE, "live")
    node.allowEditingOfContents()

    # ---- 1. parms -----------------------------------------------------------
    ptg = node.parmTemplateGroup()

    def add_after(anchor, tmpl):
        if ptg.find(tmpl.name()) is not None:
            ptg.replace(tmpl.name(), tmpl)
        else:
            ptg.insertAfter(ptg.find(anchor), tmpl)

    for name, label in (("web_thick", "Web Thickness"),
                        ("flange_thick", "Flange Thickness")):
        t = hou.FloatParmTemplate(name, label, 1, default_value=(0.1,),
                                  min=0.0, max=1.0)
        # a DEFAULT EXPRESSION, not a default value: an instance saved before
        # these parms existed picks up the default, which evaluates to thick -
        # which is exactly the backward compatibility the parity test proved
        t.setDefaultExpression(('ch("thick")',))
        t.setDefaultExpressionLanguage((hou.scriptLanguage.Hscript,))
        t.setHelp("Full thickness. Defaults to Thickness, so existing scenes "
                  "are unchanged until you set it.")
        add_after("thick", t)

    lg = hou.ToggleParmTemplate(
        "legacy_ibeam_web", "Legacy I-Beam Web", default_value=True)
    lg.setHelp("On: reproduce 2.0's I-beam, whose web is TWICE Web Thickness. "
               "Off: the web equals Web Thickness, consistent with the other "
               "profiles and with real rolled sections.")
    add_after("flange_thick", lg)

    # ---- 2. menu, APPEND ONLY ----------------------------------------------
    et = ptg.find("ext_type")
    items = list(et.menuItems())
    labels = list(et.menuLabels())
    if items[:5] != ["0", "1", "2", "3", "4"]:
        print("!! ext_type no longer starts 0-4 (%s) - aborting" % items[:5])
        return 1
    for tok, lab in NEW_MENU:
        if tok not in items:
            items.append(tok); labels.append(lab)
    et.setMenuItems(tuple(items))
    et.setMenuLabels(tuple(labels))
    ptg.replace("ext_type", et)
    node.setParmTemplateGroup(ptg)
    print("ext_type menu now: %s" % ", ".join(
        "%s=%s" % (i, l) for i, l in zip(items, labels)))

    # ---- 3. the wrangle -----------------------------------------------------
    w = node.node("ProfileVEX")
    if w is None:
        w = node.createNode("attribwrangle", "ProfileVEX")
    w.parm("class").set(0)                      # 0 = Detail, runs once
    with open(VEX, encoding="utf-8") as f:
        w.parm("snippet").set(f.read())
    w.setPosition(node.node("switchExtrusionType").position() + hou.Vector2(0, 2))
    w.setColor(hou.Color(0.35, 0.55, 0.75))
    w.setComment("Profile generation. Replaces six Add SOPs.\n"
                 "Parity-proven against 2.0: 135/135.")
    w.setGenericFlag(hou.nodeFlag.DisplayComment, True)

    # ---- 4. rewire ----------------------------------------------------------
    node.node("switchAddBevels").setInput(0, w)
    node.node("polybevel1").setInput(0, w)
    print("rewired switchAddBevels[0] and polybevel1[0] -> ProfileVEX")

    # ---- 5. cook every profile before writing anything ----------------------
    fails = []
    for i in range(10):
        node.parm("ext_type").set(i)
        try:
            node.cook(force=True)
            g = node.geometry()
            if not len(g.points()):
                fails.append("type %d produced NO points" % i)
        except hou.Error as e:
            fails.append("type %d: %s" % (i, str(e).split("\n")[0][:70]))
    node.parm("ext_type").set(0)
    if fails:
        print("\n!! NOT SAVING - cook failures:")
        for f in fails:
            print("   %s" % f)
        return 1
    print("all 10 profiles cook and produce geometry")

    # ---- 6. write -----------------------------------------------------------
    # updateFromNode, never copyToHDAFile: the latter writes an EMPTY asset when
    # the definition is embedded.
    before = os.path.getsize(d.libraryFilePath())
    d.updateFromNode(node)
    after = os.path.getsize(d.libraryFilePath())
    print("saved %s  (%d -> %d bytes)" % (d.libraryFilePath(), before, after))
    return 0


if __name__ == "__main__":
    sys.exit(main())
