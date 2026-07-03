# UK Coverage Expansion — Scotland & Northern Ireland

Current coverage is **England & Wales only** (6,856 English + 408 Welsh MSOAs =
7,264 areas; ~90% of the UK population). Scotland (~5.5M people) and Northern
Ireland (~1.9M) are absent. This document plans each, then answers the real
question: **do them now, or after the mobile app and the rest of the roadmap?**

> Dates/source facts below are point-in-time and marked **[verify]** where they
> should be re-confirmed before build — the devolved data landscape moves.

---

## 0. The seam that makes this tractable

The whole engine funnels through two marts:

```
stg_* (per source) → int_* → rpt_area_profile_mvp → rpt_neighbourhood_score → decision.duckdb → API → web/mobile
```

Two properties decide everything about coverage expansion:

1. **Everything above the profile mart is coverage-agnostic.** The API, the
   scoring re-weight, the website's 7k area-page template, the map, the mobile
   app — none of them know what a "nation" is. They read rows. **Adding a
   nation = adding rows to `rpt_area_profile_mvp` in the same columns/units.**
   The API/web/mobile need **zero** changes.

2. **Scores anchor to the *pooled* distribution.** `rpt_neighbourhood_score`
   computes its p2/median/p98 bounds over the *entire* profile table. Add
   Scottish rows and the bounds recompute across E&W+Scotland automatically —
   so scores land on one UK-wide scale for free. The math is not the problem.

**Therefore the work is 100% in the per-nation ingestion layer, plus one
cross-nation judgement call (comparability, §3).** There is no architectural
penalty for doing this later — a fact that drives the sequencing decision (§5).

### What's already UK-wide (less work than "3× everything")
- **Geography lookup:** the ONS Postcode Directory (ONSPD) is UK-wide and
  already maps postcodes to Scottish Data Zones / Intermediate Zones and NI
  SOAs. The `stg_geo__postcodes` bridge extends rather than gets rebuilt. **[verify]**
- **Sale prices:** the **UK House Price Index** is a joint ONS / HM Land
  Registry / Registers of Scotland / Land & Property Services product covering
  the *whole UK*. One source, all four nations. **[verify]**
- **Amenities/transport:** OpenStreetMap is UK-wide. No gap.

### What is genuinely nation-specific (the real work)
- **Crime:** `data.police.uk` is England & Wales + British Transport Police
  only. Scotland and NI publish separately, coarser, different taxonomies.
- **EPC:** separate registers for Scotland and NI.
- **Flood:** Environment Agency (Eng) / NRW (Wales) / SEPA (Scot) / DfI (NI).
- **Rent:** partly devolved; per-nation series and grains.

So per nation the work is ~3 hard staging models (crime, EPC, flood) + a rent
source + a geography extension + rescore — not a from-scratch pipeline.

---

## 1. Scotland plan

**Population ~5.5M. Bigger gap, better open data. Do this one first.**

### Geography
- Use **Intermediate Zones (IZ)** as the recommendation grain — 1,279 zones,
  ~4,000 people each, the closest analogue to the MSOA (~7,200). Data Zones
  (6,976, ~760 people) are too granular and noisy for scoring. Source: National
  Records of Scotland (NRS). Postcodes → IZ already in ONSPD. **[verify]**
- `area_id` will be `S…`-prefixed IZ codes; slots straight into `dim_area`.

### Per-indicator source map
| Indicator | Source | Grain | Confidence note |
|---|---|---|---|
| Affordability — prices | **UK HPI** (RoS component) | Data Zone/LA | Same source family as E&W |
| Affordability — rent | Scottish Govt Private Sector Rent Statistics / ONS PIPR | BRMA / LA | Map BRMA→IZ **[verify]** |
| Safety — crime | **Police Scotland / statistics.gov.scot recorded crime** | **Local Authority, quarterly** | ⚠ No street-level feed like Police.uk — **coarser; flag lower confidence** |
| Energy — EPC | **Scottish EPC Register** (Energy Saving Trust / Scot Govt) | Certificate/postcode | Same SAP/RdSAP methodology → comparable |
| Flood | **SEPA flood risk maps** | Polygon | Flag only; different methodology to EA |
| Convenience | OpenStreetMap | Point | Identical to E&W |

