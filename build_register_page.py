"""Render AB_Assets.csv + the icon SVGs into one review page.

Inlining 150 SVGs into a single document collides their internal ids - every icon
defines id="bg" and id="oglow", and url(#bg) then resolves to whichever appeared
first. Ids are rewritten with a per-icon prefix on the way in.
"""
import os, csv, re, html, collections

CSV   = "U:/AB_Standardization/AB_Assets.csv"
ICONS = "U:/Git/AssetBashTools/IconDev/Icons"
OUT   = "U:/AB_Standardization/ab_tool_register.html"

rows = list(csv.DictReader(open(CSV, encoding="utf-8")))
ship = [r for r in rows if r["Ships"] == "SHIP"]
sup  = [r for r in rows if r["Ships"] != "SHIP"]

ID_RE  = re.compile(r'id="([^"]+)"')
URL_RE = re.compile(r'url\(#([^)]+)\)')


def inline_icon(fname, n):
    p = os.path.join(ICONS, fname)
    try:
        s = open(p, encoding="utf-8").read()
    except Exception:
        return ""
    s = re.sub(r"<\?xml.*?\?>", "", s, flags=re.S)
    pre = "i%d_" % n
    s = ID_RE.sub(lambda m: 'id="%s%s"' % (pre, m.group(1)), s)
    s = URL_RE.sub(lambda m: "url(#%s%s)" % (pre, m.group(1)), s)
    s = re.sub(r'\s(width|height)="[^"]*"', "", s, count=2)
    return s.replace("<svg", '<svg class="ic" aria-hidden="true"', 1)


# --- what needs a human decision ------------------------------------------
malformed = [r for r in ship if ":" in r["Tool"] or r["TypeName"].startswith("AOD::")]
mismatch  = [r for r in rows if r["FilenameTypeMismatch"]]
noicon    = [r for r in ship if not r["Icon"]]

by_tool = collections.defaultdict(list)
for r in rows:
    by_tool[r["Tool"]].append(r)
multi = {t: v for t, v in by_tool.items() if len(v) > 1}

used = {r["Icon"] for r in ship if r["Icon"]}
unused = sorted(f for f in os.listdir(ICONS)
                if f.endswith(".svg") and f not in used)

CSS = """
:root{
  --ground:#F6F5F2; --surface:#FFFFFF; --ink:#1B1E22; --muted:#6A7078;
  --rule:#E3E1DC; --rule-strong:#CFCCC5;
  --accent:#14655A; --ship:#14655A; --old:#8A6A22; --bad:#A33A2A;
  --chip:#EFEDE8;
}
@media (prefers-color-scheme:dark){
  :root:not([data-theme="light"]){
    --ground:#131519; --surface:#1B1E23; --ink:#E7E8E9; --muted:#949AA1;
    --rule:#282C32; --rule-strong:#3A3F47;
    --accent:#3FA893; --ship:#3FA893; --old:#C9A24A; --bad:#D97C6A;
    --chip:#22262C;
  }
}
:root[data-theme="dark"]{
  --ground:#131519; --surface:#1B1E23; --ink:#E7E8E9; --muted:#949AA1;
  --rule:#282C32; --rule-strong:#3A3F47;
  --accent:#3FA893; --ship:#3FA893; --old:#C9A24A; --bad:#D97C6A;
  --chip:#22262C;
}
*{box-sizing:border-box}
body{
  margin:0; background:var(--ground); color:var(--ink);
  font-family:system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;
  font-size:15px; line-height:1.55;
}
.wrap{max-width:1180px;margin:0 auto;padding:56px 28px 96px}
h1,h2{font-family:ui-serif,"Iowan Old Style","Palatino Linotype",Palatino,Georgia,serif;
  font-weight:600; text-wrap:balance; margin:0}
h1{font-size:38px;letter-spacing:-.015em}
h2{font-size:22px;letter-spacing:-.01em}
.sub{color:var(--muted);margin:10px 0 0;max-width:64ch}
.mono{font-family:ui-monospace,"SF Mono","Cascadia Mono",Consolas,monospace;
  font-variant-numeric:tabular-nums}
.eyebrow{font-size:11px;letter-spacing:.14em;text-transform:uppercase;
  color:var(--muted);font-weight:600}

.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));
  gap:1px;background:var(--rule);border:1px solid var(--rule);margin:36px 0 8px}
.stat{background:var(--surface);padding:16px 18px}
.stat .n{font-size:28px;font-weight:600;letter-spacing:-.02em}
.stat .l{font-size:12px;color:var(--muted);margin-top:2px}
.stat.bad .n{color:var(--bad)} .stat.old .n{color:var(--old)}
.stat.ship .n{color:var(--ship)}

section{margin-top:56px}
.head{display:flex;align-items:baseline;gap:14px;flex-wrap:wrap;
  border-bottom:2px solid var(--rule-strong);padding-bottom:10px;margin-bottom:20px}
.count{color:var(--muted);font-size:13px}

table{width:100%;border-collapse:collapse;font-size:14px}
th{text-align:left;font-size:11px;letter-spacing:.1em;text-transform:uppercase;
  color:var(--muted);font-weight:600;padding:8px 12px 8px 0;
  border-bottom:1px solid var(--rule)}
td{padding:9px 12px 9px 0;border-bottom:1px solid var(--rule);vertical-align:top}
tbody tr:hover td{background:var(--chip)}
.tbl{overflow-x:auto}

.tag{display:inline-block;font-size:11px;font-weight:600;letter-spacing:.04em;
  padding:2px 7px;border-radius:2px;white-space:nowrap}
.t-ship{color:var(--ship);border:1px solid var(--ship)}
.t-old{color:var(--old);border:1px solid var(--old)}
.t-bad{color:var(--bad);border:1px solid var(--bad)}

.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(258px,1fr));
  gap:1px;background:var(--rule);border:1px solid var(--rule)}
.cell{background:var(--surface);padding:10px 12px;display:flex;gap:11px;align-items:center;min-width:0}
.ic{width:38px;height:38px;flex:0 0 38px;border-radius:4px;display:block}
.ph{width:38px;height:38px;flex:0 0 38px;border-radius:4px;border:1px dashed var(--bad);
  display:grid;place-items:center;color:var(--bad);font-size:16px;font-weight:600}
.nm{min-width:0}
.nm b{display:block;font-weight:600;font-size:13.5px;overflow:hidden;
  text-overflow:ellipsis;white-space:nowrap}
.nm span{display:block;font-size:11.5px;color:var(--muted)}
.cell.miss{outline:1px solid var(--bad);outline-offset:-1px}

.note{background:var(--surface);border-left:3px solid var(--accent);
  padding:14px 18px;margin:18px 0;font-size:14px}
.note b{color:var(--accent)}
footer{margin-top:72px;padding-top:20px;border-top:1px solid var(--rule);
  color:var(--muted);font-size:12.5px}
a{color:var(--accent)}
"""


