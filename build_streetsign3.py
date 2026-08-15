"""Cut AB::StreetSignGenerator::3.0 from 2.0. Run inside Houdini:

    exec(open('U:/AB_Standardization/build_streetsign3.py').read())
    exec(open('U:/AB_Standardization/build_streetsign3.py').read()); publish()

3.0 keeps everything 2.0 got right - the pole system, the bbox-driven height solve,
the bolt hardware, the second-sign chain - and replaces the sign faces with
AB::SignLibrary.

A NEW VERSION, not an edit of 2.0. The parameter interface changes incompatibly
(the six-groups-of-four integer picker is gone), so existing scenes must keep
resolving 2.0. Houdini compares versions numerically and unversioned creation takes
the highest, so 3.0 becomes the default for new nodes while old scenes are untouched.

Removed:
  CreateSignGraphics   2,220 nodes, 72% of the asset - the hand-built sign faces
  mats/AB_RoadSigns_*  the 10 atlas shaders, referenced only from that branch
  ImageProcessing      a SignMaker leftover; verified referenced by NOTHING, and
                       its one node still carried the dead name
                       SignMaker__4_8_Metal_RuggedIron_2k_s_tga
Kept:
  mats/Metal_Galvanized_01   the pole material, used by both pole branches
  mats/Wood_01, Concrete_01  unreferenced but PoleWithStand is work in progress
"""
import hou

SRC_TYPE  = "AB::StreetSignGenerator::2.0"
TYPE_NAME = "AB::StreetSignGenerator::3.0"
HDA_PATH  = "U:/Git/AssetBashTools/Sops/CityProps/AB.StreetSignGenerator.3.0.hda"
SUBMENU   = "Asset Bash/Signs"
LIB_DEFAULT = "$ASSETBASH/config/signs_library.csv"

SETS = ("Any", "Highway_Signs_US", "Highway_Signs_International",
        "Symbol_Signs_Recreational", "Symbol_Signs_Transportation_01",
        "Symbol_Signs_Transportation_02", "International_Icons_Electronic_Labeling")
SET_LABELS = ("Any set", "US Highway", "Intl Highway", "Recreational",
              "Transportation 1", "Transportation 2", "Electronic")
SHAPES = ("Any", "Rectangle", "Circle", "Ellipse", "Diamond", "Triangle",
          "Octagon", "Traced", "Pictogram")

# Parameters of the old picker. Twenty-four addressable signs, chosen by integer.
DEAD_PARMS = (["PrimarySignGroup"] + ["PrimarySignType%d" % i for i in range(1, 7)] +
              ["SecondSignGroup"] + ["SecondSignType%d" % i for i in range(1, 7)])

MENU_TMPL = '''
import csv, hou
node = kwargs["node"]
try:
    path = hou.text.expandString(node.evalParm("LibraryFile"))
    want_set = node.evalParm("%(p)sSet")
    want_shape = node.evalParm("%(p)sShape")
    out = []
    with open(path, encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            if want_set != "Any" and r["set"] != want_set:
                continue
            if want_shape != "Any" and r["shape"] != want_shape:
                continue
            if r["is_decal"] == "1":
                continue
            out.extend([r["code"], "%%s   [%%s]" %% (r["name"], r["set_label"])])
    return out or ["", "(no signs match this filter)"]
except Exception as e:
    return ["", "ERROR: %%s" %% e]
'''


def sign_folder(label, prefix, default_code):
    f = hou.FolderParmTemplate(prefix + "Folder", label)
    s = hou.StringParmTemplate(prefix + "Set", "Set", 1, ("Any",))
    s.setMenuItems(SETS); s.setMenuLabels(SET_LABELS)
    f.addParmTemplate(s)
    sh = hou.StringParmTemplate(prefix + "Shape", "Shape", 1, ("Any",))
    sh.setMenuItems(SHAPES); sh.setMenuLabels(SHAPES)
    f.addParmTemplate(sh)
    sg = hou.StringParmTemplate(prefix + "Sign", "Sign", 1, (default_code,))
    sg.setItemGeneratorScript(MENU_TMPL % {"p": prefix})
    sg.setItemGeneratorScriptLanguage(hou.scriptLanguage.Python)
    f.addParmTemplate(sg)
    return f


