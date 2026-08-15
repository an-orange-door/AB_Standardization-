"""Find nodes wired to THEMSELVES in every AB HDA - fully offline, no licence.

    python U:/AB_Standardization/scan_selfloops.py

Background: AB::DowntownBuilding::3.6 could not cook at all - 97 nodes reporting
"Infinite recursion in evaluation" - because two null nodes in
Classical/ProcessWalls/.../GroupRanges took themselves as input. It looked like
rename damage: lowercase grouprange1/2 sat beside PascalCase GroupRange1/2, and
the renamed pair kept the wiring while the originals were left pointing at
themselves. Five other building tools were versioned up in the same batch and
were never checked.

Why offline: the obvious check is to instance every HDA and walk allSubChildren(),
but bulk-instantiating ~149 types in Jordan's live session coincided with Houdini
dropping to Limited Commercial (one FX seat). hotl -X needs no licence and cannot
disturb a running session.

How it works: an expanded HDA stores each node's wiring in its own .def file:

    inputs
    {
    0 	switch1 0 1
    }

fields being <input index> <source node> <source output> <flag>. A self-loop is
simply a row whose source name equals the node's own name.

MAX_PATH: hotl -X silently drops files past the Windows limit and still exits 0,
so everything expands under a deliberately short root and the node count is
checked against the expansion.

⚠ THE CASE-COLLISION FALSE POSITIVE - the reason this script has a second pass.
Windows filenames are case-insensitive. DowntownBuilding's GroupRanges network
holds BOTH `grouprange1` and `GroupRange1`, so hotl writes GroupRange1.def on top
of grouprange1.def and only one survives - under the *first* name written. The
surviving content is GroupRange1's, whose input genuinely IS `grouprange1`, so a
naive reader sees "node grouprange1 takes grouprange1 as input" and cries
self-loop. That is exactly backwards: the wiring is correct.

The true file list survives in the `Contents.contents` manifest, which is written
before the filesystem collapses anything. So: parse the manifest, find every name
that collides case-insensitively inside one directory, and refuse to judge those
nodes offline. They are reported separately and must be confirmed in Houdini.

This cost a wrong call once already - the first run "found" the DowntownBuilding
self-loop in a file that had been correctly fixed and committed hours earlier.
"""
import collections
import csv
import os
import re
import shutil
import subprocess
import sys

HOTL = r"C:/Program Files/Side Effects Software/Houdini 22.0.368/bin/hotl.exe"
LIB = "U:/Git/AssetBashTools"
TMP = "C:/abtmp/sl"
OUT = "U:/AB_Standardization/selfloop_scan.csv"

SKIP_DIRS = ("/backup/", "/OLD/", "/old/")
INPUTS_RE = re.compile(r"^\s*(\d+)\s+(\S+)\s+(\d+)\s+(\d+)\s*$")


def hdas():
    for root, dirs, files in os.walk(os.path.join(LIB, "Sops")):
        rel_root = root.replace("\\", "/")
        if any(s in rel_root + "/" for s in SKIP_DIRS):
            continue
        for f in sorted(files):
            if f.endswith(".hda"):
                p = os.path.join(root, f).replace("\\", "/")
                yield p, p[len(LIB) + 1:]


def parse_inputs(def_path):
    """Return [(input_index, source_node_name), ...] from a node .def file."""
    out, inside = [], False
    try:
        with open(def_path, "r", errors="replace") as fh:
            for line in fh:
                s = line.rstrip("\n")
                if not inside:
                    if s.strip() == "inputs":
                        inside = True
                    continue
                if s.strip() == "{":
                    continue
                if s.strip() == "}":
                    break
                m = INPUTS_RE.match(s)
                if m:
                    out.append((int(m.group(1)), m.group(2)))
    except OSError:
        pass
    return out


