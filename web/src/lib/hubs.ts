import type { Area } from "./types";
import { townSlug } from "./geo";

// Grouping helpers over the full dataset, for the region/town hubs and the
// internal-link mesh. All pure functions of an Area[] the caller fetched once.

export function rankByOverall(areas: Area[]): Area[] {
  return [...areas].sort((a, b) => (b.overall_score ?? -1) - (a.overall_score ?? -1));
}

export function areasInRegion(all: Area[], region: string): Area[] {
  return all.filter((a) => a.region === region);
}

export function areasInTown(all: Area[], localAuthority: string): Area[] {
  return all.filter((a) => a.local_authority_name === localAuthority);
}

export interface TownSummary {
  name: string;
  region: string | null;
  count: number;
  avgScore: number | null;
}

/** Local authorities ("towns") within a region, with size + average score. */
export function townsInRegion(all: Area[], region: string): TownSummary[] {
  const byLa = new Map<string, Area[]>();
  for (const a of areasInRegion(all, region)) {
    if (!a.local_authority_name) continue;
    const list = byLaGet(byLa, a.local_authority_name);
    list.push(a);
  }
  return [...byLa.entries()]
    .map(([name, list]) => ({
      name,
      region,
      count: list.length,
      avgScore: averageScore(list),
    }))
    .sort((a, b) => (b.avgScore ?? -1) - (a.avgScore ?? -1));
}

function byLaGet(map: Map<string, Area[]>, key: string): Area[] {
  let list = map.get(key);
  if (!list) {
    list = [];
    map.set(key, list);
  }
  return list;
}

export interface TownGroup {
  name: string;
  region: string | null;
  areas: Area[];
}

/** Resolve a town slug to its local-authority group (LA name isn't a fixed list). */
export function findTownBySlug(all: Area[], slug: string): TownGroup | null {
  const areas = all.filter(
    (a) => a.local_authority_name && townSlug(a.local_authority_name) === slug,
  );
  if (areas.length === 0) return null;
  return { name: areas[0].local_authority_name!, region: areas[0].region, areas };
}

/** Mean of a numeric Area field over the areas that have it, or null. */
export function averageField(areas: Area[], key: keyof Area): number | null {
  const values = areas
    .map((a) => a[key])
    .filter((v): v is number => typeof v === "number");
  if (values.length === 0) return null;
  return Math.round(values.reduce((x, y) => x + y, 0) / values.length);
}

export function averageScore(areas: Area[]): number | null {
  const scores = areas.map((a) => a.overall_score).filter((s): s is number => s != null);
  if (scores.length === 0) return null;
  return Math.round((scores.reduce((x, y) => x + y, 0) / scores.length) * 10) / 10;
}

/** Other areas in the same local authority, nearest in score first — for the mesh. */
export function siblingsByScore(all: Area[], area: Area, limit: number): Area[] {
  if (!area.local_authority_name) return [];
  return areasInTown(all, area.local_authority_name)
    .filter((a) => a.area_id !== area.area_id)
    .sort((a, b) => {
      const da = Math.abs((a.overall_score ?? 0) - (area.overall_score ?? 0));
      const db = Math.abs((b.overall_score ?? 0) - (area.overall_score ?? 0));
      return da - db;
    })
    .slice(0, limit);
}
