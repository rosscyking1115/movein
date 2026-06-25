# Housing Area Profile Contract

Date prepared: 2026-06-25

## Decision

Use MSOA as the canonical MVP recommendation area.

The product should rank MSOAs, not postcode areas, local authorities, or individual properties. Other grains remain useful, but they should roll into or annotate the MSOA-level recommendation layer.

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

`dim_area` should contain one row per current MSOA used by the product.

Required columns:

| Column | Type | Rule |
|---|---|---|
| `area_id` | text | Stable MSOA code; primary key |
| `area_name` | text | Human-readable MSOA name where available |
| `area_type` | text | For MVP, always `MSOA` |
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

## MVP Area Profile Mart

`rpt_area_profile_mvp` should be the first decision-support mart. It should be explainable and incomplete-friendly: missing source layers should appear as nulls plus confidence flags, not silently disappear.

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
| `rent_source_grain` | text | Example: `local_authority`, `BRMA`, `MSOA`, `user_entered` |
| `affordability_ratio` | numeric | Rent divided by user budget or default income scenario |
| `epc_median_rating` | text | Energy profile where available |
| `crime_rate_per_1000` | numeric | Crime indicator; never labelled safe/unsafe |
| `flood_risk_flag` | text | `low`, `medium`, `high`, `unknown` or source-native label |
| `planning_constraint_count` | integer | Count of relevant planning constraints/intersections |
| `commute_minutes_sample` | numeric | For configured destination/sample |
| `confidence_level` | text | `high`, `medium`, `low` |
| `confidence_notes` | text | Explain missing/coarse data |
| `why_this_area` | text | Short explanation assembled from component signals |

## Test Contract

The first geography implementation is not complete until these tests exist:

- `dim_area.area_id` is unique and non-null.
- `dim_postcode_geography.postcode` is unique and non-null.
- At least 95 percent of Land Registry fact rows with a postcode map to an `area_id`, or the shortfall is documented with a failing-threshold rationale.
- No `rpt_area_profile_mvp` row has a non-null recommendation/confidence label without an `area_id`.
- Latitude/longitude values are within valid ranges.
- `rent_source_grain` is non-null whenever `official_rent_monthly_gbp` is non-null.
- `confidence_notes` is non-null whenever any core source layer is missing.

## First Implementation Slice

Build this in the existing repo only as a prototype branch, or copy the pattern into a new `uk-housing-decision-support` repo.

1. Add official postcode lookup ingestion. Done as a local CSV/ZIP normalizer in `scripts/prepare_onspd_seed.py`; the full official snapshot is intentionally not committed.
2. Build `stg_geo__postcodes`. Done against the committed `ref_onspd_sample` fixture.
3. Build `dim_postcode_geography`. Done at postcode grain.
4. Build `dim_area` at MSOA grain. Done for fixture-backed MSOA-like areas.
5. Add geography coverage tests. Started with uniqueness, source caveat, and area-profile market-match tests; full Land Registry coverage threshold still needs the real lookup snapshot.
6. Add a tiny `rpt_area_profile_mvp` with Land Registry market context only. Done with low-confidence caveats for missing source layers.
7. Add ONS rent as the first non-Land-Registry source after the geography join is proven.

## Official Lookup Preparation

The committed fixture is deliberately tiny. To prepare a local official postcode lookup snapshot, run:

```bash
python scripts/prepare_onspd_seed.py path/to/onspd.zip --member "Data/*.csv" --snapshot-date 2026-05-01
```

By default, the output is written to `data/raw/ref_onspd_normalized.csv`, which is ignored by git. Use `--output seeds/ref_onspd_sample.csv --limit 1000` only when intentionally refreshing a small committed fixture.

## Non-Goals For This Slice

- Do not build a final neighbourhood score yet.
- Do not claim live rental availability.
- Do not scrape portals.
- Do not make property-level risk claims from area-level data.
- Do not show a "safe/unsafe" label.

## Open Questions

- Which official postcode lookup snapshot should be the pinned first source?
- Should the prototype cover England and Wales only, matching Land Registry, or include Scotland/Northern Ireland with partial source coverage notes?
- Should the first commute slice be London-first with TfL, or UK-wide but approximate with station/stop proximity?