def fork_version():
    """Copy 2.0's definition to a new 3.0 file and install it.

    createDigitalAsset() refuses to run on a node that is already an HDA instance
    ("The specified node cannot be converted to a digital asset"), so a new version
    is forked from the DEFINITION and then edited in place.
    """
    src = hou.sopNodeTypeCategory().nodeTypes()[SRC_TYPE].definition()
    src.copyToHDAFile(HDA_PATH, new_name=TYPE_NAME, new_menu_name="AB Street Signs")
    hou.hda.installFile(HDA_PATH)


def apply_interface():
    """Swap the picker for library selection, ON THE DEFINITION.

    Order matters: this runs before any instance exists, so the internal
    chs("../../PrimarySign") expressions have something to bind to. Editing an HDA
    instance's template group does not reach the definition - the old parms come
    back on every new node.
    """
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
        ptg.append(sign_folder("Primary Sign", "Primary", "X01A01"))      # Stop
    if not ptg.find("SecondarySign"):
        ptg.append(sign_folder("Secondary Sign", "Secondary", "X01A03"))  # 4-Way plaque
    if not ptg.find("SignThickness"):
        ptg.append(hou.FloatParmTemplate("SignThickness", "Sign Thickness", 1,
                                         (0.004,), min=0.001, max=0.05))
    d.setParmTemplateGroup(ptg)


def build(parent_path="/obj", geo_name="StreetSign3Dev"):
    fork_version()
    apply_interface()
    obj = hou.node(parent_path)
    old = obj.node(geo_name)
    if old:
        old.destroy()
    geo = obj.createNode("geo", geo_name)
    node = geo.createNode(TYPE_NAME, "StreetSign3")
    node.allowEditingOfContents()

    # --- strip the hand-built sign machinery -----------------------------------
    removed = []
    for nm in ("CreateSignGraphics", "ImageProcessing"):
        n = node.node(nm)
        if n:
            removed.append("%s (%d nodes)" % (nm, len(n.allSubChildren()) + 1))
            n.destroy()
    mats = node.node("mats")
    for c in list(mats.children()):
        nm = c.name()                     # read before destroy; the object goes stale
        if nm.startswith("AB_RoadSigns"):
            c.destroy()
            removed.append("mats/" + nm)

    ss = node.node("StreetSign")
    for nm in ("object_merge4", "object_merge5"):
        n = ss.node(nm)
        if n:
            n.destroy()
            removed.append("StreetSign/" + nm)

    # --- sign faces now come from the library ----------------------------------
    prim = ss.createNode("AB::SignLibrary::1.0", "PrimarySignLib")
    sec = ss.createNode("AB::SignLibrary::1.0", "SecondarySignLib")
    for lib, prefix in ((prim, "Primary"), (sec, "Secondary")):
        lib.parm("LibraryFile").setExpression('chs("../../LibraryFile")')
        lib.parm("SetFilter").setExpression('chs("../../%sSet")' % prefix)
        lib.parm("ShapeFilter").setExpression('chs("../../%sShape")' % prefix)
        lib.parm("Sign").setExpression('chs("../../%sSign")' % prefix)
        lib.parm("Thickness").setExpression('ch("../../SignThickness")')
        # Width is left alone so the real MUTCD size out of the CSV comes through.

    ss.node("SignIn").setInput(0, prim)
    ss.node("transform4").setInput(0, sec)
    ss.layoutChildren()

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
    node = node or hou.node("/obj/StreetSign3Dev/StreetSign3")
    d = node.type().definition()
    d.updateFromNode(node)               # bake the edited contents into 3.0

    # The old picker parms come from the DEFINITION, so removing them from an instance
    # does nothing - they reappear on every node. Strip them from the definition.
    d.addSection("Tools.shelf", TOOLS_SHELF)
    # 2.0 carried a stale viewer-state section from the SignMaker split
    for dead in ("ViewerStateName.orig",):
        if dead in d.sections():
            d.removeSection(dead)
    return node


NODE, REMOVED = build()
