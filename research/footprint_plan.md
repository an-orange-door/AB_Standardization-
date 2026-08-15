# Building Footprints — the MetalExtrusionMaker treatment

Plan drafted 2026-08-15 at Jordan's request: *"I would like to think about the floorplan
tool and starting to fix it along the lines of the metal extrusion maker."* (Confirmed:
building footprints, **not** interior room plans.)

---

## 0. The situation, measured

**`AB::BuildingFootprintGenerator::1.0` already exists** — `Sops/Buildings/`, 6 parms,
186 inner nodes, menu `0 Rectangular · 1 L · 2 Rounded Corner`, nested by
`SkyscraperGenerator::2.1`. The extraction was started and never finished.

**Four tools still carry an inline copy** of the same machinery (measured by expanding every
Buildings / CityGen / BuildingHelpers / BuildingProps HDA with `hotl -X` and grepping for
`CreateBldBase`, `Corner_01`, `FootprintSquare`, `BaseFromCurve`):

| Tool | CreateBldBase | Corner_01 | BaseFromCurve |
|---|---|---|---|
| `DowntownBuilding 3.6` | 12 | 11 | 6 |
| `DestructionBuilding 1.0` | 12 | 11 | 6 |
| `ApartmentRow 1.2` | 6 | 11 | 3 |
| `VictorianHouses 1.1` | 7 | 11 | — |
| `BuildingFootprintGenerator 1.0` | — | 9 | — |

Inside `DowntownBuilding`, `CreateBldBase` is **277 nodes for three shapes**, plus 73 nodes of
abandoned work (`FootprintU`, `FootprintRound`, `FootprintSquare1` — all with no outputs).

**The disease, stated exactly:** the node count scales with EDGE COUNT.
`FootprintSquare` (4 edges) has 8 `groupcreate` / 8 `color` / 8 `attribcreate` / 16 `switch`;
`FootprinL` (6 edges) has 12 of each and 24 switches. Groups are hand-named —
`WallLeft/Front/Right/Back` + `Corner_01…Corner_04`. Adding a U means hand-authoring 8 walls
and 8 corners, which is why `FootprintU` was abandoned half-built.

---

## 1. The parallel is exact

| MetalExtrusionMaker (done) | BuildingFootprintGenerator (proposed) |
|---|---|
| 6 Add SOPs, ~70 interdependent hscript expressions | 3 subnets, 277 nodes, per-edge groups |
| `ext_type` menu 0–4 | `BuildingShape` menu 0–2 |
| One Detail wrangle emits any profile | One wrangle emits any footprint |
| `width` · `height` · `thick` | `BuildingWidth` · `BuildingDepth` · `BldCornerSize` |
| Menu appended 5–9, 0–4 untouched | Menu appended 3+, 0–2 untouched |
| Parity 135/135 before the swap | Parity on the 3 shapes before the swap |
| 8 dependent tools | 5 dependent tools |
| Found a bug nobody knew about (Square Tube) | Expect the same |

**And the same trap applies.** MetalExtrusionMaker taught that **winding must be enforced, not
assumed** — measured with the shoelace formula and corrected. A footprint gets *extruded*, so
its winding decides which way the wall normals face. Enforce it in the generator; do not hope
the point order was typed correctly for eight shapes.

---

## 2. The design — three layers, and only the middle one is new

### Layer 1 · OUTLINE — where the polygon comes from
Two sources, one output:
- **Parametric shapes**, one point list per menu entry in a single wrangle (the MEM pattern).
- **An input curve** — `BaseFromCurve` today, which becomes a first-class input rather than a
  degraded path.

Most real building footprints are **rectilinear compositions of rectangles**: L, U, T, cross
and courtyard are one to three rectangles unioned or notched. That is worth *knowing* while
authoring the point lists, but a **named menu with clean parms beats a generic boolean rig**
for a shipping tool — keep the menu, drop the subnets.

### Layer 2 · CLASSIFY — the actual payload ⭐
For **any** closed planar polygon, compute what is currently hand-named:

```
per vertex:  turn angle from incoming/outgoing edge
             sign of the cross-product z  ->  convex (+) or reflex (−)
             i@corner_id, f@corner_angle, i@corner_convex
per edge:    length, direction, i@wall_id
             s@name zone, and the legacy group name
```

