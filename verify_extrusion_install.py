"""Prove the SAVED tool still matches the backup. Reports only; writes nothing.

    hython U:/AB_Standardization/verify_extrusion_install.py <old|new> <out.json>
    (run twice, then diff)

The parity test compared a scratch wrangle against the HDA's internal nulls.
That is no longer the question. The question now is whether the tool AS SAVED,
instantiated FRESH, still produces what 2.0 produced - measured at the tool's
real output, after SwitchAxis / SwitchPlacement / the bevel branch, because
those are what an existing scene actually sees.

Fresh instance matters: the install ran on a live node I had edited. A
definition can be saved from a working node and still be broken when
instantiated (that is exactly how copyToHDAFile shipped an empty asset), so the
only honest test creates a new one from the file on disk.
"""
import itertools
import json
import os
import sys

import hou

LIB = "U:/Git/AssetBashTools"
TYPE = "AB::MetalExtrusionMaker::2.0"
BACKUP = "U:/AB_Standardization/_backup_20260815/AB.MetalExtrusionMaker.2.0.hda"


def install_all(skip=None):
    """skip: a filename to leave out.

    ⚠ Installing a SECOND file that defines the same type does NOT override the
    first - the initial run of this script reported the repo definition for both
    passes, which would have made the comparison meaningless. So the only
    reliable way to test the old definition is to never install the new one.
    """
    for root, dirs, files in os.walk(LIB):
        r = root.replace("\\", "/") + "/"
        if any(s in r for s in ("/backup/", "/OLD/", "/_Archive/", "/.git")):
            continue
        for f in sorted(files):
            if skip and f.lower() == skip.lower():
                continue
            if f.lower().endswith((".hda", ".otl")):
                try:
                    hou.hda.installFile(os.path.join(root, f))
                except Exception:
                    pass


def main():
    which, outp = sys.argv[1], sys.argv[2]
    if which == "old":
        install_all(skip="AB.MetalExtrusionMaker.2.0.hda")
        hou.hda.installFile(BACKUP)
    else:
        install_all()
    src = hou.nodeType(hou.sopNodeTypeCategory(), TYPE).definition().libraryFilePath()
    print("using definition from: %s" % src)

    holder = hou.node("/obj").createNode("geo", "Verify")
    out = {}
    widths = (1.0, 0.35, 2.5)
    heights = (1.0, 0.6, 3.0)
    thicks = (0.1, 0.02, 0.25)

    for etype in range(5):                       # only 0-4 exist in the backup
        for W, H, t in itertools.product(widths, heights, thicks):
            for ax in (0, 1):                    # exercise SwitchAxis too
                n = holder.createNode(TYPE, None)  # FRESH instance every time
                for p, v in (("ext_type", etype), ("width", W), ("height", H),
                             ("thick", t), ("axis", ax)):
                    if n.parm(p) is not None:
                        n.parm(p).set(v)
                try:
                    n.cook(force=True)
                    g = n.geometry()
                    key = "%d|%g|%g|%g|%d" % (etype, W, H, t, ax)
                    out[key] = [[round(c, 5) for c in p.position()]
                                for p in g.points()]
                except hou.Error as e:
                    out["%d|%g|%g|%g|%d" % (etype, W, H, t, ax)] = \
                        "ERROR " + str(e).split("\n")[0][:60]
                n.destroy()

    with open(outp, "w", encoding="utf-8") as f:
        json.dump(out, f)
    print("wrote %s  (%d cases)" % (outp, len(out)))


if __name__ == "__main__":
    main()
