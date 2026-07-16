import type { Area, ComponentKey } from "./types";
import { COMPONENT_KEYS } from "./types";
import contract from "../../../contracts/neighbourhood-scoring-v2.json";

// Client-side mirror of api/scoring.py reweight(): match_score is the weighted
// geometric mean of the components an area actually has (missing ones are
// dropped, never scored zero). Lets sliders re-rank the visible pool instantly,
// with no round-trip.

// Weighted GEOMETRIC mean of the available components (floored at 1), matching
// the warehouse overall_score so a single excellent pillar can't mask a poor one.
export function matchScore(area: Area, weights: Record<ComponentKey, number>): number | null {
  let logSum = 0;
  let den = 0;
  for (const k of COMPONENT_KEYS) {
    const v = area[k];
    const w = weights[k] ?? 0;
    if (!Number.isFinite(w) || w < contract.allowed_weight.minimum || w > contract.allowed_weight.maximum) {
      throw new RangeError(
        `Weights must be finite numbers from ${contract.allowed_weight.minimum} to ${contract.allowed_weight.maximum}.`,
      );
    }
    if (v != null && Number.isFinite(v) && w > 0) {
      logSum += w * Math.log(Math.max(v, contract.component_floor));
      den += w;
    }
  }
  if (den === 0) return null;
  const scale = 10 ** contract.rounding_decimal_places;
  return Math.round(Math.exp(logSum / den) * scale) / scale;
}

export function reweight(
  areas: Area[],
  weights: Record<ComponentKey, number>,
): Area[] {
  return areas
    .map((a) => ({ ...a, match_score: matchScore(a, weights) }))
    .sort((a, b) => {
      if (a.match_score == null) return 1;
      if (b.match_score == null) return -1;
      return b.match_score - a.match_score || a.area_id.localeCompare(b.area_id);
    });
}

export type EvidenceInputs = {
  available_component_count: number;
  crime_population_denominator: number | null;
  crime_population_reference_date: string | null;
  crime_period_start: string | null;
  crime_period_end: string | null;
  rent_source_grain: string | null;
  rent_reference_date: string | null;
  median_sale_price_confidence: string | null;
  all_component_source_dates_known: boolean;
  planning_source_status: string | null;
  flood_source_status: string | null;
};

export function evidenceQuality(inputs: EvidenceInputs): "strong" | "mixed" | "limited" {
  if (
    inputs.available_component_count < 3 ||
    inputs.crime_population_denominator == null ||
    inputs.planning_source_status !== "covered" ||
    inputs.flood_source_status !== "covered"
  ) {
    return "limited";
  }
  if (
    inputs.available_component_count === 5 &&
    inputs.rent_source_grain === "msoa" &&
    inputs.median_sale_price_confidence === "reliable" &&
    inputs.all_component_source_dates_known &&
    inputs.rent_reference_date != null &&
    inputs.crime_population_reference_date != null &&
    inputs.crime_period_start != null &&
    inputs.crime_period_end != null
  ) {
    return "strong";
  }
  return "mixed";
}
