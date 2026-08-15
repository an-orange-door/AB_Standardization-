"""Merge every analysis pass into one browsable register.

    python U:/AB_Standardization/build_tool_register.py

Reads (all read-only, all already on disk):
    analysis/tools.csv            version, parm + node counts, unresolved types
    analysis/nesting.csv          the dependency graph
    analysis/orphan_literals.csv  the triage list
    analysis/menus.csv            ordinal menus, for the append-only check
    zone_coverage.csv             s@name zone coverage + any existing notes

Writes ab_tool_register_v2.html - self-contained, no external requests.

WHY A REBUILD RATHER THAN A COLUMN ADDED TO THE OLD PAGE:
the old worklist answered one question (does this tool name its zones). The
sweep answers five, and they interact - a tool with no zones AND an unresolved
type AND six orphan flags is not three separate tickets, it is one tool to open
once. The register is per-TOOL so that lands on one row.

⚠ Edits live in localStorage, which Google Drive does NOT sync. The Export CSV
button is therefore not a convenience, it is the only way to share or back up
edits. Said plainly in the page itself.
"""
import collections
import csv
import html
import json
import os
import re

BASE = "U:/AB_Standardization"
OUT = BASE + "/ab_tool_register_v2.html"

GEO_NODES = {"add", "box", "grid", "circle", "tube", "sphere", "bound",
             "divide", "line", "curve"}
DIM_FAMS = ("size", "rad", "pt", "div", "height", "width", "length")


