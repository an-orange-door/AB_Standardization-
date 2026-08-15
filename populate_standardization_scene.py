"""Put one instance of every latest-version AB tool into the standardization scene.

    hython U:/AB_Standardization/populate_standardization_scene.py

RUN WITH THE HOUDINI GUI CLOSED. It instantiates ~59 HDAs, and bulk
instantiation in Jordan's live session is what coincided with a drop to Limited
Commercial. Working on the saved .hip headless avoids the live session entirely:
Jordan saves and closes, this writes the next version, he reopens it.

Reads  AB_HDA_STANDARDIZATION_v001.hip
Writes AB_HDA_STANDARDIZATION_v002.hip   (never overwrites the input)

Nodes are grouped into one geo container per category, mirroring Sops/<Category>,
and are created but NOT cooked - some tools are heavy and the point here is
coverage, not evaluation. Display flags are left off so the viewport does not
try to draw 149 assets at once.
"""
import os
import re
import sys

import hou

SRC = "U:/Houdini/AB_HDA_STANDARDIZATION_v001.hip"
DST = "U:/Houdini/AB_HDA_STANDARDIZATION_v002.hip"
LIB = "U:/Git/AssetBashTools"
VER = re.compile(r"^(.*)::(\d+)\.(\d+)$")


def install_library():
    n = 0
    for root, dirs, files in os.walk(LIB):
        r = root.replace("\\", "/") + "/"
        if any(s in r for s in ("/backup/", "/OLD/", "/old/", "/_Archive/", "/.git")):
            continue
        for f in sorted(files):
            if f.lower().endswith((".hda", ".otl")):
                try:
                    hou.hda.installFile(os.path.join(root, f))
                    n += 1
                except Exception:
                    pass
    return n


def latest_types():
    best = {}
    for name, nt in hou.sopNodeTypeCategory().nodeTypes().items():
        if not name.startswith("AB"):
            continue
        d = nt.definition()
        if d is None:
            continue
        p = d.libraryFilePath().replace("\\", "/")
        if "/AssetBashTools/" not in p:
            continue
        cat = p.split("/AssetBashTools/")[-1].split("/")[1]
        m = VER.match(name)
        key, ver = (m.group(1), (int(m.group(2)), int(m.group(3)))) if m else (name, (0, 0))
        if key not in best or ver > best[key][0]:
            best[key] = (ver, name, cat)
    return sorted((n, c) for _, n, c in best.values())


def main():
    print("installed %d library files" % install_library())
    hou.hipFile.load(SRC, suppress_save_prompt=True, ignore_load_warnings=True)
    print("loaded %s" % SRC)

    present = set()
    for n in hou.node("/").allSubChildren():
        try:
            present.add(n.type().name())
        except Exception:
            pass

    targets = [(t, c) for t, c in latest_types() if t not in present]
    print("latest-version tools: %d   already present: %d   to add: %d\n"
          % (len(latest_types()), len(latest_types()) - len(targets), len(targets)))

    obj = hou.node("/obj")
    root = obj.node("AB_LIBRARY") or obj.createNode("subnet", "AB_LIBRARY")
    root.setDisplayFlag(False)

    made, failed = [], []
    by_cat = {}
    for t, c in targets:
        by_cat.setdefault(c, []).append(t)

    for cat in sorted(by_cat):
        geo = root.node(cat) or root.createNode("geo", cat)
        geo.setDisplayFlag(False)
        y = 0
        for t in by_cat[cat]:
            short = t.split("::")[1] if t.count("::") >= 2 else t
            try:
                n = geo.createNode(t, short)
                n.setPosition(hou.Vector2(0, -y * 1.4))
                n.setDisplayFlag(False)
                # colour + comment so the human can see these were generated
                n.setColor(hou.Color(0.35, 0.55, 0.75))
                n.setComment("added by populate_standardization_scene.py")
                made.append(t)
                y += 1
            except Exception as e:
                failed.append((t, str(e)[:110]))
                print("   FAILED %-44s %s" % (t, str(e)[:80]))
                sys.stdout.flush()
        print("   %-18s %d node(s)" % (cat, len(by_cat[cat])))
        sys.stdout.flush()

    hou.hipFile.save(DST)
    print("")
    print("=" * 66)
    print("added   : %d" % len(made))
    print("failed  : %d" % len(failed))
    for t, e in failed:
        print("    %-44s %s" % (t, e))
    print("saved   : %s (%.1f MB)" % (DST, os.path.getsize(DST) / 1048576.0))


if __name__ == "__main__":
    main()