This is the whole fix. It works identically on a menu shape and on an arbitrary curve, so
**one code path serves both** and new shapes cost zero new nodes.

⚠ **This is the same layer the roof work needs.** `w_e = cot θ_e` makes per-edge pitch a
per-edge weight, so the roof's input *is* this classification. Build it once — see
`Architectural Plans`.

### Layer 3 · TREAT — corners, by angle band
`square | chamfer | round | none`, selected from a **catalog keyed by angle band**, the same
column-lookup as `SignLibrary`'s SizeClass. Driven by the existing `BldCornerSize` /
`BldCornerDepth`.

⚠ **Convex and reflex need opposite operations** — an outer chamfer versus an inner fillet.
The current sphere-bounding method cannot tell them apart, which is precisely why an L's inner
corner is wrong today.

---

## 3. What today's corner mechanism actually is, and why it caps out

`BaseFromCurve` finds corners by **bounding object**: resample the curve at `BaseModSize`,
copy a sphere onto each ORIGINAL curve point, group the resampled points that land inside.

The instinct is right. Four limits:
1. **The sphere is a fixed absolute size** — `rad 0.5 × scale 0.1` ≈ 0.05 units. It does not
   scale with `BldCornerSize` (3.0) or with the resample length, so corner capture is a
   constant radius at any building size.
2. **It cannot measure the corner angle** — 90° and 175° group identically.
3. **It cannot detect reflex corners.**
4. **It groups points, not edges** — so there is no per-wall classification at all.

That fourth point is the ceiling: downstream modules consume `MF_walls`, `BldBase`,
`BldCorners`, `extrudePlane`. **Those group names are the contract**, and a curve input can
never produce them today.

---

## 4. The plan

**Phase 0 · BASELINE — before changing anything.**
Standing lesson from the MaterialStyle migration: *measure the BEFORE state, then change.*
Sweep `BuildingShape` 0–2 × a range of width/depth/corner size, and record for each: point
positions (ordered and sorted), the full group list with membership counts, prim count,
winding, and bbox. This is the parity oracle. **Do it first or the rewrite is unfalsifiable.**

**Phase 1 · The classification wrangle**, standalone and testable on its own.
Verify: an N-gon yields exactly N wall groups and N corner groups; a known L reports exactly
one reflex corner; angles sum to (n−2)·180°.

**Phase 2 · The shape wrangle** — the 3 shipping shapes as point lists, winding enforced.
Gate: **parity against Phase 0, ordered and sorted separately.** Ordered failure with sorted
pass means winding or start vertex only — a much smaller fix than bad maths.

**Phase 3 · Corner treatment by angle band**, replacing the sphere method. Gate: the 3 shapes
still match; the L's inner corner now behaves differently from its outer corners.

**Phase 4 · New shapes, APPENDED** — `3 U · 4 T · 5 Cross · 6 Courtyard · 7 Chamfered ·
8 Angled`. `BuildingShape` 0–2 must not move; abort the build if they do.
(`FootprintU` already exists half-built and can seed the U point list.)

**Phase 5 · Repoint the copies — one tool at a time, biggest risk, last.**
`SkyscraperGenerator` already consumes the HDA, so it validates first for free. Then
`VictorianHouses` → `ApartmentRow` → `DestructionBuilding` → `DowntownBuilding` (last: it is
the largest and most depended-on). Each repoint gated by a cook-and-compare against a saved
baseline of that tool's output.

---

## 5. Verification — what makes it provable

- **Parity** on shapes 0–2, ordered and sorted separately, across a width/depth/corner sweep.
- **N-gon → N wall groups + N corner groups.** The Euler-style count that catches the whole
  class of classification bugs.
- **Interior angles sum to (n−2)·180°**, and exactly one reflex corner on an L.
- **Winding consistent** across every shape — footprints get extruded, so this decides normals.
- **Closed, planar, non-self-intersecting** for every parameter combination, including
  degenerate ones (corner size larger than the wall it sits on).
- **Legacy group names still emitted**, or every downstream building tool breaks.