### New dbt models
`stg_crime__scotland`, `stg_epc__scotland`, `stg_flood__scotland_sepa`,
`stg_rent__scotland` (+ extend `stg_geo__postcodes`, `stg_landreg__transactions`→
UK HPI). All conform to and union into `rpt_area_profile_mvp`. `rescore_extract.py`
regenerates the extract; existing tests apply unchanged.

### Known risks
- **Street-level crime gap** is the biggest. Scottish crime lands at LA level →
  every Scottish area shares its council's crime rate → coarse safety scores.
  Honest handling: compute per-1,000 rate at LA, attach to IZs, and mark the
  safety component `medium`/`low` confidence for Scotland.
- Rent BRMA→IZ mapping and PIPR Scotland coverage need confirming. **[verify]**
- IZ vs DZ grain decision affects everything downstream — decide first.

### Effort (T-shirt)
Discovery spike **S** · geography **S** (ONSPD extend) · prices **S** (UK HPI) ·
EPC **M** · crime **M** (coarse but simple) · flood **M** (spatial) · rent **M** ·
rescore+tests **S**. **Total ≈ M–L**, front-loaded with a discovery spike to
confirm each source is still available/licensed.

---

## 2. Northern Ireland plan

**Population ~1.9M. Smallest gap, thinnest data. Do this last.**

### Geography
- Use **Super Output Areas (SOA)** — 890 zones, ~2,100 people each — or the
  newer **Data Zones 2021** (NISRA). SOA is the established analogue. Postcodes
  → SOA via ONSPD / NISRA Central Postcode Directory. **[verify]**
- `area_id` = `N…`-prefixed SOA codes.

### Per-indicator source map
| Indicator | Source | Grain | Confidence note |
|---|---|---|---|
| Affordability — prices | **UK HPI** (LPS component) | LGD/postcode | Same source family |
| Affordability — rent | NISRA / NI Housing Executive rent stats | LGD (11 councils) | Very coarse; **[verify]** availability |
| Safety — crime | **PSNI recorded crime** | **Policing District / LGD** | ⚠ Coarser than Scotland; no street-level |
| Energy — EPC | **NI EPC register** (Dept of Finance) | Certificate/postcode | Comparable methodology |
| Flood | **DfI Rivers flood maps** | Polygon | Flag only |
| Convenience | OpenStreetMap | Point | Identical |

### New dbt models
`stg_crime__ni`, `stg_epc__ni`, `stg_flood__ni_dfi`, `stg_rent__ni` (+ geography
extend). Same conform-and-union pattern.

### Known risks
- **Coarsest grain of all three nations.** With only 890 SOAs and several
  indicators at LGD (11-council) level, NI scores will be blunt. Rent in
  particular may only exist at council level.
- Thinner open-data ecosystem; more sources behind request/registration.
- Smaller payoff (1.9M people) for comparable plumbing effort → lowest
  value-per-effort of the two.

### Effort (T-shirt)
Similar plumbing to Scotland but **harder acquisition, coarser grain, lower
confidence throughout**. **Total ≈ M–L**, dominated by data-availability
discovery.

---

## 3. The cross-nation problem: comparability

Pooled scoring means a "72 safety" in Glasgow sits on the same scale as
Manchester — but the *inputs* are not identical:

- **Crime taxonomies differ** (Police.uk vs Police Scotland vs PSNI categories);
  per-1,000 rates are roughly comparable, not definitionally identical.
- **Grain differs**: MSOA (~7,200) vs IZ (~4,000) vs SOA (~2,100). Scores are
  computed over differently-sized units.
- **Flood methodologies differ** (EA vs SEPA vs DfI) — already only a flag.
- **EPC is the most comparable** (shared SAP/RdSAP methodology UK-wide).

