import type { Metadata } from "next";
import Link from "next/link";
import { getAllAreas } from "@/lib/api";
import { REGIONS, regionSlug } from "@/lib/geo";
import { areasInRegion, averageScore } from "@/lib/hubs";
import { score } from "@/lib/format";
import type { Area } from "@/lib/types";

export const revalidate = 86400;

export const metadata: Metadata = {
  title: "Neighbourhood rankings by region",
  description:
    "Browse ranked neighbourhoods across the ten regions of England & Wales — the best areas to live by our affordability, safety, energy, flood and convenience indicators.",
};

export default async function RankingsIndex() {
  let all: Area[] = [];
  try {
    all = await getAllAreas();
  } catch {
    all = [];
  }

  const regions = REGIONS.map((name) => {
    const areas = areasInRegion(all, name);
    return { name, count: areas.length, avg: averageScore(areas) };
  });

  return (
    <div className="mx-auto max-w-4xl px-5 py-10">
      <header className="mb-8 max-w-2xl">
        <h1 className="text-3xl font-semibold tracking-tight">Rankings by region</h1>
        <p className="mt-2 text-ink-muted">
          Pick a region to see its best-scoring neighbourhoods and a breakdown by
          local authority.
        </p>
      </header>

      <div className="grid gap-3 sm:grid-cols-2">
        {regions.map((r) => (
          <Link
            key={r.name}
            href={`/rankings/${regionSlug(r.name)}`}
            className="flex items-center justify-between rounded-card border border-rule bg-paper-raised px-4 py-3 transition-colors hover:border-rule-strong"
          >
            <div>
              <div className="font-medium">{r.name}</div>
              <div className="text-xs text-ink-muted">
                {r.count.toLocaleString("en-GB")} areas
              </div>
            </div>
            <div className="text-right">
              <div className="tnum text-lg font-semibold">{score(r.avg)}</div>
              <div className="text-[10px] uppercase tracking-wide text-ink-faint">avg</div>
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
}
