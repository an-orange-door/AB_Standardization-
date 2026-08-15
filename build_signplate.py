"""Build and publish AB::SignPlate. Run inside Houdini:

    exec(open('U:/AB_Standardization/build_signplate.py').read())     # build only
    exec(open('U:/AB_Standardization/build_signplate.py').read()); publish()

Kept on disk rather than built live: the first version was lost when the Trace SOP
crashed the session, and the second was broken by collapseIntoSubnet. Re-running is
idempotent.

Hard-won details, each one cost a debugging round:

  * circle/grid with type=polygon already emit a closed FACE. A polyfill after them
    re-fills into a fan with a centre point and bad normals, which sends the
    extrusion to ~4e6 units.

  * circle SOP orient 0 = XY. orient 2 is ZX, so the shape rotation tilts the
    profile out of plane instead of spinning it.

  * polyextrude has TWO toggles per face set: 'outputfront' builds the geometry,
    'outputfrontgrp' names the group. Set only the group toggle and you get a sign
    with no back face.

  * circle emits a -Z facing polygon, grid a +Z one. The n-gon branch is reversed so
    every profile faces +Z: textured face at z=0 pointing at the viewer, body behind.
    Traced profiles must be authored facing +Z as well.

  * BUILD INSIDE THE SUBNET. collapseIntoSubnet rewrites every internal ../Parm
    reference to ../../Parm, which then points outside the asset and silently
    evaluates to 0 - a plate with zero size and one primitive.

  * createDigitalAsset does NOT carry the parm interface onto the definition, and a
    setExpression on one node does not reach it either. The interface is applied to
    the definition explicitly, and the Shape-driven parms carry their logic as
    DEFAULT EXPRESSIONS so every new instance is born with them.

  * The SOP Trace node segfaults in 22.0.368 (SOP_Trace::syncNodeVersion, signal 11).
    Do not add one. Input 2 reads a cached traced profile off disk instead.
"""
import hou

TYPE_NAME = "AB::SignPlate::1.0"
HDA_PATH  = "U:/Git/AssetBashTools/Sops/CityProps/AB.SignPlate.1.0.hda"
SUBMENU   = "Asset Bash/Signs"

SHAPES = ("Rectangle", "Circle", "Ellipse", "Diamond", "Triangle", "Octagon", "Traced")
LABELS = ("Rectangle", "Circle", "Ellipse", "Diamond", "Triangle", "Octagon",
          "Traced (cached profile)")

# Shape index -> behaviour. Diamond is a 4-gon at rotation 0 (vertices at
# 0/90/180/270). Triangle rotates -90 so it points down, which Yield needs.
# Octagon rotates 22.5 for a flat top, like Stop.
EXPR_BRANCH = 'if(ch("Shape")==0, 1, if(ch("Shape")==6, 2, 0))'
EXPR_DIVS   = 'if(ch("Shape")==3, 4, if(ch("Shape")==4, 3, if(ch("Shape")==5, 8, 64)))'
EXPR_ROT    = 'if(ch("Shape")==4, -90, if(ch("Shape")==5, 22.5, 0))'


