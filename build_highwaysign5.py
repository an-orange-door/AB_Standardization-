"""⚠ NO LONGER REPRODUCES THE SHIPPED ASSET - 2026-08-14.

Jordan hand-edited AB.HighwaySignGenerator.5.0.hda after this script generated it,
clearing the locally-embedded copy of SignHighway inside CreateSigns (229 nodes) so the
node inherits the SignHighway::2.0 definition instead of carrying its own edited
contents. Re-running build() would fork from 4.9 again and DISCARD that.

The .hda on disk is now the source of truth. This file is kept as the record of what the
5.0 conversion did and why - the library wiring, the MUTCD size class, the sign-two
spacing solve, the hardware packing and the traps each one hit. Read it, do not run it,
unless you intend to rebuild from 4.9 from scratch.
"""

"""Cut AB::HighwaySignGenerator::5.0 from 4.9. Run inside Houdini:

    exec(open('U:/AB_Standardization/build_highwaysign5.py').read()); publish()

Same surgery as StreetSignGenerator 3.0: the hand-built CreateSignGraphics branch
is replaced by AB::SignLibrary, and the integer picker by a name menu.

5.0 rather than 4.10 - version comparison is numeric so 4.10 would have worked, but
the interface change is breaking and a major bump says so.

NOT applied to RoofTopSignGenerator or CommercialSignGenerator. Those have no
CreateSignGraphics at all: they are lettering tools (CreateFonts, switch_ADD_TEXT,
CreateNeonText, Arrows) building custom text and neon, not standard road signage.
The sign library does not apply to them.
"""
import hou

SRC_TYPE  = "AB::HighwaySignGenerator::4.9"
TYPE_NAME = "AB::HighwaySignGenerator::5.0"
HDA_PATH  = "U:/Git/AssetBashTools/Sops/CityProps/AB.HighwaySignGenerator.5.0.hda"
SUBMENU   = "Asset Bash/Signs"
LIB_DEFAULT = "$ASSETBASH/config/signs_library.csv"

DEAD_PARMS = ["PrimarySignGroup", "PrimarySignType1",
              "SecondSignGroup", "SecondSignType1", "SecondSignType2"]

# reuse the interface builders from the street sign script - one definition of the
# menu, so the two tools cannot drift apart
import importlib.util as _ilu
_spec = _ilu.spec_from_file_location("ss3", "U:/AB_Standardization/build_streetsign3.py")


def _load_helpers():
    """Pull SETS / SHAPES / sign_folder from build_streetsign3 without running it."""
    src = open("U:/AB_Standardization/build_streetsign3.py", encoding="utf-8").read()
    src = src.split("def fork_version()")[0]        # stop before anything that builds
    ns = {"hou": hou}
    exec(compile(src, "build_streetsign3.py", "exec"), ns)
    return ns


H = _load_helpers()
sign_folder = H["sign_folder"]


def fork_version():
    src = hou.sopNodeTypeCategory().nodeTypes()[SRC_TYPE].definition()
    src.copyToHDAFile(HDA_PATH, new_name=TYPE_NAME, new_menu_name="AB Highway Signs")
    hou.hda.installFile(HDA_PATH)


def apply_interface():
    d = hou.sopNodeTypeCategory().nodeTypes()[TYPE_NAME].definition()
    ptg = d.parmTemplateGroup()
    for p in DEAD_PARMS:
        t = ptg.find(p)
        if t:
            ptg.remove(t)
    if not ptg.find("LibraryFile"):
        ptg.append(hou.StringParmTemplate(
            "LibraryFile", "Library File", 1, (LIB_DEFAULT,),
            string_type=hou.stringParmType.FileReference))
    if not ptg.find("PrimarySign"):
        ptg.append(sign_folder("Primary Sign", "Primary", "X01F01"))     # Interstate
    if not ptg.find("SecondarySign"):
        ptg.append(sign_folder("Secondary Sign", "Secondary", "X01F14"))  # North banner
    if not ptg.find("SignSizeClass"):
        sc = hou.StringParmTemplate("SignSizeClass", "Sign Size Class", 1, ("freeway",))
        sc.setMenuItems(("minimum", "conventional", "expressway", "freeway", "oversized"))
        sc.setMenuLabels(("Minimum", "Conventional road", "Expressway", "Freeway",
                          "Oversized"))
        ptg.append(sc)
    if not ptg.find("SignSpacing"):
        ptg.append(hou.FloatParmTemplate("SignSpacing", "Sign Spacing", 1, (0.10,),
                                         min=0.0, max=1.5))
    if not ptg.find("SignThickness"):
        ptg.append(hou.FloatParmTemplate("SignThickness", "Sign Thickness", 1,
                                         (0.006,), min=0.001, max=0.05))
    d.setParmTemplateGroup(ptg)


