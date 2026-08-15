"""Cut AB::SignHighway::2.0 from 1.0, and fix the filename/type mismatch.

    exec(open('U:/AB_Standardization/build_signhighway2.py').read()); publish()

The asset shipped as AB.SignHighway.2.0.hda while defining type AB::SignHighway::1.0 -
tracker item AB-008. Renaming the file to match the type is the non-breaking half of the
fix: HighwaySignGenerator 4.9 references the TYPE, so it keeps resolving. 2.0 is then a
genuine new version carrying the correction below, and only 5.0 points at it.

Fixes 'LightCasing ' - the name attribute carried a TRAILING SPACE, which becomes a USD
prim name and an Unreal component name. It is written once and matched in four more
places, so all five have to move together or the material and colour assignments silently
stop matching.

Not fixed here: SignPlatformMetal is 5,708 prims and the single largest remaining block.
It is built by foreach loops, and for-each output never shares geometry, so it cannot be
instanced without restructuring that section onto CopyToPoints with Pack and Instance.
That is a rework, not a toggle, and is left as a deliberate decision rather than a
drive-by change to a 170-node flat network.
"""
import os
import hou

SRC_TYPE  = "AB::SignHighway::1.0"
TYPE_NAME = "AB::SignHighway::2.0"
OLD_FILE  = "U:/Git/AssetBashTools/Sops/CityProps/AB.SignHighway.2.0.hda"
FILE_1_0  = "U:/Git/AssetBashTools/Sops/CityProps/AB.SignHighway.1.0.hda"
HDA_PATH  = OLD_FILE          # 2.0 reclaims the name it was already using

BAD = "LightCasing "          # note the trailing space
GOOD = "LightCasing"


def rename_1_0():
    """Give type 1.0 a filename that matches it, so 4.9 keeps resolving."""
    if os.path.exists(OLD_FILE) and not os.path.exists(FILE_1_0):
        d = hou.sopNodeTypeCategory().nodeTypes()[SRC_TYPE].definition()
        d.copyToHDAFile(FILE_1_0)          # same type name, correct filename
        hou.hda.installFile(FILE_1_0)


def fix_names(node):
    """Strip the trailing space everywhere it is written or matched."""
    fixed = []
    for c in node.allSubChildren():
        for p in c.parms():
            try:
                v = p.eval()
            except Exception:
                continue
            if isinstance(v, str) and BAD in v:
                p.set(v.replace(BAD, GOOD))
                fixed.append("%s.%s" % (c.name(), p.name()))
    return fixed


def build(parent_path="/obj", geo_name="SignHighway2Dev"):
    rename_1_0()
    src = hou.sopNodeTypeCategory().nodeTypes()[SRC_TYPE].definition()
    src.copyToHDAFile(HDA_PATH, new_name=TYPE_NAME,
                      new_menu_name="AB Highway Sign Single")
    hou.hda.installFile(HDA_PATH)

    obj = hou.node(parent_path)
    old = obj.node(geo_name)
    if old:
        old.destroy()
    geo = obj.createNode("geo", geo_name)
    node = geo.createNode(TYPE_NAME, "SignHighway2")
    node.allowEditingOfContents()
    fixed = fix_names(node)
    return node, fixed


def publish(node=None):
    node = node or hou.node("/obj/SignHighway2Dev/SignHighway2")
    node.type().definition().updateFromNode(node)
    return node


NODE, FIXED = build()
