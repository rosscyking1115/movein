import type { Metadata } from "next";
import { search } from "@/lib/api";
import { SearchClient } from "@/components/SearchClient";

export const metadata: Metadata = {
  title: "Search neighbourhoods by your priorities",
  description:
    "Rank England & Wales neighbourhoods by what matters to you — affordability, safety, energy, flood risk, convenience — and filter by budget and region.",
};

type Props = {
  searchParams: Promise<{ regions?: string | string[] }>;
};

function parseRegions(raw: string | string[] | undefined): string[] {
  if (!raw) return [];
  const list = Array.isArray(raw) ? raw : raw.split(",");
  return list.map((r) => r.trim()).filter(Boolean);
}

export default async function SearchPage({ searchParams }: Props) {
  const initialRegions = parseRegions((await searchParams).regions);

  // Server-render an initial pool so the page is useful with JS still loading.
  const initial = await search({
    regions: initialRegions.length ? initialRegions : null,
    limit: 200,
  });

  return (
    <div className="mx-auto max-w-5xl px-5 py-10">
      <header className="mb-8 max-w-2xl">
        <h1 className="text-3xl font-semibold tracking-tight">
          Find your neighbourhood
        </h1>
        <p className="mt-2 text-ink-muted">
          Tell us what matters. We rank {initial.total.toLocaleString("en-GB")}{" "}
          England &amp; Wales neighbourhoods on five indicators and show the fact
          behind every score.
        </p>
      </header>
      <SearchClient initialAreas={initial.results} initialRegions={initialRegions} />
    </div>
  );
}