def build(parent_path="/obj", geo_name="HighwaySign5Dev"):
    fork_version()
    apply_interface()
    obj = hou.node(parent_path)
    old = obj.node(geo_name)
    if old:
        old.destroy()
    geo = obj.createNode("geo", geo_name)
    node = geo.createNode(TYPE_NAME, "HighwaySign5")
    node.allowEditingOfContents()

    removed = []
    style = node.node("HighwaySigns/HwyStyle_01")

    prim = style.createNode("AB::SignLibrary::1.0", "PrimarySignLib")
    sec = style.createNode("AB::SignLibrary::1.0", "SecondarySignLib")
    for n in (prim, sec):
        n.setComment("Data only - resolves a library row for the sign materials.\n"
                     "Its geometry output is deliberately unconnected.")
        n.setGenericFlag(hou.nodeFlag.DisplayComment, True)
    for lib, prefix in ((prim, "Primary"), (sec, "Secondary")):
        lib.parm("LibraryFile").setExpression('chs("../../../LibraryFile")')
        lib.parm("SetFilter").setExpression('chs("../../../%sSet")' % prefix)
        lib.parm("ShapeFilter").setExpression('chs("../../../%sShape")' % prefix)
        lib.parm("Sign").setExpression('chs("../../../%sSign")' % prefix)
        lib.parm("Thickness").setExpression('ch("../../../SignThickness")')
        # The MUTCD sizes a sign per class, not by one multiplier, so the class picks a
        # column in the library. A gantry is freeway by definition.
        lib.parm("SizeClass").setExpression('chs("../../../SignSizeClass")')

    # These are the signs ATTACHED TO THE SUPPORT, not the big overhead gantry panel.
    # The panel is built by CreateSigns and is left alone. Both attached signs are real
    # plates, so the library supplies geometry here - the same drop-in that works in
    # StreetSignGenerator.
    #
    # They keep the tool's SignFront_0 / SignFront_1 naming so its existing material
    # slots still bind, and so sign one can be told apart from sign two.
    renamers = {}
    for src_node, idx in ((prim, 0), (sec, 1)):
        w = style.createNode("attribwrangle", "NameSignFace_%d" % idx)
        w.setInput(0, src_node)
        w.parm("class").set(1)
        w.parm("snippet").set(
            'if (s@name == "SignFront") s@name = "SignFront_%d";' % idx)
        renamers[src_node] = w

    for om_name, src in (("object_merge6", renamers[prim]),
                         ("object_merge7", renamers[sec])):
        om = style.node(om_name)
        if om:
            for out in om.outputs():
                for i, inp in enumerate(out.inputs()):
                    if inp and inp.name() == om_name:
                        out.setInput(i, src)
            om.destroy()
            removed.append("HwyStyle_01/%s -> library" % om_name)

    # Sign two dropped by a hardcoded -2.0, which left the two plates overlapping.
    # Solve it from both plates so sign two always clears sign one by SignSpacing,
    # whatever pair is chosen.
    #
    # Reference only PrimarySignIn / PrimarySignIn1. Both are sibling inputs to the
    # copytopoints and independent of transform3. Referencing SignsOut instead cycles
    # through the panel branch - "Infinite recursion in evaluation" on the whole asset.
    t3 = style.node("transform3")
    if t3:
        t3.parm("ty").setExpression(
            '-(bbox("../PrimarySignIn", D_YSIZE) * 0.5'
            ' + bbox("../PrimarySignIn1", D_YSIZE) * 0.5'
            ' + ch("../../../SignSpacing"))')
    style.layoutChildren()

    # --- point the tool's own sign materials at the library texture ------------
    # HighwaySign keeps its sign faces on SignShape_001..004 and drives their tint from
    # the Color Options panel, so the right integration is to feed those materials
    # rather than to bypass them. Their basecolor_texture was left as a dead "op:"
    # reference by the old COP-based system, which is why the face rendered untextured.
    mats = node.node("PrincipledMaterials/mats")
    for matname, prefix in (("SignShape_001", "Primary"), ("SignShape_002", "Secondary")):
        m = mats.node(matname) if mats else None
        if not m:
            continue
        m.parm("basecolor_useTexture").set(1)
        m.parm("basecolor_texture").set(
            '$AB_SIGNS/`chs("../../../HighwaySigns/HwyStyle_01/%sSignLib/InfoTexture")`'
            % prefix)
        removed.append("retextured %s <- %sSignLib" % (matname, prefix))

    # --- galvanised metal on the support structure -----------------------------
    # Metal_GalvanizedRusty_01 is a materialbuilder: two principled shaders blended by
    # noise for the rust, with the Metal colour from the Color Options panel feeding it.
    # MechanicalsMetal is the base layer the supports actually shade with, so the maps go
    # there and the rust layering and colour controls are left intact.
    gal = mats.node("Metal_GalvanizedRusty_01") if mats else None
    base = gal.node("MechanicalsMetal") if gal else None
    if base:
        base.parm("basecolor_useTexture").set(1)
        base.parm("basecolor_texture").set("$AB_TEX/Metal_Galvanized_01_basecolor.png")
        base.parm("rough_useTexture").set(1)
        base.parm("rough_texture").set("$AB_TEX/Metal_Galvanized_01_roughness.png")
        base.parm("baseNormal_useTexture").set(1)
        base.parm("baseNormal_texture").set("$AB_TEX/Metal_Galvanized_01_normal.png")
        removed.append("galvanised maps -> Metal_GalvanizedRusty_01/MechanicalsMetal")

    # SignHighway 2.0 carries the LightCasing name fix (the 1.0 attribute had a trailing
    # space, which becomes a USD prim and Unreal component name). 4.9 keeps 1.0.
    for c in list(node.allSubChildren()):
        if c.type().name() != "AB::SignHighway::1.0":
            continue
        nm = c.name()            # changeNodeType destroys the old node and returns a new
        try:                     # one, so read the name first
            c.changeNodeType("AB::SignHighway::2.0", keep_parms=True)
            removed.append("retyped %s -> SignHighway 2.0" % nm)
        except Exception as e:
            removed.append("could not retype %s: %s" % (nm, str(e)[:60]))

    # 'LightCasing ' carried a TRAILING SPACE, which becomes a USD prim name and an
    # Unreal component name. It appears in HighwaySign's own material1 group list AND in
    # the SignHighway copies embedded in this definition - retyping those to 2.0 does not
    # clean them, because the definition carries its own edited contents. Sweep everything
    # reachable so the written name and every matcher move together.
    swept = 0
    for c in node.allSubChildren():
        for prm in c.parms():
            try:
                v = prm.eval()
            except Exception:
                continue
            if isinstance(v, str) and "LightCasing " in v:
                try:
                    prm.set(v.replace("LightCasing ", "LightCasing"))
                    swept += 1
                except hou.PermissionError:
                    removed.append("LOCKED, still stale: %s.%s" % (c.name(), prm.name()))
    if swept:
        removed.append("stripped the trailing space from %d parameters" % swept)

    # --- pack the repeated hardware -------------------------------------------
    # 72% of this asset was bolt hardware: 24,704 HW_Nut + 11,504 HW_Bolt + 2,864
    # HW_Washer as unique geometry, which in Unreal is tens of thousands of separate
    # meshes. Packing at the points where HardwareMaker output is copied collapses
    # them to a handful of packed prims that all share ONE geometry object - and
    # sharing is by object identity, which is what becomes an ISM in Unreal and an
    # instanceable prim in USD.
    #
    # A packed prim inherits the TARGET POINT's attributes, not the source geometry's,
    # so each pack ships nameless and unshaded unless the zone name is re-stamped.
    # Every name below is already listed in material1 slot 1, so the existing material
    # assignment picks them up with no change to the material node.
    PACK_POINTS = (
        ("HighwaySigns/HwyStyle_01/CreateSupportBrackets/copytopoints3", "HW_Bolt"),
        ("HighwaySigns/HwyStyle_01/CreateSupportBrackets/copytopoints2", "SupportBracket"),
        ("HighwaySigns/HwyStyle_01/CreateFooter/copytopoints1",          "HW_Bolt"),
        ("HighwaySigns/HwyStyle_02/CreateFooter/copytopoints1",          "HW_Bolt"),
    )
    for path, zone in PACK_POINTS:
        ctp = node.node(path)
        if not ctp:
            continue
        try:
            ctp.parm("pack").set(1)
            if ctp.parm("pivot"):
                ctp.parm("pivot").set(1)
        except hou.PermissionError:
            removed.append("LOCKED, could not pack: " + path)
            continue
        # capture the consumers BEFORE building the wrangle, or the new node appears in
        # outputs() and the rewire feeds it back into itself - "Infinite recursion".
        consumers = [(o, i) for o in ctp.outputs()
                     for i, inp in enumerate(o.inputs())
                     if inp and inp.path() == ctp.path()]
        parent = ctp.parent()
        w = parent.createNode("attribwrangle", "NamePack_" + ctp.name())
        w.parm("class").set(1)
        w.parm("snippet").set('s@name = "%s";' % zone)
        w.setInput(0, ctp)
        for o, i in consumers:
            o.setInput(i, w)
        parent.layoutChildren()
        removed.append("packed %s as %s" % (ctp.name(), zone))

    csg = node.node("CreateSignGraphics")
    if csg:
        removed.append("CreateSignGraphics (%d nodes)" % (len(csg.allSubChildren()) + 1))
        csg.destroy()

    return node, removed


TOOLS_SHELF = """<?xml version="1.0" encoding="UTF-8"?>
<shelfDocument>
  <tool name="$HDA_DEFAULT_TOOL" label="$HDA_LABEL" icon="$HDA_ICON">
    <toolMenuContext name="viewer"><contextNetType>SOP</contextNetType></toolMenuContext>
    <toolMenuContext name="network"><contextOpType>$HDA_TABLE_AND_NAME</contextOpType></toolMenuContext>
    <toolSubmenu>%s</toolSubmenu>
    <script scriptType="python"><![CDATA[import soptoolutils
soptoolutils.genericTool(kwargs, '$HDA_NAME')]]></script>
  </tool>
</shelfDocument>
""" % SUBMENU


def publish(node=None):
    node = node or hou.node("/obj/HighwaySign5Dev/HighwaySign5")
    d = node.type().definition()
    d.updateFromNode(node)
    d.addSection("Tools.shelf", TOOLS_SHELF)
    return node


NODE, REMOVED = build()
