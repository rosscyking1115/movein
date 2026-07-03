# Scotland Coverage — Discovery Spike

The first, deliberately small task from [UK_COVERAGE_EXPANSION_PLAN.md](UK_COVERAGE_EXPANSION_PLAN.md#1-scotland-plan).
**Goal: confirm every source is available, licensed, and mappable — before writing
any pipeline code.** Timebox ~2–3 days. No production models until this passes.

Nothing here changes the product surfaces: Scotland lands as new rows on the
existing `rpt_area_profile_mvp` contract, and the API/web/mobile are already
coverage-agnostic. So this spike is pure data due-diligence.

## Decisions to lock first (blockers for everything downstream)
- [ ] **Recommendation grain: Intermediate Zone (IZ) vs Data Zone (DZ).**
      Plan recommends **IZ** (~1,279 zones, ~4,000 people — closest MSOA analogue).
      Confirm and record the choice; it fixes `area_id` prefixes and every join.
- [ ] **Scoring anchoring: pooled UK-wide vs within-nation.** Plan recommends
      **pooled** (one scale) + confidence flags. Confirm with product owner.
- [ ] **Comparability stance for coarse inputs** (esp. crime): agree that
      LA-level Scottish crime attaches to IZs with a lowered `confidence_level`,
      and that the UI will say so.

## Source availability — confirm each (replace [verify] with a dated finding)
For each: is it downloadable/open, what licence, what grain, does it map to IZ?

- [ ] **Geography — ONSPD** already carries postcode→Data Zone/Intermediate Zone.
      Confirm the current ONSPD release includes Scottish fields and the licence
      permits our use. Land in an extended `stg_geo__postcodes`.
- [ ] **Prices — UK House Price Index (RoS component).** Confirm UK HPI publishes
      Scotland at Data Zone/LA and the licence (OGL). Extends the affordability
      inputs; no new bespoke scraper.
- [ ] **Rent — Scottish Government Private Sector Rent Statistics** (and/or ONS
      PIPR Scotland). Confirm grain (BRMA/LA), per-bedroom availability, and how
      BRMA maps to IZ. Rent is the least certain affordability input.
- [ ] **Crime — Police Scotland / statistics.gov.scot recorded crime.** Confirm
      it is **LA-level** (no street-level equivalent to data.police.uk),
      per-category, and derive a per-1,000-residents rate. Record the taxonomy
      differences vs Police.uk for the comparability note.
- [ ] **Energy — Scottish EPC Register.** Confirm bulk/domestic download, access
      requirements, and that it uses SAP/RdSAP (so it's comparable to E&W EPC).
- [ ] **Flood — SEPA flood risk maps.** Confirm polygon download + licence; this
      stays a flag, not a precise risk, matching the EA treatment.
- [ ] **Amenities — OpenStreetMap.** No change; already UK-wide.

## Population denominator
- [ ] Source IZ-level population (NRS mid-year estimates) to convert crime counts
      and any count-based indicators into rates. Confirm grain matches IZ.

## Landing plan (write only after the above is green)
New/extended staging models, all conforming to the existing profile contract:
- [ ] `stg_geo__postcodes` — extend with Scottish postcode→IZ rows
- [ ] extend price inputs to UK HPI (RoS)
- [ ] `stg_rent__scotland`
- [ ] `stg_crime__scotland`  (LA-level → IZ, confidence-flagged)
- [ ] `stg_epc__scotland`
- [ ] `stg_flood__scotland_sepa`
- [ ] union all into `rpt_area_profile_mvp` (S-prefixed IZ `area_id`s)
- [ ] `scripts/rescore_extract.py` regenerates `data/decision.duckdb`
- [ ] existing data-quality tests apply unchanged; add Scotland row-count bounds

## Definition of done for the spike
- [ ] Every source above has a dated availability + licence finding (or a blocker
      raised).
- [ ] The three decisions are recorded.
- [ ] A one-page effort estimate per staging model, so the build phase can be
      planned with real numbers instead of T-shirt sizes.
- [ ] A short "comparability notes" list (crime taxonomy, grain, flood method)
      that will become the UI's per-nation confidence copy.

## Explicitly out of scope for the spike
- Building any staging model or pipeline.
- Any change to the API, website, mobile app, or scoring math (the pooled bounds
  in `rpt_neighbourhood_score.sql` absorb new rows automatically).
- Northern Ireland (its own spike, after Scotland).

---

*Companion to `UK_COVERAGE_EXPANSION_PLAN.md`. Start here when Scotland coverage
is scheduled (per the plan: after the mobile app ships).*
