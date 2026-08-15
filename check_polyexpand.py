"""Is polyexpand2d (Houdini's native weighted straight skeleton) used anywhere?

The roof research claims it appears in none of the 155 tools. That is a claim
about OUR library, so it is checkable - and it matters, because if Houdini
already ships the core algorithm then the roof work is wiring, not implementing.
"""
import os, collections, hou
LIB="U:/Git/AssetBashTools"
for root,dirs,files in os.walk(LIB):
    r=root.replace("\\","/")+"/"
    if any(s in r for s in ("/backup/","/OLD/","/_Archive/","/.git")): continue
    for f in sorted(files):
        if f.lower().endswith((".hda",".otl")):
            try: hou.hda.installFile(os.path.join(root,f))
            except Exception: pass

WANT = ("polyexpand2d", "straightskeleton", "polyoffset")
best={}
for cat in (hou.sopNodeTypeCategory(), hou.objNodeTypeCategory()):
    for tn, nt in cat.nodeTypes().items():
        d=nt.definition()
        if d is None: continue
        if not (d.libraryFilePath() or "").replace("\\","/").lower().startswith(LIB.lower()):
            continue
        c=nt.nameComponents(); key=(c[1],c[2]); v=c[3] or "0"
        vk=tuple(int(x) if x.isdigit() else 0 for x in str(v).split("."))
        if key not in best or vk > best[key][0]: best[key]=(vk,nt)

print("scanning %d latest-version tools for: %s" % (len(best), ", ".join(WANT)))
holder=hou.node("/obj").createNode("geo","PE")
hits=collections.Counter(); where=collections.defaultdict(list)
for i,(k,(vk,nt)) in enumerate(sorted(best.items()),1):
    parent = holder if nt.category()==hou.sopNodeTypeCategory() else hou.node("/obj")
    try:
        n=parent.createNode(nt.name(),None); n.allowEditingOfContents()
    except Exception: continue
    for c in n.allSubChildren(top_down=True, recurse_in_locked_nodes=True):
        base=c.type().name().split("::")[0]
        if base in WANT:
            hits[base]+=1; where[base].append(nt.name())
    n.destroy()
    if i%40==0: print("  %d/%d" % (i,len(best)))
print()
for w in WANT:
    print("%-18s %d node(s)  in %s" % (w, hits[w],
          ", ".join(sorted(set(where[w]))) if where[w] else "NO TOOL"))
