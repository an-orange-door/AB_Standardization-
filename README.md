# AB_Standardization

Work products for the AssetBash standardization campaign — the analysis, the
plans, the rewrites and the verification scripts. **The HDA library itself lives
in a separate repo** (`AssetBashTools`); nothing here is a shipping asset, and
`.hda` files are gitignored so the library is never duplicated.

## Layout

| Path | What it is |
|---|---|
| `analysis/` | Full-library sweep output — `tools`, `parms`, `menus`, `nesting`, `orphan_literals` |
| `baseline/` | **Verification oracles.** Captured BEFORE a rewrite so it can be judged after |
| `research/` | The architectural research: roof typology + maths, the footprint plan |
| `moulding/` | The WM moulding profile grammar prototype + SVG sheet |
| `vex/` | VEX source installed into HDAs |
| `schema_draft/` | Typology / variation schema drafts |
| `*.py` | Audit, build and verification scripts. Most need `hython` with the GUI closed |

## The habit this repo exists to support

**Measure the BEFORE state, then change.** A MaterialStyle migration was once
reverted because 31 apparent failures turned out to be pre-existing breakage
nobody had baselined — the rewrite could not be judged because there was no
before. Every rewrite since carries an oracle:

- `parity_test_extrusions.py` — 135 cases, proved the MetalExtrusionMaker rewrite
- `footprint_baseline.py` → `baseline/footprint_baseline.json` — 162 cases,
  captured before the BuildingFootprintGenerator rewrite

## Running the scripts

Most need the Houdini GUI **closed** — there is one FX seat, and hython will
take it. `hotl -X` expansion and anything pure-Python run fine alongside a live
session.

    hython U:/AB_Standardization/<script>.py
