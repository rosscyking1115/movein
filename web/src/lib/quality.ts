import type { Area, ComponentKey } from "./types";
import { COMPONENT_KEYS } from "./types";

// Thin-content discipline at ~7k pages: only index an area page that carries
// enough genuine data to be non-substitutable. Sparse areas render but are
// noindex'd until they fill in, so they can't drag the site-wide quality signal.

export interface Completeness {
  componentsPresent: number;
  hasAmenities: boolean;
  indexable: boolean;
}

export function completeness(area: Area): Completeness {
  const componentsPresent = COMPONENT_KEYS.filter(
    (k: ComponentKey) => area[k] != null,
  ).length;
  const hasAmenities = (area.walkable_amenity_count ?? 0) > 0;
  const indexable =
    area.overall_score != null && componentsPresent >= 4 && hasAmenities;
  return { componentsPresent, hasAmenities, indexable };
}