def collided_nodes(exp_root):
    """Node paths whose .def was overwritten by a case-twin. See the header note.

    Returns a set of "<network>/<nodename-lowercased>" keys that cannot be judged
    from the expanded files, because two differently-cased nodes share one path.
    """
    out = set()
    for root, dirs, files in os.walk(exp_root):
        if "Contents.contents" not in files:
            continue
        seen = collections.defaultdict(list)
        with open(os.path.join(root, "Contents.contents"), errors="replace") as fh:
            for line in fh:
                name = line.strip()
                if name.endswith(".def"):
                    seen[name.lower()].append(name)
        for low, variants in seen.items():
            if len(variants) > 1:
                out.add(low[:-4])          # strip ".def"
    return out


def scan_expansion(exp_root):
    """Walk every .def under Contents.dir.

    Returns (node_count, [confirmed findings], [unverifiable case-collisions]).
    """
    collided = collided_nodes(exp_root)
    found, unverifiable, count = [], [], 0
    for root, dirs, files in os.walk(exp_root):
        r = root.replace("\\", "/")
        if "/Contents.dir/" not in r + "/":
            continue
        # note the trailing "/": the walk also visits Contents.dir itself
        rel_dir = (r + "/").split("/Contents.dir/", 1)[1].rstrip("/")
        for f in files:
            if not f.endswith(".def"):
                continue
            count += 1
            node = f[:-4]
            key = ("%s/%s" % (rel_dir, node)).lower()
            for idx, src in parse_inputs(os.path.join(root, f)):
                if src != node:
                    continue
                net = rel_dir
                if net.startswith("hdaroot"):
                    net = net[len("hdaroot"):].lstrip("/")
                rec = (net or "(root)", node, idx)
                if key in collided:
                    unverifiable.append(rec)
                else:
                    found.append(rec)
    return count, found, unverifiable


def main():
    if os.path.isdir(TMP):
        shutil.rmtree(TMP, ignore_errors=True)
    os.makedirs(TMP, exist_ok=True)

    rows, unver_rows, clean, failed = [], [], 0, []
    for i, (full, rel) in enumerate(hdas(), 1):
        d = os.path.join(TMP, str(i))
        os.makedirs(d, exist_ok=True)
        p = subprocess.run([HOTL, "-X", d, full],
                           capture_output=True, text=True)
        if p.returncode != 0:
            failed.append((rel, (p.stderr or p.stdout).strip()[:120]))
            shutil.rmtree(d, ignore_errors=True)
            continue
        count, found, unver = scan_expansion(d)
        if count == 0:
            failed.append((rel, "expanded to 0 nodes - MAX_PATH?"))
        else:
            for net, node, idx in found:
                rows.append((rel, net, node, idx))
            for net, node, idx in unver:
                unver_rows.append((rel, net, node, idx))
            if found:
                print("  %-56s %d SELF-LOOP(S)" % (rel, len(found)))
            elif unver:
                print("  %-56s %d case-collision, unverifiable offline"
                      % (rel, len(unver)))
            else:
                clean += 1
            sys.stdout.flush()
        shutil.rmtree(d, ignore_errors=True)

    with open(OUT, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["File", "Network", "Node", "InputIndex", "Verdict"])
        for r in rows:
            w.writerow(list(r) + ["SELF-LOOP"])
        for r in unver_rows:
            w.writerow(list(r) + ["UNVERIFIABLE-CASE-COLLISION"])

    print("")
    print("scanned          : %d" % (clean + len({r[0] for r in rows})
                                     + len({r[0] for r in unver_rows})
                                     + len(failed)))
    print("clean            : %d" % clean)
    print("real self-loops  : %d files, %d nodes"
          % (len({r[0] for r in rows}), len(rows)))
    print("unverifiable     : %d files, %d nodes (case-collision - check in Houdini)"
          % (len({r[0] for r in unver_rows}), len(unver_rows)))
    print("failed           : %d" % len(failed))
    for rel, why in failed:
        print("    %-56s %s" % (rel, why))
    print("")
    print("wrote %s" % OUT)


if __name__ == "__main__":
    main()
