import type { MetadataRoute } from "next";
import { getAllAreas } from "@/lib/api";
import { areaSlug } from "@/lib/slug";
import { completeness } from "@/lib/quality";
import { REGIONS, regionSlug, townSlug } from "@/lib/geo";

export const revalidate = 86400;

const SITE_URL =
  process.env.NEXT_PUBLIC_SITE_URL?.replace(/\/$/, "") ?? "http://localhost:3000";

// Core + hub pages always; area pages that clear the quality gate. Sparse areas
// stay out (they're noindex anyway) so the sitemap only advertises pages worth
// crawling.
export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const core: MetadataRoute.Sitemap = [
    { url: SITE_URL, changeFrequency: "weekly", priority: 1 },
    { url: `${SITE_URL}/search`, changeFrequency: "weekly", priority: 0.8 },
    { url: `${SITE_URL}/compare`, changeFrequency: "monthly", priority: 0.5 },
    { url: `${SITE_URL}/check`, changeFrequency: "monthly", priority: 0.7 },
    { url: `${SITE_URL}/rankings`, changeFrequency: "weekly", priority: 0.7 },
    { url: `${SITE_URL}/methodology`, changeFrequency: "monthly", priority: 0.5 },
    ...REGIONS.map((r) => ({
      url: `${SITE_URL}/rankings/${regionSlug(r)}`,
      changeFrequency: "weekly" as const,
      priority: 0.7,
    })),
  ];

  try {
    const all = await getAllAreas();

    const towns = new Set<string>();
    const areas: MetadataRoute.Sitemap = [];
    for (const area of all) {
      if (area.local_authority_name) towns.add(area.local_authority_name);
      if (completeness(area).indexable) {
        areas.push({
          url: `${SITE_URL}/area/${areaSlug(area.area_id, area.area_name)}`,
          changeFrequency: "monthly",
          priority: 0.6,
        });
      }
    }

    const townUrls: MetadataRoute.Sitemap = [...towns].map((t) => ({
      url: `${SITE_URL}/town/${townSlug(t)}`,
      changeFrequency: "monthly",
      priority: 0.6,
    }));

    return [...core, ...townUrls, ...areas];
  } catch {
    // API unavailable at build — ship the core sitemap rather than failing.
    return core;
  }
}
