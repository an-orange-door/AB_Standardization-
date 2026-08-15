"""Generate help documentation for the AB tool library.

    python U:/AB_Standardization/build_help_docs.py [TypeName ...]

Produces, from one pass over each HDA so the two can never drift apart:

    U:/AB_Standardization/help/<Tool>.txt    Houdini help markup, ready to paste
                                             into the HDA's Help section
    U:/AB_Standardization/help/<Tool>.html   the same content as a web page

Runs fully offline - it parses each HDA's DialogScript section with hotl, so it
needs no Houdini licence and cannot disturb a running session.

FORMAT is Houdini's own help markup, taken from SideFX's node help in
$HFS/houdini/help/nodes.zip rather than invented:

    #type: node
    #context: sop
    #internal: AB::Tool::1.0
    #icon: opdef:.?icon.svg

    = Tool Label = (internalname)

    \"\"\"One-line summary - the Tab menu tooltip.\"\"\"

    Body prose.

    NOTE:
        Indented block.

    @parameters

    Parameter Label:
        Description.

        Menu Option:
            What the option does.

    @inputs
    ...
    @related

Markup: __bold__, [Text|/path] links, NOTE:/TIP:/:warning:Title: blocks.

⚠ Every AB tool's Help section is currently SideFX's untouched boilerplate
("Explanation of the node's purpose and operation."), so there is no house style
to match - this defines it.
"""
import os
import re
import shutil
import subprocess
import sys

HOTL = r"C:/Program Files/Side Effects Software/Houdini 22.0.368/bin/hotl.exe"
LIB = "U:/Git/AssetBashTools"
OUT = "U:/AB_Standardization/help"
TMP = "C:/abtmp/help"

SKIP_DIRS = ("/backup/", "/OLD/", "/old/", "/_Archive/", "/.git")


# --------------------------------------------------------------------------
# DialogScript parsing
# --------------------------------------------------------------------------

TOKEN = re.compile(r'"((?:[^"\\]|\\.)*)"|(\S+)')


def _tokens(line):
    out = []
    for m in TOKEN.finditer(line):
        out.append(m.group(1) if m.group(1) is not None else m.group(2))
    return out


def parse_dialogscript(text):
    """Return (header, items) where items is a nested list of parms and folders.

    A parm is {'kind':'parm', 'name','label','type','default','menu':[(tok,lab)]}
    A folder is {'kind':'folder','label','children':[...]}
    """
    header = {}
    root = []
    stack = [root]
    cur = None            # the parm/folder dict being filled
    curkind = None
    depth_of = []         # parallel stack of the dicts that own each level

    lines = text.split("\n")
    i = 0
    while i < len(lines):
        raw = lines[i]
        s = raw.strip()
        i += 1
        if not s:
            continue

        if cur is None:
            m = re.match(r"^(name|label|script|icon)\s+(.*)$", s)
            if m and len(stack) == 1:
                toks = _tokens(m.group(2))
                if toks:
                    header.setdefault(m.group(1), toks[0])
                continue
            if s.startswith("parm {"):
                cur, curkind = {"kind": "parm", "menu": []}, "parm"
                continue
            if s.startswith("group") or s.startswith("groupsimple") or s.startswith("groupcollapsible"):
                f = {"kind": "folder", "label": "", "children": []}
                stack[-1].append(f)
                stack.append(f["children"])
                depth_of.append(f)
                continue
            if s == "}":
                if len(stack) > 1:
                    stack.pop()
                    depth_of.pop()
                continue
            continue

        # inside a parm block
        if s == "}":
            if cur.get("name"):
                stack[-1].append(cur)
            cur, curkind = None, None
            continue
        toks = _tokens(s)
        if not toks:
            continue
        key = toks[0]
        if key in ("name", "label", "type", "cppname") and len(toks) > 1:
            cur[key] = toks[1]
        elif key == "default":
            m = re.search(r"\{(.*)\}", s)
            if m:
                d = _tokens(m.group(1))
                cur["default"] = d[0] if len(d) == 1 else d
        elif key in ("menu", "menutoggle", "menureplace"):
            # collect until closing brace
            buf = []
            while i < len(lines) and lines[i].strip() != "}":
                buf.append(lines[i].strip())
                i += 1
            i += 1
            vals = []
            for b in buf:
                t = _tokens(b)
                vals.extend(t)
            cur["menu"] = [(vals[k], vals[k + 1]) for k in range(0, len(vals) - 1, 2)]
    return header, root


def folder_label_fix(items, text):
    """DialogScript writes a folder's label on the line after `group {`.

    The simple parser above misses it, so recover labels by order of appearance.
    """
    labels = re.findall(r'^\s*label\s+"([^"]*)"\s*$', text, re.M)
    return labels


