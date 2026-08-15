"""Build and publish AB::SignLibrary::1.0. Run inside Houdini:

    exec(open('U:/AB_Standardization/build_signlibrary.py').read())
    exec(open('U:/AB_Standardization/build_signlibrary.py').read()); publish()

Pick a sign by name; out comes the plate, correctly shaped, proportioned and framed.
This is what replaces the 6-groups-of-4 integer picker that capped the sign tools at
24 signs against a 1,383-sign library.

The library is a CSV in config/, NOT a section inside the HDA. Embedding it would
repeat the mistake 2026-08-14 was spent undoing. Texture paths resolve through
$AB_SIGNS so a customer sets one variable.

Data flows one way and re-evaluates: a Python SOP reads the row and writes detail
attributes, and the internal SignPlate reads those with detail() expressions. No
callbacks, no stored state, so changing the filter or the CSV just re-cooks.
"""
import hou

TYPE_NAME = "AB::SignLibrary::1.0"
HDA_PATH  = "U:/Git/AssetBashTools/Sops/CityProps/AB.SignLibrary.1.0.hda"
SUBMENU   = "Asset Bash/Signs"
LIB_DEFAULT = "$ASSETBASH/config/signs_library.csv"

SETS = ("Any", "Highway_Signs_US", "Highway_Signs_International",
        "Symbol_Signs_Recreational", "Symbol_Signs_Transportation_01",
        "Symbol_Signs_Transportation_02", "International_Icons_Electronic_Labeling")
SET_LABELS = ("Any set", "US Highway", "Intl Highway", "Recreational",
              "Transportation 1", "Transportation 2", "Electronic")
SHAPE_FILTERS = ("Any", "Rectangle", "Circle", "Ellipse", "Diamond", "Triangle",
                 "Octagon", "Traced", "Pictogram")

# Menu of signs, filtered. Runs on every menu open; 1383 rows is trivial to scan.
MENU_SCRIPT = '''
import csv, hou
node = kwargs["node"]
try:
    path = hou.text.expandString(node.evalParm("LibraryFile"))
    want_set = node.evalParm("SetFilter")
    want_shape = node.evalParm("ShapeFilter")
    hide_decals = node.evalParm("HideDecals")
    out = []
    with open(path, encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            if want_set != "Any" and r["set"] != want_set:
                continue
            if want_shape != "Any" and r["shape"] != want_shape:
                continue
            if hide_decals and r["is_decal"] == "1":
                continue
            label = "%s   [%s]" % (r["name"], r["set_label"])
            out.extend([r["code"], label])
    if not out:
        out = ["", "(no signs match this filter)"]
    return out
except Exception as e:
    return ["", "ERROR: %s" % e]
'''

# Reads one row and publishes it as detail attributes.
PY_SOP = '''
import csv, hou

node = hou.pwd()
geo = node.geometry()
hda = node.parent()

path = hou.text.expandString(hda.evalParm("LibraryFile"))
code = hda.evalParm("Sign")

row = None
try:
    with open(path, encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            if r["code"] == code:
                row = r
                break
except Exception:
    row = None

# Defaults keep the node cooking even with a bad path or an empty menu, so a broken
# library shows an obvious 1x1 plate rather than an error the user has to decode.
size_class = hda.evalParm("SizeClass") or "conventional"

defaults = dict(shape_index="0", aspect="1.0", width="0.5",
                u0="0", v0="0", u1="1", v1="1",
                name="(none)", code="", texture="", is_decal="0", shape="Rectangle")
src = dict(row) if row else dict(defaults)
# The MUTCD gives a size per sign PER CLASS, so the class selects a column rather
# than scaling one number. Older library files without the columns fall back.
col = "width_" + size_class
if col in src:
    src["width"] = src[col]

# A Traced shape needs a cached profile on disk. If one has not been authored yet the
# switch reads an empty File SOP and the node silently produces NOTHING - which is how
# a highway shield default turned into an invisible sign. Fall back to a Rectangle and
# say so, rather than emitting zero geometry.
traced_dir = hou.text.expandString(hda.evalParm("TracedDir"))
traced_file = ""
traced_missing = 0
if src["shape"] == "Traced":
    import os as _os
    for ext in (".bgeo.sc", ".bgeo", ".obj", ".geo"):
        cand = _os.path.join(traced_dir, "%s_%s%s" % (src["name"], src["code"], ext))
        if _os.path.exists(cand):
            traced_file = cand.replace(chr(92), "/")   # chr(92) survives every quoting layer
            break
    if not traced_file:
        traced_missing = 1
        src = dict(src)
        src["shape_index"] = "0"          # Rectangle stand-in

def put(name, value):
    # addAttrib only seeds the DEFAULT. String detail attributes come back empty
    # unless the value is set explicitly as well.
    geo.addAttrib(hou.attribType.Global, name, value)
    geo.setGlobalAttribValue(name, value)

put("shape_index", int(float(src["shape_index"])))
for key in ("aspect", "width", "u0", "v0", "u1", "v1"):
    put(key, float(src[key]))
for key in ("name", "code", "texture", "shape"):
    put("sign_" + key, str(src[key]))
put("size_source", str(src.get("size_source", "")))
put("is_decal", int(float(src["is_decal"])))
put("found", 1 if row else 0)
put("traced_file", traced_file)
put("traced_missing", traced_missing)
'''


