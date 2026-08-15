# Roof Typology, Geometry and Code — a generative system for AssetBash

**Author:** roof-architect (agent)
**Date:** 2026-08-15
**Status:** research report. Nothing here has been built yet.
**Scope:** the mathematics that turns a plan outline into a roof; the roof forms
worth having; the code and zoning that produce regional difference; and the
smallest generative vocabulary that spans it, expressed in AssetBash terms.

---

---

## Summary

**The vocabulary.** Four operators span the whole typology:

1. **`SKELETON`** — a weighted straight skeleton, lifted by a banded section
   profile. Takes a footprint, a per-edge weight vector, and an ordered list of
   bands. **Absorbs fourteen of the eighteen named roof forms with no branching**,
   including hip-and-valley and cross-gable, which turn out not to be separate
   types at all.
2. **`SWEEP`** — a periodic section along an axis, clipped to the footprint.
   Sawtooth, folded plate, repeated monitors and vaults.
3. **`INSERT`** — a sub-mass booleaned into a face. Dormers, bulkheads, tanks,
   chimneys, skylights, cupolas.
4. **`TRIM`** — a profile swept along a classified skeleton edge. Eave, rake,
   ridge, hip, valley, coping, cornice. **This is where all of STYLE lives.**

The hinge identity is `w_e = cot θ_e` — **per-edge pitch is per-edge wavefront
speed**. Set two weights to zero and a hip becomes a gable; set three and it
becomes a shed. And the band profile, drawn in (run, rise), **is a moulding
profile** — same curve, same authoring problem, so `moulding_grammar.py`'s ten
elements are the roof section library, reused rather than rewritten.

**Footprint-derivable or not.** Eight forms come from the outline alone or from
the outline plus a handful of *bits* (gable, hip, pyramidal, hip-and-valley,
cross-gable, shed, butterfly, and — via the classical semicircle construction —
**gambrel**). Six need exactly one scalar (jerkinhead, Dutch gablet, saltbox,
flat-with-parapet, barrel, dome). Two need two scalars (mansard, monitor). Three
are **not footprint problems at all** (sawtooth, folded plate, and every dormer),
because their generators — a direction, a period, a room — are not in the
perimeter. §1.9 states each minimum extra input exactly.

**The most useful code findings.**

- **NYC ZR 23-421 is a straight-skeleton envelope written into law**: walls to 25
  ft, sloping planes converging on a **35 ft ridge line**, max face angle **80°**.
  Pitch is therefore a *consequence of plan depth* — `atan(10/(D/2))`.
- **The three cities reward a pitched roof in three incompatible ways.** SF pays
  **continuously** (measured to the *midrise*, so half the rise is free,
  uncapped). LA pays a **flat bounty at a single gate** (+5 or +6 ft, only at
  slope ≥ 25 %). NYC pays **nothing** and draws the envelope instead. That yields
  three different pitch *distributions* from one line of policy each — and an
  LA-specific **spike at exactly 3:12**.
- **Parapets** are free in SF (≤ 4 ft, exempt from the area cap too), pinned into
  a **6-inch window** in NYC (BC 1510.8 requires ≥ 42 in, ZR 23-411(f) permits
  ≤ 4 ft), and **counted in full** in LA.
- SF budgets rooftop clutter by **area** (30 %, → 40 % if screened); LA by **feet
  and setback** with no area cap at all; NYC by **coverage tier plus a street-wall
  setback**. Three visibly different rooftops, three columns of a CSV.
- **IRC R905** gives a hard, citable floor on pitch per covering material —
  slate 4:12, asphalt 2:12, standing seam ¼:12 — which is the honest way to
  clamp a pitch slider.

**What surprised me.**

- **Rectilinear footprints are the *degenerate* case for the straight skeleton,
  not the general one.** For *any* rectilinear L, the reflex vertex's split event
  and an edge-collapse event are **always simultaneous**, at `t = min(w,h)/2`.
  Since city footprints are overwhelmingly rectilinear, the tie is the normal
  condition and deterministic tie-breaking is mandatory, not defensive.
- **The framing folk rule for the hip backing bevel — `tan β = sin(θ_hip)` — is
  only true at a square corner.** At a 120° plan corner and 6:12 it is off by
  10.5° and in the wrong direction. Since a skeleton roof produces hips at every
  plan angle, the general formula is required.
- **The gambrel is footprint-derivable** via the classical semicircle
  construction, *and* it can explain itself: at the same 12 ft ridge height over
  a 24 ft span it yields **75.8 %** of the span with ≥ 7 ft of clear headroom
  against a 12:12 gable's **41.7 %**. The form is a volume optimisation, not a
  decoration.
- **`polyexpand2d` already computes the weighted straight skeleton natively** —
  its "Inside Scale" local attribute *is* `cot θ_e` — and it is used **nowhere**
  in the 155-HDA library.
- **Los Angeles's new *form-based* code regulates roof form less than the code it
  replaces.** A full-text search of the 98-page Chapter 1A Article 2 for "pitch",
  "slope", "gable", "hip roof" and "dormer" returns **zero hits**.
- **NYC's sky exposure plane has been demoted to an opt-in alternative** since
  2024-12-05. The stepped-ziggurat massing is now the rule for what is standing,
  not for what is built.

**What I could not verify.** The ASCE 7 primary text (paywalled — the 7:12 /
½:12 window is corroborated by secondary sources only, and the degree
conversions are derived rather than read); the IRC habitable-attic *wording*;
the IBC low-slope *section attribution*; NYC ZR 33-42 entirely; all NYC Building
Code text beyond a secondary publisher; the City of Yes old→new section mapping,
which DCP appears not to publish; and which geographies LAMC Chapter 1A is
currently operative in. Each is flagged in place. One fabricated "verbatim" code
quotation was caught and discarded during the research — recorded in §3.5,
because that failure mode is exactly what the confidence marks exist to catch.

---

## 0. How to read the confidence marks

This project treats an unmarked recalled number as a defect, so every figure
below carries one of four marks. They are used consistently and they mean
different things.

| Mark | Meaning |
|---|---|
| **[derived]** | Follows from geometry. Computed and checked numerically in `roof_math_check.py` (see §1.10). Self-verifying — re-run the script. |
| **[cited]** | Read from a source I fetched. Section number and URL given in §6. |
| **[trade]** | From a trade or vendor page, not a standard. Directionally right, not authoritative. Do not put it in a spec. |
| **[UNVERIFIED]** | Recalled, not read. Treat as a placeholder that must be checked before it drives geometry or ships. |

Units: framing arithmetic is in feet and inches because that is the unit the
standards and the round numbers live in. AssetBash data is metres, per the
convention already set in `schema_draft/typologies_mutcd_sign_installation.json`.
Imperial originals are kept alongside for the same reason that file keeps them.

---

## 1. The mathematics: footprint → roof

### 1.1 The one construction that does most of the work

Take the plan outline as a simple polygon. Move every edge inward,
perpendicular to itself, all at the same speed. The polygon shrinks. Its
vertices trace paths. **Those traces are the straight skeleton**, and if you
lift each trace point to a height proportional to how long it has been moving,
you get exactly the hip-and-valley roof a framer would build over that plan.

CGAL's manual states the mechanism plainly:

> "Wavefronts (or grassfires) are spawned at each edge of the polygon, and are
> moving inward." … "Polygon vertices move along the angular bisector of the
> lines subtending the edges, at a speed that depends on the angle between the
> two incident contour edges."

and the roof property explicitly:

> "Given a polygonal roof, the straight skeleton directly gives the layout of
> each tent. If each skeleton edge is lifted from the plane a height equal to
> its offset distance, the resulting roof is 'correct' in that water will always
> fall down to the contour edges."

[cited — CGAL 6.2, *2D Straight Skeleton and Polygon Offsetting*]

Everything below is that one sentence, taken seriously.

The construction was introduced for exactly this purpose: Aichholzer, Alberts,
Aurenhammer and Gärtner proposed the skeleton in 1995 as a tool for automatic
roof construction over irregular ground plans, avoiding overlaps and
guaranteeing complete coverage [cited — see §6].

### 1.2 The lift, and why it is the whole trick

Parametrise the shrink by time `t`. At time `t` every edge has moved inward by
distance `t`. Define the roof surface by

```
    z(x, y) = t(x, y) · tan θ
```

where `t(x, y)` is the time at which the wavefront passed through `(x, y)` and
`θ` is the pitch. Three properties fall out, and they are the reason this is
the right primitive:

1. **Every face is planar.** The face generated by edge `e` is the set of points
   whose nearest wavefront edge is `e`; on it, `t` equals the perpendicular
   distance to the supporting line of `e`, which is a linear function of
   `(x, y)`. A linear function times a constant is a plane. No optimisation, no
   fitting.
2. **Every face has the same slope, `θ`.** So the roof surface area is
   `A_footprint / cos θ` exactly. **[derived]** For the worked L in §1.7:
   footprint 1024 ft², at 6:12, roof surface 1144.867 ft², parity residual 0.
   This is the cheapest, strongest verification test available and §4.6 makes
   it the primary one.
3. **Water drains.** Every point's steepest-descent path leads to the eave that
   generated its face. No ponds, no reverse falls, no landlocked valleys —
   provided the lift is monotone, which it is for a single-pitch skeleton.

The one-line reformulation that unlocks everything in §4: **parametrise by
height, not time.** If instead you advance edge `e` inward by `z · cot θ_e` as
the height `z` rises, then `z` *is* the parameter, and per-edge pitch is per-edge
speed. That identity —

```
    edge speed  w_e  =  cot θ_e            (offset per unit HEIGHT)
```

— is the hinge of this entire report. See §1.6.

### 1.3 Events: what actually happens as the polygon shrinks

The shrink is not smooth; it is a sequence of discrete topology changes. There
are exactly two kinds.

**Edge event.** A wavefront edge shrinks to zero length: its two bounding
vertices collide. The edge disappears from the wavefront and the two skeleton
arcs meet at a node. In roof terms this is where a **hip meets a ridge**, or
where a pyramidal roof reaches its apex.

An edge's collapse time is available in closed form. If edge `e` has length
`L₀` and its two bounding vertices approach each other at a combined rate `r`,
it collapses at `t = L₀ / r`. For a rectilinear polygon with two convex ends,
`r = 2` and the collapse time is simply half the edge length. **[derived]**

**Split event.** A **reflex** vertex — one whose interior angle exceeds 180°,
i.e. an inside corner of the plan — runs into a wavefront edge on the far side
and splits the shrinking polygon into two independent polygons. In roof terms
this is where a **valley bottoms out** and the roof resolves into two separate
ridge systems. This is the event that makes L-, T-, U- and cross-shaped plans
interesting, and it is the event that implementations get wrong.

CGAL is precise about why reflex vertices are the whole story:

> "Only reflex vertices (i.e., vertices whose internal angle > π) are
> responsible for deviations of the bisectors from its center location."

[cited — CGAL 6.2]

A convex polygon has no reflex vertices, therefore no split events, therefore
its skeleton is a simple tree of hips converging on a ridge or a point. Every
interesting roof in a city comes from a reflex vertex.

**Cost.** The classical algorithm keeps `O(n)` edge-collapse times plus `O(n²)`
potential split times in a priority queue, running in `O(n² log n)` time and
`O(n²)` memory [cited — see §6]. For building footprints (`n` typically under
50) this is irrelevant; for a whole city block re-solved per frame it is not.

### 1.4 Degeneracies — and the one that matters most for cities

This is where a naive implementation produces a different roof on different
machines, and it is worth being blunt about it.

**Simultaneous events.** Two or more events at the same `t`. The event queue
has a tie, and the order in which ties are popped changes the output topology.

**A rectangular plan is the maximally degenerate case.** A square footprint has
all four edge events at the same instant, at the same point — the apex of a
pyramidal roof. Four arcs meet at one node instead of the generic three. A
rectangle has its two end events simultaneous.

**Finding (derived, and I did not expect it to be this clean):** for *any*
rectilinear L-shaped footprint, the split event of the reflex vertex and one
edge-collapse event are **always simultaneous**. Not usually — always.

Let the L be `A(0,0) B(W,0) C(W,h) D(w,h) E(w,H) F(0,H)` with the reflex vertex
at `D`. Then:

- top edge `EF` has length `w`, so it collapses at `t = w/2`;
- vertex `D` moves at velocity `(−1,−1)`, and the left edge `FA` offsets to
  `x = t`, so `D` reaches it when `w − t = t`, i.e. `t = w/2`.

Identical, by construction, because the leg width and the top edge length are
the same number in a rectilinear plan. Symmetrically, if `w > h` the split lands
on the bottom edge at `t = h/2` and the right edge `BC` collapses at `t = h/2`.
Either way: **split time = min(w, h)/2, and it ties with an edge collapse.**
**[derived — verified in `roof_math_check.py`]**

The two events are at the *same time* but *different places*, so they are
independent and a correct implementation handles them in either order. But a
queue with an unstable sort, or a tolerance-based comparison, has a coin flip
in it. Since city footprints are overwhelmingly rectilinear, **this tie is the
normal case, not the corner case.** §4.6 makes deterministic tie-breaking a
required test.

**Other degeneracies to guard:**

- **Parallel edges / zero-length edges** in the input. A footprint carrying a
  vestigial 1 mm edge from a boolean will produce a spurious skeleton node and a
  sliver face. Clean the polygon first; this is not optional.
- **Near-collinear vertices.** Two edges at 179.9° produce a hip arc that is
  almost parallel to the eave and a face that is almost degenerate. Houdini's
  `polyexpand2d` exposes a **Parallelism Tolerance** and a **Coincidence
  Tolerance** for exactly this [cited — SideFX docs].
- **Holes** (courtyard buildings). The skeleton still exists but its faces stop
  being well behaved: "faces of a straight skeleton of a polygon with holes are
  no longer necessarily weakly simple polygons: a face can for example
  completely encompass a set of faces incident to a hole" [cited — CGAL 6.2].
  A donut footprint is a real building type (NYC courtyard blocks) and it needs
  a test case.

### 1.5 It is not the medial axis, and the difference is visible

The medial axis is the locus of points equidistant from **the polygon boundary**.
The straight skeleton's arcs are equidistant from **the supporting lines of the
edges**. CGAL:

> the bisectors "are not equidistant to its defining edges but to the supporting
> lines of such edges. As a result, the bisectors of a straight skeleton might
> not be located in the center of the polygon."

and

> for convex polygons "the straight skeleton, the medial axis and the Voronoi
> diagram are exactly equivalent."

[cited — CGAL 6.2]

The practical consequence: at a **reflex** vertex the medial axis grows a
**parabolic arc** (points equidistant from a vertex and an edge lie on a
parabola), whereas the straight skeleton grows a **straight** bisector. So a
medial-axis "roof" over an L-plan has a curved valley. No framer has ever cut
that. Everything is straight-line-and-plane, which is what timber is.

**And it is not the lower envelope of the tilted wall planes either.** The
tempting shortcut — "tilt every wall inward at the pitch and take
`z(x,y) = min_e (signed distance to edge e's line) · tan θ_e`" — is correct for
a **convex** footprint and silently wrong for every other one. On the §1.7 L
(inward normals, 6:12) **[derived]**:

| Point | Naive min-plane `z` | True skeleton `z` |
|---|---|---|
| (4, 40) | **−10.00** (from edge `CD`) | 2.00 |
| (8, 30) | **−5.00** (from edge `CD`) | 4.00 |
| (20, 4) | **−2.00** (from edge `DE`) | 2.00 |

The reason is structural: a point in the wing is on the *outside* of edge `CD`'s
supporting line, so that plane dives below grade there. The straight skeleton
avoids this because a face is bounded by the **wavefront** the edge actually
reaches, not by its infinite supporting line. Any implementation that reaches
for a `min()` over planes will produce roofs that dip below the eaves on exactly
the L, T and U plans that make a city.

