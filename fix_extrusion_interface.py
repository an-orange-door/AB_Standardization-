"""Put the new parms on the DEFINITION, which is where an HDA interface lives.

    hython U:/AB_Standardization/fix_extrusion_interface.py

⚠ THE BUG THIS FIXES - worth stating because it fails silently and looks fine:
`install_extrusion_vex.py` called node.setParmTemplateGroup(...) on a live
instance and then definition.updateFromNode(node). The CONTENTS saved (the file
grew 10,804 -> 17,080 bytes and the wrangle was there), but the INTERFACE did
not: a fresh instance had no web_thick / flange_thick / legacy_ibeam_web at all.
The VEX then read ch("../web_thick") on a parm that does not exist, got 0, and
produced flangeless profiles - a difference of exactly `thick` on every case,
which is what the verification caught.

Setting the parm group on the NODE edits that instance. Setting it on the
DEFINITION edits the tool. Same family as the copyToHDAFile and
createDigitalAsset traps: always re-instantiate and check, never trust the save.
"""
import os
import sys

import hou

LIB = "U:/Git/AssetBashTools"
TYPE = "AB::MetalExtrusionMaker::2.0"
NEW_MENU = [("5", "Round Tube"), ("6", "Round Bar"), ("7", "Flat Bar"),
            ("8", "Hat Channel"), ("9", "Z Purlin")]


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
    ntype = hou.nodeType(hou.sopNodeTypeCategory(), TYPE)
    d = ntype.definition()
    print("target: %s" % d.libraryFilePath())

    ptg = d.parmTemplateGroup()          # <- the DEFINITION's interface

    for name, label in (("web_thick", "Web Thickness"),
                        ("flange_thick", "Flange Thickness")):
        t = hou.FloatParmTemplate(name, label, 1, default_value=(0.1,),
                                  min=0.0, max=1.0)
        t.setDefaultExpression(('ch("thick")',))
        t.setDefaultExpressionLanguage((hou.scriptLanguage.Hscript,))
        t.setHelp("Full thickness. Defaults to Thickness, so existing scenes "
                  "are unchanged until you set it.")
        if ptg.find(name) is not None:
            ptg.replace(name, t)
        else:
            ptg.insertAfter(ptg.find("thick"), t)

    lg = hou.ToggleParmTemplate("legacy_ibeam_web", "Legacy I-Beam Web",
                                default_value=True)
    lg.setHelp("On: reproduce 2.0's I-beam, whose web is TWICE Web Thickness. "
               "Off: the web equals Web Thickness, consistent with the other "
               "profiles and with real rolled sections.")
    if ptg.find("legacy_ibeam_web") is not None:
        ptg.replace("legacy_ibeam_web", lg)
    else:
        ptg.insertAfter(ptg.find("flange_thick"), lg)

    et = ptg.find("ext_type")
    items, labels = list(et.menuItems()), list(et.menuLabels())
    if items[:5] != ["0", "1", "2", "3", "4"]:
        print("!! ext_type no longer starts 0-4 (%s) - aborting" % items[:5])
        return 1
    for tok, lab in NEW_MENU:
        if tok not in items:
            items.append(tok); labels.append(lab)
    et.setMenuItems(tuple(items))
    et.setMenuLabels(tuple(labels))
    ptg.replace("ext_type", et)

    d.setParmTemplateGroup(ptg)
    print("definition interface updated")

    # ---- the only test that counts: a FRESH instance from the file ----------
    holder = hou.node("/obj").createNode("geo", "Check")
    n = holder.createNode(TYPE, "fresh")
    n.parm("thick").set(0.1)
    ok = True
    for p, want in (("web_thick", 0.1), ("flange_thick", 0.1),
                    ("legacy_ibeam_web", 1)):
        pm = n.parm(p)
        if pm is None:
            print("  %-16s STILL MISSING" % p); ok = False; continue
        got = pm.eval()
        good = abs(got - want) < 1e-6
        ok = ok and good
        print("  %-16s = %-6s %s" % (p, got, "ok" if good else "EXPECTED %s" % want))

    fails = []
    for i in range(10):
        n.parm("ext_type").set(i)
        try:
            n.cook(force=True)
            if not len(n.geometry().points()):
                fails.append("type %d: no points" % i)
        except hou.Error as e:
            fails.append("type %d: %s" % (i, str(e).split("\n")[0][:60]))
    for f in fails:
        print("  !! %s" % f)
    print("\n%s" % ("all 10 profiles cook, parms resolve"
                    if ok and not fails else "PROBLEMS ABOVE"))
    return 0 if (ok and not fails) else 1


if __name__ == "__main__":
    sys.exit(main())
