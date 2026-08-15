"""Build the AssetBash zone-coverage worklist as a self-contained HTML page.

    python U:/AB_Standardization/build_zone_page.py

Reads zone_coverage.csv (from audit_zone_coverage.py) plus the tool icons, and
writes one page with everything inlined so it can be published as an Artifact -
hosted, shareable, and not lost with a machine.

⭐ CLASS is the thing that makes the audit honest. One standard applied to every
tool is wrong: AB::GroupWalls::2.0 emits no zones because it is a PROCESSOR - it
takes geometry in, groups it, and passes s@name through. Demanding zones of it
would be a defect, not compliance. So each tool carries a class, and each class
has its own contract:

    Generator   makes geometry from nothing   zones REQUIRED, MaterialStyle yes
    Component   block used inside other tools zones REQUIRED, MaterialStyle opt
    Processor   geometry in -> modified out   zones NOT required; must PRESERVE
                                              s@name, never invent it
    Scatter     emits instancing points       contract is s@unreal_instance etc
    Pipeline    the standardization chain     contract only; may not ship
    Deprecated  not in the release            -

Classes here are SUGGESTIONS pre-filled from explicit name/category lists, not a
regex - a loose pattern classified "ResortGenerator" as a helper because
"Re-sort-" contains "sort". Jordan corrects them in the page; the export becomes
config/tool_classes.json.

Editable Class / Priority / Status / Owner / Notes persist in the browser's local
storage. There is no shared-database capability, so the CSV export is how state
is shared or committed.
"""
import csv
import json
import os
import re

CSV = "U:/AB_Standardization/zone_coverage.csv"
ICONS = "U:/Git/AssetBashTools/IconDev/Icons"
OUT = "U:/AB_Standardization/ab_zone_worklist.html"

CLASSES = ["Generator", "Component", "Processor", "Scatter", "Pipeline", "Deprecated"]

# explicit, so a tool is never misclassified by a substring accident
PIPELINE = {
    "MaterialBinding", "MaterialLibrary", "EngineAttributes", "ExportPack",
    "ZoneAudit", "VisTools", "PythonScripter", "CreateLODs", "UnrealTerrainWrite",
}
PROCESSOR = {
    "GroupWalls", "RooftopProcessor", "SidewalkProcessor", "DoorsCreateCopies",
    "WindowsCreateCopies", "CopyByDensity", "CopyWithRotation", "ExtendedSweep",
    "ColorByVelocity", "RadialFalloff", "RadialPointSort", "RadialSmoothNoise",
    "CircularNoise", "CreateRGBNoise", "PointBlends", "ModuleAssembler",
}
SCATTER = {
    "RadialScatter", "RadialScatterVex", "PhylotaxisScatter",
    "MultiAxisPointScatter", "Flocking", "CliffordAttractor",
}
COMPONENT = {
    "SignPlate", "SignLibrary", "SignHighway", "MetalExtrusionMaker",
    "HardwareMaker", "DoorHardware", "PipesAndEnds", "FancyCurves",
    "PanelGenerator", "ElectricalParts", "SimplePipe", "FlangeGenerator",
    "ValveGenerator", "ArchitecturalPlantOns",
}


def short(type_name):
    m = re.match(r"^AB::([^:]+)", type_name)
    return m.group(1) if m else type_name


def suggest_class(type_name, category):
    s = short(type_name)
    if s in PIPELINE:
        return "Pipeline"
    if s in PROCESSOR:
        return "Processor"
    if s in SCATTER:
        return "Scatter"
    if s in COMPONENT:
        return "Component"
    if s.startswith("Modules") or s.startswith("MModules"):
        return "Component"
    if category == "Utilities":
        return "Pipeline"
    return "Generator"


def icon_for(type_name):
    s = short(type_name)
    for cand in ("SOP_AB__%s.svg" % s, "HDA_%s.svg" % s):
        p = os.path.join(ICONS, cand)
        if os.path.isfile(p):
            with open(p, "r", encoding="utf-8", errors="replace") as fh:
                t = fh.read()
            t = re.sub(r"<\?xml.*?\?>", "", t, flags=re.S)
            t = re.sub(r"<!DOCTYPE.*?>", "", t, flags=re.S)
            return t.replace("<svg", '<svg class="ic" aria-hidden="true"', 1).strip()
    return ""


