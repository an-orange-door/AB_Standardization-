# Building Plans — the regularities, the architects who break them, and what is computable

Research for the AssetBash architectural simulator, 2026-08-16.
Companion to `roof_typology_and_math.md` (roofs) and `footprint_plan.md` (the
`BuildingFootprintGenerator` rewrite). Those two are about the *outline* and the
*lid*. This one is about what happens between them.

---

## Summary — the argument in one page

**There is a small generative vocabulary for the plan, but it is not one
vocabulary — it is three, and they compose in a fixed order.** That is the
central finding, and it is why previous attempts to write "a floor plan
generator" produce mush.

```
  1. GRID       a lattice, usually rectangular and usually irregular
                (a 'tartan' — alternating structural and infill bands)
  2. CORE       a placed, sized, occupancy-driven blob of servant space
  3. PARTITION  a subdivision of what remains, subject to an adjacency graph
```

Each layer constrains the next and **never the reverse**. The grid is set by
economics below the building (parking, spans, formwork repetition). The core is
sized by the population it serves and placed by daylight and site. Only then is
there a residual to subdivide.

The four things worth internalising:

1. **The grid is usually not designed, it is inherited.** In any building with
   structured parking, the parking module sets the column grid and everything
   above lives with it. The parking module is itself derived from a car:
   `module = stall_depth + aisle + stall_depth`, and the along-bay column spacing
   is `n × stall_width`. That is a two-parameter derivation of the single most
   visible regularity in a city.
2. **The plan is governed by one number more than any other: the depth from
   core face to glass.** Everything — daylight, lettable value, ventilation,
   the decision to taper the tower — is downstream of it. And it is *measurable
   on generated geometry*, which makes it a scoring function, not just a
   parameter (§2.2, §4.3).
3. **Egress is the topology.** The double-loaded corridor is not a design
   choice, it is the shape that falls out of "two remote exits + a travel
   distance limit + a dead-end limit." Encode the three constraints and the
   corridor appears without being modelled (§2.5).
4. **The signature architects are not exceptions to this — they are
   *substitutions* into it.** Every one of the four studied replaces exactly
   one of the three layers and leaves the other two intact. MAD replaces the
   grid's *transform* and keeps the core rigid. OMA replaces the partition
   *order* with a programme sequence and keeps the grid. Corbusier's free plan
   formally *decouples* layers 1 and 3. Morphosis superimposes two instances of
   layer 1. This is what makes them computable rather than merely stylish
   (§5).

The most useful computational finding is in §4.4: **space syntax integration
can be used as a reward signal, not just an analysis**, and there is now a 2026
paper that does exactly that with a fully specified, reproducible formula. That
converts "does this plan make sense" from an opinion into a number this project
can put in a parity test.

The honest limit is in §8: **nothing in the literature generates a plan for a
building type it has not been shown.** Not shape grammars, not the learned
models. Every working system is a *style transcription*, not a design engine.
That is not a reason to avoid the work; it is a reason to build the catalog
first and the generator second — the same order this project already used for
mouldings, signs and metal sections.

---

## 0. How to read the confidence marks

Same scheme as `roof_typology_and_math.md`, with one addition, because a lot of
architectural "knowledge" only exists in trade press.

| Mark | Meaning |
|---|---|
| **[derived]** | Follows from geometry or arithmetic given in the text. Self-checking. |
| **[cited]** | Read from a source I fetched and read myself. URL in §10. |
| **[snippet]** | ⚠ **NEW MARK.** Appeared in a search-engine summary of a source I could **not** fetch (403/404). Second-hand. Better than recall, worse than [cited]. Do not put in a spec without checking. |
| **[trade]** | From a vendor/consultant/blog page. Directionally right, not authoritative. |
| **[UNVERIFIED]** | Recalled, not read. A placeholder that must be checked before it drives geometry. |

Units: imperial where the standard is imperial (US parking, US codes, US lease
practice), metric where the standard is metric (UK/EU structural tables).
AssetBash data stays metric per the existing convention.

⚠ **A note on the sources for §2.3 and §2.4.** The CTBUH papers that hold the
best core-position and efficiency statistics are behind 404s and 403s for
automated fetching. Several headline numbers in those sections are therefore
**[snippet]**, and I have flagged each one individually rather than smoothing
them into the prose. §9 lists them for a USC pull.

---

## 1. The plan taxonomy

Three organising logics, not three building sizes. A four-storey office over
retail is *commercial* logic; a four-storey walk-up is *residential* logic; they
can be the same height and the same footprint and share nothing.

### 1.1 The taxonomy