---

## 6. Where standards attach later

`ModuleWidth` (default 10.0) is already a structural bay parameter — that is the hook for a
catalog of real bay spacings. Lot coverage, setbacks and corner radii are zoning facts and
belong in the same `config/catalogs/` CSV pattern as signs, hardware and mouldings.
Not Phase 1 work, but the parm to build the plan around.

---

## 6b. THE NAMING STANDARD — Jordan's call: *"fix any name inconsistencies and standardize anything we can"*

### ⭐ How group names are actually authored — measured, and it changes the risk
**All 30 `groupcreate` nodes set `groupname` to the expression `` `opname(".")` `` — the group
name IS the node name.** So standardising is mechanically a *node rename*.
⚠ **That inverts the standing rule.** `[[naming-convention-pascalcase]]` says node renames are
safe and group / `s@name` renames are not. **Here a node rename IS a group rename**, because
the group name is derived from it. Treat every rename in this tool as breaking.

### The measured defects
| Shape | Walls | Corners | Defects |
|---|---|---|---|
| Rectangular | 4 | 4 | — |
| L | 6 | 6 | **mixed suffix style** — `WallRight_01` beside a bare `WallLeft` |
| RoundedCorner | 4 | 5 | **`WallRight1`** (bare digit, vs `_01` elsewhere) · **`arc`** (lowercase, a working group not a zone) · **walls ≠ corners** |

### ⛔ The deepest problem: compass names cannot generalise
`WallLeft` / `WallFront` / `WallRight` / `WallBack` work for a rectangle and **nothing else**.
A U has 8 walls, a courtyard 8, an arbitrary curve N. **There is no "Front" on a 12-gon.**
So compass naming is not merely untidy — it is *structurally incompatible* with the
classification approach, and no amount of tidying rescues it. This is a redesign, and it is
the real reason to do it now rather than after release, when the names become public API.

### The proposed standard
```
Wall_01 … Wall_NN        one per input edge, zero-padded
Corner_01 … Corner_NN    one per vertex
```
- **Index follows the polygon winding** from a deterministic start vertex. Rule: **the vertex
  nearest the bounding-box minimum corner, walking counter-clockwise.** It must be documented
  and stable, because if the start vertex moves when a parameter changes, every wall index
  shuffles and every downstream binding silently rebinds to the wrong wall.
- ⭐ **`Corner_i` sits between `Wall_i` and `Wall_i+1`.** There is *no such relation today* —
  corner and wall numbering are independent. Establishing it is most of the value: a consumer
  can then find the walls adjoining any corner arithmetically.
- **Convex/reflex is an ATTRIBUTE, not a name** — `i@corner_convex`, `f@corner_angle`. Encoding
  it in the name would repeat the compass mistake.
- **`arc` is a working group** — either drop it from the output or promote it to `CornerArc`.
  Lowercase violates the PascalCase standing rule either way.
- **Legacy aliases** behind a `LegacyGroupNames` toggle, default ON for one release: emit
  `WallLeft/Front/Right/Back` *in addition* for the rectangular case only, documented as
  deprecated. That is what lets the four copies be repointed one at a time instead of in a
  single flag-day commit.

### Verification for the rename
- Every shape: **N walls, N corners, and `Corner_i` adjoins `Wall_i` / `Wall_i+1`.**
- Every group name matches `^(Wall|Corner)_[0-9]{2}$` — a regex gate in the test, so drift
  cannot creep back.
- With `LegacyGroupNames` on, the three shipping shapes produce a **superset** of today's
  groups with identical membership.

## 7. Honest risks

- ✅ **DECIDED (Jordan, 8/15): fix the names and standardise.** See §6b. The risk moves from
  "which ugliness do we preserve" to "how do we migrate five consumers safely" — answered by
  the `LegacyGroupNames` alias toggle, which lets the repoint happen one tool at a time.
- **Five tools depend on this**, four by private copy. A repoint that changes group membership
  silently is the failure mode to fear, which is why Phase 5 is last and gated per tool.
- **`DowntownBuilding` is 117 MB and 12,143 nodes.** Editing it is slow and each save writes a
  backup. Batch its changes into one commit.
