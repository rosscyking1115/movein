import type { Area, ComponentKey } from "./types";
import { COMPONENT_KEYS } from "./types";

// Client-side mirror of api/scoring.py reweight(): match_score is the weighted
// mean of the components an area actually has (missing ones are dropped, never
// scored zero). Lets sliders re-rank the visible pool instantly, no round-trip.

export function matchScore(area: Area, weights: Record<ComponentKey, number>): number | null {
  let num = 0;
  let den = 0;
  for (const k of COMPONENT_KEYS) {
    const v = area[k];
    const w = weights[k] ?? 0;
    if (v != null && w > 0) {
      num += v * w;
      den += w;
    }
  }
  if (den === 0) return null;
  return Math.round((num / den) * 10) / 10;
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
