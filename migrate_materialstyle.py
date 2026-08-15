"""Make MaterialStyle uniform across every AB tool: Principled | Unreal | USD.

    hython U:/AB_Standardization/migrate_materialstyle.py

RUN WITH THE HOUDINI GUI CLOSED. This instantiates ~46 HDAs; doing that in
Jordan's live session is what coincided with a drop to Limited Commercial on
2026-08-14, and there is only one FX seat.

Jordan's call (2026-08-14): "everything should be the same and if something
breaks we will fix it." So this normalises all 46 tools rather than protecting
the three whose indices shift.

THE CONTRACT each tool must satisfy afterwards:

    0  Principled   shop_materialpath present, no unreal_material
    1  Unreal       unreal_material present, no shop_materialpath
    2  USD          neither - zones only, because Solaris assignmaterial keys
                    off s@name and target-specific attributes leak into USD as
                    primvars if left in

HOW: one attribdelete at the tool's output, driven by a single expression
rather than a third input on every internal switch:

    primdel = ifs(MaterialStyle == 2, "shop_materialpath unreal_material",
              ifs(MaterialStyle == 1, "shop_materialpath", "unreal_material"))

This enforces the contract no matter what the tool's internals do - EXCEPT when
the internal switch order disagrees with the canonical order, which stripping
cannot repair. Known case: WaterTankGenerator 2.0 is genuinely None|Principled|
Unreal, so its switch needs remapping too (REMAP below). "Unity" was never
implemented anywhere - those switches have only two inputs, so Houdini clamped
index 2 to Unreal.

Everything is verified by COOKING each tool at each value and reading the prim
attributes. A green cook proves nothing; several bugs today looked fine and did
nothing.
"""
import os
import sys
import traceback

import hou

LIB = "U:/Git/AssetBashTools"
CANON = ("Principled", "Unreal", "USD")

# tools whose internal switch order does not match the canonical order.
# value = expression remapping canonical index -> the tool's own input index
REMAP = {
    # genuine None|Principled|Unreal: canonical 0->1, 1->2, 2->0
    "AB::WaterTankGenerator::2.0":
        'if(ch("../MaterialStyle") == 0, 1, if(ch("../MaterialStyle") == 1, 2, 0))',
}

STRIP_EXPR = ('ifs(ch("../MaterialStyle") == 2, "shop_materialpath unreal_material", '
              'ifs(ch("../MaterialStyle") == 1, "shop_materialpath", "unreal_material"))')


def install_library():
    n = 0
    for root, dirs, files in os.walk(LIB):
        r = root.replace("\\", "/") + "/"
        if any(s in r for s in ("/backup/", "/OLD/", "/_Archive/", "/.git")):
            continue
        for f in sorted(files):
            if f.lower().endswith((".hda", ".otl")):
                try:
                    hou.hda.installFile(os.path.join(root, f))
                    n += 1
                except Exception:
                    pass
    return n


def targets():
    out = []
    for name, nt in hou.sopNodeTypeCategory().nodeTypes().items():
        if not name.startswith("AB"):
            continue
        d = nt.definition()
        if d is None:
            continue
        if "/AssetBashTools/" not in d.libraryFilePath().replace("\\", "/"):
            continue
        try:
            if d.parmTemplateGroup().find("MaterialStyle") is None:
                continue
        except Exception:
            continue
        out.append(name)
    return sorted(out)


def find_output(node):
    """The tool's terminal node: an output SOP, else the display node."""
    outs = [c for c in node.children() if c.type().name() == "output"]
    if outs:
        outs.sort(key=lambda c: c.parm("outputidx").eval() if c.parm("outputidx") else 0)
        return outs[0]
    return node.displayNode()


def set_menu(defn):
    ptg = defn.parmTemplateGroup()
    t = ptg.find("MaterialStyle")
    before = list(t.menuLabels())
    if before == list(CANON):
        return before, False
    t.setMenuItems(tuple(str(i) for i in range(len(CANON))))
    t.setMenuLabels(CANON)
    ptg.replace("MaterialStyle", t)
    defn.setParmTemplateGroup(ptg)
    return before, True


def migrate(name, holder):
    defn = hou.sopNodeTypeCategory().nodeTypes()[name].definition()
    before, changed = set_menu(defn)

    node = holder.createNode(name, "m")
    node.allowEditingOfContents()

    out = find_output(node)
    if out is None:
        node.destroy()
        return before, "NO OUTPUT NODE - skipped"

    strip = node.node("MaterialStyleStrip")
    if strip is None:
        src = out.inputs()[0] if out.inputs() else None
        if src is None:
            node.destroy()
            return before, "output has no input - skipped"
        strip = node.createNode("attribdelete", "MaterialStyleStrip")
        strip.setInput(0, src)
        out.setInput(0, strip)
    strip.parm("primdel").setExpression(STRIP_EXPR)

    # only where the tool's own switch order disagrees with canonical
    if name in REMAP:
        for c in node.allSubChildren():
            if not c.type().name().startswith("switch"):
                continue
            p = c.parm("input")
            try:
                ex = p.expression()
            except hou.OperationFailed:
                continue
            if "MaterialStyle" in ex:
                p.setExpression(REMAP[name])

    defn.updateFromNode(node)
    node.destroy()
    return before, "migrated"


def verify(name, holder):
    """Cook at each value and read what actually comes out."""
    node = holder.createNode(name, "v")
    rows = []
    try:
        for v, want in enumerate(CANON):
            node.parm("MaterialStyle").set(v)
            try:
                node.cook(force=True)
                g = node.geometry()
                prim = {a.name() for a in g.primAttribs()}
                got = ("Principled" if "shop_materialpath" in prim
                       else "Unreal" if "unreal_material" in prim else "USD")
                rows.append((v, want, got, got == want))
            except hou.Error as e:
                rows.append((v, want, "COOK ERROR: %s" % str(e).replace("\n", " ")[:50], False))
    finally:
        node.destroy()
    return rows


def main():
    print("installed %d files" % install_library())
    names = targets()
    print("tools carrying MaterialStyle: %d\n" % len(names))

    holder = hou.node("/obj").createNode("geo", "MSMigrate")
    ok, failed, mismatched = [], [], []
    try:
        for i, name in enumerate(names, 1):
            try:
                before, status = migrate(name, holder)
                rows = verify(name, holder) if status == "migrated" else []
                bad = [r for r in rows if not r[3]]
                flag = "OK" if (rows and not bad) else ("MISMATCH" if bad else status)
                print("[%2d/%d] %-42s %-9s %s" % (i, len(names), name, flag, before))
                for v, want, got, good in bad:
                    print("            %d wanted %-11s got %s" % (v, want, got))
                if bad:
                    mismatched.append(name)
                elif rows:
                    ok.append(name)
                sys.stdout.flush()
            except Exception as e:
                failed.append((name, str(e)[:120]))
                print("[%2d/%d] %-42s EXCEPTION %s" % (i, len(names), name, str(e)[:80]))
                traceback.print_exc()
                sys.stdout.flush()
    finally:
        holder.destroy()

    print("")
    print("=" * 70)
    print("clean        : %d" % len(ok))
    print("mismatched   : %d  %s" % (len(mismatched), mismatched))
    print("exceptions   : %d" % len(failed))
    for n, e in failed:
        print("    %-42s %s" % (n, e))


if __name__ == "__main__":
    main()