⚠ **Naming trap that will bite in Houdini.** The `Labs Straight Skeleton 3D`
SOP is *not* this construction. Its own documentation says "A straight skeleton
(also called a medial axis)…" and describes a voxel-based mesh-shrinking solver
with a Voxel Size parameter [cited — SideFX docs]. It produces a medial-axis
curve for UVs, destruction and joint generation. **The roof tool is
`polyexpand2d`**, which really does compute the straight skeleton (§4.2).

### 1.6 The weighted variant — and why it is the whole vocabulary

Uniform pitch is the special case. The general case gives each edge its own
speed. From §1.2:

```
    w_e = cot θ_e          offset of edge e per unit of HEIGHT
```

so if the offset parameter is driven to `D`, every point on the wavefront is at
height `D`, and edge `e` has moved inward `D · w_e`. That is a
**multiplicatively-weighted straight skeleton**, exactly as defined in the
literature: "Contour edges are assigned a positive weight, which can be
understood as assigning a speed to the wavefront spawned from the contour edge"
… "a larger weight implies a faster moving front" [cited — CGAL 6.2].

Now read off what particular weights mean:

| `w_e` | `θ_e` | What it is |
|---|---|---|
| `cot θ` (same for all edges) | θ | **Hip roof** at pitch θ |
| `0` | 90° | Edge does not move → **vertical gable end / parapet / firewall** |
| `0` on two opposite edges, `cot θ` on the others | — | **Gable roof** |
| `0` on three of four edges | — | **Shed / skillion** |
| Different `w` on two opposite edges | — | **Saltbox** (needs one more input, §1.9) |
| Negative lift, any weights | — | **Butterfly** |
| Very large `w` | ≈0° | Nearly flat plane, drains to one edge |

**A gable is a hip with two weights set to zero.** A shed is a hip with three
weights set to zero. A cross-gable is a gable on a cruciform footprint —
*it is not a separate roof type at all.* This collapse is the single most
useful result in this report and §4.1 builds the tool on it.

**What breaks under weighting.** Be honest about this before relying on it:

- The faces remain planar (each is still a linear function of `(x,y)` times a
  constant), so the area-parity test survives, but it becomes
  `Σ_i A_i / cos θ_i = A_footprint` — one term per face, not one global factor.
- The skeleton is no longer a distance function of the boundary, so "offset
  distance" and "height" decouple. Any code that reconstructs height from a
  single `edgedist` value must use *that face's own* edge weight.
- **The topology is not stable under weight change.** Changing one edge's pitch
  can reorder events and change which arcs exist. A pitch slider can *pop* the
  roof to a different topology. This must be surfaced in the UI, not hidden.
- A weight of exactly `0` is a limit case: the edge never moves, so it never
  collapses and never splits, and some implementations divide by speed. Clamp
  to a small epsilon or special-case it.

**Additive weights** are the second lever: instead of scaling the speed, offset
the edge's *starting position*. That models a per-edge setback or eave height —
the mechanism behind a mansard's kick and, at building scale, a zoning setback.

### 1.7 Worked example — the L-plan hip-and-valley

Footprint, in feet, counter-clockwise:

```
    A(0,0)   B(32,0)   C(32,20)   D(16,20)   E(16,44)   F(0,44)
```

A 32 × 20 ft main block with a 16 × 24 ft wing running back. `D` is the reflex
vertex. Uniform pitch 6:12 (`m = 0.5`, θ = 26.565°).

**Moving vertices** (all interior angles are 90° or 270°, so every convex vertex
moves at speed √2 along a 45° bisector):

```
    A(t) = (  t,   t)          D(t) = (16−t, 20−t)   ← reflex
    B(t) = (32−t,  t)          E(t) = (16−t, 44−t)
    C(t) = (32−t, 20−t)        F(t) = (  t,  44−t)
```

**Event table** **[derived — all times verified numerically]**

| t | Event | Where | What it is on the roof |
|---|---|---|---|
| 8 | **Split** of reflex `D` against edge `FA` | (8, 12) | Valley bottoms out; roof separates into wing + main block |
| 8 | **Edge collapse** of `EF` | (8, 36) | Wing's hip apex — *ties with the split, per §1.4* |
| 10 | **Edge collapse** of `BC` | (22, 10) | Main block's east hip apex |
| 10 | **Edge collapse** of the residual `FA` | (10, 10) | Main block's west ridge end |

Edges `CD` (length 16) and `DE` (length 24) **never collapse** — both of their
endpoints move with identical velocity, so their lengths are constant. Their
faces survive to the end. **[derived]**

**Skeleton arcs and their heights at 6:12:**

| Arc | Plan | Type | Height start → end |
|---|---|---|---|
| A → (10,10) | 10√2 = 14.142 | hip | 0 → 5.0 |
| B → (22,10) | 14.142 | hip | 0 → 5.0 |
| C → (22,10) | 14.142 | hip | 0 → 5.0 |
| **D → (8,12)** | 8√2 = 11.314 | **valley** | 0 → 4.0 |
| E → (8,36) | 11.314 | hip | 0 → 4.0 |
| F → (8,36) | 11.314 | hip | 0 → 4.0 |
| (8,12) → (8,36) | 24.0 | **wing ridge** | 4.0 (level) |
| (8,12) → (10,10) | 2√2 = 2.828 | hip | 4.0 → 5.0 |
| (10,10) → (22,10) | 12.0 | **main ridge** | 5.0 (level) |

**The two ridges are at different heights — 4.0 ft and 5.0 ft — and that is
correct, not a bug.** The wing is 16 ft wide (half-span 8), the main block 20 ft
deep (half-span 10); at one pitch, the deeper block rides higher. A framer gets
the same answer, which is why in practice the wing's ridge is either accepted
lower or the wing's pitch is raised.

**Raising it, with the weighted skeleton:** to bring the wing's ridge to 5.0 ft
over a half-span of 8, the wing needs `m = 5/8 = 0.625` = **7.5:12**
**[derived]**. Set `w = cot θ` on the wing's two long edges and `cot 26.565°` on
the main block's, and both ridges land at 5.0. This is the canonical, real
reason to reach for a weighted skeleton, and it is a one-line rule the tool can
offer as a button: *"match ridge heights."*

**The six faces, and the parity check** **[derived — all shoelace areas
computed, residual exactly 0]**. One face per input edge, always:

| Face (its source edge) | Plan polygon | Plan area | Surface at 6:12 |
|---|---|---|---|
| `AB` bottom eave | (0,0) (32,0) (22,10) (10,10) | 220.000 | 245.9675 |
| `BC` right eave | (32,0) (32,20) (22,10) | 100.000 | 111.8034 |
| `CD` main block back | (32,20) (16,20) (8,12) (10,10) (22,10) | 156.000 | 174.4133 |
| `DE` wing east | (16,20) (16,44) (8,36) (8,12) | 192.000 | 214.6625 |
| `EF` wing end | (16,44) (0,44) (8,36) | 64.000 | 71.5542 |
| `FA` left eave | (0,44) (0,0) (10,10) (8,12) (8,36) | 292.000 | 326.4659 |
| **Sum** | | **1024.000** | **1144.8668** |

Footprint by shoelace = 1024.0 ft². **Residual exactly 0.** Predicted surface
`1024 / cos(26.565°)` = 1144.8668 ft². **Six faces for six input edges** — the
Euler check of §4.6 V2. Note face `FA` is a pentagon and face `CD` is a
pentagon: skeleton faces are *not* trapezoids in general, and any implementation
that assumes quads will be wrong on exactly the footprints that matter.

### 1.8 Framing arithmetic

Everything here is derived and machine-checked; none of it is recalled.

**Pitch conversions** **[derived]**

| Pitch | Grade | Angle | Common rafter ×run | Hip ×common run | Hip slope |
|---|---|---|---|---|---|
| 1/4 : 12 | 2.08 % | 1.193° | 1.00022 | 1.41437 | 0.844° |
| 1/2 : 12 | 4.17 % | 2.386° | 1.00087 | 1.41483 | 1.688° |
| 2 : 12 | 16.67 % | 9.462° | 1.01379 | 1.42400 | 6.721° |
| 2½ : 12 | 20.83 % | 11.768° | 1.02147 | 1.42948 | 8.380° |
| 3 : 12 | 25.00 % | 14.036° | 1.03078 | 1.43614 | 10.025° |
| 4 : 12 | 33.33 % | 18.435° | 1.05409 | 1.45297 | 13.263° |
| 5 : 12 | 41.67 % | 22.620° | 1.08333 | 1.47432 | 16.416° |
| 6 : 12 | 50.00 % | 26.565° | 1.11803 | 1.50000 | 19.471° |
| 7 : 12 | 58.33 % | 30.256° | 1.15770 | 1.52980 | 22.415° |
| 8 : 12 | 66.67 % | 33.690° | 1.20185 | 1.56347 | 25.239° |
| 9 : 12 | 75.00 % | 36.870° | 1.25000 | 1.60078 | 27.938° |
| 10 : 12 | 83.33 % | 39.806° | 1.30171 | 1.64148 | 30.509° |
| 12 : 12 | 100.00 % | 45.000° | 1.41421 | 1.73205 | 35.264° |
| 16 : 12 | 133.33 % | 53.130° | 1.66667 | 1.94365 | 43.314° |
| 20 : 12 | 166.67 % | 59.036° | 1.94365 | 2.18581 | 49.684° |
| 24 : 12 | 200.00 % | 63.435° | 2.23607 | 2.44949 | 54.736° |

With `m = rise/run`:

```
    θ            = atan(m)
    common       = run · √(1 + m²)
    hip (90°)    = run · √(2 + m²)             run = the COMMON run
    hip slope    = atan(m/√2)
```

The framer's "17" is just `12√2 = 16.9706` **[derived]** — the hip advances
16.97 in of plan for every 12 in the common advances, so you lay out a hip on a
framing square using 17 in on the body instead of 12.

**Worked rafter set** — the 32 × 20 ft main block above, 6:12, 2×8 rafters on a
2×4 plate with a 1½ in ridge board **[derived]**:

| Quantity | Value |
|---|---|
| Nominal run (half of 20 ft) | 10.0000 ft |
| Run corrected for half the ridge thickness | 9.9375 ft |
| Common rafter line length, nominal | 11.1803 ft |
| Common rafter line length, corrected | 11.1105 ft |
| Ridge rise above plate | 5.0000 ft |
| Hip plan run | 14.1421 ft |
| Hip line length | 15.0000 ft (exactly — `10 · √2.25`) |
| Hip slope | 19.4712° |
| Jack common difference @ 16 in o.c. | 1.49071 ft = **17.8885 in** |
| Jack common difference @ 24 in o.c. | 2.23607 ft = **26.8328 in** |

**Ridge-thickness correction matters for modelling.** The run is measured to the
*centreline* of the ridge, but the rafter stops at its *face*, so the true run
is `half-span − ridge_thickness/2`. Half an inch of ridge is 0.07 ft of rafter —
invisible in a render, fatal in a cut list. Model the geometric roof to the
centreline and the timber to the face.

**Jack rafters.** Jacks run from the eave to a hip (or from a valley to a
ridge). For a plan corner of interior angle `2α` and equal pitches, a jack at
distance `x` along the eave has run `x·tan α`, so

```
    jack common difference  =  spacing · tan α · √(1 + m²)
```

At a square corner `α = 45°`, `tan α = 1`, and the difference reduces to
`spacing · √(1+m²)` — the familiar figure printed on a framing square.
**[derived]**

**Birdsmouth.** The notch that seats the rafter on the plate. With seat width
`b` (= plate width) and pitch `m`, the plumb heel cut is `v = b·m`, and the
remaining depth above the seat — the **HAP**, height above plate — is

```
    HAP  =  d / cos θ  −  b · m
```

For a 2×8 (7.25 in actual) on a 2×4 plate (3.5 in) at 6:12: `v = 1.75 in`,
`HAP = 6.3557 in`, i.e. 78.4 % of the plumb-measured rafter depth remains.
**[derived]** The IRC routes birdsmouth notching through R802.7.1 → R502.8.1
[cited]; the specific residual-depth limits should be read from R502.8.1 before
any span claim is made — I did not fetch that section.

**Hip backing bevel — and a folk rule that is wrong.**

The top edge of a hip rafter sits under two roof planes, so it must be beveled
to a shallow ridge. Deriving it properly: let `2α` be the interior plan angle at
the corner and `γ = 90° − α`. Then with `c = m·cos γ` and `s = m·sin γ`,

```
    tan β  =  s / √(1 + c²)  =  m·sin γ / √(1 + m² cos² γ)
```

**[derived — closed form and direct vector computation agree to 1e-9]**

At a **square** corner (`α = γ = 45°`) this reduces to `tan β = sin(θ_hip)`,
which is the rule every framing text gives. It is correct — *there*. It is
wrong everywhere else, and badly:

| Interior plan angle | True β at 6:12 | `sin(θ_hip)` rule gives |
|---|---|---|
| 60° | **22.787°** | 14.036° |
| 90° | **18.435°** | 19.471° |
| 120° | **12.921°** | 23.413° |
| 135° | **9.854°** | 24.794° |

**[derived]** At 120° the folk rule is off by 10.5° and moving in the wrong
direction. Since a straight-skeleton roof over an arbitrary footprint produces
hips at every plan angle, a tool that uses the square-corner rule will bevel
non-square hips wrongly. Use the general formula.

**Ridge board versus ridge beam.** A ridge *board* is a nailing spacer; it
carries nothing. The rafter pair is a triangle, and its outward thrust is taken
by ceiling joists or rafter ties in tension. Break the tension member and the
walls spread. The IRC codifies this precisely:

> "Where ceiling joist or rafter ties do not provide continuous ties across the
> structure as required by Section R802.5.2, the ridge shall be supported by a
> wall or ridge beam designed in accordance with accepted engineering practice."
> — IRC 2021 **R802.3** [cited]

and the pitch threshold:

> "Where the roof pitch is less than 3:12 (25-percent slope), structural members
> that support rafters, such as ridges, hips and valleys, shall be designed as
> beams." — IRC 2021 **R802.4.4** [cited]

**Below 3:12 the ridge, hips and valleys become beams.** That is a genuine
visual difference — a deep dropped ridge beam and posts, not a 1× board — and
it is a rule a generator can apply automatically from the pitch it already
knows.

**Ties.** [all cited, IRC 2021]

- **Rafter ties**: not less than 2×4, at max 24 in o.c., in the **bottom third**
  of the rafter height (R802.5.2 / R802.5.2.2).
- **Collar ties**: not less than 1×4 nominal, spaced not more than 4 ft o.c., in
  the **upper third** of the attic space; ridge straps of 1¼ in × 20 gauge may
  substitute (R802.4.6).
- Moving the tie **up** costs span. Table R802.4.1(9) gives the penalty
  explicitly, with `H_C` the tie height above the plate and `H_R` the ridge
  height above the plate:

  | `H_C/H_R` | Span factor |
  |---|---|
  | 1/3 | 0.67 |
  | 1/4 | 0.76 |
  | 1/5 | 0.83 |
  | 1/6 | 0.90 |
  | ≤ 1/7.5 | 1.00 |

  This is the arithmetic of "cathedral ceiling costs you a third of your span."

- **Purlins and braces**: purlins sized not less than the rafters they support,
  braced to bearing walls at **not less than 45°** from horizontal, braces at
  max 4 ft o.c., unbraced brace length ≤ 8 ft (R802.4.5) [cited]. This is the
  under-roof furniture of a traditional cut roof and it is fully determined by
  the geometry — a generator can place it.

**Trusses.** Span figures found only on vendor/trade pages, so: king post ≤ ~25
ft; queen post ~25–40 ft; Fink ~20–60 ft; Howe ~30–70 ft; scissor ~20–50 ft;
attic/room-in-roof commonly to ~30 ft **[trade — do not put these in a spec]**.
The one structurally important point that is not a number: **a truss roof and a
cut roof produce the same outside and completely different insides.** A hip set
in trusses steps down off a girder truss; it does not have a continuous hip
rafter at all. If the underside is ever visible, the straight skeleton is a
surface model, not a framing plan (§5).