**Recommendation:** keep **pooled UK-wide scoring** (one scale, simplest for
users), but be honest in the UI:
- a per-area "scored against all UK areas; Scottish crime is council-level" note,
- lower `confidence_level` where the input is coarser,
- never hide that sources are devolved.

This is consistent with the product's founding principle — indicators with
sources and uncertainty, never laundered into a false-precision verdict.

---

## 4. Effort & payoff comparison

| | Scotland | Northern Ireland |
|---|---|---|
| Population reached | ~5.5M (8%) | ~1.9M (3%) |
| New areas (~) | ~1,300 IZ | ~890 SOA |
| Data quality | Good, crime coarse | Thinner, coarser |
| Plumbing effort | M–L | M–L |
| Value-per-effort | **Higher** | Lower |
| SEO pages unlocked (free, via existing template) | ~1,300 | ~890 |

---

## 5. Sequencing: now, or after the roadmap?

**Recommendation: continue the roadmap (mobile app + SEO growth) and add
Scotland then NI as a well-scoped *later* phase — but ship the cheap "honesty"
fixes now.**

### Why defer coverage, not the product
1. **Zero architectural penalty for waiting (§0).** Because nations only add
   rows to the profile mart and everything above is coverage-agnostic, deferral
   costs nothing in rework. If adding a nation forced API/UI changes, I'd say do
   it now to avoid churn — but it doesn't. This is the decisive point.
2. **Coverage widens the funnel; the roadmap builds the funnel.** The mobile
   app, Rightmove share-in, and the 7k programmatic-SEO area pages are what
   create *usage and distribution*. Adding two nations to a product few people
   use yet grows the addressable market but not actual users. Build the growth
   engine first, then widen what it feeds.
3. **90% of the population is already covered.** Scotland+NI add ~11% of people
   for a large share of the remaining data-engineering cost (two nations of
   devolved sources + comparability work). Value-per-effort says finish the
   product for the 90% first.
4. **Coverage work is discovery-heavy R&D** (crime gaps, EPC/rent availability,
   grain decisions). Front-loading uncertain R&D ahead of the known,
   high-value mobile work risks stalling momentum. Keep shipping.
5. **The ordering compounds.** Growth = programmatic SEO over area pages. Mature
   that engine first, and when Scotland/NI land later they *automatically*
   generate ~2,200 new indexable, internally-linked area pages with no extra
   frontend work. Coverage-after-SEO is worth more than coverage-before-SEO.

### Do these now (hours, not weeks — protects trust)
- **Fix the "UK" overclaim.** The API is titled "UK Housing Decision Support
  API" but covers E&W. Either rename to "England & Wales" or keep "UK" as the
  ambition while ensuring *every* surface labels current coverage.
- **Make the out-of-coverage path a feature.** The resolver already 422s
  Scottish/NI postcodes; change the copy to "We don't cover Scotland yet — it's
  on our roadmap," and capture a lightweight "notify me" signal. Every rejected
  postcode becomes a demand data-point telling you *where* to expand next.
- **Add a one-line coverage note to `/methodology`.**

### When I'd flip to "do Scotland now"
Only if the market/investor/customer story is **Scotland-specific**, or a
launch commitment requires nationwide coverage on day one. Absent that, defer.

### Proposed phase order
- **Now:** honesty fixes (hours) + continue **Phase 3 (mobile)** and the
  **Phase 2 SEO** build.
- **Phase 5 (after mobile ships):** **Scotland** coverage — discovery spike
  first, then the six staging models, rescore, expand the sitemap.
- **Phase 6:** **Northern Ireland** coverage, same pattern.

Each coverage phase is "add rows to the profile mart + rescore + tests + expand
sitemap" — self-contained, low-risk, and shippable without touching the product
surfaces the mobile/SEO work will have built.

---

*Drafted 2026-07-02. Grounds: `models/marts/decision/rpt_neighbourhood_score.sql`
(pooled scoring), `HOUSING_DECISION_SUPPORT_DATA_SOURCES.md`, `PRODUCT_ROADMAP.md`.
Source-availability facts marked **[verify]** need a discovery spike before build.*