def read(path):
    p = os.path.join(BASE, path)
    if not os.path.isfile(p):
        return []
    with open(p, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def tier_a(row):
    """Geometry-defining orphan: far likelier to be a real bug than a transform."""
    return (row["node_type"].split("::")[0] in GEO_NODES
            and any(row["parm_family"].startswith(d) for d in DIM_FAMS))


def main():
    tools = read("analysis/tools.csv")
    nesting = read("analysis/nesting.csv")
    orphans = read("analysis/orphan_literals.csv")
    menus = read("analysis/menus.csv")
    zones = {z["Tool"]: z for z in read("zone_coverage.csv")}

    # --- dependency graph, AB/AOD types only -------------------------------
    # nesting.csv also lists stock types (boolean::2.0 etc). Those are noise for
    # work ordering - what matters is which AB tool depends on which AB tool.
    nests = collections.defaultdict(list)
    nested_by = collections.defaultdict(set)
    known = {t["tool"] for t in tools}
    base_of = {}
    for t in tools:
        base_of["%s::%s" % (t["namespace"], t["name"])] = t["tool"]
    for r in nesting:
        ty = r["nests_type"]
        if not ty.startswith(("AB::", "AB.", "AOD::", "AOD.")):
            continue
        nests[r["tool"]].append((ty, int(r["count"])))
        # map a versioned reference back to whichever tool provides it
        parts = ty.split("::")
        resolved = base_of.get("::".join(parts[:2])) if len(parts) >= 2 else None
        if resolved and resolved != r["tool"]:
            nested_by[resolved].add(r["tool"])

    orph = collections.defaultdict(list)
    for r in orphans:
        if r["confidence"] != "high":
            continue
        r["tier"] = "A" if tier_a(r) else "B"
        orph[r["tool"]].append(r)

    menu_n = collections.Counter()
    for r in menus:
        menu_n[r["tool"]] += 1

    rows = []
    for t in tools:
        name = t["tool"]
        z = zones.get(name, {})
        flags = orph.get(name, [])
        a = [f for f in flags if f["tier"] == "A"]
        unres = [u for u in t["unresolved_types"].split() if u]
        third_party = [u for u in unres if "::" not in u]
        zc = int(z.get("ZoneCount") or 0)
        rows.append({
            "tool": name,
            "short": t["name"],
            "ver": t["version"],
            "cat": z.get("Category") or "-",
            "file": t["file"].replace("U:/Git/AssetBashTools/", ""),
            "parms": int(t["n_parms"] or 0),
            "nodes": int(t["n_inner_nodes"] or 0),
            "menus": menu_n.get(name, 0),
            "zones": zc,
            "zonenames": z.get("Zones", ""),
            "cook": z.get("Cook", ""),
            "nests": sorted(nests.get(name, []), key=lambda x: -x[1]),
            "nestedby": sorted(nested_by.get(name, ())),
            "orphA": len(a),
            "orphB": len(flags) - len(a),
            "orph": [{"n": f["inner_node"], "t": f["node_type"],
                      "f": f["parm_family"], "l": f["literals"],
                      "r": f["referenced"], "tier": f["tier"]} for f in flags],
            "unres": unres,
            "third": third_party,
            "status": z.get("Status", ""),
            "owner": z.get("Owner", ""),
            "notes": z.get("Notes", ""),
        })
    rows.sort(key=lambda r: r["short"].lower())

    # must mirror guessClass()/zoneExempt() in the page, or the headline counter
    # disagrees with the rows underneath it
    def is_utility(short):
        return bool(re.search(
            r"group|select|attrib|material|assign|util|export|import|processor",
            short, re.I))

    stats = {
        "tools": len(rows),
        "nozones": sum(1 for r in rows
                       if not r["zones"] and not is_utility(r["short"])),
        "unres": sum(1 for r in rows if r["unres"]),
        "third": sum(1 for r in rows if r["third"]),
        "orphA": sum(r["orphA"] for r in rows),
        "orphAtools": sum(1 for r in rows if r["orphA"]),
        "nodes": sum(r["nodes"] for r in rows),
    }

    with open(OUT, "w", encoding="utf-8") as f:
        f.write(TEMPLATE.replace("__DATA__", json.dumps(rows))
                        .replace("__STATS__", json.dumps(stats)))
    print("wrote %s  (%d tools, %.0f KB)"
          % (OUT, len(rows), os.path.getsize(OUT) / 1024.0))


TEMPLATE = r"""<title>AssetBash Tool Register</title>
<style>
/* Palette: drafting-table. Ink with a blue bias, blueprint accent, oxide
   warning colours - grounded in the engineering-drawing world these tools
   model, rather than a default neutral grey. */
:root{
  --paper:#F7F9FB; --surface:#FFFFFF; --sunk:#EEF2F6;
  --ink:#111820; --muted:#5A6875; --line:#D9E1E9;
  --accent:#15679E; --accent-soft:#E4EFF7;
  --bad:#9E3324; --bad-soft:#F8E7E4;
  --warn:#96650F; --warn-soft:#FBF0DC;
  --good:#2A6349; --good-soft:#E2F0E9;
  --mono:ui-monospace,"SF Mono",Menlo,Consolas,monospace;
  --sans:ui-sans-serif,system-ui,"Segoe UI",Roboto,sans-serif;
}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){
  --paper:#0C1116; --surface:#141B22; --sunk:#1B242D;
  --ink:#E4EBF2; --muted:#8A9AA8; --line:#26313C;
  --accent:#4E9FD6; --accent-soft:#152633;
  --bad:#D4705F; --bad-soft:#2C1A17;
  --warn:#D0A055; --warn-soft:#2A2113;
  --good:#63A886; --good-soft:#16261F;
}}
:root[data-theme="dark"]{
  --paper:#0C1116; --surface:#141B22; --sunk:#1B242D;
  --ink:#E4EBF2; --muted:#8A9AA8; --line:#26313C;
  --accent:#4E9FD6; --accent-soft:#152633;
  --bad:#D4705F; --bad-soft:#2C1A17;
  --warn:#D0A055; --warn-soft:#2A2113;
  --good:#63A886; --good-soft:#16261F;
}
*{box-sizing:border-box}
body{margin:0;background:var(--paper);color:var(--ink);font-family:var(--sans);
     font-size:14px;line-height:1.5}
.wrap{max-width:1500px;margin:0 auto;padding:28px 20px 80px}
h1{font-size:21px;letter-spacing:-.01em;margin:0 0 2px}
.sub{color:var(--muted);font-size:13px;margin:0 0 20px;max-width:70ch}

/* summary before detail: what needs attention, readable at a glance */
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));
       gap:10px;margin-bottom:18px}
.card{background:var(--surface);border:1px solid var(--line);border-radius:7px;
      padding:11px 13px}
.card .n{font-family:var(--mono);font-size:23px;font-variant-numeric:tabular-nums;
         letter-spacing:-.02em}
.card .k{font-size:10.5px;text-transform:uppercase;letter-spacing:.07em;
         color:var(--muted);margin-top:2px}
.card.bad .n{color:var(--bad)} .card.warn .n{color:var(--warn)}

.note{background:var(--warn-soft);border:1px solid var(--line);
      border-left:3px solid var(--warn);border-radius:6px;padding:10px 13px;
      margin-bottom:18px;font-size:13px}
.note b{color:var(--warn)}

.bar{display:flex;gap:8px;flex-wrap:wrap;align-items:center;margin-bottom:14px;
     position:sticky;top:0;background:var(--paper);padding:10px 0;z-index:5;
     border-bottom:1px solid var(--line)}
input,select,button{font:inherit;color:var(--ink);background:var(--surface);
      border:1px solid var(--line);border-radius:6px;padding:6px 9px}
input:focus,select:focus,button:focus-visible{outline:2px solid var(--accent);
      outline-offset:1px}
button{cursor:pointer}
button.primary{background:var(--accent);color:#fff;border-color:transparent;
      font-weight:600}
.chip{border:1px solid var(--line);border-radius:20px;padding:4px 11px;
      cursor:pointer;background:var(--surface);font-size:12.5px}
.chip[aria-pressed="true"]{background:var(--accent-soft);
      border-color:var(--accent);color:var(--accent);font-weight:600}

.tablewrap{overflow-x:auto;border:1px solid var(--line);border-radius:8px;
      background:var(--surface)}
table{border-collapse:collapse;width:100%;min-width:1080px}
th{position:sticky;top:52px;background:var(--sunk);text-align:left;
   font-size:10.5px;text-transform:uppercase;letter-spacing:.07em;
   color:var(--muted);padding:8px 10px;border-bottom:1px solid var(--line);
   cursor:pointer;white-space:nowrap}
td{padding:7px 10px;border-bottom:1px solid var(--line);vertical-align:top}
tr.row{cursor:pointer}
tr.row:hover td{background:var(--sunk)}
.num{text-align:right;font-family:var(--mono);font-variant-numeric:tabular-nums}
.tool{font-weight:600}
.path{color:var(--muted);font-size:11.5px;font-family:var(--mono)}
/* severity encoded in form, not only in number */
.stripe{border-left:3px solid transparent}
.stripe.s2{border-left-color:var(--bad)}
.stripe.s1{border-left-color:var(--warn)}
.pill{display:inline-block;font-size:11px;padding:1px 7px;border-radius:20px;
      border:1px solid var(--line);white-space:nowrap}
.pill.bad{background:var(--bad-soft);color:var(--bad);border-color:transparent}
.pill.warn{background:var(--warn-soft);color:var(--warn);border-color:transparent}
.pill.good{background:var(--good-soft);color:var(--good);border-color:transparent}
td input,td select{padding:3px 6px;font-size:12.5px;width:100%}
td.pri input{width:46px;text-align:center}

.detail td{background:var(--sunk);padding:14px 16px}
.detail h4{margin:0 0 7px;font-size:10.5px;text-transform:uppercase;
      letter-spacing:.07em;color:var(--muted)}
.detail section{margin-bottom:14px}
.mono{font-family:var(--mono);font-size:12px}
.orph{border-left:2px solid var(--line);padding:3px 0 3px 9px;margin-bottom:5px}
.orph.A{border-left-color:var(--bad)}
.empty{padding:36px;text-align:center;color:var(--muted)}
</style>

<div class="wrap">
<h1>AssetBash Tool Register</h1>
<p class="sub">Every latest-version tool, with the five things the 15 Aug sweep
measured on each. Per tool rather than per issue, because a tool with no zones
<em>and</em> an unresolved type <em>and</em> six orphan flags is one tool to open
once, not three tickets. Click a row for detail.</p>

<div class="cards" id="cards"></div>

<div class="note"><b>Edits are stored in this browser only.</b> Google Drive does
not sync localStorage, so a copy of this file on Drive shows other people an
empty sheet. Use <b>Export CSV</b> to share or back up — that file is the one to
put on Drive.</div>

<div class="bar">
  <input id="q" placeholder="Search tool, zone, path…" style="min-width:230px">
  <select id="cat"></select>
  <button class="chip" id="f-unres" aria-pressed="false">Unresolved types</button>
  <button class="chip" id="f-third" aria-pressed="false">Needs qLib</button>
  <button class="chip" id="f-orph" aria-pressed="false">Orphan literals (A)</button>
  <button class="chip" id="f-zone" aria-pressed="false">No zones</button>
  <span style="flex:1"></span>
  <span class="path" id="count"></span>
  <button class="primary" id="export">Export CSV</button>
  <button id="reset">Clear edits</button>
</div>

<div class="tablewrap"><table>
<thead><tr>
  <th data-s="short">Tool</th><th data-s="cat">Category</th>
  <th data-s="ver">Ver</th><th>Class</th><th data-s="pri" class="num">Pri</th>
  <th data-s="zones" class="num">Zones</th>
  <th data-s="orphA" class="num" title="Tier A: geometry-defining">Orph A</th>
  <th data-s="nestedbyN" class="num" title="How many tools embed this one">Used by</th>
  <th data-s="parms" class="num">Parms</th>
  <th data-s="nodes" class="num">Nodes</th>
  <th>Health</th><th>Status</th><th>Notes</th>
</tr></thead>
<tbody id="tb"></tbody>
</table></div>
<div class="empty" id="empty" hidden>Nothing matches those filters.</div>
</div>

<script>
const ROWS = __DATA__, STATS = __STATS__;
const KEY = "ab_tool_register_v1";
let edits = {};
try { edits = JSON.parse(localStorage.getItem(KEY) || "{}"); } catch(e){ edits = {}; }
ROWS.forEach(r => { r.nestedbyN = r.nestedby.length;
                    const e = edits[r.tool] || {};
                    r.pri = e.pri ?? ""; r.cls = e.cls ?? guessClass(r);
                    r.status = e.status ?? r.status; r.notes = e.notes ?? r.notes; });

// A tool that emits no prims and names nothing is almost certainly plumbing,
// not a generator. Pre-filled as a starting point, always overridable.
function guessClass(r){
  /* Folder beats name. Everything in Sops/Modules is a Library (Jordan,
     15 Aug) - an archive of parts you pick from. Note this does NOT contradict
     Modules being the STYLE axis: the CLASS describes the mechanism (pick from
     an archive), while Gothic/Brutalist/ArtDeco is what the archive contains.
     A name-based guess gets this wrong every time, because "ModulesGothic"
     looks like a style and "HardwareMaker" looks like a generator. */
  if (/^Sops\/Modules\//.test(r.file)) return "Library";
  if (KNOWN_CLASS[r.short]) return KNOWN_CLASS[r.short];
  const n = r.short.toLowerCase();
  if (/library|archive|catalog/.test(n)) return "Library";
  if (/group|select|attrib|material|assign|util|export|import|processor/.test(n))
    return "Utility";
  if (/modules|style/.test(n)) return "Style";
  if (/generator|maker|builder|tool/.test(n)) return "Generator";
  return "";
}
function save(){ localStorage.setItem(KEY, JSON.stringify(edits)); }
function setEdit(tool, k, v){ (edits[tool] = edits[tool] || {})[k] = v; save(); }

/* "Library" is its own class, not a flavour of Generator. HardwareMaker holds
   door handles and similar - an archive you PICK from, partly procedural.
   SignLibrary is the same shape: pick one of 1,383 by name. That is the CATALOG
   data shape from the preset design, and it is already the pattern SignLibrary's
   ReadLibrary Python SOP implements, so steel_sections.csv should copy it rather
   than invent a third way. Naming alone cannot tell these apart - "Maker" reads
   as a generator - so the obvious ones are named outright. */
const CLASSES = ["", "Generator", "Library", "Style", "Component", "Utility",
                 "Deprecated"];
const KNOWN_CLASS = {
  HardwareMaker: "Library", SignLibrary: "Library", SignPlate: "Component",
  DoorHardware: "Library", MetalExtrusionMaker: "Component",
};
const cards = [
  ["tools","Tools",""], ["orphAtools","Tools w/ orphan flags","warn"],
  ["unres","Unresolved types","bad"], ["third","Need qLib","bad"],
  ["nozones","Missing zones (excl. utilities)","warn"], ["nodes","Inner nodes scanned",""],
];
document.getElementById("cards").innerHTML = cards.map(([k,l,c]) =>
  `<div class="card ${c}"><div class="n">${STATS[k].toLocaleString()}</div>
   <div class="k">${l}</div></div>`).join("");

const cats = [...new Set(ROWS.map(r=>r.cat))].sort();
document.getElementById("cat").innerHTML =
  `<option value="">All categories</option>` +
  cats.map(c=>`<option>${c}</option>`).join("");

let sortKey = "short", sortDir = 1, open = new Set();
const F = {unres:false, third:false, orph:false, zone:false};
["unres","third","orph","zone"].forEach(k=>{
  const b = document.getElementById("f-"+k);
  b.onclick = () => { F[k] = !F[k]; b.setAttribute("aria-pressed", F[k]); draw(); };
});
document.querySelectorAll("th[data-s]").forEach(th=>{
  th.onclick = () => { const k = th.dataset.s;
    sortDir = (k === sortKey) ? -sortDir : 1; sortKey = k; draw(); };
});
document.getElementById("q").oninput = draw;
document.getElementById("cat").onchange = draw;
document.getElementById("reset").onclick = () => {
  if (!confirm("Clear all Priority / Class / Status / Notes edits in this browser?")) return;
  edits = {}; save(); ROWS.forEach(r=>{ r.pri=""; r.cls=guessClass(r); }); draw();
};

function esc(s){ return String(s ?? "").replace(/[&<>"]/g,
  c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c])); }

function visible(){
  const q = document.getElementById("q").value.toLowerCase();
  const c = document.getElementById("cat").value;
  return ROWS.filter(r =>
    (!c || r.cat === c) &&
    (!F.unres || r.unres.length) && (!F.third || r.third.length) &&
    (!F.orph || r.orphA) && (!F.zone || (!r.zones && !zoneExempt(r))) &&
    (!q || (r.tool+" "+r.zonenames+" "+r.file).toLowerCase().includes(q)));
}

/* A tool classed Utility or Deprecated is not SUPPOSED to name zones -
   GroupWalls makes groups and emits nothing to bind a material to. Flagging it
   turns the zone column into noise that has to be mentally filtered on every
   pass, which is how a worklist stops being read. Class suppresses the zone
   warning; it never suppresses a real defect. */
function zoneExempt(r){ return r.cls === "Utility" || r.cls === "Deprecated"; }

function health(r){
  const p = [];
  if (r.third.length) p.push(`<span class="pill bad">qLib</span>`);
  else if (r.unres.length) p.push(`<span class="pill bad">unresolved</span>`);
  if (r.orphA) p.push(`<span class="pill warn">${r.orphA} orphan</span>`);
  if (!r.zones && !zoneExempt(r)) p.push(`<span class="pill warn">no zones</span>`);
  if (!p.length) p.push(`<span class="pill good">${
      zoneExempt(r) ? "n/a" : "clean"}</span>`);
  return p.join(" ");
}
function sev(r){
  if (r.unres.length) return 2;
  return (r.orphA || (!r.zones && !zoneExempt(r))) ? 1 : 0;
}

function draw(){
  const rows = visible().sort((a,b)=>{
    const x = a[sortKey], y = b[sortKey];
    const n = (typeof x === "number" && typeof y === "number")
      ? x - y : String(x).localeCompare(String(y));
    return n * sortDir;
  });
  document.getElementById("count").textContent =
    `${rows.length} of ${ROWS.length} tools`;
  document.getElementById("empty").hidden = rows.length > 0;
  const tb = document.getElementById("tb");
  tb.innerHTML = rows.map(r => {
    const o = open.has(r.tool);
    return `<tr class="row" data-t="${esc(r.tool)}">
      <td class="stripe s${sev(r)}"><div class="tool">${esc(r.short)}</div>
          <div class="path">${esc(r.file)}</div></td>
      <td>${esc(r.cat)}</td><td class="num">${esc(r.ver)}</td>
      <td><select data-k="cls">${CLASSES.map(c=>
          `<option${c===r.cls?" selected":""}>${c}</option>`).join("")}</select></td>
      <td class="num pri"><input data-k="pri" value="${esc(r.pri)}"
          inputmode="numeric" maxlength="1" placeholder="–"></td>
      <td class="num">${r.zones || "<span style='color:var(--muted)'>0</span>"}</td>
      <td class="num">${r.orphA || ""}</td>
      <td class="num">${r.nestedbyN || ""}</td>
      <td class="num">${r.parms}</td>
      <td class="num">${r.nodes.toLocaleString()}</td>
      <td>${health(r)}</td>
      <td><input data-k="status" value="${esc(r.status)}"></td>
      <td><input data-k="notes" value="${esc(r.notes)}"></td>
    </tr>` + (o ? detail(r) : "");
  }).join("");

  tb.querySelectorAll("tr.row").forEach(tr => {
    tr.onclick = e => {
      if (e.target.closest("input,select,button")) return;
      const t = tr.dataset.t; open.has(t) ? open.delete(t) : open.add(t); draw();
    };
  });
  tb.querySelectorAll("input[data-k],select[data-k]").forEach(el => {
    el.onchange = () => {
      const t = el.closest("tr").dataset.t, k = el.dataset.k;
      const r = ROWS.find(x => x.tool === t);
      r[k] = el.value; setEdit(t, k, el.value);
      if (k === "pri" || k === "cls") draw();
    };
  });
}

function detail(r){
  let h = `<tr class="detail"><td colspan="13">`;
  if (r.unres.length) h += `<section><h4>Unresolved types — breaks on any machine
    without a definition</h4><div class="mono">${r.unres.map(u =>
    `<span class="pill ${u.includes("::")?"bad":"bad"}">${esc(u)}</span>`)
    .join(" ")}</div>${r.third.length ? `<div class="path"
    style="margin-top:5px">${esc(r.third.join(", "))} is qLib, not AssetBash —
    a customer without qLib gets a broken tool.</div>` : ""}</section>`;
  if (r.orph.length){
    const a = r.orph.filter(o=>o.tier==="A"), b = r.orph.filter(o=>o.tier!=="A");
    h += `<section><h4>Orphan literals — ${a.length} geometry-defining,
      ${b.length} transform/other. Triage, not confirmed bugs.</h4>` +
      a.concat(b).slice(0,14).map(o=>`<div class="orph ${o.tier}">
        <span class="mono">${esc(o.n)}</span>
        <span class="path">${esc(o.t)} · family ${esc(o.f)}</span><br>
        <span class="mono" style="color:var(--bad)">literal ${esc(o.l)}</span>
        <span class="path">wired ${esc(o.r)}</span></div>`).join("") +
      (r.orph.length > 14 ? `<div class="path">…${r.orph.length-14} more in
        analysis/orphan_literals.csv</div>` : "") + `</section>`;
  }
  if (r.nests.length) h += `<section><h4>Nests</h4><div class="mono">${
    r.nests.map(([t,n]) => `${esc(t)}${n>1?" ×"+n:""}`).join("  ·  ")}</div></section>`;
  if (r.nestedby.length) h += `<section><h4>Used by ${r.nestedby.length} tools —
    edit blast radius</h4><div class="mono">${
    r.nestedby.map(t=>esc(t.replace("AB::",""))).join("  ·  ")}</div></section>`;
  if (r.zonenames) h += `<section><h4>Zones</h4>
    <div class="mono">${esc(r.zonenames)}</div></section>`;
  if (!r.unres.length && !r.orph.length && !r.nests.length && !r.zonenames)
    h += `<div class="path">Nothing flagged.</div>`;
  return h + `</td></tr>`;
}

/* Export has to work in two very different places:
   - opened straight off U:\ as a local file, where window.claude does not
     exist and a blob link is the only option (and works fine);
   - published as an artifact, where a blob link is inert and the viewer must
     be offered the file through the downloads capability instead.
   Detect rather than assume, or the button silently does nothing in one of
   them - which is the exact failure this whole page is meant to prevent. */
const HOSTED = !!(window.claude && window.claude.use);

function buildCSV(){
  const cols = ["tool","cat","ver","cls","pri","zones","orphA","orphB",
                "nestedbyN","parms","nodes","unres","third","status","notes"];
  const q = v => {
    const s = Array.isArray(v) ? v.join(" ") : String(v ?? "");
    return /[",\n]/.test(s) ? '"' + s.replace(/"/g,'""') + '"' : s;
  };
  return [cols.join(",")].concat(
    visible().map(r => cols.map(c => q(r[c])).join(","))).join("\r\n");
}
function say(msg){ document.getElementById("count").textContent = msg; }

document.getElementById("export").onclick = async () => {
  const csv = buildCSV();
  if (!HOSTED){
    const a = document.createElement("a");
    a.href = URL.createObjectURL(new Blob([csv], {type:"text/csv"}));
    a.download = "ab_tool_register.csv"; a.click();
    return;
  }
  const dl = await window.claude.use("downloads");
  if (!dl){ say("Export unavailable in this view — open the file from U:\\ instead."); return; }
  const attempt = async name => dl.save({filename:name, data:csv});
  try { await attempt("ab_tool_register.csv"); draw(); }
  catch(e){
    // csv sits in the extended extension set and may not be enabled here.
    // .txt is always allowed and imports into Sheets just the same.
    if (e && e.code === "extension_not_enabled"){
      try { await attempt("ab_tool_register.csv.txt"); draw(); }
      catch(e2){ say("Export failed: " + ((e2 && e2.code) || "unknown")); }
    } else if (e && e.code === "declined"){ draw(); }
    else { say("Export failed: " + ((e && e.code) || "unknown")); }
  }
};

draw();
</script>
"""


if __name__ == "__main__":
    main()