### 1.9 Where a footprint is not enough — stated plainly

The skeleton gives ridges, hips and valleys from the outline. It does **not**
give:

| Roof feature | Minimum extra input, stated exactly |
|---|---|
| **Gable vs hip on a given end** | One boolean per edge (`w_e = 0` or `cot θ`). `n` bits for `n` edges. |
| **Saltbox** | The ridge's plan offset from centre — one scalar — *or* equivalently the rear eave height. The two are related by the pitches; supply one. |
| **Gambrel** | A break height `h` and a second pitch. **Unless** you accept the semicircle construction (§2.3), which supplies both from the span alone. |
| **Mansard** | Break height `h` + upper pitch, and normally a per-edge decision about whether the steep face is a roof or a wall. |
| **Jerkinhead** | The clip height `h` (one scalar), as a fraction of the ridge height. |
| **Dutch gable** | The gablet height `h` (one scalar). |
| **Dormers** | Position along the eave, width, height, and type. Four numbers per dormer, plus a placement rule. Not derivable — dormers follow the *rooms*, which the footprint does not know. |
| **Cross-gables at unequal pitch** | One pitch per wing (the weighted skeleton takes them), **plus** a decision about whether ridges match height, eaves match height, or neither. That decision is architectural, not geometric. |
| **Monitor / clerestory** | Interior section: the raised bay's width, its wall height, and its position. Driven by the room below. |
| **Sawtooth / folded plate** | A direction vector and a period. The footprint does not contain either. In the northern hemisphere the glazing faces **north** [trade], so the direction is at least *constrainable* by site orientation. |
| **Barrel vault / dome** | A rise. A footprint gives a span; the rise is a choice. Semicircular (rise = half-span) is the one canonical answer. |
| **Anything driven by interior volume** | Churches, atria, halls, double-height spaces. The plan perimeter is silent about them. |
| **Roof over an addition** | Buildings accrete. A wing added in 1910 to an 1880 house has a different pitch, different eave height, different covering. The skeleton makes a roof that looks designed all at once. Needs an explicit massing decomposition into dated parts. |

### 1.10 Reproducing the numbers

Every `[derived]` figure above was produced and checked by
`roof_math_check.py`. It is pure Python, no Houdini, no license — deliberately,
so the arithmetic can be checked before any of it goes near an HDA, exactly as
`moulding_grammar.py` was built. It sits beside this report at
`U:/AB_Standardization/research/roof_math_check.py`; run it with
`python roof_math_check.py`. It checks: the pitch table; the L-plan event times and the simultaneity claim;
the residual-rectangle stage; area parity; the full rafter set; the backing
bevel by two independent methods; the gambrel semicircle; and the headroom
comparison in §2.3.

---

## 2. Typology and style matrix

### 2.1 The matrix

`FP?` = derivable from footprint alone. `FP+n` = footprint plus `n` scalars.
Pitch ranges marked **[cited]** are code minimums for the covering; ranges
marked **[trade]** or **[UNVERIFIED]** are what is actually built and are art
direction, not fact.

| Form | Generating geometry | FP? | Minimum extra input | Built pitch | Framing | Period / region |
|---|---|---|---|---|---|---|
| **Gable** | Skeleton, `w=0` on the two ends | **FP+n bits** | which edges are gable | 4:12–12:12 typical **[UNVERIFIED]**; ≥2:12 for asphalt **[cited R905.2.2]** | Rafters + ridge board + rafter ties; or Fink trusses | Universal; the American default |
| **Hip** | Plain skeleton, uniform `w` | **FP only** | — | 4:12–8:12 **[UNVERIFIED]** | Hips + jacks + common rafters; hip truss set | Georgian, Colonial Revival, Prairie; hurricane and high-wind regions |
| **Pyramidal / pavilion** | Hip on a square or regular polygon | **FP only** | — | 6:12–12:12 **[UNVERIFIED]** | Four hips to a point, no ridge | Foursquare, Italianate towers, garden pavilions |
| **Hip-and-valley** | *Nothing new* — hip on a non-convex footprint | **FP only** | — | as hip | as hip + valley rafters | Any plan with a wing |
| **Cross-gable** | *Nothing new* — gable on a cruciform/L footprint | **FP+n bits** | which edges are gable | as gable | as gable + valleys | Gothic Revival, Queen Anne, Tudor |
| **Dutch gable (US usage)** | Hip to height `h`, then gable above | **FP+1** | gablet height `h` | as hip | Hip below, short gable framing above | ⚠ see terminology note §2.2 |
| **Jerkinhead / clipped gable** | Gable to height `h`, then hip above | **FP+1** | clip height `h` | 8:12–12:12 **[UNVERIFIED]** | Gable with the peak hipped back | Tudor Revival, English vernacular, Craftsman |
| **Gambrel** | Two-band gable: steep then shallow | **FP only** *if* the semicircle construction is used (§2.3); otherwise **FP+2** | break height + upper pitch | lower ≈29:12 / upper ≈5:12 by construction **[derived]** | Purlin plate at the break; or a gambrel truss | Dutch Colonial, American barns |
| **Mansard** | Two-band **hip**: steep then shallow | **FP+2** | break height + upper pitch | lower 60–80°, upper 2:12–6:12 **[UNVERIFIED]** | Steep face is effectively a wall carried on a curb; flat deck above | Second Empire (US ~1860–1885); Parisian |
| **Shed / skillion** | Skeleton, `w=0` on all but one edge | **FP+1 bit** | which edge is the high side | 1:12–6:12 **[UNVERIFIED]**; ≥¼:12 for membrane **[cited R905.12.1]** | Single rafter run, no ridge, no thrust | Additions, lean-tos, modernist, contemporary |
| **Saltbox** | Gable with unequal pitches / unequal eave heights | **FP+1** | ridge plan offset (or rear eave height) | front 10:12, rear 6:12 **[UNVERIFIED]** | Long rear rafter over a lean-to | New England colonial |
| **Butterfly** | Skeleton with **negative** lift | **FP+1 bit** | sign of the lift | 1:12–4:12 **[UNVERIFIED]** | Central valley beam; internal drainage — the failure mode | Mid-century modern, Le Corbusier, Palm Springs |
| **Sawtooth** | Periodic section swept along an axis, clipped | **not FP** | axis direction + period | glazed face vertical–70°; sloped face ≈8:12 ≈30° **[trade]** | North-light trusses on columns | Industrial, ~1827 onward **[trade]**; mills, weaving sheds |
| **Monitor** | Three-band section: slope, wall, slope | **not FP** | raised-bay width + wall height + position | as gable | Raised centre bay carried on posts | Barns, mills, railway sheds, early factories |
| **Flat with parapet** | Skeleton, all `w = 0`; flat top | **FP+1** | parapet height | ≥¼:12 to drain **[cited IBC 1507]** | Joists/deck + tapered insulation; internal drains | Urban commercial and rowhouse everywhere; NYC/SF/LA all |
| **Barrel vault** | Gable band replaced by a circular arc | **FP+1** | rise (½-span = semicircular) | n/a | Arched ribs, laminated or steel; or masonry vault | Romanesque, Quonset, market halls, rail sheds |
| **Dome** | Hip band replaced by a circular arc, on a near-circular footprint | **FP+1** | rise | n/a | Ribs + rings; or shell | Civic, religious, capitols |
| **Folded plate** | Periodic section swept, like sawtooth but symmetric | **not FP** | axis + period + fold depth | n/a | The fold *is* the structure; thin concrete or plate steel | Post-war modern, ~1950s–60s |

### 2.2 Terminology traps worth encoding once

**"Dutch gable" means two different things.** In American and Australasian
usage it is a **gablet roof** — a small gable at the top of a hip. In European
usage it is a **shaped gable wall** with curved sides and a pediment, which is a
*wall* treatment, not a roof form at all [cited — see §6]. AssetBash ships to a
global audience. **Name the American one `HipWithGablet` and the European one
`ShapedGable`, and never use the string "Dutch gable" in a menu.** (Note also
that "Dutch roof" is used for *gambrel* in some survey forms [trade], making the
word "Dutch" a three-way collision. Avoid it entirely.)

**"Mansard" is a typology, not a style.** This matters for AssetBash's three
axes and it is the single most likely place to get them wrong. A mansard changes
the *dimensions* of the roof — the break height, the two pitches, the resulting
massing. Under this project's rule, anything that changes dimensions is
TYPOLOGY. The **style** is Second Empire. Same for gambrel (typology) versus
Dutch Colonial (style).

The test the project already uses applies cleanly: *changing style must not
change the dimensions.* Applying an Art Deco articulation to a 6:12 gable must
leave it a 6:12 gable — different parapet coping, different fascia, different
covering pattern, same skeleton, same bounding box.

### 2.3 The gambrel is footprint-derivable, and it earns its shape

This surprised me and it is worth its own note.

The classical construction: draw a semicircle on the span; divide the semicircle
into four equal arcs; the roof profile is the two chords on each side. Working it
out for radius `R` (= half-span) **[derived]**:

- Lower chord: from (R, 0) to (0.70711R, 0.70711R) — slope **2.4142 = 67.500° =
  28.97:12**
- Upper chord: from (0.70711R, 0.70711R) to (0, R) — slope **0.41421 = 22.500° =
  4.97:12**
- Break point at **70.711 % of the half-span** horizontally, at **70.711 % of the
  ridge height**
- Ridge height = `R` = the half-span

Every number comes from the span. **No extra input.** So a gambrel *can* sit in
the "footprint only" column, provided the tool ships this construction as its
default and exposes the break as an override.

The construction is documented as a traditional method and is known as the
**demi-octagon** [trade]; a second classical variant divides the semicircle into
**five** equal arcs instead of four and joins the first division point to the
top. Both are footprint-only, and having two gives free typological variety at
zero parameter cost **[derived]**:

| Construction | Lower slope | Upper slope | Break at (of half-span, of ridge ht) |
|---|---|---|---|
| 4 arcs (demi-octagon) | 67.500° = 28.97:12 | 22.500° = 4.97:12 | 70.711 %, 70.711 % |
| 5 arcs | 72.000° = 36.93:12 | 27.000° = 6.11:12 | 80.902 %, 58.779 % |

The 5-arc version is steeper below and lower-breaking — it reads as the barn
gambrel; the 4-arc reads as the Dutch Colonial house gambrel. **[the visual
attribution is art direction, UNVERIFIED; the geometry is derived.]**

And the reason the form exists is measurable. Span 24 ft, and ask how much width
has at least 7 ft of clear height (the IRC habitable-space ceiling height
[cited]) **[derived]**:

| Profile | Ridge height | Width with ≥ 7 ft clear |
|---|---|---|
| **Gambrel (4-chord)** | 12.0 ft | **18.20 ft — 75.8 % of the span** |
| Gable 12:12 | 12.0 ft | 10.00 ft — 41.7 % |
| Gable 18:12 | 18.0 ft | 14.67 ft — 61.1 % |
| Gable 24:12 | 24.0 ft | 17.00 ft — 70.8 % |

At the *same ridge height*, the gambrel gives **1.82×** the usable floor width of
a 12:12 gable, and it beats a 24:12 gable while standing half as tall. That is
the entire argument for the form — barns and Dutch Colonials are not decorated
gables, they are volume optimisations — and it is derivable, which means the
tool can *explain itself* to the user rather than presenting a menu item.

### 2.4 Covering minimum slopes — the hard floor on pitch

These are code, not taste, and they are the right way to constrain the pitch
slider per material. All **[cited — IRC 2021 Chapter 9]**.

| Covering | Section | Minimum slope |
|---|---|---|
| Asphalt shingles | R905.2.2 | 2:12 (17 %); **double underlayment required from 2:12 up to 4:12** |
| Clay and concrete tile | R905.3.2 | 2½:12 (21 %); double underlayment 2½:12–4:12 |
| Metal roof **shingles** | R905.4.2 | 3:12 |
| Mineral-surfaced roll roofing | R905.5.2 | 1:12 (8 %) |
| **Slate** | R905.6.2 | **4:12 (33 %)** |
| Wood shingles | R905.7.2 | 3:12 |
| Wood shakes | R905.8.2 | 3:12 |
| Built-up | R905.9.1 | ¼:12 (2 %); coal-tar ⅛:12 (1 %) |
| Metal roof **panels**, lapped, no sealant | R905.10.2 | 3:12 |
| Metal roof panels, lapped, with sealant | R905.10.2 | ½:12 (4 %) |
| Metal roof panels, **standing seam** | R905.10.2 | **¼:12 (2 %)** |
| Modified bitumen | R905.11.1 | ¼:12 |
| Thermoset single-ply | R905.12.1 | ¼:12 |
| Thermoplastic single-ply | R905.13.1 | ¼:12 |
| Sprayed polyurethane foam | R905.14.1 | ¼:12 |
| Liquid-applied | R905.15.1 | ¼:12 |

The exact quoted wording for the governing one:

> "Asphalt shingles shall be used only on roof slopes of 2 units vertical in 12
> units horizontal (17-percent slope) or greater." — IRC 2021 R905.2.2 [cited]

**This table is a catalog CSV, not prose.** It is the roof equivalent of the
sign-size table: a fact with a section number attached, per row. §4.4.

### 2.5 Snow and wind: where geometry meets load

**ASCE 7 unbalanced snow window.** For hip and gable roofs, unbalanced snow
loads need not be considered where the slope exceeds **7:12 (30.2°)** or is less
than **½:12 (2.38°)** — ASCE 7 §7.6.1. The degree conversions check out exactly:
`atan(0.5/12) = 2.386°`, `atan(7/12) = 30.256°` **[derived]**. The provision is
**[cited via secondary sources only — ASCE 7 is paywalled and I could not fetch
the primary text; treat the exact wording as UNVERIFIED, the numbers as
corroborated]**. Unbalanced load is also only checked for roofs wider than about
20 ft with sufficient ground snow **[UNVERIFIED]**.

Why it matters here: **the snow-country pitch window and the unbalanced-load
window are the same window.** Roofs in snow regions cluster steeper than 7:12
precisely to shed rather than accumulate, which is a *derived* reason for a
regional pitch distribution rather than an art-directed one.

**Slope factor `C_s`.** ASCE 7 Figure 7.4-1 reduces roof snow load with slope,
and the reduction begins at different slopes depending on whether the roof is
warm or cold and slippery or not — roughly, warm+slippery starts reducing around
5°, warm+other around 30°, cold+slippery around 10°, cold+other around 45°, all
reaching zero at 70° **[trade — read from a calculator vendor's description of
the figure, not from the figure]**.

**Low-slope drainage.** The 2021 IBC requires a minimum design slope of ¼ unit
vertical in 12 (2 %) for low-slope roofs, and defines *positive drainage* as a
design that "accounts for deflections from all design loads and has sufficient
additional slope to ensure that drainage of the roof occurs within 48 hours of
precipitation" [cited — IBC 2021, quoted via IIBEC/trade summary; **section
attribution to 1507 is [UNVERIFIED]**].

**Consequence for modelling: a "flat" roof is never flat.** It is a ¼:12 plane,
or more usually a field of tapered insulation crickets falling to interior
drains. A truly flat top surface is the single most common tell of a synthetic
building. §4.1 handles this with a `flat` band that is actually a ¼:12 band.

**Habitable attic.** IRC R202 defines a habitable attic by occupiable floor area
≥ 70 ft² at a ceiling height per R305, which is **not less than 7 ft**; for
sloped ceilings, more than 50 % of the required area must have ≥ 7 ft
[cited/paraphrased from code-summary sources; the 70 ft²/7 ft/50 % figures are
consistent across sources but I did not fetch the code text itself —
**[UNVERIFIED wording, corroborated numbers]**]. IRC R807 requires attic access
where the attic exceeds 30 ft² and has a vertical height of 30 in or greater
[same caveat].