def parm_group():
    ptg = hou.ParmTemplateGroup()
    f = hou.FolderParmTemplate("SignLibrary", "Sign Library")

    lib = hou.StringParmTemplate("LibraryFile", "Library File", 1, (LIB_DEFAULT,),
                                 string_type=hou.stringParmType.FileReference)
    f.addParmTemplate(lib)

    sf = hou.StringParmTemplate("SetFilter", "Set", 1, ("Any",))
    sf.setMenuItems(SETS)
    sf.setMenuLabels(SET_LABELS)
    f.addParmTemplate(sf)

    shf = hou.StringParmTemplate("ShapeFilter", "Shape", 1, ("Any",))
    shf.setMenuItems(SHAPE_FILTERS)
    shf.setMenuLabels(SHAPE_FILTERS)
    f.addParmTemplate(shf)

    f.addParmTemplate(hou.ToggleParmTemplate("HideDecals", "Hide Decals", 1))
    sc = hou.StringParmTemplate("SizeClass", "Size Class", 1, ("conventional",))
    sc.setMenuItems(("minimum", "conventional", "expressway", "freeway", "oversized"))
    sc.setMenuLabels(("Minimum", "Conventional road", "Expressway", "Freeway", "Oversized"))
    f.addParmTemplate(sc)
    f.addParmTemplate(hou.StringParmTemplate(
        "TracedDir", "Traced Profiles", 1, ("$AB_SIGNS/_Traced",),
        string_type=hou.stringParmType.FileReference))

    sign = hou.StringParmTemplate("Sign", "Sign", 1, ("X01A01",))
    sign.setItemGeneratorScript(MENU_SCRIPT)
    sign.setItemGeneratorScriptLanguage(hou.scriptLanguage.Python)
    f.addParmTemplate(sign)

    # Width defaults to the per-set value in the CSV but stays typed-over-able.
    w = hou.FloatParmTemplate("Width", "Width", 1, (0.76,), min=0.05, max=6)
    w.setDefaultExpression(('detail("./ReadLibrary", "width", 0)',))
    w.setDefaultExpressionLanguage((hou.scriptLanguage.Hscript,))
    f.addParmTemplate(w)

    f.addParmTemplate(hou.FloatParmTemplate("Thickness", "Thickness", 1, (0.004,),
                                            min=0.001, max=0.1))
    f.addParmTemplate(hou.FloatParmTemplate("CornerRadius", "Corner Radius", 1, (0.03,),
                                            min=0, max=0.3))
    f.addParmTemplate(hou.FloatParmTemplate("ChamferSize", "Edge Chamfer", 1, (0.001,),
                                            min=0, max=0.01))

    mat = hou.FolderParmTemplate("Materials", "Materials",
                                 folder_type=hou.folderType.Collapsible)
    for n, l, node in (("MatFront", "Material Front", "SignFrontMat"),
                       ("MatBack", "Material Back", "SignBackMat")):
        t = hou.StringParmTemplate(n, l, 1, ("",),
                                   string_type=hou.stringParmType.NodeReference)
        t.setDefaultExpression(('opfullpath("./matnet/%s")' % node,))
        t.setDefaultExpressionLanguage((hou.scriptLanguage.Hscript,))
        mat.addParmTemplate(t)
    f.addParmTemplate(mat)

    info = hou.FolderParmTemplate("Info", "Resolved", folder_type=hou.folderType.Collapsible)
    for n, l, e in (("InfoName", "Name", 'details("./ReadLibrary", "sign_name")'),
                    ("InfoShape", "Shape", 'details("./ReadLibrary", "sign_shape")'),
                    ("InfoTexture", "Texture", 'details("./ReadLibrary", "sign_texture")')):
        t = hou.StringParmTemplate(n, l, 1, ("",))
        t.setDefaultExpression((e,))
        t.setDefaultExpressionLanguage((hou.scriptLanguage.Hscript,))
        info.addParmTemplate(t)
    srcp = hou.StringParmTemplate("InfoSizeSource", "Size Source", 1, ("",))
    srcp.setDefaultExpression(('details("./ReadLibrary", "size_source")',))
    srcp.setDefaultExpressionLanguage((hou.scriptLanguage.Hscript,))
    info.addParmTemplate(srcp)
    warn = hou.StringParmTemplate("InfoWarning", "Warning", 1, ("",))
    warn.setDefaultExpression((
        # ifs() not if() - the numeric form cannot return a string and the parm
        # errors with "Bad data type for function or operation"
        'ifs(detail("./ReadLibrary","traced_missing",0), '
        '"no traced profile - using a Rectangle stand-in", "")',))
    warn.setDefaultExpressionLanguage((hou.scriptLanguage.Hscript,))
    info.addParmTemplate(warn)
    a = hou.FloatParmTemplate("InfoAspect", "Aspect", 1, (1.0,))
    a.setDefaultExpression(('detail("./ReadLibrary", "aspect", 0)',))
    a.setDefaultExpressionLanguage((hou.scriptLanguage.Hscript,))
    info.addParmTemplate(a)
    f.addParmTemplate(info)

    ptg.append(f)
    return ptg


