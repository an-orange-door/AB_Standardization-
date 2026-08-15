"""Full read-only sweep of the AB library. Writes CSVs; changes nothing.

    hython U:/AB_Standardization/analyze_hda_library.py

RUN WITH THE HOUDINI GUI CLOSED - one FX seat.

Latest versions only (Jordan's standing rule).

Five passes, each answering a question we have been answering by hand:

  1 PARMS       every parm, type, default, and menu ordinals.
                Feeds the help docs AND shows where a standards table can
                attach. One parse serves both, so they cannot drift apart.

  2 MENUS       every ordinal menu with its items in order.
                Makes the append-only rule CHECKABLE instead of remembered.
                A future run diffs against this and fails if an item moved.

  3 ORPHANS     ** the new one, and the reason for this sweep **
                The AB.MetalExtrusionMaker Square Tube was broken for years:
                inside add5, pt2y and pt3x were wired to ch("../height") and
                ch("../width") while pt1y and pt2x stayed at a literal 1.0.
                Someone wired two of four and stopped.
                That leaves a fingerprint: within ONE node, parms of the same
                family are part channel-referenced and part literal. Nothing
                about it is specific to Add SOPs, so it is worth sweeping the
                whole library for.
                Reported with a confidence, because a mixed family is
                suspicious, not proof - plenty of nodes legitimately drive one
                component and leave another alone.

  4 NESTING     which tool contains which other AB type.
                Gives blast radius for any edit, and orders the work: fix
                leaves before the tools that embed them.

  5 HEALTH      version staleness, unresolved types, error state.

Nothing here writes to a .hda. It only reads and reports.
"""
import collections
import csv
import os
import re
import sys

import hou

LIB = "U:/Git/AssetBashTools"
OUT = "U:/AB_Standardization/analysis"

SKIP_DIRS = ("/backup/", "/OLD/", "/_Archive/", "/.git", "/otls_old/")

# a trailing component index (pt3x -> pt3, tx -> t) so parms that describe one
# thing land in one family
FAMILY_RE = re.compile(r"^(.*?)(\d*)([xyzw]?)$")


def family_of(name):
    m = FAMILY_RE.match(name)
    if not m:
        return name
    base, idx, axis = m.groups()
    return base + idx if axis else base


def install_all():
    files, n = [], 0
    for root, dirs, fnames in os.walk(LIB):
        r = root.replace("\\", "/") + "/"
        if any(s in r for s in SKIP_DIRS):
            continue
        for f in sorted(fnames):
            if f.lower().endswith((".hda", ".otl")):
                p = os.path.join(root, f)
                try:
                    hou.hda.installFile(p)
                    files.append(p)
                    n += 1
                except Exception:
                    pass
    return n


def latest_defs():
    """One definition per (namespace, name) - the highest version installed."""
    best = {}
    for cat in (hou.sopNodeTypeCategory(), hou.objNodeTypeCategory()):
        for tname, ntype in cat.nodeTypes().items():
            d = ntype.definition()
            if d is None:
                continue
            src = (d.libraryFilePath() or "").replace("\\", "/")
            if not src.lower().startswith(LIB.lower().replace("\\", "/")):
                continue
            comps = ntype.nameComponents()      # (scope, namespace, name, version)
            key = (comps[1], comps[2])
            ver = comps[3] or "0"
            prev = best.get(key)
            if prev is None or _vkey(ver) > _vkey(prev[0]):
                best[key] = (ver, ntype, d)
    return best


def _vkey(v):
    return tuple(int(x) if x.isdigit() else 0 for x in str(v).split("."))


def scan_parms(ntype, w_parms, w_menus):
    tname = ntype.name()
    try:
        ptg = ntype.parmTemplateGroup()
    except hou.Error:
        return
    for pt in ptg.entriesWithoutFolders():
        kind = pt.type().name()
        default = ""
        try:
            dv = pt.defaultValue()
            default = ";".join(str(x) for x in dv) if isinstance(dv, tuple) else str(dv)
        except Exception:
            pass
        menu_n = 0
        try:
            items = list(pt.menuItems() or ())
            labels = list(pt.menuLabels() or ())
            menu_n = len(items)
            for i, it in enumerate(items):
                w_menus.writerow([tname, pt.name(),
                                  i, it, labels[i] if i < len(labels) else ""])
        except Exception:
            pass
        w_parms.writerow([tname, pt.name(), pt.label(), kind,
                          getattr(pt, "numComponents", lambda: 1)(),
                          default, menu_n])


