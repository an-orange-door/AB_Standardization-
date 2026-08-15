"""Install the authored SVG icons onto every AB tool that lacks one.

    hython U:/AB_Standardization/install_icons.py [--apply]

RUN WITH THE HOUDINI GUI CLOSED - one FX seat.
Without --apply this is a dry run and writes nothing.

153 of 192 tools sat on the stock SOP_subnet icon while 150 finished icons went
unused in IconDev/Icons. This is the "128 identical rows" bulk job from the
tracker: one script, not 128 decisions.

MECHANISM - copied from the 16 tools that already work, not invented:
    definition.addSection("IconSVG", <svg text>)
    definition.setIcon("opdef:.?IconSVG")
The icon travels INSIDE the .hda, so a customer needs no env var and no install
step - the same reasoning that put the config tables in the repo rather than in
Houdini's preset system.

⚠ SIZE GUARD - the reason this script has a threshold at all.
Git LFS stores WHOLE FILES, not deltas, so re-saving an .hda to add a 2 KB icon
costs its ENTIRE size in the remote, forever. AB.CrystalGenerator.1.0.hda is
276 MB of embedded data. Adding an icon to it would push 276 MB to pay for
2 KB. Anything over MAX_MB is skipped and reported instead - those need their
embedded payload extracted first (the texture-extraction work is what made the
other 150 affordable).

Undo is git: the icon is one section, and `git checkout -- <file>` restores it.
"""
import os
import re
import sys

import hou

LIB = "U:/Git/AssetBashTools"
ICONS = LIB + "/IconDev/Icons"
MAX_MB = 3.0
APPLY = "--apply" in sys.argv

SKIP_DIRS = ("/backup/", "/OLD/", "/_Archive/", "/.git")
LEGACY_ICON = re.compile(r"^(AOD-HO-|AB-HO-).*\.svg$", re.I)


def install_all():
    for root, dirs, files in os.walk(LIB):
        r = root.replace("\\", "/") + "/"
        if any(s in r for s in SKIP_DIRS):
            continue
        for f in sorted(files):
            if f.lower().endswith((".hda", ".otl")):
                try:
                    hou.hda.installFile(os.path.join(root, f))
                except Exception:
                    pass


def latest():
    best = {}
    for cat in (hou.sopNodeTypeCategory(), hou.objNodeTypeCategory()):
        for tn, nt in cat.nodeTypes().items():
            d = nt.definition()
            if d is None:
                continue
            p = (d.libraryFilePath() or "").replace("\\", "/")
            if not p.lower().startswith(LIB.lower()):
                continue
            if any(s in p for s in SKIP_DIRS):
                continue
            c = nt.nameComponents()
            key = (c[1], c[2])
            v = c[3] or "0"
            vk = tuple(int(x) if x.isdigit() else 0 for x in str(v).split("."))
            if key not in best or vk > best[key][0]:
                best[key] = (vk, nt, d)
    return best


def main():
    install_all()
    tools = latest()
    print("mode: %s" % ("APPLY" if APPLY else "DRY RUN (pass --apply to write)"))
    print("latest-version tools: %d\n" % len(tools))

    done = skipped_big = no_icon = already = failed = 0
    big, missing, errs = [], [], []

    for (ns, name), (vk, nt, d) in sorted(tools.items()):
        svg_path = os.path.join(ICONS, "SOP_AB__%s.svg" % name)
        if not os.path.isfile(svg_path):
            no_icon += 1
            missing.append(name)
            continue

        f = d.libraryFilePath()
        mb = os.path.getsize(f) / 1048576.0
        if mb > MAX_MB:
            skipped_big += 1
            big.append((name, mb))
            continue

        try:
            with open(svg_path, encoding="utf-8") as fh:
                svg = fh.read()
            sections = d.sections()
            had = "IconSVG" in sections and d.icon() == "opdef:.?IconSVG"

            if APPLY:
                d.addSection("IconSVG", svg)
                d.setIcon("opdef:.?IconSVG")
                # drop leftovers from the pre-rename naming, which otherwise sit
                # in the file forever as dead weight
                for s in list(d.sections().keys()):
                    if LEGACY_ICON.match(s):
                        d.removeSection(s)
            if had:
                already += 1
            else:
                done += 1
        except Exception as e:
            failed += 1
            errs.append((name, str(e).split("\n")[0][:70]))

    print("installed / would install : %d" % done)
    print("already correct           : %d" % already)
    print("skipped, file > %.0f MB     : %d" % (MAX_MB, skipped_big))
    for n, mb in sorted(big, key=lambda x: -x[1]):
        print("      %-34s %7.1f MB  <- extract its payload first" % (n, mb))
    print("no matching SVG           : %d" % no_icon)
    for n in missing[:12]:
        print("      %s" % n)
    if errs:
        print("FAILED                    : %d" % failed)
        for n, e in errs:
            print("      %-30s %s" % (n, e))

    if not APPLY:
        return 0

    # ---- verify on FRESH instances, never on the definitions we just wrote ----
    print("\nverifying fresh instances...")
    holder = hou.node("/obj").createNode("geo", "IconCheck")
    bad = []
    checked = 0
    for (ns, name), (vk, nt, d) in sorted(tools.items()):
        if not os.path.isfile(os.path.join(ICONS, "SOP_AB__%s.svg" % name)):
            continue
        if os.path.getsize(d.libraryFilePath()) / 1048576.0 > MAX_MB:
            continue
        fresh = hou.nodeType(nt.category(), nt.name())
        icon = fresh.definition().icon()
        checked += 1
        if icon != "opdef:.?IconSVG":
            bad.append((name, icon))
    print("checked %d, wrong icon: %d" % (checked, len(bad)))
    for n, i in bad[:10]:
        print("      %-30s %s" % (n, i))
    return 0


if __name__ == "__main__":
    sys.exit(main())