def build(parent_path="/obj", geo_name="SignLibraryDev"):
    obj = hou.node(parent_path)
    old = obj.node(geo_name)
    if old:
        old.destroy()
    geo = obj.createNode("geo", geo_name)

    sub = geo.createNode("subnet", "SignLibrary")
    for c in sub.children():
        c.destroy()

    reader = sub.createNode("python", "ReadLibrary")
    reader.parm("python").set(PY_SOP)

    plate = sub.createNode("AB::SignPlate::1.0", "Plate")
    plate.parm("Shape").setExpression('detail("../ReadLibrary", "shape_index", 0)')
    plate.parm("Aspect").setExpression('detail("../ReadLibrary", "aspect", 0)')
    for p, a in (("UMin", "u0"), ("VMin", "v0"), ("UMax", "u1"), ("VMax", "v1")):
        plate.parm(p).setExpression('detail("../ReadLibrary", "%s", 0)' % a)
    for p in ("Width", "Thickness", "CornerRadius", "ChamferSize", "MatFront", "MatBack"):
        fn = 'chs' if p.startswith("Mat") else 'ch'
        plate.parm(p).setExpression('%s("../%s")' % (fn, p))
    plate.parm("TracedFile").setExpression('details("../ReadLibrary", "traced_file")')
    plate.parm("SignCode").setExpression('details("../ReadLibrary", "sign_code")')
    plate.parm("SignName").setExpression('details("../ReadLibrary", "sign_name")')
    plate.parm("SignShapeName").setExpression('details("../ReadLibrary", "sign_shape")')
    # backtick expression inside a string parm: var stays unexpanded on disk
    plate.parm("TexturePath").set('$AB_SIGNS/`details("../ReadLibrary", "sign_texture")`')

    # --- materials -------------------------------------------------------------
    # The plate needs its own shaders or it renders as the default checker: SignPlate
    # only writes s@name, and the old CreateSignGraphics is what used to supply these.
    mats = sub.createNode("matnet", "matnet")

    # A real sign is artwork PRINTED ON retroreflective sheeting, so the face is ONE
    # material - not a reflective border around a flat face. Jordan's call, 2026-08-14.
    #
    #   emitcolor = the artwork
    #   emitint   = pow(|dot(N,I)|, falloff) * luminance(artwork)
    #
    # Scaling by the artwork's own luminance reproduces the ASTM D4956 ordering almost
    # for free: white sheeting returns 250 cd/lx/m2, red 45, blue 20 - and blue is also
    # the darkest pixel. So a STOP sign's white legend blazes while its red field glows,
    # which is exactly how it reads at night.
    front = mats.createNode("materialbuilder", "SignFrontMat")
    fg, fcol = front.node("surface_globals"), front.node("output_collect")
    tex = front.createNode("texture::2.0", "SignArt")
    tex.parm("map").set('$AB_SIGNS/`details("../../../ReadLibrary", "sign_texture")`')
    lum = front.createNode("luminance", "ArtLuminance")
    lum.setNamedInput("rgb", tex, "clr")
    fnN = front.createNode("normalize", "NormalizeN"); fnN.setNamedInput("vec", fg, "N")
    fnI = front.createNode("normalize", "NormalizeI"); fnI.setNamedInput("vec", fg, "I")
    fdt = front.createNode("dot", "FacingDot")
    fdt.setNamedInput("vec1", fnN, "nvec"); fdt.setNamedInput("vec2", fnI, "nvec")
    fab = front.createNode("abs", "FacingAbs"); fab.setNamedInput("val", fdt, "dotprod")
    fpf = front.createNode("parameter", "Falloff")
    fpf.parm("parmname").set("retrofalloff"); fpf.parm("parmlabel").set("Retro Falloff")
    fpf.parm("parmtype").set("float"); fpf.parm("floatdef").set(2.5)
    fpw = front.createNode("pow", "RetroFalloff")
    fpw.setNamedInput("val", fab, "abs"); fpw.setNamedInput("exp", fpf, "retrofalloff")
    frr = front.createNode("multiply", "RetroByArt")
    frr.setInput(0, fpw, 0); frr.setInput(1, lum, 0)
    fps = front.createNode("principledshader::2.0", "Sheeting")
    fps.setNamedInput("basecolor", tex, "clr")
    fps.setNamedInput("emitcolor", tex, "clr")
    fps.setNamedInput("emitint", frr, "product")
    fps.parm("rough").set(0.25); fps.parm("metallic").set(0.0)
    fcol.setInput(0, fps, 0)
    front.layoutChildren()

    # Galvanised, matching the pole. These maps came out of the HDAs in the 8/14
    # extraction and now live under $AB_TEX.
    back = mats.createNode("principledshader::2.0", "SignBackMat")
    back.parm("basecolor_useTexture").set(1)
    back.parm("basecolor_texture").set("$AB_TEX/Metal_Galvanized_01_basecolor.png")
    back.parm("rough_useTexture").set(1)
    back.parm("rough_texture").set("$AB_TEX/Metal_Galvanized_01_roughness.png")
    back.parm("baseNormal_useTexture").set(1)
    back.parm("baseNormal_texture").set("$AB_TEX/Metal_Galvanized_01_normal.png")
    back.parm("metallic").set(1.0)
    mats.layoutChildren()

    out = sub.createNode("null", "OUT_SIGNLIBRARY")
    out.setInput(0, plate)
    out.setDisplayFlag(True)
    out.setRenderFlag(True)
    outnode = sub.createNode("output", "output0")
    outnode.setInput(0, out)

    sub.setParmTemplateGroup(parm_group())
    sub.layoutChildren()
    return sub


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


def publish(sub=None, path=HDA_PATH):
    sub = sub or hou.node("/obj/SignLibraryDev/SignLibrary")
    asset = sub.createDigitalAsset(
        name=TYPE_NAME, hda_file_name=path, description="AB Sign Library",
        min_num_inputs=0, max_num_inputs=0, ignore_external_references=True)
    d = asset.type().definition()
    d.setParmTemplateGroup(parm_group())     # createDigitalAsset does not do this
    d.addSection("Tools.shelf", TOOLS_SHELF)
    return asset


NODE = build()