def tag(kind, text):
    return '<span class="tag t-%s">%s</span>' % (kind, text)


out = []
A = out.append
A('<title>AssetBash Tool Register</title>')
A("<style>%s</style>" % CSS)
A('<div class="wrap">')
A('<p class="eyebrow">AssetBash standardization &middot; 2026-08-14</p>')
A("<h1>Tool Register</h1>")
A('<p class="sub">Every HDA in the library, the version that ships, and the icon it '
  "should carry. Decisions that block the release come first; the bulk jobs follow.</p>")

A('<div class="stats">')
for cls, n, l in (("", len(by_tool), "tools"),
                  ("", len(rows), "files on disk"),
                  ("ship", len(ship), "shipping versions"),
                  ("old", len(sup), "superseded"),
                  ("ship", len([r for r in ship if r["Icon"]]), "icons matched"),
                  ("bad", len(noicon), "icons missing"),
                  ("bad", len(mismatch) + len(malformed), "identity defects")):
    A('<div class="stat %s"><div class="n mono">%d</div><div class="l">%s</div></div>' % (cls, n, l))
A("</div>")

# ---------------------------------------------------------------- decisions
A("<section>")
A('<div class="head"><h2>Identity defects</h2>'
  '<span class="count">%d &mdash; these need a ruling before anything keys off version</span></div>'
  % (len(malformed) + len(mismatch)))
A('<div class="note"><b>Namespace</b> &mdash; three tools are not in the AB namespace at all. '
  '<code class="mono">AB:RockMaker</code> has a single colon, so its type is literally '
  '<code class="mono">AB:RockMaker</code>; two more are still <code class="mono">AOD::</code> '
  "with lowercase names. Renaming a type is a breaking change, so these want deciding early.</div>")
A('<div class="tbl"><table><thead><tr><th>Tool</th><th>Type it defines</th>'
  "<th>Filename says</th><th>Type says</th><th>File</th></tr></thead><tbody>")
for r in malformed:
    A("<tr><td><b>%s</b> %s</td><td class='mono'>%s</td><td class='mono'>%s</td>"
      "<td class='mono'>%s</td><td class='mono' style='color:var(--muted)'>%s</td></tr>"
      % (html.escape(r["Tool"]), tag("bad", "namespace"), html.escape(r["TypeName"]),
         r["VersionInFilename"], r["VersionInType"], html.escape(r["File"])))
for r in mismatch:
    A("<tr><td><b>%s</b> %s</td><td class='mono'>%s</td><td class='mono'>%s</td>"
      "<td class='mono'>%s</td><td class='mono' style='color:var(--muted)'>%s</td></tr>"
      % (html.escape(r["Tool"]), tag("bad", "version"), html.escape(r["TypeName"]),
         r["VersionInFilename"], r["VersionInType"], html.escape(r["File"])))
A("</tbody></table></div>")
A("</section>")