def parm_group():
    ptg = hou.ParmTemplateGroup()
    f = hou.FolderParmTemplate("SignPlate", "Sign Plate")
    f.addParmTemplate(hou.MenuParmTemplate("Shape", "Shape", SHAPES, LABELS))
    f.addParmTemplate(hou.FloatParmTemplate("Width", "Width", 1, (0.76,), min=0.05, max=6))
    f.addParmTemplate(hou.FloatParmTemplate("Aspect", "Aspect", 1, (1.0,), min=0.1, max=8))
    f.addParmTemplate(hou.FloatParmTemplate("Thickness", "Thickness", 1, (0.012,), min=0.001, max=0.1))
    f.addParmTemplate(hou.FloatParmTemplate("CornerRadius", "Corner Radius", 1, (0.02,), min=0, max=0.3))
    f.addParmTemplate(hou.IntParmTemplate("CornerDivs", "Corner Divisions", 1, (8,), min=1, max=16))
    f.addParmTemplate(hou.FloatParmTemplate("ChamferSize", "Edge Chamfer", 1, (0.001,),
                                            min=0.0, max=0.01))

    uv = hou.FolderParmTemplate("UVWindowFolder", "UV Window",
                                folder_type=hou.folderType.Collapsible)
    for n, l, d in (("UMin", "U Min", 0.0), ("VMin", "V Min", 0.0),
                    ("UMax", "U Max", 1.0), ("VMax", "V Max", 1.0)):
        uv.addParmTemplate(hou.FloatParmTemplate(n, l, 1, (d,), min=0, max=1))
    f.addParmTemplate(uv)

    idf = hou.FolderParmTemplate("Identity", "Identity",
                                 folder_type=hou.folderType.Collapsible)
    for n, l in (("SignCode", "Sign Code"), ("SignName", "Sign Name"),
                 ("SignShapeName", "Shape Name")):
        idf.addParmTemplate(hou.StringParmTemplate(n, l, 1, ("",)))
    for n, l in (("TexturePath", "Texture Path"), ("TracedFile", "Traced Profile File")):
        idf.addParmTemplate(hou.StringParmTemplate(
            n, l, 1, ("",), string_type=hou.stringParmType.FileReference))
    for n, l in (("MatFront", "Material Front"), ("MatBack", "Material Back")):
        idf.addParmTemplate(hou.StringParmTemplate(n, l, 1, ("",)))
    f.addParmTemplate(idf)

    dv = hou.FolderParmTemplate("Derived", "Derived (driven by Shape)",
                                folder_type=hou.folderType.Collapsible)
    for tmpl, expr in ((hou.IntParmTemplate("ProfileBranch", "Profile Branch", 1, (0,)), EXPR_BRANCH),
                       (hou.IntParmTemplate("ShapeDivs", "Shape Divisions", 1, (64,)), EXPR_DIVS),
                       (hou.FloatParmTemplate("ShapeRotate", "Shape Rotate", 1, (0.0,)), EXPR_ROT)):
        tmpl.setDefaultExpression((expr,))
        tmpl.setDefaultExpressionLanguage((hou.scriptLanguage.Hscript,))
        dv.addParmTemplate(tmpl)
    f.addParmTemplate(dv)

    ptg.append(f)
    return ptg


