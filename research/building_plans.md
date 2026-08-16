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

⭐ The tartan grid is not a modern idea and not my coinage: it is Stiny &
Mitchell's term for Palladio's underlying structure (§6.1), and Palladio got the
method — dimension everything from one module by ratio — from Vitruvius (§5A).

Each layer constrains the next and **never the reverse**. The grid is set by
economics below the building (parking, spans, formwork repetition). The core is
sized by the population it serves and placed by daylight and site. Only then is
there a residual to subdivide.

The five things worth internalising:

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
4. **The proportional system is two thousand years old and was always a
   lookup table, not a constant.** Vitruvius sizes the wings of an atrium by a
   ratio that *changes with the size of the atrium* (§5A.3) — the same
   band-keyed catalog pattern this project already uses for signs and corner
   treatments. The line Vitruvius → Palladio → Stiny & Mitchell → this tool is
   unbroken, and §5A draws it explicitly.
5. **The signature architects are not exceptions to this — they are
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
| **TOP-LIT HALL** (basilica, church, market hall, mill, atrium office — §5A.4) | the **section**: a raised centre over lower flanks | the span of the central volume | ⭐ *not applicable* — depth is solved in section, not plan | aisles are structural bays, not rooms |
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
generator.

⭐ **And the US version of the switch is four numbers**, from IBC 2021
Table 1006.3.4(1) [cited — full tables in §6.6]: Group R-2 may have a single
exit at basement, 1st, 2nd and 3rd storey, with a maximum of **4 dwelling units**
per storey, a maximum **125 ft** travel distance, sprinklered throughout, with
emergency escape openings. **4th storey and above: not permitted.** Change those
four numbers and you change the entire residential fabric of a generated city.

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
| Whether the plan needs a top-lit spine, and how wide | plate depth vs `2 × lease_span` — OP-BASILICA | §5A.4 |
| Room orientation (which room faces where) | `north` + the seasonal-use table | §5A.3 |
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
  north            : vector                      -> §5A.3 room orientation, §4.3 S1
  classical_mode   : enum {off, applied, structural}  -> §5A.6
```

**Eleven inputs.** Everything in §3.1 follows. That is the answer to "what
generates a plan."

⚠ **`north` is easy to forget and expensive to add later.** Every learned
dataset in §6.3 omits it, and MSD's authors call that out as a defect
(*"the direction of the sun is a critical feature in environmental design"*).
Vitruvius had it in Book VI. Put it in from the start.

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

## 5A. The classical foundation — Vitruvius, and why the line runs straight to §6.1

Added 2026-08-16 at Jordan's request: *"the classical architecture that was
established by Vitruvius and how a roman villa or a basilica was created and how
that still informs certain types of architecture."*

⭐ **This is not a detour, it is the root of the computational thread.** The
line is unbroken and worth stating once, plainly:

```
  Vitruvius (c. 30–15 BC)   sizes buildings from a module and derives the rest
                            by ratio; publishes graduated proportion TABLES
        |
  Palladio (1570)           I Quattro Libri — receives Vitruvius, adds his own
                            canon: seven room ratios, bilateral symmetry,
                            wall thickness as a unit
        |
  Stiny & Mitchell (1978)   formalise Palladio as 72 production rules in 8
                            stages  ->  §6.1
        |
  this project              a tartan grid, a proportion catalog, a band lookup
```

**Everything Stiny & Mitchell formalised was already parametric when Vitruvius
wrote it down.** They did not invent the parametrisation; they invented the
*notation*. That is worth knowing, because it means the correct thing to look
for in Vitruvius is not inspiration — it is **data**.

Sources: the translation hosted at LacusCurtius
(`penelope.uchicago.edu/Thayer/E/Roman/Texts/Vitruvius/`), and Morgan's 1914
translation via Perseus, fetched independently and used to cross-check the
basilica passage. All quotations below are **[cited]** from one of those two.
Where the two translations were compared, that is noted.

### 5A.1 The six principles, and which of them are computable

Vitruvius Book I ch. 2 names six: **ordinatio, dispositio, eurythmia,
symmetria, decor, distributio**. Read as a specification rather than as
philosophy, they sort cleanly into three that a generator can act on and three
that it cannot:

| Principle | Vitruvius's definition [cited] | Computable? |
|---|---|---|
| **Ordinatio** | *"The adjustment of size of the several parts to their several uses, and required due regard to the general proportions of the fabric"* | ⭐ **Yes** — this is sizing by function. It is §2.3's core-sizing derivation, stated in 25 BC |
| **Dispositio** | *"The disposition in their just and proper places of all the parts of the building"* | ⭐ **Yes** — this is the adjacency graph plus a placement rule (§4.1) |
| **Symmetria** | *"The parity of the parts to one another; each corresponding with its opposite, as in the human figure"* | ⭐⭐ **Yes** — a module and a set of ratios. §5A.2 |
| **Eurythmia** | the pleasing effect of the arrangement | ✖ No. This is the judgement layer |
| **Decor** | consistency arising from circumstance, custom and nature | ✖ Not directly — but it is *catalog selection by context*, which is implementable as a lookup even if the judgement is not |
| **Distributio** | *"A due and proper application of the means afforded according to the ability of the employer and the situation chosen"* | ~ Partly. This is the pro forma — the budget constraint that §2.2 shows really governs lease span |

And the famous triad, Book I ch. 3 [cited]:

> *"All these should possess strength, utility, and beauty. Strength arises from
> carrying down the foundations to a good solid bottom, and from making a proper
> choice of materials without parsimony. Utility arises from a judicious
> distribution of the parts, so that their purposes be duly answered, and that
> each have its proper situation. Beauty is produced by the pleasing appearance
> and good taste of the whole, and by the dimensions of all the parts being duly
> proportioned to each other."*

⭐ Note what *venustas* is actually defined as: **"the dimensions of all the
parts being duly proportioned to each other."** Beauty is defined as a
proportional relation, not as an aesthetic response. Vitruvius is asserting that
the third term is computable from the same data as the other two. Whether that
is *true* is a two-thousand-year argument; that it is a **specification** is not
in doubt, and it is the reason this material is usable at all.

### 5A.2 Symmetria and the module — a parametric system from the first century BC

**The move.** Fix one dimension. Derive everything else from it as a ratio. That
is the whole method, and it is identical in structure to
`MetalExtrusionMaker`'s `width` / `height` / `thick`.

For a temple the base unit is the **column diameter**. For a domus it is the
**atrium length**. For a basilica it is the **central span**. The unit changes
with the building type; the method does not.

**The body as the justification** (Book III ch. 1). Vitruvius derives the ratios
from the human figure, and gives them as explicit fractions of total height
[cited]:

```
  face (chin to hairline)             1/10 of total height
  chin to crown of head                1/8
  nape of neck to crown                1/8
  top of breast to hairline            1/6
  top of breast to crown               1/4
  foot                                 1/6
  forearm                              1/4
  width of breast                      1/4

  face subdivides in THIRDS:
      chin -> underside of nostrils        1/3 of face
      nostrils -> middle of eyebrows       1/3
      eyebrows -> hairline                 1/3
```

Plus the two geometric claims that became the Vitruvian Man [cited]: with the
navel as centre, a circle *"will touch his fingers and toes"*; and height equals
arm span, *"so that lines at right angles to each other, enclosing the figure,
will form a square."*

And the unit system itself is derived from the body — *"the measures necessarily
used in all buildings and other works, are derived from the members of the human
body, as the digit, the palm, the foot, the cubit"* [cited].

⭐⭐ **This is exactly Le Corbusier's move in the Modulor (§5.1), two thousand
years earlier, and the parallel is not a coincidence — Corbusier read
Vitruvius.** Both fix a human dimension, both derive a ladder of dimensions from
it, and **both over-claim universality from a single idealised male body.** The
critique in §5.1 of the Modulor applies verbatim to Book III ch. 1. The
*mechanism* is sound and reusable; the *justification* is not, and a generator
should take the first and drop the second.

**The intercolumniation set — a small generative vocabulary, already written
down** (Book III ch. 3). Five named spacings, each stated in column diameters
[cited]:

| Name | Intercolumniation | Vitruvius's own comment [cited] |
|---|---|---|
| **Pycnostyle** | 1½ diameters | thick-set |
| **Systyle** | 2 diameters | *"the distance between their plinths is then equal to their front faces"* |
| **Eustyle** | **2¼ diameters**, with the **centre bay 3 diameters** | his preferred type — *"well in respect of convenience, as of beauty and strength"* |
| **Diastyle** | 3 diameters | ⚠ *"the epistylia or architraves over the columns frequently fail, from their bearings being too long"* |
| **Araeostyle** | wider still, wooden architraves | *"clumsy, heavy roofed, low and wide"* |

⭐ **Five names, one number each, and one of them carries a structural warning.**
That is precisely the shape of vocabulary this project has now built four times
(metal sections, moulding elements, roof operators, sign classes). It ships as a
CSV with three columns: `name`, `spacing_diameters`, `centre_bay_diameters`.

⭐ And note the **eustyle exception**: the centre bay is wider than the others.
That single irregularity — a wider central intercolumniation to align with the
door — is the difference between a colonnade that reads as designed and one that
reads as extruded. It is a one-line rule with an outsized effect, and it belongs
in the façade generator immediately.

### 5A.3 The domus — a canonical plan sequence, and it is directly generatable

**The sequence.** The Roman atrium house is organised on a single axis, and the
order is fixed:

```
  street -> vestibulum -> fauces -> ATRIUM (impluvium) -> tablinum
                                       |                     |
                                  alae L + R            -> PERISTYLE -> hortus
```

with `cubicula` (bedrooms) opening off the atrium, `triclinia` (dining) and
`exedrae` off the peristyle, `culina` (kitchen) tucked in service space, and
`tabernae` (shops) fronting the street *outside* the house's own circulation
[cited].

⭐⭐ **This is the most directly generatable plan type in this entire
document**, and the reason is worth being precise about: it is not merely an
adjacency graph, it is **an adjacency graph with a total order along an axis**.
That collapses the whole partition problem (§6.5) from a packing to a
one-dimensional sequence with widths. There is no search. It is a scan.

```
  DOMUS_GENERATOR:
      axis        = the deep dimension of the lot
      sequence    = [fauces, atrium, tablinum, peristyle, hortus]
      for each element: width and depth from the ratio tables below
      side rooms  = attached to atrium or peristyle, MIRRORED about the axis
      terminate   = when the lot depth is consumed
```

**⭐ The proportion tables — and they are a BAND LOOKUP.** This is the finding
that makes the section worth its length. Vitruvius does not give one ratio for
the wings; he gives a **graduated table keyed to the atrium's length** [cited,
Book VI ch. 3]:

| Atrium length | Width of each **ala** |
|---|---|
| 30–40 ft | 1/3 of the length |
| 40–50 ft | 1 part of 3½ (= 2/7) |
| 50–60 ft | 1/4 of the length |
| 60–80 ft | 1 part of 4½ (= 2/9) |
| 80–100 ft | 1/5 of the length |

| Atrium width | **Tablinum** width |
|---|---|
| 20 ft | 2/3 of the width |
| 30–40 ft | 1/2 |
| 40–60 ft | 2/5 |

Tablinum **height** = *"one eighth part more than the breadth"* (i.e. 9/8 of its
width). **Fauces** width = the tablinum width less one third, in smaller houses;
one half, in larger ones [cited].

⭐⭐ **That is the same data structure as `SignLibrary`'s SizeClass lookup and
the corner-treatment-by-angle-band in `footprint_plan.md`.** A graduated table
keyed to a size band, with the ratio *decreasing* as the building grows — which
is exactly the non-linear scaling that a single constant ratio cannot express
and that makes big buildings look wrong when generated naively. **Vitruvius
solved the "one ratio does not scale" problem by tabulating it.** So should we,
and the table already exists.

**The atrium's own proportions** — three permitted length:width ratios [cited]:

```
  5 : 3       (1.667)
  3 : 2       (1.5)
  1 : sqrt(2) (1.414)   "a square being described whose side is equal to the
                         width, a diagonal line is drawn therein, the length of
                         which is to be equal to the length of the atrium"