These two thresholds — **7 ft** and **30 in** — are the geometric constants that
decide whether a roof gets dormers and windows or stays blind. §2.3 uses the 7 ft
figure to explain the gambrel.

---

## 3. Codes and zoning: NYC, San Francisco, Los Angeles

All sections below accessed **2026-08-15**. Sourcing caveats are stated inline
and repeated in §3.5 — several important texts were only reachable through
secondary publishers.

### 3.1 New York City

#### 3.1.0 Two facts that invalidate most existing references

**(a) Zoning Resolution Article II Chapter 3 was completely renumbered on
2024-12-05** by *City of Yes for Housing Opportunity* (N 240290 ZRY). Every
section in that chapter now reads "Last Amended 12/5/2024". The old `23-60`
series no longer contains height-and-setback rules — **ZR 23-62 is now
"Balconies."** Height and setback moved to the **23-40** series; permitted
obstructions to **23-411 / 23-412 / 23-413**; the sky exposure plane to
**23-73**. **Article II Chapter 8 — the old Quality Housing Program chapter —
returns HTTP 404 and is gone.** DCP appears not to publish an old→new
conversion table; the correspondences are inference and are **[UNVERIFIED]**,
though the *current* numbering is verified against the live TOC.

**(b) The sky exposure plane has been demoted in residence districts.** It is
now an **opt-in alternative**, not the default. ZR 23-731, verbatim:

> "The optional provisions for sky exposure plane buildings set forth in Section
> 23-73, inclusive, **may be applied** to zoning lots in R6 through R10 Districts
> without a letter suffix, except that such alternative provisions shall not
> apply to: (1) zoning lots in R6-1, R6-2, R7-3 and R9-1 Districts; …"

The default residential envelope is now the **contextual** street-wall +
base-height + max-building-height model of ZR 23-431/432/433. **For a city
generator this is the single most consequential finding in the report**: the
iconic 1916-lineage stepped-ziggurat massing is no longer the *rule* for new
residential construction in NYC. It is the rule for what is *already standing*,
which is what a set dresses. Both models are needed, and they should be a
TYPOLOGY choice — `NYC_SkyExposurePlane` versus `NYC_Contextual` — not a style.

#### 3.1.1 The sky exposure plane, as a construction

Definition, ZR 12-10:

> "**Sky exposure plane** — An imaginary inclined plane: beginning above the
> *street line* … at a height set forth in the district regulations; and rising
> over a *zoning lot* at a ratio of vertical distance to horizontal distance set
> forth in the district regulations."

**[cited, but with a caveat: the official 12-10 page paginates and renders only
roughly A–F, so this definition was read from up.codes and corroborated by a
search snippet of the official page — wording consistent across two sources,
not read on the official site.]**

Three parameters generate it: **initial setback distance** from the street line;
**maximum front-wall height**; and a **slope** as vertical:horizontal. ZR 33-43
supplies the enabling rule; the numbers live in 33-431 and 33-432.

**ZR 33-432, commercial districts** [cited, table extracted three times with
agreement]:

| Districts | Initial setback (narrow / wide) | Max front wall | Plane height above street line | Slope narrow | Slope wide |
|---|---|---|---|---|---|
| C3, C4-1, C8-1 | 20 / 15 ft | 30 ft or 2 stories, whichever is less | 30 ft | **1 : 1** | **1 : 1** |
| C1-6, C2-6, C4-2…C4-5, C8-2, C8-3 | 20 / 15 ft | 60 ft or 4 stories | 60 ft | **2.7 : 1** | **5.6 : 1** |
| C1-7…C1-9, C2-7, C2-8, C4-6…C4-12, C5, C6, C8-4 | 20 / 15 ft | 85 ft or 6 stories | 85 ft | **2.7 : 1** | **5.6 : 1** |

**ZR 23-736, residence districts (opt-in)** [cited]:

| Districts | Initial setback (narrow / wide) | Max front wall | Slope narrow | Slope wide |
|---|---|---|---|---|
| R6, R7 | 20 / 15 ft | 60 ft or 6 stories | 2.7 : 1 | 5.6 : 1 |
| R8, R9, R10 | 20 / 15 ft | 85 ft or 9 stories | 2.7 : 1 | 5.6 : 1 |

**The slope is the same number everywhere.** `2.7 : 1` on a narrow street,
`5.6 : 1` on a wide street, across every district and both the commercial and
residential tables — only the low-density commercial tier differs, at `1 : 1`.
An **alternate** setback (ZR 33-442 commercial, 23-736(b) residential) trades a
deeper front open area (15 ft narrow / 10 ft wide) for a steeper plane at
**3.7 : 1** and **7.6 : 1**.

**So the generative rule is four numbers, not a lookup table.** `(initial
setback, front-wall height, slope_narrow, slope_wide)` — and only the middle one
really varies. Worked: a 60 ft front wall with a 15 ft initial setback, at 20 ft
in from the street line, permits **73.50 ft** at 2.7:1 and **88.00 ft** at 5.6:1
**[derived]**. The staircase profile that reads as "New York" is the building
maximising volume against that plane in whole-storey steps.

#### 3.1.2 The contextual envelope (the current default)

- **ZR 23-431** — street-wall location: on wide streets "at least 70 percent of
  the aggregate width of *street walls* shall be located within eight feet of
  the *street line*"; narrow streets, within 10 ft; large lots (≥40,000 ft² or
  full block), 50 % within 15 ft [cited].
- **ZR 23-432** — a table of min base height / max base height / max building
  height per district, in feet, with a second pair of columns for qualifying
  affordable or senior housing. Range runs from R6B (30 / 45 / 55) to the new
  **R11 and R12 districts created by City of Yes** (R12: 60 / 155 / 325, or 395
  with the affordable bonus) [cited].
- **ZR 23-433** — setback above the max base height: **≥10 ft from a wide-street
  street wall, ≥15 ft from a narrow-street street wall**, reducible by 1 ft per
  foot the wall sits behind the required front yard but **never below 7 ft**
  [cited].

#### 3.1.3 Dormers — the one rule that literally generates roof form

NYC has **two** dormer allowances and they are different.

**ZR 23-412**, low-density: "Dormers having an aggregate width of street walls
equal to not more than **50 percent** of the width of the street wall of a
detached or semi-detached single- or two-family residence" [cited].

**ZR 23-413**, contextual districts — the successor to the old 23-621(g). Within
a required front setback above a maximum base height, **either**:

> "the aggregate width of all dormers at the maximum base height does not exceed
> **60 percent** of the width of the *street wall* of the highest *story*
> entirely below the maximum base height. **For each foot above the maximum base
> height, the aggregate width of all dormers shall be decreased by one percent**
> …; **or**
> the aggregate width of all dormers at the maximum base height does not exceed
> **40 percent** … **Such dormers need not decrease in width as the height above
> the maximum base height increases.**"

[cited, fetched twice]

Three readings that matter for a generator:

1. **A dormer penetrates the required SETBACK, not the maximum height.** ZR
   23-433 says so explicitly. The roof still stops at the max building height.
   This is precisely the mechanism that produces the familiar New York mansard-
   with-dormers upper storey.
2. **The 60 %-decaying option produces a tapering dormer band** — 60 % at the
   base height, 1 percentage point narrower per foot of rise. That is a
   *formula*, and it is directly implementable: `dormer_fraction(h) =
   0.60 − 0.01·(h − base_height)`, clamped at 0, giving a battered profile that
   vanishes at 60 ft above the base height **[derived from the cited rule]**.
3. Where tower allowances are used (ZR 23-435), "dormers may only rise to a
   height equivalent to **75 percent** of the height of the tower portion" and
   count toward tower coverage [cited].

#### 3.1.4 Permitted obstructions — the rooftop furniture, with numbers

**ZR 23-411**, general [cited]:

| Obstruction | Limit |
|---|---|
| Chimneys / flues | total width ≤ **10 %** of aggregate street-wall width at any level |
| Decks / recreational surfaces | ≤ **3 ft 6 in** above the max height limit |
| **Parapets** | ≤ **4 ft**; railings ≤ 4 ft 6 in; safety guards ≤ 10 ft and **≥ 90 % transparent** |
| **Roof thickness** (insulation) | ≤ **12 in**, and only for buildings built **before 2024-12-05** |
| Skylights | ≤ 4 ft, ≤ 10 % of roof coverage, ≥ 8 ft from the street-wall edge; **not permitted above a roof sloped > 20°** |
| **Solar** | ≤ **15 ft** on roofs sloped < 20°; ≤ 6 ft on a bulkhead; ≤ **60 in measured perpendicular** on roofs sloped > 20° |
| **Vegetated roofs** | ≤ **3 ft 6 in** excluding vegetation; ≤ 12 in perpendicular on roofs sloped > 20° |
| Weirs / stormwater equipment | ≤ 3 ft 6 in |

**ZR 23-412**, bulkheads and tanks [cited]: elevator and stair bulkheads, roof
water tanks, energy infrastructure and accessory mechanical equipment must be
set back **≥ 10 ft from the street wall** (need not exceed 25 ft from a narrow
street line / 20 ft from a wide one), *except* where a bulkhead occupies ≤ 30 %
of the street-wall width. The bulk allowance is one of two:

- ≤ **50 % of building lot coverage** at up to **15 ft** above the max height; or
- ≤ **30 % coverage** at up to **25 ft** (R1–R5 and certain R3-2/R4/R5),
  **35 ft** (R6–R12 where max height ≤ 120 ft), or **55 ft** (R6–R12 where max
  height > 120 ft).

**This table is the rooftop-prop scatter rule.** `AB::RooftopProcessor` currently
scatters antennas and water tanks with no such constraint; feeding it the 30 %/
50 % coverage figure and the 10 ft street-wall setback would make a NYC rooftop
read correctly at almost no cost.

⚠ **ZR 33-42**, the commercial permitted-obstruction list, was **not retrieved**.
Its numeric limits are **[UNVERIFIED]**.

#### 3.1.5 The pitched-roof envelope — a directly implementable generator

**ZR 23-421 "Basic pitched-roof envelopes"** applies to single- or two-family
detached, semi-detached and zero-lot-line buildings in R1, R2, R3A, R3X, R3-1,
R3-2, R4, R4-1, R4A, R5A. **There is no maximum building height number at all.**
Verbatim:

> "Perimeter walls are subject to setback regulations at a maximum height above
> the *base plane* of **25 feet**. Above these heights, sloping planes control
> the maximum height … These planes start at the maximum permitted height of the
> perimeter walls and **meet at a ridge line of 35 feet above the base plane**."
> … "**The maximum angle of pitch for any sloping plane may not exceed 80 degrees
> to the horizontal.**"

and the apex rule for projecting wings:

> "(b) Each perimeter wall … with a horizontal dimension of eight feet or more
> which projects from an adjacent perimeter wall at least 18 inches may have an
> **apex point** directly above it on the 35-foot-high plane … provided **a line
> drawn from the intersection of two perimeter walls to such an apex point does
> not exceed 80 degrees to the horizontal**."

**[cited — (a)–(b) verified on the official site; (c)–(g) from up.codes because
the official page truncates after (b). Confirm (c)–(g) against the DCP PDF.]**

Read that as geometry and it is *exactly this report's subject*: **a wall plane
to 25 ft, sloping planes above it, converging on a ridge line at 35 ft, with a
maximum face angle of 80°.** It is a straight-skeleton envelope written into
law — the ridge is a locus, not a point, and the 80° cap is a weight floor
(`w_e ≥ cot 80° = 0.1763` **[derived]**). A generator can implement ZR 23-421
literally: run the skeleton, cap the lift at 35 − 25 = 10 ft of rise, and reject
any face steeper than 80°.

**ZR 23-422 "Basic flat-roof envelopes"** covers R3-2, R4, R4B, R5, R5B, R5D with
hard caps (R4B 25 ft; R3-2/R4/R5B/R5 base 35 ft; R5 building 45 ft; R5D 45 ft)
and **gives a pitched roof no relief whatsoever** — the top of the roof must be
at or below the maximum building height [cited].

R3-2 and R4 appear in **both** sections. A 1–2 family detached/semi-detached
house gets the sloping envelope; anything else on the same lot gets the 35 ft
flat cap. **That overlap is the actual answer to "how does a pitched roof count
in NYC."**

#### 3.1.6 How NYC measures height

Height is measured from the **base plane** in the residential height-and-setback
sections — ZR 23-42 and ZR 23-43 both state verbatim: "The height of all
buildings or other structures shall be measured from the base plane." [cited]

The base plane is not a computed constant. ZR 12-10: within 100 ft of a street
line "**the level of the base plane is any level between curb level and street
wall line level**" — i.e. **elected by the applicant within a range**. Beyond
100 ft it is the average final grade. Sites sloping ≥ 5 % may use a **sloping**
base plane. Multi-frontage lots get separate base planes or a lot-coverage-
weighted "adjusted base plane." [cited]

The **commercial** sky-exposure-plane rules use **curb level** for the front wall
and the **street line** for the plane. The ZR runs two datums in parallel and
says so — ZR 64-11 (flood) reads "base plane or curb level, as applicable."

**Headline: NYC has no citywide midpoint or mean-height rule for a pitched
roof, and a pitched roof is not on any permitted-obstruction list.** It cannot
penetrate a maximum height limit. A midpoint rule appears to exist in exactly
one special district, ZR 119-212 — **[UNVERIFIED, search snippet only]**.

The ZR's only other recognition of pitch is a **20° threshold that restricts
rooftop equipment** (§3.1.4), mirrored in the Building Code's roof-stair waiver.

#### 3.1.7 NYC Building Code

⚠ **Edition trap.** In the 2014 code, Rooftop Structures was **BC 1509**. In the
**2022 NYC Construction Codes** — current in 2026, with a separate Existing
Building Code taking effect 2027-07-17 — **BC 1509 is "Radiant Barriers" and
Rooftop Structures is BC 1510.** Citing 1509 in 2026 is an edition error.

| Provision | Section | Content |
|---|---|---|
| **Parapet minimum** | **BC 1510.8** | "Buildings greater than 22 feet in height with roof slopes less than **2.4 units vertical in 12 units horizontal (20-percent slope)** shall be provided with a parapet, guards, fence, or combination thereof, **not less than 42 inches** in height." Recreational roofs: wire fencing ≥ 10 ft (1510.8.1). |
| **Rooftop structures excluded from height** | **BC 504.3** | Roof tanks, mechanical, bulkheads, penthouses, chimneys and **parapets ≤ 4 ft** are excluded from building height "unless the aggregate area of all such structures … exceeds **33⅓ percent** of the area of the roof." |
| **Roof access** | **BC 1011.12** | Buildings **four or more stories or more than 40 ft** need a stair to the roof through a bulkhead — **unless the roof slope exceeds 20 degrees.** |
| **Cool roof** | **BC 1504.9** | Roofs sloped **≤ 2:12 (17 %)** need "a minimum initial solar reflectance of **0.7**." |
| **Sustainable roofing zone** | **BC 1512.2** | "A sustainable roofing zone shall be required on **100 percent of the roof**" — solar PV where ≥ 4 kW is achievable, otherwise a green roof on low-slope roofs. Seven exceptions. |
| Bulkhead construction | BC 1510.2 | Constructed as required for the building; relaxations where rooftop structures occupy ≤ 33 % of roof area. |

**A precise interlock worth encoding.** ZR 23-411(f) caps a parapet at **4 ft**
as a permitted obstruction; BC 1510.8 requires **at least 42 in** on any
low-slope roof over 22 ft. **A compliant NYC parapet is therefore between 3 ft 6
in and 4 ft — a 6-inch window.** That is a hard constraint, not a taste, and it
should be the default parapet height in the catalog for any NYC row.