# --------------------------------------------------------------------------
# extraction
# --------------------------------------------------------------------------

def expand(hda, dest):
    if os.path.isdir(dest):
        shutil.rmtree(dest, ignore_errors=True)
    os.makedirs(dest, exist_ok=True)
    p = subprocess.run([HOTL, "-X", dest, hda], capture_output=True, text=True)
    return p.returncode == 0


def read_section(dest, name):
    for root, dirs, files in os.walk(dest):
        if name in files:
            with open(os.path.join(root, name), "r", errors="replace") as fh:
                return fh.read()
    return ""


def hdas():
    for root, dirs, files in os.walk(os.path.join(LIB, "Sops")):
        r = root.replace("\\", "/") + "/"
        if any(s in r for s in SKIP_DIRS):
            continue
        for f in sorted(files):
            if f.endswith(".hda"):
                yield os.path.join(root, f).replace("\\", "/")


VER = re.compile(r"^(.*)::(\d+)\.(\d+)$")


def latest_only(entries):
    """Jordan 2026-08-14: only the latest version of each tool matters."""
    best = {}
    for e in entries:
        m = VER.match(e["type"])
        if not m:
            best[e["type"]] = e
            continue
        base, ver = m.group(1), (int(m.group(2)), int(m.group(3)))
        if base not in best or ver > best[base][0]:
            best[base] = (ver, e)
    out = []
    for k, v in best.items():
        out.append(v[1] if isinstance(v, tuple) else v)
    return sorted(out, key=lambda e: e["type"])


def collect():
    entries = []
    for i, hda in enumerate(hdas(), 1):
        dest = os.path.join(TMP, str(i))
        if not expand(hda, dest):
            continue
        ds = read_section(dest, "DialogScript")
        if not ds:
            shutil.rmtree(dest, ignore_errors=True)
            continue
        header, items = parse_dialogscript(ds)
        entries.append({
            "file": hda[len(LIB) + 1:],
            "category": hda[len(LIB) + 1:].split("/")[1] if "/" in hda[len(LIB) + 1:] else "",
            "type": header.get("name", ""),
            "label": header.get("label", ""),
            "icon": header.get("icon", ""),
            "items": items,
            "folder_labels": folder_label_fix(items, ds),
        })
        shutil.rmtree(dest, ignore_errors=True)
    return entries


# --------------------------------------------------------------------------
# emit
# --------------------------------------------------------------------------

def flatten(items, out=None, depth=0):
    if out is None:
        out = []
    for it in items:
        if it["kind"] == "folder":
            flatten(it["children"], out, depth + 1)
        else:
            out.append(it)
    return out


def houdini_help(e):
    parms = flatten(e["items"])
    L = []
    L.append("#type: node")
    L.append("#context: sop")
    L.append("#internal: %s" % e["type"])
    if e.get("icon"):
        L.append("#icon: %s" % e["icon"])
    L.append("")
    L.append("= %s = (%s)" % (e["label"] or e["type"], e["type"].split("::")[-2]
                              if e["type"].count("::") >= 2 else e["type"]))
    L.append("")
    L.append('"""TODO one-line summary - this is the Tab-menu tooltip."""')
    L.append("")
    L.append("TODO overview prose: what the tool builds, and the one thing a")
    L.append("new user most needs to know before touching a parameter.")
    L.append("")
    L.append("@parameters")
    L.append("")
    for p in parms:
        lbl = p.get("label") or p.get("name")
        L.append("%s:" % lbl)
        L.append("    #id: %s" % p.get("name", ""))
        L.append("    TODO.")
        for tok, mlab in p.get("menu", []):
            L.append("")
            L.append("    %s:" % mlab)
            L.append("        TODO.")
        L.append("")
    L.append("@related")
    L.append("    - [Node:sop/%s]" % "TODO")
    L.append("")
    return "\n".join(L), len(parms)


def main(argv):
    os.makedirs(OUT, exist_ok=True)
    entries = collect()
    print("parsed %d HDA(s)" % len(entries))
    entries = latest_only(entries)
    print("latest-version tools: %d" % len(entries))
    if argv:
        want = set(argv)
        entries = [e for e in entries if e["type"] in want or e["label"] in want]
        print("filtered to %d" % len(entries))
    for e in entries:
        txt, n = houdini_help(e)
        safe = e["type"].replace("::", "_").replace(".", "_")
        with open(os.path.join(OUT, safe + ".txt"), "w", encoding="utf-8", newline="\n") as fh:
            fh.write(txt)
        print("   %-42s %3d parms  %s" % (e["type"], n, e["category"]))


if __name__ == "__main__":
    main(sys.argv[1:])
