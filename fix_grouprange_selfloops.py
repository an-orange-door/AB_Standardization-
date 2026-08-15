"""Repair the self-referencing GroupRanges nulls in the Classical building tools.

    exec(open('U:/AB_Standardization/fix_grouprange_selfloops.py').read()); run()

Generalises fix_downtownbuilding_selfloop.py, because the same damage turned up a
second time in AB::DestructionBuilding::1.0 - byte-for-byte the same network, the
same two nulls, the same two dangling nodes. Both tools share a Classical branch,
so they almost certainly share an ancestor that was renamed once and copied twice.

The damage, in
  Classical/ProcessWalls/ProcessWalls/GF_walls/LowerWalls/GroupRanges :

    GroupedWallsIn1 -> delete3 -> groupdelete3 -> sort1 -> (dead end)
    grouprange1 (ITSELF)  -> GroupRange1 -> delete2 -> (dead end)
    grouprange2 (ITSELF)  -> GroupRange2 -> output0

The two dead ends and the two self-loops fit together exactly one way, which is
the chain restored below. The tell is lowercase grouprange1/2 sitting beside
PascalCase GroupRange1/2: the renamed pair kept the wiring, the originals were
left pointing at themselves.

Fixed in place rather than versioned up: neither asset can cook at all
(DowntownBuilding 97 nodes in error, DestructionBuilding 103), so there is no
working behaviour for anyone to be depending on.

⚠ DETECTION MUST COMPARE NODE IDENTITY, NOT NAMES. `c.name() in
[i.name() for i in c.inputs()]` reports false positives: a subnet indirect input
resolves to the node feeding the subnet from OUTSIDE, which often shares the
inner node's name. That heuristic flagged HardwareMaker's
Hinges/HingeFancy_001/CreateRivets/subnet4/subnet3/subnet2/transform3, which is
correctly wired and cooks 25,313 prims. Use inputConnections() and compare
inputItem().path().
"""
import hou

NET = "Classical/ProcessWalls/ProcessWalls/GF_walls/LowerWalls/GroupRanges"
REWIRE = {"grouprange1": "sort1", "grouprange2": "delete2"}

TYPES = [
    # Nothing to run. Kept because the repair is documented and reusable if the
    # damage shows up a third time.
    #
    # "AB::DowntownBuilding::3.6"     already fixed + committed in 64860dc
    # "AB::DestructionBuilding::1.0"  NOT to be fixed - Jordan 2026-08-14:
    #     "Destruction building is totally broken, don't worry about that".
    #     Repairing these two wires would clear the 103 cook errors but the tool
    #     is unusable for other reasons, so it is out of scope for the release.
]


def self_loops(node):
    """Real self-loops only - identity, not name. See the header warning."""
    out = []
    for c in node.allSubChildren():
        for conn in c.inputConnections():
            item = conn.inputItem()
            if isinstance(item, hou.Node) and item.path() == c.path():
                out.append(c.path())
    return out


def fix_one(type_name, parent_path="/obj"):
    obj = hou.node(parent_path)
    holder = obj.node("SLFix")
    if holder:
        holder.destroy()
    holder = obj.createNode("geo", "SLFix")
    node = holder.createNode(type_name, "n")
    node.allowEditingOfContents()

    before = self_loops(node)
    net = node.node(NET)
    if not net:
        raise RuntimeError("network not found in %s: %s" % (type_name, NET))

    done = []
    for name, src in REWIRE.items():
        n, s = net.node(name), net.node(src)
        if not n or not s:
            continue
        looped = any(isinstance(c.inputItem(), hou.Node)
                     and c.inputItem().path() == n.path()
                     for c in n.inputConnections())
        if looped:                       # only touch it if it really loops
            n.setInput(0, s)
            done.append("%s <- %s" % (name, src))

    after = self_loops(node)
    return holder, node, before, done, after


def publish(node):
    node.type().definition().updateFromNode(node)


def verify_from_disk(type_name, parent_path="/obj"):
    """Reload the definition off disk, then re-test. Proves the FILE is fixed.

    An in-memory definition can carry a fix that never reached the file - that
    happened once already - so nothing counts as verified until it survives a
    reload.
    """
    path = hou.sopNodeTypeCategory().nodeTypes()[type_name].definition() \
              .libraryFilePath()
    hou.hda.reloadFile(path)
    obj = hou.node(parent_path)
    holder = obj.node("SLVerify")
    if holder:
        holder.destroy()
    holder = obj.createNode("geo", "SLVerify")
    node = holder.createNode(type_name, "n")
    try:
        node.cook(force=True)
        prims, cook_err = len(node.geometry().prims()), None
    except hou.Error as e:
        prims, cook_err = -1, str(e).replace("\n", " ")[:120]
    node.allowEditingOfContents()
    result = {"path": path, "prims": prims, "cook_error": cook_err,
              "self_loops": self_loops(node),
              "nodes_in_error": len([c for c in node.allSubChildren()
                                     if c.errors()])}
    holder.destroy()
    return result


def run():
    report = []
    for t in TYPES:
        holder, node, before, done, after = fix_one(t)
        publish(node)
        holder.destroy()
        report.append((t, before, done, after, verify_from_disk(t)))
    return report