# ------------------------------------------------------------------- icons
A("<section>")
A('<div class="head"><h2>Icon assignment</h2>'
  '<span class="count">%d matched &middot; %d missing &middot; %d icons unused</span></div>'
  % (len(ship) - len(noicon), len(noicon), len(unused)))
A('<div class="note">Matched on Houdini\'s own convention &mdash; type '
  '<code class="mono">AB::Foo</code> takes <code class="mono">SOP_AB__Foo.svg</code>. '
  "Nothing is fuzzy-matched: a tool either has an exact match or is flagged, because a "
  "wrong icon is worse than a missing one.</div>")
# Grouped by the categories in TOOL_MAP - Jordan's own grouping, so the grid reads
# the way the spec was written rather than as a flat alphabetical wall.
groups = collections.defaultdict(list)
for r in ship:
    groups[r.get("IconGroup") or "Unspecified"].append(r)
n = 0
for gname in sorted(groups, key=lambda g: (g == "Unspecified", g.lower())):
    members = sorted(groups[gname], key=lambda x: x["Tool"].lower())
    A('<h3 style="font-size:13px;letter-spacing:.1em;text-transform:uppercase;'
      'color:var(--muted);margin:26px 0 10px;font-weight:600">%s '
      '<span style="font-weight:400;text-transform:none;letter-spacing:0">&middot; %d</span></h3>'
      % (html.escape(gname), len(members)))
    A('<div class="grid">')
    for r in members:
        n += 1
        detail = " &middot; ".join(x for x in (r.get("IconMotif"), r.get("IconPalette")) if x)
        note = html.escape(r.get("Notes") or "")
        if r["Icon"]:
            A('<div class="cell">%s<div class="nm"><b>%s</b>'
              '<span class="mono">%s</span><span>%s</span>%s</div></div>'
              % (inline_icon(r["Icon"], n), html.escape(r["Tool"]),
                 r["VersionInType"] or r["VersionInFilename"], detail,
                 ('<span style="color:var(--accent)">%s</span>' % note) if note else ""))
        else:
            A('<div class="cell miss"><div class="ph">?</div><div class="nm"><b>%s</b>'
              '<span class="mono">%s</span><span style="color:var(--bad)">no icon, no spec</span>'
              "%s</div></div>"
              % (html.escape(r["Tool"]), r["VersionInType"] or r["VersionInFilename"],
                 ('<span style="color:var(--accent)">%s</span>' % note) if note else ""))
    A("</div>")
if unused:
    A('<p class="sub" style="margin-top:18px"><b>%d icons with no tool</b> &mdash; '
      "left over from renames and splits: %s</p>"
      % (len(unused), ", ".join('<code class="mono">%s</code>' % u[:-4] for u in unused)))
A("</section>")

# --------------------------------------------------------------- versions
A("<section>")
A('<div class="head"><h2>Version collapse</h2>'
  '<span class="count">%d tools carry more than one version &middot; %d files could leave the scan path</span></div>'
  % (len(multi), len(sup)))
A('<div class="note">Every superseded file still sits in <code class="mono">HOUDINI_OTLSCAN_PATH</code>. '
  "Archiving them outside it closes several nested-version items for free, because those "
  "references live inside versions that were never going to ship.</div>")
A('<div class="tbl"><table><thead><tr><th>Tool</th><th>Versions</th><th>Ships</th>'
  "<th>Archive</th></tr></thead><tbody>")
for tool, group in sorted(multi.items(), key=lambda kv: (-len(kv[1]), kv[0].lower())):
    g = sorted(group, key=lambda r: [int(x) for x in re.findall(r"\d+", r["VersionInType"] or "0")])
    shipv = [r for r in g if r["Ships"] == "SHIP"][0]
    olds = [r["VersionInType"] or r["VersionInFilename"] for r in g if r["Ships"] != "SHIP"]
    A("<tr><td><b>%s</b></td><td class='mono'>%d</td><td class='mono'>%s %s</td>"
      "<td class='mono' style='color:var(--muted)'>%s</td></tr>"
      % (html.escape(tool), len(g), shipv["VersionInType"] or shipv["VersionInFilename"],
         tag("ship", "SHIP"), ", ".join(olds)))
A("</tbody></table></div>")
A("</section>")

A('<footer>Generated from <code class="mono">AB_Assets.csv</code> and '
  '<code class="mono">IconDev/Icons</code>. Version order is compared numerically, so 4.10 '
  "beats 4.9; the type is read from each file rather than trusted from its name.</footer>")
A("</div>")

open(OUT, "w", encoding="utf-8").write("\n".join(out))
print("written: %s  (%.0f KB)" % (OUT, os.path.getsize(OUT) / 1024))
print("tools %d  ship %d  superseded %d  no-icon %d  defects %d"
      % (len(by_tool), len(ship), len(sup), len(noicon), len(mismatch) + len(malformed)))
