"""Read the MetalExtrusionMaker network before changing it. Reports only."""
import os, hou
LIB="U:/Git/AssetBashTools"
for root,dirs,files in os.walk(LIB):
    r=root.replace("\\","/")+"/"
    if any(s in r for s in ("/backup/","/OLD/","/_Archive/","/.git")): continue
    for f in sorted(files):
        if f.lower().endswith((".hda",".otl")):
            try: hou.hda.installFile(os.path.join(root,f))
            except Exception: pass
g=hou.node("/obj").createNode("geo","insp")
n=g.createNode("AB::MetalExtrusionMaker::2.0","m"); n.allowEditingOfContents()
print("top-level children of the HDA:")
for c in n.children():
    ins=[i.name() if i else "-" for i in c.inputs()]
    outs=[o.name() for o in c.outputs()]
    print("   %-24s %-22s in=%-34s out=%s"
          % (c.name(), c.type().name(), ",".join(ins)[:34], ",".join(outs)[:40]))
print()
for sw in n.children():
    if sw.type().name()=="switch":
        print("SWITCH %s  index parm = %r" % (sw.name(), sw.parm("input").rawValue()))
        for i,inp in enumerate(sw.inputs()):
            print("    %d <- %s" % (i, inp.name() if inp else "(none)"))
print()
d=n.type().definition()
print("display/render flagged node:",
      [c.name() for c in n.children() if c.isDisplayFlagSet()])
print("output nodes:", [c.name() for c in n.children() if c.type().name()=="output"])
