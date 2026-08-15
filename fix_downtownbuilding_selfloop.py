"""Repair the self-referencing nulls in AB::DowntownBuilding::3.6.

    exec(open('U:/AB_Standardization/fix_downtownbuilding_selfloop.py').read())

Symptom: creating the asset fills it with "Infinite recursion in evaluation" and 97
nodes in error. Cause: in
  Classical/ProcessWalls/ProcessWalls/GF_walls/LowerWalls/GroupRanges
two null nodes take THEMSELVES as input, and two other nodes are left dangling:

    GroupedWallsIn1 -> delete3 -> groupdelete3 -> sort1 -> (dead end)
    grouprange1 (self) -> GroupRange1 -> delete2 -> (dead end)
    grouprange2 (self) -> GroupRange2 -> output0

The dead ends and the self-loops fit together exactly one way, which is the chain
restored below. It looks like rename damage - lowercase grouprange1/2 sit beside
PascalCase GroupRange1/2, and the renamed pair kept the wiring while the originals
were left pointing at themselves.

NOT caused by the 2026-08-14 texture repoint. Diffing the asset against the commit
before that change shows five differing files, all texture sections and their
ExtraFileOptions/Sections.list entries; Contents.dir is byte-identical and the
self-loop is present in the earlier version too.

Fixed in place rather than versioned up: 3.6 cannot cook at all, so there is no
working behaviour for anyone to be depending on.
"""
import hou

TYPE_NAME = "AB::DowntownBuilding::3.6"
NET = "Classical/ProcessWalls/ProcessWalls/GF_walls/LowerWalls/GroupRanges"
# node -> the input it should have taken
REWIRE = {"grouprange1": "sort1", "grouprange2": "delete2"}


def fix(parent_path="/obj", geo_name="DTBFixDev"):
    obj = hou.node(parent_path)
    old = obj.node(geo_name)
    if old:
        old.destroy()
    geo = obj.createNode("geo", geo_name)
    node = geo.createNode(TYPE_NAME, "dtb")
    node.allowEditingOfContents()

    net = node.node(NET)
    if not net:
        raise RuntimeError("network not found: " + NET)
    done = []
    for name, src in REWIRE.items():
        n, s = net.node(name), net.node(src)
        if not n or not s:
            continue
        ins = [i.name() if i else None for i in n.inputs()]
        if name in ins:                       # only touch it if it really loops
            n.setInput(0, s)
            done.append("%s <- %s" % (name, src))
    return node, done


def publish(node):
    node.type().definition().updateFromNode(node)
    return node


NODE, DONE = fix()