def build(parent_path="/obj", geo_name="SignPlateDev"):
    obj = hou.node(parent_path)
    old = obj.node(geo_name)
    if old:
        old.destroy()
    geo = obj.createNode("geo", geo_name)

    # Build directly inside the subnet - never collapse into one.
    sub = geo.createNode("subnet", "SignPlate")
    for c in sub.children():
        c.destroy()

    ngon = sub.createNode("circle", "NGonProfile")
    ngon.parm("type").set("poly")     # by token; see RectProfile note below
    ngon.parm("orient").set(0)
    ngon.parm("divs").setExpression('ch("../ShapeDivs")')
    ngon.parm("rz").setExpression('ch("../ShapeRotate")')

    revn = sub.createNode("reverse", "ReverseNGon")
    revn.setInput(0, ngon)

    rect = sub.createNode("grid", "RectProfile")
    # Set by TOKEN, not index. circle's type menu is (prim, poly, nurbs, bezier) so
    # 1 = poly, but grid's is (poly, mesh, nurbs, ...) so 1 = MESH. A mesh grid gives
    # a correct bbox, so sizing looks fine, but polybevel cannot round its corners -
    # the Corner Radius silently does nothing on every rectangular sign.
    rect.parm("type").set("poly")
    rect.parm("orient").set(0)
    rect.parm("rows").set(2)
    rect.parm("cols").set(2)

    traced = sub.createNode("file", "TracedProfile")
    traced.parm("file").setExpression('chs("../TracedFile")')
    traced.parm("missingframe").set(1)

    switch = sub.createNode("switch", "SwitchProfile")
    switch.setInput(0, revn)
    switch.setInput(1, rect)
    switch.setInput(2, traced)
    switch.parm("input").setExpression('ch("../ProfileBranch")')

    # Normalise to a 1x1 bbox first so the bevel offset means the same thing on every
    # branch (circle is radius 1, grid is 10 across, a traced profile is anything).
    norm = sub.createNode("xform", "NormaliseProfile")
    norm.setInput(0, switch)
    norm.parm("sx").setExpression('1.0 / max(bbox(opinputpath(".",0), D_XSIZE), 1e-6)')
    norm.parm("sy").setExpression('1.0 / max(bbox(opinputpath(".",0), D_YSIZE), 1e-6)')

    bevel = sub.createNode("polybevel", "RoundCorners")
    bevel.setInput(0, norm)
    # grouptype defaults to "guess" with an empty group, which bevels NOTHING on a
    # flat 2D profile - Corner Radius moves but the geometry never changes. It has to
    # be "points" explicitly. Empty group then means all points.
    bevel.parm("grouptype").set("points")
    bevel.parm("group").set("")
    bevel.parm("ignoreflatpoints").set(0)
    bevel.parm("offset").setExpression(
        'ch("../CornerRadius") / max(ch("../Width"), 1e-6)')
    bevel.parm("divisions").setExpression('ch("../CornerDivs")')

    # A zero-offset bevel still splits every corner into coincident points, so skip
    # the node entirely rather than emit degenerate geometry.
    bsw = sub.createNode("switch", "BevelSwitch")
    bsw.setInput(0, norm)
    bsw.setInput(1, bevel)
    # Skipped for Circle and Ellipse (rounding a disc's corners changes nothing and
    # takes it from 128 to 512 points) and for Octagon, whose corners are the shape.
    bsw.parm("input").setExpression(
        'ch("../CornerRadius") > 0 && ch("../Shape") != 1 && ch("../Shape") != 2'
        ' && ch("../Shape") != 5')

    # Size last. Rounding corners shrinks the profile, so fitting after the bevel is
    # what keeps the plate bbox exactly Width by Width/Aspect - which the UV window
    # and the real-world sign dimensions both depend on.
    xf = sub.createNode("xform", "FitToAspect")
    xf.setInput(0, bsw)
    xf.parm("sx").setExpression(
        'ch("../Width") / max(bbox(opinputpath(".",0), D_XSIZE), 1e-6)')
    xf.parm("sy").setExpression(
        'ch("../Width") / ch("../Aspect") / max(bbox(opinputpath(".",0), D_YSIZE), 1e-6)')

    ext = sub.createNode("polyextrude", "ExtrudePlate")
    ext.setInput(0, xf)
    # NEGATIVE. The profile faces +Z, and a positive distance drives the extruded cap
    # to -Z, leaving the textured face buried at the BACK of the plate with its normal
    # pointing into the solid. The artwork then reads mirrored, because you are seeing
    # it through the plate. Negating puts SignFront at +Z facing outward.
    ext.parm("dist").setExpression('-ch("../Thickness")')
    for geo_tog, grp_tog, grp, nm in (
            ("outputfront", "outputfrontgrp", "frontgrp", "__front"),
            ("outputback",  "outputbackgrp",  "backgrp",  "__back"),
            ("outputside",  "outputsidegrp",  "sidegrp",  "__side")):
        ext.parm(geo_tog).set(1)
        ext.parm(grp_tog).set(1)
        ext.parm(grp).set(nm)

    # --- micro chamfer on the front and back rim -------------------------------
    # Front-to-side and back-to-side edges sit at ~90 degrees; the edges running
    # around a rounded corner are nearly flat. Selecting 88-91 degrees therefore
    # picks out exactly the two rims and nothing else.
    # House convention: the group node is named EdgeBev1 and its group name is
    # opname("."), so the name follows the node; the bevel then reads EdgeBev* so
    # the pair can be copied without editing anything.
    egrp = sub.createNode("groupcreate", "EdgeBev1")
    egrp.setInput(0, ext)
    egrp.parm("groupname").setExpression('opname(".")', hou.exprLanguage.Hscript)
    egrp.parm("grouptype").set("edge")
    egrp.parm("groupedges").set(1)
    egrp.parm("dominedgeangle").set(1)
    egrp.parm("minedgeangle").set(88)
    egrp.parm("domaxedgeangle").set(1)
    egrp.parm("maxedgeangle").set(91)

    chamfer = sub.createNode("polybevel", "ChamferEdges")
    chamfer.setInput(0, egrp)
    chamfer.parm("grouptype").set("edges")
    chamfer.parm("group").set("EdgeBev*")
    chamfer.parm("filletshape").set("chamfer")   # flat cut, not a round
    chamfer.parm("divisions").set(1)
    chamfer.parm("offset").setExpression('ch("../ChamferSize")')

    csw = sub.createNode("switch", "ChamferSwitch")
    csw.setInput(0, ext)
    csw.setInput(1, chamfer)
    csw.parm("input").setExpression('ch("../ChamferSize") > 0')

    unwrap = sub.createNode("uvunwrap", "UnwrapSides")
    unwrap.setInput(0, csw)

    uvw = sub.createNode("attribwrangle", "SetFrontUVs")
    uvw.setInput(0, unwrap)
    uvw.parm("class").set(3)
    uvw.parm("snippet").set(
        '// The front face reads the measured content window out of the untouched\n'
        '// 2048 frame, so artwork lands centred with no crop and no re-export.\n'
        'if (!inprimgroup(0, "__front", @primnum)) return;\n'
        'vector bmin, bmax;\n'
        'getbbox(0, bmin, bmax);\n'
        'vector p = point(0, "P", @ptnum);\n'
        'v@uv = set(fit(p.x, bmin.x, bmax.x, chf("../UMin"), chf("../UMax")),\n'
        '           fit(p.y, bmin.y, bmax.y, chf("../VMin"), chf("../VMax")), 0);')

    nm = sub.createNode("attribwrangle", "SetZoneNames")
    nm.setInput(0, uvw)
    nm.parm("class").set(1)
    nm.parm("snippet").set(
        '// Canonical zone names. SignFront carries the artwork; everything else is\n'
        '// the galvanised plate, same material as the pole.\n'
        's@name = inprimgroup(0, "__front", @primnum) ? "SignFront" : "SignBack";\n'
        'string mf = chs("../MatFront"), mb = chs("../MatBack");\n'
        'if (s@name == "SignFront" && mf != "") s@shop_materialpath = mf;\n'
        'if (s@name == "SignBack"  && mb != "") s@shop_materialpath = mb;')

    ident = sub.createNode("attribwrangle", "StampIdentity")
    ident.setInput(0, nm)
    ident.parm("class").set(0)
    ident.parm("snippet").set(
        '// Detail attributes so an exported plate says which sign it is.\n'
        's@sign_code    = chs("../SignCode");\n'
        's@sign_name    = chs("../SignName");\n'
        's@sign_shape   = chs("../SignShapeName");\n'
        's@sign_texture = chs("../TexturePath");\n'
        'f@sign_aspect  = chf("../Aspect");\n'
        'f@sign_width   = chf("../Width");')

    out = sub.createNode("null", "OUT_SIGNPLATE")
    out.setInput(0, ident)
    out.setDisplayFlag(True)
    out.setRenderFlag(True)

    outnode = sub.createNode("output", "output0")
    outnode.setInput(0, out)

    sub.setParmTemplateGroup(parm_group())
    sub.layoutChildren()
    return sub


def publish(sub=None, path=HDA_PATH):
    sub = sub or hou.node("/obj/SignPlateDev/SignPlate")
    asset = sub.createDigitalAsset(
        name=TYPE_NAME, hda_file_name=path, description="AB Sign Plate",
        min_num_inputs=0, max_num_inputs=1, ignore_external_references=True)
    d = asset.type().definition()
    d.setParmTemplateGroup(parm_group())     # createDigitalAsset does not do this
    d.addSection("Tools.shelf", TOOLS_SHELF)
    return asset


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

NODE = build()