| Type | The organising element | What sets the grid | What sets the depth | Partition rule |
|---|---|---|---|---|
| **HOUSE** (detached, 1–3 storeys) | the **circulation figure** (hall, stair, or nothing) | the structural span of a joist/rafter; nothing else | the site and the roof | adjacency graph, served/servant, wet-wall grouping |
| **BAR / ROW** (rowhouse, walk-up, double-loaded slab) | the **corridor** | party wall rhythm = unit width | `2 × unit_depth + corridor` | unit type repeated; partitions inside a unit only |
| **COMMERCIAL PLATE** (office, low/mid-rise) | the **core** | parking below, or 30 ft spec bay | lease span from core face to glass | *no partitions* — the plan is deliberately empty |
| **TOWER** | the **core + the taper** | as commercial, plus lateral system | as commercial, but varies by floor | as commercial |
| **BIG** (Koolhaas's term, §5.2) | the **section** | irrelevant — programme dominates | irrelevant | the plan is a residue of the stacking |

The critical distinction for a procedural system, and the one that decides the
whole architecture of the tool:

> **In a house, the plan is the design. In a commercial plate, the plan is
> deliberately not designed — the value of the product is that it is empty.**

An office floor plate that arrives full of authored rooms is *wrong*. What the
generator must produce for a commercial plate is: a core, a structural grid, a
perimeter, and nothing else. Tenant fit-out is a separate, later, optional
layer. This is a large simplification and it should be exploited: **the two
hardest cases (office, tower) need the least partition logic.**

### 1.2 The residential type set, as a small vocabulary

Residential is where a long enumeration is tempting and unnecessary. The
generative set is:

```
  unit  = (bedroom_count, aspect, exposure_count, has_corridor_frontage)
  block = (access_type, units_per_landing, corridor_type)

  access_type ∈ { direct | stair-only (point access) | single-loaded |
                  double-loaded | gallery/deck }
```

Five access types × a unit vocabulary generates essentially all multifamily
housing plans. The access type is *not* a style choice — it is determined by
the egress rules in §2.5 plus climate. That is the whole point: it derives.

---

## 2. The regularities, as numbers

### 2.1 The grid — and why parking sets it

**The rule.** In any building with structured parking beneath it, the column
grid of the parking sets the column grid of everything above, because
transferring columns costs a transfer beam or slab and transfer structure is
expensive and deep enough to eat a storey.

**Where the parking module comes from.** Two numbers and one arithmetic:

```
  double_loaded_module = stall_depth + aisle_width + stall_depth
  along_bay_spacing    = n_stalls × stall_width
```

Measured values:

| Quantity | Value | Mark |
|---|---|---|
| 90° stall, US typical | 9 ft × 18 ft (8'-6" also common) | [snippet] |
| Two-way drive aisle, 90° parking | 24 ft | [snippet] |
| ⇒ double-loaded module | 18 + 24 + 18 = **60 ft** | [derived] |
| 90° double-loaded module, quoted range | 60–64 ft | [snippet] |
| Precast garage column bay spacings | **36, 45, 48 ft** | [cited] |
| Precast double-tee widths | **12 and 15 ft** | [cited] |
| Post-tensioned garage column bay | **24 ft** | [cited] |
| Structural depth, precast or PT garage | **≈ 3 ft** | [cited] |
| Filigree system: span limit / intermediate column | 44 ft with a column at 16 ft, for a 60 ft module | [cited] |
| Along-bay column spacing | "a function of the number of parking spaces between, **such as 20 or 28 feet**" | [cited] |
| PT one-way slab garage grid, common | 60 ft × 18 ft | [snippet] |
| ⇒ tower grid above should use **9 ft increments** to land on the garage grid | | [snippet] |

⚠ The last two are **[snippet]** from an engineering forum via a search summary
and I could not open the thread. The *principle* — that the grid above is
dimensioned in whole multiples of the garage's sub-module — is sound and is
independently supported by the [cited] "function of the number of parking
spaces between" statement. The specific 60×18 and 9 ft figures need checking.

**The generative consequence.** A single `stall_width` parameter propagates all
the way to the façade module of a 40-storey tower:

```
  stall_width = 9 ft
  bay         = 3 × 9 = 27 ft            (three cars between columns)
  or            5 × 9 = 45 ft            (long-span, matches the precast 45)
  facade_module divides bay:  27 / 5 = 5.4 ft,  27 / 6 = 4.5 ft
  45 / 5 = 9.0 ft,  45 / 6 = 7.5 ft,  45 / 9 = 5.0 ft
```

This is the AssetBash-shaped answer: **not a table of bay spacings, a
derivation from one dimension.** `ModuleWidth` in
`BuildingFootprintGenerator` (currently a bare `10.0`) is the hook.

**What is rule vs preference here:**
- **RULE:** transfer structure is expensive; grids align. Universal.
- **RULE:** the parking module is `2 × depth + aisle`. Geometric.
- **PREFERENCE:** 27 ft vs 30 ft vs 45 ft. Regional, era-dependent, and a
  function of the framing material. This belongs in a catalog CSV, not a
  parameter default.

### 2.2 Lease span — the one number that governs a commercial plate

**Definition.** The clear distance from the face of the core to the inside face
of the glass. Everything about a commercial floor plate follows from it.

The published rules of thumb, all of which are really the same rule seen from
different sides:

| Rule | Value | Source basis | Mark |
|---|---|---|---|
| Effective daylight from one side, at 9'–12' ceilings | **not beyond 25 ft** | Daylighting Pattern Guide, Pattern 3 | [cited] |
| Daylight washes the back wall when depth ≤ | **2.5 × window head height** | same | [cited] |
| German workplace custom: no workstation further than | **8 m (24 ft)** from a window | Daylighting Pattern Guide, Pattern 1 | [cited] |
| Perimeter task-daylight zone / ambient zone | **4.5 m (15 ft)** each, so 9 m (30 ft) total | 2030 Palette | [snippet] |
| Spec-office minimum "leased span" | **40 ft** | Daylighting Pattern Guide, Pattern 3 | [cited] |
| Suburban office lease depth, standard range | 40–50 ft | CRE glossary | [trade] |
| Above this, interior space struggles to lease | > 50 ft | CRE trade | [trade] |

⭐ **The two numbers disagree, and the disagreement is the whole subject.**
Daylight says 25 ft. The pro forma says 40 ft minimum. The gap between them is
the entire history of the twentieth-century office building. The generator
should expose it as a single explicit axis:

```
  lease_span ∈ [25, 45] ft     25 = daylight-optimal, pre-WWII / European
                               35 = post-2000 sustainable US
                               40 = US speculative minimum
                               45+ = deep-plate, air-conditioned, 1960s–90s
```

⭐⭐ **The best find in this whole section, and it is a scoring function, not a
parameter.** The Daylighting Pattern Guide characterises real buildings by
**maximum distance to perimeter** and **percentage of floor area within 20 ft of
a window**. All [cited]:

| Building | Max distance to perimeter | % of area within 20 ft of a window |
|---|---|---|
| Marshall Field Wholesale Store | 23 ft | 96% |
| Terry Thomas Building | 19 ft | 100% |
| General Motors Office Building | 32 ft | 90% |
| Alliance Kai | 42 ft | 91% |
| Seagram Building | 56 ft | 65% |
| Aon Center Tower | 92'-6" | 39% |

This is directly computable on generated geometry — a per-point distance
transform from the glazed perimeter, integrated over the floor plate. **It gives
the project an era classifier and a plausibility gate in one number.** A
generated "1920s office building" whose plate scores 39% is wrong and the test
says so. See §7 for the implementation.

Note Alliance Kai at 42 ft / 91%: a *deep* plate that still daylights well,
because the depth is measured to a courtyard as well as to the street. Depth
alone is not the metric; **distance to the nearest glass** is. A courtyard is
the operator that decouples them.

### 2.3 The core — position, size, contents

**What is in it (rule, and the list is short):**

```
  CORE = elevators + elevator lobby
       + exit stairs (≥2, see §2.5)
       + toilets
       + electrical/telecom risers
       + mechanical shafts
       + janitor / service
```

**Position — the taxonomy.** Four positions, and each does something specific
to the plan:

| Position | Effect on plan | Effect on massing | Structural consequence |
|---|---|---|---|
| **Central** | ring-shaped lease space, all four orientations, uniform span | free, symmetrical envelope | core doubles as the lateral system — cheapest |
| **Offset** (one side) | single-orientation deep plate; column-free lease space | one blank face, three glazed | needs outriggers or a perimeter frame; asymmetric wind |
| **Split** (two ends) | column-free bar between the cores | strong end-condition expression | very efficient laterally; big net-to-gross cost |
| **External / detached** | maximally free plate | core reads as separate object | most expensive; needs its own structure |

**Frequencies and sizes — treat with care.**

| Quantity | Value | Mark |
|---|---|---|
| Share of tall buildings with a **central** core (sample 500) | **85%** | ⚠ [snippet] — Oldfield & Doherty 2019, PDF 404'd |
| Core-to-GFA ratio, range across tall buildings | 4–21% | ⚠ [snippet] |
| Core-to-GFA, mean and sd | mean **13.4%**, sd 3.2% | ⚠ [snippet] |
| Central-core buildings cluster at | 8–13% core-to-GFA | ⚠ [snippet] |
| Tall hotel towers: mean space efficiency / mean core ratio | 81.2% / 16% | ⚠ [snippet] |
| Tall hotel towers: range | 70–94% / 4–28% | ⚠ [snippet] |
| Japanese tall buildings using central core | 70% of sample | ⚠ [snippet] |

Every figure in that table is second-hand. They are consistent with each other
and with practice, which is mild corroboration, but **do not ship any of them.**
§9 lists the four papers to pull.

**Core sizing — the derivation that actually matters.** Core area is not a
percentage, it is a *consequence of population*:

```
  population   = NFA / occupant_density
  lifts        = f(population above this floor, handling capacity, interval)
  stairs       = f(occupant load per floor)            [see §2.5]
  toilets      = f(population, occupancy type)         [plumbing code]
  shafts       = f(air volume, electrical load)
  core_area    = Σ of the above + walls + lobby
```

⭐ **This is why towers taper.** The core serves the floors *above* it. As you
rise, fewer floors remain above, so fewer lifts are needed, so the core shrinks.
A constant floor plate with a shrinking core would give a rising net-to-gross —
so instead the plate is shrunk to hold the ratio, and the tower tapers or
sets back. The taper is a *derived* form, not a stylistic one.

Supporting figures (all [snippet], from a search summary of an MDPI review):
lifts, stairs and plant occupy **30–40% of total floor area** in tall buildings;
sky lobbies are recommended above **~40 storeys**; a 52-storey office needing
24 single-deck cars in three zones can be served by 13 double-deck cars in two
zones. ⚠ Not fetched.

**Rule vs preference vs signature:**
- **RULE:** the core exists, contains those items, and is sized by population.
- **RULE:** it shrinks with height in a tall building.
- **PREFERENCE:** central. It is the default because it is cheapest laterally
  and gives equal lease spans, not because it is better architecture.
- **SIGNATURE:** offset and split cores are strongly associated with particular
  offices and eras — Inland Steel (1958), HSBC Hong Kong (1985), Lloyd's of
  London (1986) are the canonical trio. ⚠ [snippet]: this trio is named in
  the Oldfield & Doherty abstract as reported by search; I have not read the
  paper.

### 2.4 Floor plate efficiency

```
  efficiency = NFA / GFA          (net-to-gross, "efficiency", "usable ratio")
  loss factor / core factor = 1 - efficiency, roughly
```

| Quantity | Value | Mark |
|---|---|---|
| Successful office towers | 80–88% | ⚠ [snippet], attributed to CTBUH by a trade site |
| "Excellent" for modern offices | 80–90% | [trade] |
| "Poor" by commercial standards | < 70% | [trade] |
| Core factor / loss factor typical range | 10–18% | [trade] |

These are all soft. What is *not* soft is the shape of the function: efficiency
falls as the plate gets smaller (the core does not shrink proportionally) and
falls as the plate gets very large (deep space is unlettable). **There is an
optimum plate size for a given core, and it is computable** — this is a genuinely
good candidate for a solve in the tool rather than a parameter.

### 2.5 Egress — the constraint that actually decides plan topology

This section deliberately states the *shape* of the rules; the exact code
sections and numbers are in §6.6, which was researched separately against IBC
text.

**The three constraints, and what each one does to the plan:**

1. **Two remote exits.** Above a small occupant load, every space needs two
   independent ways out, and the two exits must be *separated* by a minimum
   fraction of the diagonal of the area served (the "one-third of the
   diagonal", relaxed to one-quarter or similar in sprinklered buildings).
   → **This is the rule that creates the two-stair core.** It also means the
   two stairs cannot be side by side, which is why cores are elongated and why
   the lift bank so often sits *between* the two stairs.

2. **Travel distance.** The longest path from any occupied point to an exit is
   capped. → **This caps the plan's radius**, and therefore caps a floor plate
   given a fixed core position. Combined with (1), it is what forces a second
   core into a long floor plate rather than a longer corridor.

3. **Dead-end limit.** A corridor may only run so far past the last exit
   before it becomes a trap. → **This is what makes the corridor
   double-ended.**

⭐ **Put those three together and the double-loaded corridor is not designed —
it precipitates.** Two stairs at the ends (constraint 1, maximum separation),
a corridor between them (constraint 3, no dead ends), a length capped by
constraint 2, and units on both sides because that is the only way to pay for
the corridor. **The most common building plan in North America is a solved
constraint problem.** That is exactly the kind of thing this project should
generate rather than model.

**The single-stair / point-access counter-case.** Much of Europe and Asia
permits a single stair for small residential floor plates, which produces a
*completely different* plan family — a point block with 2–4 units around one
core, cross-ventilated, no corridor. This is why European and American
apartment buildings look different in plan, and it is a **code parameter, not a
culture parameter.** Making `egress_regime ∈ {two_stair, point_access}` a
first-class input is the highest-leverage single switch in the whole residential
generator. ⚠ The specific unit-count and travel-distance limits for the
single-stair exception are **[UNVERIFIED]** — I ran out of search budget before
reading them and did not want to recall numbers. §9.

### 2.6 Residential adjacency and the wet stack

**Served and servant.** Kahn's formulation is the cleanest statement of a rule
that predates him: *served* spaces (rooms people occupy) and *servant* spaces
(stairs, corridors, plant, shafts, bathrooms) are different in kind and should
be planned separately [cited]. At Richards Medical he pushed the servant spaces
into four external towers specifically so the laboratories would have
"uninterrupted floor areas" [cited].

For a generator this is the right primitive: **classify every room as served or
servant before laying anything out**, because servant spaces stack and served
spaces do not.

**The wet stack — a genuinely hard constraint, with numbers.**

| Quantity | Value | Mark |
|---|---|---|
| 3-inch stack capacity | up to **72 DFU** (IPC 2024) | [cited] |
| 4-inch stack capacity | up to **500 DFU** (IPC 2024) | [cited] |
| At ~10 DFU/floor from bathroom groups, a 4-inch stack serves | up to **50 residential floors** | [cited] |
| Back-to-back bathrooms above 51 floors need | **6-inch** stack | [cited] |
| Floor opening for a cast-in-place firestop, 3" / 4" / 6" pipe | ≈ **4.5" / 5.5" / 7.5"** | [cited] |
| Single-stack systems limited to | 10–20 floors before trap-seal failure | [snippet] |

**The plan rules that follow, and they are hard rules:**

```
  R1  every wet room sits on a wet wall
  R2  a wet wall is continuous vertically through the whole stack of floors
  R3  back-to-back wet rooms share one wall and one stack   (halves the risers)
  R4  wet wall thickness > standard partition               (pipe + firestop)
  R5  a kitchen and a bathroom may share a stack; two bathrooms preferably do
```

R2 is the one that breaks naive generators: **you cannot generate floor plans
independently per floor.** A residential tower's plan is generated *once* and
repeated, or generated as a stack with the wet walls as fixed rails. This is
the direct analogue of the "corner_i sits between wall_i and wall_i+1"
invariant established in `footprint_plan.md` — an inter-element relation that
must be built in, not checked afterwards.

**Circulation as the organising element, not the leftover.** The standing error
in procedural room layout is to place rooms and then connect what is left. The
correct order is the reverse, and it is what every architect actually does:

```
  1. place the circulation figure (hall / corridor / stair / open plan spine)
  2. place the servant spaces against it, stacked
  3. hang the served spaces off it
  4. the leftover is storage or is a mistake
```

**Residential floor plate dimensions:**

| Quantity | Value | Mark |
|---|---|---|
| Double-loaded corridor block, min floor plate width | 40 ft | [snippet] |
| Double-loaded corridor block, max floor plate width | 70 ft | [snippet] |
| Unit depth, curtain wall to core face (high-rise) | 20–30 ft | [snippet] |
| Apartment corridor width, typical code minimum | 1.2–1.5 m (4–5 ft) | [snippet] |

⚠ All [snippet] — the MDPI source (Buildings 11(3):99) returned 403. §9.

### 2.7 The section constrains the plan

**The rule.** Floor-to-floor height is the sum of a stack, and the stack has a
floor: structure + services + ceiling + clear height. Once floor-to-floor is
fixed by an FAR/height limit or a pro forma, the **available structural depth is
fixed**, and structural depth caps the span. Span caps the grid. So *the
section chooses the grid*, top-down.

Measured, from SteelConstruction.info [cited] — this table is the most
directly usable structural data in the whole document:

**Span-to-depth ratios**

| Construction | Secondary beams | Primary beams |
|---|---|---|
| Steel beam | 18–20 | 13–15 |
| Composite beam | 22–25 | 16–18 |
| Cellular beam | 20–27 | 15–18 |
| Shallow floor / integrated beam | 26–28 | — |
| Steel truss | 15–18 | 12–15 |

**Structural depth for multi-storey buildings**

| Structural option | Structural depth |
|---|---|
| Composite beam construction | 800–1,200 mm |
| Cellular beams with service integration | 800–1,100 mm |
| Downstand beams with precast slabs | 1,200–1,450 mm |
| Shallow floor / integrated beams | 600–800 mm |

**Floor-to-floor heights**

| Project type | Floor-to-floor |
|---|---|
| Prestige office | 4.0–4.2 m |
| Speculative office | 3.6–4.0 m |
| Renovation | 3.5–3.9 m |

And the summary statement, [cited] verbatim: *"an overall structural and
services depth of 1 to 1.2m (including 120mm for the ceiling) is generally used
in planning for multi-storey buildings."*

⭐ **This closes the loop and makes the whole thing a solve.** Given a
floor-to-floor and a system:

```
  available_depth = floor_to_floor - clear_height - ceiling(120mm) - raised_floor
  max_span        = available_depth × span_depth_ratio[system]
  bay             = the largest grid ≤ max_span that also divides the
                    parking module (§2.1) and the facade module
```

Three inputs — `floor_to_floor`, `system`, `clear_height` — and the grid falls
out. That is the metal-extrusion-maker shape applied to structure.

---

## 3. What generates a plan, and what must be authored

The brief asks for the smallest set of inputs from which a plausible plan
follows. Here it is, honestly split.

### 3.1 What genuinely derives

| Output | Derives from | Section |
|---|---|---|
| Column grid | `floor_to_floor`, `system`, `parking_below?`, `stall_width` | §2.1, §2.7 |
| Floor plate depth | `lease_span` + core size | §2.2 |
| Core size | occupant load ⇒ lifts + stairs + toilets + shafts | §2.3 |
| Core position | site frontage count + `core_strategy` | §2.3 |
| Number and separation of stairs | occupant load + diagonal rule | §2.5 |
| Whether there is a corridor, and its topology | egress regime + unit count | §2.5 |
| Building depth for a residential bar | `2 × unit_depth + corridor_width` | §2.6 |
| Wet wall positions | unit plan, stacked | §2.6 |
| Taper / setback profile | core shrinkage with height | §2.3 |
| Roof form | the footprint, via the weighted straight skeleton | `roof_typology_and_math.md` |

That is a lot. **Ten of the visible properties of a building plan derive from
about six numbers.** This is the generative vocabulary the project asks for,
and it exists.

### 3.2 What does not derive and must be authored

Say this plainly, because pretending otherwise is how procedural work produces
pastiche:

1. **The room adjacency graph of a house.** There is no derivation from site
   and size to "kitchen adjacent to dining, bathroom off the hall". It is
   cultural, regional and period-specific. It must come from a **catalog of
   graphs**, one per house typology per region per era — exactly the CSV
   pattern already used for signs, mouldings and hardware.
2. **Room proportions.** Palladio's seven ratios (§6.1) are a catalog, not a
   derivation. Modern room ratios are a different catalog.
3. **Which of the four core positions.** Derivable *only* if you also model the
   site, the views and the developer's brief. In practice: a weighted choice
   from the catalog, biased by frontage count.
4. **The programme.** What is in the building. This is upstream of everything
   and is pure input.
5. **Irregularity, wear, deviation, non-conformity.** Real plans are full of
   local exceptions. These are art direction and belong in a separate layer
   with their own parameters, per the standing rule about separating fact from
   art direction.
6. **Anything about a *specific* architect's work** (§5). Signature is
   authored, always.

### 3.3 The minimum input set

```
  programme        : one of { house, rowhouse, walkup, slab, plate, tower }
  footprint        : polygon (already produced by BuildingFootprintGenerator)
  storeys          : int
  floor_to_floor   : float                       -> §2.7 gives the grid
  structural_system: enum                        -> §2.7
  lease_span       : float (commercial only)     -> §2.2
  egress_regime    : enum {two_stair, point_access}  -> §2.5
  parking_below    : bool + stall_width          -> §2.1
  era/region       : catalog key                 -> adjacency graph, ratios
```

**Nine inputs.** Everything in §3.1 follows. That is the answer to "what
generates a plan."

---

## 4. The graph layer — how to *score* a plan rather than just produce one

### 4.1 The plan as a graph

Two graphs, and conflating them is a common error:

- **The adjacency graph** — nodes are rooms, edges are shared walls.
- **The access graph** — nodes are rooms, edges are *doors*. This is the one
  space syntax uses, and the one that matters, because two rooms can share a
  wall and be a hundred steps apart.

Add a root node for the exterior/entrance and you have the **justified graph**
(j-graph): the access graph redrawn with the exterior at the bottom and every
other node placed at its shortest-path depth from it. The *shape* of the
j-graph is a readable signature of a plan type — a shallow bush is an open
plan, a deep chain is an enfilade, a wide shallow tree with one hub is a
hall-and-rooms house.

### 4.2 What space syntax measures

Hillier & Hanson's contribution is to normalise depth so that plans of
different sizes can be compared. The formulas below are **[cited] verbatim
from Jiang & Zhang (2026)**, §6.2 of that paper, which restates the
Hillier–Hanson definitions in a form that is directly implementable:

For a node `i` in a connected component `C` with `n = |C|`, where `d(i,j)` is
the shortest-path distance:

```
  Total depth      TD_i = Σ_{j ∈ C, j ≠ i} d(i,j)

  Mean depth       MD_i = TD_i / (n − 1)

  Relative
  asymmetry        RA_i = 2(MD_i − 1) / (n − 2)

  Normalisation    D_n  = 2·{ n·[ log2((n+2)/3) − 1 ] + 1 } / ((n−1)(n−2))

  Real relative
  asymmetry        RRA_i = RA_i / D_n

  Integration      s_i = 1 / RRA_i
```

Degenerate cases: for `n ≤ 2`, or non-positive `RRA_i`, set `s_i = 0` to avoid
infinities [cited]. The alternative closeness form is `s_i = (n−1)/TD_i`
[cited].

**Reading it:** high integration = topologically close to everything else = a
configurational core. Low integration = segregated = private.

**The `D_n` term is doing the real work.** It is the expected RA of a node in a
"diamond-shaped" j-graph of the same size, so dividing by it removes the size
effect. Without it you cannot compare a studio to a mansion. This is the
formula worth implementing carefully.

### 4.3 The scoring functions this project should actually implement

Four, in increasing order of ambition. All are cheap, all are testable, and
none of them require a neural network:

**S1 — Daylight coverage.** Fraction of floor area within `d` of glazing, and
max distance to perimeter (§2.2). Compare against the [cited] table of real
buildings. Immediately useful and needs nothing but a distance field.

**S2 — Egress satisfaction.** For every point: shortest path to the nearest
exit ≤ travel-distance limit; two paths exist that do not share an edge;
exit separation ≥ the diagonal fraction. This is a *pass/fail* gate, and it is
the honest way to make a generated plan legal rather than merely plausible.

**S3 — Space syntax integration profile.** Compute integration per room,
average per room *category*, and compare the ordering against an expected
profile. Jiang & Zhang's target is explicit and architecturally meaningful:
**shared living spaces should be integrative; private spaces should remain
segregated** [cited]. So the check is:

```
  integration(living) > integration(circulation) > integration(bedroom)
                                                > integration(bathroom)
```

A generated plan where the bathroom is the most integrated space is *wrong*,
and this catches it without anyone looking at it.

**S4 — Structural consistency.** Every partition either sits on the grid or is
declared free-plan (§5.1). Wet walls stack across all floors. Every column has
a column above and below or a declared transfer.

⭐ **S1 through S4 are the parity oracle for the plan work**, the same role
that the ordered/sorted point comparison plays in the footprint rewrite.

### 4.4 The finding worth acting on

> **Space syntax integration can be used as an optimisation signal, not only as
> analysis.**

Jiang & Zhang (2026), *Space Syntax-guided Post-training for Residential Floor
Plan Generation* (arXiv:2602.22507v2), Tongji University / HKUST(GZ), do
exactly this. Their framing of the gap is precise and worth quoting because it
describes the state of the entire field [cited]:

> "in floor plan generation, spatial configurational logic is largely limited
> to input-side conditioning, without output-side evaluation and feedback-driven
> model optimization."

That is: every existing generator is *told* the adjacency graph and then judged
on whether the picture looks like the training set. Nobody measures whether the
result is spatially sensible. Their "Space Syntax Integration Oracle" (SSIO)
converts a generated plan into a rectangle-space graph and computes integration
deterministically — and then feeds it back, either by filter-and-retrain
(SSPT-Iter) or by PPO reinforcement learning (SSPT-PPO).

**Why this matters for AssetBash even though we are not training a network:**
the *oracle* is the reusable part, and it is entirely classical. Their pipeline
is five deterministic stages [cited]:

```
  1. parse plan to labelled room regions + door-mediated connectivity
  2. decompose each room's walkable core into maximal axis-aligned rectangles
     (greedy cover, discard rectangles below area A_min)
  3. build a graph: rectangle = node; within-room edges by adjacency;
     cross-room edges via interior-door connected components
  4. compute integration per node; aggregate to room, then to room category
  5. validity checks; skip empty cores / zero rectangles
```

**Every step of that is a Houdini SOP network.** Step 2 is a rectangular
decomposition (see §6.5), step 3 is a graph build, step 4 is `shortestpath` plus
a wrangle. There is no learning anywhere in the oracle. **We can implement
their evaluator without implementing their generator, and use it as a gate on
plans produced by grammar rules.** That is the single most actionable thing in
this document.

One incidental but valuable data point from the same paper: applying automated
validity screening to **RPLAN's 80,788 real residential plans** left **76,878
usable, 95.16%** [cited]. Even a curated academic dataset is 5% broken.

---

## 5. The signature architects, as operators

The instruction for this section is to express each as rules or operators, and
to be explicit about rule vs preference vs signature. The organising insight,
stated at the top because it is the useful one:

> **Each of these four practices substitutes into exactly one of the three
> layers (grid / core / partition) and leaves the others conventional.**

That is what makes them computable. A practice that broke all three at once
would just be noise.

### 5.1 Le Corbusier — the Five Points, Dom-Ino, the Modulor

**Dom-Ino (1914) is the enabling structure**, and it is one diagram: slabs,
six columns set in from the edge, a stair. No load-bearing walls. Everything
else follows from that one move — the columns are inboard of the slab edge, so
the façade carries nothing.

**The Five Points (1926):** pilotis; the free plan; the free façade; the ribbon
window; the roof garden.

⭐ **The free plan is the point that matters, and it is precisely a
frame/infill separation.** As a formal operator:

```
  FREE_PLAN:
      partition_layer ⊥ structure_layer

      structure:  a column lattice, set in from the slab edge
      partitions: any curve, any position, subject only to
                  (a) not intersecting a column
                  (b) topological validity of the resulting rooms
      facade:     independent of both (this is the free facade —
                  the same decoupling applied to the vertical plane)
```

**This is the exact separation AssetBash needs**, and it is worth saying why in
project terms. Right now the building tools couple wall generation to the
footprint's edges. A free-plan model makes them three independent generators
with defined interfaces:

```
  FRAME   : grid  -> columns, beams, slab edges     (§2.1, §2.7)
  INFILL  : region + adjacency graph -> partitions  (§4, §6.1, §6.5)
  SKIN    : slab edge -> facade                     (existing edge classification)
```

The `Corner_i` / `Wall_i` classification in `footprint_plan.md` is the SKIN
interface. This document is about FRAME and INFILL. **They should not know
about each other.**

**The Modulor (1948)** is the dimensional catalog: a 1.83 m figure, navel at
1.13 m, raised hand at 2.26 m, with two golden-ratio progressions — the *red*
series keyed to 1.13 and the *blue* keyed to 2.26 [snippet — these figures
appeared in a search summary; I could not fetch a primary source]. As a
generator input it is a **dimension quantiser**: snap free dimensions to the
nearest member of the series. That is trivially implementable and gives a
recognisable proportional signature.

**Where the claims do not survive contact with use.** This must be in the
document, because a system that swallows the manifesto uncritically will
generate a world nobody lives in.

- **Pessac (Quartiers Modernes Frugès, 1924–26), documented by Philippe Boudon
  in *Lived-in Architecture: Le Corbusier's Pessac Revisited*.** Residents
  systematically undid the five points: infilled the pilotis, replaced ribbon
  windows with conventional punched openings, added pitched roofs over the roof
  terraces, added rooms [snippet — I could not fetch a full text; the pattern
  of modifications is consistently reported across several sources]. A 1970
  study found many changes were *technical*, not aesthetic: flat roofs leaked,
  and the bespoke windows had no off-the-shelf replacements [snippet].
- Le Corbusier's own reported response: *"it is life that is right and the
  architect who is wrong"* [snippet — widely reproduced; I have not seen a
  primary citation and it should be treated as apocryphal until one is found].
- **The Modulor's universal claim is false** and is now routinely criticised as
  a masculinist and ableist universalism built on a six-foot male figure,
  fitted to the mathematics rather than derived from it [snippet].

⭐ **The procedural lesson from Pessac is directly useful and is not a
criticism of Corbusier.** It is that **the free plan is unstable under
occupation**: given time, occupants re-introduce enclosure, pitched roofs and
punched windows. So a convincing generated free-plan building of any age should
have a *modification layer* — and the modification operators are enumerable:
infill pilotis, subdivide the open plan, punch the ribbon, cap the terrace.
That is four operators and it is a whole aging system for modernist buildings.

**Rule / preference / signature:**
- **RULE:** a column frame set in from the slab edge permits free partitions
  and a free façade. Structural fact.
- **PREFERENCE:** ribbon windows and roof gardens. Available consequences of
  the rule, not required by it.
- **SIGNATURE:** pilotis, the specific curved partition vocabulary, the
  Modulor. These identify Corbusier, and applying them to a generic building
  produces pastiche.

### 5.2 OMA / Rem Koolhaas — the section as generator

OMA is the most computable of the four because the method is already close to a
constraint solver: **stack the programme, then let the plan be whatever the
stacking leaves.**

**The five theorems of Bigness** (from *Bigness, or the Problem of Large*,
1994). Theorems 1–5 [cited from a fetched full text]:

1. *"Beyond a certain critical mass, a building becomes a Big Building. Such a
   mass can no longer be controlled by a single architectural gesture, or even
   by any combination of architectural gestures."*
2. *"The elevator — with its potential to establish mechanical rather than
   architectural connections — and its family of related inventions render null
   and void the classical repertoire of architecture."*
3. ⭐ *"In Bigness, the distance between core and envelope increases to the
   point where the facade can no longer reveal what happens inside."*
4. *"Through size alone, such buildings enter an amoral domain, beyond good or
   bad. Their impact is independent of their quality."*
5. *"Together, all these breaks … imply the final, most radical break: Bigness
   is no longer part of any urban tissue. It exists; at most, it coexists. Its
   subtext is fuck context."*

⭐ **Theorem 3 is §2.2 restated as a theory of architecture.** Koolhaas is
describing lease span. When core-to-perimeter exceeds the depth at which the
interior can be read from outside, interior and exterior become independent
projects. **For this generator that is a licence, not a lament**: past a depth
threshold, the façade generator and the plan generator can be fully decoupled
and no one can tell. That is a real performance saving and a real
plausibility argument.

**The operators, extracted:**

```
  OP-1  PROGRAMME_STACK
        Given an ordered list of programmes, assign each to a contiguous band
        of floors. The plan of each band is derived independently.
        Adjacency in SECTION replaces adjacency in PLAN.

  OP-2  PLATFORM / VOID ALTERNATION       (Seattle Central Library)
        n stable programmatic platforms, alternating with (n−1) unstable
        "in-between" planes. The platforms have fixed size and programme;
        the in-between spaces absorb all the slack.
        Seattle: FIVE platforms and FOUR flowing 'in between' planes [cited],
        and OMA states these "together dictate the building's distinctive
        faceted shape" [cited] — i.e. the ENVELOPE is derived from the
        programme stack, not the reverse.

  OP-3  CONTINUOUS_RAMP
        Replace the stacked-floor topology with a single monotonic ramp
        through a programme sequence. (Seattle's Books Spiral [cited].)

  OP-4  SECTION_TO_PLAN ROTATION
        Take a section, rotate it 90°, use it as a plan. OMA's Parc de la
        Villette entry used the Downtown Athletic Club section rotated into
        striated programmatic bands [snippet], for "maximum permeability
        through each programmatic band" [snippet].

  OP-5  PROGRAMMATIC COLLISION
        Deliberately place incompatible programmes on the same floor with no
        transition. The Downtown Athletic Club's ninth floor — locker room,
        punching bags, and an oyster bar with a Hudson view — is the canonical
        instance [snippet].
```

**OP-1 and OP-2 are directly implementable and should be built.** They are how
you get a mixed-use tower that is not just a stack of identical plates: each
programme band gets its *own* lease span, its own grid dimension within the
inherited module, and its own floor-to-floor — and the envelope faceting falls
out of the differences.

**OP-4 and OP-5 are signature.** They produce OMA buildings. Use with intent.

**Rule / preference / signature:**
- **RULE:** past a size threshold, no single gesture controls the whole; parts
  become autonomous. Theorem 1 is an observation about scale, and it is true.
- **RULE:** theorem 3. It is lease span.
- **PREFERENCE:** letting the section drive. Legitimate and general.
- **SIGNATURE:** the specific faceting, the diagonal void, the exposed
  programmatic collision, the graphic diagram aesthetic.

### 5.3 MAD / Ma Yansong — continuous curvature, rigid core

Ma's stated position is *Shanshui City* — not an eco-city or a garden city, but
architecture organised around an "affinity for the natural world" drawn from
Eastern philosophy [snippet — from a search summary of the MAD site, which
returned 403 to direct fetch].

The important question the brief poses — *what happens to a core, a lease span
and a structural grid when the perimeter is a curve?* — has a clean, measured
answer at the Absolute Towers, Mississauga:

| Property | Value | Mark |
|---|---|---|
| Tower A | 56 storeys, 170 m | [cited] |
| Tower B | 50 storeys, 150 m | [cited] |
| Rotation per floor | **1° to 8°** at each successive level | [cited] |
| Total rotation, bottom to top | **209°** | [snippet] |
| Floor plate | ellipse | [snippet] |
| Core | **remains fixed**; torsion carried by concrete load-bearing walls that "extend and contract depending on the rotation of the floors" | [snippet] |
| Balconies | continuous, wrapping every level, cantilevered | [cited] |

⭐ **The answer to the brief's question is: nothing happens to the core.** MAD
rotates the *perimeter* and holds the *core* rigid. Lease span becomes a
function of floor index, structure becomes a variable-length radial wall, and
the balcony absorbs the mismatch. As an operator:

```
  OP-MAD  ROTATE_PERIMETER_HOLD_CORE

    core(z)      = constant polygon, constant orientation
    perimeter(z) = R(θ(z)) · base_perimeter,   θ monotone in z
    θ'(z)        ∈ [1°, 8°] per floor          (measured, Absolute Towers)
    structure    = radial walls from core to perimeter, LENGTH VARIES per floor
    lease_span(z, direction) = |perimeter(z) − core| — now a FIELD, not a number
    balcony      = the difference between successive plates
```

**Three secondary consequences, all computable:**
1. The balcony is not applied, it is *derived* — it is the sweep between plate
   `z` and plate `z+1`. That is a boolean/loft, not an asset.
2. Self-shading: the recess produced by rotation shades the floor below. MAD
   describe the balconies as shading the interior from summer sun while
   admitting winter sun [cited]. So the rotation rate has a *performance*
   reading, not only a formal one.
3. Rotation rate is a **profile curve, not a constant** — 1° to 8° means it
   accelerates and decelerates. A constant twist reads as a cheap imitation.
   This is exactly the "ramp curve" problem the moulding work already solved.

**Rule / preference / signature:**
- **RULE:** a rotating plate needs a torsion-resisting system, and holding the
  core fixed is the cheap way to get one.
- **RULE:** the derived balcony. Geometry.
- **PREFERENCE:** curvature at all; continuous rather than faceted perimeter.
- **SIGNATURE:** the *shanshui* landscape reading, the specific ellipse, the
  non-uniform twist profile.

### 5.4 Morphosis / Thom Mayne — superimposed orders

The Morphosis operation is the one a grid-based system genuinely cannot do,
and it is easy to state: **more than one organising geometry, present at once,
unreconciled.**

Reported characterisation of the method [snippet — from search summaries; the
firm's own site is an Angular app that returns no text to a fetcher, and SFMOMA
does not carry these statements]: Mayne "challenges architectural conventions
by collapsing plan, elevation, and detail through juxtapositions of scale,
oblique angles, projection, and rotation", and the designs "often include
multiple organizational systems which find unique expression."

⚠ I could not verify that phrasing against a primary source and it should be
treated as second-hand. The *operator*, however, is directly visible in the
buildings and does not depend on the quotation:

```
  OP-MORPH  SUPERIMPOSE

    Take k organising systems, k ≥ 2:
        G1 = orthogonal structural grid, aligned to the street
        G2 = a second grid, rotated by α, aligned to something else
             (a site diagonal, a view, a former alignment, a circulation axis)

    Assign each ELEMENT CLASS to one system, not each REGION:
        columns, slabs        -> G1     (structure stays orthogonal)
        circulation, skin,    -> G2     (the visible layer rotates)
        brise-soleil, ramps

    The building's character is the RESIDUE where G1 and G2 disagree.
```

⭐ **The key point, and the one that keeps this from being noise: the two
systems are assigned to different *element classes*, not to different parts of
the plan.** A plan chopped into a rotated half and a straight half is a bad
imitation. A plan where the structure is orthogonal and the circulation and
skin are rotated is the real operation. It is also *cheap* — the frame stays
buildable and only the light layers rotate.

**A second, more useful Morphosis observation.** The San Francisco Federal
Building (2007) is a signature-architect building that *re-imposes* the oldest
plan rule in this document:

| Property | Value | Mark |
|---|---|---|
| Tower width | **65 ft** (≈20 m) | [snippet] |
| Height | 18 storeys, 240 ft | [snippet] |
| Upper floors, naturally ventilated, no air conditioning | **13 floors** | [snippet] |
| Lower floors, air conditioned | 5 | [snippet] |
| Claimed lighting energy reduction | ≈26% vs a standard office | [snippet] |
| Claimed power reduction vs Title 24 | 33% | [snippet] |

⚠ All [snippet]; the GSA PDF is a binary I could not text-extract and the
Architectural Record page was not fetched.

⭐ At 65 ft wide with a perimeter core arrangement, that is a **~25–30 ft lease
span** — the *pre-air-conditioning* number from §2.2, arrived at from the
opposite direction. **This is the single most useful fact in §5 for the
generator**: the daylight-driven narrow plate is not a period feature. It is a
performance requirement, and it recurs. A generated "green office tower" that
has a 45 ft lease span is wrong.

**Rule / preference / signature:**
- **RULE:** a 65 ft plate can be daylit and cross-ventilated; a 120 ft plate
  cannot. Physics.
- **PREFERENCE:** superimposing two orders at all.
- **SIGNATURE:** the specific angle, the exposed structural exoskeleton, the
  perforated metal layer, the fragmentation.

### 5.5 The rule / preference / signature table

The consolidated version, because conflating these is how procedural work
produces pastiche:

| Statement | Class | Applies to |
|---|---|---|
| Grids align across a transfer; parking sets the grid | **RULE** | all |
| `module = 2·stall_depth + aisle` | **RULE** | all with parking |
| Daylight from one side reaches ~2.5 × head height | **RULE** | all |
| Two remote exits; travel distance capped; dead ends capped | **RULE** | all |
| Core is sized by the population above it, so towers taper | **RULE** | tall |
| Wet walls stack vertically | **RULE** | residential |
| `available_depth × span/depth ratio` caps the bay | **RULE** | all framed |
| A column frame set in from the edge frees plan and façade | **RULE** | framed |
| Beyond a critical mass, no single gesture controls the whole | **RULE** | big |
| Rotating plates need a torsion system; a fixed core is the cheap one | **RULE** | twisted |
| A 65 ft plate can cross-ventilate; a 120 ft one cannot | **RULE** | all |
| Central core | **PREFERENCE** (85% ⚠[snippet]) | tall |
| 40 ft minimum lease span | **PREFERENCE** — a pro forma, not physics | US spec office |
| 27 ft / 30 ft / 45 ft bay | **PREFERENCE** — regional and era-bound | all |
| Ribbon windows, roof gardens | **PREFERENCE** | modernist |
| Letting the section drive the plan | **PREFERENCE** | any |
| Superimposing two organising orders | **PREFERENCE** | any |
| Pilotis, the Modulor, the free-form partition | **SIGNATURE** — Corbusier | — |
| Faceted platform/void envelope, diagonal void, programmatic collision | **SIGNATURE** — OMA | — |
| Non-uniform twist, continuous wrapping balcony, *shanshui* framing | **SIGNATURE** — MAD | — |
| Exoskeleton, rotated skin over orthogonal frame, fragmentation | **SIGNATURE** — Morphosis | — |

**Use of the tool should be:** rules always on; preferences from a catalog with
regional/era weights; signatures behind an explicit, named, off-by-default
switch. If a signature is ever on by default, the tool generates pastiche.

---