**And the biggest single driver of contemporary NYC roof appearance is BC 1512**:
a required sustainable roofing zone over 100 % of the roof means the default
modern NYC roof is a *fully occupied technical plane* — solar array or green
roof — with the ZR 23-411(j)/(k) height allowances (15 ft solar, 3 ft 6 in
vegetated) determining how tall the clutter reads. A bare grey membrane deck is
now the historical condition, not the current one.

⚠ **Sourcing caveat for all of §3.1.7:** amlegal (NYC's official code library)
and `nyc.gov/site/buildings` both return **HTTP 403** to direct fetch. Every
Building Code quotation above is from **up.codes**, a secondary publisher.
Section numbers and edition labels were consistent across multiple up.codes
pages, but for legal citation they must be confirmed against DOB or amlegal.

### 3.2 San Francisco

Edition verified from the page header: SF Planning Code, American Legal
**"2026 S-96 (current)."**

#### 3.2.1 The premise was wrong, and the truth is better

I went looking for a provision letting a pitched roof rise a fixed number of
feet above the SF height limit. **There is no such provision.** The complete
text of § 260(b) — all of (b)(1)(A)–(O) and (b)(2)(A)–(R) — was read; pitched
roofs appear nowhere in the exemption list. **Treat "a pitched roof gets N extra
feet in SF" as disconfirmed, not merely unverified.**

What SF does instead is change the **measurement rule**. § 260(a)(2), verbatim:

> "The upper point to which such measurement shall be taken shall be the highest
> point on the finished roof in the case of a flat roof, and **the average height
> of the rise in the case of a pitched or stepped roof, or similarly sculptured
> roof form**, or any higher point of a feature not exempted under subsection
> (b) below."

[cited]

So the ridge legally overtops the numeric limit by **half the rise**, uncapped —
the bonus is a function of the roof's own geometry rather than a fixed
allowance. A 6:12 gable on a 30 ft-wide house earns 3.75 ft; a 12:12 gable earns
7.5 ft **[derived]**. *Every extra degree of pitch buys height.*

And SF caught the exploit that creates. Zoning Administrator interpretation on
§ 260(a)(2), *Measurement of pitched roof*, effective 6/96, revised 3/21,
verbatim:

> "This method of measurement could encourage buildings to be built that have
> higher roofs than would otherwise be designed in order to maximize the floor
> area … by placing habitable floors within the building volume above the eave
> line using dormer windows, skylights, or windows on walls surrounded by the
> pitch of the roof. To neutralize this tendency, **in cases where habitable
> floors occupy the area above the eave line, the point that is the minimum legal
> ceiling height for occupancy per the Building Code shall be used as a guideline
> to determine the location of the bottom of the roof** for purposes of this
> paragraph."

[cited] SF patched the loophole by **relocating the notional eave upward**
rather than by capping the bonus — so the reward survives only for a roof that
is genuinely a roof and not a disguised storey. That is an unusually elegant
piece of drafting and it is directly modellable: the averaging datum is
`max(actual eave, the height at which 7 ft of clear ceiling first exists)`.

#### 3.2.2 The exempt-features list — an *area* budget

§ 260(b)(1) chapeau, verbatim:

> "…the sum of the horizontal areas of all features listed in this subsection
> (b)(1) shall not exceed **30%** of the horizontal area of the roof above which
> they are situated… and provided further that in any R, RC-3, or RC-4 District
> the sum of the horizontal areas of all such features located **within the first
> 10 feet of depth of the building** … **shall not exceed 20%** …"
>
> "Any such sum of 30% heretofore described **may be increased to 40% by unroofed
> screening** designed either to obscure the features listed under (A) and (B)
> below or to provide a more balanced and graceful silhouette for the top of the
> building."

[cited]

That last clause is a design-quality bargain written into law: *screen it well
and you may cover more roof.*

| Feature | § 260(b) limit |
|---|---|
| Mechanical, chimneys, vents, cooling towers, water tanks, solar panels, window-washing gear | top **16 ft** where the limit is ≤ 65 ft; top **20 ft** where > 65 ft |
| Elevator, stair and mechanical penthouses, fire towers, skylights, **dormer windows** | same 16 / 20 ft; **elevator penthouses limited to the footprint of the shaft**, and their design "shall be consistent with the *Residential Design Guidelines*" |
| Ornamental features of public and religious buildings — towers, spires, cupolas, belfries, domes | exempt "where such features are not used for human occupancy" |
| C-3 spires and vertical extensions | up to **75 ft** above the limit via § 309 |
| **Railings, parapets and catwalks** | **max 4 ft, and exempt from the area cap entirely** (b)(2)(A) |
| Flagpoles, clotheslines, weathervanes, antennas, cranes | exempt, no area limit |

[all cited]

#### 3.2.3 Inclined planes, height-and-bulk notation, dormers

- **§ 261**, certain RH districts: RH-1 family capped at **35 ft**, rising to 40
  where the rear lot line averages ≥ 20 ft higher than the front, falling to 30
  and 25 ft on downhill lots. **§ 261(c)(1) adds a front-yard 45° inclined plane
  rising from 30 ft at the front lot line**, and § 261(c)(2) lets that limit rise
  to *the average height of the two adjacent buildings* — contextual height by
  formula, which is a straightforwardly implementable neighbour rule [cited].
- **§ 261.1**, narrow streets and alleys (ROW ≤ 40 ft): upper storeys set back
  ≥ 10 ft above a height equal to **1.25 × the width of the abutting narrow
  street**; east–west narrow streets also get a **45° sun access plane** from the
  opposite property line [cited].
- **§ 252 and Table 270** decode the notation: **"40-X" = 40 ft height limit +
  bulk district X**, and **"X" means Table 270 does not apply — no plan-dimension
  limits at all**. Lettered bulk districts cap the plan *length* and *diagonal*
  above a stated height (e.g. A: above 40 ft, 110 ft length, 125 ft diagonal;
  M: above 100 ft, 250 / 300) [cited]. The 40-X workhorse is therefore
  height-controlled and bulk-unconstrained, which is why SF's fabric is even and
  low rather than stepped.
- **§ 263.6, Chinatown corners and parapets** — the most roof-form-explicit
  provision found in any of the three cities. It permits a corner "decorative
  pavilion, sculpture or pagoda" ≤ 150 ft², or "a decorative parapet similar to
  those existing in the Chinatown area," extending **not more than eight feet**
  above the limit, expressly "to reassert the traditional Chinatown pattern"
  [cited]. **A city buying a specific historic roofline with bonus height.** For
  a set-dressing tool this is a gift: a named regional roof articulation with a
  legal dimension attached.

**Dormers — ZA Bulletin 3 is REPEALED** as of March 2026; dormers are now in
**ZA Bulletin 4** (issued Oct 2002, revised March 2026). Under § 311(b)(4),
verbatim:

> "Dormers are not considered an 'alteration' when they, along with all other
> features exempt from the height limit and notification on a building
> collectively **do not exceed 20 percent of the roof area**; and when each dormer
> is limited to a **plan dimension of eight feet by eight feet**, is setback **at
> least three feet from the side property line and 10 feet from the front
> building wall**, is separated by **at least three feet from other dormers**, and,
> at its highest point is **no higher than the peak of the roof nor 10 feet above
> the height limit, whichever point is lower**."

[cited] ⚠ **The repealed ZAB 3 PDF still returns HTTP 200 and reads as
authoritative. Its live presence is not evidence of currency**, and its numbers
were already out of step with the codified § 260(b) figures. Do not cite it.

**This is a complete, implementable dormer placement rule** — a Poisson-disc
scatter with radius 3 ft, cell size 8 × 8 ft, margins of 3 ft from the side and
10 ft from the front, total area budget 20 %, height clamp `min(ridge,
limit + 10)`.

#### 3.2.4 Residential Design Guidelines — roof form as a review criterion

Adopted by the Planning Commission **2003-12-04**. ⚠ The SF Planning landing page
metadata says "December 2013" but serves the **2003** document — cite 2003.
These are mandatory, not advisory: Planning Code § 311(c)(1) provides that they
"shall be used to review plans for all new construction and alterations" [cited].

- **p. 30, "Rooflines"** — *"Design rooflines to be compatible with those found on
  surrounding buildings."* "Predominant rooflines found on buildings in San
  Francisco include front gabled, multi-gabled, hipped, or flat… if most
  buildings have front gables, **adding a building with a flat roof may not be
  consistent with the neighborhood pattern**."
- **p. 38–39, rooftop features** — *"design rooftop features with the smallest
  possible overall dimensions"*; **"Limit the number of rooftop features"**; stair
  penthouses may be eliminated by roof hatches; *"Slope the roof of the penthouse
  structure to follow the slope of the interior stairway."*
- **p. 39, parapets** — *"Using a fire-rated roof can eliminate the need for a
  parapet wall, reducing the height of a building as viewed from the street."*
- **p. 40, dormers** — *"The minimum recommended set back is 10 feet. The peak of
  the dormers should not be higher than the peak of the building's roof."*
- **Appendix C, p. 57, "Roof Forms"** illustrates exactly **five**: **Gable,
  Gambrel, Hip, Mansard, Shed.**

Two corrections worth carrying: **the RDG contains no numeric roof-pitch
requirement anywhere**, and **it does not tie roof form to topography** — roof
form is keyed only to surrounding *buildings* (p. 30), while topography (p. 11)
is a separate site-design principle about placement. Do not merge them.

### 3.3 Los Angeles

Edition verified from the page header: LAMC, American Legal **"2026 Rev. 8
(current)."**

#### 3.3.1 Height is measured to the highest point — full stop

LAMC § 12.03, *Height of Building or Structure*, verbatim:

> "Is the vertical distance above grade measured to **the highest point of the
> roof, structure, or the parapet wall, whichever is highest**. Retaining walls
> shall not be used for the purpose of raising the effective elevation of the
> finished grade…"

[cited] **There is no averaging of a sloped roof anywhere in the LA
definition.** This is the sharpest contrast with SF in the whole report.

*Grade* is "the lowest point of elevation of the finished surface of the
ground… between the building and the property line, or … a line 5 feet from the
building." In hillside areas, *Grade* is "the finished or natural surface of the
ground, **whichever is lower**" [cited].

⚠ A genuine drafting seam worth a footnote: **§ 12.03 defines "Slope" as a
property of a *ground surface*** — "an inclined ground surface the inclination of
which is expressed as a ratio of horizontal distance to vertical distance… or as
a percentage" — **yet the height provisions apply the same term to roofs. The
code never separately defines roof slope.**

#### 3.3.2 The pitched-roof bonus — a step function at 25 %

LAMC § 12.21.1 (Ord. 181,624, eff. 5/9/11), verbatim, for lots **not** in a
Hillside Area or Coastal Zone:

> "In the R1, RS, or RE9 Zones, no Building or Structure shall exceed 33 feet in
> height; **except that when the roof of the uppermost Story of a Building or
> Structure or portion of the Building or Structure has a Slope of less than 25
> percent, the maximum height shall be 28 feet.** In the RE11, RE15, RE20, RE 40
> or RA Zones, no Building or Structure shall exceed 36 feet in height; except
> that when the roof… has a Slope of less than 25 percent, the maximum height
> shall be 30 feet."

[cited] **25 percent is exactly 3:12** **[derived]** — but note the code says
*percent* and never states a 3:12 ratio. Cite the percentage.

The Baseline Hillside Ordinance repeats the structure with its own table.
**Table 12.21 C.10-4** [cited, retrieved in full]:

| Height District | Slope ≥ 25 % — R1/RS/RE9 | Slope ≥ 25 % — RE11…RA | Slope < 25 % — R1/RS/RE9 | Slope < 25 % — RE11…RA | **Bonus** |
|---|---|---|---|---|---|
| 1, 1L, 1VL | 33 | 36 | 28 | 30 | **+5 / +6 ft** |
| 1XL | 30 | 30 | 28 | 30 | +2 / **0** |
| 1SS | 22 | 22 | 18 | 18 | **+4 ft** |

**The threshold is applied per portion**, not per building — "or portion
thereof… for said portion of Building or Structure thereof." A mixed-roof design
earns the bonus only over its ≥ 25 %-slope portions. That is a strong shaping
incentive, and it is why LA hillside houses so often carry a token pitched
element over an otherwise flat mass.

Also: a **prevailing-height override** — where "40 percent or more of the
existing One-Family Dwellings with Frontage on both sides of the block have
Building heights exceeding these limits, the maximum height for any Building on
that block may be the average height of the Dwellings exceeding these limits"
[cited]. A contextual rule that a city generator can evaluate directly from its
own neighbours.

#### 3.3.3 Roof structures — feet and setback, never area

LAMC § 12.21.1 B.3 (Ord. 182,110, eff. 5/29/12), verbatim:

> "Tanks or similar equipment required to operate and maintain the building,
> skylights, towers, steeples, flagpoles, smokestacks, wireless masts, water
> tanks, silos, or similar structures may be erected above the building height
> limit by **up to five feet if the structure is set back from the roof perimeter
> by five feet**.
> Chimney, exhaust ducts, solar water heaters, or any roof structure housing
> stairways, elevators or ventilation fans may also exceed the building height
> limit by **up to five feet, but are not required to provide a setback** … **Where
> height is limited to seventy-five (75) feet, roof structures for the housing of
> elevators and stairways may exceed the building height limit by up to twenty
> (20) feet …, and where height is limited to thirty (30) feet or forty-five (45)
> feet, … by up to ten (10) feet …**
> **No such structure or any other space above the specified height limit shall be
> allowed for the purpose of providing additional floor space.**"

[cited] **There is no area-percentage limit in LAMC 12.21.1 B.3.** LA controls
roof structures by feet plus setback, not by roof coverage. Solar gets +3 ft
anywhere with no setback, and **+15 ft on a flat roof** outside R1 and more
restrictive zones [cited].

Hillside **Table 12.21 C.10-5** adds two unambiguous numbers worth having:
**a stairway housing no larger than 36 ft² needs no setback**, and **skylights
covering more than 33⅓ % of the roof are limited to 30 inches** [cited; some
merged cells in that table were ambiguous on extraction].

LADBS bulletin **IB/P/ZC 2023-008** ("Determination of the Zoning 'Height of a
Building or Structure'", effective 2023-01-01) supplies the procedure and one
very useful worked example: lowest grade within 5 ft of the wall = 104 ft;
highest point = 155 ft at a chimney; "however, a chimney is allowed to project
up to 5'. Therefore, the highest point of the building to be used is 153'" →
**49 ft** of height. The bulletin explicitly labels the section/elevation method
**INCORRECT**, noting it "often results in an INCORRECT building height of 45
ft" — *the same building, 4 ft apart, purely from method* [cited]. It also
states that the **Zoning Code definition of height differs from the Building
Code definition and each must be applied independently.**

#### 3.3.4 ⚠ The new LA zoning code deletes roof form from the conversation

LA is replacing Chapter 1 zoning with **LAMC Chapter 1A**, applied incrementally
as Community Plans update. **Article 2 (Form)** was established by Ord. 188,418,
effective 2025-01-20, operative 2025-01-27.

Measurement, Sec. 2C.4.2.D.1: "Maximum height in feet is measured as the
vertical distance from **grade plane to the top of the roof structure**." Allowed
vertical encroachments (Sec. 2C.4.2.E) are graduated by district height rather
than flat:

| Feature | ≤ 45 ft | > 45–90 ft | > 90 ft |
|---|---|---|---|
| Roof-mounted mechanical | 3 ft *(setback 3)* | 5 ft *(3)* | 10 ft *(5)* |
| Architectural elements | 5 ft *(3)* | 5 ft *(3)* | 10 ft *(5)* |
| **Vertical circulation** | **10 ft *(setback 0)*** | **20 ft *(0)*** | **20 ft *(0)*** |
| Safety barriers | 6 ft *(0)* | 6 ft *(0)* | 6 ft *(0)* |

**And the decisive finding: a full-text search of the 98-page Article 2 for
"pitch", "slope", "gable", "hip roof", "roof form", "roof type" and "dormer"
returns ZERO hits.** Chapter 1A **abolishes the sloped-roof height bonus
entirely.** Under the new code a pitched roof is neither rewarded nor
penalised; height runs plumb from grade plane to the top of the roof structure
regardless of shape.

For a report about roof form that is the most striking result of the whole code
survey: **the *form-based* code regulates roof form less than the code it
replaces.**

⚠ **[UNVERIFIED]** which geographies Chapter 1A is currently operative in. It
applies incrementally via Community Plan updates and the coverage map was not
checked.

### 3.4 Where the three cities disagree — and why that is the useful part

The agreements are dull (everyone permits bulkheads, everyone caps parapets
somewhere near four feet). The disagreements are where authentic regional
variation comes from, and there are four real ones.

#### Disagreement 1 — is a pitched roof rewarded, and how?

| | New York City | San Francisco | Los Angeles (Ch. 1) | Los Angeles (Ch. 1A) |
|---|---|---|---|---|
| **Mechanism** | A **separate envelope**: no height number at all in ZR 23-421, just walls to 25 ft and planes converging on a 35 ft ridge | The **measurement rule**: § 260(a)(2) measures to the *average height of the rise* | **Explicit extra feet** at a slope gate | **None** |
| **Measured to** | Envelope containment, not a point | **Midrise** | **Highest point** of roof / structure / parapet | Top of roof structure |
| **Size of reward** | Structural, not numeric | **Uncapped — half the rise.** Steeper pays more, continuously | **Fixed: +5 ft** (R1/RS/RE9), **+6 ft** (RE11–RA), +4 (1SS), +2 or 0 (1XL) | Zero |
| **Threshold** | Max pitch **80°**; equipment rules switch at **20°** | None — any pitch qualifies | **Slope ≥ 25 % (= 3:12)**, applied **per portion** | n/a |
| **Anti-abuse** | Pitched roof is not a permitted obstruction; it simply must fit | ZA interpretation relocates the notional eave to minimum legal ceiling height | Not needed — measured to the peak | n/a |

**The architectural consequences are opposite in character and both are real.**
SF's rule is **continuous** — every extra degree of pitch buys height — which
favours steep, expressive roofs and required a patch to stop the attic becoming
a floor. LA's is a **step function** — 24 % and 26 % slope differ by five feet of
legal building — which pushes designs to cluster *exactly at* the threshold and
gives no incentive to go steeper. **SF pays by the degree; LA pays a flat bounty
at a single gate; NYC does not pay at all and instead draws the envelope for
you.**

For a generator, that is three genuinely different pitch *distributions* from
one line of policy each:

- **SF:** a broad distribution skewed steep, because steeper is strictly better.
- **LA:** a **spike at exactly 3:12** with a thin tail, because 25 % is the whole
  prize and nothing above it pays.
- **NYC (low-density):** pitch determined by the geometry of a 25 ft wall and a
  35 ft ridge over the given depth — so the pitch is a *consequence of the plan
  depth*, and narrow lots get steep roofs while deep lots get shallow ones.
  **[derived from the cited envelope: for a house of depth `D`, the maximum
  uniform pitch is `atan(10 / (D/2))`, e.g. 30 ft deep → 33.7°, 50 ft deep →
  21.8°.]** That is a footprint-driven pitch, which is exactly this report's
  subject appearing in law.

#### Disagreement 2 — rooftop mechanical: an area budget or a height allowance?

| | NYC | San Francisco | LA (Ch. 1) |
|---|---|---|---|
| **Controlling metric** | **Both** — coverage % *and* feet | **Percentage of roof area** | **Feet + setback** |
| **Area cap** | 50 % @ 15 ft, or 30 % @ 25/35/55 ft | **30 %, → 40 % with unroofed screening**; 20 % in the front 10 ft in R districts | **None** |
| **Mechanical height** | Per the coverage tier above | top **16 ft** (limit ≤ 65) / **20 ft** (> 65) | **5 ft** + 5 ft setback |
| **Elevator / stair** | Same tiers; ≥ 10 ft from the street wall unless ≤ 30 % of street-wall width | top 16 ft; **limited to the shaft footprint**; design bound by the RDG | **10 ft** (30/45 ft limits), **20 ft** (75 ft limit) |

**SF regulates the roofscape as a *silhouette* problem; LA regulates it as a
*dimensional* one; NYC regulates it as a *bulk* problem.** SF's 30 %→40 %
screening bargain and the RDG's "limit the number of rooftop features" treat the
roof as a composed object. LA gives you five feet and a setback and does not ask
what it looks like. NYC gives you a coverage fraction and a street-wall setback
and cares mainly that you cannot see it from the pavement.

That produces three visibly different rooftops, and it is free regional variety:
- **SF:** few, small, screened objects, clustered away from the front 10 ft.
- **LA:** many small objects, all about five feet tall, five feet in from the
  edge, unscreened.
- **NYC:** a small number of *large* volumes — bulkheads and tanks — set well
  back from the street wall, plus, since Local Laws 92/94 of 2019, a **solar or
  green roof over 100 % of the remaining roof**.

#### Disagreement 3 — parapets

The single sharpest divergence, and it is one detail.

- **SF § 260(b)(2)(A):** parapets exempt from the height limit up to **4 ft**,
  *and* exempt from the 30 % area cap entirely.
- **NYC:** ZR 23-411(f) permits **4 ft**; BC 1510.8 *requires* **≥ 42 in** on any
  roof sloped < 20 % on a building over 22 ft. **A compliant NYC parapet lives in
  a 6-inch window between 3 ft 6 in and 4 ft.**
- **LA § 12.03:** height is measured **to the parapet wall, whichever is
  highest.** A parapet is not exempt at all.

**The identical detail is free in San Francisco, mandatory-and-nearly-fixed in
New York, and costs a foot of building for every foot of parapet in Los
Angeles.** SF's own guidelines push designers to delete it — "using a fire-rated
roof can eliminate the need for a parapet wall, reducing the height of a
building as viewed from the street." That one sentence explains a great deal
about why SF and LA rooflines read differently, and it is a two-line rule in a
catalog.

#### Disagreement 4 — the datum, and terrain

- **NYC:** the **base plane**, which within 100 ft of a street is *elected by the
  applicant* anywhere between curb level and street-wall-line level. Sloping
  lots ≥ 5 % may use a *sloping* base plane. Multi-frontage lots may use a
  lot-coverage-weighted "adjusted base plane."
- **SF:** curb level at the **building centreline** on level or downhill lots;
  **averaged ground elevations per cross-section** on uphill lots; **the owner
  chooses** the governing street on a corner. Lateral slope then caps the
  **width** that may be measured from one point — Table 260-1 falls from 65 ft to
  **35 ft** as cross-slope passes 25 %.
- **LA flatland:** a single **lowest** grade within 5 ft of the wall to a single
  **highest** point. One datum, one peak.
- **LA hillside:** the strictest of all — a **plumb-line envelope from Hillside
  Area Grade at every section**: "At no point shall any given section of any part
  of the proposed Building or Structure exceed the maximum envelope height,"
  plus a 20 ft / 45° encroachment plane in R1.

So **LA constrains the whole envelope continuously on a hillside while SF
constrains a measured width and lets the ridge float, and NYC lets the applicant
pick the datum.** LADBS even declares its general height bulletin inapplicable to
BHO lots — **Los Angeles runs two genuinely different height-measurement regimes
in one city**, which is itself a source of variation within LA.

### 3.5 Sourcing caveats for §3, consolidated

| Item | Status |
|---|---|
| NYC Zoning Resolution (zr.planning.nyc.gov) | **Fetched directly.** ⚠ The site *truncates* — plain URLs silently drop enumerated sub-paragraphs and tables; the `/index.php/` variant of the same path returns more. Tables were extracted 2–3 times before being trusted; one extraction of ZR 23-736 reported 5 district rows where there are 2. |
| NYC ZR 12-10 definitions ("sky exposure plane", "initial setback distance", "story") | ⚠ The official 12-10 page renders only ~A–F. Read from up.codes and corroborated by a search snippet. **Not read on the official site.** |
| NYC ZR 33-42 (commercial permitted obstructions) | **NOT RETRIEVED. Numeric limits [UNVERIFIED].** |
| NYC ZR 23-421 (c)–(g) | up.codes only; the official page truncates after (b). Confirm against the DCP PDF. |
| All NYC Building Code text | **up.codes only.** amlegal and nyc.gov/site/buildings return **HTTP 403** to fetch. |
| "2022 NYC Construction Codes current in 2026" | From a search snippet of a 403-blocked DOB page. |
| City of Yes old→new section mapping | **Not published by DCP.** All old→new correspondences are inference, **[UNVERIFIED]**. |
| ZR 119-212 pitched-roof midpoint rule | **Search snippet only, [UNVERIFIED].** A special-district provision, not citywide. |
| SF Planning Code, LAMC | **Fetched directly** via `curl` with a browser user-agent — `codelibrary.amlegal.com` and `planning.lacity.gov` return **HTTP 403** to ordinary fetch. Worth recording; it will bite anyone reproducing this. |
| SF Planning Code § 102 definition of "Height" | **NOT RETRIEVED.** The operative measurement is § 260 regardless. |
| SF Residential Design Guidelines date | Document says **December 2003**; landing-page metadata says December 2013. **Cite 2003.** |
| SF ZA Bulletin 3 | **REPEALED March 2026** — but the PDF still returns HTTP 200 and reads as current. Do not cite. |
| LAMC Chapter 1A geographic applicability | **[UNVERIFIED.]** Applied incrementally via Community Plan updates. |
| LA Table 12.21 C.10-5, IB/P/ZC 2023-008 Chart 1 | Merged-cell tables; some cells ambiguous on extraction. The 36 ft² stairway and 30 in skylight values are unambiguous. |
| Raster figures throughout | Dimension callouts in RDG figures, CP-4061 Figure 3, LAMC Figure 12.21 C.10(d)(1)(i) are **not recoverable from text layers**. |

⚠ **One hallucination was detected and discarded during this research**: a fetch
of NYC ZR 23-421 returned confident fake "verbatim" text containing a *"for each
foot of horizontal distance… the plane rises vertically at a rate of one foot"*
formula that conflicts with the real section. **If that phrasing appears
anywhere downstream, it is not ZR text.** Recording it here because the failure
mode — a plausible, well-formed, entirely invented code quotation — is exactly
the one this project's confidence marks exist to catch.

---

## 4. The AssetBash implementation plan

### 4.1 The smallest vocabulary: four operators

The project has proven this shape twice — metal sections reduced to a handful of
parameters, and 200 moulding profiles reduced to ten composable elements. The
roof equivalent is **four operators**, and the first one absorbs fourteen of the
eighteen named forms in §2.1.

---

**OP 1 — `SKELETON`.** A weighted straight skeleton, lifted by a banded section
profile.

Inputs:
- the footprint polygon;
- a **per-edge weight vector** `w_e` (§1.6): `cot θ_e`, or `0` for a vertical
  end;
- an ordered **band list**: the section profile in (run, rise).

That is it. Read the forms off it:

```
  Gable            w = [1,0,1,0]      slope(6)
  Hip              w = all 1          slope(6)
  Pyramidal        w = all 1          slope(10)          [regular footprint]
  Hip-and-valley   w = all 1          slope(6)           [non-convex footprint]
  Cross-gable      w = [1,0,1,0,...]  slope(8)           [cruciform footprint]
  Shed             w = [1,0,0,0]      slope(3)
  Butterfly        w = [1,0,1,0]      slope(-2)
  Flat + parapet   w = all 0          wall(p) ; flat()
  Jerkinhead       w = [1,0,1,0] slope(9, to_rise=0.75H) ; w = all 1  slope(9)
  HipWithGablet    w = all 1     slope(9, to_rise=h)     ; w = [1,0,1,0] slope(9)
  Gambrel          w = [1,0,1,0] slope(29, to_rise=0.7071R) ; slope(5)
  Mansard          w = all 1     slope(30, to_rise=h)    ; slope(3)
  Monitor (section) w = [1,0,1,0] slope(6,to_rise=h1) ; wall(h2) ; slope(6)
  Barrel           w = [1,0,1,0]      arc_convex(R, R)
  Dome             w = all 1          arc_convex(R, R)   [circular footprint]
  Saltbox          w = [1,0,c,0]      slope(10)          [+ ridge offset]
```

**Fourteen named roof types, one operator, no branching.** Cross-gable and
hip-and-valley need no entry at all — they are gable and hip on a different
footprint. That is the reduction this report exists to find.

**The band elements are the moulding elements.** This is not an analogy. A roof
section drawn in (horizontal offset, height) is a moulding profile drawn in
(projection, face) — same 2D curve, same authoring problem, same "each element
declares the box it consumes" solution, and therefore the same mechanical
dimension check. `moulding_grammar.py` already ships `line`, `chamfer`, `ovolo`,
`cove`, `bead`, `scotia`, `cyma_recta`, `cyma_reversa`, `quirk`, `fillet`. Map
them:

| Roof band | Moulding element | Gives you |
|---|---|---|
| `slope(p, …)` | `line(run, rise)` | Every straight roof plane |
| `wall(h)` | `line(0, h)` | Gable ends, parapets, monitor walls, mansard curbs |
| `flat(r)` | `line(r, 0)` — in practice `line(r, r/48)` | Flat decks at the code ¼:12 |
| `arc_convex` | `ovolo` | Barrel vaults, domes, bell-cast eaves |
| `arc_concave` | `cove` | Flared eaves, concave mansards, pagoda curves |
| `ogee` | `cyma_recta` / `cyma_reversa` | Ogee domes, Tudor and East Asian roofs |
| — | `quirk` | The small setback at a break line, e.g. a mansard curb |

**So the roof section grammar is the moulding grammar, reused, not rewritten.**
The catalog column can literally hold the same kind of string:
`"slope(29,to_rise=.7071) slope(5)"`. That is a strong argument for building
`RoofSection` on top of the existing module rather than beside it.

---

**OP 2 — `SWEEP`.** A periodic section swept along an axis and clipped to the
footprint.

Inputs: axis direction, period, section profile, phase.
Covers: **sawtooth, folded plate, repeated monitors, repeated barrel vaults,
corrugated and standing-seam relief at a coarse scale.**

This is the operator the skeleton genuinely cannot supply, because a periodic
roof's direction and period are not in the perimeter. In the northern hemisphere
the sawtooth glazing faces north [trade], so the axis can at least default from
the scene's north vector rather than from a raw number — a small thing that
makes a city of sawtooth sheds read as coherent instead of random.

---

**OP 3 — `INSERT`.** A sub-mass booleaned into a roof face.

Covers: **dormers** (gable, shed, hipped, eyebrow, wall), **bulkheads and stair
penthouses**, **elevator overruns**, **water tanks**, **chimneys**, **skylights**,
**mechanical screens**, **cupolas**. Each is a small footprint given its own
`SKELETON` call — a gable dormer is literally a tiny gable roof — and unioned in,
with the parent face providing the cut plane.

Every item in that list is also a **zoning object** (§3), which is why this
operator must accept an externally supplied allowance envelope rather than
inventing its own limits.

---

**OP 4 — `TRIM`.** A profile swept along a classified skeleton edge.

Covers: **eave/fascia/soffit, rake, ridge cap, hip cap, valley flashing, gutter,
parapet coping, cornice, cresting, snow guards, drip edge.**

The skeleton already classifies its edges — eave, ridge, hip, valley — so the
edge groups the moulding sweeper needs are produced for free by OP 1. This is
where **all** of the STYLE axis lives (§4.5). It is also where the existing
moulding work lands a second time.

---

**Four operators. Eighteen-plus roof forms.** The tool that does not exist yet is
OP 1; OP 4 is largely a re-aim of shipped moulding code.

### 4.2 What Houdini already gives us

`polyexpand2d` **computes the straight skeleton** — "The node computes the
straight skeleton of the input, and to do so tries to build a triangulation of
the input and its convex hull" [cited — SideFX docs]. More importantly it
already exposes exactly the two things §1.6 needs:

- **Inside Scale** — a *local attribute* (vertex, point or primitive) that
  "scale[s] the inside offset for each edge by the value of this attribute";
  non-positive values are ignored [cited].
  **This is the multiplicative weight.** Set it to `cot θ_e` and the weighted
  straight skeleton is native — no custom solver.
- **Edge Distance Attribute** (vertex) — distance from the original polyline —
  and **Edge Speed Attribute** (prim) — propagation speed, 1.0 when unscaled
  [cited]. Between them, height is reconstructible per face.

Also present and directly relevant: **Divisions** ("Numbers greater than 1
divide the offset distance into multiple evenly spaced outlines") for banding;
**Coincidence Tolerance** and **Parallelism Tolerance** for §1.4's degeneracies;
**Skeleton Failure** handling; **Cache Straight Skeleton**.

**⚠ Two things to verify in Houdini before designing around them** — I did not
have a Houdini session and will not assert them:

1. Whether `edgedist` is measured to *that face's own* source edge (which makes
   `z = edgedist · tan θ_e` correct under weighting) or to the nearest source
   edge globally (which does not). **[UNVERIFIED — this is the single most
   important thing to test first.]**
2. Whether `Inside Scale` of exactly `0` is usable for a gable end, given the
   documented "non-positive values are ignored". If not, a gable must be made by
   an epsilon weight plus a post-clip, or by pre-splitting the footprint.
   **[UNVERIFIED]**

**⚠ Do not use `Labs Straight Skeleton 3D`.** Its documentation calls the
straight skeleton "also called a medial axis" and it is a voxel mesh-shrinking
solver [cited] — §1.5. It is the wrong tool with the right name.

### 4.3 Where it sits among the existing tools

Measured from `analysis/tools.csv` and `analysis/parms.csv` (2026-08-15): **the
library has no roof-form generator at all.** What exists is:

- `AB::RooftopProcessor::1.0` (BuildingHelpers) — 0 parameters, 108 inner nodes.
- `AB::RoofVentGenerator::3.0`, `AB::RooftopMechanicals::3.0`,
  `AB::RoofTopSignGenerator::4.8` — all rooftop *props*, not roofs.
- `AB::ApartmentRow::1.2` has a `RoofStyle` menu with exactly **two** entries:
  `Flat` and `Peaked`.
- Everything else is `RoofDepth`, `roof_thick`, `roof_overhang`, `RoofColor` —
  i.e. a slab with a thickness.

Three more measured facts from `analysis/nesting.csv`, and they settle the
build-versus-reuse question:

- **`polyexpand2d` appears nowhere in the library.** Zero uses across ~155 HDAs.
  The core capability of this whole report is unused, native, and free.
- `labs::straight_skeleton_2D` appears exactly **once**, inside
  `AB::CommercialSignGenerator::4.8` — so the node is not unknown here, just
  never aimed at a roof.
- **Nothing nests `AB::RooftopProcessor::1.0`.** It is an orphan helper that
  scatters `AB::AntennaGenerator` and `AB::WaterTankGenerator` onto a deck via
  `copytopoints`. It has no consumer to break, which makes it safe to re-point
  at a real roof deck.

So this is a genuine gap, not a duplication. Proposed placement:

| HDA | Category | Role |
|---|---|---|
| `AB::RoofSkeleton::1.0` | `Sops/BuildingHelpers` | OP 1. Footprint + weights + bands → roof faces, with `s@name` zones and edge groups. The one hard piece. |
| `AB::RoofSweep::1.0` | `Sops/BuildingHelpers` | OP 2. |
| `AB::RoofTrim::1.0` | `Sops/BuildingHelpers` | OP 4. Wraps the moulding sweeper onto skeleton edge groups. |
| `AB::DormerMaker::1.0` | `Sops/BuildingProps` | OP 3, one dormer. Nests `RoofSkeleton`. |
| `AB::RoofGenerator::1.0` | `Sops/Buildings` | The shipping tool. Reads the catalog row, drives the four above. |

`AB::RooftopProcessor` stays what it is — the place rooftop props are scattered
— and consumes `RoofGenerator`'s output deck instead of assuming a flat slab.

⚠ **`RoofStyle` on `ApartmentRow` is an ordinal menu with `Flat`=0 and
`Peaked`=1, and menus in this project are APPEND-ONLY.** Any new roof forms go
on the *end* — `Flat`=0, `Peaked`=1, `Hip`=2, … — and `Peaked` must keep meaning
whatever it means today. Do not "tidy" it into alphabetical order; every saved
scene stores the integer.

### 4.4 Catalog CSV versus parameter — the dividing line

The rule that keeps this honest: **the catalog holds what is a FACT about a
named roof type; a parameter holds what the user is choosing about this
building.** Same split that makes `SignLibrary` and the WM moulding catalog work.

**`config/roof_typology.csv`** — one row per named form. Facts, each with a
source:

```
name, family, section_grammar, edge_weight_rule, pitch_default, pitch_min,
pitch_max, footprint_derivable, extra_inputs, covering_default,
covering_min_slope, covering_source, period, region, confidence
```

Example rows (values as established above; `covering_min_slope` and its source
come straight from §2.4):

```
Gable,        skeleton, "slope($pitch)",                    "ends=0",  6, 3, 12, yes+bits, "gable_edges",      AsphaltShingle, 2.0,  "IRC 2021 R905.2.2",  Universal,   US,        measured
Hip,          skeleton, "slope($pitch)",                    "all=1",   5, 3,  9, yes,      "",                 AsphaltShingle, 2.0,  "IRC 2021 R905.2.2",  Georgian+,   US,        measured
Gambrel,      skeleton, "slope(28.97,to_rise=.70711R) slope(4.97)", "ends=0", -, -, -, yes, "",               WoodShingle,    3.0,  "IRC 2021 R905.7.2",  DutchColonial, US-NE,   derived
Mansard,      skeleton, "slope($lower,to_rise=$h) slope($upper)",   "all=1",  -, -, -, no,  "break_h,upper_pitch", Slate,       4.0,  "IRC 2021 R905.6.2",  SecondEmpire, US+FR,   measured
FlatParapet,  skeleton, "wall($parapet) flat()",            "all=0",   0.25, 0.25, 2, no,  "parapet_h",        SinglePlyTPO,   0.25, "IRC 2021 R905.13.1", C19-present, urban US, measured
Sawtooth,     sweep,    "slope(8) wall($glazing_h)",        "-",       8, 6, 12, no,       "axis,period",      MetalPanel,     3.0,  "IRC 2021 R905.10.2", 1827-1940,   industrial, trade
```

Note `covering_min_slope` **clamps** `pitch_min`. A `Slate` row cannot go below
4:12 without violating R905.6.2, and the HDA should refuse rather than warn —
that is a dimension coming from a standard, which is exactly what TYPOLOGY means
in this project.

**Parameters on the HDA** — the choices:

- `Pitch` (clamped to `[max(pitch_min, covering_min_slope), pitch_max]`)
- `Overhang` (eave), `RakeOverhang`
- `EdgeGableMask` — per-edge, from a group or a primitive attribute
- The named extra inputs for the row (`break_h`, `parapet_h`, `axis`, `period`,
  `ridge_offset`) — **shown only when the row declares them**, so the interface
  is honest about §1.9
- `MatchRidgeHeights` toggle — the §1.7 button: solve per-wing pitch so ridges
  meet
- `MaterialStyle` (`Principled | Unreal | USD` — the canonical contract)
- `Seed`

**A second catalog, `config/roof_covering.csv`**, holds §2.4 verbatim: material,
IRC section, minimum slope, underlayment threshold. It is 16 rows and it is
citable, which makes it exactly the sort of thing that backs the claim "based on
accepted standards."

### 4.5 The three axes

| Axis | For roofs | What it may touch |
|---|---|---|
| **TYPOLOGY** — what it IS; drives dimensions from standards | Which catalog row. Sets the section grammar, the edge-weight rule, the pitch window (clamped by the covering's code minimum), whether a ridge board or a ridge **beam** (< 3:12, R802.4.4), whether ties are in the lower or upper third, whether the attic can be habitable (7 ft rule). | **Dimensions.** Only. |
| **STYLE** — how it is ARTICULATED | Everything in OP 4: fascia and cornice profile, rake board, ridge cresting, finials, snow guards, gutter profile, parapet coping, covering pattern and unit size, dormer *articulation*. Gothic = steep-looking trim, foliate cresting; Art Deco = stepped coping, chevron parapet; Brutalist = no trim at all, exposed slab edge. | **Ornament and subdivision.** Never dimensions. |
| **VARIATION** — its CONDITION | Ridge sag, plane deflection between rafters, slipped and missing shingles, patched planes, one slope re-covered in a different material, moss and staining on the north face, rust streaks below flashing, tarps, deferred-maintenance ponding on the flat. | Displacement, material assignment, small removals. |

**Three specific traps:**

1. **Mansard and gambrel are TYPOLOGY, not STYLE.** §2.2. If a "style" menu ever
   contains "Mansard", the axes have collapsed and the invariance test will fail.
2. **Pitch is TYPOLOGY, not STYLE.** "Gothic roofs are steep" is true, but the
   steepness must arrive as a *typology row* (`GothicSteepGable`, pitch window
   12:12–20:12) not as a style multiplier — otherwise style changes dimensions.
3. **VARIATION deliberately breaks planarity**, so it must run *after* the
   verification tests in §4.6, never before. Order matters and should be
   enforced by the network, not by a comment.

### 4.6 The mechanical verification test

Not inspection. Measurement. Seven tests, in the order they should run, all
runnable headless like `parity_test_extrusions.py` already is.

**V1 — Area parity (the primary test).**
```
    Σ_faces  area(face) · cos(θ_face)   ==   area(footprint)
```
Tolerance 1e-6 relative. For uniform pitch it degenerates to
`A_roof · cos θ == A_footprint`, verified at residual 0 for the §1.7 L
**[derived]**. This one test catches: non-planar faces, missing faces, duplicated
faces, faces at the wrong slope, and a skeleton that failed to close. It costs
nothing and it is the strongest single check available.

**V2 — Watertightness and Euler.** Every roof edge is used exactly twice except
eave edges, which are used once. Face count == input edge count for a
single-band skeleton (one face per edge, always). Any deviation is an event
handled wrongly.

**V3 — Drainage.** Drop a marble from each face centroid and from each face's
lowest interior point; every path must reach an eave. Equivalently: no interior
local minimum, and every valley terminates at an eave. This is the property
CGAL states the construction guarantees, so **failing V3 means the
implementation is wrong, not the roof** — which makes it a very sharp test.

**V4 — Height/skeleton parity under weighting.** Reconstruct each skeleton node's
height two independent ways: from `edgedist · tan θ_face`, and from an explicit
`polyexpand2d` run at `Divisions = N` reading the offset parameter. They must
agree. This is the test that answers the §4.2 open question about `edgedist`
semantics, so **it should be written first, before the HDA.**

**V5 — Determinism under degeneracy.** Cook the rectilinear-L test case (§1.4)
100 times, in both Houdini's threaded and single-threaded modes, and hash the
output topology. All 100 hashes must match. Then perturb the footprint by ±1e-4
in each direction and confirm the topology does *not* flip. Because §1.4 proves
the tie is structural for rectilinear plans, **this test is not optional.**

**V6 — Style invariance (the project's standing test).** For every STYLE value:
bounding box identical to 1e-9; face-slope histogram identical; skeleton node
positions identical. Only trim geometry and material assignment may differ.
This is the test that keeps the three axes honest, and it is the one that will
catch someone adding "Mansard" to a style menu.

**V7 — Menu append-only.** Diff the menu token order in every roof HDA against
the previous release; fail on any reorder or removal. The project has already
been bitten by ordinal menus; automate the guard.

**Regression corpus.** Nine footprints, fixed: square; rectangle; L; T; U;
cruciform; a convex polygon with a 135° corner (exercises the non-square backing
bevel, §1.8); a footprint with a hole (courtyard block, §1.4); and a footprint
with a deliberate 1 mm vestigial edge (cleanup test). Store as a `.geo` and hash
the outputs.

### 4.7 Suggested order of work

1. Write the pure-Python straight-skeleton reference (no Houdini) and get V1–V3
   passing on the nine-footprint corpus. Mirrors how `moulding_grammar.py` was
   built and validated before it touched an HDA.
2. Answer the two `polyexpand2d` questions in §4.2 with V4.
3. Build `AB::RoofSkeleton::1.0` — uniform pitch only, `slope()` bands only.
4. Add per-edge weights; re-run V1 in its summed form; add V5.
5. Add multi-band sections; gambrel/mansard/jerkinhead/gablet fall out.
6. Reuse the moulding sweeper for `AB::RoofTrim`; add V6.
7. `RoofSweep` and `DormerMaker` last — they are additive and do not disturb the
   core.

### 4.8 Turning §3 into data: a third catalog

The code research produces something better than colour: **three cities that
disagree in ways a generator can implement in a few dozen numbers.** That
belongs in `config/roof_region.csv`, one row per (city, district-family), and it
is the cheapest authenticity available anywhere in this system.

```
region, district_family, height_datum, pitch_rule, pitch_bonus_ft,
pitch_threshold, parapet_min_ft, parapet_max_ft, rooftop_area_cap,
rooftop_obj_height_ft, rooftop_setback_ft, dormer_rule, source, confidence
```

Filled from §3 [all cited unless marked]:

| region | pitch rule | parapet | rooftop objects | dormers |
|---|---|---|---|---|
| **NYC low-density** (ZR 23-421) | **Envelope**: walls to 25 ft, planes to a 35 ft ridge, ≤ 80°. Pitch is a *consequence of plan depth*: `atan(10/(D/2))` **[derived]** | 3 ft 6 in – 4 ft (BC 1510.8 ∧ ZR 23-411(f)) | bulkheads/tanks ≥ 10 ft from street wall; 50 % @ 15 ft or 30 % @ 25 ft | **50 %** of street-wall width, detached/semi-detached 1–2 family (ZR 23-412) |
| **NYC contextual** (ZR 23-43x) | Flat; max base + max building height from the 23-432 table | same 6-inch window | 30 % @ 35 ft (≤ 120 ft bldg) or 55 ft (> 120 ft) | **60 % decaying 1 %/ft**, *or* **40 % fixed** (ZR 23-413) |
| **NYC sky-exposure** (opt-in, ZR 23-73 / 33-432) | Flat; stepped envelope, initial setback 20/15 ft, slope **2.7:1 narrow / 5.6:1 wide** (alt. 3.7 / 7.6) | same | same | same |
| **SF residential** (§ 260, RDG) | Measured to **midrise** → bonus = **½ the rise, uncapped**; *no* threshold; roofline must match neighbours (RDG p. 30) | ≤ 4 ft, **exempt and free**; RDG pushes to delete it | **30 % of roof area → 40 % if screened**; 20 % in the front 10 ft; objects in the top **16 ft** (limit ≤ 65) / 20 ft | **≤ 20 % of roof area; each ≤ 8 × 8 ft; ≥ 3 ft from side, ≥ 10 ft from front wall, ≥ 3 ft apart; top ≤ min(ridge, limit + 10 ft)** (ZAB 4) |
| **SF Chinatown** (§ 263.6) | as above | **+ 8 ft decorative parapet or corner pavilion ≤ 150 ft²** | as above | as above |
| **LA flatland R1** (§ 12.21.1) | **Step at 25 % slope**: 33 ft if ≥ 25 %, 28 ft if < 25 % | **counted in height** (§ 12.03) — costs 1 ft per ft | **5 ft** + 5 ft setback; stair/elevator +10 ft (30/45 ft limits) or +20 ft (75 ft); **no area cap** | no code rule found |
| **LA hillside** (BHO) | same 25 % step, **per portion**; plumb-line envelope at every section; 20 ft / 45° encroachment plane | counted | 5 ft + 5 ft setback; **stair ≤ 36 ft² needs no setback**; skylight > 33⅓ % of roof ≤ 30 in | — |
| **LA Chapter 1A** (2025) | **No roof-form rule at all** — zero hits for pitch/slope/gable/dormer in 98 pp | safety barriers 6 ft, no setback | mechanical 3/5/10 ft by building height; vertical circulation 10/20/20 ft, **no setback** | — |

**Three uses for this table, in order of value:**

1. **A pitch *distribution*, not a pitch value.** §3.4 shows the three cities
   produce three different distributions from one line of policy each: SF broad
   and skewed steep; **LA a spike at exactly 3:12**; NYC low-density determined by
   plan depth. Sampling a `region` row is a far better source of variety than a
   random pitch, and it is defensible.
2. **A rooftop-prop rule for `AB::RooftopProcessor`.** It currently scatters with
   no constraint at all. Feeding it `rooftop_area_cap`, `rooftop_obj_height_ft`
   and `rooftop_setback_ft` per region makes an SF roof read as SF (few, small,
   screened, back from the front 10 ft) and an LA roof read as LA (many, all
   about five feet, five feet in from the edge) — at the cost of three columns.
3. **A dormer placement rule.** SF's ZAB 4 is a complete, implementable
   scatter specification. NYC's 23-413 is a width *budget* with a decay term.
   They produce visibly different dormer bands and neither needs invention.

⚠ **All three are TYPOLOGY, not STYLE** — they set dimensions. A `region` column
must never appear in a style menu.

---

## 5. What this approach cannot do — an honest list

1. **Real roofs are frequently not straight skeletons.** Ren et al. built a
   2,539-roof mesh-image dataset specifically because the straight skeleton is
   "more limited in expressiveness" than what real roofs require, and replaced
   it with an optimised roof *graph* [cited]. A skeleton-only tool will produce
   a plausible roof for most footprints and the *wrong* roof for a substantial
   minority.
2. **Buildings accrete; skeletons do not.** A real roof records additions,
   raisings and re-coverings — different pitches, different eave heights,
   different materials meeting at awkward flashings. The skeleton produces a
   roof designed all at once. Fixing this needs the *massing* decomposed into
   dated parts before the roof operator ever runs, which is a building-generator
   problem, not a roof problem.
3. **The perimeter is silent about the interior.** Anything whose form is driven
   by the volume below — churches, halls, atria, double-height spaces, stair and
   lift cores — cannot come out of a footprint. Dormers are the everyday case:
   they follow rooms.
4. **Framing ≠ surface.** §1.8. A truss roof and a cut roof have identical
   outsides. If the underside is ever seen — a barn, a mill, a ruin, a
   destruction asset — the skeleton is not a framing plan and a hip set in
   trusses does not even contain a hip rafter.
5. **The topology can pop.** Under weighting, changing one edge's pitch can
   reorder events and change which arcs exist (§1.6). A pitch slider is not
   continuous in the output. This must be visible in the UI.
6. **Rectilinear plans are the degenerate case, not the general one** (§1.4).
   The most common footprints in a city are precisely the ones with tied events.
   Any claim of robustness that has not run V5 is unfounded.
7. **Curved forms are approximations.** A barrel vault as a fine band-stack is
   fine. A true dome on a non-circular footprint is *not* a banded offset object,
   and neither is a groin vault, a sail vault, or a hyperbolic paraboloid.
8. **Zoning massing is not a roof problem.** The setback envelopes of §3 shape
   the *building*, and the roof should consume a supplied envelope rather than
   compute one. Conflating them will produce a roof tool that quietly becomes a
   zoning tool and is wrong at both.
9. **Holes are under-specified.** Courtyard footprints give skeleton faces that
   are not weakly simple [cited]. They will need explicit handling and a test
   case, and I have not designed that handling.
10. **I could not verify the ASCE 7 primary text**, the IRC habitable-attic
    wording, or the IBC low-slope section attribution. Those three are flagged
    in place and should be read from the actual documents before they drive
    geometry.
11. **The zoning findings have a short shelf life, and it is shorter than it
    looks.** NYC renumbered all of Article II Chapter 3 on **2024-12-05** and
    demoted the sky exposure plane; LA began replacing its entire zoning code
    with Chapter 1A on **2025-01-20**; SF repealed ZA Bulletin 3 in **March
    2026**; SF added Table 260-2 by ordinance effective **2026-01-12**. All four
    of those post-date most published references and two of them post-date the
    last year. **Any `roof_region.csv` built from §3 needs a `source_checked`
    date column and an annual re-read**, and every row should carry the section
    number so a re-check is mechanical rather than archaeological.
12. **A code's *intent* is not recoverable from its numbers, and the tool will
    fake it badly.** SF's rooftop rules are written to compose a silhouette; LA's
    are written to bound a dimension. A generator that satisfies both numerically
    will still produce an LA-looking roof in San Francisco, because what SF is
    actually enforcing — through mandatory design review under Planning Code
    § 311(c)(1) — is a judgement, not a measurement. The `region` column buys
    real variety; it does not buy design review.

---

## 6. Sources

**Geometry**

- CGAL 6.2 User Manual, *2D Straight Skeleton and Polygon Offsetting*.
  https://doc.cgal.org/latest/Straight_skeleton_2/index.html — accessed
  2026-08-15. Source of the wavefront definition, the reflex-vertex statement,
  the medial-axis distinction, the weighted-skeleton definition, the roof/
  drainage property, and the polygon-with-holes caveat.
- O. Aichholzer, D. Alberts, F. Aurenhammer, B. Gärtner (1995), *A novel type of
  skeleton for polygons* — the origin of the construction and of its roof
  application; and the `O(n² log n)` / `O(n²)` complexity statement. Accessed
  via secondary summaries 2026-08-15; **primary text not fetched
  [UNVERIFIED wording]**.
- S. Held, P. Palfrader, *Straight Skeletons with Additive and Multiplicative
  Weights and Their Application to the Algorithmic Generation of Roofs and
  Terrains*, Computer-Aided Design 92 (2017) 33–41, DOI
  10.1016/j.cad.2017.07.003.
  https://www.palfrader.org/research/2017/ — PDF fetched but not text-extractable
  2026-08-15; cited for the existence of additive and multiplicative weighted
  variants applied to roofs. **Body text [UNVERIFIED].**
- J. Ren, B. Zhang, B. Wu, J. Huang, L. Fan, M. Ovsjanikov, P. Wonka,
  *Intuitive and Efficient Roof Modeling for Reconstruction and Synthesis*,
  arXiv:2109.07683 (2021). https://arxiv.org/abs/2109.07683 — accessed
  2026-08-15. Abstract fetched; source of the "more powerful and expressive than
  specialized tools such as the straight skeleton" limitation and the
  2,539-roof dataset figure.

**Model codes**

- IRC 2021, Chapter 8, *Roof-Ceiling Construction* — R802.3, R802.4.1 and Table
  R802.4.1(9), R802.4.4, R802.4.5, R802.4.6, R802.5.2/R802.5.2.2, R802.7.
  https://up.codes/viewer/maryland/irc-2021/chapter/8/roof-ceiling-construction
  — accessed 2026-08-15. (Maryland's adoption of the 2021 IRC; the cited
  sections are the model text.)
- IRC 2021, Chapter 9, *Roof Assemblies* — R905.2.2 through R905.15.1.
  https://up.codes/viewer/maryland/irc-2021/chapter/9/roof-assemblies —
  accessed 2026-08-15.
- IRC R202 (habitable attic), R305 (ceiling height), R807 (attic access) —
  figures corroborated across https://up.codes/s/habitable-attics and
  https://www.jaspector.com/codes/irc-2021/ — accessed 2026-08-15.
  **Wording [UNVERIFIED]; numbers corroborated.**
- IBC 2021, low-slope minimum design slope and *positive drainage* definition —
  via IIBEC, *Secondary Drainage and Ponding Requirements in the IBC and IEBC*,
  https://iibec.org/secondary-drainage-ponding-requirements-ibc-iebc/ — accessed
  2026-08-15. **Section attribution [UNVERIFIED].**
- ASCE/SEI 7-22, §7.3 flat-roof snow, §7.4 slope factor `C_s` (Fig. 7.4-1),
  §7.6.1 unbalanced snow for hip and gable roofs.
  https://amplify.asce.org/content/standard/9780784415788/part/provisions/standard-chapter/s7
  — **paywalled; primary text NOT fetched.** The 7:12 / ½:12 window is
  corroborated by multiple secondary sources; the degree conversions (30.256°,
  2.386°) are **[derived]**.

**New York City** — all accessed 2026-08-15

- NYC Zoning Resolution, https://zr.planning.nyc.gov — ZR 12-10 (definitions);
  **23-411 / 23-412 / 23-413** (permitted obstructions and the two dormer
  allowances); **23-42 / 23-421 / 23-422 / 23-424** (low-density height and the
  pitched-roof envelope); **23-43 / 23-431 / 23-432 / 23-433 / 23-434 / 23-435 /
  23-436 / 23-441** (contextual envelope and towers); **23-73 / 23-731 / 23-736 /
  23-738** (the opt-in sky exposure plane and the sliver rule); **33-43 / 33-431 /
  33-432 / 33-442 / 33-451** (commercial); 64-11 (flood reference plane). All
  "Last Amended 12/5/2024" unless noted. **ZR 33-42 not retrieved.**
- City of Yes for Housing Opportunity, N 240290 ZRY, adopted 2024-12-05,
  https://zr.planning.nyc.gov/recently-adopted/city-yes-housing-opportunity-n-240290-zry
- NYC Building Code (2022 NYC Construction Codes) — **BC 504.3** (rooftop
  structures excluded from height, 33⅓ %); **BC 1011.12** (stair to roof, 20°
  waiver); **BC 1504.9** (cool roof, 0.7 reflectance); **BC 1510.2** (bulkheads);
  **BC 1510.8** (42 in parapet); **BC 1512.2** (100 % sustainable roofing zone).
  Via https://up.codes/viewer/new_york_city/nyc-building-code-2022/chapter/15/roof-assemblies-and-rooftop-structures
  — **secondary publisher; amlegal and nyc.gov return HTTP 403.**

**San Francisco** — American Legal "2026 S-96 (current)", accessed 2026-08-15

- SF Planning Code **§ 252** (height and bulk district classes),
  **§ 260** (height limits: measurement, and the (b) exemption lists),
  **§ 261** (RH districts, 45° front-yard plane), **§ 261.1** (narrow streets,
  1.25× rule, sun access plane), **§ 263 / 263.6 / 263.20** (special exceptions,
  Chinatown parapets), **§ 270 / Table 270** (bulk).
  https://codelibrary.amlegal.com/codes/san_francisco/latest/sf_planning/
- Zoning Administrator interpretation, *Code Section 260(a)(2), Measurement of
  pitched roof*, eff. 6/96, rev. 3/21.
  https://codelibrary.amlegal.com/codes/san_francisco/latest/sf_planning/0-0-0-32341
- SF Planning Department, *Residential Design Guidelines*, adopted 2003-12-04
  (⚠ landing-page metadata says 2013).
  http://default.sfplanning.org/publications_reports/residential_design_guidelines.pdf
- ZA Bulletin 4, *Public Notification of Building Permits*, issued Oct 2002,
  revised March 2026 (dormer rule, § 311(b)(4)).
  https://sfplanning.org/resource/zoning-administrator-bulletin-4-public-notification-building-permits-residential-and
- ZA Bulletin 3, *Dormer Windows* — **REPEALED March 2026.**
  https://sfplanning.org/resource/zoning-administrator-bulletin-3-dormer-windows

**Los Angeles** — American Legal "2026 Rev. 8 (current)", accessed 2026-08-15

- LAMC **§ 12.03** (Height of Building or Structure; Grade; Slope),
  **§ 12.21.1** (height limits, the 25 % slope rule, B.3 roof structures,
  B.2 the 12 ft slope bonus), **§ 12.21 C.10** (Baseline Hillside Ordinance —
  Table 12.21 C.10-4 heights, Table 12.21 C.10-5 projecting roof structures,
  (d)(1)(i) envelope height, (d)(1)(ii) encroachment plane).
  https://codelibrary.amlegal.com/codes/los_angeles/latest/lamc/
- LAMC **Chapter 1A, Article 2 (Form)**, Ord. 188,418 eff. 2025-01-20 —
  Sec. 2C.4.2.D.1 measurement, Sec. 2C.4.2.E allowed vertical encroachments.
  https://zoning.lacity.gov/sites/default/files/zcode_download/article_2.pdf
- LADBS **IB/P/ZC 2023-008**, *Determination of the Zoning "Height of a Building
  or Structure"*, eff. 2023-01-01.
  https://dbs.lacity.gov/sites/default/files/efs/pdf/publications/zoning/determination-of-the-zoning-height-of-a-building-or-structure-ib-p-zc2002-008.pdf
- LADBS *Baseline Hillside Ordinance Correction Sheet*, PC/STR/Corr.Lst.107A
  rev. 2017-04-06.
- LA City Planning **CP-4061**, *Hillside Area Development Standards —
  Single Family Zone*, 2020-02-14.

⚠ `codelibrary.amlegal.com` and `planning.lacity.gov` return **HTTP 403** to an
ordinary fetch; the SF and LA text above was retrieved with `curl` and a browser
user-agent.

**Typology and history**

- NPS Preservation Brief 4, *Roofing for Historic Buildings*, Sarah M. Sweetser.
  https://npshistory.com/publications/preservation/briefs/4.pdf — accessed
  2026-08-15 (search-result summary only; PDF not text-extracted).
- District of Columbia Historic Preservation Guidelines, *Roofs on Historic
  Buildings*.
  https://planning.dc.gov/sites/default/files/dc/sites/op/publication/attachments/DC%20Roof%20Guidelines.pdf
  — **fetched but not text-extractable 2026-08-15.**
- Vermont Division for Historic Preservation architectural survey form — roof
  taxonomy (Gable, Hip, Shed, Flat, Mansard, Gambrel, Jerkinhead, Saw Tooth,
  With Monitor, With Bellcast, With Parapet, With False Front). Cited as
  evidence that the survey vocabulary is small and enumerable. **[trade]**
- Terminology of "Dutch gable" — https://en.wikipedia.org/wiki/Dutch_gable and
  https://en.wikipedia.org/wiki/Gablet — accessed 2026-08-15. **[trade, but the
  ambiguity itself is well attested.]**
- Sawtooth / north-light origin (W. Fairbairn, 1827) and north-facing glazing —
  trade and encyclopaedic sources, accessed 2026-08-15. **[trade]**
- Truss span ranges — vendor and trade pages only. **[trade — not for a spec.]**

**Houdini**

- SideFX, *Poly Expand 2D geometry node*.
  https://www.sidefx.com/docs/houdini/nodes/sop/polyexpand2d.html — accessed
  2026-08-15. Straight-skeleton statement, Inside/Outside Scale local
  attributes, Edge Distance and Edge Speed attributes, Divisions, tolerances.
- SideFX, *Labs Straight Skeleton 3D geometry node*.
  https://www.sidefx.com/docs/houdini/nodes/sop/labs--straight_skeleton_3d.html
  — accessed 2026-08-15. Cited for the medial-axis conflation warning in §1.5.

**AssetBash internal (read 2026-08-15)**

- `U:/AB_Standardization/analysis/tools.csv`, `parms.csv`, `menus.csv` — the
  measurement behind §4.3's claim that no roof-form generator exists.
- `U:/AB_Standardization/moulding/moulding_grammar.py` and
  `moulding_catalog.csv` — the grammar precedent §4.1 builds on.
- `U:/AB_Standardization/schema_draft/typologies_mutcd_sign_installation.json` —
  the confidence-marking and `binds_to` conventions followed here.
