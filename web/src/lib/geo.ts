import { slugify } from "./slug";

// The ten England & Wales regions the dataset uses. Region hubs are a fixed,
// known set — so we can render /rankings/[region] from slugs without a lookup.
export const REGIONS = [
  "North East",
  "North West",
  "Yorkshire and The Humber",
  "East Midlands",
  "West Midlands",
  "East of England",
  "London",
  "South East",
  "South West",
  "Wales",
] as const;

export type Region = (typeof REGIONS)[number];

export function regionSlug(region: string): string {
  return slugify(region);
}

/** Resolve a region slug back to its canonical name, or null if unknown. */
export function regionFromSlug(slug: string): Region | null {
  return REGIONS.find((r) => regionSlug(r) === slug) ?? null;
}

// "Town" hubs are keyed on local authority — the closest grouping the data
// gives us above MSOA. Slug is just the slugified LA name.
export function townSlug(localAuthority: string): string {
  return slugify(localAuthority);
}
