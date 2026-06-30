import type { Area, ComponentKey } from "./types";
import { COMPONENT_KEYS } from "./types";

// Client-side mirror of api/scoring.py reweight(): match_score is the weighted
// mean of the components an area actually has (missing ones are dropped, never
// scored zero). Lets sliders re-rank the visible pool instantly, no round-trip.

// Weighted GEOMETRIC mean of the available components (floored at 1), matching
// the warehouse overall_score so a single excellent pillar can't mask a poor one.
export function matchScore(area: Area, weights: Record<ComponentKey, number>): number | null {
  let logSum = 0;
  let den = 0;
  for (const k of COMPONENT_KEYS) {
    const v = area[k];
    const w = weights[k] ?? 0;
    if (v != null && w > 0) {
      logSum += w * Math.log(Math.max(v, 1));
      den += w;
    }
  }
  if (den === 0) return null;
  return Math.round(Math.exp(logSum / den) * 10) / 10;
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
      return b.match_score - a.match_score;
    });
}
