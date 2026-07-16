# Housing Area Profile Contract

Date prepared: 2026-07-15

## Decision

Use MSOA as the canonical area-indicator grain for the completed reference implementation.

The implemented marts rank MSOAs, not postcode areas, local authorities, or individual properties. Other grains roll into or annotate the MSOA-level indicator layer.

## Why MSOA

MSOA is the best first product grain because it is:

- Small enough to feel like a neighbourhood decision, unlike region or local authority.
- Large enough to reduce sparsity and privacy risk compared with full postcode or individual-property scoring.
- Compatible with many official UK geography lookups and demographic/statistical joins.
- A practical bridge between coarse official rent statistics and fine sources such as EPC, crime points, planning geometry, flood flags, and user-entered listings.

## Grain Roles

| Grain | Role in product | MVP status |
|---|---|---|
| Full postcode | User-entered listing lookup and source joins only; not final recommendation grain | Join key |
| Postcode area/outward | Legacy market overview and fallback rollup | Fallback only |
| LSOA | Fine evidence layer where source data supports it | Roll up to MSOA |
| MSOA | Canonical area recommendation grain | Required |
| Local authority | Coarse rent/house-price context and coverage fallback | Required context |
| Region | Portfolio-level context and broad comparison | Existing |

## Canonical Area Entity

`dim_area` contains one row per current MSOA used by the implementation.

Required columns:

| Column | Type | Rule |
|---|---|---|
| `area_id` | text | Stable MSOA code; primary key |
| `area_name` | text | Human-readable MSOA name where available |
| `area_type` | text | Always `MSOA` in the shipped model |
| `local_authority_code` | text | Non-null when source lookup provides it |
| `local_authority_name` | text | Non-null when source lookup provides it |
| `region` | text | England/Wales region or `Unknown` fallback |
| `centroid_latitude` | double | Between -90 and 90 |
| `centroid_longitude` | double | Between -180 and 180 |
| `source_snapshot_date` | date | Date of geography lookup snapshot |
| `source_name` | text | Example: `ONS Postcode Directory` |
| `source_url` | text | Source landing page or download URL |

## Postcode Geography Bridge

`dim_postcode_geography` should map current and observed postcodes into the area hierarchy.

Required columns:

| Column | Type | Rule |
|---|---|---|
| `postcode` | text | Normalised full postcode |
| `postcode_outward` | text | Existing outward code logic can be reused |
| `postcode_area` | text | Existing area code logic can be reused |
| `area_id` | text | MSOA code, nullable only for unmatched/retired postcodes |
| `lsoa_code` | text | LSOA code where available |
| `local_authority_code` | text | Local authority code |
| `region` | text | England/Wales region or `Unknown` |
| `latitude` | double | Postcode centroid latitude |
| `longitude` | double | Postcode centroid longitude |
| `is_current_postcode` | boolean | From lookup status where available |
| `is_in_source_lookup` | boolean | False for observed postcodes missing from the official lookup |
| `source_snapshot_date` | date | Lookup snapshot date |

## Area Profile Mart

`rpt_area_profile_mvp` is the decision-support fact mart. It is explainable and incomplete-friendly: missing or unsupported source layers appear as nulls plus explicit coverage states, not silently favourable values.

Grain:

- One row per `area_id`.

Required columns:

| Column | Type | Rule |
|---|---|---|
| `area_id` | text | MSOA key |
| `area_name` | text | Display name |
| `local_authority_name` | text | Context |
| `region` | text | Context |
| `median_sale_price_gbp` | numeric | From Land Registry rollup where available |
| `sales_count_latest_year` | integer | Market depth indicator |
| `official_rent_monthly_gbp` | numeric | Coarsest reliable rent estimate available |
| `rent_source_grain` | text | `local_authority` in the shipped extract; never presented as neighbourhood rent |
| `rent_reference_date` | date | Official rent observation date |
| `affordability_ratio` | numeric | Rent divided by user budget or default income scenario |
| `median_sale_price_confidence` | text | `reliable`, `indicative`, or `none` from latest-year sample depth |
| `epc_median_rating` | text | Energy profile where available |
| `crime_rate_per_1000` | numeric | Monthly recorded-crime indicator using a compatible ONS MSOA population denominator; never labelled safe/unsafe |
| `crime_record_count` | integer | Recorded events in the published observation window |
| `crime_months_observed` | integer | Distinct months used by the rate |
| `crime_period_start` / `crime_period_end` | text | Inclusive `YYYY-MM` observation bounds |
| `crime_population_denominator` | integer | ONS mid-2024 population for the same MSOA 2021 geography |
| `crime_population_reference_date` | date | Population denominator reference date |
| `crime_population_geography` / `crime_population_source_name` | text | Denominator provenance |
| `flood_risk_flag` | text | `low`, `medium`, `high`, or null outside coverage |
| `flood_postcode_pct` | numeric | Share of area postcodes intersecting the covered flood-risk-zone geometry |
| `flood_source_status` | text | `covered`, `not_covered`, or `source_missing` |
| `flood_source_name` | text | Environment Agency flood-risk zones |
| `planning_constraint_count` | integer | Count of relevant planning constraints/intersections; null outside coverage |
| `planning_source_status` | text | `covered`, `not_covered`, or `source_missing` |
| `planning_source_name` | text | Planning Data Platform provenance |
| `nearest_*_km` / `walkable_amenity_count` | numeric | OpenStreetMap amenity and station access facts |
| `latitude` / `longitude` | numeric | MSOA display centroid |
| `commute_minutes_sample` | numeric | Null placeholder; door-to-door commute is not implemented or claimed |
| `source_coverage_notes` | text | Explain missing, unsupported, or coarse source coverage |
| `why_this_area` | text | Short explanation assembled from component signals |

`rpt_neighbourhood_score` adds `available_component_count`,
`expected_component_count`, `all_component_source_dates_known`,
`evidence_quality_level` (`strong`, `mixed`, or `limited`) and
`evidence_quality_notes`. Strong evidence is unavailable until every scored
component has dated provenance.

## Enforced Test Contract

The build enforces these conditions in schema and singular dbt tests:

- `dim_area.area_id` is unique and non-null.
- `dim_postcode_geography.postcode` is unique and non-null.
- At least 95 percent of Land Registry fact rows with a postcode map to an `area_id`, or the shortfall is documented with a failing-threshold rationale.
- No `rpt_area_profile_mvp` row has a non-null recommendation/evidence label without an `area_id`.
- Latitude/longitude values are within valid ranges.
- `rent_source_grain` is non-null whenever `official_rent_monthly_gbp` is non-null.
- `source_coverage_notes` is non-null whenever any core source layer is missing.

## Current Implementation Status

- `scripts/prepare_onspd_seed.py` and `scripts/load_geography.py` prepare and load the official postcode lookup.
- `stg_geo__postcodes`, `dim_postcode_geography`, and `dim_area` establish the MSOA 2021 spine with human names.
- `rpt_area_profile_mvp` combines market, official local-authority rent, EPC, recorded crime with compatible population, planning/flood coverage, and OpenStreetMap access facts.
- `rpt_neighbourhood_score` applies scoring contract v2, deterministic tie order, null-safe weighting, and explicit evidence quality.
- Fixture CI and the 7,264-area real-source build exercise the same marts; the real-source coverage manifest is in `evidence/`.

## Official Lookup Preparation

The committed fixture is deliberately tiny. To prepare a local official postcode lookup snapshot, run:

```bash
python scripts/prepare_onspd_seed.py path/to/onspd.zip --member "Data/*.csv" --snapshot-date 2026-05-01
```

By default, the output is written to `data/raw/ref_onspd_normalized.csv`, which is ignored by git. Use `--output seeds/ref_onspd_sample.csv --limit 1000` only when intentionally refreshing a small committed fixture.

## Current Non-Goals

- Do not claim live rental availability.
- Do not scrape portals.
- Do not make property-level risk claims from area-level data.
- Do not show a "safe/unsafe" label.
- Do not imply Scotland, Northern Ireland, door-to-door commute, or user-listing ingestion is planned; those surfaces are outside the completed England-and-Wales reference scope.
