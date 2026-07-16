// Typed contract mirroring the public FastAPI v2 API (api/models.py).
// Keep in sync with the FastAPI Pydantic models; ideally generate from OpenAPI later.

export type ComponentKey =
  | "affordability_score"
  | "safety_score"
  | "energy_score"
  | "flood_score"
  | "convenience_score";

export const COMPONENT_KEYS: ComponentKey[] = [
  "affordability_score",
  "safety_score",
  "energy_score",
  "flood_score",
  "convenience_score",
];

export const COMPONENT_LABELS: Record<ComponentKey, string> = {
  affordability_score: "Affordability",
  safety_score: "Recorded crime",
  energy_score: "Energy efficiency",
  flood_score: "Flood resilience",
  convenience_score: "Convenience",
};

export interface Area {
  area_id: string;
  area_name: string;
  local_authority_name: string | null;
  region: string | null;
  overall_score: number | null;
  overall_rank: number | null;
  match_score: number | null;
  available_component_count: number | null;
  expected_component_count: number;
  all_component_source_dates_known: boolean;
  evidence_quality_level: "strong" | "mixed" | "limited" | null;
  evidence_quality_notes: string | null;
  why_this_area: string | null;
  affordability_score: number | null;
  safety_score: number | null;
  energy_score: number | null;
  flood_score: number | null;
  convenience_score: number | null;
  official_rent_monthly_gbp: number | null;
  median_sale_price_gbp: number | null;
  rent_source_grain: string | null;
  rent_reference_date: string | null;
  median_sale_price_confidence: string | null;
  rent_1bed_gbp: number | null;
  rent_2bed_gbp: number | null;
  rent_3bed_gbp: number | null;
  rent_4plus_gbp: number | null;
  epc_median_rating: string | null;
  crime_rate_per_1000: number | null;
  crime_record_count: number | null;
  crime_months_observed: number | null;
  crime_period_start: string | null;
  crime_period_end: string | null;
  crime_population_denominator: number | null;
  crime_population_reference_date: string | null;
  crime_population_geography: string | null;
  crime_population_source_name: string | null;
  flood_risk_flag: string | null;
  flood_postcode_pct: number | null;
  flood_source_status: string | null;
  flood_source_name: string | null;
  planning_constraint_count: number | null;
  planning_source_status: string | null;
  planning_source_name: string | null;
  walkable_amenity_count: number | null;
  nearest_station_km: number | null;
  nearest_supermarket_km: number | null;
  nearest_gp_km: number | null;
  nearest_school_km: number | null;
  nearest_greenspace_km: number | null;
  latitude: number | null;
  longitude: number | null;
  nearest_city: string | null;
  distance_to_city_km: number | null;
}

export interface Meta {
  areas: number;
  components: string[];
  default_weights: Record<string, number>;
  data_vintage: string;
  scoring_contract_version: string;
  note: string;
}

export interface AreaIndexResponse {
  count: number;
  data_vintage: string;
  areas: Area[];
}

export interface SearchRequest {
  weights?: Record<string, number>;
  max_rent?: number | null;
  regions?: string[] | null;
  min_overall?: number | null;
  limit?: number;
  offset?: number;
}

export interface SearchResponse {
  total: number;
  limit: number;
  offset: number;
  results: Area[];
}

export interface ResolveResponse {
  postcode: string;
  msoa_code: string;
  msoa_name: string | null;
  area: Area;
}

export type Deal = "rent" | "buy";
export type Bedrooms = "1" | "2" | "3" | "4plus" | "any";

export interface ListingCheckRequest {
  postcode: string;
  deal: Deal;
  bedrooms: Bedrooms;
  asking_gbp: number;
}

export interface PriceCheck {
  asking_gbp: number;
  comparison_gbp: number | null;
  pct_vs_comparison: number | null;
  band: string;
  basis: string;
}

export interface ListingCheckResponse {
  postcode: string;
  msoa_code: string;
  msoa_name: string | null;
  area: Area;
  price: PriceCheck | null;
}