def scan_orphans(node, tname, w):
    """The Square Tube fingerprint: a parm left literal while its siblings got wired.

    Reported PER NODE, not per parm family. In add5 the giveaway was pt2x
    (mixed family, pt2y referenced), but the other half of the bug was pt1y,
    whose whole family is literal and so looks innocent on its own. Once a node
    is suspect, a human needs to see every stale literal on it at once - so the
    family test decides WHETHER to report, and the row then lists ALL of them.

    Two tiers, because a mixed family is suspicious and a lone literal is not:
      high   a parm family is part-referenced, part non-default literal.
             This is the exact Square Tube shape.
      medium the node is parameterised somewhere, and carries non-default
             literals elsewhere. Often legitimate. Triage, not a bug list.
    """
    found = 0
    for c in node.allSubChildren(top_down=True, recurse_in_locked_nodes=True):
        fams = collections.defaultdict(list)
        any_ref = False
        for p in c.parms():
            try:
                expr = p.expression()
                has_ref = "ch(" in expr or "chs(" in expr or "chf(" in expr
            except hou.OperationFailed:
                expr, has_ref = None, False
            any_ref = any_ref or has_ref
            fams[family_of(p.name())].append((p, has_ref))
        if not any_ref:
            continue                       # nothing wired here at all - normal

        literals, refd_names, mixed = [], [], []
        for fam, members in fams.items():
            refd = [m for m in members if m[1]]
            refd_names.extend(m[0].name() for m in refd)
            fam_lits = []
            for p, has_ref in members:
                if has_ref:
                    continue
                try:
                    v = p.eval()
                except Exception:
                    continue
                if not isinstance(v, (int, float)) or isinstance(v, bool):
                    continue
                try:
                    if p.isAtDefault():
                        continue           # untouched, so nobody forgot it
                except Exception:
                    pass
                fam_lits.append((p.name(), v))
            # part wired, part typed-and-left: the Square Tube shape
            if refd and fam_lits and len(members) > 1:
                mixed.append(fam)
            literals.extend(fam_lits)

        if not literals:
            continue
        w.writerow([tname, c.path().split(tname, 1)[-1] or c.name(),
                    c.type().name(), " ".join(sorted(mixed)),
                    len(refd_names), len(literals),
                    "high" if mixed else "medium",
                    " ".join("%s=%g" % (n, v) for n, v in literals),
                    " ".join(sorted(set(refd_names)))])
        found += 1
    return found


def main():
    if not os.path.isdir(OUT):
        os.makedirs(OUT)
    print("installed %d files" % install_all())

    best = latest_defs()
    print("latest-version tools: %d" % len(best))
    sys.stdout.flush()

    f_parms = open(OUT + "/parms.csv", "w", newline="", encoding="utf-8")
    f_menus = open(OUT + "/menus.csv", "w", newline="", encoding="utf-8")
    f_orph = open(OUT + "/orphan_literals.csv", "w", newline="", encoding="utf-8")
    f_nest = open(OUT + "/nesting.csv", "w", newline="", encoding="utf-8")
    f_tools = open(OUT + "/tools.csv", "w", newline="", encoding="utf-8")

    w_parms = csv.writer(f_parms); w_parms.writerow(
        ["tool", "parm", "label", "type", "components", "default", "menu_items"])
    w_menus = csv.writer(f_menus); w_menus.writerow(
        ["tool", "parm", "ordinal", "token", "label"])
    w_orph = csv.writer(f_orph); w_orph.writerow(
        ["tool", "inner_node", "node_type", "parm_family",
         "n_referenced", "n_in_family", "confidence", "literals", "referenced"])
    w_nest = csv.writer(f_nest); w_nest.writerow(
        ["tool", "nests_type", "count"])
    w_tools = csv.writer(f_tools); w_tools.writerow(
        ["tool", "namespace", "name", "version", "category", "file",
         "n_parms", "n_inner_nodes", "n_orphan_flags", "unresolved_types",
         "instantiate_error"])

    holder = hou.node("/obj").createNode("geo", "AnalysisHolder")
    sop_types = set(hou.sopNodeTypeCategory().nodeTypes().keys())

    for i, ((ns, name), (ver, ntype, d)) in enumerate(sorted(best.items()), 1):
        tname = ntype.name()
        scan_parms(ntype, w_parms, w_menus)

        n_inner = n_orph = 0
        unresolved = []
        err = ""
        node = None
        try:
            parent = holder if ntype.category() == hou.sopNodeTypeCategory() else hou.node("/obj")
            node = parent.createNode(tname, "probe_%d" % i)
            node.allowEditingOfContents()
            kids = node.allSubChildren(top_down=True, recurse_in_locked_nodes=True)
            n_inner = len(kids)
            counts = collections.Counter()
            for c in kids:
                ct = c.type().name()
                if ct.startswith(("AB::", "AB.", "AOD::", "AOD.")) or "::" in ct:
                    counts[ct] += 1
                if (c.type().category() == hou.sopNodeTypeCategory()
                        and ct not in sop_types):
                    unresolved.append(ct)
            for ct, n in sorted(counts.items()):
                w_nest.writerow([tname, ct, n])
            n_orph = scan_orphans(node, tname, w_orph)
        except Exception as e:
            err = str(e).split("\n")[0][:120]
        finally:
            if node is not None:
                try:
                    node.destroy()
                except Exception:
                    pass

        try:
            n_parms = len(ntype.parmTemplateGroup().entriesWithoutFolders())
        except Exception:
            n_parms = 0

        w_tools.writerow([tname, ns, name, ver,
                          ntype.category().name(),
                          (d.libraryFilePath() or "").replace("\\", "/"),
                          n_parms, n_inner, n_orph,
                          " ".join(sorted(set(unresolved))), err])
        if i % 20 == 0:
            print("  %d/%d" % (i, len(best))); sys.stdout.flush()

    for f in (f_parms, f_menus, f_orph, f_nest, f_tools):
        f.close()
    print("\nwrote %s/{tools,parms,menus,orphan_literals,nesting}.csv" % OUT)


if __name__ == "__main__":
    main()