def main():
    rows = list(csv.DictReader(open(CSV, encoding="utf-8")))
    data = []
    for r in rows:
        data.append({
            "tool": r["Tool"],
            "label": r["Label"],
            "cat": r["Category"],
            "file": r["File"],
            "cook": r["Cook"],
            "has": r["HasZones"],
            "n": int(r["ZoneCount"] or 0),
            "zones": [z for z in r["Zones"].split(" ") if z],
            "bad": [z for z in r["NonCanonical"].split(" ") if z],
            "cls": suggest_class(r["Tool"], r["Category"]),
            "icon": icon_for(r["Tool"]),
        })
    data.sort(key=lambda d: (d["cat"], d["tool"]))

    doc = TEMPLATE
    doc = doc.replace("__DATA__", json.dumps(data).replace("</", "<\\/"))
    doc = doc.replace("__CATS__", json.dumps(sorted({d["cat"] for d in data})))
    doc = doc.replace("__CLASSES__", json.dumps(CLASSES))

    with open(OUT, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(doc)
    counts = {}
    for d in data:
        counts[d["cls"]] = counts.get(d["cls"], 0) + 1
    print("wrote %s  (%.0f KB)" % (OUT, os.path.getsize(OUT) / 1024.0))
    print("   tools: %d" % len(data))
    for k in CLASSES:
        if counts.get(k):
            print("      suggested %-11s %d" % (k, counts[k]))


TEMPLATE = r"""<title>AssetBash Zone Coverage</title>
<style>
:root{
  --bg:#f4f2ef; --panel:#fffefc; --line:#ddd7cf; --ink:#22201d; --dim:#6d675f;
  --accent:#b4531f; --accent-soft:#f0e2d8;
  --ok:#2f6b46; --ok-bg:#e2efe7; --warn:#8a6410; --warn-bg:#f6ecd6;
  --bad:#98341f; --bad-bg:#f6e0da; --mut:#5b5751; --mut-bg:#eae6e0;
  --mono:ui-monospace,"SFMono-Regular",Menlo,Consolas,monospace;
}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){
  --bg:#1a1917; --panel:#232120; --line:#38342f; --ink:#ece8e2; --dim:#9b938a;
  --accent:#e08a52; --accent-soft:#3a2a20;
  --ok:#7fc19a; --ok-bg:#1e3227; --warn:#d9b465; --warn-bg:#332a17;
  --bad:#e39079; --bad-bg:#3a221c; --mut:#9b938a; --mut-bg:#2b2825;}}
:root[data-theme="dark"]{
  --bg:#1a1917; --panel:#232120; --line:#38342f; --ink:#ece8e2; --dim:#9b938a;
  --accent:#e08a52; --accent-soft:#3a2a20;
  --ok:#7fc19a; --ok-bg:#1e3227; --warn:#d9b465; --warn-bg:#332a17;
  --bad:#e39079; --bad-bg:#3a221c; --mut:#9b938a; --mut-bg:#2b2825;}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);
  font:15px/1.5 ui-sans-serif,system-ui,-apple-system,"Segoe UI",sans-serif}
.wrap{max-width:1620px;margin:0 auto;padding:28px 20px 80px}
h1{font-size:24px;margin:0 0 2px;letter-spacing:-.01em}
.sub{color:var(--dim);font-size:14px;margin:0 0 20px;max-width:80ch}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:10px;margin-bottom:18px}
.card{background:var(--panel);border:1px solid var(--line);border-radius:9px;padding:13px 15px}
.card .n{font-size:26px;font-weight:600;font-variant-numeric:tabular-nums;line-height:1.1}
.card .k{font-size:11px;text-transform:uppercase;letter-spacing:.07em;color:var(--dim);margin-top:3px}
.card.hot .n{color:var(--accent)}
.bar{display:flex;flex-wrap:wrap;gap:8px;align-items:center;margin-bottom:14px}
input[type=search],select{background:var(--panel);color:var(--ink);border:1px solid var(--line);
  border-radius:7px;padding:7px 10px;font:inherit;font-size:14px}
input[type=search]{min-width:220px}
button{background:var(--accent);color:#fff;border:0;border-radius:7px;padding:8px 14px;
  font:inherit;font-size:14px;font-weight:500;cursor:pointer}
button.ghost{background:transparent;color:var(--ink);border:1px solid var(--line)}
button:focus-visible,select:focus-visible,input:focus-visible,[contenteditable]:focus-visible{
  outline:2px solid var(--accent);outline-offset:2px}
.tablewrap{overflow-x:auto;background:var(--panel);border:1px solid var(--line);border-radius:9px}
table{border-collapse:collapse;width:100%;font-size:13.5px}
th{position:sticky;top:0;background:var(--panel);border-bottom:1px solid var(--line);
  text-align:left;padding:9px 10px;font-size:11px;text-transform:uppercase;
  letter-spacing:.06em;color:var(--dim);white-space:nowrap;z-index:2}
td{border-bottom:1px solid var(--line);padding:7px 10px;vertical-align:top}
tr:last-child td{border-bottom:0}
.ic{width:26px;height:26px;display:block}
.tool{font-family:var(--mono);font-size:12.5px;white-space:nowrap}
.lab{color:var(--dim);font-size:12px}
.pill{display:inline-block;padding:2px 8px;border-radius:999px;font-size:11px;font-weight:600;white-space:nowrap}
.p-ok{background:var(--ok-bg);color:var(--ok)}
.p-no{background:var(--bad-bg);color:var(--bad)}
.p-warn{background:var(--warn-bg);color:var(--warn)}
.p-mut{background:var(--mut-bg);color:var(--mut)}
.num{font-variant-numeric:tabular-nums;text-align:right}
.zones{font-family:var(--mono);font-size:11px;color:var(--dim);max-width:300px;line-height:1.45;word-break:break-word}
.zones .bd{color:var(--bad);font-weight:600}
select.cls{min-width:104px}
select.pri{min-width:62px}
select.st{min-width:78px}
select.sug{border-style:dashed;color:var(--dim)}
.ed{min-width:90px;min-height:22px;border:1px solid transparent;border-radius:5px;padding:3px 5px;font-size:13px}
.ed:hover{border-color:var(--line)}
.ed:empty::before{content:attr(data-ph);color:var(--dim);opacity:.55}
.note{background:var(--accent-soft);border:1px solid var(--line);border-left:3px solid var(--accent);
  border-radius:7px;padding:11px 14px;margin:0 0 18px;font-size:13.5px}
.foot{color:var(--dim);font-size:12px;margin-top:16px;max-width:90ch}
code{font-family:var(--mono);font-size:.92em}
</style>

<div class="wrap">
<h1>AssetBash Zone Coverage</h1>
<p class="sub">Every latest-version AB tool, measured by cooking it and reading <code>s@name</code>.
Zone coverage gates the material system &mdash; without zones, <code>AB::MaterialBinding</code> has
nothing to key off and no Principled branch can be generated. <strong>Class decides which contract
applies</strong>: a Processor emitting no zones is correct, not a defect.</p>

<div class="cards" id="cards"></div>

<p class="note"><strong>Classes are suggestions</strong> &mdash; shown dashed until you confirm or change
one. They come from explicit name lists, not pattern matching: a loose regex classified
<code>ResortGenerator</code> as a helper because &ldquo;Re<em>sort</em>&rdquo; contains &ldquo;sort&rdquo;.
<strong>&ldquo;Did not cook&rdquo; means unmeasured, not broken</strong> &mdash; those tools were instanced
with no input, and processors legitimately need upstream geometry.
<strong>Packing keys are excluded</strong> from all counts: <code>piece0</code>-style names are unique per
piece, not shading zones.</p>

<div class="bar">
  <input type="search" id="q" placeholder="Search tool, label, zone&hellip;" aria-label="Search">
  <select id="cat" aria-label="Category"><option value="">All categories</option></select>
  <select id="cls" aria-label="Class"><option value="">All classes</option></select>
  <select id="filt" aria-label="Filter">
    <option value="">All tools</option>
    <option value="gap">Needs zones (by class)</option>
    <option value="bad">Non-canonical names</option>
    <option value="err">Did not cook</option>
    <option value="todo">Unset priority</option>
    <option value="unconf">Unconfirmed class</option>
  </select>
  <select id="sort" aria-label="Sort">
    <option value="cat">Sort: category</option>
    <option value="pri">Sort: priority</option>
    <option value="zones">Sort: zone count</option>
    <option value="tool">Sort: name</option>
  </select>
  <button id="exp">Export CSV</button>
  <button class="ghost" id="clr">Clear my edits</button>
  <span class="lab" id="count"></span>
</div>

<div class="tablewrap">
<table>
<thead><tr>
  <th></th><th>Tool</th><th>Category</th><th>Class</th><th class="num">Zones</th>
  <th>State</th><th>Zone names</th><th>Pri</th><th>Status</th><th>Owner</th><th>Notes</th>
</tr></thead>
<tbody id="tb"></tbody>
</table>
</div>
<p class="foot">Class, Priority, Status, Owner and Notes are saved in this browser only &mdash; no shared
database is available to this page. <strong>Export CSV</strong> to hand the state back, commit it, or
turn it into <code>config/tool_classes.json</code>.</p>
</div>

<script>
const DATA = __DATA__, CATS = __CATS__, CLASSES = __CLASSES__;
const KEY = "ab_zone_worklist_v2";
let edits = {};
try { edits = JSON.parse(localStorage.getItem(KEY) || "{}"); } catch(e){ edits = {}; }
const save = () => { try{ localStorage.setItem(KEY, JSON.stringify(edits)); }catch(e){} };
const get  = (t,f) => (edits[t] && edits[t][f]) || "";
const set  = (t,f,v) => { (edits[t] = edits[t] || {})[f] = v; save(); };
const cls  = d => get(d.tool,"cls") || d.cls;
const confirmed = d => !!get(d.tool,"cls");

// only these classes owe zones
const NEEDS_ZONES = {Generator:1, Component:1};

function state(d){
  if (d.cook !== "OK") return ["p-mut","unmeasured"];
  if (d.bad.length)    return ["p-warn","non-canonical"];
  if (NEEDS_ZONES[cls(d)] && d.has === "NO") return ["p-no","needs zones"];
  if (d.has === "YES") return ["p-ok","ok"];
  return ["p-ok","n/a for class"];
}

const el = id => document.getElementById(id);
CATS.forEach(c => el("cat").add(new Option(c,c)));
CLASSES.forEach(c => el("cls").add(new Option(c,c)));

function cards(){
  const gaps = DATA.filter(d => d.cook==="OK" && NEEDS_ZONES[cls(d)] && d.has==="NO").length;
  const ok   = DATA.filter(d => d.has==="YES").length;
  const bad  = DATA.filter(d => d.bad.length).length;
  const err  = DATA.filter(d => d.cook!=="OK").length;
  const unc  = DATA.filter(d => !confirmed(d)).length;
  el("cards").innerHTML =
    card(DATA.length,"tools") + card(gaps,"needs zones","hot") +
    card(ok,"emit zones") + card(bad,"non-canonical") +
    card(err,"unmeasured") + card(unc,"class unconfirmed");
}
const card = (n,k,c="") => '<div class="card '+c+'"><div class="n">'+n+'</div><div class="k">'+k+'</div></div>';

function render(){
  const q = el("q").value.toLowerCase().trim(), cat = el("cat").value,
        cf = el("cls").value, filt = el("filt").value, sort = el("sort").value;
  let rows = DATA.filter(d => {
    if (cat && d.cat !== cat) return false;
    if (cf && cls(d) !== cf) return false;
    if (filt==="gap"    && !(d.cook==="OK" && NEEDS_ZONES[cls(d)] && d.has==="NO")) return false;
    if (filt==="bad"    && !d.bad.length) return false;
    if (filt==="err"    && d.cook==="OK") return false;
    if (filt==="todo"   && get(d.tool,"pri")) return false;
    if (filt==="unconf" && confirmed(d)) return false;
    if (q && !((d.tool+" "+d.label+" "+d.cat+" "+d.zones.join(" ")).toLowerCase().includes(q))) return false;
    return true;
  });
  const P = d => get(d.tool,"pri") || "9";
  if (sort==="pri")   rows.sort((a,b)=>P(a).localeCompare(P(b))||a.tool.localeCompare(b.tool));
  if (sort==="zones") rows.sort((a,b)=>a.n-b.n||a.tool.localeCompare(b.tool));
  if (sort==="tool")  rows.sort((a,b)=>a.tool.localeCompare(b.tool));
  if (sort==="cat")   rows.sort((a,b)=>a.cat.localeCompare(b.cat)||a.tool.localeCompare(b.tool));

  const tb = el("tb"); tb.textContent="";
  const frag = document.createDocumentFragment();
  rows.forEach(d => {
    const tr = document.createElement("tr");
    const [c,t] = state(d);
    const zh = d.zones.length
      ? d.zones.map(z => d.bad.includes(z) ? '<span class="bd">'+z+'</span>' : z).join(" ")
      : '<span style="opacity:.5">&mdash;</span>';
    tr.innerHTML =
      '<td>'+(d.icon||'')+'</td>'+
      '<td><div class="tool">'+d.tool+'</div><div class="lab">'+(d.label||'')+'</div></td>'+
      '<td class="lab">'+d.cat+'</td><td></td>'+
      '<td class="num">'+(d.cook==="OK"?d.n:"&mdash;")+'</td>'+
      '<td><span class="pill '+c+'">'+t+'</span></td>'+
      '<td class="zones">'+zh+'</td><td></td><td></td><td></td><td></td>';
    const td = tr.querySelectorAll("td");
    td[3].appendChild(classSel(d));
    td[7].appendChild(sel("pri", d.tool, ["","1","2","3","4","5"], "pri"));
    td[8].appendChild(sel("st",  d.tool, ["","To do","Doing","Done","N/A"], "st"));
    td[9].appendChild(ed(d.tool,"own","owner"));
    td[10].appendChild(ed(d.tool,"note","notes"));
    frag.appendChild(tr);
  });
  tb.appendChild(frag);
  el("count").textContent = rows.length+" of "+DATA.length+" shown";
  cards();
}

function classSel(d){
  const s = document.createElement("select");
  s.className = "cls" + (confirmed(d) ? "" : " sug");
  CLASSES.forEach(c => s.add(new Option(c,c)));
  s.value = cls(d);
  s.title = confirmed(d) ? "confirmed" : "suggested \u2014 change or re-pick to confirm";
  s.addEventListener("change", () => { set(d.tool,"cls",s.value); render(); });
  return s;
}
function sel(k,tool,opts,field){
  const s = document.createElement("select"); s.className = k;
  opts.forEach(o => s.add(new Option(o||"\u2014", o)));
  s.value = get(tool,field);
  s.addEventListener("change", ()=>{ set(tool,field,s.value); render(); });
  return s;
}
function ed(tool,field,ph){
  const d = document.createElement("div");
  d.className="ed"; d.contentEditable="true"; d.dataset.ph=ph;
  d.textContent = get(tool,field);
  d.addEventListener("blur", ()=>set(tool,field,d.textContent.trim()));
  return d;
}

["q","cat","cls","filt","sort"].forEach(i => el(i).addEventListener("input", render));
el("clr").addEventListener("click", ()=>{
  if(!confirm("Clear Class, Priority, Status, Owner and Notes for every tool in this browser?")) return;
  edits={}; save(); render();
});
el("exp").addEventListener("click", async ()=>{
  const cols=["Tool","Label","Category","File","Class","ClassConfirmed","Cook",
              "HasZones","ZoneCount","Zones","NonCanonical","Priority","Status","Owner","Notes"];
  const esc=v=>'"'+String(v==null?"":v).replace(/"/g,'""')+'"';
  const lines=[cols.join(",")];
  DATA.forEach(d=>lines.push([d.tool,d.label,d.cat,d.file,cls(d),confirmed(d)?"yes":"suggested",
    d.cook,d.has,d.n,d.zones.join(" "),d.bad.join(" "),
    get(d.tool,"pri"),get(d.tool,"st"),get(d.tool,"own"),get(d.tool,"note")].map(esc).join(",")));
  const downloads = await window.claude?.use?.("downloads");
  if(!downloads){ alert("Download is not available in this view."); return; }
  try { await downloads.save({filename:"zone_coverage_edited.csv", data:lines.join("\n")}); }
  catch(e){ alert("Download was cancelled or failed."); }
});

render();
</script>
"""

if __name__ == "__main__":
    main()
