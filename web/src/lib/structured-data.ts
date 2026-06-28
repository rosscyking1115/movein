import type { Area } from "./types";
import { answerSentence } from "./summary";

const SITE_URL =
  process.env.NEXT_PUBLIC_SITE_URL?.replace(/\/$/, "") ?? "http://localhost:3000";

/** ItemList + BreadcrumbList for a ranking/hub page. */
export function rankingJsonLd(
  opts: {
    title: string;
    path: string;
    crumbs: { name: string; path: string }[];
    items: { name: string; path: string }[];
  },
): Record<string, unknown> {
  return {
    "@context": "https://schema.org",
    "@graph": [
      {
        "@type": "ItemList",
        name: opts.title,
        url: `${SITE_URL}${opts.path}`,
        numberOfItems: opts.items.length,
        itemListElement: opts.items.map((it, i) => ({
          "@type": "ListItem",
          position: i + 1,
          name: it.name,
          url: `${SITE_URL}${it.path}`,
        })),
      },
      {
        "@type": "BreadcrumbList",
        itemListElement: opts.crumbs.map((c, i) => ({
          "@type": "ListItem",
          position: i + 1,
          name: c.name,
          item: `${SITE_URL}${c.path}`,
        })),
      },
    ],
  };
}

/** schema.org Place + BreadcrumbList for an area page, as a @graph. */
export function areaJsonLd(area: Area, slug: string): Record<string, unknown> {
  const url = `${SITE_URL}/area/${slug}`;
  return {
    "@context": "https://schema.org",
    "@graph": [
      {
        "@type": "Place",
        "@id": `${url}#place`,
        name: area.area_name,
        description: answerSentence(area),
        url,
        address: {
          "@type": "PostalAddress",
          addressRegion: area.region ?? undefined,
          addressLocality: area.local_authority_name ?? undefined,
          addressCountry: "GB",
        },
      },
      {
        "@type": "BreadcrumbList",
        itemListElement: [
          { "@type": "ListItem", position: 1, name: "Home", item: SITE_URL },
          { "@type": "ListItem", position: 2, name: "Areas", item: `${SITE_URL}/search` },
          { "@type": "ListItem", position: 3, name: area.area_name, item: url },
        ],
      },
    ],
  };
}
