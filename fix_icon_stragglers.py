"""Eight tools kept their old IconImage reference. Remove the raster section.

⭐ MEASURED CAUSE, and it is not what it looks like: `setIcon()` is IGNORED when
an `IconImage` section exists. Houdini DERIVES the icon from the embedded
section, and **IconImage takes precedence over IconSVG**. Writing the relative
form did nothing; writing the fully-qualified absolute form did nothing either -
`d.icon()` still reported `?IconImage` immediately after the call.
The fix is to delete the stale `IconImage` section, which is also the right
outcome: the SVG is the newer authored art, and the raster is dead weight.
"""
import os, sys, hou
LIB="U:/Git/AssetBashTools"
ICONS=LIB+"/IconDev/Icons"
for root,dirs,files in os.walk(LIB):
    r=root.replace("\\","/")+"/"
    if any(s in r for s in ("/backup/","/OLD/","/_Archive/","/.git")): continue
    for f in sorted(files):
        if f.lower().endswith((".hda",".otl")):
            try: hou.hda.installFile(os.path.join(root,f))
            except Exception: pass

best={}
for cat in (hou.sopNodeTypeCategory(), hou.objNodeTypeCategory()):
    for tn,nt in cat.nodeTypes().items():
        d=nt.definition()
        if d is None: continue
        p=(d.libraryFilePath() or "").replace("\\","/")
        if not p.lower().startswith(LIB.lower()) or "/backup/" in p or "/_Archive/" in p: continue
        c=nt.nameComponents(); k=(c[1],c[2]); v=c[3] or "0"
        vk=tuple(int(x) if x.isdigit() else 0 for x in str(v).split("."))
        if k not in best or vk>best[k][0]: best[k]=(vk,nt,d)

fixed=[]
for (ns,nm),(vk,nt,d) in sorted(best.items()):
    ic=d.icon() or ""
    if not ic.endswith("?IconImage"): continue
    svgp=os.path.join(ICONS,"SOP_AB__%s.svg"%nm)
    if not os.path.isfile(svgp): print("  no svg for %s"%nm); continue
    if os.path.getsize(d.libraryFilePath())/1048576.0 > 3.0: continue
    with open(svgp,encoding="utf-8") as fh: svg=fh.read()
    d.addSection("IconSVG", svg)
    if "IconImage" in d.sections():
        d.removeSection("IconImage")          # <- the operative line
    d.setIcon("opdef:.?IconSVG")
    fixed.append((nm, d.icon()))
print("rewrote %d" % len(fixed))
for n,i in fixed: print("   %-26s %s" % (n,i))
