import type { Metadata } from "next";
import { search } from "@/lib/api";
import type { SearchResponse } from "@/lib/types";
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
  // Degrade gracefully if the data API is unavailable rather than crashing.
  let initial: SearchResponse | null = null;
  try {
    initial = await search({
      regions: initialRegions.length ? initialRegions : null,
      limit: 200,
    });
  } catch {
    initial = null;
  }

  return (
    <div className="mx-auto max-w-[1140px] px-6 pb-[70px] pt-[34px]">
      <header className="mb-7 max-w-[620px]">
        <h1 className="font-display text-[clamp(34px,4.6vw,52px)] font-bold leading-[1.05] text-ink">
          Rank by what matters to you
        </h1>
        <p className="mt-2 text-[17px] text-ink2">
          Move the sliders. The list re-ranks live across{" "}
          {(initial?.total ?? 7264).toLocaleString("en-GB")} neighbourhoods — and
          shows you exactly which indicators did the lifting. No black box.
        </p>
      </header>
      {initial === null && (
        <p className="mb-4 rounded-[10px] border border-caution bg-caution/10 px-4 py-3 text-sm text-caution">
          The data service is starting up or briefly unavailable — results may be
          empty for a moment. Try reloading shortly.
        </p>
      )}
      <SearchClient initialAreas={initial?.results ?? []} initialRegions={initialRegions} />
    </div>
  );
}