```

Height to the underside of the beams = **the length less one quarter** (3/4 L).
The **compluvium** (the roof opening) is *"not to be less than a fourth nor more
than one-third of the width"* [cited].

⭐ Note the third atrium ratio is **1:√2** — the same irrational that appears as
Palladio's third room proportion (§6.1) seventeen centuries later, described in
the same way: as the diagonal of a square. **That is the transmission line made
visible in a single number.**

**The peristyle** [cited]: *"transversely one third part longer than across"*
(so 4:3); columns as high as the width of the portico; intercolumniations
*"not less than three nor more than four diameters."*

**The five kinds of atrium** — and they are a *roof* classification, not a plan
one [cited]:

| Type | What distinguishes it |
|---|---|
| **Tuscan** | beams span the court with trimmers; valleys run from the internal angles — no columns |
| **Tetrastyle** | columns under the beams at the four angles, *"which give strength"* |
| **Corinthian** | more columns; the beams are detached from the walls and rest on columns |
| **Displuviate** | water is thrown **off outwards**, not into the impluvium |
| **Testudinate** | fully roofed, no opening — *"used when the span is not great"* |

⭐ **This is a span-driven taxonomy wearing a stylistic name**, and it maps
directly onto §2.7's logic: as the court gets wider, you add columns, and when it
is narrow enough you can simply roof it. Tuscan → tetrastyle → Corinthian is an
increasing-span sequence. The generator should select the type **from the span**,
not from a style menu — and then let a style parameter override.

**Orientation and season** (Book VI). Vitruvius assigns rooms to compass
directions by use [cited]:

```
  winter triclinia + baths   -> winter west   (afternoon light wanted)
  spring / autumn rooms      -> east          (cool when wanted)
  summer rooms               -> north         ("that aspect ... is always cool")
  bedrooms and libraries     -> east          ("their purposes require the
                                               morning light")
```

⭐ **That is a room-to-orientation constraint table, and it is directly usable.**
It is also the *only* place in this entire document where a classical source and
a modern performance requirement (§2.2's daylight rules, §5.4's SF Federal
Building) are saying the same thing. Orientation-aware room assignment is a
genuinely reusable constraint — and note that House-GAN's datasets famously do
*not* carry compass orientation (§6.3), which is one of the things MSD was built
to fix.

**Villa urbana / villa rustica.** The split is programmatic: the *urbana* is the
owner's residence, planned like a town house with atrium and peristyle; the
*rustica* is the working farm — quarters, presses, stores, stalls — planned for
production. Many villas contain both, adjacent and distinct.
⚠ **[UNVERIFIED]** — I could not fetch a source that states the distinction with
citable authority within the remaining budget. The *generative* consequence
holds regardless and is worth stating: **a villa is two adjacency graphs joined
at one point**, one composed on the axial sequence above and one packed for
function. That is the same served/servant split as §2.6, at building scale.

### 5A.4 The basilica — a SECTION type that determines the plan

This is the part with the longest reach, and the brief is right that it is a
section problem wearing a plan's clothes.

**The type.** A long hall with a taller central nave flanked by lower aisles, so
that the difference in height opens a band of **clerestory** window above the
aisle roofs. That is the whole idea: **light a deep plan from above the middle,
because you cannot light it from the sides.** It is §2.2's problem, solved in
section rather than by making the plan narrower.

**Vitruvius's proportional rules** (Book V ch. 1). The following were fetched
from **two independent translations and agree** — the LacusCurtius text and
Morgan's 1914 via Perseus:

| Rule | Value [cited, cross-checked] |
|---|---|
| Basilica width : length | *"not less than one third nor more than one half of their length"* |
| Aisle width | *"limited to one third of the breadth which the open space in the middle is to have"* |
| Column height | equal to the breadth of the portico (aisle) |
| Upper-tier columns | *"one fourth smaller than those of the lower"* |
| Parapet (pluteus) between upper columns | *"one fourth lower than the columns of the upper tier"* |

And the stated *reason* for the parapet, which is a wonderful piece of
programmatic honesty [cited]: *"so that people walking in the upper story of the
basilica may not be seen by the business men."* A dimension derived from a
sightline. That is a constraint a generator can actually evaluate.

**His own basilica at Fano** [cited, both translations agree]:

```
  central hall     120 ft long  x  60 ft wide
  aisles           20 ft broad
  lower columns    50 ft high (with capitals), 5 ft thick
  first pilasters  20 ft high, 2½ ft broad, 1½ ft thick
  upper pilasters  18 ft high, 2 ft broad, 1 ft thick
```

⭐⭐ **Check Fano against his own rules and it does not comply.** [derived]:

- Width : length = 60 : 120 = **1 : 2**. ✅ At the extreme permitted limit
  ("not more than one half").
- Aisle : central breadth = 20 : 60 = **1 : 3**. ✅ Exactly the rule.
- Column height should equal the aisle breadth = 20 ft. **The columns are 50 ft.**
  ✖ **Two and a half times the rule.**

He also states he **omitted the two central columns on one side** so that *"the
view of the pronaos of the temple of Augustus may not be obstructed"* [cited] —
a deliberate break in the colonnade rhythm for a sightline to a neighbouring
building.

**That is the single most useful thing in §5A for art direction**, and it should
be said plainly:

> **The canonical source breaks its own rules, in its own worked example, for
> reasons it names — and the reasons are contextual (a view, a sightline), not
> aesthetic.** A generator that applies classical rules uniformly is *more*
> rigid than Vitruvius was. The deviations should be modelled as a first-class
> feature driven by site conditions, not as noise.

**Structural necessity vs convention — the split the brief asks for:**

| Feature | Class | Why |
|---|---|---|
| Nave taller than aisles | **NECESSITY** if you want top-light into a deep plan. There is no other way to do it before electric light | |
| Aisles present at all | **NECESSITY** — they are what buttress the nave walls and support the clerestory | |
| Clerestory band | **NECESSITY**, and it is the entire point of the type | |
| Aisle = 1/3 of nave width | **CONVENTION.** A proportional preference; structurally any ratio works | |
| Width 1/3 to 1/2 of length | **CONVENTION**, and a broad band at that | |
| Upper columns 1/4 smaller | **CONVENTION**, justified by analogy to tapering tree trunks [cited] — an aesthetic argument dressed as a natural one | |
| Two-tier colonnade | **CONVENTION.** Fano's 50 ft single order does the same job | |
| Apse at the end | **CONVENTION** in the Roman basilica; it becomes *programmatic* in the Christian one (the altar) | |
| Parapet at 3/4 of upper column height | **CONVENTION**, from a stated sightline. Recomputable if the sightline changes | |

**Where the section recurs — and this is the payoff.** The same section solves
the same problem every time deep floor plates need daylight without side
windows:

| Building | Nave | Aisles | Clerestory | Note |
|---|---|---|---|---|
| Roman basilica | central hall | flanking, lower | yes | the original |
| Christian basilica / church | nave | aisles | yes | ⭐ programme changes, section does not; the apse becomes the sanctuary and the axis becomes liturgical |
| Mill / weaving shed | central bay | side bays | yes | often becomes a **sawtooth** instead — same problem, north-light solution |
| Train shed | platforms | — | ridge glazing | span dominates; the aisles vanish |
| Market hall | central avenue | stalls | yes | |
| **Sawtooth factory** | repeated | — | monitor roof | ⭐ **already in the roof work.** The sawtooth is the basilica section repeated `n` times instead of once, with the clerestory turned to face north |
| **Atrium office building** | the atrium | office floor plates | glass roof | ⭐⭐ **A basilica section with the clerestory replaced by a glazed roof over the whole nave.** It exists for exactly the §2.2 reason: it lets a deep plate have a second daylight face |

⭐⭐ **The atrium office is the connection that makes this section pay for
itself.** §2.2 showed that Alliance Kai achieves 91% of area within 20 ft of
glass at a 42 ft maximum depth *because* the depth is measured to a courtyard as
well as to the street. That courtyard, roofed, is the basilica nave. **So the
classical section is a live operator in the commercial generator, not a period
feature**, and it should be implemented as one:

```
  OP-BASILICA  TOP_LIT_SPINE

    Given a plate deeper than 2 x lease_span:
        carve a central void of width w along the long axis
        raise the void's roof above the flanking floors by h
        glaze the difference                  -> clerestory
        or glaze the void's roof entirely     -> atrium

    Consequences, all derived:
        - lease_span is now measured to the void as well as to the perimeter
        - the S1 daylight score (§4.3) jumps, and by a computable amount
        - egress gains a second face; travel distances shorten (§6.6)
        - floor plate efficiency FALLS (the void is not lettable)  -> §2.4

    Parameters:  w (from the daylight requirement),
                 h (from the clerestory band height),
                 n (1 = basilica/atrium, n>1 = sawtooth)
```

**That is one operator with three parameters that generates the Roman basilica,
the church, the market hall, the sawtooth factory and the atrium office.** It
belongs beside the four roof operators, and it is the plan-side answer to the
brief's standing preference for a small generative vocabulary.

### 5A.5 Prescription vs what was actually built — and what I could not verify

This is the fact-versus-art-direction split the brief asks for, and honesty
requires being blunt about the limits of what I could confirm.

**What is certain from the text alone.** Vitruvius's own worked example at Fano
violates his own column-height rule by a factor of 2.5 (§5A.4, [derived] from
figures he supplies). So the prescriptions were not treated as binding **by
their author**.

**What is widely held but which I could not source within budget, and therefore
mark [UNVERIFIED]:**

- That excavated Pompeian and Herculanean houses **frequently do not match**
  Vitruvius's atrium ratios or his alae/tablinum bands, and that many houses
  have no tablinum, no peristyle, or an atrium of a proportion he does not list.
- That the canonical fauces→atrium→tablinum→peristyle sequence describes a
  particular class of elite house at a particular date, and that the majority of
  Roman urban dwellings — apartments (*insulae*), shop-houses, and irregular
  infill — do not follow it at all.
- That the *pes monetalis* (Roman foot) is approximately 296 mm.

⚠ **These are exactly the kind of recalled numbers this project treats as
defects, so they are marked and not used.** They are, however, the *right*
questions, and §9 lists the works to pull. The generative consequence, if they
hold, would be significant and is worth stating conditionally:

> If the canonical domus is an elite minority type rather than the norm, then
> generating a Roman quarter entirely from the axial sequence would be as wrong
> as generating an American suburb entirely from Palladian villas. **The
> sequence should be one entry in a catalog with a low population weight, not
> the default.**

⚠ Note also that a search budget limit meant the *De architectura* text was read
in **translation only**, and only one passage (the basilica) was cross-checked
against a second translation. Translations of Vitruvius differ materially —
Gwilt's 1826 and Morgan's 1914 render the same proportional clauses with
different words. **Any figure from §5A that is going to drive geometry should be
checked against the Latin.**

### 5A.6 Where it still shows up — concretely, and where it is only cited

**Where the classical plan is genuinely *used* (the structure does work):**

| Instance | What survives |
|---|---|
| **The Beaux-Arts *parti*** | The axial sequence itself: a marche (route) through a hierarchy of spaces, symmetrical about a principal axis, with subsidiary cross-axes. ⭐ This is the domus sequence generalised to any programme, and it is a **graph with an order** — the same collapse from packing to scan noted in §5A.3 |
| **The museum enfilade** | Palladio's stage-7 door-alignment rule (§6.1), which is Vitruvius's *"void over the void"* — an aligned door sequence produced by alignment rather than drawn. The visitor route *is* the plan |
| **The bank hall** | A basilica: top-lit central volume, lower flanking service, an apsidal or terminal focus. The section is doing the work, not the ornament |
| **Courthouse and civic planning** | Axial approach, raised podium, a principal volume with a clear terminal focus. The sequence is legible from the plan alone |
| **⭐ The atrium office building** | §5A.4. A basilica section with the clerestory replaced by a glazed roof, for a daylight reason that is measurable (§4.3, S1) |
| **The sawtooth factory** | Already in the roof work. `n > 1` in OP-BASILICA |

**Where it is only *cited* — ornament applied to a plan organised on other
grounds.** A generator that cannot tell the difference produces pastiche, so
name the tell:

> **The test is whether removing the classical language would change the plan.**
> If the columns come off and the plan is unaffected, the classicism is
> applied. If the plan collapses, it is structural.

By that test: a 1920s American bank with a giant order across a deep,
efficiently-planned commercial floor plate is **citation** — the portico is a
frontispiece on a spec plan. A Beaux-Arts museum whose whole route depends on
the axis is **use**. A postmodern pediment on a curtain-walled tower is
citation, and self-consciously so.

⭐ **The implementation consequence is a single flag**, and it should exist from
the start:

```
  classical_mode ∈ { STRUCTURAL, APPLIED }

    STRUCTURAL : the axial sequence generates the plan; the order sets the
                 grid; bay spacing comes from the intercolumniation table
    APPLIED    : the plan is generated by the ordinary commercial path
                 (§7 Phases 1-4) and a classical façade vocabulary is
                 attached to the street-facing edges only
```

Both are correct buildings. Producing them by the same path is what produces
pastiche.

### 5A.7 Rule / preference / signature — the classical row

| Statement | Class |
|---|---|
| Derive all dimensions from one module by ratio | **RULE** — a method, and it is the method this project already uses |
| A deep plan can only be top-lit by raising the middle above the flanks | **RULE** — physics, and the origin of the whole basilica lineage |
| Wider court ⇒ more columns; narrow court can simply be roofed | **RULE** — span |
| A proportional ratio must be **graduated by size**, not constant | ⭐ **RULE**, and the most transferable single idea in §5A |
| The eustyle wider centre bay | **PREFERENCE**, with a functional reason (the door) |
| Aisle = 1/3 of nave; upper columns 1/4 smaller; parapet at 3/4 | **PREFERENCE** — proportional convention, not necessity |
| The three atrium ratios (5:3, 3:2, 1:√2) | **PREFERENCE** — a catalog |
| Room orientation by season | **PREFERENCE** with a physical basis — climate-dependent, so a *regional* catalog entry |
| The fauces→atrium→tablinum→peristyle sequence | **SIGNATURE** of one house type in one culture at one period. ⚠ Not the Roman norm — see §5A.5 |
| Deriving the human-body fractions as universal proportion | **SIGNATURE** — and, like the Modulor, an over-claim (§5.1) |

---

## 6. The computational literature

### 6.1 Shape grammars, and the Palladian grammar in particular

**Origin.** Stiny, G. and Gips, J., *"Shape Grammars and the Generative
Specification of Painting and Sculpture"*, in *Information Processing 71*,
North-Holland, 1972, pp. 1460–1465 — presented at IFIP Congress 71, August 1971
[snippet: bibliographic details from a search summary; I did not fetch the paper
itself]. A shape grammar is a production system over *shapes* rather than
symbols: rules of the form `α → β` that match a labelled sub-shape and replace
it. The crucial difference from a string grammar is that matching is
**geometric and under transformation** — a rule fires wherever its left side
appears at any position, rotation and scale, which is why shape grammars find
sub-shapes that were never explicitly drawn.

#### ⭐⭐ The Palladian grammar — read in full, and it is the model to copy

**Stiny, G. and Mitchell, W. J., "The Palladian grammar", *Environment and
Planning B*, 1978, vol. 5, pp. 5–18.** DOI 10.1068/b050005. ✅ **Read in full**
— everything in this subsection is [cited] from the paper itself.

This is the closest existing thing to what this project wants, and it deserves
the detail, because the *architecture of the grammar* is more instructive than
the fact that it exists.

**The eight stages, in order and verbatim from the paper:**

```
  (1) grid definition
  (2) exterior-wall definition
  (3) room layout
  (4) interior-wall realignment
  (5) principal entrances — porticos and exterior-wall inflections
  (6) exterior ornamentation — columns
  (7) windows and doors
  (8) termination
```

**Rule count: 72.** Rules are numbered 1 through 72 across the eight stages. So:
*the entire ground-plan language of Palladio's villas is 72 rules in 8 stages.*
That is the scale the AssetBash plan vocabulary should aim at — the same order
as the ten moulding elements and the four roof operators.

**The dimensional system, and it is beautifully small:**
- Unit of measure = **one Vicentine foot**.
- **Standard ground-floor wall thickness = 2 feet.** So the unit is *half a
  wall thickness*. Every dimension in the system is expressed in
  wall-thickness halves.
- *"Rooms almost invariably have dimensions that are small integer multiples of
  the unit foot."*

**Stage 1 — the grid, which is the whole thing.** The grid is a **labelled
rectangular 'tartan' grid** with bilateral symmetry about a north–south axis.
Formally: a **(2m+1) × n array** of variously-dimensioned rectangles, `m > 0`,
`n > 0`. **Most of Palladio's villa plans are based on 5 × 3 grids.** The
central column of rectangles is bisected by the axis; each rectangle left of the
axis has a mirror right of it; **adjacent rectangles are separated by a fixed
distance of one wall thickness** and their parallel edges are the same length.

⭐ *That last clause is the definition of a tartan grid and it is the single most
transferable idea in the paper.* The grid is not a set of lines, it is an
**alternating sequence of room-bands and wall-bands**. Rooms sit in the wide
bands, walls in the narrow ones. The plan is then dimensionally consistent by
construction, because wall thickness is a band rather than a subtraction.

And the paper is explicit about why this ordering matters:

> *"Once a grid has been generated, it constrains all subsequent applications of
> rules in such a way that their associated variables are forced to assume the
> correct values."*

**That is the answer to the whole layering question in §1.** Generate the grid
first and everything downstream is forced. Generate rooms first and you spend
the rest of the pipeline fighting inconsistency. It is the same lesson
`footprint_plan.md` learned about classification-before-treatment.

**The seven room proportions**, quoted by Stiny & Mitchell from Palladio
(page 27 of the Ware translation) — the parametric catalog:

> *"The most beautiful and proportionable manner of rooms, and which succeed
> best, are seven, because they are either made round (tho' but seldom) or
> square, or their length will be the diagonal line of the square, or of a
> square and a third, or of one square and a half, or of one square and two
> thirds, or of two squares"*

As numbers:

```
  1 : round
  2 : 1 : 1        square
  3 : 1 : sqrt(2)  the diagonal of the square          (1.4142)
  4 : 1 : 4/3      "a square and a third"              (1.3333)
  5 : 1 : 3/2      "one square and a half"             (1.5)
  6 : 1 : 5/3      "one square and two thirds"         (1.6667)
  7 : 1 : 2        "two squares"
```

**Seven values. That is the entire room-proportion vocabulary of a canonical
architectural language.** Ship it as a CSV column.

**Stage 3 — room shapes.** Interior spaces may be **rectangular, I-shaped,
T-shaped, or +-shaped**, formed by *recursively concatenating* cells of the wall
pattern. Two invariants: rule application preserves the plan's symmetry, and
**a plan can have at most one non-rectangular space, which must be bisected by
the axis.**

⭐ That constraint — *at most one non-rectangular room, and it must be on the
axis* — is a fine example of a rule that is trivially checkable, cheap to
enforce, and does enormous work in making output read as designed rather than
random. It is exactly the kind of invariant the AssetBash plan generator should
carry.

**Stage 7 — the enfilade, derived not modelled.** Windows are inserted one per
non-axial exterior wall segment. Windows in parallel wall segments are inserted
*together* and linked by a marked line segment. **Interior doors may only be
placed where such a linking segment cuts a wall.** The result, in the paper's
words, is *"the characteristic enfilade"* — the aligned door sequence —
produced as a *consequence* of window placement rather than being drawn.
Palladio's own statement of the goal is quoted: *"that the void may be over the
void, and the solid upon the solid, and all face one another."*

⭐⭐ **This is the door-placement algorithm to steal.** Doors are not placed;
they are *induced by alignment*. It is one rule and it generates a recognisably
classical circulation pattern.

**Stage 8 — termination as a correctness proof.** The termination rules erase
labels, but with a condition: the marked segments around a plan can be erased
**if and only if** there is an interior wall segment associated with them —
which forces the grid to have been minimal. The paper's conclusion:

> *"Only plans which have been correctly generated in the previous seven stages
> can have all of their labels erased."*

⭐ **The grammar terminates only on valid plans.** Termination *is* validation.
A partially-labelled result is a detectable failure. Any AssetBash plan grammar
should adopt this: carry labels through generation, and treat leftover labels as
an error state rather than trying to validate finished geometry after the fact.

**Biaxial villas** (the Villa Rotonda) are handled by taking the uniaxial rules,
locating an east–west axis orthogonal to the north–south one, and **reflecting
every rule about it** — plus rules replacing an axis-centred square with a
circle of matching radius. The two-axis language is a *derived* grammar, not a
second one.

**The honest limits, stated by the authors.** They say the corpus choice is
arbitrary; the *Quattro Libri* drawings contain "numerous small errors and
inconsistencies"; constructed buildings deviate from the drawings; and what
counts as a trivial variation is a judgement call. The grammar covers **ground
plans only** — not façades, and not a full treatment of Palladio's proportional
system.

**And the limit they do not state, which matters most here:** the grammar
*describes* Palladio. It does not generalise. There is no Palladian grammar for
a supermarket. See §8.

### 6.2 Space syntax

Hillier, B. and Hanson, J., *The Social Logic of Space*, Cambridge University
Press, 1984. The formulas as implemented are in §4.2, taken verbatim from a
source I read. What the theory contributes beyond the arithmetic:

- **Configuration, not geometry, is the object of study.** Two plans with
  identical room sizes and different door positions are different buildings.
  That is precisely the distinction a procedural system needs and usually lacks.
- **The justified graph** as a visual signature of plan type (§4.1).
- **Integration is normalised**, so a studio and a palace are comparable — that
  is the `D_n` term. It is what makes the measure usable as a score.
- **Intelligibility** — the correlation between local connectivity and global
  integration across a plan. High intelligibility means you can infer where you
  are in the whole from what is visible locally. ⚠ I did not read a primary
  source for the exact definition; treat as **[UNVERIFIED]** and check before
  implementing.

**What it is good for here:** scoring (§4.3). **What it is not good for:**
generation. Space syntax has no production rules. It measures.

### 6.3 Learned plan generation — what it achieves and where it fails

Access marks in this subsection: ✅ = the paper's abstract and/or body was read;
⚠ = citation verified but text not retrieved; 🔒 = paywalled, listed in §9.

#### What the main systems actually do

| System | Venue | Input | Output | Trained on |
|---|---|---|---|---|
| **House-GAN** (Nauata et al.) | ECCV 2020 | bubble diagram (room graph) | **axis-aligned bounding boxes**, one per room | LIFULL, 117,587 plans |
| **House-GAN++** (Nauata et al.) | CVPR 2021 | bubble diagram + previous layout | iteratively refined layout | **RPLAN**, 60k |
| **Graph2Plan** (Hu et al.) | SIGGRAPH 2020 | building boundary + room counts | **retrieves** a real plan + graph from RPLAN, then refines | RPLAN, 80k |
| **HouseDiffusion** (Shabani et al.) | CVPR 2023 | bubble diagram | **1D polygonal loops** per room *and per door*; non-Manhattan; exact corner counts | RPLAN, 60k |
| **Raster-to-Vector** (Liu et al.) | ICCV 2017 | a raster plan image | junctions → **integer programming** → walls/doors/icons | LIFULL |

Two are worth understanding in detail, because the *representation choice* is
the transferable part:

- **HouseDiffusion represents a room as a closed polygonal loop and denoises the
  corner coordinates**, with a discrete objective that snaps the result to
  parallelism, orthogonality and shared corners. That is a procedural-friendly
  representation, and the snapping objective is a good idea regardless of the
  learning: **generate loosely, then snap to alignment invariants.**
- **Graph2Plan is retrieval-first.** It looks up a real plan and adapts it to a
  boundary. ⭐ **That is the catalog pattern this project already uses**,
  arrived at independently by a SIGGRAPH paper. It is also an honest admission
  that plan *design* is hard and plan *adaptation* is tractable.

#### ⛔ Where they fail — and the critique literature is strong

**(a) They are not buildable, and the state-of-the-art authors say so
themselves.** Lara et al. (Findings of ACL 2026) state that House-GAN and
House-GAN++ *"only condition on a bubble diagram and cannot impose other forms
of constraints,"* and that outputs are *"scale-invariant (i.e., not metric) and
thus cannot be used directly in any downstream task"* [✅ read]. Their own
Limitations section names what is unmodelled: *"circulation, egress,
accessibility, daylight, structural constraints, and local building codes"* —
and adds *"strong performance on our metrics should not be interpreted as
evidence of code compliance or construction readiness."*

House-GAN's own stated limitations, verbatim [✅ read]: *"A node property does
not have a room size; A room shape is always a rectangle; and An edge property
(i.e. room adjacency) does not reflect the presence of doors."* **No walls, no
doors, no metric scale.** That is not a floor plan; it is a bubble diagram
rendered as boxes.

**(b) Single typology, and worse, single *region*.** van Engelenburg et al.
(ECCV 2024, the MSD dataset paper) [✅ read]: today's large datasets
*"predominantly feature simple floor plan layouts, typically representing
single-apartment dwellings only"*, and RPLAN and LIFULL are *"axis-aligned and
entirely Manhattan-shaped layouts, which is at odds with realistic dwellings"*.
Neither provides compass orientation, *"while the direction of the sun is a
critical feature in environmental design."*

⭐⭐ **The finding that should end any thought of using these datasets as ground
truth for "how buildings are": RPLAN contains ~70% near-duplicates and LIFULL
~50%.** The effective dataset sizes are a fraction of the headline numbers. On
the MSD benchmark House-GAN++ scores 11.6 MIoU / 64.2 compatibility, and the
paper concludes the problem *"invites researchers to rethink current methods."*

**(c) Cross-domain generalisation fails by an order of magnitude.** Ospici et
al. (2026) tested RPLAN / MagicPlan / Swiss Dwellings transfer and found SOTA
models *"highly sensitive to domain shift, with up to an order of magnitude
performance degradation when transferred across domains"* [✅ read]. The failure
is bidirectional.

**(d) Even the ground truth is not code-compliant.** GreenPlanner (2025)
audited its training plans against national residential standards and found
**only 37.4% fully comply** [✅ read].

**(e) ⭐ The evaluation is the weakest part of the field.** This is the most
important thing to know, because it means the reported numbers should not be
taken at face value:

- FloorPlan-LLaMa (ACL 2025) [✅ read]: *"existing evaluation methods for floor
  plan generation rely mainly on statistical metrics like FID, GED, and PSNR,
  which often fail to evaluate using domain knowledge. As a result, even
  high-performing models on these metrics struggle to generate viable floor
  plans in practice."*
- Jang, Roh & Lee (*Automation in Construction* 174:106174, 2025), a PRISMA
  review of **161 journal papers, 2014–2024** [✅ abstract read; 🔒 full text]:
  *"comparative evaluation was most utilized (60.9%) supported by subjective
  assessment by authors (34.2%) and third parties (17.4%)."* **A third of the
  field grades its own output subjectively.** Also: AI is used in schematic
  design in 68.94% of papers, *"while later phases remain underexplored"* — the
  buildability gap in one number.
- Stoppani et al. (2026) [✅ read]: *"naively optimizing for standard realism
  metrics is counterproductive, as it pushes the model towards overfitting and
  mode collapse."*
- On the "realism user study" specifically: **House-GAN used 22 judges,
  House-GAN++ 20, HouseDiffusion 10 judges making 15 comparisons each.** No
  inter-rater reliability, no power analysis and no preregistration are
  reported. House-GAN++ additionally meta-optimises its refinement schedule
  against the metric it reports. **A search for a published replication or
  reproducibility study of House-GAN / House-GAN++ found none** — that is a
  genuine gap, and it is reported here as a gap rather than dressed up as
  evidence.

#### 🔴 The licensing blocker, which is the practical finding

This matters more for AssetBash than any accuracy figure, because AssetBash
ships.

- **RPLAN** (Wu et al., SIGGRAPH Asia 2019) — 80,788 plans, 256×256
  four-channel images over an **18 m × 18 m** square, 13 room types, filtered
  from ~120K real-world plans by USTC with **Kujiale** (a commercial Chinese 3D
  interior platform). Access is a Google Form whose required checkbox reads,
  verbatim: *"I will not redistribute the dataset in any way and in any format…
  I agree that the data will be used only for non-commercial research and
  academic purposes."* ⚠ **That restricts the *use*, not only redistribution**
  — it plausibly reaches a model trained on it and then shipped. ⛔ **Unusable
  for a commercial AssetBash release.**
- **LIFULL HOME'S** — via NII/ROIS IDR. 5.33 M rental listings; the usable
  high-resolution floor-plan images (5.31 M files, ~140 GB) are behind a
  *second* application. Eligibility: *"Only researchers belonging to a
  university or a public research institution can apply."* The Japanese-language
  page states outright that private-company personnel cannot use it. Requires a
  wet-signed consent form from *"a dean of a school or higher"* with official
  seal, annual utilisation reports, and advance approval for any
  internet-accessible demo. ⚠ **Jordan's USC affiliation makes this
  *possible*, but the academic-use restriction makes anything shipped from it a
  problem.**
- ✅ **The three that are actually usable:**
  - **MSD** (van Engelenburg et al., ECCV 2024) — **CC BY 4.0**. 5,372 plans /
    18.9K apartments / 163.5K areas, from Swiss Dwellings. ⭐ **Includes
    load-bearing walls and columns.** The only one of these with a structural
    layer, which makes it the right benchmark for the FRAME/INFILL split.
  - **ResPlan** (Abouagour & Garyfallidis, 2025) — **CC BY 4.0**. 17,000
    residential plans, **vector geometry with metric coordinates in metres**,
    walls / doors / windows, a 17-class space taxonomy, and four typed edge
    kinds (`via_door`, `adjacency`, `direct`, `via_window`); 8.1 functional
    rooms and 9.2 graph nodes on average. ⭐⭐ **This is the one to use.** Typed
    edges plus metric scale is exactly the adjacency-graph catalog that §3.2
    says must be authored — here it is, already authored, 17,000 times, under a
    licence that permits shipping.
  - **CubiCasa5K** (Kalervo et al., SCIA 2019) — open on GitHub. 5,000 samples,
    80+ object categories, dense polygon annotation, from ~15,000 mostly
    **Finnish** plans. Small and regionally narrow, but clean.

⭐ **Recommendation: do not train anything.** Mine ResPlan and MSD for the
adjacency-graph catalog and the room-proportion distributions, and generate with
rules. That gets the empirical grounding without the licence problem, the
generalisation problem, or the evaluation problem — and it fits the pattern this
project has now used successfully four times.

### 6.4 Straight skeleton and medial axis for plan decomposition

The roof work already establishes the weighted straight skeleton
(`roof_typology_and_math.md` §1). For plans it does two additional jobs.

**(a) Corridor and circulation extraction.** The medial axis of a corridor
region is its centreline. For indoor navigation this is standard practice: the
medial axis *"is an effective way to represent the paths of indoor spaces"*,
being consistent with how people describe routes [snippet]. The straight-skeleton
variant is preferred in implementation because it is piecewise linear — the
medial axis of a polygon *"may involve parabolic curves"* wherever a reflex
vertex is involved [snippet], and parabolic arcs are a nuisance in a SOP network.

⭐ **The reverse direction is the useful one for generation.** Do not extract a
corridor from a plan; **place a skeleton and inflate it into a corridor.** Given
the footprint and the core position(s):

```
  1. compute the straight skeleton of the footprint
  2. keep the skeleton edges connecting the core(s) to the extremities
  3. offset that path by corridor_width       ->  the corridor region
  4. the remainder is the leasable / partitionable residue
```

That is a four-step corridor generator that works on any footprint including
non-convex ones, reuses machinery the roof work already needs, and produces
exactly the double-loaded corridor of §2.5 when the footprint is a bar — without
the corridor ever being modelled as such.

**(b) Rectangle decomposition for the space-syntax oracle.** Jiang & Zhang's
SSIO decomposes each room's walkable core into maximal axis-aligned rectangles
by greedy cover (§4.4) [cited]. This is necessary because integration must be
computed on a graph whose nodes have comparable size — one node per room would
weight a corridor and a closet equally, and would make integration a function of
how the plan happened to be labelled.

### 6.5 Rectangular dualisation and VLSI floorplanning

This is the branch of the literature that starts from *an adjacency graph the
designer authored* and produces geometry — which is the opposite direction from
everything in §6.3, and much more useful here.

#### The theorem

A **rectangular dual** of a plane graph is a partition of a rectangle into
rectangles, one per vertex, such that two rectangles share a boundary segment
exactly when their vertices are adjacent. The classical characterisation:

> **Koźmiński & Kinnen.** A *nonseparable* plane graph with all interior faces
> triangular admits a rectangular dual **if and only if** it has **at most four
> corner-implying paths (CIPs)** and **no separating triangle**.

Definitions [cited, from Kumar & Shekhawat's free restatements]:
- **Separating triangle** (= *complex triangle* in the Bhasker–Sahni
  vocabulary) — a 3-cycle with vertices both inside and outside it.
- **Shortcut** — an edge joining two vertices of the outermost cycle that is not
  itself on that cycle.
- **CIP** — a path along the outermost cycle containing no vertices of a
  shortcut other than its endpoints.

⭐ **The "at most four CIPs" condition is just: a rectangle has four corners.**
No more than four boundary paths may each demand one. That is a satisfyingly
physical reading of a graph-theoretic condition.

Equivalent modern phrasing [snippet]: a planar triangulation with a designated
degree-4 outer face is rectangularly dualisable exactly when it is 4-connected,
i.e. has no separating triangle.

**Complexity:** Koźmiński & Kinnen gave an **O(n²)** algorithm (1985); Bhasker &
Sahni brought both the existence check (1987) and the construction (1988) to
**O(n)**. All four papers are paywalled — §9.

⚠ **One correction worth carrying:** Kumar & Shekhawat explicitly claim a
**counterexample to Koźmiński & Kinnen's stated conditions for the *separable*
case**. The nonseparable theorem stands; the separable extension in the 1985
paper does not. Their Theorem 2.2 gives corrected conditions for separable
graphs (no separating triangle; block-neighbourhood graph is a *path*; endpoint
blocks have ≤2 critical CIPs; other blocks none) [cited].

#### The consequence for a plan generator, stated plainly

> **Not every adjacency graph an architect can draw is realisable as a
> rectangular plan.**

That is the single most important thing in this subsection, and it is *good*
news, because it means an authored adjacency-graph catalog (§3.2) can be
**validated at authoring time** in linear time, before it ever reaches geometry.
A graph with a separating triangle simply cannot be laid out in rectangles —
and there are published transformation algorithms that repair such graphs
(Kumar & Shekhawat, *TCS* 871, 2021, paywalled).

#### VLSI floorplan representations, and which one to use

| Representation | Source | Represents | Verdict for AssetBash |
|---|---|---|---|
| **Slicing tree / normalised Polish expression** | Wong & Liu, DAC '86 | **Slicing floorplans only.** Binary tree, internal nodes `*` (vertical cut) / `+` (horizontal cut), leaves = rooms; postorder = Polish expression; *normalised* = no consecutive identical operators, giving a 1:1 encoding | ⭐ **Start here.** A slicing tree *is* a recursive subdivision — exactly what a Houdini for-each/subnet structure already is. Cheap, parameterisable, artist-legible. ⛔ **Cannot express a pinwheel** (four rooms rotating around a fifth), which is a common real motif |
| **Sequence pair** | Murata et al., IEEE TCAD 15, 1996 | **Non-slicing** — all packings. A pair of permutations jointly encoding left-of/below relations | Handles pinwheels. Decode is a longest-path computation. Solution space (n!)²; the mapping to geometry is indirect and hard to give artists handles on |
| **O-tree** | Guo, Cheng & Yoshimura, DAC '99 | Non-slicing but only *admissible* (left/bottom-compacted) placements; n(2+⌈lg n⌉) bits | Compaction means you cannot hold a room at an arbitrary position |
| **B\*-tree** | Chang et al., DAC '00 | Non-slicing, admissible. Ordered binary tree; search/insert O(1), delete O(n). Reported ~4.5× faster and ~60% less memory than O-tree | Best speed/expressiveness trade if you need non-slicing with fast perturbation |
| **Corner block list (CBL)** | Hong et al., ICCAD 2000 | Non-slicing **mosaic** floorplans — no empty space, no overlap. Triple (S, L, T); **linear-time decode** | ⭐ **Mosaic is exactly the architectural condition**: every square metre inside the envelope belongs to some room. Arguably the most architecturally natural of the non-slicing family |

⭐ **The design decision, stated for the record: slicing vs non-slicing is the
whole choice.** A slicing tree gets a clean recursive Houdini implementation and
covers everything a corridor-spine plan needs. You need non-slicing (CBL or
B\*-tree) the moment you want a pinwheel core, wrapped circulation, or an
L-shaped service block. **Rectangular dualisation sits above both** — it is the
only route that starts from a *designer-authored adjacency graph* rather than
from a packing.

⚠ Solution-space size figures for these representations (the usual
`O(n!·2^{3n}/n^{1.5})` family) are **[UNVERIFIED]**.

#### The modern architectural line — Shekhawat / GPLAN

**Krishnendra Shekhawat (BITS Pilani, Mathematics)** is the centre of gravity,
and this work is the closest published thing to what this project wants on the
partition side.

- **GPLAN** — Shekhawat, Upasani, Bisht & Jain, *"GPLAN: Computer-Generated
  Dimensioned Floorplans for given Adjacencies"*, arXiv:2008.01803, 2020. Free.
  Takes an adjacency graph drawn in a GUI and returns a set of **topologically
  distinct dimensioned rectangular floorplans**; or takes a dimensionless layout
  and dimensions it while preserving adjacency, position and shape. Live at
  `app.gplan.in` (free login) [snippet — not exercised].
- **Upasani, Shekhawat & Sachdeva (2020), "Automated generation of dimensioned
  rectangular floorplans"**, *Automation in Construction* 113:103149. Paywalled;
  **free preprint arXiv:1910.00081**. ⭐ **The method to copy**: adjacency
  becomes a dimensionless *rectangular arrangement* (which guarantees
  existence), dimensional requirements become **min-width plus an aspect-ratio
  range per room**, and the dimensioning is then a **linear program**.
- **Bisht et al. (2022), "Transforming an Adjacency Graph into Dimensioned
  Floorplan Layouts"**, *Computer Graphics Forum* 41:5–22. Paywalled. The
  graphics-venue entry point.
- **⭐ Shiksha, Anand, Shekhawat & Agrawal (2025), "Automated generation of
  circulations within a floorplan"**, *AI EDAM* 39, DOI
  10.1017/s0890060425000022. **Open access.** Generates **corridors** inside a
  rectangular floorplan from the plane graph, with corridor-thickness,
  entry-point and privacy constraints. **This is the missing middle piece** —
  it turns a room-adjacency plan into something with circulation you can measure
  travel distance along.
- **Lohani & Shekhawat, "DPLAN: Minimal Connectivity to Floorplan Generation"**,
  arXiv:2606.21159, 2026. Free. ⭐ **Inverts the input**: the user supplies a
  room count plus which rooms must share a *door* and which must *not* be
  adjacent. It builds a bi-connected plane triangulation guaranteeing a plan
  with no overlaps and no leftover space. **The closest fit to a procedural
  front end**, because a door graph is what §4.1 says actually matters.
- **Lohani, Suthar & Shekhawat, "Algorithmic Design and Graph-Based
  Classification for Rectilinear-Shaped Modules in Floor Plans"**,
  arXiv:2601.00539, 2026. Free. **L- and T-shaped modules**, linear-time
  construction, shape-preservation constraints. Escapes the all-rectangles
  limitation — and note it lands on the same shape set as Palladio's stage 3
  (§6.1: rectangular, I, T, +).
- **Klawitter, Klesen & Wolff (2021), "Algorithms for Floor Planning with
  Proximity Requirements"**, arXiv:2107.05036, CAAD Futures 2021. Free.
  **NP-hard**; decomposes into floor assignment + single-floor planning, both as
  ILPs. The reference if the work goes multi-storey.

### 6.6 Automated code checking — and the actual IBC numbers

#### What the history teaches

**ICC SMARTcodes (2007)** — code text is marked up (applicability / requirement
/ exception), a dictionary maps code concepts to BIM properties, and constraints
serialise as tuples such as
`<require topic="vapor retarder" property="permeance" comparison=".le." value="1" unit="perm">`.
Results log as compliant, non-compliant, **or "not checkable at design
review"** — that third class is the intellectually honest part and should be in
any implementation here. ⛔ **The patent application is abandoned and the
trademark lapsed in 2012 without ever entering commercial use.** Its markup
approach survives as **RASE** (Requirement / Applicability / Selection /
Exception), which is in current use.

**Solibri Model Checker** — ~50+ parametric rule *templates*; users configure
parameters, they do not write code. The documentation is blunt: *"the rules do
not change the model; they only find potential problems."* The template
catalogue is mostly model-quality checking; genuine *code* rules cluster in only
three families: **fire compartmentation, accessibility geometry, and egress**.
Nothing requiring judgement has a template. Their Rule 179 "Escape Route
Analysis" exposes travel distances, occupancy ratios, route counts, a shared-route
length multiplier, stair length method, door widths — **but the path-finding
algorithm itself is undocumented.**

**⭐⭐ CORENET / FORNAX (Singapore, e-PlanCheck live September 2000) — the one
architectural lesson worth copying.** FORNAX is a **semantic enrichment layer
above IFC**: it *"adds higher level semantics relevant to code checking by
encapsulating building components into a set of FORNAX objects, each of which
defines relevant attributes and behaviours."* **A FORNAX object is a class with
methods, not a data record.** The published example: an apartment becomes
`FXApartmentUnit` with `GetSpaces`, `CalculateArea`, and — crucially —
**`CalculateTravelDistance`**.

> **The lesson: put the hard geometry inside a compiled object method, and keep
> the "rule" above it as a trivial numeric comparison against a table.** Every
> attempt to express egress geometry *in* a rule language has stalled. The one
> system that shipped put it in an object method.

**CORENET X** mandates openBIM/IFC-SG submission — GFA ≥ 30,000 m² from
1 Oct 2025, all new projects from 1 Oct 2026, all ongoing projects from
1 Oct 2027. ⚠ **Caveat:** primary sources describe CORENET X as a *submission
and concurrent-review* platform, **not** an automated compliance engine. IFC-SG
makes automated checking *possible*; it does not appear to deliver it today.

#### ⚠ A citation correction

**The brief's title for the Eastman paper is wrong, and so is much of the
literature.** There is no *Automation in Construction* 2009 paper called "A
review of automated rule checking systems." The paper meant is:

> **Eastman, C., Lee, J., Jeong, Y. & Lee, J. (2009). "Automatic rule-based
> checking of building designs." *Automation in Construction* 18(8),
> 1011–1033. DOI 10.1016/j.autcon.2009.07.002** — Crossref-verified.
> Paywalled.

Also flag: the frequently-cited DOI `10.1016/j.autcon.2015.01.003` for
Solihin & Eastman 2015 is **wrong and 404s**. The correct DOI is
**10.1016/j.autcon.2015.03.003**.

#### ⭐ The actual numbers — IBC 2021

All of the following were read from UpCodes' rendering of the Illinois Building
Code 2021, which adopts IBC 2021 with these chapters unamended; section
numbering cross-checked against the Washington State adoption. Marked **[cited]**
throughout, with one flagged exception.

**§1004.5 Occupant load — Table 1004.5, the rows a building generator needs:**

| Function of space | Floor area per occupant |
|---|---|
| **Business areas** | **150 gross** |
| **Residential** | **200 gross** |
| **Mercantile** | **60 gross** |
| **Educational — classroom** | **20 net** |
| Assembly w/o fixed seats — concentrated (chairs only) | 7 net |
| Assembly w/o fixed seats — standing space | 5 net |
| Assembly w/o fixed seats — unconcentrated (tables & chairs) | 15 net |
| Parking garages | 200 gross |
| Industrial areas | 100 gross |
| Warehouses | 500 gross |
| Accessory storage / mechanical equipment room | 300 gross |
| Kitchens, commercial | 200 gross |
| Exercise rooms | 50 gross |
| Library — reading rooms / stack area | 50 net / 100 gross |

**§1006.2.1 — one exit permitted, and common path of egress travel.** Two exits
are required from a space where *either* the occupant load *or* the common path
exceeds these:

| Occupancy | Max occupant load for 1 exit | Common path, **unsprinklered** | Common path, **sprinklered** |
|---|---|---|---|
| A, E, M | 49 | 75 ft | 75 ft |
| **B** | 49 | **75 ft** | **100 ft** |
| **F** | 49 | 75 ft | 100 ft |
| **S** | **29** | 75 ft | 100 ft |
| U | 49 | 75 ft | 100 ft |
| R-1 | 10 | NP | 75 ft |
| **R-2, R-3, R-4** | **20** | NP | **125 ft** |
| I-1, I-2, I-4 | 10 | NP | 75 ft |
| I-3 | 10 | NP | 100 ft |
| H-1, H-2, H-3 | 3 | NP | 25 ft |
| H-4, H-5 | 10 | NP | 75 ft |

⚠ **Data-quality warning worth recording as a standing lesson.** The first
automated extraction of this table returned the B/F/S/U sprinkler columns
**swapped** — 100 ft unsprinklered and 75 ft sprinklered, which is physically
backwards. It was caught only by cross-checking a second source. **Assume any
single scrape of a code table is suspect until cross-checked.** This is the same
class of error as the `arc`-is-a-wall mistake in `footprint_plan.md`: a
plausible-looking result inferred without checking against the physics.

**§1006.3.3 — minimum number of exits per storey:**

| Occupant load per storey | Minimum exits |
|---|---|
| **1–500** | **2** |
| 501–1,000 | 3 |
| More than 1,000 | 4 |

Single-exit storeys, **Table 1006.3.4(1)**, Group R-2: permitted at basement,
1st, 2nd and 3rd storey, with a maximum of **4 dwelling units**, maximum
**125 ft** travel, sprinklered, with emergency escape openings. **4th storey and
above: not permitted.**

⭐ **That is the "point access block" switch from §2.5, with numbers.** Four
units per floor, three storeys, sprinklered. It is a completely different
residential plan family, and it is four numbers.

**§1007.1.1 — exit separation, the diagonal rule** [cited, verbatim]:

> "Where two exits or exit access doorways are required, they shall be placed a
> distance apart **not less than one-half of the length of the maximum overall
> diagonal dimension of the building or area to be served**, measured in a
> straight line between them."

- **Sprinklered exception:** separation reduces to **not less than one-third**
  of the maximum overall diagonal.
- **§1007.1.1.1 exception:** where interior exit stairways are interconnected by
  a **1-hour rated corridor**, separation is measured *along the shortest direct
  line of travel within the corridor* rather than straight-line.

⚠ **This rule is a ratio to a derived property of the space, not a fixed
distance** — which is exactly why it gets implemented wrongly. Purushotham et
al. (2026) document LLM-generated Revit rules that computed the *maximum linear
separation between doors* instead of comparing separation to the half-diagonal,
and **dropped the sprinklered one-third exception entirely** [snippet].

**§1017.2 — Table 1017.2, exit access travel distance (feet):**

| Occupancy | Unsprinklered | Sprinklered |
|---|---|---|
| **A, E, F-1, M, R, S-1** | **200** | **250** |
| **B** | **200** | **300** |
| **F-2, S-2, U** | **300** | **400** |
| I-1 | NP | 250 |
| I-2, I-3 | NP | 200 |
| I-4 | 150 | 200 |
| H-1 / H-2 / H-3 / H-4 / H-5 | NP | 75 / 100 / 150 / 175 / 200 |

**§1017.3 — measurement, and this is the rule that governs the algorithm**
[cited]: measured from the most remote point of each room *"along the natural
and unobstructed path of horizontal and vertical egress travel"* to the entrance
to an exit; where more than one exit exists, to the **nearest** one. On stairways
it is measured on a plane *"parallel and tangent to the stair tread nosings"*,
in the centre of the stair and landings.

**§1020.5 — dead-end corridors** [cited]. ⚠ Note this is **§1020.5** in IBC
2021, renumbered from §1020.4 in IBC 2018:

> "Where more than one exit or exit access doorway is required, dead-end
> corridors shall not exceed **20 feet**."

Exceptions: **50 ft** for Groups B, E, F, I-1, M, R-1, R-2, S, U in fully
sprinklered buildings; 50 ft for I-3 Conditions 2/3/4; 30 ft for I-2 Condition
2 corridors not serving patient rooms; and **no limit where the dead end is less
than 2.5× the least width of the corridor.**

**§1020.3 — corridor width:** **44 in.** minimum where the corridor serves 50 or
more occupants; **36 in.** permitted below 50. **§1011.2 — stairway width:**
same 44 in. / 36 in. split. ⚠ The individual occupancy rows of Table 1020.3
(e.g. the 72 in. institutional case) are **[UNVERIFIED]**.

#### ⭐⭐ The unsolved problem, and it is a real opportunity

The governing measurement text is **NFPA 101 §7.6**, mirrored by IBC §1017.3
[snippet for the NFPA wording]: measured *"along the centerline of the natural
path of travel, starting from the most remote point subject to occupancy,
curving around any corners or obstructions with a 1-ft (305 mm) clearance
therefrom, and ending at the center of the doorway."*

Three computational consequences, and together they are a complete algorithm:

```
  1. "centerline of the natural path"  ->  follow the MEDIAL AXIS / STRAIGHT
                                           SKELETON of the free space, not the
                                           Euclidean shortest route
  2. "1-ft clearance"                  ->  ERODE the free space by 305 mm before
                                           path-finding; you get the
                                           characteristic corner fillet
  3. "center of the doorway"           ->  terminate at the DOOR CENTROID, not
                                           at a wall
```

⚠ Note carefully: **IBC §1017.3 says "natural and unobstructed path" but does
not itself state the 1-ft offset.** That clearance rule is NFPA 101. Implementing
it to IBC alone makes the offset a defensible interpretation, not literal text.
It should be a documented parameter, not a hard-coded constant.

> **No published paper joins all three.** Straight-skeleton indoor navigation
> graphs exist (Fu et al. 2020, *Automation in Construction* 112:103057).
> Travel-distance code checking exists (Ismail et al. 2023, *Buildings* 13(6),
> open access, 256 fire-safety clauses via RASE markup and Dynamo). **Neither
> closes the loop.** Ismail et al. check travel distance without specifying how
> the path is traced.

⭐ **And AssetBash already has the straight-skeleton machinery** for the roof
work. Implementing centreline + 305 mm erosion + door-centroid termination in
Houdini is a genuinely novel result, not merely a feature.

**One more gap, stated by the second research strand and worth repeating:**

> The two literatures do not meet. Rectangular dualisation produces a plan from
> an adjacency graph; code checking evaluates a finished plan. **Nobody has
> published dualisation *constrained by* egress.** Shekhawat's 2025 circulation
> paper (open access) is the missing middle piece, because it produces the
> corridors you would measure along.

---

## 7. The implementation path for Houdini

### 7.1 What to build first, and why

The order below is chosen so that **every phase is independently testable and
every phase is used by the next one.** It follows the pattern that worked for
metal extrusions, mouldings and signs.

**Phase 0 — BASELINE, before anything.** Same standing lesson as always: measure
the before state. There is no existing plan tool, so the baseline here is
different in kind — it is a **corpus**. Build a small set of hand-authored
reference plans (one per taxonomy row in §1.1), stored as flat geometry with
labelled rooms and doors. These are the parity oracle for everything that
follows. Without them the work is unfalsifiable.

**Phase 1 — `AB::PlanGrid::1.0`. The tartan grid.** ⭐ This is the
`MetalExtrusionMaker` of the plan work: small, self-contained, and everything
else consumes it.

```
  Input :  footprint polygon (from AB::BuildingFootprintGenerator)
           floor_to_floor, structural_system, clear_height     (§2.7)
           parking_below?, stall_width                          (§2.1)
  Output:  a labelled tartan grid — ALTERNATING room-bands and wall-bands
           (§6.1), as a set of cells with i@band_type, f@band_width
           plus columns at band intersections
```

The internal derivation is §2.7: `available_depth × span_depth_ratio[system]`
gives `max_span`; the bay is the largest grid ≤ `max_span` that divides the
parking module. Wall thickness is a *band*, not a subtraction — that one
decision removes an entire class of dimensional-drift bug.

**Phase 2 — `AB::PlanCore::1.0`. Core placement and sizing.**

```
  Input :  the grid, storeys, occupancy type, core_strategy enum
  Output:  a core region snapped to grid cells, with sub-regions tagged
           (lift, stair_a, stair_b, toilet, riser, lobby)
           plus core_area(z) for the taper
```

Sizing per §2.3. **Two exit stairs are placed by the diagonal rule (§6.6),
not by hand.** This is the phase where egress starts to shape geometry.

**Phase 3 — `AB::PlanCirculation::1.0`. The corridor, from the skeleton.**
Per §6.4: straight skeleton of the footprint → keep the branches connecting core
to extremities → offset by `corridor_width` → the residue is partitionable.
⭐ **This reuses the roof work's skeleton machinery directly.** It is the
strongest argument for doing the roof and plan work with one shared
implementation.

**Phase 3b — OP-BASILICA, the top-lit spine.** ⭐ Small, and it should be built
here rather than deferred, because it *changes the residue* Phase 4 partitions.
Trigger: plate depth > `2 × lease_span`. Carve a central void along the long
axis, raise its roof, glaze the difference (§5A.4). Three parameters — `w`, `h`,
`n` — and `n > 1` gives the sawtooth the roof work already knows about. It is the
cheapest phase in the plan and it moves the S1 daylight score more than anything
else in the tool.

**Phase 4 — `AB::PlanPartition::1.0`. Rooms in the residue.** A **slicing tree**
(§6.5) over the residue, driven by an adjacency graph from the catalog. Start
slicing-only; it covers every corridor-spine plan. Add corner block lists only
when a pinwheel is genuinely needed. Room aspect ratios come from the catalog
(Palladio's seven for period work, ResPlan-derived distributions for modern).

**Phase 5 — `AB::PlanScore::1.0`. The oracle.** S1–S4 from §4.3, plus the
travel-distance measurement from §6.6. ⭐ **This is not the last phase because
it is least important — it is last because it must be able to score the output
of all four earlier ones.** It should be usable standalone on hand-authored
plans, which is how Phase 0's corpus gets validated.

### 7.2 What it reuses from existing work

| Existing asset | Reused for |
|---|---|
| **Edge classification** (`vex/footprint_classify.vex`) — per-edge `i@wall_id`, per-vertex `i@corner_convex`, `f@corner_angle` | ⭐ The single most reused piece. The grid needs to know which footprint edges are street-facing (frontage ⇒ glazing ⇒ lease-span measurement) and which are party walls (no glazing). **`corner_convex` already distinguishes the courtyard condition** that §2.2 shows decouples depth from daylight |
| **`Corner_i` sits between `Wall_i` and `Wall_i+1`** (the invariant established in `footprint_plan.md`) | The same *inter-element* invariant discipline applies to `Room_i` / `Door_i` / `Wall_i`. Establish it up front; do not check for it afterwards |
| **The weighted straight skeleton** (roof work, §1 of `roof_typology_and_math.md`) | Phase 3 corridor generation, and the travel-distance path in Phase 5. **One implementation, three consumers** |
| **The catalog CSV pattern** (`config/catalogs/`, as used by signs, mouldings, hardware) | Adjacency graphs by typology/region/era; room-proportion sets; bay-spacing preferences; IBC tables from §6.6 |
| **`SignLibrary`'s column-lookup-by-class** | Selecting an adjacency graph by `(typology, region, era)` is the same lookup shape as selecting a sign by SizeClass |
| **`ModuleWidth` in `BuildingFootprintGenerator`** (currently a bare `10.0`) | Becomes the output of the Phase 1 derivation rather than a magic number |
| **The angle-band corner-treatment lookup** (`footprint_plan.md` §2, Layer 3) | ⭐ Exactly the shape of Vitruvius's alae/tablinum band tables (§5A.3). **The same lookup code serves both** — a ratio keyed to a size band |
| **The sawtooth in the roof work** | `n > 1` in OP-BASILICA (§5A.4). One operator, two consumers |
| **The `LegacyGroupNames` migration pattern** | Same technique when plan output starts feeding `DowntownBuilding` and friends |

### 7.3 The verification test

Mechanical, falsifiable, and runnable without looking at anything:

**Grid (Phase 1)**
- Bands strictly alternate room / wall around both axes.
- Σ band widths = footprint extent, to floating-point tolerance. *(This is the
  test the tartan formulation is designed to pass trivially and a
  centreline-and-subtract formulation fails intermittently.)*
- `bay ≤ available_depth × span_depth_ratio[system]` for every bay.
- With `parking_below = true`, every column lands on the parking grid.

**Core (Phase 2)**
- Core region is a union of whole grid cells — no partial cells.
- Exactly the required number of stairs for the occupant load (Table 1006.3.3).
- **Straight-line distance between the two stairs ≥ ½ × max overall diagonal**
  (⅓ if sprinklered). §1007.1.1.
- `core_area(z)` is monotonically non-increasing with height.

**Circulation (Phase 3)**
- The corridor region is connected, and every room touches it.
- **No dead end exceeds 20 ft** (50 ft sprinklered, per §1020.5), *or* is less
  than 2.5× the corridor's least width.
- Corridor width ≥ 44 in. where its occupant load ≥ 50.

**Partition (Phase 4)**
- **Mosaic property:** the union of rooms + corridor + core = the footprint
  exactly. No gaps, no overlaps. *(This is why CBL's mosaic condition matters —
  it is the property, so make it the test.)*
- Room count = adjacency graph node count. Every graph edge realised as a shared
  boundary segment of non-zero length.
- **Every room's aspect ratio is a member of the catalog set.**
- **⭐ Wet walls are vertically continuous across every floor of the stack.**
  This is the one that fails silently if plans are generated per-floor.
- Palladian mode only: at most one non-rectangular room, and it is bisected by
  the axis (§6.1).
- **Domus mode:** the room sequence along the axis is exactly
  `fauces → atrium → tablinum → peristyle → hortus`, truncated but never
  reordered; side rooms mirror about the axis; the atrium's length:width is a
  member of {5:3, 3:2, 1:√2}; ala width matches the band table for the atrium's
  length (§5A.3).
- **OP-BASILICA:** aisle width, clerestory height and nave width all satisfy the
  declared ratios; and ⭐ **the S1 daylight score is measurably higher with the
  spine than without it** — run both and compare, which is the honest test that
  the operator does what it claims.

**Score (Phase 5)**
- **S1:** for a generated 1900s office, ≥90% of area within 20 ft of glass; for
  a generated 1970s plate, 35–70%. The [cited] table in §2.2 is the calibration.
- **S2:** every point's travel distance to the nearest exit ≤ Table 1017.2;
  two edge-disjoint paths exist.
- **S3:** integration ordering holds —
  `living > circulation > bedroom > bathroom`. A plan whose most integrated
  space is a bathroom fails.
- **S4:** every partition is on-grid, or explicitly tagged `free_plan`.

**The Euler-style structural check that catches a whole class of bug**, in the
spirit of `footprint_plan.md`'s "N-gon → N wall groups":

```
  rooms + corridors + core_cells  ==  grid_cells_consumed
  doors                           ==  adjacency_graph_edges_marked_via_door
  Σ room_area + corridor_area + core_area  ==  footprint_area
```

### 7.4 Two things worth building because nobody has

1. **The NFPA 7.6-conformant travel-distance measurement** (§6.6): straight
   skeleton + 305 mm erosion + door-centroid termination. The literature has
   the pieces and has not joined them, and AssetBash already owns the hardest
   piece.
2. **Rectangular dualisation constrained by egress** (§6.5/§6.6). Also
   unpublished. Also within reach, because Phase 2 already places stairs by the
   diagonal rule and Phase 5 already measures travel distance — the only missing
   step is feeding the failure back into the partition.

---

## 8. What this approach cannot do — an honest list

1. **It cannot design a building type it has not been shown.** This is the
   deepest limit and it is shared by every system in §6. The Palladian grammar
   describes Palladio; House-GAN describes small Chinese apartments;
   `AB::PlanPartition` will describe whatever is in its catalog. **There is no
   general plan generator in the literature and this will not be one.**
2. **The adjacency graph is authored, always.** §3.2. Everything downstream is
   adaptation, not invention.
3. **Space syntax scores configuration, not quality.** A well-integrated plan can
   still be a bad building. S3 catches gross errors; it does not certify design.
4. **The code checks are geometric only.** Following Solihin & Eastman's
   taxonomy, only rules reducible to *"geometric properties and quantifiable
   thresholds"* are checkable. Material suitability, performance-based
   alternatives and design intent are not. **Keep SMARTcodes' third result
   class — "not checkable" — and report it.**
5. **Slicing trees cannot make a pinwheel.** A real limit with a known fix
   (§6.5), deferred rather than solved.
6. **Nothing here handles the section properly.** Split levels, double-height
   spaces, mezzanines, ramps and the OMA continuous-ramp operator (§5.2) all
   break the one-plan-per-floor assumption. This is the biggest structural gap
   in the proposal and it should be acknowledged now rather than discovered in
   Phase 4.
7. **Regional coverage is only as good as the catalog.** ResPlan is
   international but residential; MSD is Swiss; CubiCasa5K is Finnish; RPLAN is
   Asian and unusable commercially. **There is no open, licensable corpus of
   non-residential plans at all.** Commercial and civic typologies will have to
   be authored by hand, and that is a real cost.
8. **§5A was read in translation, and the archaeology was not read at all.**
   Every Vitruvian ratio in this document is [cited] from an English
   translation, and one passage only was cross-checked against a second
   translation. The three claims about how real Roman houses differ from the
   prescriptions are marked [UNVERIFIED] and are *not used*. Until items 26–29
   in §9 are pulled, **the domus generator should be treated as a generator of
   Vitruvius's ideal house, not of a Roman house.** Those are different things
   and the difference is exactly the kind that produces pastiche.
9. **The signature-architect operators produce a *resemblance*, not a design.**
   OP-MAD gives a twisting tower; it does not give a MAD building. Say so in the
   UI, and keep signatures behind an explicit switch (§5.5).

---

## 9. Papers to request through USC

Grouped by why they are worth the request. DOIs are Crossref-verified unless
noted. **Nothing in this document paraphrases a paper marked here as unread.**

### Tier 1 — request these four first

| # | Citation | Why |
|---|---|---|
| 1 | **Park, K., Ergan, S. & Feng, C. (2024).** "Quality assessment of residential layout designs generated by relational Generative Adversarial Networks (GANs)." *Automation in Construction* **158**, 105243. **DOI 10.1016/j.autcon.2023.105243** | The single most on-point paper nobody could read. An empirical audit of House-GAN-lineage output against architect-made plans (80,000+ each side) on space-size distribution, visibility/privacy and room connectivity, via Mann–Whitney U tests. Reports significant disparities indicating *"a gap in the generative design models' understanding of nuanced, latent rules present in real-world data."* ⚠ Quotes read only via an index mirror — verify before citing |
| 2 | **Solihin, W. & Eastman, C. (2015).** "Classification of rules for automated BIM rule checking development." *Automation in Construction* **53**, 69–82. **DOI 10.1016/j.autcon.2015.03.003** ⚠ *(the widely-cited DOI …2015.01.003 is wrong and 404s)* | The four-class rule-complexity taxonomy. The single most useful item for deciding **what is machine-checkable at all**, which is the gate on the whole §6.6 effort |
| 3 | **Koźmiński, K. & Kinnen, E. (1985).** "Rectangular duals of planar graphs." *Networks* **15**(2), 145–157. **DOI 10.1002/net.3230150202** | The theorem itself (§6.5). Only free restatements were read. ⚠ Kumar & Shekhawat claim a counterexample to its *separable* case — worth reading the original before implementing |
| 4 | **Bhasker, J. & Sahni, S. (1988).** "A linear algorithm to find a rectangular dual of a planar triangulated graph." *Algorithmica* **3**, 247–278. **DOI 10.1007/BF01762117** | The O(n) construction. The free author PDF of the conference version exists but would not text-extract |

### Tier 2 — the numbers this document had to mark [snippet]

| # | Citation | Fixes |
|---|---|---|
| 5 | **Oldfield, P. & Doherty, B. (2019).** "Offset Cores: Trends, Drivers and Frequency in Tall Buildings." *CTBUH Journal* 2019 Issue II. *(CTBUH PDF endpoints returned 404)* | The "85% of 500 tall buildings have central cores" figure and the offset-core driver taxonomy — every core-position number in §2.3 |
| 6 | **Oldfield, P. et al. (2021).** "Space Efficiency in Contemporary Supertall Office Buildings." *Journal of Architectural Engineering* **27**(3). **DOI 10.1061/(ASCE)AE.1943-5568.0000486** | The floor-plate efficiency and core-to-GFA statistics in §2.3–§2.4 |
| 7 | **"Design determinants of core efficiency in tall timber buildings: a typological analysis."** *Discover Sustainability*, 2025. **DOI 10.1007/s43621-025-02266-7** *(Springer redirected to an auth wall)* | The 4–21% / mean 13.4% core-to-GFA range and the central/peripheral/external typology counts |
| 8 | **"Optimizing Multi-Family Building Massing for Affordability and Envelope Performance."** *Buildings* **11**(3), 99, 2021. *(MDPI returned 403 — nominally open access, so it may only need a retry)* | The 40 ft / 70 ft double-loaded floor-plate width bounds in §2.6 |

### Tier 3 — the review literature

| # | Citation |
|---|---|
| 9 | **Eastman, C., Lee, J., Jeong, Y. & Lee, J. (2009).** "Automatic rule-based checking of building designs." *Automation in Construction* **18**(8), 1011–1033. **DOI 10.1016/j.autcon.2009.07.002** ⚠ *title corrected — see §6.6* |
| 10 | **Weber, R. E., Mueller, C. & Reinhart, C. (2022).** "Automated floorplan generation in architectural design: A review of methods and applications." *Automation in Construction* **140**, 104385. **DOI 10.1016/j.autcon.2022.104385** — the canonical pre-diffusion review; abstract not retrieved |
| 11 | **Jang, S., Roh, H. & Lee, G. (2025).** "Generative AI in architectural design: Application, data, and evaluation methods." *Automation in Construction* **174**, 106174. **DOI 10.1016/j.autcon.2025.106174** — abstract read; full text would give the evaluation breakdown by method |
| 12 | **Zhang, H. & Zhang, R. (2025).** "An Attention-Based Constrained Diffusion Model for Accessible Floor Plan Generation." *Journal of Computing in Civil Engineering* **39**(5). **DOI 10.1061/JCCEE5.CPENG-6456** — accessibility as a first-class constraint; metadata only |

### Tier 4 — floorplanning representations (§6.5), if the partition work goes non-slicing

| # | Citation |
|---|---|
| 13 | Wong, D. F. & Liu, C. L. (1986). "A new algorithm for floorplan design." *DAC '86*, 101–107. **DOI 10.1145/318013.318030** — slicing trees / Polish expressions |
| 14 | Murata, H., Fujiyoshi, K., Nakatake, S. & Kajitani, Y. (1996). "VLSI module placement based on rectangle-packing by the sequence-pair." *IEEE TCAD* **15**, 1518–1524. **DOI 10.1109/43.552084** |
| 15 | Chang, Y.-C., Chang, Y.-W., Wu, G.-M. & Wu, S.-W. (2000). "B\*-trees: a new representation for non-slicing floorplans." *DAC '00*, 458–463. **DOI 10.1145/337292.337541** |
| 16 | Hong, X. et al. (2000). "Corner block list: an effective and efficient topological representation of non-slicing floorplan." *ICCAD 2000*, 8–12. **DOI 10.1109/iccad.2000.896442** — the mosaic representation |
| 17 | Bhasker, J. & Sahni, S. (1987). "A linear time algorithm to check for the existence of a rectangular dual of a planar triangulated graph." *Networks* **17**(3), 307–317. **DOI 10.1002/net.3230170306** |

### Tier 5 — Shekhawat's dimensioned-floorplan line (§6.5)

| # | Citation | Note |
|---|---|---|
| 18 | Upasani, N., Shekhawat, K. & Sachdeva, G. (2020). "Automated generation of dimensioned rectangular floorplans." *Automation in Construction* **113**, 103149. **DOI 10.1016/j.autcon.2020.103149** | ⭐ the LP-dimensioning method. **Free preprint arXiv:1910.00081 — try this before requesting** |
| 19 | Shekhawat, K., Upasani, N., Bisht, S. & Jain, R. (2021). "A tool for computer-generated dimensioned floorplans based on given adjacencies." *Automation in Construction* **127**, 103718. **DOI 10.1016/j.autcon.2021.103718** | Free preprint arXiv:2008.01803 |
| 20 | Bisht, S. et al. (2022). "Transforming an Adjacency Graph into Dimensioned Floorplan Layouts." *Computer Graphics Forum* **41**, 5–22. **DOI 10.1111/cgf.14451** | The graphics-venue entry point |
| 21 | Kumar, V. & Shekhawat, K. (2021). "A transformation algorithm to construct a rectangular floorplan." *Theoretical Computer Science* **871**, 94–106. **DOI 10.1016/j.tcs.2021.04.014** | Repairs graphs that are *not* rectangularly dualisable |

### Tier 6 — egress computation (§6.6)

| # | Citation |
|---|---|
| 22 | Fu, M., Liu, R., Qi, B. & Issa, R. R. A. (2020). "Generating straight skeleton-based navigation networks with Industry Foundation Classes for indoor way-finding." *Automation in Construction* **112**, 103057. **DOI 10.1016/j.autcon.2019.103057** — ⭐ the medial-axis primitive |
| 23 | Essawy, Y., Abdullah, A. & Nassar, K. (2024). "Graph Representation for Emergency Egress Code Analysis." *LNCE* (CSCE 2022), 617–627. **DOI 10.1007/978-3-031-35471-7_45** |
| 24 | Purushotham, S., Kailashnath, A. & Mutis, I. (2026). "Framework for automated building code compliance checking…" *Automation in Construction* **181**, 106598. **DOI 10.1016/j.autcon.2025.106598** — documents the half-diagonal failure mode |
| 25 | Hjelseth, E. (2015). "Public BIM-based model checking solutions: lessons learned from Singapore and Norway." *WIT Transactions on the Built Environment*, 421–436. **DOI 10.2495/bim150351** — probably the best account of why CORENET e-PlanCheck stalled |

### Free and worth reading now, no request needed

- **Stiny, G. & Mitchell, W. J. (1978).** "The Palladian grammar." *Environment
  and Planning B* **5**, 5–18. DOI 10.1068/b050005. ✅ Free PDF at CMU
  (`contrib.andrew.cmu.edu/~ramesh/teaching/course/48-747/...`). Read in full for
  this document.
- **Jiang, Z. & Zhang, D. (2026).** "Space Syntax-guided Post-training for
  Residential Floor Plan Generation." arXiv:2602.22507v2. ✅ Free. The
  integration formulas in §4.2 and the SSIO pipeline in §4.4.
- **Shiksha, Anand, Shekhawat, K. & Agrawal (2025).** "Automated generation of
  circulations within a floorplan." *AI EDAM* **39**. DOI
  10.1017/s0890060425000022. ✅ Open access. ⭐ The corridor-generation piece.
- **Lohani & Shekhawat (2026).** "DPLAN: Minimal Connectivity to Floorplan
  Generation." arXiv:2606.21159. ✅ Free. Door-graph input.
- **Lohani, Suthar & Shekhawat (2026).** "Algorithmic Design and Graph-Based
  Classification for Rectilinear-Shaped Modules in Floor Plans."
  arXiv:2601.00539. ✅ Free. L- and T-shaped rooms.
- **van Engelenburg, C. et al. (2024).** "MSD: A Benchmark Dataset for Floor
  Plan Generation of Building Complexes." ECCV 2024, arXiv:2407.10121. ✅ Free,
  dataset CC BY 4.0. The near-duplicate finding and the load-bearing-wall layer.
- **Abouagour, M. & Garyfallidis, E. (2025).** "ResPlan: A Large-Scale
  Vector-Graph Dataset of 17,000 Residential Floor Plans." arXiv:2508.14006.
  ✅ Free, CC BY 4.0. ⭐⭐ **The dataset to actually use.**
- **Ismail, A. et al. (2023).** "BIM-Based Automated Code Compliance Checking
  System in Malaysian Fire Safety Regulations." *Buildings* **13**(6), 1404.
  DOI 10.3390/buildings13061404. ✅ Open access. RASE markup, 256 clauses.
- **Nassar, K. & Nguyen, T. (2005).** "Using building topological information to
  check for means of egress building code compliance." *ITcon* **10**, 219–227.
  ✅ Open access. ⚠ No DOI confirmed.
- **Klawitter, Klesen & Wolff (2021).** "Algorithms for Floor Planning with
  Proximity Requirements." arXiv:2107.05036. ✅ Free. The multi-storey ILP.
- **Vitruvius, *De architectura*** — ✅ free and public domain. Read for §5A via
  LacusCurtius (`penelope.uchicago.edu/Thayer/E/Roman/Texts/Vitruvius/`) and
  Morgan's 1914 translation via Perseus. Books I.2–3, III.1 and III.3, V.1,
  VI.1 and VI.3 are the ones that carry data.

### ⭐ For §5A — the Roman-house reality check, which I could NOT verify

⚠ **§5A.5 flags three claims as [UNVERIFIED] because no source for them could be
fetched within budget.** These are the works that settle them, and they are the
highest-value classical request because they are exactly the fact-versus-art-
direction split the project cares about. **Nothing in §5A paraphrases any of
them.**

| # | Citation | Settles |
|---|---|---|
| 26 | **Wallace-Hadrill, A. (1994).** *Houses and Society in Pompeii and Herculaneum.* Princeton University Press. ISBN 0-691-06987-5 | The canonical statistical survey of what Roman urban houses actually are, by size and type. Would settle whether the atrium-house sequence is the norm or an elite minority |
| 27 | **Allison, P. M. (2004).** *Pompeian Households: An Analysis of Material Culture.* Cotsen Institute, UCLA. *(An open-access companion database exists at `stoa.org/projects/ph/home`)* | Room-use assignment from finds rather than from Vitruvius's labels — i.e. whether the named rooms were used as named |
| 28 | **Peterse, K.**, work on the metrological design of Pompeian atrium houses (e.g. "Notes on the design of the House of Pansa", *BABesch*). ⚠ Exact citation **not verified** | Whether built atria match Vitruvius's 5:3 / 3:2 / 1:√2 ratios and the alae/tablinum bands, measured |
| 29 | **Gros, P. (ed.), Vitruve, *De l'architecture*** (Budé / Les Belles Lettres), or Rowland & Howe (1999), *Vitruvius: Ten Books on Architecture*, Cambridge UP | ⚠ §5A was read in **translation only**, and only the basilica passage was cross-checked against a second translation. Any §5A figure that will drive geometry should be checked against the Latin with a modern critical commentary |

⚠ Also unverified and deliberately unused in §5A: the value of the *pes
monetalis* (Roman foot). It is needed before any §5A dimension in feet is
converted to metres.

### Could not read, and this document does not paraphrase them

Stiny & Gips (1972) IFIP paper — bibliographic details from a search summary
only. Koolhaas, *Delirious New York* (1978) and *S,M,L,XL* (1995) — not
consulted; the Bigness theorems came from a fetched reproduction of the essay,
not from the book. Hillier & Hanson (1984) — not consulted directly; the
formulas in §4.2 are from Jiang & Zhang's restatement. Boudon, *Lived-in
Architecture* (1972) — not consulted; the Pessac account in §5.1 is
**[snippet]** and should be checked against the book, which is at
archive.org/details/livedinarchitect0000boud.

---

## 10. Sources fetched and read

Everything marked **[cited]** in this document came from one of these:

**Structural and dimensional**
- SteelConstruction.info, *Framing schematics* —
  `https://steelconstruction.info/Framing_schematics` (§2.7 tables)
- THA Consulting, *What are common structural systems for long span garages?* —
  `https://www.tha-consulting.com/parking-database/what-are-common-structural-systems-for-long-span-garages/` (§2.1)
- phcppros, *Multifamily Residential Walls: How Big Do They Need to Be?* —
  `https://www.phcppros.com/articles/23151-...` (§2.6 DFU figures)

**Daylight and floor plate**
- Daylighting Pattern Guide, *Pattern 3: Section Depth* —
  `https://www.patternguide.advancedbuildings.net/patterns/pattern-3-section-depth.html`
- Daylighting Pattern Guide, *Pattern 1: Floor Plate Geometry* —
  `https://patternguide.advancedbuildings.net/pattern-slideshow/Pattern%201_%20Floor%20Plate%20Geometry.html`
  (§2.2, the max-distance / %-within-20-ft table)

**Grammar and syntax**
- Stiny, G. & Mitchell, W. J., "The Palladian grammar", *Environment and
  Planning B* 5, 5–18, 1978 — full PDF read
- Jiang, Z. & Zhang, D., arXiv:2602.22507v2, 2026 — full PDF read (§4.2 formulas,
  §4.4 SSIO pipeline, RPLAN screening figures)

**Architects**
- Koolhaas, *Bigness, or the Problem of Large* — reproduced text, the five
  theorems (§5.2)
- OMA project page, Seattle Central Library —
  `https://www.oma.com/projects/seattle-central-library` (five platforms, four
  in-between planes, Books Spiral)
- OMA partner page, Rem Koolhaas — `https://www.oma.com/partners/rem-koolhaas`
- designboom, *MAD architects: absolute towers completed* (§5.3, storeys,
  heights, 1–8°/floor, balcony statements)

**Classical (§5A)**
- Vitruvius, *De architectura*, translation hosted at LacusCurtius —
  `https://penelope.uchicago.edu/Thayer/E/Roman/Texts/Vitruvius/` — Books I, III
  and VI read for §5A.1–5A.3
- Vitruvius Book V ch. 1, Morgan's 1914 translation via Perseus —
  `perseus.tufts.edu/hopper/text?doc=Perseus:text:1999.02.0073:book=5:chapter=1`
  — fetched independently to **cross-check the basilica passage against the
  LacusCurtius text**. The two agree on every proportional rule and every Fano
  dimension quoted in §5A.4
- Wikipedia, *Domus* — used only for the room-name sequence in §5A.3, and it
  explicitly carries **no** evidence on divergence from Vitruvius, which is why
  §5A.5 is marked unverified

**Codes** — UpCodes rendering of the Illinois Building Code 2021 (adopting IBC
2021 unamended in Chapter 10): §1004.5 / Table 1004.5; §1006.2.1 /
Table 1006.2.1; §1006.3.3; Tables 1006.3.4(1) and (2); §1007.1.1 and
§1007.1.1.1; §1017.2 / Table 1017.2; §1017.3; §1020.3; §1020.5; §1011.2.

**Fetch failures worth recording**, because they are why several sections carry
**[snippet]** marks: CTBUH paper PDFs (404 on every endpoint tried);
`i-mad.com` (403); `morphosis.com` (Angular app, returns no text);
`mdpi.com` (403 on several nominally open-access papers); `springer.com`
(auth-wall redirect); `sciencedirect.com` (403 throughout); `dezeen.com` (403);
`archpaper.com` (403); `codes.iccsafe.org` (403). Several PDFs downloaded but
would not text-extract without poppler on this machine — the Le Corbusier Five
Points PDF and the GSA San Francisco Federal Building PDF among them.

⚠ **The WebSearch budget (200 calls) was exhausted during this research.** Three
items were cut short and are flagged in place: the single-stair/point-access
travel-distance limits beyond Table 1006.3.4(1); Table 1020.3's per-occupancy
corridor-width rows; and CORENET X's actual automated-checking scope.
