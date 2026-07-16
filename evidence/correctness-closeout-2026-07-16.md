# Correctness and evidence closeout

Release candidate: `correctness-closeout-2026-07-16`

This maintenance release closes the known correctness and evidence gaps and
adopts one descriptive identity across the repository, API, and website:
**England & Wales Housing Decision Support**.

## Correctness changes

- Recorded-crime rates now divide the observed event count by the number of
  observed months and the compatible ONS mid-2024 MSOA population, then multiply
  by 1,000. The denominator, date, geography, and source are published beside the rate.
- Planning and flood sources now carry `covered`, `not_covered`, or
  `source_missing` status. Wales is explicitly unsupported by those England-only
  sources; missing coverage can no longer become a favourable zero or low score.
- Score inputs propagate nulls explicitly. Missing rent or crime facts no longer
  produce a component score through database null-handling behaviour.
- Evidence quality is derived from component availability, jurisdiction coverage,
  source grain, and provenance. `strong` is impossible until every scored
  component has dated provenance; its explanatory note is tested against its level.
- The weighted geometric-mean scoring contract is versioned at `2.0.0` and shared
  with dbt, Python, and TypeScript golden cases. The committed dbt seeds are
  checked mechanically against the canonical JSON before dbt executes them.
- The API publishes `/v2` as its documented contract. Compatibility aliases for
  `/v1` remain callable but are excluded from OpenAPI.

## Evidence

- Shipped extract: 7,264 MSOAs (6,856 England; 408 Wales).
- Component coverage: affordability 7,262; recorded crime 7,237; energy 7,264;
  flood 6,856; convenience 7,264; overall 7,264.
- Evidence quality: 6,856 `mixed`, 408 `limited`, 0 `strong`. All 7,264 rows
  explicitly report that not every component source date is known, so no release
  claim is made that the current extract has strong evidence.
- Planning/flood coverage: all 6,856 English areas `covered`; all 408 Welsh areas
  `not_covered`.
- Crime population denominator: all 7,264 areas, MSOA 2021, reference date
  30 June 2024.
- The committed decision extract was compared row-for-row with SQL rescoring for
  all 7,264 areas.
- Verification: 222 dbt data tests, 2 dbt unit tests, 43 Python tests (including
  14 API tests), 16 TypeScript tests, web lint, and a production Next.js build.
- Local browser smoke: homepage, English and Welsh area receipts, listing check,
  and the search map passed. The map rendered an accessible MapLibre canvas,
  displayed OpenFreeMap/OpenStreetMap attribution, made successful keyless tile
  requests, and produced no browser errors.
- Live deployment smoke is deliberately marked pending until this candidate is
  merged and the Fly/Vercel/GitHub Pages deployments complete.
- dbt source freshness emits the declared warning because the committed
  Land Registry build ends in 2025 and is older than the 35-day operational
  threshold; this is recorded as a warning, not represented as current data.

The machine-readable source-vintage and coverage manifest is
[`correctness-closeout-2026-07-16.json`](correctness-closeout-2026-07-16.json).
Coverage statistics are reproducible with:

```bash
uv run python scripts/summarize_decision_extract.py
```

## Published wording changes

- The retired product name is removed from application identity and public copy.
- Listing checks compare user input with a named official area-level figure; they
  do not call it a valuation or a local "typical" price.
- Public pages continue to put the fact beside the score, use human-readable area
  names, avoid red/amber/green score judgements, and describe uncertainty directly.
- The search map no longer uses Google Maps. MapLibre GL JS renders keyless
  OpenFreeMap vector tiles, removing usage-based map billing. The public tile
  service is free but has no availability SLA, so the results list remains the
  provider-independent fallback.

## Maintenance limits

This is a completed portfolio reference implementation, not an active product
roadmap. Maintenance is limited to source breakages, security and dependency
updates, correctness defects, and evidence/documentation alignment. Exact upstream
vintages are not yet carried through every field of the slim public extract; the
manifest says where that limitation applies instead of implying false freshness.
